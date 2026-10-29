"""Productivity from frozen capsules or unfinished local traces.

Usage: python tools/dz_productivity.py RUN [ROUND] [--compare BASE] [--json]
Comparison uses matching game/body snapshots, avoiding coverage composition bias.
"""
import argparse
import collections
import json
from pathlib import Path
import re
import zipfile

ROOT=Path(__file__).resolve().parents[1]
CATEGORIES=('work','progress','stall','idle','other')
TIME=re.compile(r'DZ_TIME round=(\d+) slot=(\d+)[^\n]*? prod (\d+) (\d+) (\d+) (\d+) (\d+)')
STUCK=re.compile(r'DZ_STUCK round=\d+ slot=\d+ kind=(\d+) index=-?\d+ pos=\S+ .*? dist=(-?\d+) state=(-?\d+)')


def load(run,root=ROOT):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+',run):raise ValueError('Invalid run name')
    folder=root/'research/dz/runs'/run
    if (folder/'results.json').exists():
        result=json.loads((folder/'results.json').read_text());cells={}
        with zipfile.ZipFile(folder/'evidence.zip') as archive:
            for game in result['per_game']:
                name=f"{game['map']}-{game['side']}"
                cells[name]=archive.read(f'games/{name}/candidate.stdout').decode('utf-8','replace')
        if not cells:raise ValueError('Completed run has no trace cells')
        clean=all(not any(game.get(k,0) for k in ('faults','fuel_outs','caught_action_errors','caught_module_errors'))
                  and 'caught_action_errors' in game for game in result['per_game'])
        return cells,'frozen capsule',clean
    cells={p.parent.name:p.read_text(encoding='utf-8',errors='replace')
           for p in (root/'artifacts/tmp/dz'/run/'games').glob('*/candidate.stdout')}
    if not cells:raise ValueError('No trace evidence found; zero files is not zero stuck episodes')
    return cells,'unfinished local trace',None


def analyse(run,at=1000,root=ROOT):
    cells,source,clean=load(run,root)
    stuck=collections.Counter();kinds=collections.Counter();snapshots={};duplicates=0;time_lines=0
    for cell,text in cells.items():
        for m in STUCK.finditer(text):stuck[cell]+=1;kinds[f'{m[1]},{m[3]}']+=1
        for m in TIME.finditer(text):
            time_lines+=1
            if int(m[1])!=at:continue
            key=(cell,int(m[2]));duplicates+=key in snapshots
            snapshots[key]=dict(zip(CATEGORIES,map(int,m.group(3,4,5,6,7))))
    if not time_lines:raise ValueError('No productivity snapshots; a release/non-trace run cannot establish zero stalls')
    if not snapshots:raise ValueError(f'No body snapshots at round {at}; choose a recorded round')
    totals=collections.Counter()
    for row in snapshots.values():totals.update(row)
    total=sum(totals.values())
    if not total:raise ValueError('Snapshots contain no observed body-turns')
    report=dict(run=run,round=at,games=len(cells),source=source,runtime_clean=clean,
        stuck_episodes=sum(stuck.values()),by_goal_state=dict(kinds),worst_maps=stuck.most_common(6),
        snapshots=len(snapshots),games_with_snapshots=len({k[0] for k in snapshots}),
        duplicate_snapshots=duplicates,body_turns=total,totals=dict(totals),
        percentages={k:100*totals[k]/total for k in CATEGORIES})
    return report,snapshots


def compare(base,candidate):
    common=base.keys()&candidate.keys()
    if not common:raise ValueError('No matching game/body snapshots')
    totals=[]
    for source in (base,candidate):
        row=collections.Counter()
        for key in common:row.update(source[key])
        n=sum(row.values())
        if not n:raise ValueError('Comparison has no body-turns')
        totals.append({k:100*row[k]/n for k in CATEGORIES})
    return dict(matching_body_snapshots=len(common),base_percentages=totals[0],
                candidate_percentages=totals[1],percentage_point_change={k:totals[1][k]-totals[0][k] for k in CATEGORIES})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run');parser.add_argument('round',type=int,nargs='?',default=1000)
    parser.add_argument('--compare');parser.add_argument('--json',action='store_true');args=parser.parse_args()
    report,snapshots=analyse(args.run,args.round)
    if args.compare:
        base,base_snapshots=analyse(args.compare,args.round)
        report['comparison']=dict(base_run=args.compare,base_runtime_clean=base['runtime_clean'],**compare(base_snapshots,snapshots))
    if args.json:print(json.dumps(report,indent=2));return
    print(f"{args.run}: games={report['games']} stuck_episodes={report['stuck_episodes']} by (goal kind, group state)={report['by_goal_state']}")
    print(f'body-turns to R{args.round}: '+' '.join(f'{k}={report["percentages"][k]:.1f}%' for k in CATEGORIES))
    print('worst maps',report['worst_maps'])
    print(f"coverage: {report['snapshots']} body snapshots in {report['games_with_snapshots']} games; source={report['source']}; runtime_clean={report['runtime_clean']}; duplicate_snapshots={report['duplicate_snapshots']}")
    if 'comparison' in report:
        c=report['comparison'];print(f"matched versus {args.compare}: {c['matching_body_snapshots']} bodies; "+' '.join(f"{k}={c['percentage_point_change'][k]:+.2f}pp" for k in CATEGORIES))


if __name__=='__main__':main()
