// Retrospective mechanics checks only; never bot inputs or prospective accuracy.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {engine,defaultAssets,verifyAssets} from './replay/engine.mjs';
if(process.env.NFS_REPLAY_ENGINE!=='2.0.0')throw new Error('Select pinned engine2.0.0');
const [file,bodyText,output,lastText='500']=process.argv.slice(2),body=Number(bodyText),last=Number(lastText);
if(!output||!Number.isInteger(body)||body<0||!Number.isInteger(last)||last<1)throw new Error('Usage: replay body output [last_round]');
if(fs.existsSync(output))throw new Error('Refuse to overwrite a completed mechanics audit');
const assets=defaultAssets();verifyAssets(assets);const E=await engine(assets),{X,check,dv,out,tsnap}=E;
E.load(fs.readFileSync(file));check(X.Game_API_Champion_Design(E.h,12,E.buf));
const passive=dv().getUint8(E.buf+8),campMultiplier=dv().getFloat32(E.buf+124,true);
const abilities=Array.from({length:2},(_,slot)=>{
  const p=E.buf+12+36*slot,kind=dv().getUint32(p,true);
  const a={slot,kind,cooldown:dv().getInt32(p+4,true),targets:dv().getUint32(p+12,true),attributes:dv().getUint32(p+16,true)};
  if(kind===7)Object.assign(a,{range:dv().getFloat32(p+20,true),modifier:dv().getFloat32(p+24,true),duration:dv().getInt32(p+28,true)});
  else if(kind===6)Object.assign(a,{range:dv().getFloat32(p+20,true),radius:dv().getFloat32(p+24,true),modifier:dv().getFloat32(p+28,true),duration:dv().getInt32(p+32,true)});
  else throw new Error('Unexpected Heart ability kind');return a;
});
if(passive!==10||!Number.isFinite(campMultiplier)||campMultiplier<=0)throw new Error('Pinned Heart design ABI mismatch');
check(X.Game_Visualiser_Timeline_GetMain(E.h,out));check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
let previous=null,previousInfo=null,ended=false,frames=0;
const actions=new Map(),casts=new Set(),shieldEvents=[];let previousShield=null;
function info(c) {
  if(!c.alive)return null;
  check(X.Game_API_Champion_Get(E.h,E.perspective(c.team,body),body,E.buf));
  const v={hp:dv().getFloat32(E.buf+16,true),max_hp:dv().getFloat32(E.buf+20,true),
    strength:dv().getFloat32(E.buf+24,true),focus:dv().getFloat32(E.buf+28,true)};
  if(dv().getInt32(E.buf+4,true)!==12||Math.abs(v.hp-c.health)>.01||v.max_hp!==c.maxHealth)throw new Error('Heart live-stats ABI mismatch');
  const monster=[1,3,5].some(i=>c.items[i]>0)?1.15:1; // public SDK IDs and nonstacking15% emblem passive
  v.damage=v.strength*campMultiplier*monster*(1+.5*(1-v.hp/v.max_hp));v.monster=monster;return v;
}
function shield(c) {
  if(!c.alive)return null;
  check(X.Game_API_Champion_GetBuffData(E.h,E.perspective(c.team,body),body,E.buf,64,out));
  const n=dv().getUint32(out,true);if(n>64)throw new Error('Buff buffer overflow');
  const buffs=[];for(let i=0;i<n;++i)if(dv().getUint32(E.buf+12*i,true)===0)
    buffs.push({duration:dv().getInt32(E.buf+12*i+4,true),value:dv().getFloat32(E.buf+12*i+8,true)});
  if(buffs.length>1)throw new Error('Stacked shields need separate accounting');return buffs[0]??null;
}
for(;frames<2000000;++frames) {
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const s=E.PC.I(dv(),tsnap);
  if(s.round>last||s.outcome!==0){ended=true;break;}
  const c=s.champions.find(c=>c.entity.index===body);let currentInfo=null;
  if(c) {
    if(c.type!==12)throw new Error('Selected body is not Heart');
    currentInfo=info(c);const buff=shield(c),own=s.step?.actor.kind===1&&s.step.actor.index===body;
    const key=s.step?`${s.step.round}:${s.step.inputPosition}`:'';
    if(own&&s.step.kind===5&&previous&&previousInfo) {
      const targets=previous.camps.filter(c=>c.health>0&&c.position.x===s.step.to.x&&c.position.y===s.step.to.y);
      if(!actions.has(key)&&targets.length===1)actions.set(key,{round:s.round,input:s.step.inputPosition,
        target:targets[0].entity.index,target_hp:targets[0].health,info:previousInfo,loss:0});
      const a=actions.get(key);if(a) {
        const before=previous.camps.find(c=>c.entity.index===a.target),after=s.camps.find(c=>c.entity.index===a.target);
        a.loss+=Math.max(0,(before?.health??0)-(after?.health??0));
      }
    }
    if(own&&s.step.kind===6&&s.step.abilityType===7&&!casts.has(key)) {
      casts.add(key);shieldEvents.push({kind:'cast',round:s.round,input:s.step.inputPosition,buff});
    }
    if(JSON.stringify(buff)!==JSON.stringify(previousShield))shieldEvents.push({kind:'change',round:s.round,
      phase:s.phase,step:s.step,before:previousShield,after:buff,disappeared:c.alive&&previousShield!==null&&buff===null});
    previousShield=buff;
  }
  previous=s;previousInfo=currentInfo;check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
}
if(!ended)throw new Error('Incomplete timeline');
const basics=[...actions.values()].filter(a=>a.loss>0),anomalies=[];
for(const a of basics) {
  a.expected=Math.min(a.target_hp,a.info.damage);a.error=a.loss-a.expected;
  if(Math.abs(a.error)>.03)anomalies.push(a);
}
const disappear=shieldEvents.filter(e=>e.kind==='change'&&e.disappeared);
const result={scope:'Retrospective native mechanics; not prospective forecast validation, policy or strength evidence',body,last_round:last,frames,
  metadata:{passive,campMultiplier,abilities,missing_health_max_bonus:.5,monster_emblem_bonus:.15},
  summary:{camp_basics:basics.length,damaged_hp_basics:basics.filter(a=>a.info.hp<a.info.max_hp).length,
    monster_emblem_basics:basics.filter(a=>a.info.monster>1).length,anomalies:anomalies.length,shield_casts:casts.size,
    vanished_after_zero_duration:disappear.filter(e=>e.before.duration===0).length,
    vanished_with_positive_duration:disappear.filter(e=>e.before.duration>0).length},basics,anomalies,shield_events:shieldEvents,
  source:{replay_sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),
    reader_sha256:crypto.createHash('sha256').update(fs.readFileSync(new URL(import.meta.url))).digest('hex'),engine:'2.0.0'}};
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result.summary));E.destroy();
