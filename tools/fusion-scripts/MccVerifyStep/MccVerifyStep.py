# Issue #119 check: import the regenerated fan base STEP, export it to STL from Fusion and count the
# mesh's open and non-manifold edges (what Bambu Studio reported). Nothing is saved to the hub.
import os
import traceback
from collections import Counter

import adsk.core
import adsk.fusion

STEP = r'C:\repos-github\magewell-converter-cases\exports\pro-convert-for-ndi-to-hdmi\base_fan.step'
TARGET = r'C:\repos-github\magewell-converter-cases\exports\fusion-verify\target.txt'  # optional: another STEP to check
OUT = r'C:\repos-github\magewell-converter-cases\exports\fusion-verify'


def stl_edges(path):
    """(triangles, open edges, non-manifold edges) of a binary STL, vertices merged at 1e-5 mm."""
    import struct
    with open(path, 'rb') as f:
        data = f.read()
    n = struct.unpack_from('<I', data, 80)[0]
    keys, edges = {}, Counter()
    for i in range(n):
        off = 84 + i * 50 + 12
        v = struct.unpack_from('<9f', data, off)
        ids = []
        for k in range(3):
            key = tuple(round(c / 1e-5) for c in v[3 * k:3 * k + 3])
            ids.append(keys.setdefault(key, len(keys)))
        for a, b in ((ids[0], ids[1]), (ids[1], ids[2]), (ids[2], ids[0])):
            edges[(min(a, b), max(a, b))] += 1
    return n, sum(1 for c in edges.values() if c == 1), sum(1 for c in edges.values() if c > 2)


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    try:
        os.makedirs(OUT, exist_ok=True)
        step = open(TARGET, encoding='utf-8').read().strip() if os.path.isfile(TARGET) else STEP
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        doc.name = 'issue-119 check: ' + os.path.basename(step)
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent
        im = app.importManager
        im.importToTarget(im.createSTEPImportOptions(step), root)
        bodies = [b for b in root.bRepBodies] + [b for o in root.allOccurrences for b in o.component.bRepBodies]
        lines = [f'STEP: {os.path.basename(step)}', f'bodies: {len(bodies)}']
        for b in bodies:
            lines.append(f'  {b.name}: solid={b.isSolid}, shells={b.shells.count}, faces={b.faces.count}, '
                         f'volume={b.volume * 1000:.0f} mm3')
        em = design.exportManager
        stl = os.path.join(OUT, os.path.basename(step)[:-5] + '_from_fusion.stl')
        opts = em.createSTLExportOptions(root, stl)
        opts.isBinaryFormat = True
        opts.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
        em.execute(opts)
        n, open_e, nonman = stl_edges(stl)
        lines += ['', f'Fusion STL export: {n} triangles', f'open edges: {open_e}', f'non-manifold edges: {nonman}',
                  '', 'PASS' if (open_e == 0 and nonman == 0 and len(bodies) == 1) else 'FAIL', '', stl]
        with open(os.path.join(OUT, 'result.txt'), 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        app.activeViewport.fit()
        ui.messageBox('\n'.join(lines), 'Issue #119 check')
    except Exception:
        ui.messageBox('MccVerifyStep failed:\n' + traceback.format_exc())
