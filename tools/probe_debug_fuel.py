"""Probe: is a debug (CAMBC_DEBUG) build of the unchanged original fuel-equivalent to its release build?

If debug_block is fuel-neutral, a debug build should play exactly the same games as the release build. That would let
training collection log inside debug_block at zero fuel cost (training/deployment parity). Bounded: a few maps.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from nfs import engine  # noqa: E402

import subprocess


def run(a, b, m, out, release):
    out.mkdir(parents=True, exist_ok=True)
    args = [engine.CLI, 'run', a, b, '--map', m, '--out-dir', out, '--statistics', out / 's.json', '--json',
            '--log-limit', '16777216']
    if release:
        args.append('--release')
    r = subprocess.run([str(x) for x in args], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        return dict(error=(r.stdout + r.stderr)[-400:])
    d = json.loads((out / 's.json').read_text(encoding='utf-8'))
    return dict(outcome=d['match']['outcome'], rounds=d['match']['roundsStarted'],
                gems={t['team']: t['submittedGems'] for t in d['teams']},
                deaths=[c['metrics']['deaths'] for c in d['champions']])


def main():
    D = engine.ROOT / 'artifacts/tmp/debugprobe'
    rel = engine.ROOT / 'references/builds/original.wasm'
    dbg = D / 'debug.wasm'
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    rows = []
    for m in engine.maps()[:n]:
        base = run(rel, rel, m, D / f'{m.stem}-rel', True)
        cases = {'debugA_norel': run(dbg, rel, m, D / f'{m.stem}-dA', False),
                 'debugB_norel': run(rel, dbg, m, D / f'{m.stem}-dB', False),
                 'release_norel': run(rel, rel, m, D / f'{m.stem}-rn', False),
                 'debugA_rel': run(dbg, rel, m, D / f'{m.stem}-dAr', True)}
        row = dict(map=m.stem, release=base, **{k: dict(v, same=(v == base)) for k, v in cases.items()})
        rows.append(row)
        print(json.dumps({'map': m.stem, **{k: v.get('same', v.get('error')) for k, v in row.items() if isinstance(v, dict) and k != 'release'}}), flush=True)
    engine.write_json(D / 'result.json', rows)


if __name__ == '__main__':
    main()
