"""Stand-in for Fusion in the host tests: a process whose main thread plays Fusion's main thread.

It loads hostlib.py of the given checkout by path under a private module name, exactly as the two hosts do,
and offers the same host interface with scripted answers instead of dialogs.

  python runtime_fake_fusion.py bridge <bridge_dir> <checkout> [--confirm yes|no] [--unattended yes|no]
                                                               [--busy-user N] [--lifetime S]
  python runtime_fake_fusion.py manual <bridge_dir> <checkout> [--confirm yes|no]
"""
import importlib.util
import os
import queue
import sys
import time


def load_hostlib(checkout):
    path = os.path.join(checkout, "cad", "fusion", "runtime", "hostlib.py")
    spec = importlib.util.spec_from_file_location("_mcc_host_hostlib", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeHost:
    def __init__(self, events, confirm, unattended, busy_user):
        self.events, self._confirm, self._unattended, self._busy = events, confirm, unattended, busy_user

    def info(self):
        return {"fusion_version": "fake-0", "python": sys.version.split()[0], "host": "fake"}

    def fire(self, name):
        self.events.put(name)
        return True

    def user_idle(self):
        if self._busy > 0:
            self._busy -= 1
            return False, "active command FakeExtrude"
        return True, ""

    def confirm(self, text):
        print("CONFIRM %s" % text, flush=True)
        return self._confirm

    def confirm_unattended(self):
        print("CONFIRM-UNATTENDED", flush=True)
        return self._unattended

    def confirm_batch(self, lines):
        print("CONFIRM-BATCH %d" % len(lines), flush=True)
        for line in lines:
            print("BATCH-LINE %s" % line, flush=True)
        return self._confirm

    def notify(self, text):
        print("NOTIFY %s" % text, flush=True)


def option(argv, name, default):
    return argv[argv.index(name) + 1] if name in argv else default


def main(argv):
    mode, bridge_dir, checkout = argv[1], argv[2], argv[3]
    hostlib = load_hostlib(checkout)
    events = queue.Queue()
    host = FakeHost(events, option(argv, "--confirm", "yes") == "yes", option(argv, "--unattended", "yes") == "yes",
                    int(option(argv, "--busy-user", "0")))
    bridge = hostlib.Bridge(bridge_dir)
    if mode == "manual":
        hostlib.run_pending(bridge, host, checkout)
        return
    runtime = hostlib.BridgeRuntime(bridge, host, checkout)
    runtime.start()
    print("ready pid=%d" % os.getpid(), flush=True)
    t_end = time.time() + float(option(argv, "--lifetime", "180"))
    try:
        while time.time() < t_end and not os.path.exists(os.path.join(bridge_dir, "QUIT")):
            try:
                name = events.get(timeout=0.1)       # "Fusion is idle": the main thread waits for events
            except queue.Empty:
                continue
            runtime.on_main_thread(name)
    finally:
        runtime.stop()
    print("stopped", flush=True)


if __name__ == "__main__":
    main(sys.argv)
