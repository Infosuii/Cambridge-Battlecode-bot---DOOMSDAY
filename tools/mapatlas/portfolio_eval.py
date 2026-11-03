"""Does a per-category strategy choice carry over to maps and opponents it was not chosen on?

Data: the counter search (30 variants x 4 opponents, every pool map and side; runs ctr3-OPP-kK, tools/x3_counter_run.sh).
A category assignment maps each map to a category. For each category the best variant is the one with the most wins
summed over that category's maps, both sides and the chosen opponents; ties keep variant 0 (the base). Estimates:
  in-sample    the choice scored on the games it was chosen on
  leave-map    each map scored with the choice made on the other maps of its category (unseen maps)
  leave-opp    each opponent scored with the choice made on the other opponents (unseen opponents)
  leave-both   each (map, opponent) scored with the choice made without that map and without that opponent
  python tools/mapatlas/portfolio_eval.py --cats research/x3/atlas/categories.json [--margin 0] [--vars 0-29]
"""
import argparse, json, sys
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OPPS = ['x3mf', 'x3inv', 'v86h', 'x1bru']
DIRS = ['research/dz/runs', 'artifacts/tmp/dz', '../x1-comms/g3/results/L007']


def load(name):
    for d in DIRS:
        for p in (ROOT / d / name / 'results.json', ROOT / d / f'{name}.json'):
            if p.exists():
                return {(g['map'], g['side']): g['outcome'] == ('team' + g['side']) for g in json.loads(p.read_text())['per_game']}
    return None


def rng(s):
    out = []
    for part in s.split(','):
        a, _, b = part.partition('-'); out += range(int(a), int(b or a) + 1)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--cats', required=True); ap.add_argument('--vars', default='0-29')
    ap.add_argument('--margin', type=int, default=0, help='extra wins over variant 0 needed to switch a category')
    ap.add_argument('--opps', default=','.join(OPPS)); ap.add_argument('--show', type=int, default=1)
    a = ap.parse_args()
    cats = json.loads(Path(a.cats).read_text(encoding='utf-8'))  # {map: category}
    ks, opps = rng(a.vars), a.opps.split(',')
    R = {(o, k): load(f'ctr3-{o}-k{k}') for o in opps for k in ks}
    miss = [f'{o}-k{k}' for (o, k), v in R.items() if v is None]
    if miss: sys.exit('missing runs: ' + ' '.join(miss))
    maps = sorted({m for m, _ in R[opps[0], 0]} & set(cats))
    bycat = defaultdict(list)
    for m in maps: bycat[cats[m]].append(m)

    def wins(k, ms, os):
        return sum(R[o, k].get((m, s), False) for o in os for m in ms for s in 'AB')

    def choose(ms, os):
        if not ms or not os: return 0
        base = wins(0, ms, os)
        best = max(ks, key=lambda k: (wins(k, ms, os), -k))
        return best if wins(best, ms, os) - base > a.margin else 0
    per = {}
    tot = defaultdict(int)
    for c, ms in sorted(bycat.items()):
        k_in = choose(ms, opps)
        s_base = wins(0, ms, opps); s_in = wins(k_in, ms, opps)
        s_lm = sum(wins(choose([x for x in ms if x != m], opps), [m], opps) for m in ms)
        s_lo = sum(wins(choose(ms, [x for x in opps if x != o]), ms, [o]) for o in opps)
        s_lb = sum(wins(choose([x for x in ms if x != m], [x for x in opps if x != o]), [m], [o]) for m in ms for o in opps)
        n = len(ms) * 2 * len(opps)
        per[c] = dict(maps=len(ms), games=n, variant=k_in, base=s_base, in_sample=s_in, leave_map=s_lm, leave_opp=s_lo, leave_both=s_lb)
        for key in ('base', 'in_sample', 'leave_map', 'leave_opp', 'leave_both'): tot[key] += per[c][key]
        tot['games'] += n
        if a.show:
            print(f"{c:22s} maps {len(ms):2d} games {n:4d} | variant {k_in:2d} | base {s_base:4d} in-sample {s_in - s_base:+4d} "
                  f"unseen maps {s_lm - s_base:+4d} unseen opps {s_lo - s_base:+4d} both {s_lb - s_base:+4d}")
    print(f"{'TOTAL':22s} games {tot['games']} | base {tot['base']} | in-sample {tot['in_sample'] - tot['base']:+d} | "
          f"unseen maps {tot['leave_map'] - tot['base']:+d} | unseen opps {tot['leave_opp'] - tot['base']:+d} | both {tot['leave_both'] - tot['base']:+d}")
    return per


if __name__ == '__main__':
    main()
