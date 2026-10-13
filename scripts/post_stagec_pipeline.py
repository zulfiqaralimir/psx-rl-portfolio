"""Runs after the 0.18% Stage C driver exits: (1) pre-patch analysis + snapshot + local commit, (2) apply the PSX data patch,
(3) start the core-16 robustness run (+ cool-down pauser) on the patched data, (4) re-evaluate every saved checkpoint on the patched test split
(no retraining: the patch only touches rows inside the test split), (5) regenerate Stage A/B/C + walk-forward tables and figures, (6) before/after effect."""
import subprocess, sys, time, shutil, os, psutil, datetime

ROOT = r"D:\psx_rl_portfolio"
PY = sys.executable
LOG = open(ROOT + r"\pipeline.log", "a", buffering=1)
def log(*a): print(datetime.datetime.now().strftime("%H:%M:%S"), *a, file=LOG, flush=True)
def run(args, **kw):
    log("RUN", " ".join(args)); r = subprocess.run([PY] + args, cwd=ROOT, stdout=LOG, stderr=subprocess.STDOUT, **kw)
    if r.returncode: log("FAILED", args, r.returncode); raise SystemExit(1)

def running(name):
    me = os.getpid()
    return any(name in " ".join(p.info["cmdline"] or []) and p.pid != me for p in psutil.process_iter(["cmdline"]))

log("waiting for run_stage_c_all.py")
while running("run_stage_c_all.py"): time.sleep(60)
time.sleep(120)   # let the old pauser exit
n = len([f for f in os.listdir(ROOT + r"\results\stageC\c0018") if f.endswith(".json")])
log("stage C driver finished; c0018 json count", n)
if n != 30: log("WARNING: expected 30 runs at 0.18%")

# (1) pre-patch analysis and snapshot
run(["scripts/analyze_stage_c.py"])
os.makedirs(ROOT + r"\results\pre_patch", exist_ok=True)
for src in (r"results\stageA_metrics.csv", r"results\stageC\stageC_summary.csv", r"results\stageC\stageC_significance.csv"):
    shutil.copy(rf"{ROOT}\{src}", rf"{ROOT}\results\pre_patch\{os.path.basename(src)}")
subprocess.run(["git", "add", "-A", "results"], cwd=ROOT, stdout=LOG, stderr=subprocess.STDOUT)
subprocess.run(["git", "commit", "-q", "-m", "Pre-patch results snapshot (0.18% runs complete, before applying the PSX data patch)\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"], cwd=ROOT, stdout=LOG, stderr=subprocess.STDOUT)
log("pre-patch snapshot committed locally")

# (2) apply the patch
run(["scripts/apply_data_patch.py", "--apply"])

# (3) start core-16 robustness + pauser on the patched data (detached)
subprocess.Popen([PY, ROOT + r"\scripts\cooldown_pauser.py"], cwd=ROOT, stdout=open(ROOT + r"\cooldown_core16.log", "w"), stderr=subprocess.STDOUT)
subprocess.Popen([PY, ROOT + r"\scripts\run_core16_all.py"], cwd=ROOT, stdout=open(ROOT + r"\core16_driver.log", "w"), stderr=subprocess.STDOUT)
log("core16 started")

# (4) re-evaluate saved checkpoints on the patched test split
run(["scripts/reeval_models.py"])
# (5) regenerate Stage A/B/C and walk-forward tables and figures
for s in ("run_stage_a.py", "analyze_stage_c.py", "analyze_walkforward.py", "make_figures.py", "make_figures_c.py", "make_tables.py", "make_tables_wf.py", "make_figures_wf.py"):
    run([f"scripts/{s}"])
# (6) before/after effect
run(["scripts/patch_effect.py"])
log("PIPELINE DONE")
