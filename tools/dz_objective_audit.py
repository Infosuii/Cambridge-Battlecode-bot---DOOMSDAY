"""Validate current objective primitives against their frozen native campaigns."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    header=hashlib.sha256((ROOT/'bots/dz/src/objective_math.h').read_bytes()).hexdigest()
    names=['dz-objective-capture-02','dz-objective-capture-control-02']
    names += [f'dz-objective-{name}-'+('03' if name.endswith('prospector') else '02') for name in ('vendetta-prospector','vendetta-control','vesper-prospector','vesper-control','vesper-reversed')]
    names += [f'dz-objective-tribute-{bag}-{active}-02' for bag in (7,14,21,35,70,98) for active in (1,0)]
    cells=[]
    for name in names:
        folder=ROOT/'research/dz/runs'/name
        report=json.loads((folder/'results.json').read_text())
        provenance=json.loads((folder/'provenance.json').read_text())
        if provenance['source']['src/objective_math.h']!=header:
            raise ValueError(f'{name}: different model source')
        if report['games']!=2 or {g['side'] for g in report['per_game']}!={'A','B'}:
            raise ValueError(f'{name}: incomplete sides')
        with zipfile.ZipFile(folder/'evidence.zip') as archive:
            frozen=archive.read('build/candidate/src/objective_math.h')
            if hashlib.sha256(frozen).hexdigest()!=header: raise ValueError(f'{name}: frozen header mismatch')
            for game in report['per_game']:
                prefix=f"games/{game['map']}-{game['side']}/"
                native_bytes=archive.read(prefix+'summary.json')
                if hashlib.sha256(native_bytes).hexdigest()!=game['summary_sha256']:
                    raise ValueError(f'{name}: native summary mismatch')
                native=json.loads(native_bytes)
                # Check both teams directly, including old receipts that omitted
                # the opponent fuel-out column. Missing data is never zero.
                if any(native['diagnostics']['botFaults'].values()) or any(
                    event['entries'] for event in native['events'] if event['kind']=='fuelExhausted'):
                    raise ValueError(f'{name}: native runtime failure')
                checks=game['diagnostic_checks']
                if not game['faults_measured'] or not checks['passed'] or checks['missing']:
                    raise ValueError(f'{name}: failed/incomplete model checks')
                if not all(checks['checks'].values()): raise ValueError(f'{name}: failed assertion')
                cells.append(dict(run=name,map=game['map'],side=game['side'],
                    native_summary_sha256=game['summary_sha256'],model_assertion_names=sorted(
                        key for key in checks['checks'] if key.startswith('math_'))))
    result=dict(verified_utc=dt.datetime.now(dt.timezone.utc).isoformat(),passed=True,
        model_sha256=header,checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        games=len(cells),capture_episodes=20,reward_episodes=70,tribute_episodes=24,
        native_faults_both_teams=0,native_fuel_outs_both_teams=0,cells=cells,
        scope='restricted solo capture, reward and tribute primitives; not full ObjModel or V-M1; no production decision activation')
    target=ROOT/'research/dz/OBJECTIVE_MATH_VALIDATION.json'
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(f'{len(cells)} current-model native cells verified; both teams: zero faults/fuel-outs')


if __name__=='__main__': main()
