"""Overall-win-rate screen: candidate vs baseline on the 120-map suite, both sides, several build seeds.

Usage: python tools/lab/screen120.py --name EXP --cand bots/v75[:DEF=V;DEF=V] --base bots/v74h[:...] [--seeds 1 2 3]
       [--maps maps/local-benchmarks maps/generated/dev maps/generated/holdout] [--workers 8]

Each bot spec is a source folder plus optional #define overrides (replacing the first existing definition in
src/common.h, else prepended). NOVA_SEED is set per seed for both bots, as bench3 does. Builds are release builds with
the official CLI (nfs.engine.official_build), cached by content hash under artifacts/tmp/screen-builds. Games run through
tools/mapgen/profile_maps.py. Writes artifacts/evaluations/<EXP>/summary.json and prints overall wins, gem margin and
map-clustered bootstrap 95% intervals (unit = map, all its sides and seeds together).
"""
import argparse
import hashlib
import json
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'python'))
from nfs import engine  # noqa: E402

PY = sys.executable
BUILD = ROOT / 'artifacts/tmp/screen-builds'


def spec_parts(spec):
    path, _, defs = spec.partition(':')
    return Path(path), [d.split('=', 1) for d in defs.split(';') if d]


def build(spec, seed):
    src_dir, defs = spec_parts(spec)
    defs = [d for d in defs if d[0] != 'NOVA_SEED'] + [['NOVA_SEED', str(seed)]]
    h = hashlib.sha256()
    for f in sorted((src_dir / 'src').iterdir()):
        h.update(f.name.encode() + f.read_bytes())
    h.update(repr(defs).encode())
    key = h.hexdigest()[:12]
    wasm = BUILD / f'{src_dir.name}-{key}.wasm'
    if wasm.exists():
        return wasm
    work = BUILD / f'{src_dir.name}-{key}'
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(src_dir / 'src', work / 'src')
    common = work / 'src/common.h'
    text = common.read_text(encoding='utf-8')
    head = ''
    for k, v in defs:
        pat = re.compile(rf'^#define {re.escape(k)}\b.*$', re.M)
        if pat.search(text):
            text = pat.sub(lambda _m: f'#define {k} {v}', text, count=1)
        else:
            head += f'#define {k} {v}\n'
    common.write_text(head + text, encoding='utf-8')
    engine.official_build(work, wasm)
    return wasm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True)
    ap.add_argument('--cand', required=True)
    ap.add_argument('--base', required=True)
    ap.add_argument('--seeds', type=int, nargs='+', default=[1, 2, 3])
    ap.add_argument('--maps', nargs='+', default=['maps/local-benchmarks', 'maps/generated/dev', 'maps/generated/holdout'])
    ap.add_argument('--workers', type=int, default=8)
    a = ap.parse_args()
    out = ROOT / 'artifacts/evaluations' / a.name
    out.mkdir(parents=True, exist_ok=True)
    games = []
    for s in a.seeds:
        wc, wb = build(a.cand, s), build(a.base, s)
        sub = out / f'seed{s}'
        subprocess.run([PY, str(ROOT / 'tools/mapgen/profile_maps.py'), '--a', str(wc), '--b', str(wb), '--maps',
                        *[str(ROOT / m) for m in a.maps], '--out', str(sub), '--workers', str(a.workers)], check=True)
        for g in json.loads((sub / 'profile.json').read_text(encoding='utf-8'))['games']:
            g['seed'] = s
            games.append(g)
    ok = [g for g in games if 'error' not in g]
    by = {}
    for g in ok:
        by.setdefault(g['map'], []).append(g)
    units = [(sum(g['win'] for g in v), sum(g['gems'] - g['opponent_gems'] for g in v), len(v)) for v in by.values()]
    rng = random.Random(1)

    def boot(i):
        vals = []
        for _ in range(4000):
            pick = [units[rng.randrange(len(units))] for _ in units]
            vals.append(sum(u[i] for u in pick) / sum(u[2] for u in pick))
        vals.sort()
        return [round(vals[99], 4), round(vals[3899], 4)]

    n = len(ok)
    res = {'exp': a.name, 'cand': a.cand, 'base': a.base, 'seeds': a.seeds, 'maps': len(by), 'games': n,
           'errors': len(games) - n, 'wins': sum(g['win'] for g in ok), 'win_rate': round(sum(g['win'] for g in ok) / n, 4),
           'win_ci95': boot(0), 'gem_margin': round(sum(g['gems'] - g['opponent_gems'] for g in ok) / n, 1),
           'margin_ci95': boot(1), 'cand_faults': sum(g['faults'] for g in ok),
           'fuel_outs': [sum(g['fuel_exhausted'] for g in ok), sum(g['opponent_fuel_exhausted'] for g in ok)],
           'deaths': [sum(g['deaths'] for g in ok)]}
    (out / 'summary.json').write_text(json.dumps(res, indent=1), encoding='utf-8')
    print(json.dumps(res))


if __name__ == '__main__':
    main()
