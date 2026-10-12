"""Cool-down for long runs: every hour, suspend run_stage_c_all.py and its training workers for 5 minutes, then resume.
Suspending (not killing) keeps all training progress. Exits when the driver is gone."""
import time, psutil

RUN_MIN, PAUSE_MIN = 60, 5


def driver():
    for p in psutil.process_iter(["pid", "cmdline"]):
        if p.info["cmdline"] and any(("run_stage_c_all" in c or "run_walkforward_all" in c) for c in p.info["cmdline"]):
            return p


def tree(p):
    return [p] + p.children(recursive=True)


while True:
    t_end = time.time() + RUN_MIN * 60
    while time.time() < t_end:
        time.sleep(30)
        if driver() is None:
            print("driver finished, pauser exits", flush=True); raise SystemExit
    d = driver()
    if d is None:
        raise SystemExit
    procs = tree(d)
    for p in procs:
        try: p.suspend()
        except psutil.Error: pass
    print(time.strftime("%H:%M"), "paused", len(procs), "procs", flush=True)
    time.sleep(PAUSE_MIN * 60)
    for p in procs:
        try: p.resume()
        except psutil.Error: pass
    print(time.strftime("%H:%M"), "resumed", flush=True)
