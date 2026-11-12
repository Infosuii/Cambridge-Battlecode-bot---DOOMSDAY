"""Ask whether a simple geometry rule transfers to maps excluded from its fit."""
import argparse
from hashlib import sha256
import json
from math import sqrt
from pathlib import Path
from statistics import quantiles
from palette import read, win

FEATURES = ('width', 'height', 'team', 'groups', 'gems', 'altars', 'altar_open_spawn_steps',
            'gem_group_altar_steps_med', 'gem_group_spawn_steps_med', 'spawn_detour_med',
            'narrow_fraction', 'bush_fraction', 'cut_gem_fraction', 'centre_gem_fraction', 'jackpot_fraction')


def evaluate(rows, maps, side, rule, geo):
    arm, field, threshold, lower = rule
    choice = set() if arm == 0 else {name for name in maps if geo[name][field] is not None and
            ((geo[name][field] <= threshold) == lower)}
    gain = loss = fuel = faults = count = 0
    for (name, s, opp), base in rows[0].items():
        if name not in maps or s != side:
            continue
        cand = rows[arm if name in choice else 0][name,s,opp]
        before, after = win(base), win(cand)
        gain += after and not before
        loss += before and not after
        fuel += cand['fuel_outs'] - base['fuel_outs']
        faults += cand['faults']
        count += 1
    z = (gain-loss) / sqrt(gain+loss) if gain+loss else 0.0
    return dict(n=count, active=len(choice), gained=gain, lost=loss, delta=gain-loss,
                z=round(z, 4), fuel_delta=fuel, faults=faults)


def fit(rows, maps, geo, side):
    control = (0, '', 0, True)
    best_rule, best_key = control, (0.0, 0, 0)
    for field in FEATURES:
        values = [geo[name][field] for name in maps if geo[name][field] is not None]
        if len(set(values)) < 2:
            continue
        for threshold in sorted(set(quantiles(values, n=4, method='inclusive'))):
            for lower in (True, False):
                for arm in rows:
                    if arm == 0:
                        continue
                    rule = (arm, field, threshold, lower)
                    metric = evaluate(rows, maps, side, rule, geo)
                    if metric['active'] < 10 or metric['faults'] or metric['fuel_delta'] > 4:
                        continue
                    key = (metric['z'], metric['delta'], -metric['active'])
                    if key > best_key:
                        best_rule, best_key = rule, key
    return best_rule


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('runs', type=Path)
    cli.add_argument('geometry', type=Path)
    cli.add_argument('tag')
    cli.add_argument('arms', nargs='+', type=int)
    cli.add_argument('--control', default='base')
    args = cli.parse_args()
    rows = read(args.runs,args.tag,args.arms,args.control)
    geo = json.loads(args.geometry.read_text())
    maps = sorted({key[0] for key in rows[0]}, key=lambda m: sha256(('gx-topo:' + m).encode()).digest())
    assert all(name in geo and geo[name]['runtime_groups'] for name in maps)
    folds = [set(maps[::2]), set(maps[1::2])]
    report = []
    for i, train in enumerate(folds):
        other = folds[1-i]
        rule = fit(rows,train,geo,'A')
        report.append(dict(fold=i, training_maps=sorted(train), rule=rule,
            training=evaluate(rows,train,'A',rule,geo),
            new_maps_A=evaluate(rows,other,'A',rule,geo),
            new_maps_B=evaluate(rows,other,'B',rule,geo)))
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
