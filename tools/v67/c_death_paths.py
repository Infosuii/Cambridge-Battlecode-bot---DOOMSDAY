"""What led to each death: the bot's own modes over the logged turns before it (APEX_DEATHLOG with a 12-turn ring).

Usage: c_death_paths.py RUN
Per death: the mode on the first logged turn with an enemy in view (what the champion was doing when contact began),
the mode on the turn before that, whether hunt/rescue/approach-type walking modes appear while an enemy is in view,
and the nearest-enemy distance trend. Printed as shares of all deaths with notes.
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
FIGHT = {'enemy', 'flee', 'fight-champ', 'tsearch', 'cmicro', 'kite', 'kite-cast', 'fight-cast', 'gap-dash', 'stand',
         'escape', 'flee-stun', 'bush-recall', 'hold-kite', 'counter', 'ambush'}


def main():
    run = sys.argv[1]
    games = json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']
    seen = set()
    entry, before, walking, lastm, hero = (collections.Counter() for _ in range(5))
    n = 0
    closing = 0
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
            h = HEAD.match(line)
            if not h:
                continue
            notes = [m for m in (NOTE.match(x) for x in lines[i + 1:i + 13]) if m]
            notes = sorted(notes, key=lambda m: int(m[1]))
            if not notes:
                continue
            n += 1
            hero[h[2]] += 1
            lastm[notes[-1][7]] += 1
            first = next((k for k, m in enumerate(notes) if int(m[9]) > 0), None)
            if first is None:
                entry['(no enemy in view)'] += 1
                continue
            entry[notes[first][7]] += 1
            before[notes[first - 1][7] if first > 0 else '(window start)'] += 1
            for m in {m[7] for m in notes[first:] if int(m[9]) > 0 and m[7] not in FIGHT}:
                walking[m] += 1
            ds = [int(m[10]) for m in notes[first:] if 0 <= int(m[10]) < 99]
            if len(ds) >= 2 and ds[-1] < ds[0]:
                closing += 1
    print(f'{n} deaths with notes over {len(seen)} games')
    show = lambda c: ', '.join(f'{k} {v / n:.2f}' for k, v in c.most_common(12))
    print('mode when an enemy first came into view:', show(entry))
    print('mode on the turn before that:', show(before))
    print('non-fight modes used with an enemy in view (share of deaths):', show(walking))
    print('last mode:', show(lastm))
    print(f'distance to nearest enemy shrank over the window: {closing / n:.2f}')
    print('hero:', show(hero))


if __name__ == '__main__':
    main()
