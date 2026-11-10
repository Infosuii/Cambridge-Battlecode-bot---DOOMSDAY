"""Build a v139 combination candidate: OUT/src = v139 + chosen changes.
usage: combo139.py REPO V139_SRC OUT [--bt] [--follow] [--plan BITS] [--knob NAME=VALUE ...]
--bt: CL_BUMP (bump_patch139.py) + CL_TRIBALERT (trib_patch.py); --follow: CL_FOLLOW; --plan: CL_PLAN bits;
--knob: rewrite '#define NAME old' to '#define NAME VALUE' in common.h (exactly one definition must exist)."""
import argparse, os, re, shutil, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("repo")
ap.add_argument("base")
ap.add_argument("out")
ap.add_argument("--bt", action="store_true")
ap.add_argument("--follow", action="store_true")
ap.add_argument("--plan", type=int, default=0)
ap.add_argument("--crew", type=int, default=0)
ap.add_argument("--knob", action="append", default=[])
a = ap.parse_args()
assert not os.path.exists(a.out), a.out
src = os.path.join(a.out, "src")
shutil.copytree(a.base, src)
T = os.path.join(a.repo, "tools", "rl_env_1104", "v130")


def run(script, *args):
    r = subprocess.run([sys.executable, "-I", os.path.join(T, script), *args], capture_output=True, text=True)
    assert r.returncode == 0, (script, r.stdout[-800:], r.stderr[-800:])
    print(r.stdout.strip().splitlines()[-1])


if a.bt:
    run("bump_patch139.py", src)
    run("trib_patch.py", src)
if a.follow:
    run("follow_patch.py", src)
if a.crew:
    run("crew_patch.py", src, str(a.crew))
if a.plan:
    run("clplan_patch.py", a.repo, src, str(a.plan))
for kv in a.knob:
    name, value = kv.split("=", 1)
    p = os.path.join(src, "common.h")
    t = open(p, encoding="utf-8", newline="").read()
    pat = re.compile(r"^#define " + re.escape(name) + r" [^\n]*$", re.M)
    assert len(pat.findall(t)) == 1, (name, pat.findall(t))
    t = pat.sub(lambda m: f"#define {name} {value}", t)
    open(p, "w", encoding="utf-8", newline="").write(t)
    print("knob", name, "=", value)
print("built", a.out)
