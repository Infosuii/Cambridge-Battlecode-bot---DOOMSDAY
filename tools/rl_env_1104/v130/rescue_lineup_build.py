"""Per-map lineup rescue for v137: one candidate per kLineups row, drafting that lineup on the target maps only (matched
in the draft by width, height and camp-group count, as LADDER_TABLES' v70_lineup does).
usage: rescue_lineup_build.py REPO BASE_SRC OUT_PREFIX N_LINEUPS map1 map2 ...  -> OUT_PREFIX_<i>/src"""
import json, os, shutil, sys

repo, base, prefix, n_lineups = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
maps = sys.argv[5:]
sys.path.insert(0, os.path.join(repo, "tools", "rl_env_1104"))
from cl_patches import patch  # noqa: E402

fps = json.load(open(os.path.join(repo, "artifacts", "tmp", "fingerprints_1108.json"), encoding="utf-8"))
keys = {}
for m, fp in fps.items():
    keys.setdefault(tuple(fp[:3]), []).append(m)
clash = {m: keys[tuple(fps[m][:3])] for m in maps if len(keys[tuple(fps[m][:3])]) > 1}
assert not clash, f"(w, h, groups) not unique: {clash}"
ANCHOR = "        v70 = v70_lineup(bc::map::width(), bc::map::height(), size, static_cast<int>(v70_ng));\n"
CODE = ("#if CL_RESCUE_LINEUP\n"
        "        for (const auto& row : cl_rescue_lineup::kRows)\n"
        "            if (row.w == bc::map::width() && row.h == bc::map::height() && row.groups == static_cast<int>(v70_ng)) {\n"
        "                v70 = row.lineup; // CL_RESCUE_LINEUP: this map's lineup from the rescue screen\n"
        "                break;\n"
        "            }\n"
        "#endif\n")


def install(src, li):
    rows = "\n".join(f"    {{{fps[m][0]}, {fps[m][1]}, {fps[m][2]}, {li}}}, // {m}" for m in maps)
    open(os.path.join(src, "cl_rescue_lineup.h"), "w", encoding="utf-8").write(
        "// CL_RESCUE_LINEUP: per-map kLineups row on maps where v137 collapses (tools/rl_env_1104/v130/rescue_lineup_build.py)\n"
        "#pragma once\nnamespace cl_rescue_lineup {\nstruct Row { int w, h, groups, lineup; };\n"
        f"inline constexpr Row kRows[] = {{\n{rows}\n}};\n}} // namespace cl_rescue_lineup\n")
    patch(src, "common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_RESCUE_LINEUP 1\n")
    t = open(os.path.join(src, "draft.cpp"), encoding="utf-8", newline="").read()
    first_include = t.index("#include")
    t = t[:first_include] + '#include "cl_rescue_lineup.h"\n' + t[first_include:]
    open(os.path.join(src, "draft.cpp"), "w", encoding="utf-8", newline="").write(t)
    patch(src, "draft.cpp", ANCHOR, ANCHOR + CODE)


for li in range(n_lineups):
    d = f"{prefix}_{li}"
    if os.path.exists(d):
        continue
    shutil.copytree(base, os.path.join(d, "src"))
    install(os.path.join(d, "src"), li)
print(n_lineups, "lineup candidates for", len(maps), "maps")
