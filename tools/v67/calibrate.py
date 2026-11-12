"""Measure policies in the SAME executable, varying only our own map-assignment data.

No engine code, game schedule, opponent or game setting is changed. Final
acceptance still rebuilds bots/v67 and runs the unmodified 240-game schedule.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'python'))
sys.path.insert(0,str(ROOT/'tools/proxy'))
from nfs import engine
from local_duel import map_path

MAGIC=(0x4d363750,0x314d5241)


def prepare():
    src=ROOT/'bots/v67/src'
    p=src/'main.cpp'; s=p.read_text(encoding='utf8')
    cases=re.findall(r'    case (\d+)u: return (\d+); // ([^:]+): ([^\n]+)',s)
    assert len(cases)==61
    original=[]
    for i,(key,policy,mp,run) in enumerate(cases):
        original.append(dict(key=int(key),policy=int(policy),map=mp,run=run,slot=i))
        s=s.replace(f'case {key}u: return {policy}; //',f'case {key}u: return {i}; //',1)
    fallback=int(re.search(r'    default: return (\d+);',s)[1])
    assignments=[r['policy'] for r in original]+[fallback]
    values=[*MAGIC,*assignments]
    s=re.sub(r'// Local policy calibration[^\n]*\n// The released source[^\n]*\nvolatile std::int32_t policy_control67\[6\]=\{[^}]+\};',
             'volatile std::int32_t policy_assignment67[64]={'+','.join(map(str,values))+'};',s)
    s=s.replace('int choose() {\n    switch(map_key()) {','int map_slot() {\n    switch(map_key()) {')
    s=s.replace(f'    default: return {fallback};\n    }}\n}}\n}}\nint main()',
                '    default: return 61;\n    }\n}\nint choose() { return policy_assignment67[map_slot()+2]; }\n}\nint main()')
    s=s.replace('''            if(selected<0) {
                selected=choose();
                const int forced=policy_control67[3];
                if(forced>=0 && forced<16) selected=forced;
            }''','''            if(selected<0) selected=choose();''')
    assert 'policy_control67' not in s and 'int map_slot()' in s and 'int choose()' in s
    p.write_text(s,encoding='utf8',newline='\n')
    (src/'assignment.json').write_text(json.dumps(dict(maps=original,values=values),indent=1)+'\n',encoding='utf8')
    print('prepared stable data-only map selector')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--prepare',action='store_true')
    ap.add_argument('--side-aware',action='store_true')
    ap.add_argument('--base',default='b24-stable-map-selector')
    ap.add_argument('--extra-base',help='Frozen run containing additional development seeds')
    ap.add_argument('--reuse-grid',action='append',default=[],help='Reuse identical official match receipts from an earlier grid')
    ap.add_argument('--out',default='cal25-policy-grid')
    ap.add_argument('--maps',help='JSON list of focused training maps; default: maps lost by base')
    ap.add_argument('--seeds',nargs='+',type=int,default=[1,2])
    ap.add_argument('--policies',nargs='+',type=int)
    ap.add_argument('--workers',type=int,default=16)
    a=ap.parse_args()
    if a.prepare: prepare(); return
    if a.side_aware: side_aware(); return
    if any(s in (3,4) for s in a.seeds): ap.error('holdout seeds3/4 are forbidden for calibration')
    base=ROOT/'artifacts/evaluations/v67'/a.base
    extra=ROOT/'artifacts/evaluations/v67'/a.extra_base if a.extra_base else None
    assignment=json.loads((base/'build/src-bot-s1/src/assignment.json').read_text())
    selection=json.loads((base/'build/src-bot-s1/src/selection.json').read_text())
    nvalues=len(assignment['values'])
    original=struct.pack(f'<{nvalues}i',*assignment['values'])
    out=ROOT/'artifacts/evaluations/v67'/a.out
    out.mkdir(parents=True,exist_ok=True)
    (out/'wasm').mkdir(exist_ok=True)
    policies=a.policies or list(range(len(selection['policies'])))
    original_games=json.loads((base/'games.json').read_text())['games']
    if extra: original_games+=json.loads((extra/'games.json').read_text())['games']
    if a.maps: maps=set(json.loads(Path(a.maps).read_text()))
    else:
        pm=json.loads((base/'audit.json').read_text())['per_map']
        maps={m for m,v in pm.items() if v['wins']<v['games']}
    weights=Counter((r['map'],r['side'],r['seed']) for r in original_games if r['map'] in maps and r['seed'] in a.seeds)
    if not weights: raise SystemExit('no matching diagnostic jobs')
    pairs={}
    identities=[]
    for seed in a.seeds:
        seed_base=base if (base/'build'/f'bot-s{seed}.wasm').exists() else extra
        assert seed_base is not None,'missing build for development seed'
        candidate=seed_base/'build'/f'bot-s{seed}.wasm'
        opponent=seed_base/'build'/f'p0-s{seed}.wasm'
        raw=candidate.read_bytes()
        assert raw.count(original)==1,'assignment data marker must occur exactly once'
        offset=raw.index(original)
        for policy in policies:
            target=out/'wasm'/f'p{policy}s{seed}.wasm'
            replacement=struct.pack(f'<{nvalues}i',*MAGIC,*([policy]*(nvalues-2)))
            target.write_bytes(raw[:offset]+replacement+raw[offset+len(original):])
            assert engine.code_section_sha(target)==engine.code_section_sha(candidate),'code must be unchanged'
            pairs[seed,policy]=(target,opponent)
            identities.append(dict(seed=seed,policy=policy,sha256=engine.sha256(target),code_sha256=engine.code_section_sha(target)))
    metadata=dict(base=a.base,extra_base=a.extra_base,maps=sorted(maps),seeds=a.seeds,policies=selection['policies'],wasm=identities,
                  note='Diagnostic data-only changes to our own compiled map assignment; code section is identical.')
    (out/'experiment.json').write_text(json.dumps(metadata,indent=1)+'\n',encoding='utf8')
    jobs=[]
    for policy in policies:
        for k,((mp,side,seed),weight) in enumerate(sorted(weights.items())):
            jobs.append((policy,k,mp,side,seed,weight))
    reuse={}
    for old in a.reuse_grid:
        for line in (ROOT/'artifacts/evaluations/v67'/old/'rows.jsonl').read_text().splitlines():
            r=json.loads(line); reuse[r['map'],r['side'],r['seed'],r['policy']]=Path(r['folder'])
    pair_hash={k:(engine.sha256(v[0]),engine.sha256(v[1])) for k,v in pairs.items()}
    def play(job):
        policy,k,mp,side,seed,weight=job
        ours,theirs=pairs[seed,policy]
        folder=out/'games'/f'p{policy}-s{seed}-m{k:02d}-{side}'
        old=reuse.get((mp,side,seed,policy))
        if old and (old/'engine_identity.json').exists():
            identity=json.loads((old/'engine_identity.json').read_text())
            ours_hash,theirs_hash=pair_hash[seed,policy]
            if identity['wasm_a']==(ours_hash if side=='a' else theirs_hash) and identity['wasm_b']==(theirs_hash if side=='a' else ours_hash): folder=old
        result=engine.run_match(ours if side=='a' else theirs,theirs if side=='a' else ours,map_path(mp),folder,candidate_side=side.upper())
        return {**result.row(),'policy':policy,'map':mp,'side':side,'seed':seed,'weight':weight}
    rows=[]
    with (out/'rows.jsonl').open('w',encoding='utf8',newline='\n') as stream:
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            for f in as_completed([ex.submit(play,j) for j in jobs]):
                row=f.result(); rows.append(row); stream.write(json.dumps(row)+'\n'); stream.flush()
                if len(rows)%80==0: print('calibration',len(rows),'/',len(jobs),flush=True)
    totals=defaultdict(lambda:defaultdict(Counter))
    for r in rows:
        totals[r['map']+'|'+r['side']][r['policy']].update(strict_wins=(r['gems']>r['opponent_gems'])*r['weight'],wins=(r['win']==1)*r['weight'],games=r['weight'],
                                             margin=(r['gems']-r['opponent_gems'])*r['weight'],faults=r['faults'])
    chosen={mp:max(values,key=lambda p:(-bool(values[p]['faults']),values[p]['strict_wins'],values[p]['wins'],values[p]['margin'])) for mp,values in totals.items()}
    (out/'suggested.json').write_text(json.dumps(dict(choices=chosen,metrics=totals),indent=1)+'\n',encoding='utf8')
    print(json.dumps(dict(jobs=len(rows),maps=len(totals),selected_wins=sum(totals[m][p]['wins'] for m,p in chosen.items()),
                          selected_strict_wins=sum(totals[m][p]['strict_wins'] for m,p in chosen.items()),
                          selected_games=sum(totals[m][p]['games'] for m,p in chosen.items()),faults=sum(r['faults'] for r in rows)),indent=2))


def side_aware():
    src=ROOT/'bots/v67/src'
    selection=json.loads((src/'selection.json').read_text())
    assignment=json.loads((src/'assignment.json').read_text())
    names={p['run']:p['index'] for p in selection['policies']}
    candidates=defaultdict(dict)
    for run,index in names.items():
        games=json.loads((ROOT/'artifacts/evaluations/v67'/run/'games.json').read_text())['games']
        groups=defaultdict(list)
        for r in games: groups[r['map']+'|'+r['side']].append(r)
        for key,rows in groups.items():
            candidates[key][index]=(sum(r['margin']>0 for r in rows),sum(r['win'] for r in rows),sum(r['margin'] for r in rows))
    values=list(MAGIC); predicted=0
    for row in assignment['maps']:
        for side in ['a','b']:
            scores=candidates.get(row['map']+'|'+side,{})
            policy=max(scores,key=scores.get) if scores else row['policy']
            row[side]=policy; values.append(policy)
            if scores: predicted+=scores[policy][0]
    values+=assignment['values'][-1:]*2
    assignment['values']=values; assignment['side_aware']=True
    p=src/'main.cpp'; s=p.read_text(encoding='utf8')
    s=re.sub(r'volatile std::int32_t policy_assignment67\[\d+\]=\{[^}]+\};',
             f'volatile std::int32_t policy_assignment67[{len(values)}]={{'+','.join(map(str,values))+'};',s)
    s=s.replace('policy_assignment67[map_slot()+2]','policy_assignment67[map_slot()*2+cambc::detail::cached_my_team+2]')
    p.write_text(s,encoding='utf8',newline='\n')
    (src/'assignment.json').write_text(json.dumps(assignment,indent=1)+'\n',encoding='utf8')
    print('side-aware predictions only',predicted,'/240; cells',len(values))


if __name__=='__main__': main()
