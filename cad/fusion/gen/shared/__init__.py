# Shared builders (layer R1): the decorator `shared` that records a builder's call, and one module per builder family.
"""Shared builders of the Fusion modelling kit (issue #81, plan 3.10, verdict A6 and A8).

A shared builder is a function whose first argument is the ``Component``.  It calls the facade only, with parameter-name
expressions, and imports the standard library and ``cad.fusion.gen.core`` only.  The decorator ``shared(builder_id,
placement)`` opens ``comp.shared_call(builder_id, arguments, placement)`` around the call, so that the build record says which
builder produced which names with which arguments (CK10 compares the arguments that are not placement, CK11 the owners).
"""
from __future__ import annotations

import functools

# Not recorded as arguments of a call: the identity of the instance (CK10 never compares it) is passed positionally.
_IDENTITY = ("name", "set_name")


def shared(builder_id, placement=()):
    """Decorator: record the call of a shared builder.  ``builder_id`` is ``module.function``; ``placement`` lists the
    keyword arguments that may differ between documents.  The recorded ``arguments`` are the keyword arguments of the call."""
    placement = tuple(placement)

    def wrap(builder):
        @functools.wraps(builder)
        def call(comp, *args, **kwargs):
            arguments = {k: v for k, v in kwargs.items() if k not in _IDENTITY}
            with comp.shared_call(builder_id, arguments, placement):
                return builder(comp, *args, **kwargs)

        return call

    return wrap
