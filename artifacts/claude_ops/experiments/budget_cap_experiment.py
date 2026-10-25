"""ISOLATED EXPERIMENT (not production): cap the move/combat candidate fuel bounds in a disposable source copy.

Evidence (2026-10-25): with the production bounds the move head is admitted for only ~2% of its opportunities
(fuel budget refusal), so the neural bot almost never moves. Measured candidate costs peak at ~23-26k fuel while the
worst-case move bound is ~50k+. This script installs a model into artifacts/tmp, patches ONLY that copy so the move and
combat bounds are min(original, CAP), builds with the official release CLI/default engine fuel and plays games against
the frozen heuristic-v1 baseline. It reports gems, wins, faults and fuel exhaustion. bot/src is never modified.

    python artifacts/claude_ops/experiments/budget_cap_experiment.py --model <export> --cap 30000 --out <name> [--telemetry]
"""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'python')); sys.path.insert(0, str(ROOT / 'tools'))
from nfs import engine  # noqa: E402
from nfs.policy.operations import load_baseline  # noqa: E402
from install_policy_v2 import install  # noqa: E402

MAPS = ['00collision', '00contest', '00elkring', '00fragment', '00lost-world', '00quadrants']
MOVE = 'return (warm?0:chunks*(kFieldCap+24)'
COMBAT = 'if(head==nncfg::H::combat)return 25000+b.w.camps.size()*60+visible_camps*1600+bodies*2200;'


def patch(src, cap):
    p = src / 'nn_policy_tactics.cpp'; text = p.read_text(encoding='utf-8')
    if text.count(MOVE) != 1 or text.count(COMBAT) != 1:
        raise SystemExit('patch anchors not found; source changed')
    text = text.replace(COMBAT, f'if(head==nncfg::H::combat)return std::min<std::uint64_t>({cap},25000+b.w.camps.size()*60+visible_camps*1600+bodies*2200);')
    text = text.replace(MOVE, f'return std::min<std::uint64_t>({cap},(warm?0:chunks*(kFieldCap+24)', 1)
    # Close the extra parenthesis at the end of the move bound expression.
    anchor = 'std::min<std::uint64_t>(16,endpoints)*1700;'
    if text.count(anchor) != 1:
        raise SystemExit('move bound tail not found')
    text = text.replace(anchor, 'std::min<std::uint64_t>(16,endpoints)*1700);')
    p.write_text(text, encoding='utf-8', newline='\n')


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('--model', type=Path, required=True); a.add_argument('--cap', type=int, default=30000)
    a.add_argument('--out', required=True); a.add_argument('--telemetry', action='store_true')
    a.add_argument('--maps', nargs='+', default=MAPS)
    a = a.parse_args()
    dest = ROOT / 'artifacts/tmp/budget_experiments' / f'{a.out}-{time.time_ns()}'
    profile = 'direct_untrained' if a.telemetry else 'direct_evaluation'  # direct_untrained = given model + telemetry, argmax
    install(dest / 'bot', profile, a.model.resolve(), 20261025)
    patch(dest / 'bot/src', a.cap)
    wasm = engine.official_build(dest / 'bot', dest / 'candidate.wasm')
    baseline, baseline_wasm = load_baseline()
    games = []
    for name in a.maps:
        for side in ('A', 'B'):
            folder = dest / 'games' / f'{name}-{side}'
            row = engine.run_match(wasm if side == 'A' else baseline_wasm, baseline_wasm if side == 'A' else wasm,
                                   engine.MAPS / (name + '.map26a'), folder, candidate_side=side).row()
            if a.telemetry:
                text = engine.team_stdout(folder, side)
                import re
                last = {}
                for m in re.finditer(r'NPO2 round=(\d+) champion=(\d+) head=(\d+) starts=(\d+) direct=(\d+) continued=(\d+) fallback=(\d+)', text):
                    last[(m[2], int(m[3]))] = (int(m[4]), int(m[5]), int(m[7]))
                heads = {}
                for (c, h), (s, d, f) in last.items():
                    t = heads.setdefault(h, [0, 0, 0]); t[0] += s; t[1] += d; t[2] += f
                row['head_starts_direct_fallback'] = heads
            games.append(dict(row, map=name, side=side)); print(json.dumps(games[-1]), flush=True)
    summary = dict(experiment='move/combat candidate bound cap (isolated copy)', cap=a.cap, model=str(a.model.resolve()), profile=profile,
                   wasm_sha256=engine.sha256(wasm), baseline_wasm_sha256=baseline['wasm_sha256'], games=len(games),
                   wins=sum(g['win'] for g in games), gems=sum(g['gems'] for g in games), opponent_gems=sum(g['opponent_gems'] for g in games),
                   faults=sum(g['faults'] for g in games), fuel_exhausted=sum(g['fuel_exhausted'] for g in games),
                   opponent_fuel_exhausted=sum(g['opponent_fuel_exhausted'] for g in games))
    (dest / 'summary.json').write_text(json.dumps(dict(summary, rows=games), indent=1) + '\n', encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
