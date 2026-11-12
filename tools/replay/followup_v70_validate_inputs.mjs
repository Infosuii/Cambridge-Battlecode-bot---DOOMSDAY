// Derived from the frozen validator; only study paths and exploratory allowlist differ.
// Independently reapply accepted inputs through official engine APIs and compare bytes/states.
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';import {engine,defaultAssets,verifyAssets,VERSION} from './engine.mjs';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const STUDY=path.join(ROOT,'research/followup-v70-2026-10-29'),LOCAL=path.join(ROOT,'artifacts/local-only/followup-v70-2026-10-29');
const assert=(x,m)=>{if(!x)throw new Error(m);},hash=b=>crypto.createHash('sha256').update(b).digest('hex');
assert(VERSION==='2.0.0','Explicit engine2 required');
const manifest=JSON.parse(fs.readFileSync(path.join(STUDY,'PUPPET_MANIFEST.json'),'utf8'));
const dir=defaultAssets();verifyAssets(dir);const E=await engine(dir),{X,dv,check}=E;
const CODE_HASH=hash(fs.readFileSync(fileURLToPath(import.meta.url)));
function head(){check(X.Game_Visualiser_ReadTimelineState(E.h,E.tsnap));const d=dv();return{
 r:d.getInt32(E.tsnap+8,true),phase:d.getUint32(E.tsnap+24,true),outcome:d.getUint32(E.tsnap+28,true),
 awaiting:!!d.getUint32(E.tsnap+20,true),input:d.getUint32(E.tsnap+56,true),actor:d.getUint32(E.tsnap+60,true)};}
function stateHash(){
 check(X.Game_Visualiser_ReadState(E.h,E.perspective(2,0xffffffff),E.snap));const s=E.PC.F(dv(),E.snap);
 const state={banked:s.submittedGems,champions:s.champions.map(c=>[c.entity.index,c.team,c.type,c.position??null,c.alive,c.health,c.maxHealth,c.gold,c.gems,c.kills,c.items,c.consumables,c.channelType,c.channelTimer,c.respawnTimer]),
  camps:s.camps.map(c=>[c.entity.index,c.health,c.team]),groups:s.groups.map(g=>[g.state,g.captureTeam,g.captureTimer,g.respawnRounds])};
 return hash(JSON.stringify(state,(k,v)=>typeof v==='bigint'?v.toString():v));
}
const entity=(kind,id)=>{dv().setUint32(E.args+128,kind,true);dv().setUint32(E.args+132,id,true);return E.args+128;};
const pos=(x,y)=>{dv().setInt32(E.args+144,x,true);dv().setInt32(E.args+148,y,true);return E.args+144;};
function apply(row){const a=row.args;
 if(row.tag===3){assert(a[0]<=2,'Unknown end reason');return X.Game_Runner_EndTurn(E.h,a[0]);}
 if(row.tag===4){assert(a[0]===1&&a[2]===255,'Unsupported automatic/forced draft record');return X.Game_Action_Draft(E.h,a[1]);}
 assert(row.tag===0,'Unsupported input tag');
 switch(row.action){
  case 0:return X.Game_Action_SetPriority(E.h,a[0]);
  case 1:return X.Game_Action_Move(E.h,a[0],a[1],E.out);
  case 2:assert(a[2]===65535,'Non-default attack modifier');return X.Game_Action_Attack(E.h,entity(a[0],a[1]));
  case 3:return X.Game_Action_Cast(E.h,a[0],entity(a[1],a[2]),pos(a[3],a[4]),E.out);
  case 4:return X.Game_Action_Recall(E.h);
  case 5:return X.Game_Action_SubmitGems(E.h,pos(a[0],a[1]));
  case 6:return X.Game_Action_BuyItem(E.h,a[0],a[1]);
  case 7:return X.Game_Action_CancelChannel(E.h);
  case 8:assert(a[1]===1,'Unsupported multi-consumable purchase');return X.Game_Action_BuyConsumable(E.h,a[0]);
  case 9:return X.Game_Action_UseConsumable(E.h,a[0],pos(a[1],a[2]),E.out);
  case 10:return X.Game_Action_PlaceWard(E.h,pos(a[0],a[1]),E.out);
  case 11:return X.Game_Action_Sell(E.h,a[0]);
  default:throw new Error('Unknown action');
 }
}
const inputs=process.argv.slice(2);assert(inputs.length,'Pass parsed local JSON inputs');
const results=[];
for(const filename of inputs){
 const spec=JSON.parse(fs.readFileSync(filename,'utf8')),entry=manifest.rows.find(r=>r.match_id===spec.match_id);
 assert(entry&&['calibration-excluded','exploratory'].includes(entry.partition),'Only calibration/examined inputs');
 if(entry.partition==='exploratory'){
  const proof=JSON.parse(fs.readFileSync(path.join(STUDY,'PUPPET_INPUT_VALIDATION.json'),'utf8'));
  assert(proof.passed===5&&proof.failed===0&&proof.code_sha256===CODE_HASH,'Five current-code calibration passes required');
 }
 const raw=fs.readFileSync(entry.partition==='calibration-excluded'?path.join(ROOT,'artifacts/local-only/deep-2026-10-28/replays/calibration-excluded',entry.match_id+'.repl26a'):path.join(LOCAL,'replays',entry.match_id+'.repl26a'));
 assert(hash(raw)===spec.replay_sha256,'Replay bytes changed');
 const map=fs.readFileSync(path.join(ROOT,spec.map_file));assert(hash(map)===spec.map_sha256,'Map changed');
 const expected=new Map();let started=false;
 E.load(raw);check(X.Game_Visualiser_Timeline_GetMain(E.h,E.out));const main=dv().getBigUint64(E.out,true);
 check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
 for(;;){const s=head();if(!started&&s.phase===10){started=true;expected.set(0,stateHash());}
  if(started&&(s.phase===0||s.outcome))expected.set(s.r,stateHash());if(s.outcome)break;check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));}
 E.destroy();const p=X.Engine_Malloc(map.length);new Uint8Array(X.memory.buffer,p,map.length).set(map);
 check(X.Game_FromMapFileBytes(p,map.length,E.out,0));E.h=dv().getBigUint64(E.out,true);X.Engine_Free(p);check(X.Game_Runner_Init(E.h));
 let matched=0,initial=false,draftIndex=0;
 const observed=new Set(),labelled=[];
 const compare=s=>{
  if(!initial&&s.phase===10){initial=true;assert(stateHash()===expected.get(0),'Initial roster/state mismatch');observed.add(0);matched++;}
  if(initial&&(s.phase===0||s.outcome)&&!observed.has(s.r)){
   assert(stateHash()===expected.get(s.r),`Round${s.r} state differs while validating raw accepted inputs`);observed.add(s.r);matched++;
  }
 };
 for(const row of spec.inputs){
  let s=head();compare(s);while(!s.awaiting&&!s.outcome){check(X.Game_Runner_Step(E.h));s=head();compare(s);}
  assert(!s.outcome,'Script continued after game end');assert(s.input===row.input-1,'Input cursor differs');
  const team=s.phase===12?draftIndex%2:spec.roster.find(c=>c.id===s.actor)?.team;
  labelled.push({...row,r:s.r,phase:s.phase,actor:s.actor===0xffffffff?null:s.actor,team});
  check(apply(row));if(row.tag===3&&s.phase===12)draftIndex++;
 }
 let final=head();compare(final);while(!final.outcome){check(X.Game_Runner_Step(E.h));final=head();compare(final);}
 check(X.Game_SaveReplay(E.h));check(X.Game_FileBuffer(E.h,E.args,E.args+4));const fp=dv().getUint32(E.args,true),n=dv().getUint32(E.args+4,true);
 const regenerated=Buffer.from(new Uint8Array(X.memory.buffer,fp,n));assert(regenerated.equals(raw),'Official API reserialization differs byte-for-byte');
 assert(observed.size===expected.size,'Not every original round was compared');
 fs.writeFileSync(filename,JSON.stringify({...spec,inputs:labelled,validation:{replay_bytes_identical:true,round_states_identical:matched,code_sha256:CODE_HASH}})+'\n');
 const r={match_id:spec.match_id,passed:true,accepted_inputs:labelled.length,round_states:matched,replay_bytes_identical:true};results.push(r);console.log(JSON.stringify(r));E.destroy();
}
if(results.length===5&&inputs.every(f=>JSON.parse(fs.readFileSync(f,'utf8')).partition==='calibration-excluded')){
 const receipt={code_sha256:CODE_HASH,passed:5,failed:0,engine:VERSION,results};fs.writeFileSync(path.join(STUDY,'PUPPET_INPUT_VALIDATION.json'),JSON.stringify(receipt,null,2)+'\n');
}
