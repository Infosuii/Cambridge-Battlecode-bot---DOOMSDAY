"""Audit repeated production siege visits on frozen correctness fixtures.

Scope: retained target, own camp damage, native healing, and deaths during
explicit withdrawals, including ones that never return. Not strength evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PATTERN=re.compile(r'DZ_SIEGE round=(\d+) body=(\d+) event=(\w+) group=(\d+) member=(\d+) phase=(\d+) hp=([\d.]+) target_hp=([\d.]+)')

def withdrawal_deaths(summary,stdout,end_round):
    """A missing Return must never hide a fatal interrupted withdrawal."""
    deaths={};pending={};issues=[];intervals=[]
    for row in summary['events']:
        if row['kind']=='death':deaths[row['owner']['id']]=[e['timestamp']['round'] for e in row['entries']]
    def close(body,stop,censored=False):
        if body not in pending:return
        start=pending.pop(body);died=[r for r in deaths.get(body,[]) if start<=r<=stop]
        intervals.append(dict(body=body,start=start,stop=stop,censored=censored))
        if died:issues.append(dict(body=body,rounds=died,start=start,stop=stop))
    for row in PATTERN.finditer(stdout):
        round_number,body,event=int(row[1]),int(row[2]),row[3]
        if event in ('select','return','done','infeasible','abandon'):close(body,round_number)
        if event in ('escape','open') and body not in pending:pending[body]=round_number
    for body in list(pending):close(body,end_round,True)
    return issues,intervals

def value_at(summary,body,metric,round_number):
    rows=[t for t in summary['championTimelines'] if t['owner']['id']==body and t['metric']==metric]
    if len(rows)!=1: raise ValueError(f'missing native {metric} timeline for {body}')
    elapsed=0
    for run in rows[0]['runs']:
        elapsed+=run['duration']
        if round_number<elapsed: return float(run['value'])
    raise ValueError('round beyond native timeline')

def audit(name):
    directory=ROOT/'research/dz/runs'/name
    result=json.loads((directory/'results.json').read_text())
    provenance=json.loads((directory/'provenance.json').read_text())
    if not provenance.get('scope','').startswith('Production bot on correctness fixture'): raise ValueError('requires a production correctness scenario')
    cells=[]
    with zipfile.ZipFile(directory/'evidence.zip') as capsule:
        if capsule.testzip() is not None: raise ValueError('corrupt evidence capsule')
        if 'trace_task(task,tc,"done",o.hp)' not in capsule.read('build/candidate/src/siege.cpp').decode('utf-8'):
            raise ValueError('older trace lacks completion markers; cannot audit interrupted withdrawals')
        for game in result['per_game']:
            prefix=f"games/{game['map']}-{game['side']}/"
            raw=capsule.read(prefix+'summary.json');stdout=capsule.read(prefix+'candidate.stdout')
            if hashlib.sha256(raw).hexdigest()!=game['summary_sha256']: raise ValueError('native summary identity mismatch')
            summary=json.loads(raw);states={};cycles=[]
            text=stdout.decode('utf-8')
            escape_deaths,withdrawals=withdrawal_deaths(summary,text,game['rounds'])
            deaths={}
            for row in summary['events']:
                if row['kind']=='death': deaths[row['owner']['id']]=[e['timestamp']['round'] for e in row['entries']]
            for row in PATTERN.finditer(text):
                round_number,body=int(row[1]),int(row[2]);event=row[3];task=int(row[4]),int(row[5]);hp=float(row[7]);target_hp=float(row[8])
                state=states.setdefault(body,{})
                if event in ('select','return'):
                    if event=='return' and state.get('task')==task and 'recover' in state:
                        escape_round=state['escape'];recover_round=state['recover']
                        damage=value_at(summary,body,'monsterDamageDone',escape_round)-value_at(summary,body,'monsterDamageDone',state.get('start',escape_round))
                        healing=value_at(summary,body,'healingReceived',round_number)-value_at(summary,body,'healingReceived',recover_round)
                        died=[r for r in deaths.get(body,[]) if escape_round<=r<=round_number]
                        if damage>0 and healing>0 and hp>state['recover_hp'] and target_hp<=state.get('target_hp',target_hp) and not died:
                            cycles.append(dict(body=body,task=task,start=state.get('start'),escape=escape_round,recover=recover_round,
                                returned=round_number,own_camp_damage=damage,native_healing=healing,return_hp=hp))
                    states[body]={'task':task,'start':round_number,'target_hp':target_hp}
                elif event=='escape':state.update(task=task,escape=round_number)
                elif event=='recover' and state.get('task')==task and 'escape' in state:state.update(recover=round_number,recover_hp=hp)
                elif event in ('abandon','infeasible'):states[body]={}
            runtime=all(game.get(key)==0 for key in ('faults','fuel_outs','caught_action_errors','caught_module_errors'))
            cells.append(dict(map=game['map'],side=game['side'],completed_cycles=len(cycles),cycles=cycles,
                escape_deaths=escape_deaths,withdrawals=withdrawals,banked=game['banked'],runtime_clean=runtime,
                passed=runtime and len(cycles)>=2 and not escape_deaths and game['banked']>0,
                stdout_sha256=hashlib.sha256(stdout).hexdigest(),summary_sha256=game['summary_sha256']))
    return dict(run=name,passed=bool(cells) and all(c['passed'] for c in cells),cells=cells,
        candidate_sha256=provenance['candidate_sha256'],scope=__doc__)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run');p.add_argument('--out',type=Path);args=p.parse_args()
    report=audit(args.run);report['auditor_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    text=json.dumps(report,indent=2)+'\n'
    if args.out:args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(text)
    print(json.dumps({k:v for k,v in report.items() if k not in ('scope','cells')}))
    for cell in report['cells']:print(cell['map'],cell['side'],'cycles',cell['completed_cycles'],'passed',cell['passed'])
    if not report['passed']:raise SystemExit('siege fixture audit failed; evidence retained')

if __name__=='__main__':main()
