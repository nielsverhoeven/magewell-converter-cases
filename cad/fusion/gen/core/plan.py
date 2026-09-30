"""The command line of the Fusion modelling kit (issue #81, plan sections 3.9 and 3.13, verdict amendments A6 and A7).

Run at the repository root::

    python -m cad.fusion.gen.core.plan --document PLANFILE --check [--stage K] [--record PATH]
    python -m cad.fusion.gen.core.plan --definitions PLANFILE [PLANFILE ...]

It reads a document plan (contract C3 of #79) without the runtime, builds the document once on the recording
backend and runs the checks of ``checks.py`` over the build record.  Exit code 0: no finding.  1: a finding, or a
builder that raises ``KitError``.  2: an unusable plan or command line.

It writes only under ``build/`` (``--record``) and imports nothing from ``cad.fusion.runtime``: a committed
inventory has one writer, ``scripts/fusion_run.py plan PLANFILE --write-inventory`` (verdict A7).  Standard
library only; ``cad.params`` is imported inside the functions that read the registry.
"""
from __future__ import annotations

import argparse
import glob
import importlib
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

from . import checks, facade
from .names import KitError

TEST_MODULE_PREFIX = "cad.fusion.gen.tests."


class PlanError(Exception):
    """A plan or an option that cannot be used."""


# ---- reading a plan ---------------------------------------------------------------------------------------------------


def load_plan(path) -> dict:
    """The plan file as a dict, with the path as given (forward slashes) under the private key ``_path``."""
    try:
        plan = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PlanError(f"{path}: cannot read the plan: {exc}") from None
    if not isinstance(plan, dict):
        raise PlanError(f"{path}: a plan is a JSON object")
    plan["_path"] = str(path).replace("\\", "/")
    return plan


def _need(plan: dict, *keys):
    node = plan
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            raise PlanError(f"{plan.get('_path', 'plan')}: the key {'.'.join(keys)!r} is missing")
        node = node[key]
    return node


def is_test_document(plan: dict) -> bool:
    """A test document: its builder module lies under ``cad.fusion.gen.tests`` (exempt from CK10)."""
    return str(_need(plan, "builder", "module")).startswith(TEST_MODULE_PREFIX)


def _stage(text: str):
    return int(text) if text.lstrip("-").isdigit() else text


def _read_inputs(plan: dict):
    """``(registry rows, {configuration id: parameter set})`` of a plan, through ``cad.params``."""
    from cad import params  # inside the body: the rest of this module runs without it

    source = _need(plan, "registry", "source")
    if source != "cad.params":
        raise PlanError(f"{plan['_path']}: registry.source is {source!r}; the kit reads plans with the source 'cad.params' only")
    csv_files = list(_need(plan, "registry", "csv"))
    set_files = sorted({f for pattern in _need(plan, "registry", "sets") for f in glob.glob(pattern, recursive=True)})
    try:
        rows = params.registry(csv_files, set_files)
        sets = {}
        for cfg in _need(plan, "configurations"):
            one = _need(cfg, "set")
            sets[_need(cfg, "id")] = params.parameter_set(_need(one, "file"), one.get("config", "default"))
    except (OSError, ValueError, KeyError) as exc:
        raise PlanError(f"{plan['_path']}: cannot read the registry or a parameter set: {exc}") from None
    return rows, sets


def build(plan: dict, stage=None):
    """Build the document once on the recording backend.  Returns ``(record, rows, sets)``; the record carries the
    keys ``plan`` and ``options`` besides the keys of ``RecordingBackend.build_record``."""
    rows, sets = _read_inputs(plan)
    build_id = _need(plan, "build_configuration")
    if build_id not in sets:
        raise PlanError(f"{plan['_path']}: build_configuration {build_id!r} is not one of the configurations")
    module = _need(plan, "builder", "module")  # also proves that builder is an object
    builder = plan["builder"]
    options = dict(builder.get("options", {}))
    if stage is not None:
        options["stage"] = stage
    ctx = SimpleNamespace(backend="recording", design=None, document=_need(plan, "document"), registry=rows,
                          values=sets[build_id]["values"], options=options, log=print)
    try:
        entry = getattr(importlib.import_module(module), builder.get("entry", "build"))
    except (ImportError, AttributeError) as exc:
        raise PlanError(f"{plan['_path']}: cannot import the builder entry: {exc}") from None
    made = []
    original = facade.Kit.__init__

    def recording_init(self, context):  # how the command reaches the Kit the builder creates
        original(self, context)
        made.append(self)

    facade.Kit.__init__ = recording_init
    try:
        entry(ctx)
    finally:
        facade.Kit.__init__ = original
    if len(made) != 1:
        raise PlanError(f"{plan['_path']}: the builder created {len(made)} Kit objects; a document has exactly one")
    record = made[0]._backend.build_record()
    record["plan"] = plan["_path"]
    record["options"] = options
    return record, rows, sets


# ---- the commands -----------------------------------------------------------------------------------------------------


def _write_record(record: dict, path: str) -> None:
    target, root = Path(os.path.abspath(path)), Path(os.path.abspath("build"))
    if root != target and root not in target.parents:
        raise PlanError(f"--record {path}: the kit writes only under build/")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")


def _report(findings) -> int:
    for finding in findings:
        print(finding)
    return 1 if findings else 0


def _document(args) -> int:
    plan = load_plan(args.document)
    record, rows, sets = build(plan, args.stage)
    if args.record:
        _write_record(record, args.record)
    if not args.check:
        print(f"{record['document']}: recorded {len(record['specs'])} specs and {len(record['shared_calls'])} shared calls")
        return 0
    findings = checks.run(record, rows, sets, _exceptions(plan), owners=plan.get("owners"),
                          protected_prefixes=plan.get("protected_prefixes", ()))
    code = _report(findings)
    if not code:
        print(f"{record['document']}: no findings ({len(record['specs'])} specs, {len(record['shared_calls'])} shared calls)")
    return code


def _exceptions(plan: dict) -> list:
    entries = plan.get("shared_exceptions", [])
    try:
        checks.exception_pairs(entries)
    except KitError as exc:
        raise PlanError(f"{plan['_path']}: {exc}") from None
    return list(entries)


def _definitions(args) -> int:
    records, exceptions = [], []
    for path in args.definitions:
        plan = load_plan(path)
        if is_test_document(plan):
            continue
        exceptions += _exceptions(plan)
        records.append(build(plan)[0])
    code = _report(checks.definitions(records, exceptions))
    if not code:
        print(f"definitions: equal in {len(records)} product document(s)")
    return code


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m cad.fusion.gen.core.plan", description=__doc__.split("\n\n")[0])
    parser.add_argument("--document", metavar="PLANFILE", help="build this document plan on the recording backend")
    parser.add_argument("--check", action="store_true", help="with --document: run the checks, exit 1 on a finding")
    parser.add_argument("--stage", type=_stage, metavar="K", help="with --document: options['stage'] of the build")
    parser.add_argument("--record", metavar="PATH", help="with --document: write the build record (only under build/)")
    parser.add_argument("--definitions", nargs="*", metavar="PLANFILE", help="CK10 over the product documents of these plans")
    args = parser.parse_args(argv)
    if (args.document is None) == (args.definitions is None):
        parser.error("exactly one of --document and --definitions")
    if args.definitions is not None and (args.check or args.record or args.stage is not None):
        parser.error("--check, --record and --stage go with --document")
    try:
        return _document(args) if args.document is not None else _definitions(args)
    except PlanError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KitError as exc:
        print(f"error: the builder raised {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
