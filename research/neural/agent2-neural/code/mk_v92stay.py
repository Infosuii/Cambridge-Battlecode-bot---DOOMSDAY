"""E124: v4/bots/NAME = v92 + a rule taken from the blend's overrides (nn_ens_why.py, nn_ens_rule.py: 94% of them keep the current target against v92's wish to switch).
In farm(), after v92's own choice: if v92 wants to leave a target that is still open (not banned, respawning with at most T rounds to go), it stays. No fuel. Optional: only when v92's new pick is on the enemy's side (--enemy-side),
or a different soft stickiness (--sticky X, v92 has 1.523).
usage (project root): python -P agent2/lab/mk_v92stay.py NAME T [--enemy-side] [--sticky X]"""
import os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
B = os.path.join(ROOT, "v4", "bots")
A = sys.argv[1:]
NAME, T = A[0], int(A[1])
ES = "--enemy-side" in A
STICKY = A[A.index("--sticky") + 1] if "--sticky" in A else None
shutil.rmtree(os.path.join(B, NAME), ignore_errors=True)
shutil.copytree(os.path.join(B, "v92"), os.path.join(B, NAME), ignore=shutil.ignore_patterns(".cambc"))
p = os.path.join(B, NAME, "src", "bot.cpp")
s = open(p, encoding="utf-8").read()
old = '    PROF_CHECK("farmsel");\n'
assert s.count(old) == 1
if T >= 0:
    side = "" if not ES else " && w.enemy_ready && best < static_cast<int>(w.group_margin.size()) && w.group_margin[static_cast<std::size_t>(best)] <= 0"
    new = old + (
        "    if (best >= 0 && best != target_group && target_group >= 0 && target_group < static_cast<int>(w.groups.size()) &&\n"
        "        avoid_until[static_cast<std::size_t>(target_group)] <= round" + side + ") {\n"
        "        const auto& stay_g = w.groups[static_cast<std::size_t>(target_group)];\n"
        f"        if (stay_g.state != GroupState::respawning || stay_g.respawn_round - round <= {T}) best = target_group, best_need = 1;\n"
        "    }\n")
    s = s.replace(old, new)
open(p, "w", encoding="utf-8", newline="\n").write(s)
if STICKY:
    p = os.path.join(B, NAME, "src", "common.h")
    c = open(p, encoding="utf-8").read()
    assert c.count("#define APEX_STICKY 1.5230f") == 1
    open(p, "w", encoding="utf-8", newline="\n").write(c.replace("#define APEX_STICKY 1.5230f", f"#define APEX_STICKY {STICKY}f"))
r = subprocess.run([os.path.join(ROOT, "v4", "cambc.exe"), "build", f"bots/{NAME}", "--release"], cwd=os.path.join(ROOT, "v4"), capture_output=True, text=True)
print(NAME, "built" if r.returncode == 0 else (r.stdout + r.stderr)[-800:], flush=True)
