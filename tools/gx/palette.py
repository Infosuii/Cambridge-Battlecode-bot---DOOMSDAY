"""Fit a map portfolio on one side; report the other side without updating the fit."""
import argparse
from collections import Counter
import json
from pathlib import Path
from math import sqrt

OPPONENTS = ('v92', 'v86h', 'x1bru')


def read(runs, tag, arms, control=None):
    all_rows = {}
    for arm in arms:
        rows = {}
        for opp in OPPONENTS:
            prefix = control if arm == 0 and control else f'{tag}{arm}'
            path = runs / f'gx-{prefix}-pool-{opp}' / 'results.json'
            result = json.loads(path.read_text())
            assert result['games'] == len(result['per_game']) == 172, path
            for game in result['per_game']:
                key = (game['map'], game['side'], opp)
                assert key not in rows, key
                rows[key] = game
        all_rows[arm] = rows
    base = all_rows[0]
    for rows in all_rows.values():
        assert rows.keys() == base.keys()
        for key, g in rows.items():
            for field in ('opponent_sha256', 'map_sha256', 'engine_hash'):
                assert g[field] == base[key][field], (key, field)
    return all_rows


def win(g):
    return g['outcome'] == 'team' + g['side']


def choose(rows, train_side):
    """Only training-side rows can affect the selected arm."""
    base = rows[0]
    maps = sorted({key[0] for key in base})
    selected = {}
    for name in maps:
        keys = [(name, train_side, opp) for opp in OPPONENTS]
        before = [base[k] for k in keys]
        base_wins = sum(map(win, before))
        base_fuel = sum(g['fuel_outs'] for g in before)
        choices = []
        for arm, cells in rows.items():
            after = [cells[k] for k in keys]
            delta = sum(map(win, after)) - base_wins
            if delta < 2 or any(g['faults'] for g in after):
                continue
            fuel_delta = sum(g['fuel_outs'] for g in after) - base_fuel
            if fuel_delta > 1:
                continue
            # Banked margin resolves ties before fuel, then the smaller arm number.
            margin = sum(g['banked'] - g['opponent_banked'] for g in after)
            choices.append((delta, margin, -fuel_delta, -arm))
        if choices:
            selected[name] = -max(choices)[3]
    return selected


def metrics(rows, table, side, opponent=None):
    c = Counter()
    for (name, s, opp), base in rows[0].items():
        if s != side or (opponent and opponent != opp):
            continue
        test = rows[table.get(name, 0)][name, s, opp]
        b, t = win(base), win(test)
        c.update(n=1, base_wins=b, wins=t, gained=(t and not b), lost=(b and not t),
                 fuel_outs=test['fuel_outs'], base_fuel_outs=base['fuel_outs'], faults=test['faults'])
    c['delta'] = c['gained'] - c['lost']
    discordant = c['gained'] + c['lost']
    return dict(c, z=round(c['delta'] / sqrt(discordant), 4) if discordant else 0.0)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('runs', type=Path)
    cli.add_argument('keys', type=Path)
    cli.add_argument('table', type=Path)
    cli.add_argument('tag')
    cli.add_argument('arms', nargs='+', type=int)
    cli.add_argument('--control', help='Existing control tag instead of arm 0')
    cli.add_argument('--train-side', choices=('A', 'B'), default='A')
    args = cli.parse_args()
    if 0 not in args.arms or len(set(args.arms)) != len(args.arms):
        cli.error('Provide control 0 and distinct arm numbers.')
    rows = read(args.runs, args.tag, args.arms, args.control)
    table = choose(rows, args.train_side)
    keys = json.loads(args.keys.read_text())
    entries = []
    for name, arm in table.items():
        for s, side in enumerate('AB'):
            key = keys[f'{name}-{side}']
            assert len(key) == 5 and key[-1] == s, key
            entries.append((*key, arm))
    assert len({e[:5] for e in entries}) == len(entries) <= 176
    # No unselected layout can hit a selected row through a key collision.
    assert len({tuple(v) for v in keys.values()}) == len(keys)
    entries += [(-1,-1,-1,-1,-1,0)] * (176 - len(entries))
    with args.table.open('x') as f:
        for e in entries:
            f.write('    '+', '.join(str(x) for x in e)+',\n')
    other = 'B' if args.train_side == 'A' else 'A'
    print(json.dumps(dict(arms=args.arms, selected=table, train_side=args.train_side,
        train=metrics(rows, table, args.train_side), held_out_side=other, held_out=metrics(rows, table, other),
        held_out_opponents={opp: metrics(rows, table, other, opp) for opp in OPPONENTS}), indent=2))


if __name__ == '__main__':
    main()
