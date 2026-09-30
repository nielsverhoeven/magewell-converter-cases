"""Client of the Fusion runtime: queue a job, wait for its result, print it as JSON, return an exit code.

Standard library only.
One JSON document goes to stdout; everything else goes to stderr.

Exit codes: 0 ok | 1 the job failed (error, time-out or ok=false) | 2 usage | 3 host unavailable or disabled |
            4 not started in time | 5 no result in time | 6 rejected by the host | 7 protocol error

Examples (the same in Git Bash and PowerShell, because no JSON has to be quoted on the command line):
    python scripts/fusion_run.py status
    python scripts/fusion_run.py probe
    python scripts/fusion_run.py build cad/fusion/documents/mcc-case.json --timeout 1800
    python scripts/fusion_run.py call cad.fusion.gen.core.debug_sketch --arg size=12 --arg name=slot
    python scripts/fusion_run.py plan cad/fusion/documents/mcc-case.json          (no Fusion needed)
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKOUT = os.path.dirname(HERE)

EXIT_OK, EXIT_FAILED, EXIT_USAGE, EXIT_UNAVAILABLE, EXIT_NOT_STARTED, EXIT_NO_RESULT, EXIT_REJECTED, EXIT_PROTOCOL = \
    0, 1, 2, 3, 4, 5, 6, 7
GRACE_S = 15.0
SPIN_MODULE = "cad.fusion.runtime.probe.spin"
CORE_PROBES = "cad.fusion.runtime.probe.core_probes"
PROBE_FILES = "cad/fusion/gen/**/probes.py"


def eprint(*a):
    print(*a, file=sys.stderr, flush=True)


def pid_alive(pid):
    """True if a process with this id exists. Never use os.kill on Windows: it terminates the process."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        k32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        k32.CloseHandle.argtypes = (wintypes.HANDLE,)
        handle = k32.OpenProcess(0x1000, False, int(pid))          # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        try:
            code = wintypes.DWORD()
            return bool(k32.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259   # STILL_ACTIVE
        finally:
            k32.CloseHandle(handle)
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def live_session(hostlib, bridge):
    """The session of a running bridge add-in, or None."""
    session = hostlib.read_json(bridge.session_path)
    if not isinstance(session, dict) or session.get("protocol") != hostlib.PROTOCOL:
        return None
    return session if pid_alive(session.get("pid", -1)) else None


def git_info(checkout):
    def git(*args):
        try:
            p = subprocess.run(["git", "-C", checkout, *args], capture_output=True, text=True, timeout=20)
            return p.stdout.strip() if p.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None
    head, porcelain = git("rev-parse", "HEAD"), git("status", "--porcelain")
    return {"head": head, "dirty": None if porcelain is None else bool(porcelain)}


def probe_modules(checkout):
    """The runtime's own probes first, then every probes.py under cad/fusion/gen of the checkout, in path order."""
    found = glob.glob(PROBE_FILES, root_dir=checkout, recursive=True)
    return [CORE_PROBES] + sorted(f.replace("\\", "/")[:-3].replace("/", ".") for f in found)


def key_values(items):
    out = {}
    for item in items or []:
        key, sep, value = item.partition("=")
        if not sep:
            raise ValueError("expected key=value, got %r" % item)
        try:
            out[key] = json.loads(value)
        except ValueError:
            out[key] = value
    return out


def job_args_of(ns):
    args = {}
    if getattr(ns, "args_file", None):
        with open(ns.args_file, "r", encoding="utf-8") as fh:
            args.update(json.load(fh))
    if getattr(ns, "args", None):
        args.update(json.loads(sys.stdin.read() if ns.args == "-" else ns.args))
    args.update(key_values(getattr(ns, "arg", None)))
    return args


def submit(hostlib, bridge, kind, args, checkout, timeout_s, queue_timeout_s, mode):
    """Write one job into the inbox. Returns (exit code or None, job dict, session or None)."""
    if os.path.exists(bridge.disabled_path):
        eprint("the runtime is disabled (file DISABLED in %s); `fusion_run.py enable` removes it" % bridge.dir)
        return EXIT_UNAVAILABLE, None, None
    session = live_session(hostlib, bridge)
    if mode == "bridge" and session is None:
        eprint("no live bridge: the add-in MccFusionBridge is not running in Fusion")
        return EXIT_UNAVAILABLE, None, None
    use_bridge = session is not None and mode != "manual"
    bridge.ensure_dirs()
    job_id = hostlib.new_job_id()
    job = {"protocol": hostlib.PROTOCOL, "job_id": job_id, "kind": kind, "args": args, "checkout": checkout,
           "session_id": session["session_id"] if use_bridge else "manual",
           "token": session["token"] if use_bridge else "",
           "created_utc": hostlib.utc_iso(), "start_deadline_epoch": time.time() + queue_timeout_s,
           "timeout_s": timeout_s, "out_dir": os.path.join(checkout, "exports", "fusion", "jobs", job_id),
           "client": {"pid": os.getpid(), "git": git_info(checkout)}}
    hostlib.write_json_atomic(os.path.join(bridge.inbox, job_id + ".json"), job)
    if not use_bridge:
        eprint("queued %s for a manual run. In Fusion: Shift+S, row MccRun, click Run, answer Yes." % job_id)
    return None, job, session if use_bridge else None


def wait_for(hostlib, bridge, job_id, start_deadline, timeout_s, session):
    result_path = os.path.join(bridge.outbox, job_id + ".json")
    inbox_path = os.path.join(bridge.inbox, job_id + ".json")
    started = None
    while True:
        result = hostlib.read_json(result_path)
        if result is not None:
            try:
                os.remove(result_path)
            except OSError:
                pass
            return exit_code_of(result), result
        now = time.time()
        status = hostlib.read_json(bridge.status_path) or {}
        if started is None and (not os.path.exists(inbox_path)
                                or (status.get("state") == "running" and status.get("job_id") == job_id)):
            started = now                                 # taken from the inbox: it runs or is about to
        if started is None and now > start_deadline + GRACE_S:
            try:
                os.remove(inbox_path)                     # withdraw the job
            except OSError:
                pass
            eprint("the job was not started in time. Host status: %s" % json.dumps(status, sort_keys=True))
            return EXIT_NOT_STARTED, None
        if started is not None and now > started + timeout_s + GRACE_S:
            eprint("no result after the time-out plus %d s. Fusion may be inside a long or hung operation;" % GRACE_S)
            eprint("look at Fusion. Host status: %s" % json.dumps(status, sort_keys=True))
            return EXIT_NO_RESULT, None
        if session is not None and not pid_alive(session["pid"]):
            eprint("the Fusion process of the bridge session is gone")
            return EXIT_UNAVAILABLE, None
        time.sleep(0.2)


def exit_code_of(result):
    status = result.get("status")
    if status == "ok":
        value = result.get("result")
        return EXIT_FAILED if isinstance(value, dict) and value.get("ok") is False else EXIT_OK
    return {"error": EXIT_FAILED, "timeout": EXIT_FAILED, "rejected": EXIT_REJECTED}.get(status, EXIT_PROTOCOL)


def emit(obj, pretty):
    sys.stdout.write(json.dumps(obj, indent=1 if pretty else None, sort_keys=True, ensure_ascii=False) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="fusion_run.py")
    ap.add_argument("--bridge-dir", help=argparse.SUPPRESS)
    ap.add_argument("--checkout", help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def job_options(p):
        p.add_argument("--timeout", type=float, default=900.0, help="seconds the job may run inside Fusion")
        p.add_argument("--queue-timeout", type=float, default=3600.0, help="seconds to wait for the start")
        p.add_argument("--mode", choices=("auto", "bridge", "manual"), default="auto")
        p.add_argument("--no-wait", action="store_true", help="queue the job and return at once")
        p.add_argument("--keep-document", action="store_true", help="leave the job's document open in Fusion")
        p.add_argument("--backend", choices=("fusion", "recording"), default="fusion", help=argparse.SUPPRESS)
        p.add_argument("--pretty", action="store_true")

    p = sub.add_parser("call", help="call <module>.<entry>(job) inside Fusion; the module lies under cad/fusion")
    p.add_argument("module")
    p.add_argument("--entry", default="run")
    p.add_argument("--args", help="JSON object, or - for stdin")
    p.add_argument("--args-file")
    p.add_argument("--arg", action="append", help="key=value; the value is read as JSON when possible")
    job_options(p)
    p = sub.add_parser("build", help="build, apply and export one document plan inside Fusion")
    p.add_argument("plan")
    p.add_argument("--configurations", help="comma-separated configuration ids; default all")
    p.add_argument("--gates", choices=("enforce", "report"), default="enforce")
    p.add_argument("--option", action="append", help="key=value passed to the builder (ctx.options)")
    p.add_argument("--regression", action="store_true", help="second pass in reverse order, regression.txt")
    job_options(p)
    p = sub.add_parser("probe", help="run the live probes and the test document")
    p.add_argument("--probes", help="comma-separated modules; default: the runtime's probes and every "
                                    "cad/fusion/gen/**/probes.py")
    p.add_argument("--only", help="comma-separated probe ids")
    p.add_argument("--block-seconds", type=float, default=0.0)
    p.add_argument("--no-spin", action="store_true", help="skip the time-out probe P79.11")
    job_options(p)
    p = sub.add_parser("plan", help="run a document plan on the recording backend; no Fusion needed")
    p.add_argument("plan")
    p.add_argument("--write-inventory", action="store_true")
    p.add_argument("--pretty", action="store_true")
    p = sub.add_parser("digest", help="print the input digest of a document plan")
    p.add_argument("plan")
    sub.add_parser("status")
    sub.add_parser("disable")
    sub.add_parser("enable")
    p = sub.add_parser("wait", help="collect the result of a job that was queued with --no-wait")
    p.add_argument("job_id")
    p.add_argument("--timeout", type=float, default=900.0)
    p.add_argument("--pretty", action="store_true")
    try:
        ns = ap.parse_args(argv)
    except SystemExit as exc:
        return EXIT_OK if exc.code == 0 else EXIT_USAGE

    checkout = os.path.realpath(ns.checkout) if ns.checkout else CHECKOUT
    sys.path.insert(0, checkout)
    pretty = getattr(ns, "pretty", False)

    def rel_plan(path):
        rel = os.path.relpath(os.path.realpath(path), checkout).replace("\\", "/")
        if rel.startswith("..") or not os.path.isfile(os.path.join(checkout, *rel.split("/"))):
            raise ValueError("the plan %s is not a file inside the checkout %s" % (path, checkout))
        return rel

    try:
        if ns.cmd == "digest":
            from cad.fusion.runtime import digest
            emit(digest.input_digest(os.path.join(checkout, *rel_plan(ns.plan).split("/")), checkout), True)
            return EXIT_OK
        if ns.cmd == "plan":
            from cad.fusion.runtime import planrun
            rel = rel_plan(ns.plan)
            try:
                written = planrun.write_inventory(checkout, rel, log=eprint) if ns.write_inventory else None
                result = planrun.record(checkout, rel, client_git=git_info(checkout), log=eprint)
            except planrun.PlanRunError as exc:
                emit({"ok": False, "kind": "build", "result": "failed", "stage": exc.stage,
                      "violations": exc.violations}, pretty)
                return EXIT_FAILED
            result.pop("inventory_text", None)
            if written is not None:
                result["inventory_written"] = written["path"]
                eprint("wrote %s" % written["path"])
            emit(result, pretty)
            return EXIT_OK if result["ok"] else EXIT_FAILED
        try:
            from cad.fusion.runtime import hostlib
        except ModuleNotFoundError as exc:
            if exc.name != "cad.fusion.runtime.hostlib":
                raise
            eprint("this checkout has no host library (cad/fusion/runtime/hostlib.py): only `plan` and `digest` work")
            return EXIT_UNAVAILABLE
        bridge = hostlib.Bridge(ns.bridge_dir)
        if ns.cmd == "status":
            session = live_session(hostlib, bridge)
            out = {"bridge_dir": bridge.dir, "bridge_live": session is not None,
                   "disabled": os.path.exists(bridge.disabled_path), "pending": bridge.pending(),
                   "status": hostlib.read_json(bridge.status_path)}
            if session:
                out["session"] = {k: v for k, v in session.items() if k != "token"}
            emit(out, True)
            return EXIT_OK if session is not None else EXIT_UNAVAILABLE
        if ns.cmd == "disable":
            bridge.ensure_dirs()
            open(bridge.disabled_path, "w").close()
            return EXIT_OK
        if ns.cmd == "enable":
            if os.path.exists(bridge.disabled_path):
                os.remove(bridge.disabled_path)
            return EXIT_OK
        if ns.cmd == "wait":
            code, result = wait_for(hostlib, bridge, ns.job_id, time.time(), ns.timeout, None)
            if result is not None:
                emit(result, pretty)
            return code

        common = {"backend": ns.backend} if ns.backend != "fusion" else {}
        if ns.keep_document:
            common["keep_documents"] = True
        if ns.cmd == "call":
            kind, args = "call", dict(common, module=ns.module, entry=ns.entry, args=job_args_of(ns))
        elif ns.cmd == "build":
            kind, args = "build", dict(common, plan=rel_plan(ns.plan), gates=ns.gates,
                                       options=key_values(ns.option), regression=ns.regression,
                                       configurations=ns.configurations.split(",") if ns.configurations else None)
        else:
            kind, args = "probe", dict(common, block_seconds=ns.block_seconds,
                                       probes=ns.probes.split(",") if ns.probes else probe_modules(checkout),
                                       only=ns.only.split(",") if ns.only else None)
    except (ValueError, OSError) as exc:
        eprint("usage error: %s" % exc)
        return EXIT_USAGE

    spin = None
    if ns.cmd == "probe" and not ns.no_spin:              # P79.11: an endless Python loop must be stopped
        code, spin, _ = submit(hostlib, bridge, "call", dict(common, module=SPIN_MODULE, entry="run", args={}),
                               checkout, 3.0, ns.queue_timeout, ns.mode)
        if code is not None:
            return code
    code, job, session = submit(hostlib, bridge, kind, args, checkout, ns.timeout, ns.queue_timeout, ns.mode)
    if code is not None:
        return code
    if ns.no_wait:
        emit({"job_id": job["job_id"], "queued": True, "mode": "bridge" if session else "manual",
              "also_queued": spin["job_id"] if spin else None}, pretty)
        return EXIT_OK
    spin_result = None
    if spin is not None:
        _, spin_result = wait_for(hostlib, bridge, spin["job_id"], spin["start_deadline_epoch"], 3.0, session)
    code, result = wait_for(hostlib, bridge, job["job_id"], job["start_deadline_epoch"], ns.timeout, session)
    if result is not None:
        if spin is not None:
            stopped = spin_result is not None and spin_result.get("status") == "timeout"
            result["P79.11"] = {"title": "An endless Python loop is stopped at the job's time-out",
                                "status": "pass" if stopped else "fail",
                                "observed": spin_result.get("status") if spin_result else None}
            if not stopped and code == EXIT_OK:
                code = EXIT_FAILED
        emit(result, pretty)
    return code


if __name__ == "__main__":
    sys.exit(main())
