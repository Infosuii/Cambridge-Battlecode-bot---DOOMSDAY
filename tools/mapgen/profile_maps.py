"""Gameplay profile of maps: one built bot against another (default: the same bot), both sides of every map.

Usage: python tools/mapgen/profile_maps.py --a <bot.wasm> [--b <bot.wasm>] --maps <dir or files...> --out <dir>
       [--workers 8]

Writes <out>/profile.json: per game the rounds played, outcome, both teams' submitted/collected gems, deaths, gold,
faults and fuel-outs (nfs.engine.run_match, official default fuel, cached per game folder). Used to screen map
quality, not to measure candidates: with the same bot on both sides it reveals nothing about a candidate.
"""
import argparse
import concurrent.futures as cf
import dataclasses
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'python'))
from nfs import engine  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--a', required=True)
    ap.add_argument('--b')
    ap.add_argument('--maps', nargs='+', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--workers', type=int, default=8)
    a = ap.parse_args()
    maps = []
    for m in a.maps:
        p = Path(m)
        maps += sorted(p.glob('*.map26a')) if p.is_dir() else [p]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    wa, wb = Path(a.a).resolve(), Path(a.b or a.a).resolve()
    jobs = []
    for m in maps:
        for side in 'AB':
            first, second = (wa, wb) if side == 'A' else (wb, wa)
            jobs.append(dict(a=first, b=second, map_path=m.resolve(), folder=out / 'games' / f'{m.stem}-{side}',
                             candidate_side=side))
    rows = []
    with cf.ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(engine.run_match, **j): j for j in jobs}
        for f in cf.as_completed(futs):
            j = futs[f]
            try:
                r = dataclasses.asdict(f.result())
            except Exception as e:  # a failed game is recorded, never silently dropped
                r = {'map': j['map_path'].stem, 'side': j['candidate_side'], 'error': str(e)[:300]}
            rows.append(r)
    rows.sort(key=lambda r: (r['map'], r['side']))
    meta = {'a': str(wa), 'b': str(wb), 'wasm_a': engine.sha256(wa), 'wasm_b': engine.sha256(wb), 'maps': len(maps),
            'games': len(rows), 'errors': sum(1 for r in rows if 'error' in r)}
    (out / 'profile.json').write_text(json.dumps({'meta': meta, 'games': rows}, indent=1), encoding='utf-8')
    print(json.dumps(meta))


if __name__ == '__main__':
    main()
