// Round-state hashes and first divergence, including draft. Original must be examined/calibration.
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';
import {engine,defaultAssets,verifyAssets,VERSION} from '../engine.mjs';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..'),STUDY=path.join(ROOT,'research/deep-2026-10-28');
const [mid,actualFile,outfile]=process.argv.slice(2);const assert=(x,m)=>{if(!x)throw new Error(m);};
assert(VERSION==='2.0.0'&&mid&&actualFile&&outfile,'Engine2 and match-id actual-raw.repl26a output.json required');
const entry=JSON.parse(fs.readFileSync(path.join(STUDY,'CANDIDATE_MANIFEST.json'),'utf8')).rows.find(r=>r.match_id===mid);
assert(entry&&['calibration-excluded','examined'].includes(entry.partition),'No held-out comparison');
const actual=path.resolve(actualFile),out=path.resolve(outfile);assert(actual.startsWith(path.join(ROOT,'artifacts')+path.sep)&&out.startsWith(path.join(ROOT,'artifacts')+path.sep),'Local artifacts only');
const original=path.join(ROOT,'artifacts/local-only/deep-2026-10-28/replays',entry.partition,mid+'.repl26a');
const dir=defaultAssets();verifyAssets(dir);const E=await engine(dir),{X,check,dv}=E;
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const encode=v=>JSON.stringify(v,(k,x)=>typeof x==='bigint'?x.toString():x);
function state(){
 check(X.Game_Visualiser_ReadState(E.h,E.perspective(2,0xffffffff),E.snap));const s=E.PC.F(dv(),E.snap);
 return{banked:s.submittedGems,champions:s.champions.map(c=>({id:c.entity.index,team:c.team,type:c.type,p:c.position??null,alive:c.alive,hp:c.health,max_hp:c.maxHealth,gold:c.gold,gems:c.gems,kills:c.kills,items:c.items,consumables:c.consumables,channel:c.channelType,timer:c.channelTimer,respawn:c.respawnTimer})),
  camps:s.camps.map(c=>[c.entity.index,c.health,c.team]),groups:s.groups.map(g=>[g.state,g.captureTeam,g.captureTimer,g.respawnRounds]),
  wards:s.wards,control_wards:s.controlWards,altar_locks:s.altarLocks,teleports:s.teleports};
}
function extract(filename){
 E.load(fs.readFileSync(filename));try{
  check(X.Game_Visualiser_Timeline_GetMain(E.h,E.out));const main=dv().getBigUint64(E.out,true);check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
  let started=false;const rows=new Map();
  for(;;){check(X.Game_Visualiser_ReadTimelineState(E.h,E.tsnap));const d=dv(),r=d.getInt32(E.tsnap+8,true),phase=d.getUint32(E.tsnap+24,true),outcome=d.getUint32(E.tsnap+28,true),input=d.getUint32(E.tsnap+56,true),substep=d.getUint32(E.tsnap+104,true),ready=!!d.getUint32(E.tsnap+20,true);
   if(phase===12&&ready){const s=E.PC.I(d,E.tsnap);rows.set('draft:'+input,{round:r,input,substep,state:{drafts:s.drafts,draftCounts:s.draftCounts}});}
   if(!started&&phase===10){started=true;rows.set('round:0',{round:0,input,substep,state:state()});}
   if(started&&(phase===0||outcome))rows.set('round:'+r,{round:r,input,substep,state:state()});
   if(outcome)break;check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
  }for(const row of rows.values())row.sha256=hash(encode(row.state));return rows;
 }finally{E.destroy();}
}
const expected=extract(original),observed=extract(actual);let first=null,matched=0;
for(const [key,a] of expected){const b=observed.get(key);if(!b||a.sha256!==b.sha256){
 if(!first){const changed=[];if(a.state.champions&&b?.state.champions)for(const ch of a.state.champions){const other=b.state.champions.find(c=>c.id===ch.id);for(const [field,value] of Object.entries(ch))if(encode(value)!==encode(other?.[field]))changed.push({champion:ch.id,field,expected:value,actual:other?.[field]??null});}
 first={sample:key,round:a.round,expected_input:a.input,actual_input:b?.input??null,changed_champion_fields:changed.slice(0,12),expected_banked:a.state.banked,actual_banked:b?.state.banked??null};}
 }else matched++;
}
const result={match_id:mid,original_sha256:hash(fs.readFileSync(original)),actual_sha256:hash(fs.readFileSync(actual)),
 replay_bytes_identical:fs.readFileSync(original).equals(fs.readFileSync(actual)),expected_samples:expected.size,actual_samples:observed.size,matched_samples:matched,
 every_round_state_identical:first===null&&expected.size===observed.size,first_divergence:first,
 samples:[...expected].map(([sample,row])=>({sample,expected:row.sha256,actual:observed.get(sample)?.sha256??null}))};
fs.writeFileSync(out,encode(result)+'\n');console.log(encode({...result,samples:undefined}));
