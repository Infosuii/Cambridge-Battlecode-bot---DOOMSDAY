"""Per-map draft selection against several opponents at once (a league), so the table does not just counter one bot.

Usage: c_draft_league.py --base OPP=RUN [...] --option LINEUP:OPP=RUN [...] --keys KEYS.json --out TABLE.json
       [--min-gain 100] [--max-loss 250] [--confirm-base OPP=RUN ... --confirm-option LINEUP:OPP=RUN ... --confirm-min 0]
For each map and lineup: the gain over the bot's own draft (same opponent, same games) per opponent, then the mean over
the opponents. A lineup is chosen when its mean gain exceeds --min-gain and it loses no more than --max-loss gems per
game against any single opponent. With --confirm-* runs (other seeds), a map keeps its choice only if that choice also
gains more than --confirm-min on them, losing no more than --max-loss to any opponent: picking the best of many noisy
options otherwise mostly picks luck. Validate the result on fresh seeds against every opponent.
"""
import argparse
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def per_map(runs):
    """Mean margin per map over one run or several comma-separated runs (e.g. two seed pairs of the same bot)."""
    out, seen = collections.defaultdict(list), set()
    for run in runs.split(','):
        for g in json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']:
            key = (g['map'], g['side'], g['seed'])
            if key not in seen:
                seen.add(key)
                out[g['map']].append(g['margin'])
    return {m: sum(v) / len(v) for m, v in out.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', action='append', required=True, metavar='OPP=RUN')
    ap.add_argument('--option', action='append', required=True, metavar='LINEUP:OPP=RUN')
    ap.add_argument('--keys', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--min-gain', type=float, default=100)
    ap.add_argument('--max-loss', type=float, default=250)
    ap.add_argument('--confirm-base', action='append', default=[], metavar='OPP=RUN')
    ap.add_argument('--confirm-option', action='append', default=[], metavar='LINEUP:OPP=RUN')
    ap.add_argument('--confirm-min', type=float, default=0.0)
    a = ap.parse_args()
    cbase = {b.split('=')[0]: per_map(b.split('=')[1]) for b in a.confirm_base}
    copts = collections.defaultdict(dict)
    for o in a.confirm_option:
        spec, run = o.split('=')
        li, opp = spec.split(':')
        copts[int(li) if li.lstrip('-').isdigit() else li][opp] = per_map(run)
    rejected = []
    base = {b.split('=')[0]: per_map(b.split('=')[1]) for b in a.base}
    opts = collections.defaultdict(dict)
    for o in a.option:
        spec, run = o.split('=')
        li, opp = spec.split(':')
        opts[int(li) if li.lstrip('-').isdigit() else li][opp] = per_map(run)
    keys = json.loads((ROOT / a.keys).read_text())
    maps = sorted(set.intersection(*(set(v) for v in base.values())))
    table, total = {}, 0.0
    for m in maps:
        best, best_gain, best_detail = None, a.min_gain, None
        for li, by_opp in opts.items():
            if set(by_opp) != set(base):
                continue
            gains = {opp: by_opp[opp][m] - base[opp][m] for opp in base if m in by_opp[opp]}
            if len(gains) != len(base):
                continue
            mean = sum(gains.values()) / len(gains)
            if mean > best_gain and min(gains.values()) >= -a.max_loss:
                best, best_gain, best_detail = li, mean, gains
        if best is not None and cbase:
            cg = {opp: copts[best][opp][m] - cbase[opp][m] for opp in cbase if m in copts.get(best, {}).get(opp, {})}
            cmean = sum(cg.values()) / len(cg) if len(cg) == len(cbase) else None
            if cmean is None or cmean <= a.confirm_min or min(cg.values()) < -a.max_loss:
                rejected.append((m, best, round(best_gain), None if cmean is None else round(cmean)))
                best = None
            else:
                best_detail = dict(best_detail, confirm=round(cmean))
        if best is not None:
            choice = dict(lineup=best) if isinstance(best, int) else dict(profile=best)
            table[m] = dict(choice, key=keys[m], gain=round(best_gain), per_opponent={k: round(v) for k, v in best_detail.items()})
            total += best_gain
    print(f'{len(table)} of {len(maps)} maps switch; in-sample mean gain {total / len(maps):+.1f} gems per game across '
          f'{len(base)} opponents (selection bias: validate on fresh seeds)')
    if cbase:
        print(f'{len(rejected)} selections failed confirmation: ' + ', '.join(f'{m} {li} ({g:+d} -> {c})' for m, li, g, c in rejected))
    for m, t in table.items():
        print(f"  {m:24s} {str(t.get('lineup', t.get('profile'))):>6s}  mean {t['gain']:+5d}  {t['per_opponent']}")
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(base=a.base, options=a.option, min_gain=a.min_gain, max_loss=a.max_loss, table=table),
                              indent=1) + '\n')


if __name__ == '__main__':
    main()
