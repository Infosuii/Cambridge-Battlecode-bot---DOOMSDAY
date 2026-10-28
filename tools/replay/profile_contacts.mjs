// Exact round-boundary geometry + native damage, basic-attack target focus.
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';
import {engine,defaultAssets,verifyAssets,VERSION} from './engine.mjs';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),STUDY=path.join(ROOT,'research/deep-2026-10-28'),LOCAL=path.join(ROOT,'artifacts/local-only/deep-2026-10-28');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex'),cheb=(a,b)=>Math.max(Math.abs(a.x-b.x),Math.abs(a.y-b.y)),assert=(x,m)=>{if(!x)throw new Error(m);};
const partition=process.argv[2],output=path.resolve(process.argv[3]??'');assert(VERSION==='2.0.0'&&['calibration-excluded','examined'].includes(partition),'Explicit engine2; calibration/examined only');assert(output.startsWith(path.join(ROOT,'artifacts')+path.sep),'Local output required');
const specHash=hash(fs.readFileSync(path.join(STUDY,'P5_PROFILE_SPEC.json'))),codeHash=hash(fs.readFileSync(fileURLToPath(import.meta.url)));
if(partition==='examined'){const p=JSON.parse(fs.readFileSync(path.join(STUDY,'PROFILE_VALIDATION.json'),'utf8'));assert(p.passed===5&&p.failed===0&&p.code_sha256===codeHash&&p.spec_sha256===specHash,'Current five-game calibration receipt required');}
const entries=JSON.parse(fs.readFileSync(path.join(STUDY,'CANDIDATE_MANIFEST.json'),'utf8')).rows.filter(r=>r.partition===partition);
const dir=defaultAssets();verifyAssets(dir);const E=await engine(dir),{X,check,dv}=E,second=X.Engine_Malloc(E.tsize),results=[];fs.mkdirSync(output,{recursive:true});
for(const entry of entries){
 const mid=entry.match_id,file=path.join(LOCAL,'replays',partition,mid+'.repl26a'),native=JSON.parse(fs.readFileSync(file.replace(/\.repl26a$/,'.summary.json'),'utf8'));
 const series=new Map(native.championTimelines.filter(s=>s.metric==='championDamageDone').map(s=>[s.owner.id,s.runs.flatMap(r=>new Array(r.duration).fill(Number(r.value)))]));
 const teams=new Map(native.roster.champions.map(c=>[c.id,c.team==='teamA'?0:1])),stats=[0,1].map(()=>({contact_champion_rounds:0,contact_damage:0,low_hp_near_enemy_rounds:0,separating_rounds:0,basic_target_rounds:0,multi_attacker_target_rounds:0}));
 const focus=new Map();let previous=null,started=false,p=E.tsnap,prevPtr=null,boundaries=0,damageChecks=0;
 E.load(fs.readFileSync(file));try{
  check(X.Game_Visualiser_Timeline_GetMain(E.h,E.out));const main=dv().getBigUint64(E.out,true);check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
  for(;;){check(X.Game_Visualiser_ReadTimelineState(E.h,p));const d=dv(),r=d.getInt32(p+8,true),phase=d.getUint32(p+24,true),outcome=d.getUint32(p+28,true),kind=d.getUint32(p+68,true),ak=d.getUint32(p+72,true),actor=d.getUint32(p+76,true);
   if(phase===10)started=true;
   if(started&&kind===5&&ak===1&&prevPtr){
    const before=E.PC.I(dv(),prevPtr),x=d.getInt32(p+88,true),y=d.getInt32(p+92,true),enemy=before.champions.find(c=>c.alive&&c.position&&c.team!==teams.get(actor)&&c.position.x===x&&c.position.y===y);
    if(enemy){const key=[r,teams.get(actor),enemy.entity.index].join(':');if(!focus.has(key))focus.set(key,new Set());focus.get(key).add(actor);}
   }
   if(started&&(phase===0||outcome)){
    const state=E.PC.I(dv(),p);boundaries++;
    for(const c of state.champions){
     const t=stats[c.team],values=series.get(c.entity.index),increment=values[r]-(values[r-1]??0);assert(increment>=-1e-6,'Damage series went backwards');damageChecks++;
     const enemies=state.champions.filter(e=>e.team!==c.team&&e.alive&&e.position);
     if(c.alive&&c.position&&enemies.some(e=>cheb(c.position,e.position)<=6)){t.contact_champion_rounds++;t.contact_damage+=increment;}
     const prior=previous?.champions.find(a=>a.entity.index===c.entity.index);
     if(prior?.alive&&prior.position&&prior.health<=.35*prior.maxHealth){
      const near=previous.champions.filter(e=>e.team!==c.team&&e.alive&&e.position).sort((a,b)=>cheb(prior.position,a.position)-cheb(prior.position,b.position))[0];
      if(near&&cheb(prior.position,near.position)<=6){t.low_hp_near_enemy_rounds++;if(c.alive&&c.position&&cheb(c.position,near.position)>cheb(prior.position,near.position))t.separating_rounds++;}
     }
    }previous=state;
   }
   if(outcome)break;prevPtr=p;p=p===E.tsnap?second:E.tsnap;check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
  }
  for(const [key,actors] of focus){const team=Number(key.split(':')[1]);stats[team].basic_target_rounds++;stats[team].multi_attacker_target_rounds+=actors.size>=2;}
  for(const s of stats){s.damage_per_contact_champion_round=s.contact_champion_rounds?s.contact_damage/s.contact_champion_rounds:null;s.basic_focus_rate=s.basic_target_rounds?s.multi_attacker_target_rounds/s.basic_target_rounds:null;s.low_hp_separation_rate=s.low_hp_near_enemy_rounds?s.separating_rounds/s.low_hp_near_enemy_rounds:null;}
  const result={match_id:mid,partition,code_sha256:codeHash,spec_sha256:specHash,passed:true,boundaries,damage_samples:damageChecks,teams:stats};
  fs.writeFileSync(path.join(output,mid+'.json'),JSON.stringify(result)+'\n');results.push(result);
 }finally{E.destroy();}
 if(results.length%25===0)console.log(JSON.stringify({processed:results.length,total:entries.length}));
}
const receipt={partition,code_sha256:codeHash,spec_sha256:specHash,passed:results.length,failed:0,hands_off_used:0,total_boundary_samples:results.reduce((a,r)=>a+r.boundaries,0),results:results.map(r=>({match_id:r.match_id,passed:r.passed,damage_samples:r.damage_samples}))};
fs.writeFileSync(path.join(output,'run.json'),JSON.stringify(receipt,null,2)+'\n');if(partition==='calibration-excluded')fs.writeFileSync(path.join(STUDY,'PROFILE_VALIDATION.json'),JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({...receipt,results:undefined}));X.Engine_Free(second);
