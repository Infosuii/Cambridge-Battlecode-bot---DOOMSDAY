// Outcome-only mechanics audit. No opponent code or bot prediction inputs.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {engine,defaultAssets,verifyAssets} from './replay/engine.mjs';
if(process.env.NFS_REPLAY_ENGINE!=='2.0.0')throw new Error('Select pinned engine2.0.0');
const [file,bodyText,output,lastText='500']=process.argv.slice(2),body=Number(bodyText),last=Number(lastText);
if(!output||!Number.isInteger(body)||body<0||!Number.isInteger(last)||last<1)throw new Error('Usage: replay body output [last_round]');
if(fs.existsSync(output))throw new Error('Refuse to overwrite completed mechanics audit');
const assets=defaultAssets();verifyAssets(assets);const E=await engine(assets),{X,check,dv,out,tsnap}=E;
E.load(fs.readFileSync(file));
check(X.Game_API_Champion_Design(E.h,10,E.buf));
const abilities=Array.from({length:2},(_,slot)=>({slot,kind:dv().getUint32(E.buf+12+36*slot,true),
  cooldown:dv().getInt32(E.buf+16+36*slot,true),modifier:dv().getFloat32(E.buf+36+36*slot,true),
  duration:dv().getInt32(E.buf+40+36*slot,true)}));
if(abilities[0].kind!==1||abilities[1].kind!==7)throw new Error('Pinned Varg ability ABI mismatch');
check(X.Game_Visualiser_Timeline_GetMain(E.h,out));check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
const actions=new Map(),casts=new Set(),shieldEvents=[],turns=[];
let previous=null,previousBuff=null,lastTurn=-1,frames=0,ended=false;
function shield(c) {
  if(!c.alive)return null;
  check(X.Game_API_Champion_GetBuffData(E.h,E.perspective(c.team,body),body,E.buf,64,out));
  const count=dv().getUint32(out,true);if(count>64)throw new Error('Buff buffer overflow');
  const shields=[];
  for(let i=0;i<count;++i)if(dv().getUint32(E.buf+12*i,true)===0)shields.push({duration:dv().getInt32(E.buf+12*i+4,true),value:dv().getFloat32(E.buf+12*i+8,true)});
  if(shields.length>1)throw new Error('Stacked shields need separate accounting');
  return shields[0]??null;
}
for(;frames<2000000;++frames) {
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const s=E.PC.I(dv(),tsnap);
  if(s.round>last||s.outcome!==0){ended=true;break;}
  const c=s.champions.find(c=>c.entity.index===body);
  if(c) {
    if(c.type!==10)throw new Error('Selected body is not Varg');
    const buff=shield(c),old=previous?.champions.find(c=>c.entity.index===body);
    const before=new Map((previous?.camps??[]).map(c=>[c.entity.index,c]));
    const own=s.step?.actor.kind===1&&s.step.actor.index===body;
    const key=s.step?`${s.step.round}:${s.step.inputPosition}`:'';
    if(own&&s.step.kind===5&&previous) {
      const targets=previous.camps.filter(c=>c.health>0&&c.position.x===s.step.to.x&&c.position.y===s.step.to.y);
      if(!actions.has(key)&&targets.length===1) {
        const primary=targets[0];
        const candidates=previous.camps.filter(c=>c.health>0&&Math.max(Math.abs(c.position.x-s.step.to.x),Math.abs(c.position.y-s.step.to.y))<=1)
          .map(c=>({id:c.entity.index,type:c.type,hp:c.health,dx:c.position.x-s.step.to.x,dy:c.position.y-s.step.to.y}));
        actions.set(key,{round:s.round,input:s.step.inputPosition,primary:primary.entity.index,candidates,loss:{}});
      }
      const action=actions.get(key);
      if(action)for(const camp of s.camps) {
        const loss=Math.max(0,(before.get(camp.entity.index)?.health??camp.health)-camp.health);
        if(loss>.01)action.loss[camp.entity.index]=(action.loss[camp.entity.index]??0)+loss;
      }
    }
    if(own&&s.step.kind===6&&s.step.abilityType===7&&!casts.has(key)) {
      casts.add(key);shieldEvents.push({kind:'cast',round:s.round,input:s.step.inputPosition,buff});
    }
    if(JSON.stringify(buff)!==JSON.stringify(previousBuff)) {
      const hpLoss=old?Math.max(0,old.health-c.health):0;
      shieldEvents.push({kind:'change',round:s.round,phase:s.phase,step:s.step,before:previousBuff,after:buff,hp_loss:hpLoss,
        disappeared:c.alive&&previousBuff!==null&&buff===null});
    }
    if(s.phase===14&&s.currentChampion===body&&s.round!==lastTurn&&c.alive) {
      const perspective=E.perspective(c.team,body),cooldowns=[];
      for(let slot=0;slot<2;++slot){check(X.Game_API_Champion_GetCooldown(E.h,perspective,body,slot,out));cooldowns.push(dv().getInt32(out,true));}
      check(X.Game_API_Champion_GetAbilityShield(E.h,perspective,body,1,out));
      turns.push({round:s.round,hp:c.health,max_hp:c.maxHealth,buff,cooldowns,shield_amount:dv().getFloat32(out,true)});lastTurn=s.round;
    }
    previousBuff=buff;
  }
  previous=s;check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
}
if(!ended)throw new Error('Timeline audit incomplete');
const basics=[...actions.values()].filter(a=>(a.loss[a.primary]??0)>0);
let collateral=0,diagonal=0,fullDamageChecks=0;const anomalies=[];
for(const a of basics) {
  const primary=a.candidates.find(c=>c.id===a.primary),hit=a.loss[a.primary];
  for(const [id,loss] of Object.entries(a.loss))if(Number(id)!==a.primary) {
    ++collateral;const target=a.candidates.find(c=>c.id===Number(id));
    if(!target)anomalies.push({kind:'outside_radius',round:a.round,input:a.input,id,loss});
    else if(Math.abs(target.dx)===1&&Math.abs(target.dy)===1)++diagonal;
  }
  if(primary.hp>hit+.03)for(const target of a.candidates)if(target.id!==a.primary) {
    ++fullDamageChecks;const expected=Math.min(target.hp,hit),actual=a.loss[target.id]??0;
    if(Math.abs(expected-actual)>.03)anomalies.push({kind:'collateral_amount',round:a.round,input:a.input,target,expected,actual});
  }
}
const disappearance=shieldEvents.filter(e=>e.kind==='change'&&e.disappeared);
const result={scope:'Retrospective mechanics audit, not prospective model validation or strength evidence',body,last_round:last,frames,abilities,
  summary:{camp_target_basics:basics.length,collateral_camp_hits:collateral,diagonal_camp_hits:diagonal,
    full_damage_checks:fullDamageChecks,anomalies:anomalies.length,shield_casts:casts.size,
    vanished_after_zero_duration:disappearance.filter(e=>e.before.duration===0).length,
    vanished_with_positive_duration:disappearance.filter(e=>e.before.duration>0).length},anomalies,basics,shield_events:shieldEvents,turns,
  source:{replay_sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),
    reader_sha256:crypto.createHash('sha256').update(fs.readFileSync(new URL(import.meta.url))).digest('hex'),engine:'2.0.0'}};
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result.summary));E.destroy();
