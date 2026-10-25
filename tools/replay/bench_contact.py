"""Contact/death checks on all 12 seeds of a predeclared bench map cohort. Offline only.
Usage: python tools/replay/bench_contact.py <prefix> <out.json> <maps comma list>
"""
from pathlib import Path
import glob,json,statistics as st,sys,zipfile
from ledger_bench import run_batches,ROOT
prefix,out,maps=sys.argv[1:4];maps=set(maps.split(','))
work=ROOT/'artifacts/tmp'/('contact-'+Path(prefix).name);work.mkdir(parents=True,exist_ok=True)
files=[];sides={}
for f in sorted(glob.glob(prefix+'-seed*-s*/games/*/*.repl26a')):
 p=Path(f);name=p.parent.name
 if name[:-2] not in maps:continue
 seed=p.parents[2].name.split('-seed')[-1].split('-')[0];outp=work/f'{name}-seed{seed}.repl26a'
 if not outp.exists():
  with zipfile.ZipFile(p) as z:outp.write_bytes(z.read('replay.repl26a'))
 files.append(str(outp));sides[outp.stem]=0 if name.endswith('-A') else 1
assert len(files)==len(maps)*24,(len(files),len(maps)*24)
for script,args,name in [('focus_fire.mjs',[],'focus'),('death_context.mjs',['2000'],'death')]:
 p=work/(name+'.json')
 if not p.exists():run_batches(script,args,files,p)
F=json.loads((work/'focus.json').read_text());D={r['id']:r for r in json.loads((work/'death.json').read_text())}
rows=[]
for g in F:
 side=sides[g['id']];r={'id':g['id']}
 for name,t in [('candidate',side),('opponent',1-side)]:
  f=g['teams'][t];ds=[d for d in D[g['id']]['deaths'] if d['team']==t]
  full=[d for d in ds if d['hp5'] is not None and d['hp5']>=.75*d['max_hp']]
  r[name]={'contact_rounds':f['contact_rounds'],'hp_lost_per_contact_round':f['dmg_dealt']/max(1,f['contact_rounds']),
    'deaths':len(ds),'full_health5_deaths':len(full),'full_health5_no_return_fire_proxy':sum(d['pvp_attacks']==0 for d in full)}
 rows.append(r)
metrics={}
for k in rows[0]['candidate']:
 metrics[k]={n:{'mean':st.mean(r[n][k] for r in rows),'median':st.median(r[n][k] for r in rows)} for n in ('candidate','opponent')}
Path(out).write_text(json.dumps({'games':len(rows),'maps':sorted(maps),'definition':'full_health5=hp five sampled alive rounds before death >=75% final maxHP; no_return_fire=pvp basic attacks zero in last5; proxy does not prove hidden vision/ambush','metrics':metrics,'per_game':rows},indent=1)+'\n',encoding='utf8')
print(json.dumps(metrics,indent=1))
