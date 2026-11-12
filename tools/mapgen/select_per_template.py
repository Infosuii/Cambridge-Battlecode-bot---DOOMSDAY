"""Pick one generated map per template: the candidate whose v58-mirror gameplay is closest to its template's official
gameplay (rounds, winner's gems, total banked, deaths; each scaled by the official spread), among candidates inside
the official envelope with no faults. Then keep --n templates by a seeded random draw and copy the maps to --copy-to.

Usage: python tools/mapgen/select_per_template.py --gen-dir <dir> --gen-profile <profile.json>
           --official-profile research/maps/profile_official_v58mirror.json --n 22 --seed 22 --out <selection.json>
           [--copy-to <new dir>]
"""
import argparse
import json
import os
import random
import shutil
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from screen_maps import METRICS, per_map  # noqa: E402

KEYS = ['rounds', 'winner_gems', 'total_banked', 'deaths']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gen-dir', required=True)
    ap.add_argument('--gen-profile', required=True)
    ap.add_argument('--official-profile', required=True)
    ap.add_argument('--n', type=int, required=True)
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--copy-to')
    a = ap.parse_args()
    off = {k: v for k, v in per_map(json.load(open(a.official_profile))).items() if v and not k.startswith('adgato')}
    env = {k: (min(v[k] for v in off.values()), max(v[k] for v in off.values())) for k in METRICS}
    spread = {k: statistics.pstdev(v[k] for v in off.values()) or 1 for k in KEYS}
    gen = per_map(json.load(open(a.gen_profile)))
    meta = {}
    for f in os.listdir(a.gen_dir):
        if f.endswith('_meta.json'):
            meta.update(json.load(open(os.path.join(a.gen_dir, f)))['maps'])
    best, rejected = {}, {}
    for name, v in sorted(gen.items()):
        if v is None or v['faults'] or any(not (env[k][0] <= v[k] <= env[k][1]) for k in METRICS):
            rejected[name] = 'fault, error or outside official range'
            continue
        t = meta[name]['template']
        d = sum(((v[k] - off[t][k]) / spread[k]) ** 2 for k in KEYS) ** 0.5
        if t not in best or d < best[t][0]:
            best[t] = (d, name)
    templates = sorted(best)
    keep = sorted(random.Random(a.seed).sample(templates, min(a.n, len(templates))))
    sel = {best[t][1]: {'template': t, 'distance_to_template_gameplay': round(best[t][0], 3), **meta[best[t][1]]}
           for t in keep}
    json.dump({'selected': sel, 'templates_available': templates, 'rejected': rejected, 'seed': a.seed},
              open(a.out, 'w'), indent=1)
    if a.copy_to:
        os.makedirs(a.copy_to, exist_ok=False)
        for n in sel:
            shutil.copyfile(os.path.join(a.gen_dir, n + '.map26a'), os.path.join(a.copy_to, n + '.map26a'))
    print(f'{len(templates)} templates with a passing candidate; kept {len(sel)}; rejected candidates {len(rejected)}')


if __name__ == '__main__':
    main()
