"""Input digest "sha256-lf-v1": one hash over the build-input files of a document.

Pure Python, standard library only. The digest does not depend on the operating system, the checkout path or
the line-end setting of git.
"""
import glob
import hashlib
import json
import os

ALGORITHM = "sha256-lf-v1"
_SKIP_DIRS = ("__pycache__",)
_SKIP_SUFFIXES = (".pyc", ".pyo")
_SKIP_PREFIXES = ("cad/fusion/replay/",)
# Inputs of every document, whatever its plan says: the runtime's own code and what the probe run taught.
# The runtime's test document and its tests are inputs of the test document's plan only, never of a product's.
MANDATORY = ("cad/fusion/runtime/**/*.py", "cad/fusion/runtime/fusion_facts.json")
_MANDATORY_SKIP = ("cad/fusion/runtime/testdoc/", "cad/fusion/runtime/tests/")


def _content(path):
    with open(path, "rb") as fh:
        data = fh.read()
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return data                                   # binary: hashed as it is
    return data.replace(b"\r\n", b"\n")               # text: CRLF and LF checkouts give the same digest


def _matches(checkout, pattern, skip=()):
    """POSIX-style relative paths of the files that one pattern matches, without the files no digest covers."""
    if os.path.isabs(pattern) or ".." in pattern.replace("\\", "/").split("/"):
        raise ValueError("input pattern must stay inside the checkout: %r" % pattern)
    for rel in glob.glob(pattern, root_dir=checkout, recursive=True):
        posix = rel.replace("\\", "/")
        if not os.path.isfile(os.path.join(checkout, rel)):
            continue
        if any(part in _SKIP_DIRS for part in posix.split("/")) or posix.endswith(_SKIP_SUFFIXES) \
                or posix.startswith(_SKIP_PREFIXES + tuple(skip)):
            continue
        yield posix


def input_files(checkout, patterns):
    """Sorted POSIX-style relative paths of all files matched by the glob patterns (relative to checkout), plus the
    mandatory runtime inputs."""
    found = set()
    for pattern in patterns:
        found.update(_matches(checkout, pattern))
    for pattern in MANDATORY:
        found.update(_matches(checkout, pattern, _MANDATORY_SKIP))
    return sorted(found)


def undeclared_modules(checkout, patterns, modules):
    """The files of loaded modules that lie under <checkout>/cad/ and are not among the input files: code that shaped
    a build but would not change its input digest. `modules` is a mapping like sys.modules; a module without a file,
    or from outside the checkout's cad package, is not the digest's business."""
    root = os.path.normcase(os.path.realpath(os.path.join(checkout, "cad"))) + os.sep
    declared = set(input_files(checkout, patterns))
    missing = set()
    for module in list(modules.values()):
        path = getattr(module, "__file__", None)
        if not isinstance(path, str):
            continue
        full = os.path.normcase(os.path.realpath(path))
        if full.startswith(root):
            rel = "cad/" + full[len(root):].replace(os.sep, "/")
            if rel not in declared:
                missing.add(rel)
    return sorted(missing)


def digest_files(checkout, patterns):
    files = input_files(checkout, patterns)
    if not files or not any(True for p in patterns for _ in _matches(checkout, p)):
        raise ValueError("no input file matches %r" % (patterns,))
    top = hashlib.sha256()
    for posix in files:
        h = hashlib.sha256(_content(os.path.join(checkout, *posix.split("/")))).hexdigest()
        top.update(("%s  %s\n" % (h, posix)).encode("utf-8"))
    return {"algorithm": ALGORITHM, "value": top.hexdigest(), "files": len(files)}


def input_digest(plan_path, root):
    """The input digest of one document: the files matched by the plan's "inputs", the plan file itself and the
    mandatory runtime inputs."""
    with open(plan_path, "r", encoding="utf-8") as fh:
        patterns = list(json.load(fh)["inputs"])
    rel = os.path.relpath(os.path.realpath(plan_path), os.path.realpath(root)).replace("\\", "/")
    return digest_files(root, sorted(set(patterns) | {rel}))
