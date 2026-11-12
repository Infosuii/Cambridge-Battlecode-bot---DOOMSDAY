"""E124: v4/bots/v92skP = v92 that runs out of fuel on P per mille of its turns (it spins until the round changes, so it loses the next turn, as a real overrun does): what is an overrun worth?
usage (project root): python -P agent2/lab/mk_v92sk.py P [P ...]"""
import os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
B = os.path.join(ROOT, "v4", "bots")
for n in sys.argv[1:]:
    name = f"v92sk{n}"
    shutil.rmtree(os.path.join(B, name), ignore_errors=True)
    shutil.copytree(os.path.join(B, "v92"), os.path.join(B, name), ignore=shutil.ignore_patterns(".cambc"))
    p = os.path.join(B, name, "src", "main.cpp")
    s = open(p, encoding="utf-8").read()
    old = "            else\n                bot.play_turn();\n#endif"
    new = ("            else {\n                bot.play_turn();\n"
           "                {\n"
           "                    static std::uint32_t h = 2166136261u;\n"
           "                    const std::uint32_t r0 = bc::round_number();\n"
           "                    h = (h ^ r0) * 16777619u;\n"
           f"                    if ((h >> 7) % 1000u < {int(n)}u) while (bc::round_number() == r0) {{}}\n"
           "                }\n"
           "            }\n#endif")
    assert s.count(old) == 1
    open(p, "w", encoding="utf-8", newline="\n").write(s.replace(old, new))
    r = subprocess.run([os.path.join(ROOT, "v4", "cambc.exe"), "build", f"bots/{name}", "--release"], cwd=os.path.join(ROOT, "v4"), capture_output=True, text=True)
    print(name, "built" if r.returncode == 0 else (r.stdout + r.stderr)[-600:], flush=True)
