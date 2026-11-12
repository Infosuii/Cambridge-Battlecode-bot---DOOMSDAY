"""Read-only collection of a fixed 24-hour window; never queues or activates bots."""
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import time
import zipfile
import threading

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
RAW = ROOT / 'artifacts/local-only/top-losses-20261026'
CLI = ROOT / 'tools/vendor/cambc.exe'
SINCE = '2026-10-25T20:24:26Z'
UNTIL = '2026-10-26T20:24:26Z'
ME = 'fcf5f666-ea55-4da0-b8d4-97c64bb37236'
REQUEST_LOCK=threading.Lock()
LAST_REQUEST=0.0

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def save(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    # The complete machine-readable ledgers have human-readable Markdown/CSV companions.
    compact=p.name in {'metrics.json','all-loss-fights.json','failure-ledger.json'}
    p.write_text(json.dumps(d, indent=None if compact else 1, ensure_ascii=False,
                            separators=(',',':') if compact else None)+'\n', encoding='utf-8')

def call(args):
    global LAST_REQUEST
    for attempt in range(10):
        with REQUEST_LOCK:
            time.sleep(max(0,1.25-(time.monotonic()-LAST_REQUEST)))
            LAST_REQUEST=time.monotonic()
        p = subprocess.run([str(CLI), *args], capture_output=True, encoding='utf8', errors='replace', timeout=120)
        if p.returncode == 0:
            return p.stdout
        if attempt == 9:
            raise RuntimeError(p.stderr[-500:])
        time.sleep(4 + attempt * 3)

def listings(kind):
    cursor, found = None, {}
    for page in range(100):
        args = ['matches','list','--team','me','--kind',kind,'--limit','100','--json']
        if cursor:
            args += ['--cursor',cursor]
        data = json.loads(call(args))
        save(OUT/'pages'/f'{kind}-{page:03}.json',data)
        for m in data['matches']:
            if SINCE <= m['createdAt'] <= UNTIL:
                found[m['matchId']] = m
        print(kind, 'page',page+1,'in-window',len(found),flush=True)
        cursor = data.get('nextCursor')
        if not cursor or (data['matches'] and min(m['createdAt'] for m in data['matches']) < SINCE):
            return list(found.values())
    raise RuntimeError('pagination incomplete: '+kind)

def collect():
    ladder = read(OUT/'ladder.json')['teams']
    tops = {t['teamId']:t for t in ladder if t['rank'] <= 25}
    rows = []
    with cf.ThreadPoolExecutor(max_workers=2) as ex:
        for result in ex.map(listings,['ranked','unranked','tournament']):
            rows.extend(result)
    rows.sort(key=lambda m:(m['createdAt'],m['matchId']))
    save(OUT/'all-matches.json',rows)
    top = [m for m in rows if any(t['teamId'] in tops for t in m['teams'])]
    save(OUT/'top25-matches.json',top)
    finished = [m for m in top if m['status']=='finished']
    save(OUT/'finished-top25.json',finished)
    losses = [m for m in finished if next(t for t in m['teams'] if t['teamId']==ME)['result']=='loss']
    save(OUT/'losses.json',losses)
    save(OUT/'collection.json',dict(since=SINCE,until=UNTIL,allMatches=len(rows),top25=len(top),finished=len(finished),losses=len(losses),rankBasis='current snapshot; not historical rank'))
    print('COLLECTION',read(OUT/'collection.json'),flush=True)

def downloads(include_replays=True):
    rows = read(OUT/'finished-top25.json')
    cached = {}
    flat={p.stem:p for p in (ROOT/'artifacts/local-only/duels').glob('*.json')}
    for base in (ROOT/'artifacts/local-only').iterdir():
        if base.is_dir() and base != RAW and not base.name.startswith(('replays-','bc-','cancelled','repo-cleanup')):
            for p in base.glob('*/summary.json'):
                cached.setdefault(p.parent.name,p.parent)
    def fetch(m):
        key=m['matchId']; dest=RAW/key; dest.mkdir(parents=True,exist_ok=True)
        old=cached.get(key)
        summary=flat.get(key,(old/'summary.json') if old else dest/'summary.json')
        if not summary.exists():
            call(['matches','summary',key,'--json','--output',str(summary)])
        data=read(summary)
        replay=None
        if include_replays and next(t for t in m['teams'] if t['teamId']==ME)['result']=='loss':
            options = [old/'replay.repl26a'] if old else []
            replay=next((p for p in options if p.exists()),dest/'replay.repl26a')
            if not replay.exists():
                call(['matches','download',key,'--output',str(replay)])
            with zipfile.ZipFile(replay) as z:
                if z.testzip() is not None:
                    raise RuntimeError('invalid replay ZIP')
        return dict(matchId=key,summary=summary.relative_to(ROOT).as_posix(),replay=replay.relative_to(ROOT).as_posix() if replay else None,
                    engine=data['match']['engineVersion'],sha256=hashlib.sha256(summary.read_bytes()).hexdigest())
    got,errors=[],[]
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        pending={ex.submit(fetch,m):m['matchId'] for m in rows}
        for f in cf.as_completed(pending):
            try: got.append(f.result())
            except Exception as e: errors.append(dict(matchId=pending[f],error=str(e)))
            if (len(got)+len(errors))%20==0:
                save(OUT/'manifest.json',dict(matches=got,errors=errors,total=len(rows)))
                print('downloads',len(got),'/',len(rows),'errors',len(errors),flush=True)
    save(OUT/'manifest.json',dict(matches=got,errors=errors,total=len(rows)))
    print('DOWNLOAD DONE',len(got),'errors',len(errors),flush=True)

if __name__=='__main__':
    import sys
    if len(sys.argv)>1 and sys.argv[1] in ['downloads','summaries']: downloads(sys.argv[1]=='downloads')
    else: collect()
