"""Platform match analysis (E63): per game from extract.js JSON (+ the team-a .fuel log): map, lineups, result, gems /
gold / strength / deaths over time, and our fuel per turn. We are team A (team 0): the fuel log is team A's.
usage: python match_report.py DIR   (DIR has g*.json from tools/viz/extract.js and g*.fuel)"""
import glob
import json
import os
import struct
import sys

NAMES = ["Ryth", "Vesper", "Vendetta", "Cassi", "Issac", "Stellar", "Prism", "Marcella", "Willow", "Ren", "Varg", "Tavi", "Heart"]
D = sys.argv[1]
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
feats = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mld_feats_v4.json")))
official = {}
for k, v in feats.items():
    if k.startswith("maps/"):
        f = v[0]
        official.setdefault((round(f[0] * 100), round(f[1] * 100)), []).append(k[5:-7])


def fuel(path, size):
    b = open(path, "rb").read()
    vals = [struct.unpack_from("<Q", b, o)[0] for o in range(13, len(b) - 7, 8)]
    turns = vals[8:]
    draft, champ = turns[:size], turns[size:]
    first = champ[:size]
    rest = champ[size:]
    return draft, first, rest


rows = []
for jf in sorted(glob.glob(os.path.join(D, "[gh][0-9]*.json"))):
    name = os.path.basename(jf)[:-5]
    d = json.load(open(jf))
    R = d["rounds"]
    fin = R[-1]
    teams = [[c for c in fin["champs"] if c["team"] == t] for t in (0, 1)]
    size = len(teams[0])
    maps = official.get((d["W"], d["H"]), ["?"])
    sub = fin["sub"]
    res = "WIN" if sub[0] > sub[1] else "LOSS" if sub[0] < sub[1] else "DRAW"
    print(f"=== {name}: map {d['W']}x{d['H']} ({'/'.join(maps)}), {size}v{size}, rounds {fin['round']}, banked us {sub[0]} - them {sub[1]} -> {res}")
    for t in (0, 1):
        print(f"  {'us  ' if t == 0 else 'them'}: " + ", ".join(f"{NAMES[c['type']]}(str {c['str']:.0f} foc {c['foc']:.0f} hp {c['mhp']})" for c in teams[t]))
    # timeline
    deaths = [[0, 0, 0], [0, 0, 0]]  # per team: rounds <300, 300-700, >700
    prev = {}
    for s in R:
        for c in s["champs"]:
            k = c["h"]
            if prev.get(k) == 1 and c["alive"] == 0:
                ph = 0 if s["round"] < 300 else 1 if s["round"] < 700 else 2
                deaths[c["team"]][ph] += 1
            prev[k] = c["alive"]
    line = "  t:"
    for target in (100, 200, 300, 400, 600, 800, 1000):
        s = next((x for x in R if x["round"] >= target), None)
        if not s or not s["champs"]:
            continue
        car = [sum(c["gems"] for c in s["champs"] if c["team"] == t) for t in (0, 1)]
        gold = [sum(c["gold"] for c in s["champs"] if c["team"] == t) for t in (0, 1)]
        st = [sum(c["str"] + c["foc"] / 2 + c["mhp"] / 20 for c in s["champs"] if c["team"] == t) for t in (0, 1)]
        line += f" r{target} bank {s['sub'][0]}/{s['sub'][1]} carry {car[0]}/{car[1]} power {st[0]:.0f}/{st[1]:.0f} |"
    print(line)
    print(f"  deaths us {deaths[0]} (r<300, 300-700, >700), them {deaths[1]}")
    ff = os.path.join(D, name + ".fuel")
    if os.path.exists(ff):
        dr, first, rest = fuel(ff, size)
        over = sum(1 for v in rest if v >= 99000)
        hi = sum(1 for v in rest if v >= 90000)
        mean = sum(rest) / max(1, len(rest))
        print(f"  fuel: draft {[round(v / 1000) for v in dr]}k; champion turn 1 {[round(v / 1000) for v in first]}k (budget 200k); "
              f"later turns mean {mean / 1000:.0f}k, >=90k {hi} ({100 * hi / max(1, len(rest)):.1f}%), >=99k {over} of {len(rest)}")
    rows.append((name, res, sub, size, maps))
print()
w = sum(1 for r in rows if r[1] == "WIN")
print(f"total: {w} wins / {len(rows)} games")
