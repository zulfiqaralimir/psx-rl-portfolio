"""Wait for the Stage C driver to finish, then start the core16 robustness run and a cool-down pauser for it."""
import subprocess, sys, time, psutil

def running(name):
    return any(name in " ".join(p.info["cmdline"] or []) and "queue_core16" not in " ".join(p.info["cmdline"] or [])
               for p in psutil.process_iter(["cmdline"]))

while running("run_stage_c_all.py"):
    time.sleep(60)
time.sleep(90)  # let the old pauser exit
subprocess.Popen([sys.executable, r"D:\psx_rl_portfolio\scripts\cooldown_pauser.py"], stdout=open(r"D:\psx_rl_portfolio\cooldown_core16.log", "w"), stderr=subprocess.STDOUT)
subprocess.run([sys.executable, r"D:\psx_rl_portfolio\scripts\run_core16_all.py"], stdout=open(r"D:\psx_rl_portfolio\core16_driver.log", "w"), stderr=subprocess.STDOUT)
