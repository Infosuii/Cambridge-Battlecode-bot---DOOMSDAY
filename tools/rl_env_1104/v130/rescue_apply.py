"""Build a candidate from rescue_select.py choices: the knob table (cl_rescue_table.h) and/or the lineup table
(cl_rescue_lineup.h) with only the chosen maps. usage: rescue_apply.py REPO BASE_SRC OUT_DIR [--knob CHOICE.json] [--lineup CHOICE.json]"""
import argparse, json, os, shutil, sys

ap = argparse.ArgumentParser()
ap.add_argument("repo")
ap.add_argument("base")
ap.add_argument("out")
ap.add_argument("--knob")
ap.add_argument("--lineup")
a = ap.parse_args()
sys.path.insert(0, os.path.join(a.repo, "tools", "rl_env_1104", "v130"))
sys.path.insert(0, os.path.join(a.repo, "tools", "rl_env_1104"))
sys.argv = [sys.argv[0], a.repo, a.base, "-", "-"]  # rescue_build reads argv at import
import rescue_build as rb  # noqa: E402
assert not os.path.exists(a.out), a.out
shutil.copytree(a.base, os.path.join(a.out, "src"))
src = os.path.join(a.out, "src")
fps = rb.fps
if a.knob:
    ch = json.load(open(a.knob, encoding="utf-8"))["choice"]
    rows = [(fps[m], rb.names.index(p), m) for m, p in sorted(ch.items())]
    rb.install(src, rows)
    print("knob table:", {m: p for m, p in sorted(ch.items())})
if a.lineup:
    ch = json.load(open(a.lineup, encoding="utf-8"))["choice"]
    sys.argv = [sys.argv[0], a.repo, a.base, "-", "0"]
    import rescue_lineup_build as rl  # noqa: E402
    rl.maps = sorted(ch)
    rows = "\n".join(f"    {{{fps[m][0]}, {fps[m][1]}, {fps[m][2]}, {int(ch[m])}}}, // {m}" for m in sorted(ch))
    open(os.path.join(src, "cl_rescue_lineup.h"), "w", encoding="utf-8").write(
        "// CL_RESCUE_LINEUP: per-map kLineups row (tools/rl_env_1104/v130/rescue_apply.py)\n#pragma once\n"
        "namespace cl_rescue_lineup {\nstruct Row { int w, h, groups, lineup; };\n"
        f"inline constexpr Row kRows[] = {{\n{rows}\n}};\n}} // namespace cl_rescue_lineup\n")
    rl.patch(src, "common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_RESCUE_LINEUP 1\n")
    t = open(os.path.join(src, "draft.cpp"), encoding="utf-8", newline="").read()
    i = t.index("#include")
    open(os.path.join(src, "draft.cpp"), "w", encoding="utf-8", newline="").write(t[:i] + '#include "cl_rescue_lineup.h"\n' + t[i:])
    rl.patch(src, "draft.cpp", rl.ANCHOR, rl.ANCHOR + rl.CODE)
    print("lineup table:", {m: int(v) for m, v in sorted(ch.items())})
print("built", a.out)
