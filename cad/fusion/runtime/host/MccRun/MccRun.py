"""MccRun: runs the queued jobs of this checkout once. The user starts it by hand from Scripts and Add-Ins.

It needs no add-in and no standing permission. It shows the list of queued jobs, asks once, runs them on
Fusion's main thread and writes each result to the outbox.
"""
import importlib.util
import os
import sys
import traceback

import adsk.core

RUNTIME_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_hostlib():
    name = "_mcc_host_hostlib"
    sys.modules.pop(name, None)                 # always the file as it is on disk now
    spec = importlib.util.spec_from_file_location(name, os.path.join(RUNTIME_DIR, "hostlib.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class _Host:
    def __init__(self, app):
        self.app, self.ui = app, app.userInterface

    def info(self):
        return {"fusion_version": self.app.version, "python": sys.version.split()[0], "host": "MccRun"}

    def confirm_batch(self, lines):
        text = "Run %d queued job(s) inside Fusion?\n\n%s" % (len(lines), "\n".join(lines))
        answer = self.ui.messageBox(text, "MccRun", adsk.core.MessageBoxButtonTypes.YesNoButtonType,
                                    adsk.core.MessageBoxIconTypes.QuestionIconType)
        return answer == adsk.core.DialogResults.DialogYes

    def notify(self, text):
        self.app.log("MccRun: " + text)
        self.ui.messageBox(text, "MccRun")


def run(context):
    app = adsk.core.Application.get()
    try:
        hostlib = _load_hostlib()
        hostlib.run_pending(hostlib.Bridge(), _Host(app), hostlib.find_checkout(RUNTIME_DIR))
    except BaseException:
        app.log("MccRun failed:\n" + traceback.format_exc())
        app.userInterface.messageBox("MccRun failed. The Text Commands window has the details.", "MccRun")
