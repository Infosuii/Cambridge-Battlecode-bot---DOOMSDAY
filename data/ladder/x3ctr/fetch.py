"""Download match summaries (JSON) for every DOOMSDAY game since x3ctr's upload (22:23 UTC 2 Nov), ranked and
unranked. Era: v92 until 03:35 UTC 3 Nov (when v75 went inactive), x3ctr (v77) after.
  python data/ladder/x3ctr/fetch.py"""
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
D = Path(__file__).resolve().parent; ROOT = D.parents[2]
CLI = str(ROOT / 'tools/vendor/cambc.exe')
ms = json.load(open(D / 'matches_all.json'))
todo = [m['matchId'] for k in ms for m in ms[k] if m['status'] == 'finished' and not (D / 'summaries' / f"{m['matchId']}.json").exists()]
def get(mid):
    import time
    for t in range(5):  # the platform refuses bursts: two at a time, back off and retry
        r = subprocess.run([CLI, 'matches', 'summary', '--json', '-o', str(D / 'summaries' / f'{mid}.json'), mid], capture_output=True)
        if r.returncode == 0: return mid, 0
        time.sleep(2 * (t + 1))
    return mid, r.returncode
bad = 0
with ThreadPoolExecutor(2) as ex:
    for i, (mid, rc) in enumerate(ex.map(get, todo)):
        bad += rc != 0
        if i % 100 == 0: print(i, 'of', len(todo), 'failed', bad, flush=True)
print('done', len(todo), 'failed', bad)
