"""End-to-end test of the host library, the script host, the add-in loop and the client, without Fusion.

A stand-in process (runtime_fake_fusion.py) plays Fusion's main thread. Everything lives in a temporary
directory: a copy of the checkout, a worktree inside it, a foreign checkout, a foreign repository nested inside the
checkout, and the bridge directory.
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

from cad.fusion.runtime.tests import runtime_support as support

PY = sys.executable
FAKE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runtime_fake_fusion.py")
M = "cad.fusion.jobs."
JOBS = {
    "ok_job.py": "from cad.fusion.jobs import helper_mod\n"
                 "def run(job):\n"
                 "    print('hello from', job['job_id'])\n"
                 "    return {'answer': helper_mod.VALUE, 'args': job['args']['args'], 'has_token': 'token' in job}\n",
    "helper_mod.py": "VALUE = 1\n",
    "error_job.py": "def run(job):\n    raise ValueError('boom')\n",
    "loop_job.py": "def run(job):\n    n = 0\n    while True:\n        try:\n            n += 1\n"
                   "        except Exception:\n            pass\n",
    "exit_job.py": "import sys\ndef run(job):\n    sys.exit(3)\n",
    "notjson_job.py": "def run(job):\n    return {1, 2, 3}\n",
    "noisy_job.py": "def run(job):\n    for i in range(30000):\n        print('x' * 100)\n    return 'done'\n",
    "chdir_job.py": "import os, sys\ndef run(job):\n    os.chdir(job['out_dir'])\n    sys.path.insert(0, 'junk')\n"
                    "    return os.getcwd()\n",
    "slow_job.py": "import time\ndef run(job):\n    time.sleep(job['args']['args'].get('s', 1.0))\n"
                   "    return job['args']['args'].get('tag')\n",
    "fake_probes.py": "def good(env):\n    return {'status': 'pass', 'x': 1}\n"
                      "def bad(env):\n    raise ValueError('probe boom')\n"
                      "PROBES = [('T.1', 'good', good), ('T.2', 'bad', bad)]\n",
}


class HostLibraryEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="mcc-hostlib-")
        cls.checkout = support.make_checkout(cls.tmp)
        cls.bridge = os.path.join(cls.tmp, "bridge")
        os.makedirs(cls.bridge)
        for name, text in JOBS.items():
            support.write(os.path.join(cls.checkout, "cad", "fusion", "jobs", name), text)
        support.write(os.path.join(cls.checkout, "cad", "fusion", "replay", "ocp_replay.py"),
                      "def run(job):\n    return 'replayed'\n")
        support.write(os.path.join(cls.checkout, "cad", "fusion", "gen", "core", "probes.py"),
                      "def one(env):\n    return {'status': 'pass'}\nPROBES = [('G.1', 'stand-in', one)]\n")
        cls.worktree = os.path.join(cls.checkout, ".claude", "worktrees", "w1")
        cls.worktree_bad = os.path.join(cls.checkout, ".claude", "worktrees", "bad")
        cls.foreign = os.path.join(cls.tmp, "foreign")
        cls.nested = os.path.join(cls.checkout, "vendor", "other")          # a repository that is no worktree of it
        linked = "gitdir: " + os.path.join(cls.checkout, ".git", "worktrees", "%s") + "\n"    # what `git worktree add` writes
        for root, mark, pointer in ((cls.worktree, "worktree-w1", linked % "w1"), (cls.foreign, "foreign", "gitdir: elsewhere\n"),
                                    (cls.worktree_bad, "bad", linked % "bad"), (cls.nested, "nested", "gitdir: elsewhere\n")):
            support.write(os.path.join(root, ".git"), pointer)
            shutil.copytree(os.path.join(cls.checkout, "cad", "fusion", "runtime"),
                            os.path.join(root, "cad", "fusion", "runtime"))
            if root != cls.worktree_bad:            # a real worktree has the package files
                support.write(os.path.join(root, "cad", "__init__.py"), "")
                support.write(os.path.join(root, "cad", "fusion", "__init__.py"), "")
            support.write(os.path.join(root, "cad", "fusion", "jobs", "ok_job.py"),
                          "def run(job):\n    return 'from %s'\n" % mark)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ---- helpers -------------------------------------------------------------------------------------
    def client_command(self, *args, checkout=None):
        cmd = [PY, os.path.join(self.checkout, "scripts", "fusion_run.py"), "--bridge-dir", self.bridge]
        if checkout:
            cmd += ["--checkout", checkout]
        args = list(args)
        if args and args[0] in ("call", "build", "probe"):
            args += ["--backend", "recording"]      # no adsk in these tests
        return cmd + args

    def client(self, *args, checkout=None):
        p = subprocess.run(self.client_command(*args, checkout=checkout), capture_output=True, text=True, timeout=180)
        out = None
        if p.stdout.strip():
            try:
                out = json.loads(p.stdout)
            except ValueError:
                out = p.stdout
        return p.returncode, out, p.stderr

    def start_bridge(self, *extra):
        p = subprocess.Popen([PY, FAKE, "bridge", self.bridge, self.checkout, *extra], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True)
        t_end = time.time() + 15
        while time.time() < t_end:
            if os.path.exists(os.path.join(self.bridge, "session.json")):
                return p
            time.sleep(0.05)
        p.kill()
        self.fail("the stand-in did not start: %s" % p.stdout.read())

    def stop_bridge(self, p):
        open(os.path.join(self.bridge, "QUIT"), "w").close()
        out = p.communicate(timeout=15)[0]
        os.remove(os.path.join(self.bridge, "QUIT"))
        return out

    def manual(self, *extra, env=None):
        p = subprocess.run([PY, FAKE, "manual", self.bridge, self.checkout, *extra], capture_output=True, text=True,
                           timeout=180, env=env)
        return p.stdout + p.stderr

    def check(self, name, condition, detail=""):
        with self.subTest(name):
            self.assertTrue(condition, detail)

    # ---- the run -------------------------------------------------------------------------------------
    def test_end_to_end(self):
        check, client, J = self.check, self.client, os.path.join(self.checkout, "cad", "fusion", "jobs")

        rc, out, err = client("status")
        check("status without a bridge exits 3", rc == 3 and out["bridge_live"] is False, (rc, out, err))
        rc, out, err = client("call", M + "ok_job", "--mode", "bridge")
        check("--mode bridge without a bridge exits 3", rc == 3, (rc, err))

        fake = self.start_bridge()
        try:
            rc, out, err = client("call", M + "ok_job", "--arg", "n=5", "--arg", "name=abc")
            check("bridge: ok job exits 0", rc == 0 and out["status"] == "ok", (rc, out, err))
            check("result and arguments returned, no token", out and out["result"]["value"] == {
                "answer": 1, "args": {"n": 5, "name": "abc"}, "has_token": False}, out)
            check("stdout captured", out and out["stdout"].startswith("hello from "), out)
            support.write(os.path.join(J, "helper_mod.py"), "VALUE = 2\n")
            rc, out, err = client("call", M + "ok_job")
            check("an edited module is reloaded", rc == 0 and out["result"]["value"]["answer"] == 2, (rc, out, err))
            check("no __pycache__ in the checkout", not os.path.exists(os.path.join(J, "__pycache__")))
            rc, out, err = client("call", M + "error_job")
            check("a raising job exits 1 with the traceback", rc == 1 and out["error"]["type"] == "ValueError"
                  and "boom" in out["error"]["traceback"], (rc, out, err))
            t0 = time.time()
            rc, out, err = client("call", M + "loop_job", "--timeout", "2")
            check("an endless loop is stopped by the watchdog", rc == 1 and out["status"] == "timeout"
                  and time.time() - t0 < 15, (rc, out and out["status"], time.time() - t0, err))
            rc, out, err = client("call", M + "ok_job")
            check("the host works after a time-out", rc == 0, (rc, out, err))
            rc, out, err = client("call", M + "exit_job")
            check("sys.exit in a job is contained", rc == 1 and out["error"]["type"] == "SystemExit", (rc, out, err))
            rc, out, err = client("call", M + "notjson_job")
            check("a result that is not JSON is reported", rc == 1 and out["error"]["type"] == "ResultNotJSON", (rc, out))
            rc, out, err = client("call", M + "noisy_job")
            check("stdout is cut at the limit", rc == 0 and out["stdout_truncated"]
                  and len(out["stdout"]) == 1000000, (rc, out and len(out["stdout"])))
            rc, out, err = client("call", M + "chdir_job")
            rc2, out2, err2 = client("call", M + "chdir_job")
            check("cwd and sys.path are restored", rc == 0 and rc2 == 0, (rc, rc2, err, err2))
            rc, out, err = client("call", "scripts.fusion_run")
            check("a module outside cad.fusion is rejected", rc == 6
                  and out["reject_reason"] == "module_outside_cad_fusion", (rc, out, err))
            rc, out, err = client("call", M + "nope")
            check("a missing module is rejected", rc == 6 and out["reject_reason"] == "module_missing", (rc, out, err))
            rc, out, err = client("call", M + "ok_job", "--entry", "__import__")
            check("a bad entry name is rejected", rc == 6 and out["reject_reason"] == "bad_entry", (rc, out, err))
            rc, out, err = client("call", M + "ok_job", checkout=self.foreign)
            check("a foreign checkout is rejected", rc == 6
                  and out["reject_reason"] == "checkout_outside_allowed_root", (rc, out, err))
            rc, out, err = client("call", M + "ok_job", checkout=self.nested)
            check("a repository nested in the checkout that is no worktree of it is rejected", rc == 6
                  and out["reject_reason"] == "checkout_not_a_worktree", (rc, out, err))
            rc, out, err = client("call", M + "ok_job", "--timeout", "99999")
            check("a time-out above the maximum is rejected", rc == 6 and out["reject_reason"] == "bad_timeout", (rc, out))
            rc, out, err = client("call", M + "ok_job", checkout=self.worktree)
            inside = os.path.normcase(os.path.realpath(self.worktree)) + os.sep
            check("a worktree job runs the worktree's module", rc == 0
                  and out["result"]["value"] == "from worktree-w1", (rc, out))
            check("and the worktree's runner", rc == 0
                  and os.path.normcase(out["result"]["runner_file"]).startswith(inside), (rc, out, err))
            rc, out, err = client("call", M + "ok_job")
            check("the next main job gets the main runner", rc == 0
                  and not os.path.normcase(out["result"]["runner_file"]).startswith(inside), (rc, out, err))
            rc, out, err = client("call", M + "ok_job", checkout=self.worktree_bad)
            bad = os.path.normcase(os.path.realpath(self.worktree_bad)) + os.sep
            check("a checkout without package files still runs its own code", rc == 0
                  and out["result"]["value"] == "from bad"
                  and os.path.normcase(out["result"]["runner_file"]).startswith(bad), (rc, out, err))
            plan = os.path.join(self.checkout, "cad", "fusion", "runtime", "testdoc", "plan.json")
            rc, out, err = client("build", plan)
            check("a build job on the recording backend", rc == 0 and out["result"]["result"] == "recorded"
                  and len(out["result"]["inventory_sha256"]) == 64, (rc, out, err))
            rc, out, err = client("probe", "--probes", "cad.fusion.jobs.fake_probes", "--no-spin")
            check("a probe job: one pass, one error, exit 1, report written", rc == 1
                  and out["result"]["summary"] == {"pass": 1, "error": 1}
                  and os.path.isfile(out["result"]["report"]), (rc, out, err))
            rc, out, err = client("call", "cad.fusion.replay.ocp_replay")
            check("the replay is never run by a host", rc == 6 and out["reject_reason"] == "module_not_allowed",
                  (rc, out, err))
            rc, out, err = client("probe", "--probes", "os", "--no-spin")
            check("a probe module outside cad.fusion is rejected", rc == 6
                  and out["reject_reason"] == "module_outside_cad_fusion", (rc, out, err))
            rc, out, err = client("probe", "--probes", "cad.fusion.jobs.no_such_probes", "--no-spin")
            check("a probe module that does not exist is rejected", rc == 6
                  and out["reject_reason"] == "module_missing", (rc, out, err))
            rc, out, err = client("probe", "--no-spin")
            check("without --probes every probes.py under cad/fusion/gen joins the run", rc == 1
                  and out["result"]["summary"].get("pass") == 1
                  and out["result"]["failed"] == ["cad.fusion.runtime.probe.core_probes"], (rc, out, err))
            rc, out, err = client("probe", "--probes", "cad.fusion.jobs.fake_probes", "--only", "T.1")
            check("the time-out probe P79.11 passes", rc == 0 and out["P79.11"]["status"] == "pass", (rc, out, err))
            procs = [subprocess.Popen(self.client_command("call", M + "slow_job", "--arg", "s=1.0", "--arg",
                                                          "tag=%d" % i), stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True) for i in range(3)]
            t0 = time.time()
            outs = [p.communicate(timeout=120) for p in procs]
            tags = sorted(json.loads(o[0])["result"]["value"] for o in outs)
            check("three clients at once all finish, one after the other", [p.returncode for p in procs] == [0, 0, 0]
                  and tags == [0, 1, 2] and time.time() - t0 >= 3.0, ([p.returncode for p in procs], tags))
            rc, out, err = client("status")
            check("status with a bridge exits 0 and hides the token", rc == 0 and out["bridge_live"]
                  and "token" not in out["session"], (rc, out))
            client("disable")
            rc, out, err = client("call", M + "ok_job")
            check("disable gives exit 3", rc == 3, (rc, err))
            client("enable")
            rc, out, err = client("call", M + "ok_job", "--mode", "manual", "--no-wait")
            manual_id = out["job_id"]
            time.sleep(1.5)
            check("a manual job is left alone by the bridge",
                  os.path.exists(os.path.join(self.bridge, "inbox", manual_id + ".json")))
            with open(os.path.join(self.bridge, "log", "bridge.log"), encoding="utf-8") as fh:
                log = fh.read()
            with open(os.path.join(self.bridge, "session.json"), encoding="utf-8") as fh:
                token = json.load(fh)["token"]
            check("the token is not in the log", token not in log and '"event": "finished"' in log)
        finally:
            text = self.stop_bridge(fake)
        asked = [line for line in text.splitlines() if line.startswith("CONFIRM ")]
        check("every question names kind, module, checkout and the dirty state", asked and all(
            re.match(r"^CONFIRM \S+  kind=(call|build|probe)  \S+  checkout=.+  dirty=(unknown|yes|no)$", line)
            for line in asked), asked[:2])
        check("every call job asked, unattended mode or not", sum("kind=call" in line for line in asked) >= 15
              and any("cad.fusion.jobs.ok_job" in line and self.checkout in line for line in asked), len(asked))
        check("unattended mode covers build and probe: only the first of them asked",
              sum("kind=build" in line or "kind=probe" in line for line in asked) == 1
              and text.count("CONFIRM-UNATTENDED") == 1, text[-400:])
        check("session.json is removed at stop", not os.path.exists(os.path.join(self.bridge, "session.json")))

        text = self.manual()
        rc, out, err = client("wait", manual_id)
        check("the manual run executes the queued manual job", "CONFIRM-BATCH 1" in text and rc == 0
              and out["status"] == "ok", (text, rc, out, err))

        fake = self.start_bridge("--unattended", "no")
        try:
            r1 = client("build", plan)[0]
            r2 = client("build", plan)[0]
        finally:
            text = self.stop_bridge(fake)
        check("unattended declined: every job asks, the second question once", r1 == 0 and r2 == 0
              and text.count("CONFIRM ") == 2 and text.count("CONFIRM-UNATTENDED") == 1, text[-300:])

        fake = self.start_bridge("--unattended", "yes")
        try:
            sequence = [client("call", M + "ok_job")[0], client("build", plan)[0], client("build", plan)[0],
                        client("probe", "--probes", "cad.fusion.jobs.fake_probes", "--only", "T.1", "--no-spin")[0],
                        client("call", M + "ok_job")[0]]
        finally:
            text = self.stop_bridge(fake)
        asked = [line.split("  ")[1] for line in text.splitlines() if line.startswith("CONFIRM ")]
        check("unattended granted: a call always asks, the first build asks, the next build and the probe do not",
              sequence == [0, 0, 0, 0, 0] and asked == ["kind=call", "kind=build", "kind=call"]
              and text.count("CONFIRM-UNATTENDED") == 1, (sequence, asked, text[-300:]))

        fake = self.start_bridge("--confirm", "no")
        try:
            rc, out, err = client("call", M + "ok_job")
        finally:
            self.stop_bridge(fake)
        check("a declined job is rejected", rc == 6 and out["reject_reason"] == "declined_by_user", (rc, out))

        fake = self.start_bridge("--busy-user", "2")
        try:
            t0 = time.time()
            rc, out, err = client("call", M + "ok_job")
        finally:
            self.stop_bridge(fake)
        check("a busy user defers the job, then it runs", rc == 0 and time.time() - t0 >= 3.5, (rc, time.time() - t0))

        ids = [client("call", M + "slow_job", "--arg", "s=0.2", "--arg", "tag=%d" % i, "--no-wait")[1]["job_id"]
               for i in range(2)]
        text = self.manual()
        res = [client("wait", i) for i in ids]
        check("manual: the one question lists every job with kind, module, checkout and dirty state",
              text.count("BATCH-LINE ") == 2 and "kind=call  cad.fusion.jobs.slow_job  checkout=" in text
              and "dirty=" in text, text)
        check("manual: two jobs, one confirmation, both run", "CONFIRM-BATCH 2" in text and "2 job(s) finished" in text
              and [r[0] for r in res] == [0, 0] and sorted(r[1]["result"]["value"] for r in res) == [0, 1], (text, res))
        check("manual: an empty queue gives a notice only", "No queued job" in self.manual())
        job_id = client("call", M + "ok_job", "--no-wait")[1]["job_id"]
        self.manual("--confirm", "no")
        rc, out, err = client("wait", job_id)
        check("manual: a declined batch is rejected", rc == 6 and out["reject_reason"] == "declined_by_user", (rc, out))
        waiter = subprocess.Popen(self.client_command("call", M + "ok_job"), stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True)
        time.sleep(1.5)
        self.manual()
        o, e = waiter.communicate(timeout=60)
        check("manual: a waiting client gets its result", waiter.returncode == 0 and json.loads(o)["status"] == "ok"
              and "Shift+S" in e, (waiter.returncode, o, e))
        rc, out, err = client("call", M + "ok_job", "--queue-timeout", "1")
        check("manual: without a run the client exits 4", rc == 4, (rc, err))
        check("and withdraws its job", not os.listdir(os.path.join(self.bridge, "inbox")))

        job_id = client("call", M + "ok_job", "--no-wait", checkout=self.worktree_bad)[1]["job_id"]
        self.manual(env=dict(os.environ, PYTHONPATH=self.checkout))
        rc, out, err = client("wait", job_id)
        check("a cad package elsewhere on sys.path that shadows the job's checkout gives a clear error", rc == 1
              and "not from the job's checkout" in out["error"]["message"], (rc, out, err))

        with open(os.path.join(self.bridge, "session.json"), "w", encoding="utf-8") as fh:
            json.dump({"protocol": 1, "session_id": "x", "token": "y", "pid": 999999}, fh)
        rc, out, err = client("call", M + "ok_job", "--mode", "bridge")
        check("a session file of a dead process gives exit 3", rc == 3, (rc, err))
        os.remove(os.path.join(self.bridge, "session.json"))

        plan = os.path.join(self.checkout, "cad", "fusion", "runtime", "testdoc", "plan.json")
        inv = os.path.join(self.checkout, "cad", "fusion", "runtime", "testdoc", "inventory.json")
        if os.path.exists(inv):
            os.remove(inv)
        rc, out, err = client("plan", plan)
        check("plan: the recording run exits 0", rc == 0 and out["result"] == "recorded"
              and all(c["gates_passed"] for c in out["configurations"]), (rc, out, err))
        rc, out, err = client("plan", plan, "--write-inventory")
        check("plan --write-inventory writes the file", rc == 0 and os.path.isfile(inv), (rc, err))
        rc, out, err = client("plan", plan)
        check("and the next run finds it fresh", rc == 0, (rc, out, err))
        with open(inv, "rb") as fh:
            fresh = fh.read()
        with open(inv, "wb") as fh:
            fh.write(fresh.replace(b'"Test_Block_Extrude"', b'"Test_Block_Extrude2"'))
        rc, out, err = client("plan", plan)
        check("plan: a stale committed inventory exits 1", rc == 1
              and "inventory_committed" in " ".join(out["violations"]), (rc, out, err))
        rc, out, err = client("plan", plan, "--write-inventory")
        with open(inv, "rb") as fh:
            check("plan --write-inventory replaces a stale file", rc == 0 and fh.read() == fresh
                  and out["inventory_written"].endswith("testdoc/inventory.json"), (rc, out, err))
        rc, out, err = client("digest", plan)
        check("digest prints sha256-lf-v1", rc == 0 and out["algorithm"] == "sha256-lf-v1"
              and len(out["value"]) == 64, (rc, out, err))


def load_hostlib():
    path = os.path.join(support.REPO, "cad", "fusion", "runtime", "hostlib.py")
    spec = importlib.util.spec_from_file_location("_mcc_test_hostlib", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConfirmationLine(unittest.TestCase):
    """What the user reads before a job runs (amendment A7)."""

    @classmethod
    def setUpClass(cls):
        cls.hostlib = load_hostlib()

    def job(self, kind, args, dirty="absent"):
        job = {"job_id": "20260930T120000Z-abcdef01", "kind": kind, "args": args, "checkout": "/work/repo"}
        if dirty != "absent":
            job["client"] = {"git": {"head": "0" * 40, "dirty": dirty}}
        return job

    def test_kind_module_checkout_and_dirty_state(self):
        line = self.hostlib.describe_job(self.job("call", {"module": "cad.fusion.jobs.x"}, dirty=True))
        self.assertEqual(line, "20260930T120000Z-abcdef01  kind=call  cad.fusion.jobs.x  checkout=/work/repo  dirty=yes")
        line = self.hostlib.describe_job(self.job("build", {"plan": "cad/fusion/documents/a.json"}, dirty=False))
        self.assertTrue(line.endswith("dirty=no"))

    def test_an_unknown_dirty_state_is_said_so(self):
        for dirty in (None, "absent"):
            line = self.hostlib.describe_job(self.job("build", {"plan": "p.json"}, dirty))
            self.assertTrue(line.endswith("dirty=unknown"))

    def test_a_probe_shows_its_modules(self):
        line = self.hostlib.describe_job(self.job("probe", {"probes": ["cad.fusion.a", "cad.fusion.b"]}, dirty=False))
        self.assertIn("kind=probe  cad.fusion.a,cad.fusion.b  checkout=", line)
        self.assertIn("(default probes)", self.hostlib.describe_job(self.job("probe", {}, dirty=False)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
