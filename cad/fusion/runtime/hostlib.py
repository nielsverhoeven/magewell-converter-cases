"""Host library of the Fusion runtime: file queue, job validation, executor, bridge loop, manual run.

Pure Python, standard library only. No adsk import: everything Fusion-specific is behind a `host` object
that the two shims (host/MccRun, host/MccFusionBridge) provide. One file on purpose: the shims load it
by path under a private module name, so it must not import sibling modules.

Consent: the script asks once for the whole batch it is about to run; the add-in asks for every job until the user
allows unattended runs, and that permission covers `build` and `probe` jobs only: a `call` job always asks. Every
question shows the kind, the plan or module, the checkout and whether the checkout is dirty.

Threads:
  main thread   Fusion's main thread. run_pending() and BridgeRuntime.on_main_thread() run here.
  worker        BridgeRuntime._worker_loop(): polls the inbox, writes the heartbeat, calls host.fire().
                It never touches the Fusion API except through host.fire() (Application.fireCustomEvent).
  watchdog      alive only while a job runs; raises JobTimeout in the main thread.
"""
import contextlib
import ctypes
import hashlib
import hmac
import importlib
import io
import json
import os
import re
import secrets
import sys
import threading
import time
import traceback
import uuid

PROTOCOL = 1
HOSTLIB_VERSION = "1.0.0"
BRIDGE_DIRNAME = "MccFusionBridge"
EVENT_ID = "MccFusionBridge.JobEvent"
RUNNER_MODULE = "cad.fusion.runtime.runner"
REPLAY_MODULE = "cad.fusion.replay"
KINDS = ("build", "probe", "call")
MAX_JOB_BYTES = 256 * 1024
MAX_CAPTURE_CHARS = 1_000_000
MAX_TIMEOUT_S = 3600.0
JOB_ID_RE = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$")
MODULE_RE = re.compile(r"^cad\.fusion(\.[A-Za-z_][A-Za-z0-9_]*)+$")
ENTRY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
POLL_S, HEARTBEAT_S, REFIRE_S = 0.25, 1.0, 2.0


# ---------------------------------------------------------------------------- files
def bridge_dir():
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        base = os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, BRIDGE_DIRNAME)


def utc_iso(epoch=None):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() if epoch is None else epoch))


def new_job_id():
    return "%s-%s" % (time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()), secrets.token_hex(4))


def read_json(path, retries=20, delay=0.025):
    """Read a JSON file that another process replaces atomically. None when it does not exist."""
    last = None
    for _ in range(retries):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except FileNotFoundError:
            return None
        except (PermissionError, json.JSONDecodeError) as exc:
            last = exc
            time.sleep(delay)
    raise last


def write_json_atomic(path, obj, retries=40, delay=0.025):
    tmp = "%s.tmp.%d.%s" % (path, os.getpid(), uuid.uuid4().hex[:6])
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    last = None
    for _ in range(retries):
        try:
            os.replace(tmp, path)
            return
        except PermissionError as exc:            # Windows: a reader has the destination open
            last = exc
            time.sleep(delay)
    try:
        os.remove(tmp)
    except OSError:
        pass
    raise last


def is_within(path, root):
    p = os.path.normcase(os.path.realpath(path))
    r = os.path.normcase(os.path.realpath(root))
    try:
        return os.path.commonpath([p, r]) == r
    except ValueError:                             # different drives
        return False


def find_checkout(path):
    """Nearest directory at or above `path` that has a `.git` entry (a directory, or a file in a worktree)."""
    d = os.path.realpath(path)
    if not os.path.isdir(d):
        d = os.path.dirname(d)
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def is_worktree_of(checkout, host_checkout):
    """True for the host checkout itself and for a linked worktree of it: a directory whose `.git` file points into
    `<host checkout>/.git/worktrees/`. Any other git directory below the host checkout is a foreign repository."""
    if os.path.normcase(os.path.realpath(checkout)) == os.path.normcase(os.path.realpath(host_checkout)):
        return True
    pointer = os.path.join(checkout, ".git")
    if not os.path.isfile(pointer):
        return False
    try:
        with open(pointer, "r", encoding="utf-8") as fh:
            first = fh.readline().strip()
    except OSError:
        return False
    if not first.startswith("gitdir:"):
        return False
    gitdir = first[len("gitdir:"):].strip()
    if not os.path.isabs(gitdir):
        gitdir = os.path.join(checkout, gitdir)
    return is_within(gitdir, os.path.join(host_checkout, ".git", "worktrees"))


class Reject(Exception):
    def __init__(self, reason, detail=""):
        Exception.__init__(self, reason)
        self.reason, self.detail = reason, detail


# ---------------------------------------------------------------------------- bridge directory
class Bridge:
    """Directory layout, session, status, log and job validation."""

    def __init__(self, directory=None):
        self.dir = directory or bridge_dir()
        self.inbox = os.path.join(self.dir, "inbox")
        self.outbox = os.path.join(self.dir, "outbox")
        self.logdir = os.path.join(self.dir, "log")
        self.session_path = os.path.join(self.dir, "session.json")
        self.status_path = os.path.join(self.dir, "status.json")
        self.disabled_path = os.path.join(self.dir, "DISABLED")
        self.lock_path = os.path.join(self.dir, "client.lock")
        self.session = None

    def ensure_dirs(self):
        for d in (self.inbox, self.outbox, self.logdir):
            os.makedirs(d, exist_ok=True)

    def open_session(self, mode, host_checkout, host_info):
        """mode: 'bridge' (add-in; a token and a session id are published) or 'manual' (script; nothing published)."""
        if host_checkout is None or not os.path.isdir(host_checkout):
            raise RuntimeError("the host is not inside a git checkout")
        self.ensure_dirs()
        self.session = {"protocol": PROTOCOL, "mode": mode, "pid": os.getpid(), "started_utc": utc_iso(),
                        "session_id": uuid.uuid4().hex if mode == "bridge" else "manual",
                        "token": secrets.token_hex(32) if mode == "bridge" else "",
                        "checkout": os.path.realpath(host_checkout), "hostlib_version": HOSTLIB_VERSION,
                        "host": host_info}
        if mode == "bridge":
            for name in self.pending():            # a job of an earlier session never runs
                if (self._peek(name) or {}).get("session_id") != "manual":
                    self.reject(name, "stale_session")
            write_json_atomic(self.session_path, self.session)
        return self.session

    def close_session(self):
        if self.session and self.session["mode"] == "bridge":
            try:
                os.remove(self.session_path)
            except OSError:
                pass
        self.session = None

    def write_status(self, **fields):
        st = {"protocol": PROTOCOL, "pid": os.getpid(), "heartbeat_epoch": time.time(), "heartbeat_utc": utc_iso(),
              "session_id": self.session["session_id"] if self.session else None}
        st.update(fields)
        try:
            write_json_atomic(self.status_path, st, retries=4)
        except OSError:
            pass                                    # a heartbeat may be skipped

    def log(self, event, **fields):
        rec = {"utc": utc_iso(), "event": event}
        rec.update(fields)
        path = os.path.join(self.logdir, "bridge.log")
        try:
            if os.path.exists(path) and os.path.getsize(path) > 5 * 1024 * 1024:
                os.replace(path, path + ".1")
            with open(path, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def pending(self):
        try:
            names = [n for n in os.listdir(self.inbox) if n.endswith(".json")]
        except OSError:
            return []
        return sorted(names)                       # a job id starts with its UTC time stamp

    def _peek(self, name):
        try:
            job = read_json(os.path.join(self.inbox, name))
        except Exception:
            return None
        return job if isinstance(job, dict) else None

    def load_job(self, name):
        """Parse and validate one inbox file against the open session. Returns the job dict. Raises Reject."""
        path = os.path.join(self.inbox, name)
        try:
            if os.path.getsize(path) > MAX_JOB_BYTES:
                raise Reject("bad_json", "job file too large")
            job = read_json(path)
        except Reject:
            raise
        except Exception as exc:
            raise Reject("bad_json", repr(exc))
        if not isinstance(job, dict):
            raise Reject("bad_json", "not an object")
        if job.get("protocol") != PROTOCOL:
            raise Reject("protocol_mismatch", "job %r, host %r" % (job.get("protocol"), PROTOCOL))
        job_id = job.get("job_id")
        if not isinstance(job_id, str) or not JOB_ID_RE.match(job_id) or job_id + ".json" != name:
            raise Reject("bad_job_id", str(job_id))
        ses = self.session
        if job.get("session_id") != ses["session_id"]:
            raise Reject("wrong_session", "job is for %r, host session is %r" % (job.get("session_id"), ses["mode"]))
        if ses["mode"] == "bridge" and not hmac.compare_digest(str(job.get("token", "")).encode(),
                                                                 ses["token"].encode()):
            raise Reject("bad_token")
        if os.path.exists(self.disabled_path):
            raise Reject("disabled")
        deadline = job.get("start_deadline_epoch")
        if not isinstance(deadline, (int, float)) or time.time() > deadline:
            raise Reject("start_deadline_passed")
        t = job.get("timeout_s")
        if isinstance(t, bool) or not isinstance(t, (int, float)) or not (0 < t <= MAX_TIMEOUT_S):
            raise Reject("bad_timeout", str(t))
        if job.get("kind") not in KINDS:
            raise Reject("bad_kind", str(job.get("kind")))
        if not isinstance(job.get("args"), dict):
            raise Reject("bad_args")
        checkout = job.get("checkout")
        if not isinstance(checkout, str) or not os.path.isabs(checkout) or not os.path.isdir(checkout):
            raise Reject("bad_checkout", str(checkout))
        checkout = os.path.realpath(checkout)
        if find_checkout(checkout) != checkout:
            raise Reject("bad_checkout", "not the root of a git checkout: %s" % checkout)
        if not is_within(checkout, ses["checkout"]):
            raise Reject("checkout_outside_allowed_root", checkout)
        if not is_worktree_of(checkout, ses["checkout"]):
            raise Reject("checkout_not_a_worktree", checkout)
        runner = os.path.join(checkout, *RUNNER_MODULE.split(".")) + ".py"
        if not os.path.isfile(runner):
            raise Reject("no_runner", runner)
        if job["kind"] == "call":
            modules = [job["args"].get("module")]
        elif job["kind"] == "probe":
            modules = job["args"].get("probes") or []
            if not isinstance(modules, list):
                raise Reject("bad_args", "probes must be a list of module names")
        else:
            modules = []
        for module in modules:
            if not isinstance(module, str) or not MODULE_RE.match(module):
                raise Reject("module_outside_cad_fusion", str(module))
            if module == REPLAY_MODULE or module.startswith(REPLAY_MODULE + "."):
                raise Reject("module_not_allowed", module)
            if not os.path.isfile(os.path.join(checkout, *module.split(".")) + ".py"):
                raise Reject("module_missing", module)
        if job["kind"] == "call":
            entry = job["args"].get("entry", "run")
            if not isinstance(entry, str) or not ENTRY_RE.match(entry):
                raise Reject("bad_entry", str(entry))
        out_dir = job.get("out_dir")
        if not isinstance(out_dir, str) or not os.path.isabs(out_dir) or \
                not is_within(out_dir, os.path.join(checkout, "exports", "fusion")):
            raise Reject("bad_out_dir", str(out_dir))
        job["checkout"] = checkout
        return job

    def take(self, name):
        try:
            os.remove(os.path.join(self.inbox, name))
        except OSError:
            pass

    def write_result(self, job_id, result):
        result.setdefault("protocol", PROTOCOL)
        result.setdefault("job_id", job_id)
        write_json_atomic(os.path.join(self.outbox, job_id + ".json"), result)

    def reject(self, name, reason, detail=""):
        stem = name[:-5] if name.endswith(".json") else name
        self.take(name)
        self.log("rejected", job=stem, reason=reason, detail=detail)
        if JOB_ID_RE.match(stem):
            self.write_result(stem, {"status": "rejected", "reject_reason": reason, "reject_detail": detail,
                                     "result": None, "error": None, "stdout": "", "stderr": "",
                                     "finished_utc": utc_iso()})


# ---------------------------------------------------------------------------- executor
class JobTimeout(BaseException):
    """Raised in the job when its time budget is used up. A BaseException: `except Exception` cannot swallow it."""


class _Capture(io.TextIOBase):
    def __init__(self, limit):
        io.TextIOBase.__init__(self)
        self._parts, self._n, self._limit, self.truncated = [], 0, limit, False

    def writable(self):
        return True

    def write(self, s):
        s = str(s)
        room = self._limit - self._n
        if room <= 0 or len(s) > room:
            self.truncated = True
        if room > 0:
            self._parts.append(s[:room])
            self._n += min(len(s), room)
        return len(s)

    def text(self):
        return "".join(self._parts)


def _async_raise(thread_ident, exc_type):
    """Make CPython raise exc_type in that thread at its next bytecode boundary; None withdraws a pending one."""
    obj = ctypes.py_object(exc_type) if exc_type is not None else ctypes.py_object()
    return ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(thread_ident), obj)


def purge_modules(roots, top_names=("cad",)):
    """Forget every module loaded from one of the roots, so the next import reads the files again."""
    roots_nc = [os.path.normcase(os.path.realpath(r)).rstrip("\\/") + os.sep for r in roots]
    doomed = []
    for name, mod in list(sys.modules.items()):
        if mod is None or name.startswith("_mcc_host_"):
            continue
        if name.split(".", 1)[0] in top_names:
            doomed.append(name)
            continue
        f = getattr(mod, "__file__", None)
        if f and any(os.path.normcase(os.path.realpath(f)).startswith(r) for r in roots_nc):
            doomed.append(name)
    for name in doomed:
        sys.modules.pop(name, None)
    importlib.invalidate_caches()
    return len(doomed)


class Executor:
    """Runs one validated job on the calling (main) thread and returns the result dict. Never raises."""

    def __init__(self, bridge, host):
        self.bridge, self.host = bridge, host
        self._lock = threading.Lock()
        self._in_job = False
        self._deadline = 0.0
        self._main_ident = None

    def _watchdog(self, done):
        while not done.wait(0.5):
            with self._lock:
                if self._in_job and time.monotonic() > self._deadline:
                    _async_raise(self._main_ident, JobTimeout)

    def execute(self, job):
        started, t0 = time.time(), time.monotonic()
        self._main_ident = threading.get_ident()
        out, err = _Capture(MAX_CAPTURE_CHARS), _Capture(MAX_CAPTURE_CHARS)
        status, error, value = "ok", None, None
        saved_path, saved_cwd, saved_dwb = list(sys.path), os.getcwd(), sys.dont_write_bytecode
        threads_before = set(threading.enumerate())
        done = threading.Event()
        public = {k: v for k, v in job.items() if k != "token"}
        public["deadline_monotonic"] = t0 + float(job["timeout_s"])
        public["host"] = {"mode": self.bridge.session["mode"], "hostlib_version": HOSTLIB_VERSION,
                          "checkout": self.bridge.session["checkout"], "info": self.host.info()}
        try:
            os.makedirs(job["out_dir"], exist_ok=True)
            purge_modules([self.bridge.session["checkout"]])
            sys.dont_write_bytecode = True
            sys.path.insert(0, job["checkout"])
            self._deadline = public["deadline_monotonic"]
            threading.Thread(target=self._watchdog, args=(done,), name="MccFusionBridge-watchdog",
                             daemon=True).start()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                try:
                    with self._lock:
                        self._in_job = True
                    runner = importlib.import_module(RUNNER_MODULE)
                    if not is_within(runner.__file__, job["checkout"]):
                        raise RuntimeError("the runtime was imported from %s, not from the job's checkout %s"
                                           % (runner.__file__, job["checkout"]))
                    value = runner.run(public)
                finally:
                    with self._lock:
                        self._in_job = False
                    _async_raise(self._main_ident, None)       # withdraw an injection that has not landed
            try:
                json.dumps(value)
            except (TypeError, ValueError) as exc:
                status, value = "error", None
                error = {"type": "ResultNotJSON", "message": str(exc), "traceback": ""}
        except JobTimeout:
            status = "timeout"
            error = {"type": "JobTimeout", "message": "the job exceeded %s s" % job["timeout_s"],
                     "traceback": traceback.format_exc()}
        except BaseException as exc:                           # SystemExit and KeyboardInterrupt included
            status = "error"
            error = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
        finally:
            done.set()
            with self._lock:
                self._in_job = False
            _async_raise(self._main_ident, None)
            sys.path[:] = saved_path
            sys.dont_write_bytecode = saved_dwb
            try:
                os.chdir(saved_cwd)
            except OSError:
                pass
        leaked = [t.name for t in threading.enumerate() if t not in threads_before and t.is_alive()
                  and not t.name.startswith("MccFusionBridge-")]
        return {"status": status, "error": error, "reject_reason": None, "result": value,
                "stdout": out.text(), "stdout_truncated": out.truncated,
                "stderr": err.text(), "stderr_truncated": err.truncated,
                "started_utc": utc_iso(started), "finished_utc": utc_iso(),
                "duration_s": round(time.monotonic() - t0, 3), "kind": job["kind"], "checkout": job["checkout"],
                "out_dir": job["out_dir"], "leaked_threads": leaked, "host": public["host"]}


def describe_job(job):
    """The line the user reads before answering: kind, plan or module, checkout, and whether the checkout has
    uncommitted changes (what runs is whatever the files of that checkout hold right now)."""
    args = job["args"]
    if job["kind"] == "probe":
        what = ",".join(args.get("probes") or []) or "(default probes)"
    else:
        what = args.get("plan") or args.get("module") or ""
    dirty = ((job.get("client") or {}).get("git") or {}).get("dirty")
    return "%s  kind=%s  %s  checkout=%s  dirty=%s" % (
        job["job_id"], job["kind"], what, job["checkout"], {True: "yes", False: "no"}.get(dirty, "unknown"))


# ---------------------------------------------------------------------------- base case: started by hand
def run_pending(bridge, host, host_checkout):
    """Body of the MccRun script: run every queued manual job once, after one confirmation. Main thread."""
    bridge.open_session("manual", host_checkout, host.info())
    try:
        live = read_json(bridge.session_path)
        jobs = []
        for name in bridge.pending():
            peek = bridge._peek(name)
            if live and peek and peek.get("session_id") == live.get("session_id"):
                continue                                         # it belongs to a running bridge add-in
            try:
                jobs.append((name, bridge.load_job(name)))
            except Reject as rej:
                bridge.reject(name, rej.reason, rej.detail)
        if not jobs:
            host.notify("No queued job. Queue one with scripts/fusion_run.py, then run this script again.")
            return []
        if not host.confirm_batch([describe_job(j) for _, j in jobs]):
            for name, _ in jobs:
                bridge.reject(name, "declined_by_user")
            return []
        executor, done = Executor(bridge, host), []
        for name, job in jobs:
            if time.time() > job["start_deadline_epoch"]:
                bridge.reject(name, "start_deadline_passed", "confirmed too late")
                continue
            bridge.take(name)
            bridge.write_status(state="running", job_id=job["job_id"], state_since_epoch=time.time(), mode="manual")
            result = executor.execute(job)
            bridge.write_result(job["job_id"], result)
            bridge.log("finished", job=job["job_id"], status=result["status"], kind=job["kind"],
                       checkout=job["checkout"], duration_s=result["duration_s"], mode="manual")
            done.append((job["job_id"], result["status"]))
        bridge.write_status(state="stopped", job_id=None, state_since_epoch=time.time(), mode="manual")
        host.notify("%d job(s) finished: %s" % (len(done), ", ".join("%s %s" % d for d in done)))
        return done
    finally:
        bridge.close_session()


# ---------------------------------------------------------------------------- accelerator: the add-in
class BridgeRuntime:
    def __init__(self, bridge, host, host_checkout):
        self.bridge, self.host, self.host_checkout = bridge, host, host_checkout
        self.executor = Executor(bridge, host)
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._worker = None
        self._state, self._job_id, self._state_since = "idle", None, time.time()
        self._event_outstanding, self._last_fire, self._defer_until = False, 0.0, 0.0
        self._main_seen = time.time()
        self.unattended = False          # consent lives in memory only; it ends with the session
        self._asked_unattended = False
        self.jobs_done = 0

    # main thread
    def start(self):
        self.bridge.open_session("bridge", self.host_checkout, self.host.info())
        self.bridge.log("session_open", session=self.bridge.session["session_id"], pid=os.getpid(),
                        checkout=self.bridge.session["checkout"])
        self._heartbeat()
        self._worker = threading.Thread(target=self._worker_loop, name="MccFusionBridge-worker", daemon=True)
        self._worker.start()

    def stop(self):
        self._stop.set()
        if self._worker is not None:
            self._worker.join(timeout=3.0)
        self.bridge.write_status(state="stopped", job_id=None, state_since_epoch=time.time(), mode="bridge")
        self.bridge.log("session_close")
        self.bridge.close_session()

    # worker thread
    def _set_state(self, state, job_id=None):
        with self._lock:
            self._state, self._job_id, self._state_since = state, job_id, time.time()

    def _heartbeat(self):
        with self._lock:
            fields = {"state": self._state, "job_id": self._job_id, "state_since_epoch": self._state_since,
                      "main_thread_seen_epoch": self._main_seen, "event_outstanding": self._event_outstanding,
                      "jobs_done": self.jobs_done, "unattended": self.unattended, "mode": "bridge"}
        fields["pending"] = len(self.bridge.pending())
        fields["disabled"] = os.path.exists(self.bridge.disabled_path)
        self.bridge.write_status(**fields)

    def _worker_loop(self):
        last_beat = 0.0
        while not self._stop.wait(POLL_S):
            try:
                now = time.time()
                if now - last_beat >= HEARTBEAT_S:
                    self._heartbeat()
                    last_beat = now
                names = [n for n in self.bridge.pending()
                         if (self.bridge._peek(n) or {}).get("session_id") != "manual"]
                if not names:
                    continue
                name = names[0]
                try:                                     # no API call: a bad job is answered even when
                    self.bridge.load_job(name)           # the main thread is blocked
                except Reject as rej:
                    self.bridge.reject(name, rej.reason, rej.detail)
                    continue
                with self._lock:
                    fire = self._state != "running" and not self._event_outstanding \
                        and now >= self._defer_until and now - self._last_fire >= 0.2
                    if fire:
                        self._event_outstanding, self._last_fire = True, now
                if fire:
                    self.host.fire(name)                 # Application.fireCustomEvent(EVENT_ID, name)
            except Exception:
                self.bridge.log("worker_error", traceback=traceback.format_exc())

    # main thread: body of the custom event handler; runs at most one job
    def on_main_thread(self, name):
        with self._lock:
            self._event_outstanding = False
            self._main_seen = time.time()
        try:
            try:
                job = self.bridge.load_job(name)          # validate again: the file may have changed
            except Reject as rej:
                if os.path.exists(os.path.join(self.bridge.inbox, name)):
                    self.bridge.reject(name, rej.reason, rej.detail)
                return
            idle, why = self.host.user_idle()
            if not idle:
                with self._lock:
                    self._defer_until = time.time() + REFIRE_S
                self._set_state("waiting_user", job["job_id"])
                self.bridge.log("deferred", job=job["job_id"], why=why)
                return
            # Unattended mode covers `build` and `probe` only; a `call` job (any module under cad/fusion/) always asks.
            if job["kind"] == "call" or not self.unattended:
                if not self.host.confirm(describe_job(job)):
                    self.bridge.reject(name, "declined_by_user")
                    return
                if job["kind"] != "call" and not self._asked_unattended:
                    self._asked_unattended = True
                    self.unattended = bool(self.host.confirm_unattended())
                    self.bridge.log("consent", unattended=self.unattended)
                if time.time() > job["start_deadline_epoch"]:
                    self.bridge.reject(name, "start_deadline_passed", "confirmed too late")
                    return
            self.bridge.take(name)
            self._set_state("running", job["job_id"])
            self._heartbeat()
            result = self.executor.execute(job)
            self.bridge.write_result(job["job_id"], result)
            self.jobs_done += 1
            self.bridge.log("finished", job=job["job_id"], status=result["status"], kind=job["kind"],
                            checkout=job["checkout"], duration_s=result["duration_s"], mode="bridge")
        except BaseException:
            self.bridge.log("handler_error", traceback=traceback.format_exc())
        finally:
            self._set_state("idle")
            with self._lock:
                self._main_seen = time.time()
