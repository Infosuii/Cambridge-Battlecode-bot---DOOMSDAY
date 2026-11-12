"""Idle-mode attribution from MD trace rows (v112log copy: `MD round slot mode x y hp gems target ne nvis`).

For the traced team in each game, finds runs of >= MIN consecutive turns in which a body stays on one tile, and
attributes the run's turns to the mode string(s) printed. Reports turns per game by mode for idle runs, plus the
overall mode mix, and lists the longest runs with their context.

usage: python -I tools/rl_env_1104/strategy/mode_idle.py runs/rl_env_1104/eval/v112-stall-trace-01 [--min 8]
"""
import argparse
import collections
import glob
import json
import os
import zipfile


def rows_for(bundle_dir, side):
    rep = glob.glob(os.path.join(bundle_dir, "*.repl26a"))
    if not rep:
        return []
    z = zipfile.ZipFile(rep[0])
    name = f"team-{side.lower()}.stdout"
    if name not in z.namelist():
        return []
    txt = z.read(name).replace(bytes(1), b"\n").decode("utf-8", "replace")
    out = []
    for l in txt.splitlines():
        q = l.split()
        if len(q) == 11 and q[0] == "MD":
            try:
                out.append(dict(r=int(q[1]), slot=int(q[2]), mode=q[3], x=int(q[4]), y=int(q[5]), hp=int(q[6]), gems=int(q[7]),
                                tg=int(q[8]), ne=int(q[9]), nv=int(q[10])))
            except ValueError:
                pass
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--min", type=int, default=8)
    a = ap.parse_args()
    idle = collections.Counter(); allm = collections.Counter(); games = 0; longest = []
    for d in sorted(glob.glob(os.path.join(a.run, "*-[AB]"))):
        side = d[-1]
        rows = rows_for(d, side)
        if not rows:
            continue
        games += 1
        res = json.load(open(d + ".json", encoding="utf-8"))["match"]["outcome"]
        by = collections.defaultdict(list)
        for r in rows:
            by[r["slot"]].append(r); allm[r["mode"]] += 1
        for slot, rs in by.items():
            rs.sort(key=lambda r: r["r"])
            i = 0
            while i < len(rs):
                j = i
                while j + 1 < len(rs) and (rs[j + 1]["x"], rs[j + 1]["y"]) == (rs[i]["x"], rs[i]["y"]) and rs[j + 1]["r"] == rs[j]["r"] + 1:
                    j += 1
                L = j - i + 1
                if L >= a.min and min(r["ne"] for r in rs[i:j + 1]) > 4:
                    modes = collections.Counter(r["mode"] for r in rs[i:j + 1])
                    for m, c in modes.items():
                        idle[m] += c
                    longest.append((L, os.path.basename(d), "won" if res == f"team{side}" else "lost", slot, rs[i]["r"], (rs[i]["x"], rs[i]["y"]), rs[i]["hp"], rs[i]["gems"], rs[i]["tg"], dict(modes)))
                i = j + 1
    print("games", games)
    print("idle (no enemy within 4) turns per game by mode:", {m: round(c / games, 1) for m, c in idle.most_common(15)})
    print("all turns per game by mode:", {m: round(c / games, 1) for m, c in allm.most_common(25)})
    for x in sorted(longest, reverse=True)[:25]:
        print(x)


if __name__ == "__main__":
    main()
