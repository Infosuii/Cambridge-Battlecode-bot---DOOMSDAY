"""Local-only paired development screen; no network or ladder operations."""
from pathlib import Path
import concurrent.futures as cf
import hashlib, importlib.util, json, re, shutil
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('dz',ROOT/'tools/dz.py')
dz=importlib.util.module_from_spec(spec);spec.loader.exec_module(dz)
BP=['X1_BUSHPRE=15','X1_BUSHPRE_LAZY=60']
PARENT=BP+['X1_PLAN=1','X1_PLAN_ROUND=150','X1_PLAN_ID=4','X1_WALKTAIL=3']
ARMS={'off':[], 'parent':PARENT, 'end500':PARENT+['X3_PLAN_END=500'],
      'cycle':['X3_BANKCYCLE=1'], 'cover':BP+['X3_COVER_SAFE=1'],
      'end500cycle':PARENT+['X3_PLAN_END=500','X3_BANKCYCLE=1']}
MAPS=[ROOT/'maps'/folder/(name+'.map26a') for folder,names in [
    ('local-benchmarks',['01starvation','01gold-rush','00great-wall','00rows']),
    ('x1-unseen',['gen4_0005']),('x1-maze',['pc_maze_00'])] for name in names]
OPPS=['x2','v86h','v81hl','v92']
CACHE=None
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def build(label,flags,trace=False):
    folder=OUT/'builds'/label
    if not folder.exists():
        shutil.copytree(ROOT/'bots/botx3/src',folder/'src')
        p=folder/'src/x1_config.h';text=p.read_text(encoding='utf-8')
        for definition in flags+(['X3_TRACE=1'] if trace else []):
            key,value=definition.split('=',1)
            text,n=re.subn(r'^#define '+key+r'\s+[^\n]+','#define '+key+' '+value,text,flags=re.M)
            if not n: text+='\n#define '+key+' '+value+'\n'
        p.write_text(text,encoding='utf-8')
    wasm=folder/'bot.wasm'
    if not wasm.exists(): dz.build(folder,wasm)
    write(folder/'identity.json',dict(flags=flags,trace=trace,sha256=dz.sha(wasm),
          source={p.name:dz.sha(p) for p in (folder/'src').iterdir() if p.is_file()},cli=dz.sha(dz.CLI)))
    print('BUILD',label,dz.sha(wasm),flush=True)
    return wasm
def cached(candidate,opponent,map_path,side):
    # Reuse exact-byte matches, with engine identity checked from provenance.
    global CACHE
    roots=[ROOT/'research/dz/runs',ROOT/'artifacts/local-only/g5070/k009-work/research/dz/runs']
    if CACHE is None:
        CACHE={};cli_hash=dz.sha(dz.CLI)
        for root in roots:
            for p in root.glob('*/results.json'):
                prov=p.with_name('provenance.json')
                if not prov.exists(): continue
                q=json.loads(prov.read_text())
                if q.get('cli_sha256')!=cli_hash:continue
                for row in json.loads(p.read_text())['per_game']:
                    key=(q.get('candidate_sha256'),q.get('opponent_sha256'),row['map_sha256'],row['side'])
                    CACHE.setdefault(key,dict(row,reused_from=str(p)))
        print('INDEX',len(CACHE),'previous exact cells',flush=True)
    return CACHE.get((dz.sha(candidate),dz.sha(opponent),dz.sha(map_path),side))
def main():
    for m in MAPS: assert m.exists(),m
    bots={k:build(k,v) for k,v in ARMS.items()}
    assert dz.sha(bots['off'])=='1746f2bb7fa341530f41bd8c8c4896b35172783f35eacee8e4a4b6ac0ceea183', 'repair-off binary changed'
    assert dz.sha(bots['parent'])=='22e6067a4233'+dz.sha(bots['parent'])[12:], 'x1c1 identity changed'
    opps={}
    for o in OPPS:
        p=OUT/'opponents'/f'{o}.wasm'
        if not p.exists():dz.build(ROOT/'bots'/o,p)
        opps[o]=p
    write(OUT/'manifest.json',dict(scope='Development smoke only, maps already inspected; not untouched validation',
         arms=ARMS,maps={str(p):dz.sha(p) for p in MAPS},opponents={o:dz.sha(p) for o,p in opps.items()},cli=dz.sha(dz.CLI)))
    jobs=[];rows=[]
    for arm,c in bots.items():
        for o,opp in opps.items():
            for m in MAPS:
                for side in ['A','B']:
                    folder=OUT/'games'/arm/o/f'{m.stem}-{side}'
                    receipt=folder/'screen.json'
                    row=json.loads(receipt.read_text()) if receipt.exists() else cached(c,opp,m,side)
                    if row:
                        row.update(arm=arm,opponent=o); rows.append(row);write(receipt,row)
                    else: jobs.append((arm,o,c,opp,m,side,folder))
    print('REUSE',len(rows),'NEW',len(jobs),flush=True)
    def play(job):
        arm,o,c,opp,m,side,folder=job
        row,_=dz.match(c,opp,m,side,folder,existing=(folder/'summary.json').exists())
        row.update(arm=arm,opponent=o);write(folder/'screen.json',row)
        return row
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(play,jobs):
            rows.append(row);write(OUT/'rows.json',rows)
            print(len(rows),'/',len(ARMS)*len(OPPS)*len(MAPS)*2,row['arm'],row['opponent'],row['map'],row['side'],row['banked'],flush=True)
    write(OUT/'rows.json',rows)
    report={}
    for arm in ARMS:
        rr=[r for r in rows if r['arm']==arm]
        report[arm]=dict(games=len(rr),wins=sum(r['outcome']=='team'+r['side'] for r in rr),fuel=sum(r['fuel_outs'] for r in rr),
            faults=sum(r['faults'] for r in rr),banked=sum(r['banked'] for r in rr)/len(rr),collected=sum(r['collected'] for r in rr)/len(rr),
            by_opponent={o:sum(r['outcome']=='team'+r['side'] for r in rr if r['opponent']==o) for o in OPPS})
    write(OUT/'summary.json',report);print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
