"""Infer the Prospector emblem effect from saved games (offline, no new matches).

Usage: prospector_check.py [RUN ...]   (default SA-IDLE-v76)
For each champion, split camp-group gem receipts (summary.json gemCollection events, context campGroup) into before and
after that champion completed a Prospector emblem (itemCombination event). Gem clusters pay 7 per cluster, so a +25%
floored bonus shows up as 7/14/21 -> 8/17/26 while wolf (4) and elk (15) receipts stay unchanged.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
runs = sys.argv[1:] or ['SA-IDLE-v76']
before, after = Counter(), Counter()
for run in runs:
    for g in json.loads((ROOT / 'artifacts/evaluations/v67' / run / 'games.json').read_text())['games']:
        events = json.loads((ROOT / g['folder'] / 'summary.json').read_text())['events']
        done = {}
        for e in events:
            if e['kind'] == 'itemCombination':
                key = (e['owner']['team'], e['owner']['id'])
                for en in e['entries']:
                    if 'Prospector Emblem' in en['target'].get('name', ''):
                        done.setdefault(key, en['timestamp']['round'])
        for e in events:
            if e['kind'] != 'gemCollection':
                continue
            key = (e['owner']['team'], e['owner']['id'])
            for en in e['entries']:
                if en.get('context') == 'campGroup':
                    (after if key in done and en['timestamp']['round'] > done[key] else before)[en['value']] += 1
print('receipt value counts before Prospector:', before.most_common(20))
print('receipt value counts after Prospector: ', after.most_common(20))
