"""Our recent losses to strong teams, with their summaries and replays, for studying what the winners did.

Lists every DOOMSDAY match (ranked and unranked) since --hours ago, keeps the losses to teams rated >= --min-rating
on the current ladder (teams not on the fetched ladder pages are below it), drops exact repeats (same opponent,
map, side and both drafts: games are deterministic, so a repeated group adds nothing), then downloads each kept
match's summary (JSON) and replay bundle.
  python tools/ladder/losses_recent.py [--hours 48] [--min-rating 2000] [--out data/ladder/losses48]
Writes OUT/matches.json (kept losses with opponent rating), OUT/ladder.json, OUT/summaries/<id>.json and
artifacts/local-only/losses48/<id>.zip (replays, not committed).
"""
import argparse, json, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
CLI = str(ROOT / 'tools/vendor/cambc.exe')


def cli_json(args, tries=8):
    for t in range(tries):
        r = subprocess.run([CLI] + args, capture_output=True)
        try:
            return json.loads(r.stdout.decode('utf-8'))
        except ValueError:
            time.sleep(3 + 3 * t)
    raise SystemExit('cambc ' + ' '.join(args) + ' failed: ' + (r.stdout + r.stderr).decode('utf-8', 'replace')[-300:])


def fetch(cmd_args, path, tries=12):
    import re
    for t in range(tries):
        if path.exists() and path.stat().st_size > 0: return True
        r = subprocess.run([CLI] + cmd_args + ['-o', str(path)], capture_output=True)
        if path.exists() and path.stat().st_size > 0:
            time.sleep(0.4)  # pace requests: the platform answers bursts with HTTP 429
            return True
        w = re.search(r'retry after (\d+) seconds', (r.stdout + r.stderr).decode('utf-8', 'replace'))
        time.sleep((int(w.group(1)) + 1) if w else 3 * (t + 1))
    return False


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--hours', type=float, default=48); ap.add_argument('--min-rating', type=float, default=2000)
    ap.add_argument('--out', default='data/ladder/losses48'); ap.add_argument('--replays', default='artifacts/local-only/losses48')
    ap.add_argument('--reuse', action='store_true', help='skip listing: download for the existing OUT/matches.json'); ap.add_argument('--workers', type=int, default=1)
    a = ap.parse_args()
    out = ROOT / a.out; (out / 'summaries').mkdir(parents=True, exist_ok=True); rep = ROOT / a.replays; rep.mkdir(parents=True, exist_ok=True)
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=a.hours)).strftime('%Y-%m-%dT%H:%M')
    if a.reuse:
        kept = json.loads((out / 'matches.json').read_text(encoding='utf-8'))
        return download(kept, out, rep, a.workers)
    ladder, page = {}, 1
    while True:
        d = cli_json(['ladder', '--json', '--page', str(page), '--limit', '25'])
        teams = d['teams'] if isinstance(d, dict) else d
        for t in teams: ladder[t['name']] = dict(rating=t['rating'], rank=t['rank'], teamId=t['teamId'])
        if not teams or min(t['rating'] for t in teams) < a.min_rating - 50: break
        page += 1
    (out / 'ladder.json').write_text(json.dumps(ladder, indent=1, ensure_ascii=False), encoding='utf-8')
    allm = []
    for kind in ('ranked', 'unranked'):
        cur = None
        for _ in range(200):
            d = cli_json(['matches', 'list', '--team', 'me', '--kind', kind, '--limit', '100', '--json'] + (['--cursor', cur] if cur else []))
            ms = d['matches']; allm += [dict(m, kind=kind) for m in ms if m['createdAt'] >= cutoff]
            cur = d.get('nextCursor')
            if not cur or not ms or min(m['createdAt'] for m in ms) < cutoff: break
    print(len(allm), 'matches since', cutoff, flush=True)
    kept, seen = [], set()
    for m in sorted(allm, key=lambda m: m['createdAt']):
        if m.get('status') != 'finished': continue
        us = next((t for t in m['teams'] if t['name'] == 'DOOMSDAY'), None); op = next((t for t in m['teams'] if t['name'] != 'DOOMSDAY'), None)
        if not us or not op or us['result'] == 'win': continue
        r = ladder.get(op['name'], {}).get('rating')
        if r is None or r < a.min_rating: continue
        key = (op['name'], m['map'], us['side'], tuple(us.get('draftPicks') or []), tuple(op.get('draftPicks') or []))
        if key in seen: continue
        seen.add(key)
        kept.append(dict(matchId=m['matchId'], createdAt=m['createdAt'], kind=m['kind'], map=m['map'], side=us['side'],
                         opponent=op['name'], opp_rating=round(r), opp_rank=ladder[op['name']]['rank'],
                         our_draft=us.get('draftPicks'), their_draft=op.get('draftPicks'), endReason=m.get('endReason'), groupId=m.get('groupId')))
    (out / 'matches.json').write_text(json.dumps(kept, indent=1, ensure_ascii=False), encoding='utf-8')
    print(len(kept), 'distinct losses to teams rated >=', a.min_rating, flush=True)

    download(kept, out, rep, a.workers)


def download(kept, out, rep, workers):
    def get(m):
        ok1 = fetch(['matches', 'summary', '--json', m['matchId']], out / 'summaries' / f"{m['matchId']}.json")
        ok2 = fetch(['matches', 'download', m['matchId']], rep / f"{m['matchId']}.zip")
        return ok1, ok2
    done = [0, 0]
    with ThreadPoolExecutor(workers) as ex:
        for i, (s, r) in enumerate(ex.map(get, kept)):
            done[0] += s; done[1] += r
            if i % 25 == 0: print(f'{i + 1}/{len(kept)} summaries {done[0]} replays {done[1]}', flush=True)
    print('done: summaries', done[0], 'replays', done[1], 'of', len(kept))


if __name__ == '__main__':
    main()
