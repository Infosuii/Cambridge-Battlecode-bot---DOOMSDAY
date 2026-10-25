"""Combine bot_match.py shard outputs: overall record, gem margin, and bot-A vs bot-B means of key stats.

    python tools/bench_summary.py <bot_match out dir> [...]
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from match_stats import game  # noqa: E402

STATS = ('collectedGems', 'submittedGems', 'lost', 'deaths', 'kills', 'monsterDamageDone')


def main():
    rows = []
    for root in map(Path, sys.argv[1:]):
        if not (root / 'summary.json').exists():
            continue  # an empty shard (fewer maps than shards)
        for g in json.loads((root / 'summary.json').read_text(encoding='utf-8'))['per_game']:
            _, _, out = game(Path(g['folder']) / 'summary.json')
            me, them = (out['teamA'], out['teamB']) if g['side'] == 'A' else (out['teamB'], out['teamA'])
            rows.append((g, me, them))
    n = len(rows)
    wins = sum(g['win'] for g, _, _ in rows)
    print(f"games {n}  record {wins:.0f}-{n - wins:.0f}  win rate {wins / n:.3f}  mean gem margin "
          f"{sum(g['gems'] - g['opponent_gems'] for g, _, _ in rows) / n:+.1f}  faults {sum(g['faults'] for g, _, _ in rows)}  "
          f"fuel exhausted {sum(g['fuel_exhausted'] for g, _, _ in rows)} vs {sum(g['opponent_fuel_exhausted'] for g, _, _ in rows)}")
    print('mean per game (A vs B): ' + '  '.join(
        f"{s} {sum(m[s] for _, m, _ in rows) / n:.0f}/{sum(t[s] for _, _, t in rows) / n:.0f}" for s in STATS))
    by_map = {}
    for g, _, _ in rows:
        by_map.setdefault(g['map'], []).append(g)
    print('per map (A side, B side wins; margins): ' + '  '.join(
        f"{m}:{''.join('W' if x['win'] else 'L' for x in sorted(v, key=lambda x: x['side']))}"
        f"({'/'.join(str(x['gems'] - x['opponent_gems']) for x in sorted(v, key=lambda x: x['side']))})" for m, v in sorted(by_map.items())))


if __name__ == '__main__':
    main()
