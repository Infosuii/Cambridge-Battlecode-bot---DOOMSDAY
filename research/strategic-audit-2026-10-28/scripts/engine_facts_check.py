"""Offline engine-fact checks from saved summaries (no games): Capture-emblem capture delay and gold-step multipliers.

Usage: engine_facts_check.py [IDLE_RUN] [CONTESTED_RUN]   (defaults SA-IDLE-v76, SA-P-base)
1. Capture delay: per champion, rounds from its campClear to its own gemCollection of the same group, split by whether
   it owned a Capture emblem (itemCombination event). Result 2026-10-28: mode 6-7 without, 4-5 with (capture time 5 -> 3).
2. Gold steps: earnedGold timeline increments split by (Vesper, owns Treasure emblem). Result: 40->44 and 100->110 with
   Treasure (+10%, kills included); Vesper 40->53, 100->133 (+33%); Vesper+Treasure 40->57, 100->143 (+43%).
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
idle, contested = (sys.argv[1:] + ['SA-IDLE-v76', 'SA-P-base'])[:2] if len(sys.argv) > 2 else ('SA-IDLE-v76', 'SA-P-base')


def summaries(run):
    for g in json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']:
        yield json.loads((ROOT / g['folder'] / 'summary.json').read_text())


def emblem_round(events, name):
    out = {}
    for e in events:
        if e['kind'] == 'itemCombination':
            for en in e['entries']:
                if name in en['target'].get('name', ''):
                    out.setdefault((e['owner']['team'], e['owner']['id']), en['timestamp']['round'])
    return out


with_c, without = Counter(), Counter()
for s in summaries(idle):
    cap = emblem_round(s['events'], 'Capture Emblem')
    clears, colls = {}, {}
    for e in s['events']:
        k = (e['owner']['team'], e['owner']['id'])
        for en in e['entries']:
            if e['kind'] == 'campClear':
                clears.setdefault(k, []).append((en['timestamp']['round'], en['target']['id']))
            if e['kind'] == 'gemCollection' and en.get('context') == 'campGroup':
                colls.setdefault(k, []).append((en['timestamp']['round'], en['target']['id']))
    for k, cl in clears.items():
        for r, gid in cl:
            later = [rc for rc, gc in colls.get(k, []) if gc == gid and r <= rc <= r + 40]
            if later:
                (with_c if k in cap and r > cap[k] else without)[min(later) - r] += 1
print('capture delay without Capture emblem:', sorted(without.items())[:10])
print('capture delay with Capture emblem   :', sorted(with_c.items())[:10])

steps = {}
for s in summaries(contested):
    names = {(c['team'], c['id']): c['name'] for c in s['roster']['champions']}
    tre = emblem_round(s['events'], 'Treasure Emblem')
    for tl in s['championTimelines']:
        if tl['metric'] != 'earnedGold':
            continue
        k = (tl['owner']['team'], tl['owner']['id'])
        t, prev = 0, 0.0
        for r in tl['runs']:
            v = float(r['value'])
            if v > prev:
                steps.setdefault((names.get(k) == 'Vesper Vale', k in tre and t > tre[k]), Counter())[round(v - prev)] += 1
            prev, t = v, t + r['duration']
for key, c in sorted(steps.items()):
    print('vesper=%s treasure=%s' % key, c.most_common(8))
