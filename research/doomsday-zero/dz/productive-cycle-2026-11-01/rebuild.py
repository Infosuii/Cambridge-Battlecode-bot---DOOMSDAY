import csv, datetime as dt, hashlib, json, re, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from dz import sample_at
from dz_cycle_report import report
OUT=ROOT/'research/dz/productive-cycle-2026-11-01'
RAW=ROOT/'artifacts/local-only/dz-cycle-reference-2026-11-01'
OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,d:p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf8',newline='\n')
names=['dz-hybrid-current-v76lab-final-01','dz-hybrid-current-v81hl-final-01',
 'dz-cycle-collision-v76-02','dz-cycle-collision-v81-01','dz-cycle-collision-v76-03',
 'dz-cycle-collision-v76-04','dz-cycle-collision-v76-05','dz-cycle-collision-v81-05',
 'dz-cycle-development-maps-05','dz-cycle-map-policy-06','dz-cycle-renewal-08',
 'dz-cycle-resource-team-09','dz-cycle-execution-repair-10','dz-cycle-execution-repair-v81-10']
reports=[report(n) for n in names]
write(ROOT/'artifacts/tmp/dz-cycle-all.json',reports)
csvrows=[]
for run in reports:
 for cell in run['cells']:
  row={k:cell[k] for k in ('map','side','rounds','outcome','banked','opponent_banked','collected','gold','deaths','faults','opponent_faults','fuel_outs','captures','clears')}
  row.update(run=run['name'],candidate_sha256=run['candidate_sha256'],opponent_sha256=run['opponent_sha256'],
   complete_collect_bank_purchase_return_bodies=sum(b['complete_collect_bank_purchase_return'] for b in cell['bodies']),
   spent_gold=sum(float(b['final']['spentGold']) for b in cell['bodies']),home_rounds='unmeasured',idle_rounds='unmeasured')
  for r in (100,250):row.update({f'R{r}_{k}':v for k,v in cell['early'][r].items()})
  csvrows.append(row)
with (OUT/'scoreboard.csv').open('w',newline='',encoding='utf8') as f:
 writer=csv.DictWriter(f,fieldnames=list(csvrows[0]),lineterminator='\n');writer.writeheader();writer.writerows(csvrows)
catalog={}
for file in ('fish-recent.json','mite-recent.json','packs-metadata.json'):
 for m in json.loads((RAW/file).read_text(encoding='utf-8-sig'))['matches']:catalog[m['matchId']]=m
selection=[('collision','ca170a4d-50d9-4491-a7ae-f8490565cc4b','teamA'),
 ('expanse','3536220a-c571-421f-91cd-4156775e019f','teamA'),
 ('split','656686a8-4b80-4a08-814c-24e23b79ad4c','teamB'),
 ('packs','1bf7d5f5-21a3-4f08-9241-ab9cddda593b','teamB')]
refs=[]
for name,mid,team in selection:
 meta=catalog[mid];s=json.loads((RAW/(name+'-summary.json')).read_text())
 native=RAW/(name+'-inner.repl26a');trace=json.loads((RAW/(name+'-trace.json')).read_text())
 local=ROOT/'maps/local-benchmarks'/('00'+name+'.map26a')
 assert sha(local)==s['match']['mapHash']
 assert s['match']['engineVersion']=='2.0.0'
 bodies=[b for b in s['champions'] if b['team']==team]
 examples=[]
 for b in bodies:
  events={series['kind']:series['entries'] for series in s['events'] if series['owner'].get('team')==team and series['owner'].get('id')==b['id']}
  examples.append(dict(body=b['id'],champion=b['name'],
   captures=[e for e in events.get('gemCollection',[]) if e['context']=='campGroup'][:4],
   banks=events.get('gemSubmission',[])[:3],purchases=events.get('buyItem',[])[:4],
   opening_actions=[a for a in trace['actions'] if a['actor']['index']==b['id'] and a['kind'] in (4,5,6)][:12]))
 entry=dict(match_id=mid,metadata=meta,opponent_build_versions='unknown; not public',
  source_url='https://2026a.battlecode.co.uk/game/match-groups/'+meta['groupId'],
  retrieved_utc=dt.datetime.fromtimestamp((RAW/(name+'.repl26a')).stat().st_mtime,dt.timezone.utc).isoformat(),
  local_map=local.stem,map_sha256=sha(local),engine=s['match']['engineVersion'],engine_hash=s['match']['engineBuildHash'],
  replay_bundle_sha256=sha(RAW/(name+'.repl26a')),replay_sha256=sha(native),summary_sha256=sha(RAW/(name+'-summary.json')),
  trace_sha256=sha(RAW/(name+'-trace.json')),raw_directory=RAW.relative_to(ROOT).as_posix(),
  observed_side=team,examples=examples)
 refs.append(entry)
write(OUT/'references.json',dict(retrieval_date='2026-11-01',ladder_sha256=sha(RAW/'ladder.json'),
 ladder=json.loads((RAW/'ladder.json').read_text(encoding='utf-8-sig')),matches=refs,
 limits='Focused descriptive examples, not causal strength estimates. Oct29 packs is older. No Varg transferred. No reserved trajectories decoded.'))
current=reports[-1]
latest={'00collision':'dz-cycle-execution-repair-10','00packs':'dz-cycle-execution-repair-10','00corners':'dz-cycle-development-maps-05'}
registry=[]
for i,p in enumerate(sorted((ROOT/'maps/local-benchmarks').glob('*.map26a')),1):
 reserved=i%5==0
 cells=[r for r in csvrows if r['map']==p.stem and r['run']==latest.get(p.stem)]
 row=dict(map=p.stem,lexical_index=i,reserved=reserved,map_sha256=None if reserved else sha(p),
  status='unopened_holdout' if reserved else 'measured_development_failure' if cells else 'unstudied',
  optimised=False,independently_confirmed=False,
  references=[] if reserved else [r['match_id'] for r in refs if r['local_map']==p.stem],
  chosen_draft=['Vesper Vale','Heart of Ruin','Vendetta'] if p.stem in ('00collision','00packs') else None,
  observed_rosters=[] if reserved else [dict(run=r['name'],side=c['side'],roster=[b['champion'] for b in c['bodies']])
    for r in reports if r['name']==latest.get(p.stem) for c in r['cells'] if c['map']==p.stem],
  map_plan='Current experimental package; not selected for release' if p.stem in ('00collision','00packs') else None,
  opening='Group2 from (0,0) side / group3 from (30,30) side; harmless helpers leave capture to onsite owner; deadline R80' if p.stem=='00packs' else None,
  roles='Solo jobs; harmless resource helpers; authoritative managed crews/siege remain separate owners' if cells else None,
  farm_circuit='Observed payout, finite contract, known expired respawn inspected at full design HP' if cells else None,
  capture='Existing onsite/lower-slot soft claim; authoritative crew capturer takes precedence' if cells else None,
  bank='Finite actual-bag task to nearest static altar; live tri-state admission; no inferred payout' if cells else None,
  gear='Mite collision profile from current reference' if p.stem=='00collision' else 'Jungle opener from older Mite packs reference' if p.stem=='00packs' else None,
  contingencies='Live neutral recovery, finite failed-job backoff, Home shopping/recovery; blocked altar planning remains incomplete' if cells else None,
  fallback='DZ_LIFECYCLE=0 preserves prior controller; generic bounded lifecycle with flag on' if not reserved else 'Unmeasured; do not tune',
  sides={side:dict(status='pending' if not any(c['side']==side for c in cells) else 'measured_failure',
    cells=[c for c in cells if c['side']==side]) for side in ('A','B')})
 registry.append(row)
write(OUT/'map-strategies.json',dict(engine='2.0.0',inventory=70,reserved=14,measured_maps=3,
 completion='Coverage inventory only; map-specific optimisation is incomplete. No map is labelled optimised.',maps=registry))
source={p.relative_to(ROOT/'bots/dz').as_posix():sha(p) for p in (ROOT/'bots/dz/src').rglob('*') if p.is_file()}
write(OUT/'SOURCE.json',dict(base_head='19549bb08e21f929b2649f1440503d3cd0c0d01f',
 current_flags=dict(DZ_ECONOMY_V2=1,DZ_LIFECYCLE=1),development_candidate=current['candidate_sha256'],
 source=source,source_manifest_sha256=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),
 frozen_incumbent='dz-cycle-collision-v76-05',working_package='dz-cycle-execution-repair-10',
 promotion=False,release_holdout_used=False))
development_source={}
for key in source:
 path=ROOT/'bots/dz'/key
 data=path.read_bytes()
 if key=='src/config.h':
  text=path.read_text()
  for flag in ('DZ_ECONOMY_V2','DZ_LIFECYCLE'):
   text,count=re.subn(r'^#define '+flag+r'\s+[^\n]+','#define '+flag+' 1',text,flags=re.MULTILINE)
   assert count==1
  data=text.encode('utf8')
 development_source[key]=hashlib.sha256(data).hexdigest()
assert development_source==current['source'],'Working source diverged from the measured candidate'
write(OUT/'SOURCE_CHECK.json',dict(exact_frozen_source_match=True,files=len(source),
 config_overrides={'DZ_ECONOMY_V2':1,'DZ_LIFECYCLE':1},candidate=current['candidate_sha256'],
 cells_verified=8,reference_maps_hash_verified=4,registry_entries=len(registry),reserved_entries=sum(r['reserved'] for r in registry)))
# Keep the detailed decoder output local; the tracked scoreboard is deliberately compact.
(OUT/'scoreboard.json').unlink(missing_ok=True)
print('Saved compact scoreboard, four attributed references, 70-map registry and source provenance')
