"""Head-to-head official matches on maps from a directory outside the registered partitions (fresh holdout maps).

    python tools/fresh_match.py --a <bot dir | .wasm> --b <bot dir | .wasm> --out artifacts/evaluations/<fresh>
           --map-dir <dir of .map26a> [--maps name ...]

Same games, output layout and summary.json as tools/bot_match.py (bench tools read it unchanged). Default --maps: every
.map26a in --map-dir. Use for maps no version was developed on, e.g. new platform pool maps (cambc maps pull),
and run each frozen candidate on them once.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from nfs import engine  # noqa: E402


def wasm(source, out, label):
    source = Path(source).resolve()
    return source if source.suffix == '.wasm' else engine.official_build(source, out / f'{label}.wasm')


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--a', required=True); p.add_argument('--b', required=True); p.add_argument('--out', type=Path, required=True)
    p.add_argument('--map-dir', type=Path, required=True); p.add_argument('--maps', nargs='+', default=None)
    a = p.parse_args()
    map_dir = a.map_dir.resolve()
    names = a.maps or sorted(f.stem for f in map_dir.glob('*.map26a'))
    missing = [m for m in names if not (map_dir / f'{m}.map26a').is_file()]
    if missing:
        raise SystemExit(f'maps not in {map_dir}: {missing}')
    out = a.out.resolve()
    if not out.is_relative_to(ROOT / 'artifacts') or out.exists():
        raise SystemExit('fresh output directory inside artifacts/ required')
    out.mkdir(parents=True)
    bot_a, bot_b = wasm(a.a, out, 'a'), wasm(a.b, out, 'b')
    games = []
    for map_name in names:
        for side in ('A', 'B'):
            r = engine.run_match(bot_a if side == 'A' else bot_b, bot_b if side == 'A' else bot_a, map_dir / f'{map_name}.map26a',
                                 out / 'games' / f'{map_name}-{side}', candidate_side=side).row()
            games.append(r)
            print(map_name, side, r['win'], r['gems'], r['opponent_gems'], r['rounds'], flush=True)
    summary = dict(a=str(a.a), b=str(a.b), games=len(games), wins=sum(g['win'] for g in games),
                   mean_gem_margin=sum(g['gems'] - g['opponent_gems'] for g in games) / len(games),
                   faults=sum(g['faults'] for g in games), fuel_exhausted=sum(g['fuel_exhausted'] for g in games),
                   opponent_fuel_exhausted=sum(g['opponent_fuel_exhausted'] for g in games), per_game=games)
    (out / 'summary.json').write_text(json.dumps(summary, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'per_game'}))


if __name__ == '__main__':
    main()
