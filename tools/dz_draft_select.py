"""Choose a draft variant per map from completed pool runs (one run per variant).

Score per map = sum over both sides of (our banked - opponent banked). A
variant replaces the default (variant 0) only when it beats it by --margin.
Best-of-K on deterministic games is optimistic: confirm the resulting table
against a different opponent before trusting it.
"""
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def per_map(run):
    rows = json.loads((ROOT / 'research/dz/runs' / run / 'results.json').read_text())['per_game']
    out = {}
    cells = set()
    for g in rows:
        cell = g['map'], g['side']
        if cell in cells or g['side'] not in ('A', 'B'):
            raise ValueError('duplicate or invalid map-side cell')
        if any(g[k] for k in ('faults', 'fuel_outs', 'opponent_faults')):
            raise ValueError('runtime failure is not a selectable draft')
        cells.add(cell)
        out.setdefault(g['map'], 0)
        out[g['map']] += g['banked'] - g['opponent_banked']
    if not out or any((m, s) not in cells for m in out for s in ('A', 'B')):
        raise ValueError('each scored map needs both sides')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', nargs='+', required=True, help='variant 0 run first, then 1..K-1')
    ap.add_argument('--margin', type=float, default=100)
    ap.add_argument('--variants', nargs='+', type=int,
                    help='actual variant IDs matching --runs, e.g. 0 4 5 6 7')
    a = ap.parse_args()
    variants = a.variants if a.variants is not None else list(range(len(a.runs)))
    if (len(variants) != len(a.runs) or len(set(variants)) != len(variants) or
            not variants or variants[0] != 0 or any(v < 0 or v > 7 for v in variants) or a.margin < 0):
        ap.error('provide distinct variants 0..7, starting with 0, one per run; margin must be nonnegative')
    scores = [per_map(r) for r in a.runs]
    if any(set(s) - set(scores[0]) for s in scores[1:]):
        raise ValueError('candidate has maps without a baseline')
    # HOLDOUT.md registers every fifth map of the complete lexical pool.
    pool = sorted(p.stem for p in (ROOT/'maps/local-benchmarks').glob('*.map26a'))
    if len(pool) != 70:
        raise ValueError('expected the registered 70-map pool')
    held_out = set(pool[4::5])
    table, gain = {}, 0
    for m in sorted(scores[0]):
        if m in held_out:
            continue
        best = max(range(len(scores)), key=lambda k: scores[k].get(m, -1e9))
        if best and scores[best][m] - scores[0][m] >= a.margin:
            table[m] = variants[best]; gain += scores[best][m] - scores[0][m]
    print(json.dumps({'table': table, 'maps_changed': len(table), 'in_sample_gain_per_game': gain / (2 * len(scores[0]))}, indent=1))
    for k, s in enumerate(scores):
        maps = set(s) - held_out
        if not maps:
            raise ValueError('no development maps in run')
        print(variants[k], 'development margin per game', round(sum(s[m] for m in maps) / (2 * len(maps)), 1),
              'baseline on same maps', round(sum(scores[0][m] for m in maps) / (2 * len(maps)), 1))


if __name__ == '__main__':
    main()
