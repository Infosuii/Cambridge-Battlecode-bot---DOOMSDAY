"""Choose a per-map plan (draft variant + experiment bits) for DZ_PLAN_TABLE from completed pool runs.

Usage: python tools/dz_plan_select.py --configs CONFIGS.json [--margin 100] [--out bots/dz/src/map_plans.inc]
       python tools/dz_plan_select.py --configs CONFIGS.json --uniform NAME --out FILE   (screen table: NAME on all 70
       maps; NAME "base" = no bits; pass FILE to tools/dz.py smoke --plan-rows with --set DZ_PLAN_TABLE=1)

CONFIGS.json: {"baseline": {"v76": RUN, "v65": RUN}, "configs": {NAME: {"draft": -1|0..7, "bits": [FLAG, ...],
"runs": {"v76": RUN, "v65": RUN}}}}. Every config needs a run against every baseline opponent.
Score per map = sum over opponents and both sides of (our banked - opponent banked). A config replaces the default on
a development map only when it beats the baseline by --margin and has no faults or fuel-outs on that map. The
registered holdout (every fifth map of the 70-map pool, HOLDOUT.md) is never assigned a row. Best-of-K on
deterministic games is optimistic: confirm the table against an opponent not used here.
The table always has 70 rows (unchanged maps: draft -1, bits 0), so with screens run through --uniform tables under
DZ_PLAN_TABLE=1 a selected map replays exactly the screened game against the screening opponents.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BITS = ['EE', 'EE_REGROUP', 'GEAR_SURVIVE', 'GEAR_PROSPECT', 'GEAR_HEALTH', 'CREWS', 'CREW_ALL', 'BANK_NEAR_MIN',
        'BANK_BIG', 'RING_GATES', 'OPENING_GOLD', 'GOLD_VALUE', 'EE2', 'EE2_BOLD', 'HOME', 'HOARD', 'FIGHT', 'TURTLE']  # Order of dz::PlanBit (plan.h).


def signatures():
    sig = dict(line.split() for line in (ROOT / 'research/dz/z-integration-2026-10-31/map_signatures.txt').read_text().splitlines())
    if len(sig) != 70:
        raise ValueError('expected 70 map signatures')
    return sig


def mask(bits):
    if any(b not in BITS for b in bits):
        raise ValueError(f'unknown bits {bits}')
    return sum(1 << BITS.index(b) for b in bits)


def per_map(run):
    rows = json.loads((ROOT / 'research/dz/runs' / run / 'results.json').read_text())['per_game']
    score, bad, cells = {}, set(), set()
    for g in rows:
        cell = g['map'], g['side']
        if cell in cells:
            raise ValueError(f'{run}: duplicate cell {cell}')
        cells.add(cell)
        score[g['map']] = score.get(g['map'], 0) + g['banked'] - g['opponent_banked']
        if g['faults'] or g['fuel_outs']:
            bad.add(g['map'])
    if any((m, s) not in cells for m in score for s in 'AB'):
        raise ValueError(f'{run}: each map needs both sides')
    return score, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--configs', required=True)
    ap.add_argument('--margin', type=float, default=100)
    ap.add_argument('--out', default=str(ROOT / 'bots/dz/src/map_plans.inc'))
    ap.add_argument('--uniform')
    a = ap.parse_args()
    spec = json.loads(Path(a.configs).read_text())
    if a.uniform:
        sig = signatures()
        c = {'draft': -1, 'bits': []} if a.uniform == 'base' else spec['configs'][a.uniform]
        lines = [f'// Uniform screen table: {a.uniform} on every map (tools/dz_plan_select.py --uniform).']
        lines += [f"    {{{sig[m]}u, {c['draft']}, {mask(c['bits'])}u}}, // {m}" for m in sorted(sig)]
        Path(a.out).write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
        return
    opponents = sorted(spec['baseline'])
    base = {o: per_map(spec['baseline'][o]) for o in opponents}
    maps = set.intersection(*(set(base[o][0]) for o in opponents))
    pool = sorted(p.stem for p in (ROOT / 'maps/local-benchmarks').glob('*.map26a'))
    if len(pool) != 70:
        raise ValueError('expected the registered 70-map pool')
    held_out = set(pool[4::5])
    sig = signatures()
    cand = {}
    missing = []
    for name, c in spec['configs'].items():
        if set(c['runs']) != set(opponents) or any(b not in BITS for b in c['bits']):
            raise ValueError(f'{name}: needs a run per opponent and known bits')
        if any(not (ROOT / 'research/dz/runs' / c['runs'][o] / 'results.json').exists() for o in opponents):
            missing.append(name)  # Not screened yet (tools/dz_z14_screen.sh); excluded from this table.
            continue
        cand[name] = {o: per_map(c['runs'][o]) for o in opponents}
    if missing:
        print('configs without complete runs, skipped:', ' '.join(sorted(missing)))
    table, gain, chosen = {}, 0.0, {}
    for m in sorted(maps - held_out):
        b = sum(base[o][0][m] for o in opponents)
        best, best_score = None, b + a.margin
        for name, runs in cand.items():
            if any(m in runs[o][1] for o in opponents):
                continue
            s = sum(runs[o][0][m] for o in opponents)
            if s >= best_score:
                best, best_score = name, s
        if best:
            table[m] = best
            gain += best_score - b
    cells = 2 * len(opponents) * len(maps - held_out)
    lines = ['// Generated by tools/dz_plan_select.py from ' + Path(a.configs).name + f' (margin {a.margin:g}; opponents '
             + ', '.join(opponents) + '). Holdout maps have no row.']
    for m in pool:
        name = table.get(m)
        c = spec['configs'][name] if name else {'draft': -1, 'bits': []}
        lines.append(f"    {{{sig[m]}u, {c['draft']}, {mask(c['bits'])}u}}, // {m}: {name or ('holdout' if m in held_out else 'base')}")
        if name:
            chosen[name] = chosen.get(name, 0) + 1
    Path(a.out).write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'maps_with_rows': len(table), 'development_maps': len(maps - held_out),
                      'in_sample_margin_gain_per_cell': round(gain / cells, 1), 'configs_used': chosen}, indent=1))


if __name__ == '__main__':
    main()
