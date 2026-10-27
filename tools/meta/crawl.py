"""Meta compiler, step 1: crawl recent top-vs-top games (research/v62/BIG_STRATEGIES.md, option A).

Lists each current top-N team's ranked matches, keeps finished games where both sides are top-N, and downloads their
native summaries (purchases, picks, events). Read-only: never queues matches or changes submissions.

  python tools/meta/crawl.py [--top 12] [--hours 24] [--max-summaries 800] [--out artifacts/local-only/meta/<stamp>]
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import json
from pathlib import Path
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / 'tools/vendor/cambc.exe'
LOCK = threading.Lock()
LAST = [0.0]


def call(args, timeout=120):
    for attempt in range(10):
        with LOCK:  # the API rate-limits: at most one request per 0.8 s
            time.sleep(max(0.0, 0.8 - (time.monotonic() - LAST[0])))
            LAST[0] = time.monotonic()
        p = subprocess.run([str(CLI), *args], capture_output=True, encoding='utf8', errors='replace', timeout=timeout)
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout
        time.sleep(3 + 3 * attempt)
    raise RuntimeError('cambc ' + ' '.join(args) + ': ' + (p.stdout + p.stderr)[-300:])


def ladder(top):
    rows = []
    for line in call(['ladder']).splitlines():
        parts = line.split(None, 3)
        if len(parts) == 4 and parts[0].isdigit():
            rows.append(dict(rank=int(parts[0]), rating=float(parts[1]), teamId=parts[2], name=parts[3].strip()))
    return [r for r in rows if r['rank'] <= top]


def team_matches(team_id, since):
    cursor, out = None, []
    for _ in range(40):
        args = ['matches', 'list', '--team', team_id, '--kind', 'ranked', '--limit', '100', '--json']
        if cursor:
            args += ['--cursor', cursor]
        d = json.loads(call(args))
        out += [m for m in d['matches'] if m['createdAt'] >= since]
        cursor = d.get('nextCursor')
        if not cursor or not d['matches'] or min(m['createdAt'] for m in d['matches']) < since:
            return out
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--top', type=int, default=12)
    ap.add_argument('--hours', type=float, default=24)
    ap.add_argument('--max-summaries', type=int, default=800)
    ap.add_argument('--out')
    a = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    out = Path(a.out) if a.out else ROOT / 'artifacts/local-only/meta' / now.strftime('%Y%m%d-%H%M')
    out.mkdir(parents=True, exist_ok=True)
    since = (now - dt.timedelta(hours=a.hours)).strftime('%Y-%m-%dT%H:%M:%S')
    tops = ladder(a.top)
    ids = {t['teamId'] for t in tops}
    games = {}
    for t in tops:
        ms = team_matches(t['teamId'], since)
        for m in ms:
            if m['status'] == 'finished' and all(x['teamId'] in ids for x in m['teams']):
                games[m['matchId']] = m
        print(f"{t['rank']:>2} {t['name'][:28]:28} {len(ms):4} ranked, {len(games):5} top-vs-top so far", flush=True)
    rows = sorted(games.values(), key=lambda m: m['createdAt'], reverse=True)
    (out / 'ladder.json').write_text(json.dumps(tops, indent=1), encoding='utf8')
    (out / 'matches.json').write_text(json.dumps(rows), encoding='utf8')
    sdir = out / 'summaries'
    sdir.mkdir(exist_ok=True)

    def fetch(m):
        p = sdir / f"{m['matchId']}.json"
        if not p.exists() or p.stat().st_size == 0:
            call(['matches', 'summary', m['matchId'], '--json', '--output', str(p)])
        return p

    done = 0
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        for f in cf.as_completed([ex.submit(fetch, m) for m in rows[:a.max_summaries]]):
            try:
                f.result()
                done += 1
            except Exception as e:  # one bad summary must not lose the crawl
                print('summary error', e, flush=True)
            if done % 100 == 0:
                print('summaries', done, flush=True)
    meta = dict(crawledAt=now.isoformat(), since=since, top=a.top, games=len(rows), summaries=done)
    (out / 'crawl.json').write_text(json.dumps(meta, indent=1), encoding='utf8')
    print('CRAWL', out, meta, flush=True)


if __name__ == '__main__':
    main()
