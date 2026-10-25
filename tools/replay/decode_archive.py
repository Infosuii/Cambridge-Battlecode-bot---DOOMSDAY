"""Decode whole platform replay archives into compact shards, one part at a time (the archives are only read).

For each replays-<date>-part<N>.zip: extract members to a scratch folder under artifacts/tmp as
`p<N>_<kind>_<match id>.repl26a` (full match id; short names collide at this scale), run decode_replays.mjs
--format npz into <out>/part<N>, write <out>/part<N>/index.json (file -> member name, kind, match id, the two team ids
in member-name order), then delete the scratch copies. A part whose shard directory already has a manifest is skipped,
so an interrupted run can simply be restarted. Progress lines go to stdout as JSON.

    python tools/replay/decode_archive.py --replays <folder with zips> --out artifacts/local-only/replays-<date> [--workers N]
"""
import argparse
import json
import re
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UUID = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
MEMBER = re.compile(rf'^(?:.*/)?(?P<kind>[a-z]+)_(?P<match>{UUID})_(?P<t1>{UUID})_vs_(?P<t2>{UUID})\.repl26a$')


def log(**fields):
    print(json.dumps(dict(time=time.strftime('%Y-%m-%dT%H:%M:%S'), **fields)), flush=True)


def decode_part(archive, out, workers, shard_size):
    part = int(re.search(r'part(\d+)', archive.name)[1])
    dest = out / f'part{part}'
    if (dest / 'manifest.json').exists():
        return log(event='part_skipped', part=part, reason='manifest exists')
    if dest.exists():
        raise SystemExit(f'{dest} exists without a manifest (interrupted run); remove it to redo part {part}')
    scratch = ROOT / 'artifacts/tmp/replay_extract' / f'part{part}'
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True)
    t0 = time.time()
    index, skipped = {}, []
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            m = MEMBER.match(info.filename)
            if not m:
                skipped.append(info.filename)
                continue
            name = f'p{part}_{m["kind"]}_{m["match"]}.repl26a'
            if name in index:
                raise SystemExit(f'duplicate match id in part {part}: {m["match"]}')
            (scratch / name).write_bytes(z.read(info))
            index[name] = dict(member=info.filename, kind=m['kind'], match_id=m['match'], team_ids=[m['t1'], m['t2']])
    log(event='part_extracted', part=part, replays=len(index), skipped=len(skipped), seconds=round(time.time() - t0))
    result = subprocess.run(['node', '--no-warnings', str(ROOT / 'tools/replay/decode_replays.mjs'), '--format', 'npz',
                             '--workers', str(workers), '--shard-size', str(shard_size), '--out', str(dest), str(scratch)],
                            capture_output=True, text=True)
    summary = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ''
    if not (dest / 'manifest.json').exists():
        raise SystemExit(f'decoder did not finish part {part}: {result.stderr[-2000:]}')
    (dest / 'index.json').write_text(json.dumps(dict(archive=str(archive), team_id_order='member name order; A/B mapping unverified',
                                                     skipped_members=skipped, replays=index)) + '\n', encoding='utf-8')
    shutil.rmtree(scratch)
    log(event='part_decoded', part=part, decoder=json.loads(summary) if summary.startswith('{') else summary,
        exit_code=result.returncode, seconds=round(time.time() - t0))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--replays', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--workers', type=int, default=18)
    p.add_argument('--shard-size', type=int, default=256)
    a = p.parse_args()
    out = a.out.resolve()
    if not out.is_relative_to(ROOT / 'artifacts'):
        raise SystemExit('output must be inside artifacts/')
    out.mkdir(parents=True, exist_ok=True)
    archives = sorted(a.replays.glob('replays-*-part*.zip'), key=lambda f: int(re.search(r'part(\d+)', f.name)[1]))
    log(event='start', archives=[f.name for f in archives], out=str(out), workers=a.workers)
    for archive in archives:
        decode_part(archive, out, a.workers, a.shard_size)
    log(event='complete')


if __name__ == '__main__':
    main()
