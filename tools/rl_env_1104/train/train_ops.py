"""Local-only training operations; build before parallel games; persist evidence."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT.parent
V4 = ROOT / 'v4'
CLI = Path(os.environ['TRAIN_CLI']) if os.environ.get('TRAIN_CLI') else V4 / ('cambc.exe' if os.name == 'nt' else 'cambc')
INITIAL = Path(os.environ.get('TRAIN_INITIAL', BASE / 'reference/nn-rl6-original/nn_rl6/student_10.pt'))
CRITIC = Path(os.environ.get('TRAIN_CRITIC', BASE / 'reference/nn-rl6-original/nn_rl6/value_10.pt'))
JOBS = int(os.environ.get('TRAIN_JOBS', '4'))
PILOT = os.environ.get('TRAIN_PILOT') == '1'
RUN = os.environ.get('TRAIN_RUN', 'pilot' if PILOT else 'v111-continuation')
EVAL_MAP_DIR = os.environ.get('TRAIN_EVAL_MAPS','maps_dev')
NATIVE_RESIDUAL = os.environ.get('TRAIN_NATIVE_RESIDUAL')=='1'
PREFIX = os.environ.get('TRAIN_BOT_PREFIX','')
LOG_KEEP = 1 if NATIVE_RESIDUAL else 10
LOG_LIMIT = 134217728 if NATIVE_RESIDUAL else 67108864
STOP = ROOT / 'STOP'


def emit(msg):
    print(time.strftime('%H:%M:%S'), msg, flush=True)


def check_stop():
    if STOP.exists():
        raise SystemExit('Stopped by request; saved checkpoints retained.')


def atomic_json(path, obj):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2), encoding='utf-8')
    tmp.replace(path)


def bot_name(name):
    return PREFIX+name if name in ('nnrq','nnrq_eval','nnqsnap') else name

def wasm(name, debug):
    name=bot_name(name)
    folder = V4 / 'bots' / name / '.cambc' / ('build' if debug else 'build-release')
    return str(folder / 'bot-injected.wasm')


def compile_bot(name, debug=False):
    check_stop()
    name=bot_name(name)
    cmd = [str(CLI), 'build', f'bots/{name}'] + ([] if debug else ['--release'])
    r = subprocess.run(cmd, cwd=V4, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300)
    logs = ROOT / 'build-logs'
    logs.mkdir(exist_ok=True)
    (logs / f'{name}-{"debug" if debug else "release"}.txt').write_text(r.stdout + r.stderr, encoding='utf-8')
    if r.returncode or not Path(wasm(name, debug)).exists():
        raise RuntimeError(f'Build failed {name}: {(r.stdout+r.stderr)[-1500:]}')


def make_bot(name, source, weights=None, overrides=None):
    name=bot_name(name)
    src = V4 / 'bots' / name / 'src'
    if not src.exists():
        shutil.copytree(V4 / 'bots' / source / 'src', src)
        common = src / 'common.h'
        prefix = ''.join(f'#define {k} {v}\n' for k, v in (overrides or {}).items())
        common.write_text(prefix + common.read_text(encoding='utf-8'), encoding='utf-8', newline='\n')
    if weights:
        shutil.copy2(weights, src / 'nn_weights.h')


def build(name, weights, rl):
    overrides = {'A2_NN_RLIVE': '1', 'A2_NN_RL_KEEP': str(LOG_KEEP)} if rl else {}
    make_bot(name, os.environ.get('TRAIN_BASE', 'v111'), weights, overrides)
    if rl and NATIVE_RESIDUAL:
        common=(V4/'bots'/bot_name(name)/'src/common.h').read_text(encoding='utf-8')
        if not common.startswith('#define A2_NN_RLIVE 1\n#define A2_NN_RL_KEEP 1\n'):
            raise RuntimeError('Native training collector configuration mismatch; use a fresh isolated bot prefix')
        p=V4/'bots'/bot_name(name)/'src/nnrec.cpp'
        text=p.read_text(encoding='utf-8')
        marker='// Native behaviour logits for anchored quantized-policy updates.'
        if marker not in text:
            needle='            std::printf("NRL %d %d %d %.5f %d %d %d %s\\n", round, slot, a, lp, chg ? 1 : 0, nn_zid, bs, b64(xn, kNF).c_str());'
            assert text.count(needle)==1
            new='''            // Native behaviour logits for anchored quantized-policy updates.
            std::printf("NRQ %d %u %s\\n", round, my_id,
                b64(reinterpret_cast<const std::int16_t*>(v),2*(kC+1)).c_str());
'''+needle
            p.write_text(text.replace(needle,new),encoding='utf-8')
    compile_bot(name, debug=False)
    if rl:
        compile_bot(name, debug=True)


def prepare_opponents():
    for name, seed in [('nnm4n1', 1), ('nnm4n2', 2)]:
        make_bot(name, 'nnm4', overrides={'A2_NN_LJIT': str(seed), 'A2_NN_LJIT_A': '0.1'})
    for name in ('nnm4', 'nnm4n1', 'nnm4n2', 'v92', 'v111'):
        compile_bot(name)
        compile_bot(name, debug=True)


def play(lines, tag, debug):
    check_stop()
    import psutil
    if psutil.virtual_memory().available < float(os.environ.get('TRAIN_MIN_FREE_GB', '2')) * 1024**3:
        raise RuntimeError('Low free RAM; checkpoint preserved, training paused.')
    out = V4 / tag
    out.mkdir(parents=True, exist_ok=True)
    (out / 'manifest.txt').write_text('\n'.join(lines) + '\n')
    assets={}
    for line in lines:
        q=shlex.split(line)
        for path in (Path(wasm(Path(q[0]).name,debug)),Path(wasm(Path(q[1]).name,debug)),V4/q[2]):
            assets[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
    atomic_json(out/'runtime-identity.json',{'cli_sha256':hashlib.sha256(CLI.read_bytes()).hexdigest(),
        'engine':'3.0.0','debug':debug,'native_residual':NATIVE_RESIDUAL,'log_keep':LOG_KEEP,'assets':assets})
    def game(line):
        check_stop()
        q = shlex.split(line)
        a, b = Path(q[0]).name, Path(q[1]).name
        output = V4 / q[3]
        summary = V4 / q[q.index('--statistics') + 1]
        # Every guest is compiled once before workers launch. No shared build races.
        cmd = [str(CLI), 'run', wasm(a, debug), wasm(b, debug), '--map', str(V4 / q[2]),
               '-o', str(output), '--statistics', str(summary), '--json', '--log-limit', str(LOG_LIMIT)]
        if not debug:
            cmd += ['--release']
        with open(output.with_suffix('.runner.log'), 'w', encoding='utf-8') as log:
            p = subprocess.Popen(cmd, cwd=V4, stdout=log, stderr=subprocess.STDOUT)
            start = time.monotonic()
            while p.poll() is None:
                if STOP.exists() or time.monotonic() - start > 1200 or psutil.virtual_memory().available < float(os.environ.get('TRAIN_GAME_MIN_FREE_GB', '1')) * 1024**3:
                    proc = psutil.Process(p.pid)
                    for child in proc.children(recursive=True):
                        child.kill()
                    p.kill()
                    p.wait()
                    raise RuntimeError('Game stopped: stop request, timeout or low RAM; inspect runner log.')
                time.sleep(0.5)
        if p.returncode or not summary.exists() or not output.exists():
            raise RuntimeError(f'Game failed: {output}; inspect {output.with_suffix(".runner.log")}')
        data = json.loads(summary.read_text(encoding='utf-8'))
        if data['match'].get('engineVersion') != '3.0.0' or data['match'].get('outcome') not in ('teamA', 'teamB', 'draw'):
            raise RuntimeError('Unfinished game or wrong engine: ' + str(summary))
        if any(data['diagnostics']['botFaults'].values()) or not data['diagnostics']['detailedCaptureComplete']:
            raise RuntimeError('Faulted or incomplete training/evaluation game: '+str(summary))
        return summary
    done = 0
    with ThreadPoolExecutor(max_workers=JOBS) as pool:
        for future in as_completed([pool.submit(game, line) for line in lines]):
            future.result()
            done += 1
            if done % 8 == 0 or done == len(lines):
                emit(f'{tag}: {done}/{len(lines)} games complete')
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=sha for p,sha in assets.items()):
        raise RuntimeError('Runtime/map artifact changed during the batch')


def prepare_batch(tag):
    path = (V4 / tag).resolve()
    allowed = (V4 / 'bench_out').resolve()
    if not path.is_relative_to(allowed) or path == allowed:
        raise ValueError('Batch path outside this experiment')
    if path.exists():
        dest = path.with_name(path.name + '-attempt-' + str(time.time_ns())).resolve()
        if not dest.is_relative_to(allowed):
            raise ValueError('Attempt path outside this experiment')
        path.rename(dest)


def replay_stdout(path, side):
    import zipfile
    path = Path(path)
    if path.is_dir():
        bundles = list(path.glob('*.repl26a'))
        if len(bundles) != 1:
            raise RuntimeError(f'Expected one replay bundle in {path}, found {len(bundles)}')
        path = bundles[0]
    with zipfile.ZipFile(path) as archive:
        raw=archive.read(f'team-{side.lower()}.stdout')
        if len(raw)>=LOG_LIMIT-8192:raise RuntimeError('Possible capped training log')
        # Guest output chunks contain zero padding. Removing it can concatenate
        # an NRL record with the next P/M record and silently lose the decision.
        return raw.replace(b'\0', b'\n').decode('utf-8', 'strict')


def evaluate(it, weights):
    name = 'nnrq_eval'
    build(name, weights, False)
    maps = sorted((V4 / EVAL_MAP_DIR).glob('*.map26a'))
    if PILOT:
        maps = maps[:2]
    # Explicit per-opponent reports; compare later against the same baseline cells.
    jobs, lines = [], []
    tag = f'bench_out/{RUN}/eval{it}'
    opponents=tuple(os.environ['TRAIN_EVAL_OPP'].split(',')) if os.environ.get('TRAIN_EVAL_OPP') else ('v111','nnm4','v92','ref_x1','ref_x3ctr','ref_p65pack') if os.environ.get('TRAIN_BROAD')=='1' else ('v111','nnm4','v92')
    for opponent in opponents:
        for mapfile in maps:
            for side in ('A', 'B'):
                a, b = (name, opponent) if side == 'A' else (opponent, name)
                f = f'{tag}/{opponent}_{mapfile.stem}_{side}'
                lines.append(f'bots/{a} bots/{b} {EVAL_MAP_DIR}/{mapfile.name} {f}.repl26a --statistics {f}.json --json')
                jobs.append((opponent, side, V4 / (f + '.json')))
    play(lines, tag, False)
    scores = {}
    for opponent, side, path in jobs:
        data = json.loads(path.read_text())
        win = data['match']['outcome']
        score = 1 if win == 'team'+side else 0.5 if win == 'draw' else 0
        entry = scores.setdefault(opponent, {'score': 0.0, 'n': 0})
        entry['score'] += score
        entry['n'] += 1
    score = sum(v['score'] for v in scores.values()) / len(jobs)
    raw=score
    if os.environ.get('TRAIN_BROAD')=='1':
        baseline=V4/'bench_out'/RUN/'eval0/report.json'
        if it and baseline.exists():
            old=json.loads(baseline.read_text())['opponents']
            worst=min(scores[o]['score']/scores[o]['n']-old[o]['score']/old[o]['n'] for o in opponents)
            direct=scores[opponents[0]]['score']/scores[opponents[0]]['n']
            # A pooled checkpoint gain must not hide direct champion or large
            # individual-opponent regressions. This remains selection, not proof.
            score-=max(0.,.5-direct)+max(0.,-worst-1/12)
    atomic_json(V4 / tag / 'report.json', {'iter': it, 'opponents': scores, 'selection_score': score, 'raw_score':raw,
                                         'purpose': 'development selection only, not promotion evidence'})
    emit(f'EVAL iter {it}: {score:.1%}; {scores}')
    return score


def initialize_run(wd, initial, value):
    import torch
    check_stop()
    if not torch.cuda.is_available() and os.environ.get('TRAIN_CPU') != '1':
        raise RuntimeError('CUDA unavailable; refusing to silently start slow CPU training.')
    if (Path(wd)/'state.json').exists():
        previous=json.loads((Path(wd)/'run.json').read_text())
        if previous.get('reward_profile','legacy_dense')!=os.environ.get('TRAIN_REWARD','legacy_dense'):
            raise RuntimeError('Cannot resume a checkpoint under a different reward objective')
    if not (Path(wd) / 'state.json').exists():
        if os.environ.get('TRAIN_FRESH_CRITIC')!='1':
            value.load_state_dict(torch.load(CRITIC, map_location='cuda' if torch.cuda.is_available() else 'cpu', weights_only=True))
        atomic_json(Path(wd) / 'run.json', {'initial': str(initial), 'original_v111': str(INITIAL),
                                          'start': datetime.now(timezone.utc).isoformat(),
                                          'torch': torch.__version__, 'gpu': torch.cuda.get_device_name() if torch.cuda.is_available() else 'cpu',
                                          'fresh_optimizer': True, 'pilot': PILOT,
                                          'reward_profile':os.environ.get('TRAIN_REWARD','legacy_dense'),
                                          'fresh_critic':os.environ.get('TRAIN_FRESH_CRITIC')=='1',
                                          'native_residual':NATIVE_RESIDUAL,'deploy_q11':os.environ.get('NN_DEPLOY_PREP')=='1',
                                          'bot_prefix':PREFIX,'evaluation_maps':EVAL_MAP_DIR,
                                          'train_mapsets':os.environ.get('TRAIN_MAPSETS'),
                                          'trainer_sha256':hashlib.sha256((Path(__file__).parent/'train.py').read_bytes()).hexdigest(),
                                          'model_sha256':hashlib.sha256((Path(__file__).parent/'nn_model.py').read_bytes()).hexdigest()})


def validate_batch(wd, it, x, xz, action, logp, diff):
    import torch
    if len(x) < 100 or not torch.isfinite(logp).all() or not torch.isfinite(diff).all():
        raise RuntimeError('Missing or invalid policy data')
    if action.min() < 0 or action.max() > 10:
        raise RuntimeError('Invalid target index')
    report = {'iter': it, 'rows': len(x), 'logp_median': diff.median().item(),
              'logp_p90': diff.quantile(.9).item(), 'logp_max': diff.max().item()}
    atomic_json(Path(wd) / f'batch_{it}.json', report)
    # Existing Q16 actor differs slightly from floating training model. Bound the
    # discrepancy and preserve actual logged behaviour probabilities for PPO.
    if report['logp_median'] > .05 or report['logp_p90'] > .25:
        raise RuntimeError(f'Actor/trainer probability mismatch: {report}; investigate before training')
    emit('Validated batch: ' + str(report))


def save_resume(wd, it, best, optimizer):
    import torch
    import random
    import numpy as np
    wd = Path(wd)
    torch.save({'optimizer': optimizer.state_dict(), 'torch_rng': torch.get_rng_state(),
                'cuda_rng': torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [], 'python_rng': random.getstate(),
                'numpy_rng': {'name': np.random.get_state()[0], 'keys': torch.as_tensor(np.random.get_state()[1].astype('int64')),
                              'pos': np.random.get_state()[2], 'gauss': np.random.get_state()[3],
                              'cached': np.random.get_state()[4]}}, wd / f'resume_{it}.pt')
    atomic_json(wd / 'state.json', {'iter': it, 'best': best})


def restore_optimizer(wd, optimizer, device):
    import torch
    import random
    import numpy as np
    wd = Path(wd)
    it = json.loads((wd / 'state.json').read_text())['iter']
    path = wd / f'resume_{it}.pt'
    if path.exists():
        data = torch.load(path, map_location='cpu', weights_only=True)
        optimizer.load_state_dict(data['optimizer'])
        torch.set_rng_state(data['torch_rng'])
        if torch.cuda.is_available() and data['cuda_rng']: torch.cuda.set_rng_state_all(data['cuda_rng'])
        random.setstate(data['python_rng'])
        r = data['numpy_rng']
        np.random.set_state((r['name'], r['keys'].numpy().astype('uint32'), r['pos'], r['gauss'], r['cached']))
