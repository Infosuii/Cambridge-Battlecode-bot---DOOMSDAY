"""Sync Agent 2's findings to the user's GitHub repo (Infosuii/neural-networkk-battlecode, a local clone) every INTERVAL
seconds: pull (rebase), copy the curated files into DEST, commit and push only when something changed. Run it in the
user's Terminal panel (GitHub credentials live there). No data dumps, replays or credentials are copied.
usage (project root): python -P agent2/lab/gh_sync.py REPO_DIR [--interval 600] [--once]"""
import os, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = sys.argv[1:]
REPO = os.path.abspath(A[0])
INTERVAL = int(A[A.index("--interval") + 1]) if "--interval" in A else 600
ONCE = "--once" in A
DEST = os.path.join(REPO, "research", "agent2-neural")
BRANCH = "agent2-neural"  # own branch: teammates' main is untouched
SCRATCH_README = os.path.join(ROOT, "agent2", "findings_README.md")
L = os.path.join(ROOT, "agent2", "lab")
FILES = {  # repo path -> source
    "README.md": SCRATCH_README,
    "docs/EXPERIMENTS.md": os.path.join(ROOT, "agent2", "EXPERIMENTS.md"),
    "docs/neural_bot_2026-11-03.md": os.path.join(ROOT, "agent2", "plans", "neural_bot_2026-11-03.md"),
    "docs/large_gains_v3_2026-11-03.md": os.path.join(ROOT, "agent2", "plans", "large_gains_v3_2026-11-03.md"),
    "docs/game_analysis_2026-11-03.md": os.path.join(ROOT, "agent2", "plans", "game_analysis_2026-11-03.md"),
    "code/mapmake6.js": os.path.join(ROOT, "tools", "viz", "mapmake6.js"),
    "models/dag3_teacher.pt": os.path.join(ROOT, "agent2", "nn_out_dag3", "teacher.pt"),
    "models/dag3_student.pt": os.path.join(ROOT, "agent2", "nn_out_dag3", "student.pt"),
    "models/dag3_student_w.h": os.path.join(ROOT, "agent2", "nn_out_dag3", "student_w.h"),
    "results/rl.log": os.path.join(ROOT, "agent2", "nn_rl1", "rl.log"),
    "results/map_stats.json": os.path.join(L, "map_stats.json"),
}
for f in ("nnrec.cpp", "nn_infer.h", "nn_model.py", "nn_train.py", "nn_labels.py", "nn_record.py", "nn_export.py", "nn_mkrec.py",
          "nn_mkbot.py", "nn_merge.py", "nn_pipeline.sh", "nn_dagger.sh", "nn_rl.py", "map_stats.js", "b1_repeat.py", "b1_ident.py",
          "gh_sync.py"):
    FILES["code/" + f] = os.path.join(L, f)
for f in ("nn1_ladder.tsv", "nn1_unseen.tsv", "nn2_ladder.tsv", "nn2_unseen.tsv", "nn3_ladder.tsv", "nn3_pool.tsv",
          "nn3t1_ladder.tsv", "nn3t2_ladder.tsv", "nn3t3_ladder.tsv"):
    FILES["results/" + f] = os.path.join(L, f)


def git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True)


def sync():
    git("checkout", BRANCH)
    has_remote = git("ls-remote", "--exit-code", "--heads", "origin", BRANCH).returncode == 0
    r = git("pull", "--rebase", "--autostash", "origin", BRANCH) if has_remote else git("status")
    if r.returncode != 0:
        print(time.strftime("%H:%M:%S"), "pull failed:", r.stderr.strip()[-300:], flush=True)
        return
    changed = 0
    for rel, src in FILES.items():
        if not os.path.exists(src):
            continue
        dst = os.path.join(DEST, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst) or open(src, "rb").read() != open(dst, "rb").read():
            shutil.copyfile(src, dst)
            changed += 1
    if not changed:
        print(time.strftime("%H:%M:%S"), "up to date", flush=True)
        return
    git("add", os.path.relpath(DEST, REPO))
    msg = f"Agent 2 findings sync {time.strftime('%Y-%m-%d %H:%M')} ({changed} files)"
    r = git("commit", "-m", msg + "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    if r.returncode != 0:
        print(time.strftime("%H:%M:%S"), "commit:", (r.stdout + r.stderr).strip()[-300:], flush=True)
        return
    r = git("push", "-u", "origin", BRANCH)
    print(time.strftime("%H:%M:%S"), f"pushed {changed} files" if r.returncode == 0 else "push failed: " + r.stderr.strip()[-300:], flush=True)


while True:
    sync()
    if ONCE:
        break
    time.sleep(INTERVAL)
