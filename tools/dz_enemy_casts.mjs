// Retrospective opponent-policy evidence only. Full replay owner views are
// analysis context, never inputs supplied to the live bot or proof of intent.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {engine,defaultAssets,verifyAssets} from './replay/engine.mjs';
if(process.env.NFS_REPLAY_ENGINE!=='2.0.0')throw new Error('Select pinned engine2.0.0');
const [file,teamText,output,lastText='500']=process.argv.slice(2),team=Number(teamText),last=Number(lastText);
if(!output||![0,1].includes(team)||!Number.isInteger(last)||last<1||fs.existsSync(output))throw new Error('Usage: replay opponent_team fresh_output [last_round]');
const assets=defaultAssets();verifyAssets(assets);const E=await engine(assets),{X,check,dv,out,tsnap}=E;
E.load(fs.readFileSync(file));check(X.Game_Visualiser_Timeline_GetMain(E.h,out));check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
const turns=[],byTurn=new Map(),seenActions=new Set(),lastBasic=new Map();let previous=null,ended=false;
function owner(c){
  const p=E.perspective(c.team,c.entity.index);check(X.Game_API_Champion_Get(E.h,p,c.entity.index,E.buf));
  const hp=dv().getFloat32(E.buf+16,true),maxHp=dv().getFloat32(E.buf+20,true),state=dv().getUint32(E.buf+40,true);
  if(dv().getInt32(E.buf+4,true)!==c.type||Math.abs(hp-c.health)>.01||maxHp!==c.maxHealth)throw new Error('Owner stats ABI mismatch');
  const cooldowns=[];for(let slot=0;slot<2;++slot){check(X.Game_API_Champion_GetCooldown(E.h,p,c.entity.index,slot,out));cooldowns.push(dv().getInt32(out,true));}
  check(X.Game_API_Champion_GetRestrictions(E.h,p,c.entity.index,out));const restrictions=dv().getUint8(out);
  check(X.Game_API_Champion_GetBuffData(E.h,p,c.entity.index,E.buf,64,out));const n=dv().getUint32(out,true);if(n>64)throw new Error('Buff buffer overflow');
  const shields=[];for(let i=0;i<n;++i)if(dv().getUint32(E.buf+12*i,true)===0)shields.push({duration:dv().getInt32(E.buf+12*i+4,true),value:dv().getFloat32(E.buf+12*i+8,true)});
  const shieldSlot=c.type===10?1:0;
  return {hp,max_hp:maxHp,hp_fraction:hp/maxHp,state,restrictions,cooldowns,shields,
    ready_by_start_fields:!!(state&2048)&&!(state&(2|4|4096))&&!(restrictions&4)&&cooldowns[shieldSlot]===0&&!shields.length};
}
for(let frame=0;frame<2000000;++frame){
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const s=E.PC.I(dv(),tsnap);
  if(s.round>last||s.outcome!==0){ended=true;break;}
  const me=s.champions.find(c=>c.entity.index===s.currentChampion),key=`${s.round}:${s.currentChampion}`;
  if(s.phase===14&&me?.alive&&me.team===team&&[10,12].includes(me.type)&&!byTurn.has(key)){
    const r={round:s.round,body:me.entity.index,type:me.type,start:owner(me),basics:[],casts:[]};turns.push(r);byTurn.set(key,r);
  }
  const step=s.step;
  if(s.phase===10&&step?.actor.kind===1){
    const c=s.champions.find(c=>c.entity.index===step.actor.index),r=byTurn.get(`${step.round}:${step.actor.index}`);
    if(c?.team===team&&r){
      const action=`${step.round}:${step.actor.index}:${step.inputPosition}`;
      if(step.kind===5){
        if(!seenActions.has(action)){
          seenActions.add(action);const champion=previous?.champions.find(t=>t.alive&&t.position.x===step.to.x&&t.position.y===step.to.y),
            camp=previous?.camps.find(t=>t.health>0&&t.position.x===step.to.x&&t.position.y===step.to.y),target=champion??camp;
          const b={input:step.inputPosition,target_kind:champion?'champion':camp?'camp':'unknown',target_id:target?.entity.index??null,target_type:target?.type??null,
            hp_after:c.health,hp_fraction_after:c.health/c.maxHealth,target_alive_after:null};r.basics.push(b);lastBasic.set(action,b);
        }
        const b=lastBasic.get(action);if(b){
          b.hp_after=c.health;b.hp_fraction_after=c.health/c.maxHealth;
          const list=b.target_kind==='champion'?s.champions:s.camps,t=list.find(t=>t.entity.index===b.target_id);
          b.target_alive_after=b.target_kind==='champion'?!!t?.alive:(t?.health??0)>0;
        }
      }
      if(step.kind===6&&!seenActions.has(action)){
        seenActions.add(action);r.casts.push({input:step.inputPosition,kind:step.abilityType,hp:c.health,max_hp:c.maxHealth,hp_fraction:c.health/c.maxHealth,
          basics_before:r.basics.length,last_basic:r.basics.length?structuredClone(r.basics.at(-1)):null});
      }
    }
  }
  previous=s;check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
}
if(!ended)throw new Error('Incomplete policy audit');
const result={scope:'Retrospective owner-view policy observations; not live inputs, causal intent or prospective model validation',opponent_team:team,last_round:last,turns,
  source:{replay_sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),reader_sha256:crypto.createHash('sha256').update(fs.readFileSync(new URL(import.meta.url))).digest('hex'),engine:'2.0.0',pinned_assets_verified:true}};
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({turns:turns.length,shields:turns.reduce((n,r)=>n+r.casts.filter(c=>c.kind===7).length,0),resets:turns.reduce((n,r)=>n+r.casts.filter(c=>c.kind===1).length,0)}));E.destroy();
