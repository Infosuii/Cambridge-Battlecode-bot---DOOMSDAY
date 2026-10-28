"""Write a benchmark plan covering the whole competition map pool: every map in maps/local-benchmarks once from each
side, no repeated slots (research/v59/duel_top1.json repeats 74 of its 240 seeded games and misses 9 pool maps).

Usage: c_pool_plan.py --out research/v68/pool_plan.json
The plan uses local_duel.py's format (groups of maps and sides); the opponent label is only a name for --proxy runs.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--group', type=int, default=10)
    ap.add_argument('--teams', action='store_true',
                    help='label groups with the top-12 teams of research/v59/duel_top1.json in turn (for --proxy-map/--per-team)')
    a = ap.parse_args()
    maps = sorted(p.stem for p in (ROOT / 'maps/local-benchmarks').glob('*.map26a'))
    slots = [(m, s) for m in maps for s in ('a', 'b')]
    teams = ['pool']
    if a.teams:
        duel = json.loads((ROOT / 'research/v59/duel_top1.json').read_text(encoding='utf8'))
        teams = list(dict.fromkeys(g['opponent'] for g in duel['groups']))
    groups = []
    for k, i in enumerate(range(0, len(slots), a.group)):
        chunk = slots[i:i + a.group]
        groups.append(dict(opponent=teams[k % len(teams)], maps=[m for m, _ in chunk], sides=[s for _, s in chunk]))
    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(note='Whole map pool, both sides, no repeated slots (tools/v67/c_pool_plan.py).',
                                   maps=len(maps), groups=groups), indent=1) + '\n', encoding='utf8')
    print(f'{len(maps)} maps, {len(slots)} slots per seed -> {out}')


if __name__ == '__main__':
    main()
