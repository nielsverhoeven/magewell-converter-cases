"""Application level: host facts, Z-up refusal, a new unsaved document, the modal guard, clean-up after a job.

Imports adsk, so it loads only inside Fusion.
"""
import contextlib
import sys

import adsk.core
import adsk.fusion

MODAL_METHODS = ("messageBox", "inputBox", "selectEntity", "createFileDialog", "createFolderDialog",
                 "createCloudFileDialog", "createCloudFolderDialog", "createProgressDialog")


class FrameError(RuntimeError):
    pass


class ModalBlocked(RuntimeError):
    pass


def app():
    return adsk.core.Application.get()


def is_z_up():
    prefs = app().preferences.generalPreferences
    return prefs.defaultModelingOrientation == adsk.core.DefaultModelingOrientations.ZUpModelingOrientation


def require_z_up():
    if not is_z_up():
        raise FrameError("Fusion's default modelling orientation is not Z up. Set Preferences > General > "
                         "Default modeling orientation to Z up, restart Fusion and run the job again.")


def host_facts():
    a = app()
    return {"fusion_version": a.version, "python": sys.version.split()[0], "up_axis": "Z" if is_z_up() else "Y",
            "open_documents": a.documents.count}


@contextlib.contextmanager
def modal_guard():
    """While active, every dialog method of UserInterface raises ModalBlocked instead of blocking Fusion."""
    cls, saved = adsk.core.UserInterface, {}

    def blocked(name):
        def raiser(self, *args, **kwargs):
            raise ModalBlocked("UserInterface.%s is not allowed inside a job" % name)
        return raiser
    for name in MODAL_METHODS:
        saved[name] = getattr(cls, name)
        setattr(cls, name, blocked(name))
    try:
        yield
    finally:
        for name, original in saved.items():
            setattr(cls, name, original)


def _open_documents(a):
    docs = a.documents
    return [docs.item(i) for i in range(docs.count)]


class Session:
    """One job's view of Fusion. Leaves every document that was open before the job exactly as it was."""

    def __init__(self, keep_documents=False):
        self.keep_documents = keep_documents
        self.previous, self.before, self.report = None, set(), {"closed": 0, "kept": 0, "restored": False}
        self._guard = None

    def __enter__(self):
        a = app()
        self.previous = a.activeDocument
        self.before = {d.creationId for d in _open_documents(a)}
        self._guard = modal_guard()
        self._guard.__enter__()
        return self

    def new_document(self, name):
        """A new, unsaved, parametric design in millimetres. Returns (document, design)."""
        require_z_up()
        doc = app().documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        if design is None:
            raise RuntimeError("the new document has no design product")
        if design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        design.fusionUnitsManager.distanceDisplayUnits = adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        doc.name = name
        return doc, design

    def __exit__(self, exc_type, exc, tb):
        self._guard.__exit__(None, None, None)
        a = app()
        for doc in _open_documents(a):
            if doc.creationId in self.before:
                continue
            if self.keep_documents:
                self.report["kept"] += 1
                continue
            try:
                if doc.close(False):                 # False: close without saving and without a prompt
                    self.report["closed"] += 1
            except RuntimeError:
                pass
        try:
            if self.previous is not None and self.previous.isValid and not self.previous.isActive:
                self.previous.activate()
            self.report["restored"] = True
        except RuntimeError:
            pass
        return False
