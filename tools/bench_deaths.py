"""Deaths, kills and results per map for bench2 runs (any seed sets), candidate vs opponent.

Usage: python tools/bench_deaths.py <maps comma list|all> <bench2 out prefix>...
"""
from collections import defaultdict
import glob
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from match_stats import game  # noqa: E402

maps = None if sys.argv[1] == 'all' else set(sys.argv[1].split(','))
for prefix in sys.argv[2:]:
    rows = defaultdict(list)
    for f in glob.glob(prefix + '-seed*-s*/summary.json'):
        for g in json.loads(Path(f).read_text(encoding='utf-8'))['per_game']:
            if maps and g['map'] not in maps:
                continue
            _, _, out = game(Path(g['folder']) / 'summary.json')
            me, them = (out['teamA'], out['teamB']) if g['side'] == 'A' else (out['teamB'], out['teamA'])
            rows[g['map']].append((g['win'], g['gems'] - g['opponent_gems'], me['deaths'], them['deaths'], me['lost'], them['lost']))
    print(Path(prefix).name)
    tot = []
    for m in sorted(rows):
        r = rows[m]; tot += r; n = len(r)
        print(f"  {m:22s} n{n:3d} wins {sum(x[0] for x in r) / n:.2f} margin {sum(x[1] for x in r) / n:+7.1f} "
              f"deaths {sum(x[2] for x in r) / n:5.1f}/{sum(x[3] for x in r) / n:5.1f} bag lost {sum(x[4] for x in r) / n:5.0f}/{sum(x[5] for x in r) / n:5.0f}")
    n = len(tot)
    if n:
        print(f"  {'ALL':22s} n{n:3d} wins {sum(x[0] for x in tot) / n:.2f} margin {sum(x[1] for x in tot) / n:+7.1f} "
              f"deaths {sum(x[2] for x in tot) / n:5.1f}/{sum(x[3] for x in tot) / n:5.1f}")
