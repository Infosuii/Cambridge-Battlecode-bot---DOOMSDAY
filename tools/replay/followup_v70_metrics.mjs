// Separate exploratory v70 opening/resource extract; never reads the old reserved partition.
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';
import {engine,defaultAssets,verifyAssets,VERSION} from './engine.mjs';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),S=path.join(ROOT,'research/followup-v70-2026-10-29'),L=path.join(ROOT,'artifacts/local-only/followup-v70-2026-10-29');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex'),code=hash(fs.readFileSync(fileURLToPath(import.meta.url))),assert=(x,m)=>{if(!x)throw new Error(m);};
const marks=new Set([25,50,75,100,150,250,500]),equip=items=>items.reduce((s,n,i)=>s+n*(i%2?(Math.floor(i/6)===12?750:150):30),0),cheb=(a,b)=>Math.max(Math.abs(a.x-b.x),Math.abs(a.y-b.y));
const mode=process.argv[2];assert(VERSION==='2.0.0'&&['validate','extract'].includes(mode),'Engine2 and validate/extract required');
if(mode==='extract'){const receipt=JSON.parse(fs.readFileSync(path.join(S,'METRICS_VALIDATION.json'),'utf8'));assert(receipt.passed===5&&receipt.code_sha256===code,'Current five-calibration equivalence required');}
const dir=defaultAssets();verifyAssets(dir);const E=await engine(dir),{X,check,dv}=E;
function analyse(file){
 const native=JSON.parse(fs.readFileSync(file.replace(/\.repl26a$/,'.summary.json'),'utf8')),roster=native.roster.champions,teams=new Map(roster.map(c=>[c.id,c.team==='teamA'?0:1])),events=native.events.flatMap(e=>e.entries.map(v=>({...v,kind:e.kind,owner:e.owner}))).sort((a,b)=>a.timestamp.ordinal-b.timestamp.ordinal);
 const series=new Map(native.championTimelines.map(s=>[s.owner.id+':'+s.metric,s.runs.flatMap(v=>new Array(v.duration).fill(Number(v.value)))])),value=(id,m,r)=>{const v=series.get(id+':'+m)?.[r];assert(v!==undefined,'Native RLE missing');return v;};
 const credits=new Map();for(const e of events.filter(e=>['kill','gemSubmission'].includes(e.kind))){const key=[e.timestamp.round,e.timestamp.input,e.timestamp.substep].join(':');if(!credits.has(key))credits.set(key,[]);credits.get(key).push(e);}
 const gold=new Map(roster.map(c=>[c.id,{capture_gold:0,kill_gold:0,bank_bonus_gold:0}])),rows=[],actions=[];let started=false,previous=null,priorPtr=null,geometry=null,checks=0,final;
 E.load(fs.readFileSync(file));const second=X.Engine_Malloc(E.tsize);let p=E.tsnap;
 const view=()=>{check(X.Game_Visualiser_ReadState(E.h,E.perspective(2,0xffffffff),E.snap));return E.PC.F(dv(),E.snap);};
 const sample=(h,initial=false)=>{
  const r=initial?0:h.r,state=view();assert(state.round===h.r,'Snapshot clock');
  if(!geometry){const sp=[0,1].map(t=>state.champions.filter(c=>c.team===t&&c.position).map(c=>c.position));geometry=state.groups.map((g,i)=>{const tiles=state.camps.filter(c=>c.group===i).map(c=>c.position),ds=sp.map(ps=>Math.min(...tiles.flatMap(p=>ps.map(q=>cheb(p,q)))));return ds[0]<.8*ds[1]?0:ds[1]<.8*ds[0]?1:2;});}
  const cs=state.champions.map(c=>{const id=c.entity.index;for(const m of ['gold','gems','earnedGold']){assert(c[m]===value(id,m,r),`Clock ${r}:${id}:${m}`);checks++;}
   const lost=events.filter(e=>e.owner.id===id&&e.kind==='gemLoss'&&e.timestamp.round<=r).reduce((a,e)=>a+Number(e.value),0),collected=value(id,'collectedGems',r),submitted=value(id,'submittedGems',r);assert(collected===submitted+lost+c.gems,'Physical gem ledger');
   const sources=gold.get(id),residual=c.earnedGold-sources.capture_gold-sources.kill_gold-sources.bank_bonus_gold;assert(residual===0,'Unclassified gold at sample');
   const receipts=events.filter(e=>e.kind==='gemCollection'&&e.owner.id===id&&e.timestamp.round<=r),camp=receipts.filter(e=>e.target?.kind==='campGroup');
   return{id,team:c.team,name:roster.find(x=>x.id===id).name,alive:c.alive,p:c.position??null,hp:c.health,max_hp:c.maxHealth,channel:c.channelType,respawn:c.respawnTimer,gold:c.gold,earned_gold:c.earnedGold,gems:c.gems,collected,banked:submitted,lost,spent_gold:value(id,'spentGold',r),sale_refunds:value(id,'saleRefunds',r),equipment_cost:equip(c.items),items:c.items,...sources,camp_gems:camp.reduce((a,e)=>a+Number(e.value),0),middle_gems:camp.filter(e=>geometry[e.target.id]===2).reduce((a,e)=>a+Number(e.value),0),enemy_territory_gems:camp.filter(e=>geometry[e.target.id]===1-c.team).reduce((a,e)=>a+Number(e.value),0),deaths:value(id,'deaths',r),monster_damage:value(id,'monsterDamageDone',r),champion_damage:value(id,'championDamageDone',r)};});
  const numeric=['gold','earned_gold','gems','collected','banked','lost','spent_gold','sale_refunds','equipment_cost','capture_gold','kill_gold','bank_bonus_gold','camp_gems','middle_gems','enemy_territory_gems','deaths','monster_damage','champion_damage'];
  rows.push({r,terminal:!!h.outcome,champions:cs,teams:[0,1].map(t=>Object.fromEntries(numeric.map(k=>[k,cs.filter(c=>c.team===t).reduce((s,c)=>s+c[k],0)])))});
 };
 try{
  check(X.Game_Visualiser_Timeline_GetMain(E.h,E.out));const main=dv().getBigUint64(E.out,true);check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
  for(;;){check(X.Game_Visualiser_ReadTimelineState(E.h,p));const d=dv(),h={r:d.getInt32(p+8,true),phase:d.getUint32(p+24,true),outcome:d.getUint32(p+28,true),input:d.getUint32(p+56,true),substep:d.getUint32(p+104,true)},kind=d.getUint32(p+68,true),actor=d.getUint32(p+76,true),ak=d.getUint32(p+72,true);
   if(!started&&h.phase===10){started=true;sample(h,true);}
   if(started){const key=[h.r,h.input,h.substep].join(':'),ce=credits.get(key)??[];
    if(previous&&priorPtr&&(h.phase===7||previous.phase===7||ce.length)){const a=E.PC.I(dv(),p),b=new Map(E.PC.I(dv(),priorPtr).champions.map(c=>[c.entity.index,c]));for(const c of a.champions){const before=b.get(c.entity.index),delta=before?c.gold-before.gold:0;if(delta<=0)continue;const own=ce.filter(e=>e.owner.id===c.entity.index),kinds=new Set(own.map(e=>e.kind));const source=h.phase===7||previous.phase===7?'capture_gold':kinds.size===1?(kinds.has('kill')?'kill_gold':'bank_bonus_gold'):null;if(source)gold.get(c.entity.index)[source]+=delta;}}
    if(ak===1&&teams.has(actor)&&[4,5,6,11,12,13,16,18,22,23,26].includes(kind))actions.push({r:d.getUint32(p+96,true),actor,kind});
    if((h.phase===0&&marks.has(h.r))||h.outcome)sample(h);
   }
   if(h.outcome){final=h;break;}previous=h;priorPtr=p;p=p===E.tsnap?second:E.tsnap;check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
  }
  assert(final.r===native.match.roundsStarted&&final.input===native.match.finalInput,'Final native cursor');assert(final.outcome===(native.match.outcome==='teamA'?1:native.match.outcome==='teamB'?2:3),'Final outcome');
  const last=rows.at(-1);for(const [t,name] of [[0,'teamA'],[1,'teamB']])assert(last.teams[t].banked===Number(native.teams.find(c=>c.team===name).submittedGems),'Final score');
  return{checks,rows,actions,geometry,final,roster};
 }finally{X.Engine_Free(second);E.destroy();}
}
fs.mkdirSync(path.join(L,'metrics'),{recursive:true});let entries;
if(mode==='validate')entries=JSON.parse(fs.readFileSync(path.join(ROOT,'research/deep-2026-10-28/CANDIDATE_MANIFEST.json'),'utf8')).rows.filter(r=>r.partition==='calibration-excluded');else entries=JSON.parse(fs.readFileSync(path.join(S,'MANIFEST.json'),'utf8')).rows;
const results=[];for(const entry of entries){const file=mode==='validate'?path.join(ROOT,'artifacts/local-only/deep-2026-10-28/replays/calibration-excluded',entry.match_id+'.repl26a'):path.join(L,'replays',entry.match_id+'.repl26a');const game=analyse(file);
 if(mode==='validate'){const old=JSON.parse(fs.readFileSync(path.join(ROOT,'artifacts/local-only/deep-2026-10-28/timeline-calibration-v5',entry.match_id+'.json'),'utf8'));for(const row of game.rows){const prior=old.rows.find(r=>r.r===row.r);assert(prior,'No reference mark');for(let t=0;t<2;t++)for(const key of ['banked','collected','lost','earned_gold','equipment_cost','capture_gold','kill_gold','bank_bonus_gold'])assert(prior.teams[t][key]===row.teams[t][key],`Old equivalence ${entry.match_id}:${row.r}:${t}:${key}`);}}
 else fs.writeFileSync(path.join(L,'metrics',entry.match_id+'.json'),JSON.stringify({match_id:entry.match_id,code_sha256:code,...game})+'\n');
 results.push({match_id:entry.match_id,checks:game.checks,passed:true});if(results.length%10===0)console.log(JSON.stringify({mode,processed:results.length,total:entries.length}));
}
const receipt={mode,passed:results.length,failed:0,resource_clock_checks:results.reduce((s,r)=>s+r.checks,0),code_sha256:code,old_reserved_games_used:0,results};fs.writeFileSync(mode==='validate'?path.join(S,'METRICS_VALIDATION.json'):path.join(L,'metrics/run.json'),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify({...receipt,results:undefined}));
