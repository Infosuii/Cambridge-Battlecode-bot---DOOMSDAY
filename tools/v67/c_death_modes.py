"""Aggregate APEX_DEATHLOG output (our team's stdout in each replay bundle) for a benchmark run.

Usage: c_death_modes.py RUN
For each of our deaths, the last four logged turns: what we were doing (mode), what we saw, and the trend.
"""
import collections
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HEAD = re.compile(r'^DEATH R(\d+) (\S+(?: \S+)*?) gems(\d+)$')
NOTE = re.compile(r'^  R(\d+) .*? p\((\d+),(\d+)\) hp(\d+)/(\d+) g(\d+) mode=(\S*) G(-?\d+) enemies=(\d+) near=(-?\d+) '
                  r'ehp=(\d+) allies4=(\d+) spawn=(-?\d+)')


def main():
    run = sys.argv[1]
    games = json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']
    seen = set()
    last_mode, any_mode, buckets = collections.Counter(), collections.Counter(), collections.Counter()
    n = 0
    hp_at = []
    for g in games:
        key = (g['map'], g['side'], g['seed'])
        if key in seen:
            continue
        seen.add(key)
        bundle = next((ROOT / g['folder']).glob('*.repl26a'))
        with zipfile.ZipFile(bundle) as z:
            text = z.read(f"team-{g['side']}.stdout").replace(b'\0', b'').decode('utf8', 'replace')
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if not HEAD.match(line):
                continue
            notes = []
            for nl in lines[i + 1:i + 5]:
                m = NOTE.match(nl)
                if m:
                    notes.append(m)
            if not notes:
                continue
            n += 1
            last = notes[-1]
            last_mode[last[7]] += 1
            for m in {x[7] for x in notes}:
                any_mode[m] += 1
            hp, mx, enemies, near, ehp, allies, spawn = (int(last[k]) for k in (4, 5, 9, 10, 11, 12, 13))
            first_hp = int(notes[0][4])
            hp_at.append(hp / max(1, mx))
            buckets['saw no enemy'] += enemies == 0
            buckets['enemy within 2'] += 0 <= near <= 2
            buckets['no ally within 4'] += allies == 0
            buckets['enemy hp > ours x1.5'] += ehp > 1.5 * hp
            buckets['hp<30% at last turn'] += hp < 0.3 * mx
            buckets['hp>60% 4 turns before'] += first_hp > 0.6 * mx
            buckets['spawn dist<=10'] += 0 <= spawn <= 10
    print(f'{n} deaths with notes over {len(seen)} games')
    print('last mode:', ', '.join(f'{k} {v / n:.2f}' for k, v in last_mode.most_common(14)))
    print('mode in last 4 turns:', ', '.join(f'{k} {v / n:.2f}' for k, v in any_mode.most_common(14)))
    for k, v in buckets.items():
        print(f'  {k:24s} {v / n:.2f}')


if __name__ == '__main__':
    main()
