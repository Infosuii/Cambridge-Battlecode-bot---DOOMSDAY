"""Explicitly resume only this user's paused, owned experiment."""
from pathlib import Path
import hashlib
import json
import sys
import psutil

BASE = Path(r'C:\projects\cambridge battlecode\work\agentic-improvement')
sys.path.insert(0, str(BASE / 'autonomy'))
import benchmark
from table_offsets import changes
from coordinate_probe import vectors
from macro_search_space import INDICES
from store import save, now

def main():
    running = []
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            command = ' '.join(p.info['cmdline'] or [])
            if str(BASE).lower() in command.lower() and p.pid != psutil.Process().pid and (
                'bounded_delivery_retune.py' in command or 'collect_games.py' in command or 'cambc.exe run' in command
            ): running.append(p.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied): pass
    assert not running, f'Existing owned work needs inspection: {running}'
    assert not (BASE / 'training/training.lock').exists()
    supervisor = json.loads((BASE / 'training/supervisor.json').read_text(encoding='utf-8'))
    assert supervisor['status'] != 'running'
    checkpoint = json.loads((BASE / 'training/runs/bounded-delivery-retune-v1/pause-20261107/checkpoint.json').read_text(encoding='utf-8'))
    checked_sources = 0
    receipts = 0
    for tag, anchor in {'o': 'auto_bank_arrive_original', 'l': 'auto_bank_arrive_learned'}.items():
        jobs = [('auto_rt7_' + tag + '_c000', [0.] * len(INDICES))]
        jobs += [('auto_rt7_' + tag + '_' + suffix, theta) for suffix, theta in vectors(.5).items()]
        parent = benchmark.ARENA / 'bots' / anchor / 'src'
        for name, theta in jobs:
            root = benchmark.ARENA / 'bots' / name
            src = root / 'src'
            if not src.exists(): continue
            assert sorted(p.name for p in src.iterdir()) == sorted(p.name for p in parent.iterdir()), name
            patch = changes(theta)[0]
            for p in parent.iterdir():
                if not p.is_file(): continue
                if p.name == 'bot.cpp':
                    text = p.read_text(encoding='utf-8')
                    assert text.count(patch['old']) == 1
                    assert (src / p.name).read_text(encoding='utf-8') == text.replace(patch['old'], patch['new']), name
                else: assert p.read_bytes() == (src / p.name).read_bytes(), name
            checked_sources += 1
            receipt = root / 'build-receipt.json'
            wasm = root / '.cambc/build-release/bot-injected.wasm'
            if receipt.exists() and wasm.exists():
                saved = json.loads(receipt.read_text(encoding='utf-8'))
                assert saved['inputs']['source'] == benchmark.digest(src), name
                assert saved['wasm'] == hashlib.sha256(wasm.read_bytes()).hexdigest(), name
                receipts += 1
    assert receipts >= checkpoint['built_variants']
    for name in ('STOP', 'CONTROLLER_STOP'):
        marker = BASE / 'autonomy' / name
        if marker.exists():
            assert 'User requested pause on2026-11-07.' in marker.read_text(encoding='utf-8'), name
    save(BASE / 'training/runs/bounded-delivery-retune-v1/resume-20261108.json', {
        'at': now(), 'sources_verified': checked_sources, 'cached_builds_verified': receipts,
        'authorization': 'User: continue and once bot packaged push to ladder. Explicit resume, packaging, GitHub findings push and official ladder upload/activation authorized.',
        'scope': 'Finish existing one bounded retune and validations, select/package bot, publish findings, then submit/activate on configured team; do not switch AI accounts.'
    })
    for name in ('STOP', 'CONTROLLER_STOP'):
        (BASE / 'autonomy' / name).unlink(missing_ok=True)
    current = BASE / 'CURRENT_WORK.md'
    current.write_text('# RESUMED — 2026-11-08\n\nUser explicitly resumed and authorized pushing packaged bot to ladder. Earlier no-official-actions restriction is superseded by this latest instruction. Finish the saved bounded retune, package the best judged bot, push all findings to GitHub, then submit and activate on the configured team. One AI account/day; no paid API fallback.\n\n' + current.read_text(encoding='utf-8'), encoding='utf-8')
    print(json.dumps({'sources_verified': checked_sources, 'cached_builds_verified': receipts, 'pause_markers_cleared': True}))

if __name__ == '__main__': main()
