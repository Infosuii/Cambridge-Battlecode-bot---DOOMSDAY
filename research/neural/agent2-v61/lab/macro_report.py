"""Report on macro_lab.js: does forbidding the bot's camp choice, banking small bags now, or holding a bag change the
team gem margin 150 rounds later? Overall and split by bag, distance to target and game phase.

usage: python macro_report.py agent2/lab/macro.jsonl
"""
import json
import statistics as st
import sys


def ms(a):
    if len(a) < 3:
        return f"n {len(a)}"
    return f"{st.mean(a):+6.1f} ± {st.stdev(a) / len(a) ** 0.5:4.1f} (n {len(a):3d}; alt better {sum(x > 0 for x in a):3d}, worse {sum(x < 0 for x in a):3d}, same {sum(x == 0 for x in a):3d})"


def main():
    rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
    print(f"{len(rows)} states (team gems 150 rounds after the intervention; + means the alternative beat the bot)")
    for k, label in [("forbid", "forbid current camp 20 rounds"), ("bank", "bank a small bag (8-19) now"), ("hold", "hold a 20+ bag 30 rounds")]:
        rs = [r[k] for r in rows if r.get(k)]
        print(f"\n== {label}: {ms([x['d'] for x in rs])}")
        if k == "forbid":
            for lo, hi in [(0, 4), (4, 10), (10, 99)]:
                print(f"   target {lo}-{hi - 1} tiles away: {ms([x['d'] for x in rs if lo <= x['dist'] < hi])}")
        else:
            for lo, hi in [(8, 20), (20, 40), (40, 999)]:
                sel = [x["d"] for x in rs if lo <= x["carried"] < hi]
                if sel:
                    print(f"   carrying {lo}-{hi - 1}: {ms(sel)}")
        for lo, hi in [(0, 150), (150, 300), (300, 999)]:
            print(f"   rounds {lo}-{hi - 1}: {ms([x['d'] for x in rs if lo <= x['at'] < hi])}")


if __name__ == "__main__":
    main()
