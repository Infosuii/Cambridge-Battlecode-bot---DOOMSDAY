"""Bounded replay acquisition for a descriptive scouting study.

Public metadata; downloads optionally use an existing user-created CLI session.
Never handles credentials, trains or creates matches. Raw responses/replays stay
under artifacts/local-only. Run catalog, inspect selection, then download.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import time
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BASE = 'https://2026a.battlecode.co.uk'
OURS = 'fcf5f666-ea55-4da0-b8d4-97c64bb37236'
FOCUS = ['01boss_battle', '01concentrated_wealth', '00elkring', '00swirl',
         '01yellow_brick_road', '00stampede', '01big_world', '01islands']


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')


class Public:
    def __init__(self, root):
        self.root, self.last = root, 0

    def get(self, endpoint, cache):
        dest = self.root / cache
        if dest.exists():
            return dest.read_bytes()
        url = urllib.parse.urljoin(BASE, endpoint)
        if urllib.parse.urlparse(url).netloc != urllib.parse.urlparse(BASE).netloc:
            raise ValueError('Unexpected download host: ' + url)
        time.sleep(max(0, 1.05 - (time.monotonic() - self.last)))
        self.last = time.monotonic()
        request = urllib.request.Request(url, headers={'User-Agent': 'Battlecode-descriptive-scout/1.0'})
        with urllib.request.urlopen(request, timeout=45) as response:
            raw = response.read(32 * 1024 * 1024 + 1)
        if len(raw) > 32 * 1024 * 1024:
            raise ValueError('Download exceeds study size cap')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        return raw

    def json(self, endpoint, cache):
        return json.loads(self.get(endpoint, cache).decode('utf-8-sig'))


def catalog(a, api):
    if not (a.work / 'ladder.json').exists():
        api.get('/api/v1/ladder?page=1&pageSize=100&category=all', 'ladder.json')
    ladder = json.loads((a.work / 'ladder.json').read_text(encoding='utf-8-sig'))
    teams = ladder['teams'][:6] + [dict(teamId=OURS, name='DOOMSDAY')]
    matches, groups_seen = {}, set()
    for team in teams:
        cursor, groups = None, []
        limit = 12 if team['teamId'] == OURS else 5
        for page in range(12):
            query = dict(scope='all', team=team['teamId'])
            if cursor:
                query['before'] = cursor
            data = api.json('/api/v1/match-groups?' + urllib.parse.urlencode(query),
                            f"lists/{team['teamId']}-{page}.json")
            groups += [g for g in data['groups'] if g['kind'] == 'ranked' and g['status'] == 'finished']
            cursor = data.get('next')
            if len(groups) >= limit or not data.get('more') or not cursor:
                break
        for group in groups[:limit]:
            if group['id'] in groups_seen:
                continue
            groups_seen.add(group['id'])
            detail = api.json('/api/v1/match-groups/' + group['id'], f"groups/{group['id']}.json")
            for match in detail['matches']:
                if match['status'] == 'finished' and match.get('replayUrl'):
                    matches[match['id']] = dict(match, group_id=group['id'])
        print(json.dumps(dict(event='catalog_team', team=team['name'], groups=min(limit, len(groups)),
                              matches=len(matches))), flush=True)
    save(a.work / 'catalog.json', list(matches.values()))
    by_rank = {t['teamId']: t['rank'] for t in ladder['teams']}
    selected, used = [], set()
    # Fix selection before decoding: four distinct maps per top-six team, preferring
    # declared problem maps and top-25 opponents; no selection by replay outcome.
    for team in teams[:6]:
        pool = [m for m in matches.values() if any(s['teamId'] == team['teamId'] for s in m['sides'])]
        def order(m):
            opponent = next(s for s in m['sides'] if s['teamId'] != team['teamId'])
            return (0 if m['map'] in FOCUS else 1,
                    0 if by_rank.get(opponent['teamId'], 9999) <= 25 else 1,
                    FOCUS.index(m['map']) if m['map'] in FOCUS else 99,
                    ''.join(chr(127 - ord(c)) for c in m['createdAt']), m['id'])
        maps = set()
        for m in sorted(pool, key=order):
            if m['id'] in used or m['map'] in maps:
                continue
            selected.append(dict(m, cohort='top', focal_team=team['teamId']))
            maps.add(m['map']); used.add(m['id'])
            if len(maps) == 4:
                break
    # The public platform deliberately hides submission versions. If absent, use
    # the documented v52 deployment window and label attribution as unverified.
    pool = [m for m in matches.values() if m['createdAt'] >= '2026-10-25T12:05:00Z'
            and any(s['teamId'] == OURS and s.get('version') in (None, 52) for s in m['sides'])]
    top_maps = {m['map'] for m in selected}
    pool.sort(key=lambda m: (0 if m['map'] in top_maps else 1, 0 if m['map'] in FOCUS else 1,
                              m['map'], m['id']))
    counts = {}
    for m in pool:
        if counts.get(m['map'], 0) >= 2 or m['id'] in used:
            continue
        own = next(s for s in m['sides'] if s['teamId'] == OURS)
        selected.append(dict(m, cohort='ours_post_v52', focal_team=OURS,
                             version_verified=own.get('version') == 52,
                             version_basis='public version' if own.get('version') == 52 else
                             'after documented v52 deployment; public version hidden'))
        counts[m['map']] = counts.get(m['map'], 0) + 1; used.add(m['id'])
        if sum(counts.values()) >= 12:
            break
    save(a.work / 'selection.json', selected)
    print(json.dumps(dict(event='selected', top=sum(m['cohort'] == 'top' for m in selected),
                          ours=sum(m['cohort'].startswith('ours') for m in selected),
                          maps=sorted({m['map'] for m in selected}))), flush=True)


def download(a, api):
    selected = json.loads((a.work / 'selection.json').read_text(encoding='utf-8'))
    receipts = []
    for m in selected:
        bundle = a.work / 'bundles' / (m['id'] + '.zip')
        if a.cli and not bundle.exists():
            bundle.parent.mkdir(parents=True, exist_ok=True)
            for attempt in range(4):
                result = subprocess.run([str(a.cli.resolve()), 'matches', 'download', m['id'],
                                         '--output', str(bundle)], capture_output=True, timeout=90)
                if not result.returncode:
                    break
                message = result.stderr.decode('utf-8', 'replace')[-1500:]
                if '429' not in message or attempt == 3:
                    raise RuntimeError(message)
                retry = re.search(r'retry after (\d+) seconds', message)
                time.sleep(max(3, int(retry[1]) if retry else 5) + 2 * attempt)
            time.sleep(1.5)
        raw = bundle.read_bytes() if bundle.exists() else api.get(m['replayUrl'], f"bundles/{m['id']}.zip")
        if len(raw) > 32 * 1024 * 1024:
            raise ValueError('Bundle exceeds the study size cap')
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            entries = z.infolist()
            if len(entries) > 64 or sum(i.file_size for i in entries) > 128 * 1024 * 1024:
                raise ValueError('Unexpected replay bundle size')
            names = [i.filename for i in entries if i.filename.endswith('.repl26a')]
            if len(names) != 1:
                raise ValueError('Expected exactly one raw replay')
            payload = z.read(names[0])
        if not payload.startswith(b'a62per'):
            raise ValueError('Unexpected replay magic')
        dest = a.work / 'replays' / (m['id'] + '.repl26a')
        dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(payload)
        receipts.append(dict(match_id=m['id'], bundle_bytes=len(raw), replay_bytes=len(payload),
                             replay_sha256=hashlib.sha256(payload).hexdigest(),
                             bundle_sha256=hashlib.sha256(raw).hexdigest(),
                             replay_header=payload[:16].hex()))
        save(a.work / 'downloads.json', receipts)
        print(json.dumps(dict(event='downloaded', count=len(receipts), match=m['id'], bytes=len(raw))), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage', choices=['catalog', 'download'])
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--cli', type=Path, help='Use an existing user-created CLI session for replay downloads')
    a = p.parse_args(); a.work = a.work.resolve()
    if not a.work.is_relative_to(ROOT / 'artifacts/local-only'):
        raise SystemExit('Raw study data must stay under artifacts/local-only')
    api = Public(a.work)
    (catalog if a.stage == 'catalog' else download)(a, api)


if __name__ == '__main__':
    main()
