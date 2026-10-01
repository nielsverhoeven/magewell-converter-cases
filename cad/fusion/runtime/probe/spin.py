"""A job that never returns by itself. The host's watchdog must end it at the job's time-out.
"""


def run(job):
    n = 0
    while True:
        try:
            n += 1
        except Exception:        # a job that swallows Exception must still be stopped
            pass
