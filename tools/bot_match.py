"""Head-to-head official matches between two built bots (any lineage), both sides of each map.

    python tools/bot_match.py --a <bot dir with src/ | .wasm> --b <bot dir | .wasm> --out artifacts/evaluations/<fresh>
           [--maps ...]

Default --b is the frozen heuristic-v1 baseline wasm. Results (per game and summary from bot A's perspective) go to
<out>/summary.json. Maps are limited to the registered training/selection partitions, as in policy_ops compare.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from nfs import engine  # noqa: E402

MAPS = ['00collision', '00contest', '00elkring', '00fragment', '00lost-world', '00quadrants']


def wasm(source, out, label):
    source = Path(source).resolve()
    return source if source.suffix == '.wasm' else engine.official_build(source, out / f'{label}.wasm')


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--a', required=True); p.add_argument('--b', default=None); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--maps', nargs='+', default=MAPS)
    p.add_argument('--holdout', action='store_true', help='allow the 12 final maps (release check only)')
    a = p.parse_args()
    partitions = json.loads((ROOT / 'evaluation/schedules/map_partitions.json').read_text())['partitions']
    allowed = set(partitions['training']) | set(partitions['selection']) | (set(partitions['final']) if a.holdout else set())
    if not set(a.maps) <= allowed:
        raise SystemExit('final/unregistered maps refused')
    out = a.out.resolve()
    if not out.is_relative_to(ROOT / 'artifacts') or out.exists():
        raise SystemExit('fresh output directory inside artifacts/ required')
    out.mkdir(parents=True)
    bot_a = wasm(a.a, out, 'a')
    if a.b:
        bot_b = wasm(a.b, out, 'b')
    else:
        # Imported only here: nfs.policy loads torch (CUDA DLLs), which exhausted the paging file with 48 shards.
        from nfs.policy.operations import load_baseline
        bot_b = load_baseline()[1]
    games = []
    for map_name in a.maps:
        for side in ('A', 'B'):
            r = engine.run_match(bot_a if side == 'A' else bot_b, bot_b if side == 'A' else bot_a, engine.MAPS / f'{map_name}.map26a',
                                 out / 'games' / f'{map_name}-{side}', candidate_side=side).row()
            games.append(r)
            print(map_name, side, r['win'], r['gems'], r['opponent_gems'], r['rounds'], flush=True)
    summary = dict(a=str(a.a), b=str(a.b or 'heuristic-v1'), games=len(games), wins=sum(g['win'] for g in games),
                   mean_gem_margin=sum(g['gems'] - g['opponent_gems'] for g in games) / len(games),
                   faults=sum(g['faults'] for g in games), fuel_exhausted=sum(g['fuel_exhausted'] for g in games),
                   opponent_fuel_exhausted=sum(g['opponent_fuel_exhausted'] for g in games), per_game=games)
    (out / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'per_game'}))


if __name__ == '__main__':
    main()
