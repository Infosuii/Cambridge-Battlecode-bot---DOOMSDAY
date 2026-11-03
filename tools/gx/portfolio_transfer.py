"""Fit bounded data profiles using alternate opponents; prepare one frozen table."""
import argparse
from collections import Counter
import json
from pathlib import Path

import datafit
from compare import load

TRAINING = ('x2', 'v86h-s2', 'v81hl-s3')
# Each pair is (mechanism profile from datafit.py, scale relative to that profile).
CATALOG = {1:(1,.28),2:(1,.55),3:(4,.28),4:(4,.55),
           5:(8,.28),6:(8,.55),7:(9,.28),8:(9,.55)}
ORIGINAL = dict(datafit.ARMS)


def install_profiles():
    datafit.ARMS = {0:{}}
    for key, (arm,scale) in CATALOG.items():
        datafit.ARMS[key] = {i:scale*v for i,v in ORIGINAL[arm].items()}


def load_training(root, opps):
    rows, shas = {}, {}
    for profile in (0,*CATALOG):
        tag = 'base' if profile == 0 else f'shrink{profile:02}'
        rows[profile], shas[profile] = {}, set()
        for opp in opps:
            part = load(root/f'gx-{tag}-pool-{opp}'/'results.json')
            if len(part) != 172:
                raise ValueError((tag,opp,'Expected both sides of all 86 layouts'))
            for (name,side), cell in part.items():
                rows[profile][(name,side,opp)] = cell
                shas[profile].add(cell['candidate_sha256'])
        if len(shas[profile]) != 1:
            raise ValueError(f'Multiple binaries in {tag}')
    base = rows[0]
    for profile, part in rows.items():
        if part.keys()!=base.keys():
            raise ValueError(f'Unpaired cells in {profile}')
        for key, cell in part.items():
            for field in ('opponent_sha256','engine_hash','map_sha256'):
                if cell[field] != base[key][field]:
                    raise ValueError((profile,key,field))
    return rows,{k:next(iter(v)) for k,v in shas.items()}


def won(row):
    return row['outcome']=='team'+row['side']


def evaluate(rows, table):
    out=Counter()
    for key, original in rows[0].items():
        candidate=rows[table.get(key[0],0)][key]
        before,after=won(original),won(candidate)
        out.update(games=1,base_wins=before,wins=after,
                   gained=after and not before,lost=before and not after,
                   fuel_delta=candidate['fuel_outs']-original['fuel_outs'],faults=candidate['faults'])
    return dict(out,delta=out['wins']-out['base_wins'])


def select(rows, opps):
    baseline=rows[0]
    chosen={}
    detail={}
    for name in sorted({key[0] for key in baseline}):
        keys=[(name,s,o) for s in 'AB' for o in opps]
        proposals=[]
        for p,cells in rows.items():
            if not p:
                continue
            diff={k:int(won(cells[k]))-int(won(baseline[k])) for k in keys}
            delta=sum(diff.values())
            if delta < 3 or any(cells[k]['faults'] for k in keys):
                continue
            sides=[sum(v for k,v in diff.items() if k[1]==s) for s in 'AB']
            opponents=[sum(v for k,v in diff.items() if k[2]==o) for o in opps]
            if min(sides)<1 or min(opponents)<0 or sum(v>0 for v in opponents)<2:
                continue
            fuel=sum(cells[k]['fuel_outs']-baseline[k]['fuel_outs'] for k in keys)
            if fuel > 2:
                continue
            margin=sum(cells[k]['banked']-cells[k]['opponent_banked'] for k in keys)
            proposals.append((delta,min(sides),margin,-fuel,-p))
        if proposals:
            total,lesser,margin,neg_fuel,neg_profile=max(proposals)
            chosen[name]=-neg_profile
            detail[name]=dict(profile=-neg_profile,delta=total,smaller_side_gain=lesser,
                banked_margin=margin,fuel_delta=-neg_fuel)
    return chosen,detail


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path,help='stock src')
    p.add_argument('dest',type=Path,help='fresh bot folder')
    args=p.add_mutually_exclusive_group(required=True)
    args.add_argument('--uniform',type=int,choices=sorted(CATALOG))
    args.add_argument('--train',type=Path,help='match record root')
    p.add_argument('--keys',type=Path)
    a=p.parse_args()
    install_profiles()
    if a.uniform is not None:
        datafit.make(a.source,a.dest,lambda key:a.uniform)
        return
    if a.keys is None:
        p.error('--train also needs --keys')
    rows,shas=load_training(a.train,TRAINING)
    chosen,detail=select(rows,TRAINING)
    keys=json.loads(a.keys.read_text())
    config={}
    for name,profile in chosen.items():
        fp=tuple(keys[name+'-A'][:4])
        if fp!=tuple(keys[name+'-B'][:4]) or fp in config:
            raise ValueError((name,fp))
        config[fp]=profile
    datafit.make(a.source,a.dest,lambda key:config.get(key,0))
    print(json.dumps(dict(profiles=CATALOG,training=TRAINING,sha256=shas,
        selected=chosen,detail=detail,metrics=evaluate(rows,chosen)),indent=2))


if __name__=='__main__':
    main()
