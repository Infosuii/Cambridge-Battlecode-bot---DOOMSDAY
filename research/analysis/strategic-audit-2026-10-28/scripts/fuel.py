"""Per-turn fuel use of our team from the engine's own trace (team-<side>.fuel inside each replay bundle).

Usage: fuel.py RUN [RUN...]
Format (reverse-engineered 2026-10-28, cambc 4.0.0): 13-byte header ('a62leuf' magic + version), then u64 words:
8 budget words (draft 10M, turn 100k, first play turn 200k, 100k; twice), then one word per body-turn in execution
order: draft turns first, then play turns. The first 20 words (draft turns and doubled first play turns) are skipped:
a negligible bias over ~3,000-9,000 turns per game. A word equal to the 100,000 budget is a turn that ran out of fuel.
"""
import glob
import json
import struct
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def turns(bundle, side):
    b = zipfile.ZipFile(bundle).read(f'team-{side}.fuel')
    n = (len(b) - 13) // 8
    v = struct.unpack('<%dQ' % n, b[13:13 + 8 * n])[8:]
    # Draft and doubled first play turns: skip the first 20 words (at most 6 bodies x 2 + draft picks).
    return v[:1], v[20:]


def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))]


for run in sys.argv[1:]:
    games = json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']
    allt, draft, full = [], [], 0
    for g in games:
        bundle = glob.glob(str(ROOT / g['folder'] / '*.repl26a'))[0]
        d, t = turns(bundle, g['side'])
        draft += d
        allt += t
        full += sum(1 for x in t if x >= 100000)
    mean = sum(allt) / len(allt)
    print(f"{run}: {len(games)} games, {len(allt)} play turns, mean {mean:,.0f}, p50 {pct(allt, .5):,}, p90 {pct(allt, .9):,},"
          f" p99 {pct(allt, .99):,}; >=90k {sum(x >= 90000 for x in allt) / len(allt):.2%}; full-budget turns {full}"
          f" ({full / len(games):.2f}/game); draft max {max(draft):,}")
