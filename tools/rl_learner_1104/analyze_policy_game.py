"""Read an actual local-game bundle; report diagnostics without filtering bad rows."""
import argparse
import base64
import json
from pathlib import Path
import statistics
import struct
import zipfile


def quantiles(values):
    if not values:return None
    s=sorted(values)
    return dict(n=len(s),p50=statistics.median(s),p95=s[int(.95*(len(s)-1))],max=s[-1],min=s[0])


def analyze(bundle,summary_path,side='A'):
    team='teamA' if side=='A' else 'teamB'
    j=json.loads(Path(summary_path).read_text())
    with zipfile.ZipFile(bundle) as z:
        data=z.read('team-'+side.lower()+'.stdout')
    text=data.replace(b'\0',b'').decode('utf-8','replace')
    dec=[];executed={};costs=[];turncosts=[];bad=0
    for line in text.splitlines():
        try:
            p=line.split()
            if line.startswith('CLA1 '):
                if len(p)!=10:raise ValueError('bad decision')
                raw=struct.unpack('<448h',base64.b64decode(p[9],validate=True))
                dec.append(dict(round=int(p[1]),slot=int(p[2]),body=int(p[3]),action=int(p[4]),
                                logp=float(p[5]),reset=int(p[6]),mask=int(p[7]),raw=raw))
            elif line.startswith('CLX1 '):
                if len(p)!=5:raise ValueError('bad execution')
                key=(int(p[1]),int(p[3]))
                if key in executed:raise ValueError('duplicate execution')
                executed[key]=int(p[4])
            elif line.startswith('CLF1 '):
                costs.append(dict(encoder=int(p[4]),forward=int(p[6]),left=int(p[8])))
            elif line.startswith('CLT1 '):
                turncosts.append(dict(used=int(p[3]),start=int(p[4]),left=int(p[5]),crossed=int(p[6])))
        except Exception:
            if line.startswith(('CLA1 ','CLX1 ','CLF1 ','CLT1 ')):bad+=1
    keys=[(d['round'],d['body']) for d in dec]
    repeated=len(keys)-len(set(keys))
    replaced=sum(executed.get(k)!=d['action'] for k,d in zip(keys,dec))
    fuel={t:sum(len(e['entries']) for e in j.get('events',[]) if e['kind']=='fuelExhausted' and e['owner'].get('team')==t)
          for t in ('teamA','teamB')}
    invalid_costs=sum(c['encoder']>1000000 or c['forward']>1000000 for c in costs)
    costs=[c for c in costs if c['encoder']<=1000000 and c['forward']<=1000000]
    result=dict(match=j['match'],teams=j['teams'],faults=j['diagnostics']['botFaults'],fuel_outs=fuel,
                decisions=len(dec),execution_rows=len(executed),malformed_rows=bad,repeated_decisions=repeated,
                replaced_or_missing_executions=replaced,stdout_bytes=len(data),
                invalid_wrapped_cost_measurements=invalid_costs,
                encoder_fuel=quantiles([c['encoder'] for c in costs]),forward_fuel=quantiles([c['forward'] for c in costs]),
                combined_fuel=quantiles([c['encoder']+c['forward'] for c in costs]),
                fuel_left_after_actor=quantiles([c['left'] for c in costs]),
                measured_total_turn_fuel=quantiles([c['used'] for c in turncosts if not c['crossed']]),
                turns_crossing_round=sum(c['crossed'] for c in turncosts),
                ppo_diagnostic_gate=(bool(dec) and not any([fuel[team],j['diagnostics']['botFaults'][team],bad,repeated,replaced])),
                limits='Diagnostic gate only; observation/probability/lifecycle/coverage audit still required.')
    return result,dec


def main():
    p=argparse.ArgumentParser();p.add_argument('--bundle',required=True);p.add_argument('--summary',required=True)
    p.add_argument('--side',default='A');p.add_argument('--out',required=True);a=p.parse_args()
    result,_=analyze(a.bundle,a.summary,a.side)
    Path(a.out).write_text(json.dumps(result,indent=2)+'\n')
    small={k:v for k,v in result.items() if k not in ('teams','match')}
    small['outcome']=result['match']['outcome'];small['scores']={t['team']:t['submittedGems'] for t in result['teams']}
    print(json.dumps(small,indent=2))


if __name__=='__main__':main()
