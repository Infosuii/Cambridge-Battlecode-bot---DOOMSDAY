"""Compare bots on the same duel_lab scenarios (same seed): luck-free best-move rate (the bot's own turn within 0.5 /
1.0 of the brute-forced best, scored on fresh variants) and mean shortfall, overall and on duels where the bot is
clearly behind on health.

usage: python duel_compare.py name=file.jsonl [name=file.jsonl ...]
"""
import json
import sys


def load(path):
    out = {}
    for line in open(path):
        if not line.strip():
            continue
        r = json.loads(line)
        if not r.get("fresh") or not r.get("actorType") or not all(r["types"]["B"]):
            continue
        out[r["k"]] = r
    return out


def main():
    sets = [(a.split("=", 1)[0], load(a.split("=", 1)[1])) for a in sys.argv[1:]]
    common = set.intersection(*(set(s) for _, s in sets))
    print(f"{len(common)} scenarios present in every run")
    for name, s in sets:
        rs = [s[k] for k in sorted(common)]
        fr = [max(0.0, r["fresh"]["regret"]) for r in rs]
        behind = [max(0.0, r["fresh"]["regret"]) for r in rs if r["hp"][0] - r["hp"][1] < -0.15]
        n = len(fr)
        print(f"  {name:12s} within 0.5: {sum(x < 0.5 for x in fr) / n:4.0%}  within 1.0: {sum(x < 1 for x in fr) / n:4.0%}  "
              f"mean shortfall {sum(fr) / n:5.2f}  | behind on health ({len(behind)}): mean {sum(behind) / max(1, len(behind)):5.2f}")


if __name__ == "__main__":
    main()
