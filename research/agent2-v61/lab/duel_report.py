"""Report on duel_lab.js output: how good is the bot's own fight turn against the engine's brute-forced best, per
champion type, and what the better turns do differently (spells, order, attacks, moving in or out).

usage: python duel_report.py agent2/lab/duel_1v1.jsonl [agent2/lab/duel_2v2.jsonl ...]
"""
import json
import sys
from collections import defaultdict
from pathlib import Path


def kinds(acts):
    a = acts.split() if acts and acts != "pass" else []
    return {
        "cast": any(x.startswith("cast") for x in a),
        "attack": any(x.startswith("attack") for x in a),
        "move": any(x.startswith("move") for x in a),
        "cast_first": bool(a) and a[0].startswith("cast"),
        "double_attack": sum(x.startswith("attack") for x in a) >= 2,
    }


def own_kinds(own):
    a = own.split() if own else []
    return {
        "cast": any(x.startswith("cast") for x in a),
        "attack": any(x == "attack" for x in a),
        "move": any(x == "move_to" for x in a),
        "cast_first": bool(a) and a[0].startswith("cast"),
        "double_attack": sum(x == "attack" for x in a) >= 2,
    }


def main():
    rows = []
    for f in sys.argv[1:]:
        for line in Path(f).read_text().splitlines():
            if line.strip() and '"abort"' not in line:
                r = json.loads(line)
                # Broken setups (a fighter missing) are dropped; a bot turn the option list cannot express counts as best.
                if len(r["types"]["A"]) < r["size"] or len(r["types"]["B"]) < r["size"] or not r.get("actorType"):
                    continue
                r["best"] = max(r["best"], r["own"])
                rows.append(r)
    for size in sorted({r["size"] for r in rows}):
        rs = [r for r in rows if r["size"] == size]
        regret = [r["best"] - r["own"] for r in rs]
        opt = sum(1 for g in regret if g < 0.5)
        print(f"\n== {size}v{size}: {len(rs)} scenarios; bot's turn within 0.5 of the best in {opt} ({opt / len(rs):.0%}); "
              f"mean regret {sum(regret) / len(rs):.2f} value (25 = a life, 12 = a full health bar)")
        print(f"   bot vs the average legal turn: {sum(r['own'] - r['meanOption'] for r in rs) / len(rs):+.2f}")
        big = [r for r in rs if r["best"] - r["own"] >= 3]
        print(f"   big misses (regret >= 3): {len(big)} ({len(big) / len(rs):.0%})")
        # What the better turn did differently, on the big misses.
        diff = defaultdict(int)
        for r in big:
            o, b = own_kinds(r["ownActs"]), kinds(r["bestActs"])
            for k in o:
                if o[k] != b[k]:
                    diff[f"{k}: bot {'yes' if o[k] else 'no'} -> best {'yes' if b[k] else 'no'}"] += 1
        for k, v in sorted(diff.items(), key=lambda kv: -kv[1]):
            print(f"     {k}: {v}")
        # Per actor type.
        by = defaultdict(list)
        for r in rs:
            by[r.get("actorType") or "?"].append(r)
        print("   per champion (n, optimal share, mean regret, big misses):")
        for t, lst in sorted(by.items(), key=lambda kv: -sum(x["best"] - x["own"] for x in kv[1]) / len(kv[1])):
            g = [x["best"] - x["own"] for x in lst]
            print(f"     {t:9s} n={len(lst):3d}  optimal {sum(1 for x in g if x < 0.5) / len(lst):4.0%}  regret {sum(g) / len(lst):5.2f}  big {sum(1 for x in g if x >= 3)}")
        print("   worst examples:")
        for r in sorted(rs, key=lambda r: r["own"] - r["best"])[:6]:
            print(f"     {r.get('actorType', '?')} vs {'+'.join(str(x) for x in r['types']['B'])} hp {r['hp']} gap {r['gap']}: bot [{r['ownActs']}] {r['own']} | best [{r['bestActs']}] {r['best']}")


if __name__ == "__main__":
    main()
