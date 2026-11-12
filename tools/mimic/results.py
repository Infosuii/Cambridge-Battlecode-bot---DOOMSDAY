"""Summarize complete local-duel runs and paired changes in the candidate's gem margin."""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import statistics


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--run', action='append', required=True, metavar='LABEL=DIR')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    runs, result = {}, {}
    for setting in a.run:
        name, directory = setting.split('=', 1)
        data = json.loads((Path(directory) / 'games.json').read_text(encoding='utf8'))
        rows = data['games']
        keyed = {(r['seed'], r['group'], r['slot']): r for r in rows}
        if len(keyed) != len(rows) or not rows:
            raise SystemExit(f'{directory}: empty or duplicate games')
        runs[name] = keyed
        result[name] = dict(games=len(rows), candidate=data['name'], candidate_wins=sum(r['win'] for r in rows),
                            candidate_margin=statistics.mean(r['margin'] for r in rows),
                            candidate_fuel_per_game=statistics.mean(r['fuel'] for r in rows),
                            mimic_fuel_per_game=statistics.mean(r['opp_fuel'] for r in rows),
                            faults=sum(r['faults'] for r in rows))
    baseline = next(iter(runs))
    for name, run in list(runs.items())[1:]:
        keys = sorted(set(run) & set(runs[baseline]))
        differences = [run[k]['margin'] - runs[baseline][k]['margin'] for k in keys]
        if differences:
            if any(run[k]['map'] != runs[baseline][k]['map'] or run[k]['opponent'] != runs[baseline][k]['opponent']
                   for k in keys):
                raise SystemExit('paired schedules disagree')
            groups = defaultdict(float)
            mean = statistics.mean(differences)
            for k, delta in zip(keys, differences):
                groups[run[k]['map']] += delta - mean
            cluster_se = math.sqrt(len(groups) / (len(groups) - 1) * sum(v * v for v in groups.values())) / len(keys) if len(groups) > 1 else None
            result[name]['paired_vs_' + baseline] = dict(games=len(keys), candidate_margin_change=statistics.mean(differences),
                standard_error=statistics.stdev(differences) / math.sqrt(len(keys)) if len(keys) > 1 else None,
                maps=len(groups), map_cluster_standard_error=cluster_se)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(result, indent=2) + '\n', encoding='utf8', newline='\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
