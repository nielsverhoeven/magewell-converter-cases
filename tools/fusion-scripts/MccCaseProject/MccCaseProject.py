# Creates (or reuses) the Fusion project 'Magewell converter cases' and saves one design in it,
# 'MCC case variants': every case variant of the repository as its own component (base + lid, the
# lid in its assembled position), laid out on a grid, built from the exact STEP exports in exports\.
# One document only, so the Personal plan's limit on active editable documents is not stretched.
import os
import traceback

import adsk.core
import adsk.fusion

EXPORTS = r'C:\repos-github\magewell-converter-cases\exports'
PROJECT = 'Magewell converter cases'
DESIGN = 'MCC case variants'
PITCH_X, PITCH_Y, COLS = 25.0, 22.0, 3  # cm (Fusion's internal unit)


def variants():
    """[(component name, [(part name, step path), ...])] -- one per base variant of every case."""
    out = []
    for slug in sorted(os.listdir(EXPORTS)):
        d = os.path.join(EXPORTS, slug)
        if slug in ('brackets', 'coupons', 'fusion-verify') or not os.path.isdir(d):
            continue
        lid = os.path.join(d, 'lid.step')
        for base in sorted(f[:-5] for f in os.listdir(d) if f.startswith('base') and f.endswith('.step')):
            name = slug if base == 'base' else f'{slug} ({base.split("_", 1)[1]})'
            parts = [(base, os.path.join(d, base + '.step'))]
            if os.path.isfile(lid):
                parts.append(('lid', lid))
            out.append((name, parts))
    return out


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        projects = app.data.dataProjects
        proj = next((projects.item(i) for i in range(projects.count)
                     if projects.item(i).name.casefold() == PROJECT.casefold()), None)
        if proj is None:
            proj = projects.add(PROJECT)
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent
        im = app.importManager
        done, failed = [], []
        for i, (name, parts) in enumerate(variants()):
            try:
                m = adsk.core.Matrix3D.create()
                m.translation = adsk.core.Vector3D.create((i % COLS) * PITCH_X, -(i // COLS) * PITCH_Y, 0)
                case = root.occurrences.addNewComponent(m).component
                case.name = name
                for part, path in parts:
                    sub = case.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
                    sub.name = f'{name} {part}'
                    im.importToTarget(im.createSTEPImportOptions(path), sub)
                done.append(name)
            except Exception:
                failed.append(f'{name}: {traceback.format_exc().splitlines()[-1]}')
        app.activeViewport.fit()
        doc.saveAs(DESIGN, proj.rootFolder,
                   'Every case variant (base + lid) from the exact STEP exports of main (issue #119 fix included).', '')
        msg = f'Project "{PROJECT}": design "{DESIGN}" saved with {len(done)} case variants.'
        if failed:
            msg += '\n\nFailed:\n' + '\n'.join(failed)
        ui.messageBox(msg, 'MCC case project')
    except Exception:
        ui.messageBox('MccCaseProject failed:\n' + traceback.format_exc())
