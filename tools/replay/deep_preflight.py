"""Capture public evidence and exact input hashes before deep-analysis attribution.

No credentials, uploads, submissions, activations or match creation are supported.
Raw HTTP responses stay under artifacts/local-only. Source matching is byte-exact
using Git blob hashes from a pinned repository tree, never filename/version guesses.
"""
import argparse
import hashlib
import json
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

ORIGIN = 'https://2026a.battlecode.co.uk'
OURS = 'fcf5f666-ea55-4da0-b8d4-97c64bb37236'
ROOT = Path(__file__).resolve().parents[2]


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


class Public:
    def __init__(self, work):
        self.work, self.last = work, 0.0

    def get(self, endpoint, name):
        url = urllib.parse.urljoin(ORIGIN, endpoint)
        if urllib.parse.urlsplit(url).netloc != urllib.parse.urlsplit(ORIGIN).netloc:
            raise ValueError('Only official event-origin downloads are allowed')
        time.sleep(max(0, 1.1 - (time.monotonic() - self.last)))
        self.last = time.monotonic()
        request = urllib.request.Request(url, headers={'User-Agent': 'DOOMSDAY-deep-analysis/1.0'})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read(32 * 1024 * 1024 + 1)
            if len(raw) > 32 * 1024 * 1024:
                raise ValueError('Response exceeds size cap')
            dest = self.work / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
            return json.loads(raw)
        except urllib.error.HTTPError as error:
            return {'unavailable': True, 'http_status': error.code}


def input_provenance(manifest, inputs):
    by_bot = defaultdict(dict)
    for entry in manifest['files']:
        parts = PurePosixPath(entry['path']).parts
        if len(parts) >= 4 and parts[0] == 'bots' and parts[2] == 'src':
            by_bot[parts[1]]['/'.join(parts[2:])] = entry['sha']
    rows = []
    for input_path in sorted(inputs):
        files = {}
        with zipfile.ZipFile(input_path) as archive:
            for info in archive.infolist():
                path = PurePosixPath(info.filename)
                if info.is_dir():
                    continue
                if path.is_absolute() or '..' in path.parts or info.file_size > 8 * 1024 * 1024:
                    raise ValueError('Unexpected archive member')
                payload = archive.read(info)
                blob = hashlib.sha1(b'blob ' + str(len(payload)).encode() + b'\0' + payload).hexdigest()
                files[str(path)] = {'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(), 'git_blob_sha': blob}
        comparisons = []
        for bot, source in by_bot.items():
            shared = set(files) & set(source)
            matched = sum(files[p]['git_blob_sha'] == source[p] for p in shared)
            comparisons.append({'bot': bot, 'exact_matches': matched, 'shared_paths': len(shared),
                                'archive_files': len(files), 'repository_files': len(source),
                                'identical_tree': len(files) == len(source) == matched})
        rows.append({'archive': input_path.name, 'archive_sha256': hashlib.sha256(input_path.read_bytes()).hexdigest(),
                     'file_count': len(files), 'files': files,
                     'comparisons': sorted(comparisons, key=lambda row: (-row['exact_matches'], row['bot']))})
    return {'evidence_label': 'measured', 'base_branch': manifest['base_branch'],
            'base_commit': manifest['base_commit'], 'inputs': rows,
            'live_source_verified': False,
            'caveat': 'These attached archives have not been established as the live submission.'}


def repository_manifest(work, ref, branch):
    """Reuse the connector export, or reproduce it from a full local Git checkout."""
    path = work / 'repository-tree.json'
    if path.exists():
        manifest = json.loads(path.read_text())
        if manifest['base_commit'] != ref or manifest['base_branch'] != branch:
            raise ValueError('Cached repository tree differs from requested provenance')
        return manifest
    raw = subprocess.check_output(['git', 'ls-tree', '-r', '-l', '-z', ref], cwd=ROOT)
    entries = []
    for row in raw.split(b'\0'):
        if not row:
            continue
        header, name = row.split(b'\t', 1)
        mode, kind, sha, size = header.decode('ascii').split()
        if kind == 'blob':
            entries.append({'path': name.decode('utf-8'), 'sha': sha, 'size': int(size)})
    manifest = {'base_branch': branch, 'base_commit': ref, 'files': entries}
    save(path, manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--repository-ref', default='294500b8c4da4af19a81f2cdb262305ea54d27f9')
    parser.add_argument('--repository-branch', default='claude/compare-fix-replay-decoder')
    args = parser.parse_args()
    args.work = args.work.resolve()
    if not args.work.is_relative_to(ROOT / 'artifacts/local-only'):
        parser.error('Raw evidence must be under artifacts/local-only')
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = repository_manifest(args.work, args.repository_ref, args.repository_branch)
    provenance = input_provenance(manifest, args.inputs.glob('*.zip'))
    save(args.out / 'INPUT_PROVENANCE.json', provenance)
    api = Public(args.work)
    ladder = api.get('/api/v1/ladder?page=1&pageSize=100&category=all', 'public/ladder.json')
    rows = [{key: team.get(key) for key in ['teamId', 'name', 'rank', 'rating', 'category']}
            for team in ladder.get('teams', [])]
    snapshot = {'evidence_label': 'measured', 'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'server_updated_at': ladder.get('updatedAt'), 'n_teams': len(rows), 'teams': rows,
                'learn_cohort': [team for team in rows if team.get('rank', 9999) <= 5],
                'climb_rank_candidates': [team for team in rows if 15 <= team.get('rank', 9999) <= 40],
                'cohorts_finalized': False, 'caveat': 'Climb selection needs since-activation losses; no opponent is queued.'}
    save(args.out / 'PUBLIC_SNAPSHOT.json', snapshot)
    groups = api.get('/api/v1/match-groups?scope=all&team=' + OURS, 'public/our-latest-groups.json')
    group_rows = groups.get('groups', [])
    if group_rows:
        detail = api.get('/api/v1/match-groups/' + group_rows[0]['id'], 'public/latest-group.json')
        save(args.work / 'public/latest-group-normalized.json', detail)
    print(json.dumps({'archives': len(provenance['inputs']), 'ladder_teams': len(rows),
                      'public_groups': len(group_rows), 'source_attribution': 'unverified'}))


if __name__ == '__main__':
    main()
