"""E125: v4/bots/NAME = v92 that spends its spare fuel on the distance fields sooner. v92 builds them at the end of its turn, only if the fuel left exceeds the field's cost + a 30-35k margin. On a 100x100 map a field costs about 43k, so with
v92's usual 40k turn the margin is rarely met, and it plays the opening without walking distances to most camp groups. Nothing heavy runs after this point in a turn: M = the margin kept (fuel not spent is lost anyway).
usage (project root): python -P agent2/lab/mk_v92f.py NAME M"""
import os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
B = os.path.join(ROOT, "v4", "bots")
NAME, M = sys.argv[1], int(sys.argv[2])
shutil.rmtree(os.path.join(B, NAME), ignore_errors=True)
shutil.copytree(os.path.join(B, "v92"), os.path.join(B, NAME), ignore=shutil.ignore_patterns(".cambc"))
p = os.path.join(B, NAME, "src", "bot.cpp")
s = open(p, encoding="utf-8").read()
old = "                full + static_cast<std::uint64_t>(NOVA_FUEL_OPEN ? 30000 : tune::kDetSafety);\n"
assert s.count(old) == 1
s = s.replace(old, f"                full + static_cast<std::uint64_t>({M});\n")
open(p, "w", encoding="utf-8", newline="\n").write(s)
r = subprocess.run([os.path.join(ROOT, "v4", "cambc.exe"), "build", f"bots/{NAME}", "--release"], cwd=os.path.join(ROOT, "v4"), capture_output=True, text=True)
print(NAME, "built" if r.returncode == 0 else (r.stdout + r.stderr)[-800:], flush=True)
