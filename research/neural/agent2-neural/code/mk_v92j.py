"""E123: v4/bots/v92jN = v92 + a tiny seeded jitter on farm_score (+-0.5% per group, redrawn every 16 rounds). The engine is deterministic
per pairing, so 70 official maps x 2 sides give only 140 games against v92; v92jN gives independent games on the same maps from what is
still v92. v92 itself is untouched. Check before trusting it: v92jN vs v92 must stay near 50%.
usage (project root): python -P agent2/lab/mk_v92j.py N [N ...]"""
import os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
B = os.path.join(ROOT, "v4", "bots")
for n in sys.argv[1:]:
    name = f"v92j{n}"
    shutil.rmtree(os.path.join(B, name), ignore_errors=True)
    shutil.copytree(os.path.join(B, "v92"), os.path.join(B, name), ignore=shutil.ignore_patterns(".cambc"))
    p = os.path.join(B, name, "src", "bot.cpp")
    s = open(p, encoding="utf-8").read()
    old = "        float score = value / cost;\n"
    new = old + (
        "        {\n"
        f"            std::uint32_t jit = {int(n)}u * 2654435761u ^ static_cast<std::uint32_t>(gi) * 40503u ^ static_cast<std::uint32_t>(round / 16) * 2246822519u;\n"
        "            jit = jit * 1664525u + 1013904223u, jit = jit * 1664525u + 1013904223u;\n"
        "            score *= 1.0f + 0.01f * (static_cast<float>(jit >> 8) / 16777216.0f - 0.5f);\n"
        "        }\n")
    assert s.count(old) == 1
    open(p, "w", encoding="utf-8", newline="\n").write(s.replace(old, new))
    r = subprocess.run([os.path.join(ROOT, "v4", "cambc.exe"), "build", f"bots/{name}", "--release"], cwd=os.path.join(ROOT, "v4"), capture_output=True, text=True)
    print(name, "built" if r.returncode == 0 else r.stdout[-800:] + r.stderr[-800:], flush=True)
