# Shows every current design of the repository in Fusion: one new, unsaved document per case,
# per bracket and per coupon, built from the exact STEP exports in exports\ (local render or a CI run).
# Nothing is saved to the hub. Close the documents without saving when done.
import os
import traceback

import adsk.core
import adsk.fusion

EXPORTS = r'C:\repos-github\magewell-converter-cases\exports'


def targets():
    """(title, [(label, step path), ...]) per document, in a fixed order."""
    out = []
    for slug in sorted(os.listdir(EXPORTS)):
        d = os.path.join(EXPORTS, slug)
        if slug in ('brackets', 'coupons', 'fusion-verify') or not os.path.isdir(d):
            continue
        parts = [p for p in ('base', 'lid') if os.path.isfile(os.path.join(d, p + '.step'))]
        out.append((slug, [(f'{slug} {p}', os.path.join(d, p + '.step')) for p in parts]))
    for group in ('brackets', 'coupons'):
        g = os.path.join(EXPORTS, group)
        if not os.path.isdir(g):
            continue
        for name in sorted(os.listdir(g)):
            d = os.path.join(g, name)
            steps = sorted(f for f in os.listdir(d) if f.endswith('.step')) if os.path.isdir(d) else []
            if steps:
                out.append((name, [(f'{name} {f[:-5]}', os.path.join(d, f)) for f in steps]))
    return out


def run(context):
    app = adsk.core.Application.get()
    ui = app.userInterface
    shown, failed = 0, []
    try:
        im = app.importManager
        for title, parts in targets():
            try:
                app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
                design = adsk.fusion.Design.cast(app.activeProduct)
                root = design.rootComponent
                for label, path in parts:
                    im.importToTarget(im.createSTEPImportOptions(path), root)
                    try:
                        root.occurrences.item(root.occurrences.count - 1).component.name = label
                    except Exception:
                        pass
                app.activeViewport.fit()
                shown += 1
            except Exception:
                failed.append(title)
        msg = f'{shown} documents opened.'
        if failed:
            msg += '\nFailed: ' + ', '.join(failed)
        ui.messageBox(msg)
    except Exception:
        ui.messageBox('MccShowAll failed:\n' + traceback.format_exc())
