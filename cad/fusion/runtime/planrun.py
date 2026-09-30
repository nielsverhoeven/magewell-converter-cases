"""Offline run of a document plan on the recording backend.

It is the engine of `fusion_run.py plan`, the only writer of a committed inventory, and the freshness check
that tests of the builders call. Pure Python, standard library only; it needs no Fusion.
"""
import os

from . import inventory, plan as planmod, registry, runner

RUN_ID = "offline"


class PlanRunError(Exception):
    def __init__(self, stage, violations):
        Exception.__init__(self, "%s: %s" % (stage, "; ".join(violations) or "failed"))
        self.stage, self.violations = stage, list(violations)


def record(checkout, plan_rel, *, gates="enforce", committed="check", client_git=None, log=None):
    """Builder, every parameter set and the gates, without Fusion. Returns the runner's result.

    With result "recorded" it carries "inventory_text": the recorded inventory in the committed layout.
    `committed="ignore"` leaves the committed inventory out of the gates. Raises PlanRunError("plan", ...) when the
    plan file itself is not valid."""
    registry.reset()                 # no parameter data cached by an earlier run in this process
    job = {"kind": "build", "job_id": RUN_ID, "checkout": checkout,
           "args": {"plan": plan_rel, "backend": "recording", "gates": gates},
           "client": {"git": client_git}, "host": {"mode": "offline"}}
    try:
        return runner.run_build(job, None, log=log or (lambda text: None), committed=committed)
    except planmod.PlanError as exc:
        raise PlanRunError("plan", [str(exc)])


def _target(checkout, plan_rel):
    try:
        plan = planmod.load(checkout, plan_rel)
    except planmod.PlanError as exc:
        raise PlanRunError("plan", [str(exc)])
    rel = plan.get("inventory")
    return plan, rel, os.path.join(checkout, *rel.split("/")) if rel else None


def inventory_status(checkout, plan_rel, *, log=None):
    """Is the committed inventory of this plan what its builder records today?

    Returns {"plan", "document", "path", "exists", "fresh", "recorded_sha256", "committed_sha256", "diff"}.
    "fresh" is True only when the file exists and has the recorded hash; "diff" holds at most 50 readable
    lines. Raises PlanRunError when the plan cannot be recorded at all (registry, sets or builder)."""
    plan, rel, full = _target(checkout, plan_rel)
    result = record(checkout, plan_rel, gates="report", committed="ignore", log=log)
    if result["result"] != "recorded":
        raise PlanRunError(result.get("stage") or "record", result.get("violations") or [])
    status = {"plan": plan_rel, "document": plan["document"], "path": rel,
              "exists": bool(full and os.path.isfile(full)), "fresh": False,
              "recorded_sha256": result["inventory_sha256"], "committed_sha256": None, "diff": []}
    if status["exists"]:
        try:
            with open(full, "r", encoding="utf-8") as fh:
                committed = inventory.loads(fh.read())
        except ValueError as exc:
            status["diff"] = ["the committed file is not a valid inventory: %s" % exc]
            return status
        status["committed_sha256"] = inventory.inventory_hash(committed)
        status["fresh"] = status["committed_sha256"] == status["recorded_sha256"]
        if not status["fresh"]:
            status["diff"] = inventory.diff(committed, inventory.loads(result["inventory_text"]))[:50]
    return status


def write_inventory(checkout, plan_rel, *, log=None):
    """Write the inventory file that the plan names. This is the only writer of a committed inventory.

    Refuses (PlanRunError) a plan that names no file and a plan whose recording run fails a gate.
    Returns inventory_status() of the written file."""
    plan, rel, full = _target(checkout, plan_rel)
    if not rel:
        raise PlanRunError("inventory", ["the plan names no inventory file"])
    result = record(checkout, plan_rel, gates="enforce", committed="ignore", log=log)
    if not result["ok"]:
        raise PlanRunError(result.get("stage") or "record", result.get("violations") or [])
    os.makedirs(os.path.dirname(full), exist_ok=True)
    tmp = full + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(result["inventory_text"])
    os.replace(tmp, full)
    return inventory_status(checkout, plan_rel, log=log)
