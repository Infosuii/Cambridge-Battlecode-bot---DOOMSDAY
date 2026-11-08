"""Per-bot fuel use in a local run_eval run, from the engine's own trace (team-a/b.fuel inside each .repl26a bundle).

Bot names come from the bundle file name (<a>-rel-vs-<b>-rel-<seed>.repl26a). Reports per bot: games, play turns,
mean / p99 fuel per turn, fuel-outs per game (a turn word equal to the 100,000 budget) and the share of games with any.
Format notes: tools/rl_env_1104/ladder_fuel.py.

usage: python -I tools/rl_env_1104/eval_fuel.py runs/rl_env_1104/eval/<run> [more runs]
"""
import glob
import os
import re
import struct
import sys
import zipfile

BUDGET = 100000


def turns(z, side):
    b = z.read(f"team-{side}.fuel")
    n = (len(b) - 13) // 8
    return list(struct.unpack("<%dQ" % n, b[13:13 + 8 * n])[8 + 12:])


def main() -> None:
    for run in sys.argv[1:]:
        agg = {}
        for f in glob.glob(os.path.join(run, "work", "g*", "*.repl26a")):
            m = re.match(r"(.+?)(?:-rel)?-vs-(.+?)(?:-rel)?-\d+\.repl26a$", os.path.basename(f))
            if not m:
                continue
            try:
                z = zipfile.ZipFile(f)
                for side, name in (("a", m.group(1)), ("b", m.group(2))):
                    t = turns(z, side)
                    s = agg.setdefault(name, dict(games=0, turns=0, total=0, outs=[], hi=[]))
                    s["games"] += 1
                    s["turns"] += len(t)
                    s["total"] += sum(t)
                    s["outs"].append(sum(x >= BUDGET for x in t))
                    s["hi"].append(sum(x >= 90000 for x in t))
            except (KeyError, zipfile.BadZipFile, struct.error):
                continue
        print(run)
        for name, s in sorted(agg.items()):
            g = max(1, s["games"])
            print(f"  {name:12s} {s['games']:5d} games  mean {s['total'] / max(1, s['turns']):7,.0f}/turn  fuel-outs {sum(s['outs']) / g:6.2f}/game"
                  f" (games with any {sum(o > 0 for o in s['outs']) / g:4.0%})  >=90k turns {sum(s['hi']) / max(1, s['turns']):.2%}")


if __name__ == "__main__":
    main()
