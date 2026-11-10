"""Pick a per-map winner from a rescue screen (rescue_build.py knob profiles or rescue_lineup_build.py lineups) and
write the table rows. For each map: every candidate's paired gain over the base on identical cells (opponent x side);
a map switches only if the best gain >= --min-gain games and that candidate loses at most --max-loss cells.
usage: rescue_select.py RUN_DIR BASE PREFIX knob|lineup OUT_JSON [--min-gain 3] [--max-loss 1]"""
import argparse, collections, json, os, sys

ap = argparse.ArgumentParser()
ap.add_argument("run")
ap.add_argument("base")
ap.add_argument("prefix")
ap.add_argument("kind", choices=["knob", "lineup"])
ap.add_argument("out")
ap.add_argument("--min-gain", type=float, default=3.0)
ap.add_argument("--max-loss", type=int, default=1)
a = ap.parse_args()
sys.stdout.reconfigure(encoding="utf-8")
rep = json.load(open(os.path.join(a.run, "report.json"), encoding="utf-8"))
score = {}
for g in rep["games"]:
    if g.get("status") == "ok":
        score[(g["candidate"], g["map"].replace(".map26a", ""), g["opponent"], g["side"])] = g["score"]
cands = sorted({k[0] for k in score if k[0].startswith(a.prefix)})
maps = sorted({k[1] for k in score})
choice, evidence = {}, {}
for m in maps:
    cells = [(o, s) for (c, mm, o, s) in score if c == a.base and mm == m]
    base_score = sum(score[(a.base, m, o, s)] for o, s in cells)
    best, best_gain, ev = None, 0.0, {}
    for c in cands:
        if not all((c, m, o, s) in score for o, s in cells):
            continue
        d = [score[(c, m, o, s)] - score[(a.base, m, o, s)] for o, s in cells]
        gain, losses = sum(d), sum(1 for x in d if x < 0)
        ev[c] = dict(gain=gain, losses=losses)
        if gain >= a.min_gain and losses <= a.max_loss and gain > best_gain:
            best, best_gain = c, gain
    evidence[m] = dict(cells=len(cells), base=base_score, best=best, best_gain=best_gain,
                       top=sorted(ev.items(), key=lambda kv: -kv[1]["gain"])[:3])
    if best:
        choice[m] = best[len(a.prefix):]
json.dump(dict(kind=a.kind, base=a.base, min_gain=a.min_gain, max_loss=a.max_loss, choice=choice, evidence=evidence),
          open(a.out, "w", encoding="utf-8"), indent=1)
for m in maps:
    e = evidence[m]
    print(f"{m:20s} base {e['base']:4.1f}/{e['cells']} -> {('switch to ' + choice[m]) if m in choice else 'keep'}"
          f"{(' (+%.1f)' % e['best_gain']) if m in choice else ''} | top: "
          + ", ".join(f"{c[len(a.prefix):]} {v['gain']:+.1f}/{v['losses']}L" for c, v in e["top"]))
print(f"{len(choice)} of {len(maps)} maps switched; in-sample gain {sum(evidence[m]['best_gain'] for m in choice):+.1f} games")
