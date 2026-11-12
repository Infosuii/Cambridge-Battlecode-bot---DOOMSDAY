"""Fetch matches played by DOOMSDAY after the 2026-11-09 11:38 inventory (v117 active). Summaries for all, replays for losses."""
from pathlib import Path
import sys, json, gzip, collections
from concurrent.futures import ThreadPoolExecutor
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import ladder_loss_analysis as L
from project import save
L.D = HERE
L.CALL_SPACING = 1.6
START = '2026-11-09T11:38:08+00:00'
seen = {}
for kind in ('ranked', 'unranked'):
    cursor = None
    while True:
        args = ['matches', 'list', '--team', 'me', '--kind', kind, '--limit', '100', '--json'] + (['--cursor', cursor] if cursor else [])
        page = L.get(*args)
        ms = page['matches']
        for m in ms:
            if L.stamp(m['createdAt']) >= L.stamp(START) and m['status'] == 'finished': seen[m['matchId']] = {**m, 'kind': kind}
        cursor = page.get('nextCursor')
        if not ms or not cursor or min(L.stamp(m['createdAt']) for m in ms) < L.stamp(START): break
ms = list(seen.values())
save(HERE / 'matches.json', ms)
with ThreadPoolExecutor(2) as pool:
    list(pool.map(lambda m: L.fetch(m, 'summary'), ms))
    list(pool.map(lambda m: L.fetch(m, 'replay'), [m for m in ms if L.own(m)['result'] == 'loss']))
c = collections.Counter((m['kind'], L.own(m)['result']) for m in ms)
print(json.dumps({str(k): v for k, v in c.items()}))
