"""Per-map rescue for v137 (v135 lineage): one candidate per research/v71 knob profile, applying that profile on the
target maps only (matched by fingerprint w, h, groups, total gems), plus the matching eval manifest.
The table code is cl_patches.newmap_table's, but applied whether or not LADDER_TABLES knows the map (knob deltas add).
usage: rescue_build.py REPO BASE_SRC OUT_PREFIX MANIFEST_OUT map1 map2 ...
  -> OUT_PREFIX_<profile>/src for every profile, MANIFEST_OUT (development split, ladder-pool map files)"""
import json, os, shutil, sys

repo, base, prefix, man_out = sys.argv[1:5]
maps = sys.argv[5:]
sys.path.insert(0, os.path.join(repo, "tools", "rl_env_1104"))
from cl_patches import PROFILES, patch  # noqa: E402

fps = json.load(open(os.path.join(repo, "artifacts", "tmp", "fingerprints_1108.json"), encoding="utf-8"))
names = sorted(PROFILES)
ANCHOR = "                break;\n            }\n        }\n    }\n    {\n        // Engine-lab joint search"
CODE = """#if CL_RESCUE_TABLE
        for (const auto& row : cl_rescue::kRows)
            if (row.w == w.width && row.h == w.height && row.groups == n_groups && row.gems == total_gems) {
                for (int i = 0; i < 48; ++i) lab::knobs[i] += cl_rescue::kDelta[row.profile][i];
                break;
            }
#endif
"""


def header(rows):
    out = ["// CL_RESCUE_TABLE: per-map knob profile on maps where v137 collapses (tools/rl_env_1104/v130/rescue_build.py)",
           "#pragma once", "namespace cl_rescue {", "struct Row { int w, h, groups; unsigned gems; int profile; };",
           "inline constexpr Row kRows[] = {"]
    out += [f"    {{{fp[0]}, {fp[1]}, {fp[2]}, {fp[3]}u, {pi}}}, // {m}: {names[pi]}" for fp, pi, m in rows] or ["    {-1, -1, -1, 0u, 0},"]
    out += ["};", f"inline constexpr int kNumProfiles = {len(names)};", "inline constexpr float kDelta[kNumProfiles][48] = {"]
    for p in names:
        v = [0.0] * 48
        for k, d in PROFILES[p].items():
            v[k] = d
        out.append("    {" + ",".join(f"{x:.4f}f" for x in v) + "}, // " + p)
    out += ["};", "} // namespace cl_rescue", ""]
    return "\n".join(out)


def install(src, rows):
    open(os.path.join(src, "cl_rescue_table.h"), "w", encoding="utf-8").write(header(rows))
    patch(src, "common.h", "#define A2_KITFIX 31\n", "#define A2_KITFIX 31\n#define CL_RESCUE_TABLE 1\n")
    patch(src, "bot.cpp", '#include "a2map.h"\n', '#include "a2map.h"\n#if CL_RESCUE_TABLE\n#include "cl_rescue_table.h"\n#endif\n')
    patch(src, "bot.cpp", ANCHOR, ANCHOR.replace("        }\n    }\n    {", "        }\n" + CODE + "    }\n    {", 1))


if __name__ == "__main__":
    missing = [m for m in maps if m not in fps]
    assert not missing, missing
    for p in names:
        d = f"{prefix}_{p}"
        if os.path.exists(d):
            continue
        shutil.copytree(base, os.path.join(d, "src"))
        install(os.path.join(d, "src"), [(fps[m], names.index(p), m) for m in maps])
    man = json.load(open(os.path.join(repo, "research", "rl_env_1104", "candidates", "manifests", "new83_1108.json"), encoding="utf-8"))
    pool = {x["file"].replace(".map26a", ""): x for x in json.load(open(os.path.join(repo, "research", "rl_env_1104", "candidates", "manifests", "new83_1108.json"), encoding="utf-8"))["maps"]}
    for f in ("final53_1108.json", "recog36_1110.json"):
        for x in json.load(open(os.path.join(repo, "research", "rl_env_1104", "candidates", "manifests", f), encoding="utf-8"))["maps"]:
            pool.setdefault(x["file"].replace(".map26a", ""), x)
    man["maps"] = [dict(pool[m], split="development") for m in maps]
    man["counts"] = {"development": len(maps)}
    man["status"] = "RESCUE_1110: v137's worst maps on the local panels (per-map profile screen)"
    json.dump(man, open(man_out, "w", encoding="utf-8"), indent=1)
    print(len(names), "profile candidates;", len(maps), "maps; manifest", man_out)
