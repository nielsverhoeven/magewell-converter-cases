"""The document port: everything the runner needs from "a document". Two implementations exist:
FusionDocument (fusion_port.py, adsk) and RecordingDocument (recording.py, plain Python).
"""


class PortError(Exception):
    """A document operation failed (parameter not accepted, suppress failed, export failed, ...)."""


class DocumentPort:
    backend = "abstract"

    def info(self):
        """{"backend", "fusion_version", "python", "design_intent", "unsaved", "hub_version", "up_axis"}."""
        raise NotImplementedError

    def add_parameters(self, rows, texts):
        """Create the user parameters, in the given order. texts: {name: text}. Raises PortError."""
        raise NotImplementedError

    def modify_parameters(self, texts):
        """Set many user parameters in ONE all-or-none call. Raises PortError; then nothing changed."""
        raise NotImplementedError

    def set_suppressed(self, names, suppressed):
        """Suppress or unsuppress the timeline objects with these names in one call. Raises PortError."""
        raise NotImplementedError

    def compute(self):
        raise NotImplementedError

    def snapshot(self):
        """The plain-data picture of the document (schema in the plan, section 3.7)."""
        raise NotImplementedError

    def measure(self, component):
        """{"bbox": {"min","max","size"}, "volume_mm3", "area_mm2", "solids"} or None when the backend cannot."""
        raise NotImplementedError

    def export(self, component, fmt, path, settings):
        """Write one file. Returns the settings actually used (dict), or None when the backend cannot export."""
        raise NotImplementedError

    def export_archive(self, path):
        raise NotImplementedError

    def capture(self, path, view, width, height):
        raise NotImplementedError

    def close(self):
        """Close without saving. Must not raise."""
        raise NotImplementedError


class BuildContext:
    """What a builder entry point receives (contract C2)."""

    def __init__(self, backend, design, document, registry, values, options, log):
        self.backend, self.design, self.document = backend, design, document
        self.registry, self.values, self.options, self.log = registry, values, options, log
