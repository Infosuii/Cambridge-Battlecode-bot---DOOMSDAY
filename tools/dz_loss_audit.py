"""Paired carried-gem loss audit from immutable native summary events."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def losses(native,side,cutoff=500):
    me='team'+side;enemy='team'+('B' if side=='A' else 'A')
    result=dict(total=0,to_enemy=0,through_cutoff=0,to_enemy_through_cutoff=0,events_30plus=0)
    for event in native['events']:
        if event['kind']!='gemLoss' or event['owner'].get('team')!=me:continue
        for entry in event['entries']:
            value=int(entry['value']);target=entry.get('target')
            if value<0:raise ValueError('negative native gem loss')
            to_enemy=isinstance(target,dict) and target.get('team')==enemy
            result['total']+=value;result['to_enemy']+=value*to_enemy;result['events_30plus']+=value>=30
            if entry['timestamp']['round']<=cutoff:
                result['through_cutoff']+=value;result['to_enemy_through_cutoff']+=value*to_enemy
    return result


def load(run,cutoff):
    folder=ROOT/'research/dz/runs'/run
    report=json.loads((folder/'results.json').read_text());rows={}
    with zipfile.ZipFile(folder/'evidence.zip') as z:
        for g in report['per_game']:
            if g['faults'] or g['fuel_outs']:raise ValueError('runtime-unclean campaign')
            key=g['map'],g['side'];raw=z.read(f'games/{key[0]}-{key[1]}/summary.json')
            if hashlib.sha256(raw).hexdigest()!=g['summary_sha256']:raise ValueError('native summary digest mismatch')
            if key in rows:raise ValueError('duplicate map-side cell')
            rows[key]=losses(json.loads(raw),key[1],cutoff)
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run');p.add_argument('--compare',required=True)
    p.add_argument('--cutoff',type=int,default=500);a=p.parse_args()
    base,candidate=load(a.compare,a.cutoff),load(a.run,a.cutoff)
    keys=sorted(set(base)&set(candidate))
    if len(keys)<2:raise ValueError('need paired native cells')
    out=dict(base=a.compare,candidate=a.run,cells=len(keys),cutoff=a.cutoff,metrics={},
             scope='Actual native loss events; repeated transfers can count the same gems again. Full-game and observed-through-cutoff totals are separate.')
    for metric in next(iter(base.values())):
        b=[base[k][metric] for k in keys];c=[candidate[k][metric] for k in keys];d=[y-x for x,y in zip(b,c)]
        out['metrics'][metric]=dict(base_mean=statistics.mean(b),candidate_mean=statistics.mean(c),
                                    delta=statistics.mean(d),descriptive_se=statistics.stdev(d)/len(d)**.5)
    print(json.dumps(out,indent=2))


if __name__=='__main__':main()
