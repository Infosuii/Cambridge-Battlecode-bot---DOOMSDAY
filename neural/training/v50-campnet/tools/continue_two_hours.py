"""Isolated, resumable second phase. Never modifies the completed first-hour run."""
import copy
import datetime as dt
import json
import os
import random
import shutil
import time
import traceback
import zipfile
from pathlib import Path

import numpy as np
import torch
import train

PARENT = train.ROOT
ROOT = PARENT / 'phase2-two-hours'
ROOT.mkdir(exist_ok=True)
train.ROOT = ROOT
SEED = 2026102302
WORKERS = 20


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save_checkpoint(path, policy, critic, optimizer, **extra):
    temporary = Path(str(path) + '.tmp')
    torch.save(dict(policy=policy.state_dict(), critic=critic.state_dict(),
                    optimizer=optimizer.state_dict(), **extra), temporary)
    temporary.replace(path)


def rank(score):
    return (score['faults'] == 0, score['win_rate'], score['mean_gem_margin'], -score['fuel'])


def setup():
    for name in ['checkpoints', 'evaluation', 'release', 'candidate', 'opponents', 'builds']:
        (ROOT / name).mkdir(exist_ok=True)
    if not (ROOT / 'candidate/src').exists():
        shutil.copytree(PARENT / 'release/bot_neural/src', ROOT / 'candidate/src')
    source_opponents = [
        ('original', PARENT / 'builds/baseline.wasm'),
        ('v47', PARENT / 'builds/v47-supplied.wasm'),
        ('first-hour', PARENT / 'release/bot_neural.wasm'),
        ('recent-proxy-0', PARENT / 'builds/recent-meta-proxy-0.wasm'),
        ('recent-proxy-1', PARENT / 'builds/recent-meta-proxy-1.wasm'),
    ]
    opponents = []
    for label, source in source_opponents:
        target = ROOT / 'opponents' / (label + '.wasm')
        if not target.exists():
            shutil.copyfile(source, target)
        if train.sha(target) != train.sha(source):
            raise ValueError('Opponent identity changed: ' + label)
        opponents.append(target)
    previous = load(PARENT / 'protocol.json')
    protocol = dict(phase='Second phase, two additional hours', seed=SEED,
        requested_training_seconds=7200, workers=WORKERS, device=train.DEVICE,
        training_maps=previous['training_maps'], selection_maps=previous['selection_maps'],
        final_holdout_maps=previous['final_holdout_maps'],
        opponents=[dict(label=p.stem, path=str(p), sha256=train.sha(p)) for p in opponents],
        initialization=dict(checkpoint=str(PARENT / 'checkpoints/best-trained.pt'),
                            sha256=train.sha(PARENT / 'checkpoints/best-trained.pt')),
        rule='Select solely on six selection maps; final eight maps never used for optimization or selection.',
        selection_rule='Keep first-hour policy unless a fault-free candidate improves pooled selection wins, then margin.',
        final_caveat='These map benchmarks were reported in phase one; reuse is not a new independent holdout.',
        learning_rate=0.0002, selection_every_iterations=12,
        fuel='Official CLI release default; no override',
        historical_data='No new historical draft fitting: prior historical branch was rejected. Existing drafting retained.',
        recent_data_rule='Only 21 October onward; no downloads or additional archives needed.',
        no_submission=True)
    target = ROOT / 'protocol.json'
    if target.exists() and load(target) != protocol:
        raise ValueError('Frozen phase-two protocol changed')
    train.write(target, protocol)
    return protocol, opponents


def evaluate(policy, label, maps, opponents):
    return train.evaluate(policy, label, maps, opponents, WORKERS)[0]


def finalize(policy, best, protocol, opponents, progress):
    policy.load_state_dict(best['policy'])
    train.event('final_validation', **progress, selected_iteration=best['iteration'])
    maps = list(map(Path, protocol['final_holdout_maps']))
    final = evaluate(policy, 'final-holdout', maps, opponents)
    original, _ = train.evaluate_artifact(opponents[0], 'original-holdout', maps, opponents, WORKERS)
    first_hour, _ = train.evaluate_artifact(opponents[2], 'first-hour-holdout', maps, opponents, WORKERS)
    train.export_weights(policy, False, SEED)
    src = ROOT / 'release/bot_neural/src'
    shutil.copytree(ROOT / 'candidate/src', src, dirs_exist_ok=True)
    wasm = ROOT / 'release/bot_neural.wasm'
    train.compile_bot(src, wasm, WORKERS)
    archive = ROOT / 'release/bot_neural.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src.glob('*')):
            z.write(p, 'src/' + p.name)
    train.write(ROOT / 'report.json', dict(status='verifying', **progress,
        selected_iteration=best['iteration'], selection=best['selection'],
        final_holdout=final, original_holdout=original, first_hour_holdout=first_hour,
        artifact=str(archive), source_sha256=train.sha(archive), wasm_sha256=train.sha(wasm),
        trained_candidate_promoted=best['iteration'] > 0,
        historical_data_supply_low=False, unsampled_archive_entries_before_filtering=89606,
        limitation=protocol['final_caveat']))
    # Independent rebuild and map-cluster uncertainty, using the existing verifier.
    import verify_release
    verify_release.ROOT = ROOT
    verify_release.main()
    # Freeze source selection before the all-map opponent comparisons.
    schedule_path = ROOT / 'evaluation/additional-schedule.json'
    all_maps = sorted(map(Path, protocol['training_maps'] + protocol['selection_maps'] + protocol['final_holdout_maps']))
    schedule = dict(candidate_sha256=train.sha(wasm), maps=[str(p) for p in all_maps],
                    opponent_sha256={p.stem: train.sha(p) for p in opponents[:3]},
                    purpose='Post-selection reporting only; cannot change chosen policy.')
    if schedule_path.exists() and load(schedule_path) != schedule:
        raise ValueError('Additional evaluation schedule changed')
    train.write(schedule_path, schedule)
    extra = {}
    for i in [1, 0, 2]:
        score, _ = train.evaluate_artifact(wasm, 'all-maps-vs-' + opponents[i].stem, all_maps, [opponents[i]], WORKERS)
        extra[opponents[i].stem] = score
    report = load(ROOT / 'report.json')
    report.update(status='complete', additional_comparisons=extra,
                  completed_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    train.write(ROOT / 'report.json', report)
    v = extra['v47']
    text = f'''# Additional two-hour training result

Training: {progress['training_games']:,} new simulated games; {progress['training_decisions']:,} recorded decisions; {progress['iterations']} PPO updates.

Selected iteration: {best['iteration']} (0 retains the first-hour policy). Selection score: {best['selection']['wins']}/{best['selection']['games']}.

Against supplied v47 on 40 maps, both sides: {v['wins']}/{v['games']} wins. This covers 40 deterministic map clusters, not 80 independent maps.

Eight reserved-map pooled results: selected bot {final['wins']}/{final['games']}; original bot {original['wins']}/{original['games']}; first-hour bot {first_hour['wins']}/{first_hour['games']}. Full opponent-specific rows and faults/fuel are in evaluation/. Earlier final maps have been reported already; these are reused benchmarks, not a fresh independent generalization test.

The source ZIP was checked against its files, then independently rebuilt with identical executable Wasm sections. Training tracing is disabled. No ladder submission was made.

No new historical draft was fitted; the first experiment's rejected historical network remains rejected. The four existing 21 October archives have 89,606 unsampled entries before eligibility filtering, so historical supply is not low. Local simulated games and historical matches are distinct.

Artifacts: release/bot_neural.zip and release/bot_neural.wasm. Full machine-readable report: report.json; verification: verification.json. The first-hour artifacts remain unchanged.
'''
    (ROOT / 'FINAL_REPORT.md').write_text(text, encoding='utf-8')
    train.event('complete', **report)


def main():
    # A stale lock is recoverable; an active Python owner must not be duplicated.
    lock = ROOT / 'training.lock'
    if lock.exists():
        owner = load(lock)
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, owner['pid'])
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            raise RuntimeError('Another phase-two trainer is active: ' + str(owner['pid']))
    train.write(lock, dict(pid=os.getpid(), started=dt.datetime.now(dt.timezone.utc).isoformat()))
    try:
        if (ROOT / 'report.json').exists() and load(ROOT / 'report.json').get('status') == 'complete':
            return
        protocol, opponents = setup()
        if train.DEVICE != 'cuda':
            raise RuntimeError('Expected laptop CUDA GPU is unavailable; do not silently train on CPU')
        torch.manual_seed(SEED)
        policy = train.Policy().to(train.DEVICE)
        critic = train.Critic().to(train.DEVICE)
        optimizer = torch.optim.Adam(list(policy.parameters()) + list(critic.parameters()), lr=0.0002)
        state_path = ROOT / 'checkpoints/latest.pt'
        best_path = ROOT / 'checkpoints/best.pt'
        clock_path = ROOT / 'training-clock.json'
        if state_path.exists():
            state = torch.load(state_path, map_location=train.DEVICE, weights_only=False)
            policy.load_state_dict(state['policy']); critic.load_state_dict(state['critic'])
            optimizer.load_state_dict(state['optimizer'])
            iteration, games, decisions = state['iteration'], state['games'], state['decisions']
        else:
            first = torch.load(PARENT / 'checkpoints/best-trained.pt', map_location=train.DEVICE, weights_only=False)
            policy.load_state_dict(first['policy'])
            previous = torch.load(PARENT / 'checkpoints/best.pt', map_location=train.DEVICE, weights_only=False)
            critic.load_state_dict(previous['critic'])
            iteration = games = decisions = 0
        selection_maps = list(map(Path, protocol['selection_maps']))
        if best_path.exists():
            best = torch.load(best_path, map_location=train.DEVICE, weights_only=False)
        else:
            train.event('initializing', device=train.DEVICE, gpu=torch.cuda.get_device_name(), workers=WORKERS,
                        requested_minutes=120, resumed_from='first-hour selected iteration 628')
            initial = evaluate(policy, 'selection-initial', selection_maps, opponents)
            save_checkpoint(best_path, policy, critic, optimizer, iteration=0, selection=initial)
            best = torch.load(best_path, map_location=train.DEVICE, weights_only=False)
        if not clock_path.exists():
            now = dt.datetime.now(dt.timezone.utc)
            train.write(clock_path, dict(started_utc=now.isoformat(), deadline_utc=(now + dt.timedelta(hours=2)).isoformat(),
                                         authorized_seconds=7200))
        clock = load(clock_path)
        started = dt.datetime.fromisoformat(clock['started_utc']).timestamp()
        deadline = dt.datetime.fromisoformat(clock['deadline_utc']).timestamp()
        train.event('training_started', deadline_utc=clock['deadline_utc'], iteration=iteration,
                    games=games, decisions=decisions, baseline_selection=best['selection'])
        train_maps = list(map(Path, protocol['training_maps']))
        while time.time() < deadline - 15:
            iteration += 1
            rng = random.Random(SEED + iteration * 7919)
            torch.manual_seed(SEED + iteration * 7919)
            train.export_weights(policy, True, SEED + iteration * 7919)
            wasm = train.compile_bot(ROOT / 'candidate/src', ROOT / f'builds/train-{iteration:04d}.wasm', WORKERS)
            jobs = []
            for mi, m in enumerate(rng.sample(train_maps, 12)):
                opponent = opponents[(mi + iteration) % len(opponents)]
                for side in ['A', 'B']:
                    a, b = (wasm, opponent) if side == 'A' else (opponent, wasm)
                    jobs.append(dict(a=a, b=b, map_path=m, candidate_side=side,
                                     folder=ROOT / f'runs/train-{iteration:04d}/m{mi:02d}-{side}'))
            results = train.run_jobs(jobs, WORKERS)
            samples, _ = train.training_samples(results)
            update = train.ppo_update(policy, critic, optimizer, samples)
            games += len(results); decisions += len(samples)
            save_checkpoint(state_path, policy, critic, optimizer, iteration=iteration, games=games, decisions=decisions)
            train.write(ROOT / f'checkpoints/train-{iteration:04d}.json', dict(**update, **train.summarize(results)))
            train.event('training_update', iteration=iteration, games=games, decisions=decisions,
                        elapsed_seconds=round(time.time() - started), remaining_seconds=max(0, round(deadline-time.time())),
                        **update, rollout=train.summarize(results))
            if iteration % 12 == 0 or time.time() >= deadline - 25:
                score = evaluate(policy, f'selection-{iteration:04d}', selection_maps, opponents)
                if score['faults'] == 0 and rank(score) > rank(best['selection']):
                    save_checkpoint(best_path, policy, critic, optimizer, iteration=iteration, selection=score)
                    best = torch.load(best_path, map_location=train.DEVICE, weights_only=False)
                train.event('selection', iteration=iteration, score=score,
                            best_iteration=best['iteration'], best_score=best['selection'])
        progress = dict(training_seconds=min(7200, round(time.time()-started)),
                        requested_training_seconds=7200, iterations=iteration,
                        training_games=games, training_decisions=decisions,
                        deadline_utc=clock['deadline_utc'])
        finalize(policy, best, protocol, opponents, progress)
    finally:
        if lock.exists() and load(lock).get('pid') == os.getpid():
            lock.unlink()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        train.event('failed', error=traceback.format_exc())
        raise
