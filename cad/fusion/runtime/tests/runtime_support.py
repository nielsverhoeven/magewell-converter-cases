"""Shared helpers of the runtime tests: a throw-away copy of the checkout, so that no test writes into the
working tree."""
import os
import shutil
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


def make_checkout(parent=None):
    """Copy what a Fusion job needs (the cad package files, the runtime, the client) into a new directory
    that looks like a git checkout. Returns its path."""
    parent = parent or tempfile.mkdtemp(prefix="mcc-runtime-")
    root = os.path.join(parent, "checkout")
    os.makedirs(os.path.join(root, ".git"))
    for rel in ("cad/__init__.py", "cad/fusion/__init__.py", "scripts/fusion_run.py"):
        target = os.path.join(root, *rel.split("/"))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        source = os.path.join(REPO, *rel.split("/"))
        if os.path.isfile(source):
            shutil.copyfile(source, target)
        else:
            open(target, "w").close()
    shutil.copytree(os.path.join(REPO, "cad", "fusion", "runtime"), os.path.join(root, "cad", "fusion", "runtime"),
                    ignore=shutil.ignore_patterns("__pycache__"))
    return root


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
