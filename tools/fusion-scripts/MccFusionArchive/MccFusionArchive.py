# Builds one Fusion design per case variant (base + lid, the lid in its assembled position) and one per
# TV-bracket assembly (brackets.json) from the exact STEP exports in exports\, saves each into the hub
# project 'Magewell converter cases' (folder HUB_FOLDER) and writes each as a Fusion archive into the
# repository (issue #125, D125.1) -- the committed .f3d snapshots under archive\fusion\. They are dumb
# STEP solids without a feature tree: viewing snapshots, not the Fusion masters of #81-#86 and never a
# parity input (R125.1). A manual script outside the Fusion runtime, so D79.5's "never saves" does not
# apply. Reads only exports\ and brackets.json; writes only under ARCHIVE_ROOT.
import hashlib
import json
import math
import os
import subprocess
import traceback

import adsk.core
import adsk.fusion

REPO = r'C:\repos-github\magewell-converter-cases'
EXPORTS = os.path.join(REPO, 'exports')
ARCHIVE_ROOT = os.path.join(REPO, 'archive', 'fusion')
PROJECT = 'Magewell converter cases'
HUB_FOLDER = 'Archive - STEP snapshots'  # never the D75.5 document names MCC-Case/-Brackets/-Coupons
# Off by default: 12 designs exceed the Personal plan's 10 active editable documents on the hub;
# the committed archives are the deliverable. Set True to also save each design to the hub folder.
SAVE_TO_HUB = False
BRACKETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'brackets.json')


def case_designs():
    """[(group, design name, stem, configuration, [(component, step path, placement), ...])]."""
    out = []
    for slug in sorted(os.listdir(EXPORTS)):
        d = os.path.join(EXPORTS, slug)
        if slug in ('brackets', 'coupons', 'fusion-verify') or not os.path.isdir(d):
            continue
        lid = os.path.join(d, 'lid.step')
        for base in sorted(f[:-5] for f in os.listdir(d) if f.startswith('base') and f.endswith('.step')):
            suffix = '' if base == 'base' else base.split('_', 1)[1]
            name = slug if not suffix else f'{slug} ({suffix})'
            stem = slug if not suffix else f'{slug}-{suffix}'
            parts = [(f'{name} {base}', os.path.join(d, base + '.step'), None)]
            if os.path.isfile(lid):
                parts.append((f'{name} lid', lid, None))
            out.append(('cases', name, stem, 'default' if base == 'base' else base, parts))
    return out


def bracket_designs():
    with open(BRACKETS, encoding='utf-8') as f:
        spec = json.load(f)
    out = []
    for b in spec['brackets']:
        d = os.path.join(EXPORTS, 'brackets', b['dir'])
        parts = [(f"{b['design']} {p['name']}", os.path.join(d, p['step'] + '.step'), p) for p in b['parts']]
        out.append(('brackets', b['design'], b['stem'], 'assembly', parts))
    return out


def _matrix(p):
    m = adsk.core.Matrix3D.create()
    if p:
        m.setToRotation(math.radians(p.get('rz', 0)), adsk.core.Vector3D.create(0, 0, 1),
                        adsk.core.Point3D.create(0, 0, 0))
        m.translation = adsk.core.Vector3D.create(p['x'] / 10, p['y'] / 10, p['z'] / 10)  # mm -> cm
    return m


def _project(app):
    projects = app.data.dataProjects
    items = [projects.item(i) for i in range(projects.count)]
    exact = [p for p in items if p.name == PROJECT]
    loose = [p for p in items if p.name.casefold() == PROJECT.casefold()]
    return (exact or loose or [projects.add(PROJECT)])[0]


def _folder(proj):
    folders = proj.rootFolder.dataFolders
    return folders.itemByName(HUB_FOLDER) or folders.add(HUB_FOLDER)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _step_source(path):
    """The git SHA the STEP's part was exported from (its manifest), else 'unknown'."""
    try:
        with open(path[:-5] + '.manifest.json', encoding='utf-8') as f:
            return json.load(f).get('git_head_sha', 'unknown')[:7]
    except Exception:
        return 'unknown'


def _checkout():
    try:
        return subprocess.run(['git', '-C', REPO, 'rev-parse', '--short', 'HEAD'], capture_output=True,
                              text=True, timeout=10, creationflags=0x08000000).stdout.strip()
    except Exception:
        return 'unknown'


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        proj = _project(app) if SAVE_TO_HUB else None
        folder = _folder(proj) if SAVE_TO_HUB else None
        im = app.importManager
        archives, failed = [], []
        for group, name, stem, config, parts in case_designs() + bracket_designs():
            try:
                out_dir = os.path.join(ARCHIVE_ROOT, group)
                os.makedirs(out_dir, exist_ok=True)
                doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
                design = adsk.fusion.Design.cast(app.activeProduct)
                root = design.rootComponent
                for comp_name, path, placement in parts:
                    sub = root.occurrences.addNewComponent(_matrix(placement)).component
                    sub.name = comp_name
                    im.importToTarget(im.createSTEPImportOptions(path), sub)
                app.activeViewport.fit()
                doc.name = name
                if SAVE_TO_HUB:
                    doc.saveAs(name, folder, f'{group[:-1].capitalize()} from the exact STEP exports (#125).', '')
                em = design.exportManager
                em.execute(em.createFusionArchiveExportOptions(os.path.join(out_dir, stem + '.f3d')))
                archives.append({
                    'file': f'{group}/{stem}.f3d', 'design': name, 'configuration': config,
                    'parts': [{'component': c, 'step': os.path.relpath(p, REPO).replace(os.sep, '/'),
                               'source_sha': _step_source(p), 'sha256': _sha256(p),
                               'placement_mm_deg': pl and {k: pl[k] for k in ('x', 'y', 'z', 'rz')}}
                              for c, p, pl in parts]})
            except Exception:
                failed.append(f'{name}: {traceback.format_exc().splitlines()[-1]}')
        with open(os.path.join(ARCHIVE_ROOT, 'manifest.json'), 'w', encoding='utf-8', newline='\n') as f:
            json.dump({'script_checkout': _checkout(), 'hub': f'{proj.name}/{HUB_FOLDER}' if proj else None,
                       'archives': archives, 'failed': failed}, f, indent=2)
            f.write('\n')
        where = f'saved to "{proj.name}/{HUB_FOLDER}" and ' if proj else ''
        msg = f'{len(archives)} designs {where}archived to\n{ARCHIVE_ROOT}'
        if failed:
            msg += '\n\nFailed:\n' + '\n'.join(failed)
        ui.messageBox(msg, 'MCC Fusion archive')
    except Exception:
        ui.messageBox('MccFusionArchive failed:\n' + traceback.format_exc())
