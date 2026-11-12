"""Which diverges first in ladder games: capture gold or dead time? (strategic audit 2026-10-28, offline, no games)

Usage: early_divergence.py [TIMELINE_DATA.json]
Reads the deep-analysis examined-set timelines (never the hands-off set). For losses and wins: mean us-minus-them gaps at
R50/100/250 in capture gold, collected gems, dead champion-rounds and kill gold, and an R100 classification of each game:
behind in capture gold with no extra dead time, behind with extra dead time, gold not behind but extra dead time, neither.
"""
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / 'deep-analysis-wt/research/deep-2026-10-28/TIMELINE_DATA.json'
rows = json.loads(path.read_text())['rows']


def g(r, m, who, k):
    return (r['curve'].get(m, {}).get(who, {}) or {}).get(k, 0) or 0


for res in ('loss', 'win'):
    sub = [r for r in rows if r['result'] == res and 'us' in r['curve'].get('100', {})]
    for m in ('50', '100', '250'):
        gap = {k: st.mean(g(r, m, 'us', k) - g(r, m, 'them', k) for r in sub)
               for k in ('capture_gold', 'collected', 'dead_rounds', 'kill_gold')}
        print(res, f'R{m} n{len(sub)}', ' '.join(f'{k} {v:+.1f}' for k, v in gap.items()))
    cls = [0, 0, 0, 0]
    for r in sub:
        behind = g(r, '100', 'us', 'capture_gold') < g(r, '100', 'them', 'capture_gold')
        dead = g(r, '100', 'us', 'dead_rounds') > g(r, '100', 'them', 'dead_rounds')
        cls[0 if behind and not dead else 1 if behind else 2 if dead else 3] += 1
    print(f'  R100: gold-behind/no-extra-dead {cls[0]}, gold-behind/extra-dead {cls[1]}, gold-ok/extra-dead {cls[2]}, neither {cls[3]}')
