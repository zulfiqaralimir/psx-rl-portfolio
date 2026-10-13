"""Queue the training-length ablation behind the core-16 run: wait until the PSX data patch has been applied (data/patch/applied.txt) and the core-16
driver has started and finished, then start a cool-down pauser (5 min after every hour) and the ablation driver (2 workers)."""
import subprocess, sys, time, os, psutil

ROOT = r"D:\psx_rl_portfolio"


def running(name):
    me = os.getpid()
    return any(name in " ".join(p.info["cmdline"] or []) and p.pid != me for p in psutil.process_iter(["cmdline"]))


while not os.path.exists(ROOT + r"\data\patch\applied.txt"):
    time.sleep(60)
t_applied = time.time()
seen = False
while True:
    if running("run_core16_all.py"):
        seen = True
    elif seen or time.time() - t_applied > 1800:   # core16 finished, or never started within 30 min of the patch (pipeline problem): go on
        break
    time.sleep(60)
time.sleep(150)   # let the core16 pauser exit
subprocess.Popen([sys.executable, ROOT + r"\scripts\cooldown_pauser.py"], cwd=ROOT, stdout=open(ROOT + r"\cooldown_ablation.log", "w"), stderr=subprocess.STDOUT)
subprocess.run([sys.executable, ROOT + r"\scripts\run_ablation_all.py"], cwd=ROOT, stdout=open(ROOT + r"\ablation_driver.log", "w"), stderr=subprocess.STDOUT)
