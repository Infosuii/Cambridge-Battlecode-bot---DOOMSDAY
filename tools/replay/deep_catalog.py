"""Join version-filtered UI group IDs to public match metadata, paced and resumable."""
import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from deep_preflight import ROOT, ORIGIN, OURS, save


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ui', type=Path, required=True)
    p.add_argument('--study', default='deep-2026-10-28')
    a = p.parse_args()
    work = ROOT / 'artifacts/local-only' / a.study
    out = ROOT / 'research' / a.study
    source = json.loads(a.ui.read_text())
    if source['source_url'] != ORIGIN + '/game/matches?group-version=69':
        raise ValueError('Expected the observed platform-v69 filter')
    work.mkdir(parents=True, exist_ok=True)
    (work / 'v69-ui-groups.json').write_bytes(a.ui.read_bytes())
    catalog = []
    issues = []
    last = 0.0

    def fetch(endpoint, cache):
        nonlocal last
        path = work / cache
        if path.exists():
            return json.loads(path.read_text())
        time.sleep(max(0, 1.2 - (time.monotonic() - last)))
        last = time.monotonic()
        req = urllib.request.Request(ORIGIN + endpoint, headers={'User-Agent':'DOOMSDAY-deep-analysis/1.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read(8 * 1024 * 1024 + 1)
        if len(raw) > 8 * 1024 * 1024:
            raise ValueError('Metadata size cap exceeded')
        d = json.loads(raw)
        save(path, d)
        return d

    for index, evidence in enumerate(source['rows']):
        if evidence.get('version') != 'v69':
            issues.append({'url':evidence['url'], 'reason':'UI did not explicitly show v69'})
            continue
        url = urllib.parse.urlsplit(evidence['url'])
        if url.netloc != urllib.parse.urlsplit(ORIGIN).netloc or not url.path.startswith('/game/match-groups/'):
            raise ValueError('Unexpected UI group link')
        gid = str(uuid.UUID(url.path.rsplit('/', 1)[-1]))
        try:
            d = fetch('/api/v1/match-groups/' + gid, 'groups/' + gid + '.json')
        except (urllib.error.URLError, ValueError) as exc:
            issues.append({'group_id':gid,'reason':str(exc)})
            save(out / 'CATALOG_STATUS.json', {'groups_seen':index+1,'issues':issues,'status':'interrupted'})
            break  # respect rate/auth/network errors; never retry in a loop
        for m in d.get('matches', []):
            sides = sorted(m.get('sides', []), key=lambda x:x['side'])
            own = next((s for s in sides if s['teamId'] == OURS), None)
            if own is None:
                issues.append({'match_id':m['id'],'reason':'DOOMSDAY absent'})
                continue
            explicit = own.get('version')
            if explicit is not None and explicit != 69:
                issues.append({'match_id':m['id'],'reason':'Metadata contradicts UI version'})
                continue
            enemy = next(s for s in sides if s['teamId'] != OURS)
            catalog.append({'match_id':m['id'],'group_id':gid,'kind':m.get('kind'),
                            'status':m.get('status'),'map':m.get('map'),'map_id':m.get('mapId'),
                            'created_at':m.get('createdAt'),'rounds':m.get('rounds'),
                            'patch_id':m.get('patchId'),'own_side':own['side'],
                            'result':own.get('result'),'our_score':own.get('score'),
                            'opponent_score':enemy.get('score'),'opponent_id':enemy['teamId'],
                            'opponent':enemy['teamName'],'platform_version':69,
                            'version_basis':'authenticated version-filtered UI group row',
                            'source_identity_basis':'user-provided live archive; server hash not independently verified',
                            'replay_url':m.get('replayUrl'),'reconciled':False})
        save(work / 'catalog.json', catalog)
        if (index+1) % 10 == 0:
            print(json.dumps({'groups':index+1,'games':len(catalog)}), flush=True)
    finished = [r for r in catalog if r['status']=='finished']
    games = {r['match_id']:r for r in finished}
    maps = defaultdict(lambda: {'games':0,'wins':0,'losses':0,'margin_sum':0,'sides':Counter()})
    opponents = defaultdict(lambda: {'games':0,'wins':0,'losses':0,'margin_sum':0,'name':None})
    for r in games.values():
        margin = (r['our_score'] or 0) - (r['opponent_score'] or 0)
        for row in (maps[r['map']], opponents[r['opponent_id']]):
            row['games'] += 1
            row['wins'] += r['result']=='win'
            row['losses'] += r['result']=='loss'
            row['margin_sum'] += margin
        maps[r['map']]['sides'][r['own_side']] += 1
        opponents[r['opponent_id']]['name'] = r['opponent']
    report = {'evidence_label':'measured', 'recorded_at':datetime.now(timezone.utc).isoformat(),
              'ui_groups_captured':len(source['rows']), 'groups_expanded':len({r['group_id'] for r in catalog}),
              'finished_games':len(games), 'wins':sum(r['result']=='win' for r in games.values()),
              'losses':sum(r['result']=='loss' for r in games.values()),
              'earliest_created_at':min((r['created_at'] for r in games.values()),default=None),
              'latest_created_at':max((r['created_at'] for r in games.values()),default=None),
              'kinds':dict(Counter(r['kind'] for r in games.values())),
              'patch_ids':dict(Counter(r['patch_id'] for r in games.values())),
              'by_map':dict(maps), 'by_opponent':dict(opponents), 'issues':issues,
              'metadata_only':True,'reconciled_games':0,
              'caveat':'UI catalog may be incomplete; selection and version evidence are preserved. No detector conclusions.'}
    save(out / 'V69_METADATA.json', report)
    save(out / 'CATALOG_STATUS.json', {'status':'complete_for_captured_ui_rows' if not issues else 'has_issues',
                                      'groups':report['groups_expanded'],'games':len(games),'issues':issues})
    print(json.dumps({k:report[k] for k in ['ui_groups_captured','groups_expanded','finished_games','wins','losses','earliest_created_at','latest_created_at']}))


if __name__ == '__main__':
    main()
