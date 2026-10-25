"""Independent supervisor for a long policy_bc.py run: 15-minute status snapshots and checkpoint game evaluations.

    python tools/train_supervisor.py --run artifacts/runs/<run> --minutes 150 [--snapshot-minutes 15]
           [--previous <export> ...] [--maps ...] [--games 24]

Runs as its own process (start it detached), so snapshots keep being written if the chat session disconnects. Each
snapshot (`<run>/supervisor/snapshot-NN.json`, also appended to `<run>/supervisor/STATUS.md`) records wall time,
training progress from metrics.jsonl, per-head validation accuracy, throughput, GPU utilisation/VRAM/temperature/power
from nvidia-smi and every evaluation so far. Each new periodic export is evaluated with `policy_ops.py compare` against
the frozen heuristic-v1 baseline and the given previous models (one evaluation at a time, never blocking snapshots).
After training stops (report.json appears) the final export is evaluated and a final snapshot is written. Nothing is
promoted, activated or submitted.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
MAPS = ['00collision', '00contest', '00elkring', '00fragment', '00lost-world', '00quadrants']


def gpu():
    try:
        q = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw',
                            '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=20).stdout.strip().split(', ')
        return dict(util_percent=float(q[0]), vram_used_mib=float(q[1]), vram_total_mib=float(q[2]), temperature_c=float(q[3]), power_w=float(q[4]))
    except Exception as error:  # nvidia-smi missing or busy: record, never fail the supervisor
        return dict(error=str(error)[:200])


def training(run):
    events = []
    path = run / 'metrics.jsonl'
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            try: events.append(json.loads(line))
            except json.JSONDecodeError: pass
    start = next((e for e in events if e['event'] == 'start'), None)
    epochs = [e for e in events if e['event'] == 'epoch']
    last = epochs[-1] if epochs else None
    best = min(epochs, key=lambda e: e['validation']['loss']) if epochs else None
    return dict(train_rows=start and start['train_rows'], validation_rows=start and start['validation_rows'],
                epochs=len(epochs), updates=last and last['updates'], elapsed_seconds=last and round(last['elapsed_seconds']),
                samples_per_second=last and round(last['samples_per_second']), train_loss=last and round(last['train_loss'], 4),
                validation_loss=last and round(last['validation']['loss'], 4),
                validation_accuracy=last and {h: round(v['accuracy'], 3) for h, v in last['validation']['heads'].items()},
                best_epoch=best and best['epoch'], best_validation_loss=best and round(best['validation']['loss'], 4),
                exports=sorted(p.name for p in (run / 'exports').glob('epoch-*')) if (run / 'exports').exists() else [],
                stopped=next((e for e in events if e['event'] == 'stop'), None))


def summary(path):
    try:
        r = json.loads((path / 'comparison.json').read_text(encoding='utf-8'))
        return dict(implementation_passed=r.get('implementation_passed'),
                    **{k: dict(games=v['games'], win_rate=round(v['win_rate'], 3), mean_gem_margin=round(v['mean_gem_margin'], 1),
                               fuel_exhausted=v['fuel_exhausted'], bot_faults=v['bot_faults']) for k, v in r['summary'].items()})
    except Exception as error:
        return dict(error=str(error)[:300])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--run', type=Path, required=True); p.add_argument('--minutes', type=float, required=True)
    p.add_argument('--snapshot-minutes', type=float, default=15); p.add_argument('--previous', type=Path, nargs='*', default=[])
    p.add_argument('--maps', nargs='+', default=MAPS); p.add_argument('--games', type=int, default=24)
    a = p.parse_args()
    run = a.run.resolve(); sup = run / 'supervisor'; sup.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONPATH=str(ROOT / 'python'), TMP=str(ROOT / 'artifacts/tmp'), TEMP=str(ROOT / 'artifacts/tmp'),
               PYTHONDONTWRITEBYTECODE='1', PATH='C:/msys64/ucrt64/bin;' + os.environ.get('PATH', ''))
    start = time.time(); next_snapshot = start; n = 0
    evaluations, queue, running, final_done = {}, [], None, False

    def launch(export, label):
        out = sup / 'evaluations' / label
        cmd = [PY, str(ROOT / 'tools/policy_ops.py'), 'compare', '--candidate', str(export), '--previous', *map(str, a.previous),
               '--maps', *a.maps, '--max-games', str(a.games), '--max-seconds', '1700', '--out', str(out)]
        log = open(sup / f'{label}.log', 'w', encoding='utf-8')
        evaluations[label] = dict(export=str(export), started=time.strftime('%H:%M:%S'), status='running')
        return subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env, cwd=ROOT), label, out

    while True:
        state = training(run)
        for name in state['exports']:
            if name not in evaluations and name not in queue: queue.append(name)
        if running and running[0].poll() is not None:
            proc, label, out = running
            evaluations[label].update(status='done', finished=time.strftime('%H:%M:%S'), exit_code=proc.returncode, result=summary(out))
            running = None
        stopped = state['stopped'] is not None and (run / 'report.json').exists()
        if running is None:
            if stopped and not final_done and (run / 'export').exists():
                running = launch(run / 'export', 'final'); final_done = True; queue.clear()
            elif queue and not stopped:
                name = queue.pop()  # newest first; older pending exports are superseded
                queue.clear(); running = launch(run / 'exports' / name, name)
        finished = final_done and running is None
        if time.time() >= next_snapshot or finished:
            n += 1
            snap = dict(snapshot=n, wall_time=time.strftime('%Y-%m-%d %H:%M:%S'), minutes_since_start=round((time.time() - start) / 60, 1),
                        planned_minutes=a.minutes, training=state, gpu=gpu(), evaluations=evaluations, final=finished)
            (sup / f'snapshot-{n:02d}.json').write_text(json.dumps(snap, indent=1) + '\n', encoding='utf-8')
            line = (f"| {snap['wall_time']} | {snap['minutes_since_start']} | epochs {state['epochs']} | updates {state['updates']} | "
                    f"val loss {state['validation_loss']} | acc {state['validation_accuracy']} | gpu {snap['gpu']} | "
                    f"evals {json.dumps({k: v.get('result', v['status']) for k, v in evaluations.items()})} |\n")
            with (sup / 'STATUS.md').open('a', encoding='utf-8') as f: f.write(line)
            next_snapshot += a.snapshot_minutes * 60
        if finished:
            break
        if time.time() > start + (a.minutes + 120) * 60:  # hard stop: training deadline plus evaluation grace
            with (sup / 'STATUS.md').open('a', encoding='utf-8') as f: f.write('| supervisor hard stop: deadline plus grace exceeded |\n')
            break
        time.sleep(20)


if __name__ == '__main__':
    main()
