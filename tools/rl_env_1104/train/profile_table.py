"""Choose a research/v71 knob profile per new map from a profile_select.sh run, and emit the bot table.

For every map: each profile's paired gain = sum over identical cells (opponent x side) of (profile score - v112
score). A map takes the profile with the largest gain if that gain is >= --min-gain (in games) and the profile never
loses a cell that v112 won by more than --max-loss cells; otherwise the map keeps v112's own play. Writes:
  <out>.json   per-map choice and evidence
  <out>.h      C++ rows {w, h, groups, gems, profile index} + the profile delta table, for cl_patches.newmap_table
usage: python -I tools/rl_env_1104/train/profile_table.py runs/rl_env_1104/eval/<OUT> artifacts/tmp/fingerprints_1108.json <out> [--min-gain 2] [--max-loss 1]
"""
import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from cl_patches import PROFILES  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("fingerprints")
    ap.add_argument("out")
    ap.add_argument("--min-gain", type=float, default=2.0)
    ap.add_argument("--max-loss", type=int, default=1)
    a = ap.parse_args()
    rep = json.load(open(os.path.join(a.run, "report.json"), encoding="utf-8"))
    fps = json.load(open(a.fingerprints, encoding="utf-8"))
    score = {}
    for g in rep["games"]:
        if g.get("status") != "ok":
            continue
        score[(g["candidate"], g["map"], g["opponent"], g["side"])] = g["score"]
    profs = [c for c in rep["candidates"] if c != "v112"]
    maps = sorted({k[1] for k in score})
    choice, evidence = {}, {}
    for m in maps:
        cells = [(o, s) for (c, mm, o, s) in score if c == "v112" and mm == m]
        best, best_gain = None, 0.0
        ev = {}
        for p in profs:
            gain, losses, n = 0.0, 0, 0
            for o, s in cells:
                if (p, m, o, s) not in score:
                    continue
                d = score[(p, m, o, s)] - score[("v112", m, o, s)]
                gain += d
                losses += d < 0
                n += 1
            ev[p] = dict(gain=gain, losses=losses, n=n)
            if n == len(cells) and gain >= a.min_gain and losses <= a.max_loss and gain > best_gain:
                best, best_gain = p, gain
        evidence[m] = dict(cells=len(cells), v112_score=sum(score[("v112", m, o, s)] for o, s in cells), profiles=ev)
        if best:
            choice[m] = best
    names = sorted(PROFILES)
    rows = []
    for m, p in sorted(choice.items()):
        fp = fps.get(m)
        if fp:
            rows.append((fp, names.index(p), m, p))
    json.dump(dict(min_gain=a.min_gain, max_loss=a.max_loss, choice=choice, evidence=evidence), open(a.out + ".json", "w"), indent=1)
    with open(a.out + ".h", "w", encoding="utf-8") as f:
        f.write("// CL_NEWMAP_TABLE: per-map research/v71 profile on maps v112 does not recognise (tools/rl_env_1104/train/profile_table.py)\n")
        f.write("#pragma once\nnamespace cl_newmap {\nstruct Row { int w, h, groups; unsigned gems; int profile; };\n")
        f.write("inline constexpr Row kRows[] = {\n")
        for fp, pi, m, p in rows:
            f.write(f"    {{{fp[0]}, {fp[1]}, {fp[2]}, {fp[3]}u, {pi}}}, // {m}: {p}\n")
        if not rows:
            f.write("    {-1, -1, -1, 0u, 0},\n")
        f.write("};\ninline constexpr int kNumProfiles = %d;\ninline constexpr float kDelta[kNumProfiles][48] = {\n" % len(names))
        for p in names:
            v = [0.0] * 48
            for k, d in PROFILES[p].items():
                v[k] = d
            f.write("    {" + ",".join(f"{x:.4f}f" for x in v) + "}, // " + p + "\n")
        f.write("};\n} // namespace cl_newmap\n")
    print(f"{len(choice)} of {len(maps)} maps switched:", collections.Counter(choice.values()).most_common())
    print("in-sample switched gain (games):", sum(evidence[m]["profiles"][p]["gain"] for m, p in choice.items()))


if __name__ == "__main__":
    main()
