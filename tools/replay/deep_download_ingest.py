"""Preserve website-downloaded study bundles and summaries without opening holdout trajectories.

Reads only group ZIPs and match JSONs named in the frozen candidate manifest.
Extracts a fixed replay member, never arbitrary ZIP paths. No network or login.
"""
import argparse
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
STUDY = 'deep-2026-10-28'
UUID = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def preserve(target, raw):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_bytes() != raw:
        raise ValueError(f'Immutable evidence differs: {target.name}')
    if not target.exists():
        target.write_bytes(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--downloads', type=Path, default=Path.home() / 'Downloads')
    args = parser.parse_args()
    report_dir = ROOT / 'research' / STUDY
    work = ROOT / 'artifacts/local-only' / STUDY
    manifest = json.loads((report_dir / 'CANDIDATE_MANIFEST.json').read_text(encoding='utf-8'))
    candidates = {r['match_id']: r for r in manifest['rows']}
    groups = defaultdict(list)
    for row in candidates.values():
        groups[row['group_id']].append(row)
    rank = {'calibration-excluded': 0, 'wave1-v69': 1, 'existing-v69': 2, 'top-v-top': 3}
    queue = sorted(groups, key=lambda gid: (min(rank.get(r['partition'], rank.get(r['source'], 4)) for r in groups[gid]), gid))
    work.mkdir(parents=True, exist_ok=True)
    (work / 'website-queue.json').write_text(json.dumps(queue) + '\n')
    records, bundles = {}, []
    for gid in queue:
        path = args.downloads / f'match-group-{gid}.zip'
        target = work / 'bundles' / path.name
        if not path.exists() and not target.exists():
            continue
        raw = (path if path.exists() else target).read_bytes()
        if len(raw) > 32 * 1024 * 1024:
            raise ValueError('Group ZIP exceeds cap')
        preserve(target, raw)
        seen = set()
        with ZipFile(io.BytesIO(raw)) as outer:
            if outer.testzip() is not None:
                raise ValueError('Group ZIP checksum failed')
            for info in outer.infolist():
                match = re.fullmatch(rf'\d+-({UUID})\.zip', info.filename)
                if not match or info.file_size > 16 * 1024 * 1024:
                    raise ValueError(f'Unexpected group member: {info.filename}')
                mid = match[1]
                if mid in seen or mid not in candidates or candidates[mid]['group_id'] != gid:
                    raise ValueError('Duplicate/unexpected match in group ZIP')
                seen.add(mid)
                with ZipFile(io.BytesIO(outer.read(info))) as inner:
                    if inner.testzip() is not None:
                        raise ValueError('Match ZIP checksum failed')
                    ri = inner.getinfo('replay.repl26a')
                    if ri.file_size > 16 * 1024 * 1024:
                        raise ValueError('Replay exceeds cap')
                    replay = inner.read(ri)
                partition = candidates[mid]['partition']
                replay_path = work / 'replays' / partition / f'{mid}.repl26a'
                preserve(replay_path, replay)
                records[mid] = {'match_id': mid, 'group_id': gid, 'partition': partition,
                                'source': candidates[mid]['source'], 'replay_sha256': digest(replay),
                                'replay_bytes': len(replay), 'replay_path': replay_path.relative_to(ROOT).as_posix()}
        expected = {r['match_id'] for r in groups[gid]}
        if seen != expected:
            raise ValueError(f'Group member mismatch: {gid}')
        bundles.append({'group_id': gid, 'bytes': len(raw), 'sha256': digest(raw), 'games': len(seen)})
    summary_count = 0
    for mid, row in records.items():
        source = args.downloads / f'match-{mid}.json'
        target = ROOT / row['replay_path'].replace('.repl26a', '.summary.json')
        if not source.exists() and not target.exists():
            row['native_summary_present'] = False
            continue
        raw = (source if source.exists() else target).read_bytes()
        if len(raw) > 32 * 1024 * 1024:
            raise ValueError('Native summary exceeds cap')
        native = json.loads(raw)
        if native['match']['engineVersion'] != '2.0.0':
            raise ValueError('Wrong native engine')
        preserve(target, raw)
        row.update(native_summary_present=True, summary_sha256=digest(raw), summary_bytes=len(raw))
        summary_count += 1
    reconciliation_path = report_dir / 'RECONCILIATION.json'
    reconciled = json.loads(reconciliation_path.read_text(encoding='utf-8'))['games'] if reconciliation_path.exists() else []
    report = {'evidence_label': 'measured', 'updated_at': datetime.now(timezone.utc).isoformat(),
              'method': 'Signed-in official website Download 5 games and per-game Summary / Download JSON controls',
              'requested_groups': len(groups), 'downloaded_groups': len(bundles),
              'downloaded_replays': len(records), 'native_summaries': summary_count,
              'replays_by_partition': dict(Counter(r['partition'] for r in records.values())),
              'replay_native_reconciled': sum(r['passed'] and r['match_id'] in records for r in reconciled),
              'hands_off_trajectories_reviewed': False,
              'bundles': bundles, 'games': sorted(records.values(), key=lambda r: r['match_id'])}
    (report_dir / 'DOWNLOADS.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('bundles', 'games')}))


if __name__ == '__main__':
    main()
