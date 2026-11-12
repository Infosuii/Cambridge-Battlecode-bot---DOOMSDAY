"""Generate the run ledger from paired results and frozen build metadata."""
import argparse
import json
from pathlib import Path
from compare import load, pair, summarise

SETS = {'maps/ladder-pool': 'pool', 'maps/x1-unseen': 'styled', 'maps/x1-maze': 'maze'}


def flags(command):
    return ', '.join(command[i + 1] for i, arg in enumerate(command[:-1]) if arg == '--set') or 'default'


def argument(command, flag, fallback='—'):
    return command[command.index(flag)+1] if flag in command else fallback


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('runs', type=Path, nargs='?', default=Path('research/gx/runs'))
    args = cli.parse_args()
    print('# GX match results\n')
    print('| Run | Bot | Switches | Opponent | Set | Wins | x3mf | Gained / lost | z | Fuel-outs | Faults | Deaths/game | Wasm |')
    print('| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |')
    for p in sorted(args.runs.glob('*/results.json')):
        provenance = json.loads(p.with_name('provenance.json').read_text())
        result = json.loads(p.read_text())
        command = provenance.get('command', [])
        opponent = argument(command, '--opponent')
        scenario = SETS.get(provenance.get('map_directory'), 'other')
        reference = args.runs/f'gx-base-{scenario}-{opponent}'/'results.json'
        if '--maps' in command and '--pool' not in command:
            scenario += ' sample'
        base_wins = flips = z = '—'
        if reference.exists() and 'sample' not in scenario:
            try:
                m = summarise(pair(load(reference), load(p)))
            except ValueError:
                pass
            else:
                base_wins = m['base']
                flips = f"{m['gained']} / {m['lost']}"
                z = f"{m['z']:.2f}"
        deaths = sum(x['deaths'] for x in result['per_game']) / result['games']
        digest = result['per_game'][0]['candidate_sha256'][:12]
        print(f"| [{p.parent.name}](../research/gx/runs/{p.parent.name}/results.json) "
              f"| {provenance.get('candidate_bot', '—')} | {flags(command)} | {opponent} | {scenario} "
              f"| {result['wins']}/{result['games']} | {base_wins} | {flips} | {z} | {result['fuel_outs']} "
              f"| {result['faults']} | {deaths:.2f} | `{digest}` |")


if __name__ == '__main__':
    main()
