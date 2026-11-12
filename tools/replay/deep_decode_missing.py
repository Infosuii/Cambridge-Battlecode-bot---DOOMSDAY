"""Decode only new downloaded pairs, then reconcile the complete local study set.

The prior JSONL is local-only and must have been produced by the same pinned
decoder. Existing decoded rows are carried forward without reviewing trajectories.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from deep_preflight import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node', required=True)
    parser.add_argument('--prior', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    work = ROOT / 'artifacts/local-only/deep-2026-10-28'
    combined = work / 'decoded.jsonl'
    extra = work / 'remaining-decoded.jsonl'
    if args.prior.resolve() in (combined.resolve(), extra.resolve()):
        raise ValueError('Prior input must be separate from output files; preserve it under a distinct name')
    report = ROOT / 'research/deep-2026-10-28/DOWNLOADS.json'
    downloads = json.loads(report.read_text(encoding='utf-8'))['games']
    seen = set()
    with args.prior.open() as source:
        for line in source:
            row = json.loads(line)
            if not row.get('ok') or not row.get('summary_check', {}).get('passed'):
                raise ValueError('Prior decode contains a failure')
            mid = Path(row['replay']).stem
            if mid in seen:
                raise ValueError('Duplicate prior replay')
            seen.add(mid)
    missing = [r['replay_path'] for r in downloads if r['match_id'] not in seen]
    env = dict(os.environ, NFS_REPLAY_ENGINE='2.0.0')
    if missing:
        subprocess.run([args.node, '--no-warnings', 'tools/replay/decode_replays.mjs',
                        '--workers', str(args.workers), '--out', str(extra.relative_to(ROOT)),
                        *missing], cwd=ROOT, env=env, check=True)
    with combined.open('wb') as target:
        for path in [args.prior, *([extra] if missing else [])]:
            with path.open('rb') as source:
                while chunk := source.read(1024 * 1024):
                    target.write(chunk)
    print(json.dumps({'prior_decodes_retained': len(seen), 'new_decodes': len(missing)}), flush=True)
    subprocess.run([sys.executable, 'tools/replay/deep_reconcile.py', str(combined)], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
