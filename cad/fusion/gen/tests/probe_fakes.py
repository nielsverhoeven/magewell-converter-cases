"""A permissive stand-in for ``adsk`` and for the ``env`` of the runtime's probe job (plan K5b).

``Auto`` answers every attribute with another ``Auto``, every call with one, and behaves as the number 1.0 where a
number is needed (``range(x.count)``, ``float(v.x)``, ``a - b``).  That is enough to run each probe function from
the first line to the last without Fusion: the kit's backend fails at its first sketch (an ``Auto`` axis is not along
a model axis), the probe records that as its answer and goes on, so every branch of a probe's bookkeeping runs.  It
proves that a record is well formed; it says nothing about what Fusion does, which is what the live run is for.

``Auto`` objects are stateful (an attribute that was read or set keeps its value) and ``Occurrences`` is a real list,
because a probe finds its components again by name.
"""
from __future__ import annotations

import contextlib
import sys
import types


class Auto:
    def __init__(self, name="auto"):
        self.__dict__["_name"] = name

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        child = "adsk::fusion::ModelParameter" if name == "objectType" else Auto(f"{self._name}.{name}")
        self.__dict__[name] = child
        return child

    def __call__(self, *args, **kwargs):
        if "_ret" not in self.__dict__:
            self.__dict__["_ret"] = Auto(f"{self._name}()")
        return self.__dict__["_ret"]

    def __iter__(self):
        return iter([Auto(f"{self._name}[0]")])

    def __getitem__(self, key):
        return Auto(f"{self._name}[{key}]")

    def __len__(self):
        return 1

    def __bool__(self):
        return True

    def __float__(self):
        return 1.0

    def __int__(self):
        return 1

    def __index__(self):
        return 1

    def __str__(self):
        return f"<{self._name}>"

    __repr__ = __str__

    def __abs__(self):
        return 1.0

    def __neg__(self):
        return -1.0

    def __round__(self, digits=None):
        return 1.0

    def __add__(self, other):
        return 1.0

    __radd__ = __sub__ = __rsub__ = __mul__ = __rmul__ = __truediv__ = __rtruediv__ = __add__

    def __lt__(self, other):
        return 1.0 < float(other)

    def __le__(self, other):
        return 1.0 <= float(other)

    def __gt__(self, other):
        return 1.0 > float(other)

    def __ge__(self, other):
        return 1.0 >= float(other)


class Occurrences:
    """``addNewComponent`` makes an occurrence with a component; ``count`` and ``item`` read them back."""

    def __init__(self):
        self.items = []

    def addNewComponent(self, matrix):
        occurrence = Auto("occurrence")
        occurrence.component = Auto("component")
        self.items.append(occurrence)
        return occurrence

    @property
    def count(self):
        return len(self.items)

    def item(self, i):
        return self.items[i]


class AutoDesign(Auto):
    def __init__(self):
        super().__init__("design")
        root = Auto("root")
        root.occurrences = Occurrences()
        self.rootComponent = root


class AutoModule(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        child = Auto(f"{self.__name__}.{name}")
        setattr(self, name, child)
        return child


def make_env(designs=None):
    """The ``env`` of contract C6: ``app``, ``ui``, ``new_design(name)``, ``out_dir``, ``log(text)``, ``cache``."""
    opened = designs if designs is not None else []

    def new_design(name):
        design = AutoDesign()
        opened.append((name, design))
        return design

    return types.SimpleNamespace(app=types.SimpleNamespace(fontNames=["Arial", "Segoe UI"]), ui=Auto("ui"), new_design=new_design,
                                 out_dir=".", log=lambda text: None, cache={}, job={}, args={}, checkout=".")


@contextlib.contextmanager
def installed(*dependents):
    """``adsk``, ``adsk.core`` and ``adsk.fusion`` as ``AutoModule`` in ``sys.modules``; ``dependents`` (dotted module
    names that import them) are dropped on the way in and out, with the attribute their package holds."""
    core, fusion = AutoModule("adsk.core"), AutoModule("adsk.fusion")
    adsk = AutoModule("adsk")
    adsk.core, adsk.fusion = core, fusion
    fakes = {"adsk": adsk, "adsk.core": core, "adsk.fusion": fusion}
    saved = {name: sys.modules.get(name) for name in (*fakes, *dependents)}
    sys.modules.update(fakes)
    for name in dependents:
        sys.modules.pop(name, None)
    try:
        yield
    finally:
        for name in dependents:
            sys.modules.pop(name, None)
            parent, _, leaf = name.rpartition(".")
            if parent in sys.modules and hasattr(sys.modules[parent], leaf):
                delattr(sys.modules[parent], leaf)
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
