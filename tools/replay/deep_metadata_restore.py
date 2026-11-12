"""Read public official metadata for frozen study groups, paced and cached.

No login, private endpoint, new match or source download is supported.
Do not change membership, outcomes or the preserved partitions.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from deep_preflight import ROOT, Public, OURS


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2) + '\n').encode('utf-8'))


def main():
    study = ROOT / 'research/deep-2026-10-28'
    work = ROOT / 'artifacts/local-only/deep-2026-10-28'
    manifest = json.loads((study / 'CANDIDATE_MANIFEST.json').read_text(encoding='utf-8'))
    wanted = {r['match_id']: r for r in manifest['rows']}
    group_ids = sorted({r['group_id'] for r in wanted.values()})
    public = Public(work)
    catalog = []
    for i, gid in enumerate(group_ids):
        cache = work / 'groups' / f'{gid}.json'
        value = json.loads(cache.read_text(encoding='utf-8')) if cache.exists() else public.get('/api/v1/match-groups/' + gid, 'groups/' + gid + '.json')
        if value.get('unavailable'):
            raise RuntimeError(f'Official public metadata unavailable: {value}')
        matches = value['matches']
        if {m['id'] for m in matches} != {r['match_id'] for r in wanted.values() if r['group_id'] == gid}:
            raise ValueError('Public group membership differs from frozen manifest')
        for match in matches:
            row = wanted[match['id']]
            if match.get('status') != 'finished' or not match['patchId'].startswith('2.0.0:85aa7167b44d') or match['map'] != row['map']:
                raise ValueError('Public engine/map/status contradicts frozen study')
            sides = match['sides']
            own = next((s for s in sides if s['teamId'] == OURS), None)
            enemy = next((s for s in sides if s['teamId'] != OURS), None) if own else None
            if own and (own['side'] != row['side'] or own['result'] != row['result']):
                raise ValueError('Public own side/outcome contradicts frozen study')
            native = json.loads((work / 'replays' / row['partition'] / (row['match_id'] + '.summary.json')).read_text(encoding='utf-8'))
            if match['patchId'].split(':')[:2] != [native['match']['engineVersion'], native['match']['engineBuildHash']]:
                raise ValueError('Public engine version/build differs from reconciled native summary')
            if match['rounds'] != native['match']['roundsStarted']:
                raise ValueError('Public round count differs from reconciled native summary')
            if any(int(side['score']) != int(next(t['submittedGems'] for t in native['teams']
                       if t['team'] == ('teamA' if side['side'] == 'a' else 'teamB'))) for side in sides):
                raise ValueError('Public scores differ from reconciled native summary')
            catalog.append({**row, 'opponent_id': enemy['teamId'] if enemy else None,
                            'opponent': enemy['teamName'] if enemy else None,
                            'rounds': match['rounds'], 'patch_id': match['patchId'],
                            'sides': sides, 'metadata_source': 'public official group read on resume'})
        if (i + 1) % 10 == 0:
            save(work / 'restored-catalog.json', catalog)
            print(json.dumps({'public_groups_read': i + 1, 'games': len(catalog)}), flush=True)
    save(work / 'restored-catalog.json', catalog)
    save(study / 'METADATA_RESTORE.json', {'evidence_label': 'measured', 'updated_at': datetime.now(timezone.utc).isoformat(),
         'groups': len(group_ids), 'games': len(catalog), 'frozen_membership_side_map_engine_outcomes_agree': True,
         'public_rounds_and_scores_match_native': True,
         'full_public_engine_version_build_match_native': True,
         'authentication_used': False, 'new_requests_created': 0,
         'raw_metadata': 'artifacts/local-only/deep-2026-10-28/restored-catalog.json'})
    print(json.dumps({'restored_groups': len(group_ids), 'restored_games': len(catalog)}))


if __name__ == '__main__':
    main()
