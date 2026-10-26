"""Agent C real-engine capture probe (scratch only; never touches bot/src).

1. Builds artifacts/tmp/C/probe/bot: lead sources + agent C files + archive/agents/C/scripts/nn_obs_probe.cpp, with a patched
   bot.cpp (two nnobs_probe() calls) and nn_config.h switched to NN_ANY_HEAD 1 (all heads still off).
2. Runs the probe vs references/builds/original.wasm on two maps (official CLI, --release, default fuel, <= 2 at once).
3. Parses NOBS/NRAW lines: fuel of capture/encode (typical/p95/worst), C++ fingerprints vs Python re-encode of the
   dumped RawTurns, feature ranges / clipped fractions / NaN counts; writes real fixtures to tests/fixtures/obs/.

Writes agents/C/evidence/probe.json. Usage: python archive/agents/C/scripts/probe.py [--maps a,b] [--rebuild]
"""
from __future__ import annotations

import argparse
import base64
import json
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'python'))
from nfs import engine, obs, schema_gen as S  # noqa: E402

TMP = ROOT / 'artifacts' / 'tmp' / 'C' / 'probe'
C_FILES = ['nn_schema.h', 'nn_obs.h', 'nn_obs.cpp', 'nn_obs_glue.cpp']
FIXTURES = ROOT / 'tests' / 'fixtures' / 'obs'

HOOK_ALIVE_AFTER = '    PROF_CHECK("sight");\n'
HOOK_DEAD_AFTER = '        type = me.champion_name();\n        shop();\n'


def build(rebuild: bool) -> Path:
    wasm = TMP / 'probe.wasm'
    if wasm.exists() and not rebuild:
        return wasm
    src = ROOT / 'bot' / 'src'
    dest = TMP / 'bot' / 'src'
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for p in src.iterdir():
        if p.is_file() and (not p.name.startswith('nn_') or p.name in C_FILES):
            shutil.copy2(p, dest / p.name)
    shutil.copy2(ROOT / 'agents' / 'C' / 'scripts' / 'nn_obs_probe.cpp', dest / 'nn_obs_probe.cpp')
    cfg = (src / 'nn_config.h').read_text(encoding='utf-8').replace('#define NN_ANY_HEAD 0', '#define NN_ANY_HEAD 1')
    assert '#define NN_ANY_HEAD 1' in cfg
    (dest / 'nn_config.h').write_text(cfg, encoding='utf-8', newline='\n')
    bot = (src / 'bot.cpp').read_text(encoding='utf-8')
    assert bot.count(HOOK_ALIVE_AFTER) == 1 and bot.count(HOOK_DEAD_AFTER) == 1
    bot = bot.replace(HOOK_ALIVE_AFTER, HOOK_ALIVE_AFTER + '    nnobs_probe(*this, 1); // SCRATCH PROBE\n')
    bot = bot.replace(HOOK_DEAD_AFTER, '        type = me.champion_name();\n        nnobs_probe(*this, 0); // SCRATCH PROBE\n        shop();\n')
    bot = bot.replace('// ---------------------------------------------------------------- setup',
                      'void nnobs_probe(const Bot& bot, int where); // SCRATCH PROBE\n\n'
                      '// ---------------------------------------------------------------- setup', 1)
    assert bot.count('SCRATCH PROBE') == 3
    (dest / 'bot.cpp').write_text(bot, encoding='utf-8', newline='\n')
    return engine.official_build(TMP / 'bot', wasm)


def parse(text: str) -> dict:
    turns, raws, info = [], [], None
    for line in text.splitlines():
        if line.startswith('NOBSINFO'):
            p = line.split()
            info = {'dim': int(p[2]), 'raw': int(p[4]), 'hash': p[6], 'shared_memory_bytes': int(p[8]),
                    'draft_memory_bytes': int(p[10]), 'meter_overhead': int(p[12])}
        elif line.startswith('NOBS ') and 'nocapture' not in line:
            p = line.split()
            if len(p) == 8:
                turns.append({'round': int(p[1]), 'handle': int(p[2]), 'alive_hook': int(p[3]), 'capture': int(p[4]),
                              'encode': int(p[5]), 'left': int(p[6]), 'hash': p[7]})
        elif line.startswith('NRAW '):
            p = line.split()
            if len(p) == 5:
                raws.append({'round': int(p[1]), 'handle': int(p[2]), 'hash': p[3], 'b64': p[4]})
    return {'info': info, 'turns': turns, 'raws': raws}


def pct(v, q):
    return float(np.percentile(np.asarray(v, dtype=np.float64), q)) if len(v) else None


def fuel_stats(vals: list[int]) -> dict:
    if not vals:
        return {}
    return {'n': len(vals), 'median': pct(vals, 50), 'p95': pct(vals, 95), 'p99': pct(vals, 99), 'max': int(max(vals)),
            'mean': float(np.mean(vals))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--maps', default='01big-world,00gemfight')
    ap.add_argument('--rebuild', action='store_true')
    args = ap.parse_args(argv)
    wasm = build(args.rebuild)
    orig = ROOT / 'references' / 'builds' / 'original.wasm'
    maps = [engine.MAPS / f'{m}.map26a' for m in args.maps.split(',')]
    jobs = []
    for k, mp in enumerate(maps):
        side = 'A' if k % 2 == 0 else 'B'
        a, b = (wasm, orig) if side == 'A' else (orig, wasm)
        jobs.append(dict(a=a, b=b, map_path=mp, folder=TMP / 'matches' / f'{mp.stem}_{side}', candidate_side=side,
                         log_limit=64 * 1048576, timeout=900))
    with ThreadPoolExecutor(max_workers=2) as ex:
        results = list(ex.map(lambda j: engine.run_match(**j), jobs))

    report = {'probe_wasm_sha256': engine.sha256(wasm), 'note': 'scratch probe build (NN_ANY_HEAD 1, all heads off, '
              'capture+encode every turn); gameplay of this build is NOT the original (probe fuel shifts decisions)',
              'matches': [], 'fixtures': []}
    FIXTURES.mkdir(parents=True, exist_ok=True)
    all_X, all_pre = [], []
    for job, res in zip(jobs, results):
        text = engine.team_stdout(job['folder'], job['candidate_side'])
        P = parse(text)
        turns, raws = P['turns'], P['raws']
        alive = [t for t in turns if t['alive_hook'] == 1]
        first = {}
        for t in turns:
            first.setdefault(t['handle'], t)
        steady = [t for t in turns if first[t['handle']] is not t]
        mism, checked = 0, 0
        X = []
        for rw in raws:
            data = base64.b64decode(rw['b64'])
            x = obs.encode(data)
            checked += 1
            if f'{obs.obs_hash(x):08x}' != rw['hash']:
                mism += 1
            X.append(x)
        X = np.stack(X) if X else np.zeros((0, S.OBS_DIM), np.float32)
        all_X.append(X)
        # fixtures: a spread of rounds/champions from this match
        picks = [rw for rw in raws if rw['round'] in (1, 2, 100, 500, 1000, 1500)][:24]
        for rw in picks:
            name = f"{job['map_path'].stem}_{job['candidate_side']}_r{rw['round']}_h{rw['handle']}.json"
            data = base64.b64decode(rw['b64'])
            fx = {'source': 'real engine (official CLI 3.0.5, --release, default fuel), scratch probe build of the original '
                            'with capture+encode each turn', 'map': job['map_path'].stem, 'side': job['candidate_side'],
                  'round': rw['round'], 'handle': rw['handle'], 'schema_hash': f'{S.OBS_SCHEMA_HASH:08x}',
                  'cpp_obs_hash': rw['hash'], 'raw_b64': rw['b64'], 'raw_size': len(data)}
            (FIXTURES / name).write_text(json.dumps(fx, indent=1) + '\n', encoding='utf-8')
            report['fixtures'].append(name)
        report['matches'].append({
            'map': job['map_path'].stem, 'probe_side': job['candidate_side'], 'result': res.row(), 'info': P['info'],
            'turn_lines': len(turns), 'alive_turn_lines': len(alive), 'raw_dumps': len(raws),
            'python_reencode_checked': checked, 'python_hash_mismatches': mism,
            'fuel_capture_all': fuel_stats([t['capture'] for t in turns]),
            'fuel_capture_steady': fuel_stats([t['capture'] for t in steady]),
            'fuel_capture_first_turn': [t['capture'] for t in first.values()],
            'fuel_encode': fuel_stats([t['encode'] for t in turns]),
            'fuel_left_after_probe': fuel_stats([t['left'] for t in alive]),
            'turns_with_less_than_20k_left_after_probe': sum(t['left'] < 20000 for t in alive),
        })
    X = np.concatenate(all_X) if all_X else np.zeros((0, S.OBS_DIM), np.float32)
    names = obs.feature_names()
    lo = np.concatenate([obs.SG_LO] + [obs.ALLY_LO] * S.ALLY_ROWS + [np.zeros(S.ALLY_ROWS, np.float32)] +
                        [obs.ENEMY_LO] * S.ENEMY_ROWS + [np.zeros(S.ENEMY_ROWS, np.float32)])
    hi = np.concatenate([obs.SG_HI] + [obs.ALLY_HI] * S.ALLY_ROWS + [np.ones(S.ALLY_ROWS, np.float32)] +
                        [obs.ENEMY_HI] * S.ENEMY_ROWS + [np.ones(S.ENEMY_ROWS, np.float32)])
    at_bound = ((X == lo) & (lo != 0)) | ((X == hi) & (hi != 1) & (hi != 0))
    stats = []
    for k in range(S.OBS_DIM):
        col = X[:, k]
        stats.append({'name': names[k], 'min': float(col.min()) if len(col) else None, 'max': float(col.max()) if len(col) else None,
                      'mean': float(col.mean()) if len(col) else None, 'nonzero_frac': float((col != 0).mean()) if len(col) else None,
                      'at_clip_bound_frac': float(at_bound[:, k].mean()) if len(col) else None})
    report['features'] = {'samples': int(len(X)), 'nan_or_inf': int((~np.isfinite(X)).sum()),
                          'never_nonzero': [s['name'] for s in stats if s['nonzero_frac'] == 0.0 and 'mask' not in s['name']],
                          'often_clipped': [s for s in stats if (s['at_clip_bound_frac'] or 0) > 0.05],
                          'per_feature': stats}
    engine.write_json(ROOT / 'agents' / 'C' / 'evidence' / 'probe.json', report)
    for m in report['matches']:
        print(m['map'], m['probe_side'], m['result']['outcome'], 'turns', m['turn_lines'], 'raws', m['raw_dumps'],
              'mismatch', m['python_hash_mismatches'], 'capture', m['fuel_capture_steady'], 'first', m['fuel_capture_first_turn'],
              'encode', m['fuel_encode'], 'info', m['info'])
    print('features samples', report['features']['samples'], 'nan', report['features']['nan_or_inf'], 'never_nonzero',
          len(report['features']['never_nonzero']), 'often_clipped', [s['name'] for s in report['features']['often_clipped']])
    return 0


if __name__ == '__main__':
    sys.exit(main())
