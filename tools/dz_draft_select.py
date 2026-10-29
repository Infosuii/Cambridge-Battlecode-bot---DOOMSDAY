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
    for g in rows:
        out.setdefault(g['map'], 0)
        out[g['map']] += g['banked'] - g['opponent_banked']
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', nargs='+', required=True, help='variant 0 run first, then 1..K-1')
    ap.add_argument('--margin', type=float, default=100)
    a = ap.parse_args()
    scores = [per_map(r) for r in a.runs]
    table, gain = {}, 0
    for m in sorted(scores[0]):
        best = max(range(len(scores)), key=lambda k: scores[k].get(m, -1e9))
        if best and scores[best][m] - scores[0][m] >= a.margin:
            table[m] = best; gain += scores[best][m] - scores[0][m]
    print(json.dumps({'table': table, 'maps_changed': len(table), 'in_sample_gain_per_game': gain / (2 * len(scores[0]))}, indent=1))
    for k, s in enumerate(scores):
        print(k, 'mean margin per game', round(sum(s.values()) / (2 * len(s)), 1))


if __name__ == '__main__':
    main()
