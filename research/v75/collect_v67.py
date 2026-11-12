"""Read-only download of v67's ranked games (summaries for all, replays for losses). Never queues or activates bots.

Usage: python research/v75/collect_v67.py   (input research/v75/matches_v67.json from tools/replay/fetch_since.py)
Output: artifacts/local-only/v67-ranked/<matchId>/{summary.json,replay.repl26a}, index research/v75/ranked_v67.json
"""
import concurrent.futures as cf
import json
from pathlib import Path
import subprocess
import threading
import time
import zipfile

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / 'tools/vendor/cambc.exe'
RAW = ROOT / 'artifacts/local-only/v67-ranked'
LOCK = threading.Lock()
LAST = [0.0]


def call(args):
    p = None
    for attempt in range(8):
        with LOCK:
            time.sleep(max(0, 1.25 - (time.monotonic() - LAST[0])))
            LAST[0] = time.monotonic()
        try:
            p = subprocess.run([str(CLI), *args], capture_output=True, encoding='utf8', errors='replace', timeout=600)
        except subprocess.TimeoutExpired:  # a starved or stalled CLI call: try again
            continue
        if p.returncode == 0:
            return
        time.sleep(4 + attempt * 3)
    raise RuntimeError(p.stderr[-400:] if p else 'cambc timed out on every attempt: ' + ' '.join(args))


def fetch(m):
    me = next(t for t in m['teams'] if t['name'] == 'DOOMSDAY')
    dest = RAW / m['matchId']
    dest.mkdir(parents=True, exist_ok=True)
    summary = dest / 'summary.json'
    if not summary.exists():
        call(['matches', 'summary', m['matchId'], '--json', '--output', str(summary)])
    replay = None
    if me['result'] == 'loss':
        replay = dest / 'replay.repl26a'
        if not replay.exists():
            call(['matches', 'download', m['matchId'], '--output', str(replay)])
        with zipfile.ZipFile(replay) as z:
            z.namelist()
    return dict(matchId=m['matchId'], map=m['map'], side=me['side'], result=me['result'],
                opponent=next(t['name'] for t in m['teams'] if t['name'] != 'DOOMSDAY'),
                ours=me['draftPicks'], theirs=next(t['draftPicks'] for t in m['teams'] if t['name'] != 'DOOMSDAY'),
                createdAt=m['createdAt'], summary=summary.relative_to(ROOT).as_posix(),
                replay=replay.relative_to(ROOT).as_posix() if replay else None)


def main():
    ms = [m for m in json.loads((ROOT / 'research/v75/matches_v67.json').read_text(encoding='utf-8')) if m['kind'] == 'ranked']
    rows, errors = [], []
    with cf.ThreadPoolExecutor(3) as ex:
        for f in cf.as_completed([ex.submit(fetch, m) for m in ms]):
            try:
                rows.append(f.result())
            except Exception as e:  # keep going; report at the end
                errors.append(str(e))
            if len(rows) % 25 == 0:
                print('done', len(rows), 'errors', len(errors), flush=True)
    rows.sort(key=lambda r: r['createdAt'])
    (ROOT / 'research/v75/ranked_v67.json').write_text(json.dumps(rows, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print('rows', len(rows), 'errors', len(errors), errors[:3])


if __name__ == '__main__':
    main()
