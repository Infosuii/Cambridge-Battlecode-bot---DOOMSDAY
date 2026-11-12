"""Proxy opponent, step 1: the ladder evidence the proxy is fitted to and judged by (read-only; never queues matches).

  python tools/proxy/fetch.py arms --plan research/v59/duel_top1.json --out research/proxy/ladder_arms.json
      Every finished game of every arm of a ladder duel plan: group, slot, map, our side, opponent, win, gem margin.
      This is the ladder verdict a local proxy has to reproduce.
  python tools/proxy/fetch.py replays --arms research/proxy/ladder_arms.json --arm v65 --crawl <meta crawl dir>
         --top-per-team 30 --out artifacts/local-only/proxy/replays
      Replays of that arm's duel games (us against the top 12, both sides in the same fights) and a sample of
      top-vs-top games from a meta crawl: the most recent games of each top team, at most --top-per-team per team.
      Each replay is unpacked to <out>/<match id>.repl26a; <out>/index.json says where every file came from.
"""
import argparse
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/meta'))
from crawl import call  # noqa: E402  (rate-limited cambc wrapper)

US = 'DOOMSDAY'


def our_unranked(since):
    found, cursor = {}, None
    for _ in range(40):
        args = ['matches', 'list', '--team', 'me', '--kind', 'unranked', '--limit', '100', '--json'] + (['--cursor', cursor] if cursor else [])
        d = json.loads(call(args))
        for m in d['matches']:
            found[m['matchId']] = m
        cursor = d.get('nextCursor')
        if not cursor or not d['matches'] or min(m['createdAt'] for m in d['matches']) < since:
            break
    return found


def summary_margin(match_id, side):
    cache = ROOT / 'artifacts/local-only/duels' / f'{match_id}.json'  # shared with ladder_duel.py --margins
    if not cache.exists() or cache.stat().st_size == 0:
        cache.parent.mkdir(parents=True, exist_ok=True)
        call(['matches', 'summary', match_id, '--json', '--output', str(cache)])
    d = json.loads(cache.read_text(encoding='utf-8-sig'))
    gems = {t['team']: float(t['submittedGems']) for t in d['teams']}
    us = 'team' + side.upper()
    return gems[us] - gems['teamB' if us == 'teamA' else 'teamA']


def arms(a):
    plan = json.loads(Path(a.plan).read_text(encoding='utf8'))
    since = min(v['since'] for v in plan['arms'].values())
    found = our_unranked(since)
    rows = []
    for arm, info in plan['arms'].items():
        slot_of = {gid: i for i, gid in enumerate(info['groups']) if gid}
        for m in found.values():
            if m['groupId'] not in slot_of or m['status'] != 'finished':
                continue
            us = next(t for t in m['teams'] if t['name'] == US)
            them = next(t for t in m['teams'] if t['name'] != US)
            g = slot_of[m['groupId']]
            rows.append(dict(arm=arm, version=info['version'], group=g, slot=m['position'], matchId=m['matchId'], map=m['map'],
                             side=us['side'], opponent=them['name'], opponentId=them['teamId'], win=us['result'] == 'win',
                             margin=summary_margin(m['matchId'], us['side']), ourPicks=us.get('draftPicks'),
                             theirPicks=them.get('draftPicks')))
    rows.sort(key=lambda r: (r['arm'], r['group'], r['slot']))
    for arm in plan['arms']:
        r = [x for x in rows if x['arm'] == arm]
        print(f"{arm:6} {len(r):4} games, {sum(x['win'] for x in r):3} wins, margin {sum(x['margin'] for x in r) / max(1, len(r)):+.1f}")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(dict(plan=a.plan, games=rows), indent=1) + '\n', encoding='utf8', newline='\n')


def unpack(match_id, out):
    dest = out / f'{match_id}.repl26a'
    if dest.exists() and dest.stat().st_size:
        return dest
    raw = out / f'{match_id}.zip'
    if not raw.exists() or not raw.stat().st_size:
        call(['matches', 'download', match_id, '--output', str(raw)], timeout=300)
    with zipfile.ZipFile(raw) as z:
        if z.testzip() is not None:
            raise RuntimeError('invalid ZIP ' + match_id)
        dest.write_bytes(z.read('replay.repl26a'))
    raw.unlink()
    return dest


def replays(a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ipath = out / 'index.json'
    index = json.loads(ipath.read_text(encoding='utf8')) if ipath.exists() else {}
    want = {}
    for r in json.loads(Path(a.arms).read_text(encoding='utf8'))['games']:
        if r['arm'] == a.arm:
            want[r['matchId']] = dict(source='duel', arm=r['arm'], group=r['group'], slot=r['slot'], map=r['map'],
                                      ourSide=r['side'], opponent=r['opponent'], win=r['win'])
    if a.crawl:
        tops = json.loads((Path(a.crawl) / 'ladder.json').read_text(encoding='utf8'))
        ms = json.loads((Path(a.crawl) / 'matches.json').read_text(encoding='utf8'))  # newest first
        count = {t['name']: 0 for t in tops}
        for m in ms:
            names = [t['name'] for t in m['teams']]
            if m.get('status') != 'finished' or any(t.get('engineVersion') != '2.0.0' for t in m['teams']):
                continue
            if all(count[n] >= a.top_per_team for n in names):
                continue
            for n in names:
                count[n] += 1
            sides = {t['side']: t for t in m['teams']}
            want[m['matchId']] = dict(source='top', map=m['map'], teamA=sides['a']['name'], teamB=sides['b']['name'],
                                      picksA=sides['a']['draftPicks'], picksB=sides['b']['draftPicks'],
                                      winner='a' if sides['a']['result'] == 'win' else 'b', createdAt=m['createdAt'])
        print('top-vs-top sample per team:', count, flush=True)
    done = 0
    for mid, info in want.items():
        try:
            unpack(mid, out)
            index[mid] = info
            done += 1
        except Exception as e:  # one bad download must not lose the rest
            print('replay error', mid, e, flush=True)
        if done % 25 == 0:
            print('replays', done, '/', len(want), flush=True)
            ipath.write_text(json.dumps(index, indent=1), encoding='utf8', newline='\n')
    ipath.write_text(json.dumps(index, indent=1), encoding='utf8', newline='\n')
    print('REPLAYS', done, '/', len(want), '->', out, flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('action', choices=['arms', 'replays'])
    ap.add_argument('--plan')
    ap.add_argument('--arms')
    ap.add_argument('--arm', default='v65')
    ap.add_argument('--crawl')
    ap.add_argument('--top-per-team', type=int, default=30)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    (arms if a.action == 'arms' else replays)(a)


if __name__ == '__main__':
    main()
