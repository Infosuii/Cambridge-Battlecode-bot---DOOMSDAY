"""Read and validate compact replay shards written by decode_replays.mjs --format npz (format `replay-shard-v1`).

Shards are plain NumPy .npz files with a JSON sidecar; the array layout is documented in npz_shards.mjs.

    python tools/replay/replay_shards.py validate --shards <dir> --jsonl <decode_replays.mjs JSONL of the same replays>

`validate` checks the manifest (format, shard SHA-256, counts), loads every shard with numpy.load(allow_pickle=False) and
compares each replay value by value with the JSONL decoder output: metadata, every action, final champions, summary
checks, failures and, for perspective shards, every turn, cooldown and fog-limited view entity (null == NaN).
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

FORMAT = 'replay-shard-v1'


def load_manifest(directory):
    manifest = json.loads((Path(directory) / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('format') != FORMAT:
        raise ValueError(f'unsupported shard format {manifest.get("format")}')
    return manifest


def iter_replays(directory, verify_sha256=True):
    """Yield one dict per decoded replay: name, sidecar entry, metadata, actions, final champions and (perspective) turns."""
    directory = Path(directory)
    manifest = load_manifest(directory)
    for shard in manifest['shards']:
        path = directory / shard['npz']
        if verify_sha256 and hashlib.sha256(path.read_bytes()).hexdigest() != shard['sha256']:
            raise ValueError(f'shard hash mismatch: {path}')
        sidecar = json.loads((directory / shard['json']).read_text(encoding='utf-8'))
        columns = sidecar['meta_columns']
        with np.load(path, allow_pickle=False) as z:
            a = {k: z[k] for k in z.files}
        if len(sidecar['replays']) != len(a['meta']):
            raise ValueError(f'sidecar/array row mismatch in {path}')
        for entry in sidecar['replays']:
            r = entry['row']
            out = dict(replay=entry['replay'], entry=entry, meta=dict(zip(columns, a['meta'][r].tolist())),
                       actions=a['actions'][a['action_offsets'][r]:a['action_offsets'][r + 1]],
                       final_champions=a['final_champions'][a['champion_offsets'][r]:a['champion_offsets'][r + 1]])
            if sidecar['perspective']:
                t0, t1 = a['turn_offsets'][r], a['turn_offsets'][r + 1]
                vc, vk = a['view_champion_offsets'], a['view_camp_offsets']
                out['turns'] = a['turns'][t0:t1]
                out['cooldowns'] = a['cooldowns'][t0:t1]
                out['views'] = [(a['view_champions'][vc[t]:vc[t + 1]], a['view_camps'][vk[t]:vk[t + 1]]) for t in range(t0, t1)]
            yield out


def _floats(rows, width):
    return np.asarray([[np.nan if v is None else v for v in row] for row in rows], np.float32).reshape(-1, width)


def validate(shards, jsonl):
    manifest = load_manifest(shards)
    rows = {}
    with open(jsonl, encoding='utf-8') as f:
        for line in f:
            row = json.loads(line)
            rows[row['replay']] = row
    seen, problems = set(), []
    sidecar_failed = []
    for shard in manifest['shards']:
        sidecar_failed += json.loads((Path(shards) / shard['json']).read_text(encoding='utf-8'))['failed']
    for rep in iter_replays(shards):
        name = rep['replay']
        seen.add(name)
        row = rows.get(name)
        if row is None or not row['ok']:
            problems.append((name, 'decoded in shards but not in JSONL'))
            continue
        meta = rep['meta']
        expect = dict(width=row['width'], height=row['height'], steps=row['steps'], inputs=row['inputs'],
                      timeline_size=row['timeline_size'], rounds=row['rounds'], outcome=row['outcome'],
                      submitted_gems_a=row['submitted_gems'][0], submitted_gems_b=row['submitted_gems'][1],
                      fuel_exhausted_turns=row['fuel_exhausted_turns'], error_turns=row['error_turns'])
        if meta != expect:
            problems.append((name, f'meta {meta} != {expect}'))
        if not np.array_equal(rep['actions'], np.asarray(row['actions'], np.int64).reshape(-1, 8)):
            problems.append((name, 'actions differ'))
        champions = [[c['index'], c['team'], c['type'], c['gold'], c['gems'], c['kills']] for c in row['champions']]
        if not np.array_equal(rep['final_champions'], np.asarray(champions, np.int64).reshape(-1, 6)):
            problems.append((name, 'final champions differ'))
        if rep['entry'].get('summary_check') != row.get('summary_check'):
            problems.append((name, 'summary check differs'))
        counts = {}
        for kind in rep['actions'][:, 2].tolist():
            counts[kind] = counts.get(kind, 0) + 1
        if sum(counts.values()) != sum(row['counts'].values()):
            problems.append((name, 'action count total differs'))
        if 'turns' in row and row['turns'] is not None:
            if 'turns' not in rep:
                problems.append((name, 'JSONL has turns but shards do not'))
                continue
            turns = np.asarray([[t['round'], t['champion'], t['action_index']] for t in row['turns']], np.int64).reshape(-1, 3)
            if not np.array_equal(rep['turns'], turns):
                problems.append((name, 'turns differ'))
            cooldowns = np.asarray([[-2, -2] if t['view']['cooldowns'] is None else
                                    [-1 if c is None else c for c in t['view']['cooldowns']] for t in row['turns']], np.int64).reshape(-1, 2)
            if not np.array_equal(rep['cooldowns'], cooldowns):
                problems.append((name, 'cooldowns differ'))
            bad = sum(not (np.array_equal(champs, _floats(t['view']['champions'], 10), equal_nan=True) and
                           np.array_equal(camps, _floats(t['view']['camps'], 5), equal_nan=True))
                      for (champs, camps), t in zip(rep['views'], row['turns']))
            if bad or len(rep['views']) != len(row['turns']):
                problems.append((name, f'{bad} turn views differ'))
    failed_jsonl = {n for n, r in rows.items() if not r['ok']}
    if {f['replay'] for f in sidecar_failed} != failed_jsonl:
        problems.append(('*', 'failed replay sets differ'))
    missing = set(rows) - seen - failed_jsonl
    if missing:
        problems.append(('*', f'{len(missing)} JSONL replays missing from shards'))
    report = dict(shards=len(manifest['shards']), replays_in_shards=len(seen), jsonl_rows=len(rows),
                  failed=len(sidecar_failed), bytes=manifest['bytes'], problems=problems[:20], problem_count=len(problems),
                  passed=not problems)
    print(json.dumps(report, indent=1))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='command', required=True)
    v = sub.add_parser('validate')
    v.add_argument('--shards', type=Path, required=True)
    v.add_argument('--jsonl', type=Path, required=True)
    a = p.parse_args()
    if a.command == 'validate' and not validate(a.shards, a.jsonl)['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
