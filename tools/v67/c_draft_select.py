"""Choose a draft lineup per map from forced-lineup runs, against the bot's own draft (baseline run).

Usage: c_draft_select.py --base RUN --option LINEUP=RUN [...] [--min-gain 150] --keys artifacts/tmp/v67/map_keys_full.json
       --out research/v70/draft_table.json
For each map, every option's mean margin over its games (both sides, all seeds) is compared with the baseline's; the
best option replaces the bot's draft only if it gains more than --min-gain gems per game. Selected on these seeds only:
validate the resulting bot on fresh seeds before trusting it.
"""
import argparse
import collections
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def per_map(run):
    out = collections.defaultdict(list)
    seen = set()
    for g in json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']:
        key = (g['map'], g['side'], g['seed'])
        if key not in seen:
            seen.add(key)
            out[g['map']].append(g['margin'])
    return {m: sum(v) / len(v) for m, v in out.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', required=True)
    ap.add_argument('--option', action='append', required=True, metavar='LINEUP=RUN')
    ap.add_argument('--min-gain', type=float, default=150)
    ap.add_argument('--keys', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    base = per_map(a.base)
    options = {int(o.split('=')[0]): per_map(o.split('=')[1]) for o in a.option}
    keys = json.loads((ROOT / a.keys).read_text())
    table, gain = {}, 0.0
    for m in sorted(base):
        best, best_v = -1, base[m]
        for li, res in options.items():
            if m in res and res[m] > best_v:
                best, best_v = li, res[m]
        if best >= 0 and best_v - base[m] > a.min_gain:
            table[m] = dict(lineup=best, key=keys[m], base=round(base[m]), chosen=round(best_v))
            gain += best_v - base[m]
    print(f'{len(table)} of {len(base)} maps switch lineup; in-sample gain {gain / len(base):+.1f} gems per game '
          f'(selected on these games: expect much less on fresh seeds)')
    for m, t in table.items():
        print(f"  {m:24s} lineup {t['lineup']:2d}  {t['base']:+6d} -> {t['chosen']:+6d}")
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(base=a.base, options=a.option, min_gain=a.min_gain, table=table), indent=1) + '\n')


if __name__ == '__main__':
    main()
