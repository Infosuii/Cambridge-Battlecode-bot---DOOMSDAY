// EXP235 preselected real replay events; offline accounting only.
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from '../../tools/replay/engine.mjs';
const [input,output]=process.argv.slice(2);
if(process.env.NFS_REPLAY_ENGINE!=='3.0.0')throw new Error('Requires explicit engine3');
const jobs=JSON.parse(fs.readFileSync(input,'utf8'));
const assets=defaultAssets();verifyAssets(assets);const E=await engine(assets);
const distance=(a,b)=>Math.max(Math.abs(a.x-b.x),Math.abs(a.y-b.y));
const rows=[];
for(const job of jobs) {
  E.load(fs.readFileSync(job.replay));
  const {X,check,dv,out,tsnap}=E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h,out));
  check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
  let previous=null,positionChanges=0;const casts=new Map();
  for(;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const s=E.PC.I(dv(),tsnap);
    const k=s.step,actor=s.champions.find(c=>c.entity.index===job.actor_id);
    const beforeActor=previous?.champions.find(c=>c.entity.index===job.actor_id);
    if(s.round>300)break;
    if(beforeActor?.alive&&actor?.alive&&distance(beforeActor.position,actor.position)>0)++positionChanges;
    const slot=job.role==='ryth'?0:1;
    if(job.role!=='marcella'&&k.kind===6&&k.actor.kind===1&&k.actor.index===job.actor_id&&k.abilitySlot===slot) {
      const id=`${k.round}:${k.inputPosition}:${k.actor.index}:${slot}:${k.to.x}:${k.to.y}`;
      const origin=beforeActor?.position??actor?.position;
      if(!origin)throw new Error('Missing cast origin');
      if(!casts.has(id))casts.set(id,{round:k.round,slot,from:origin,aim:k.to,centre_distance:distance(origin,k.to),damage:0,damaged_camps:[]});
      const cast=casts.get(id);
      if(previous)for(const c of s.camps) {
        const before=previous.camps.find(p=>p.entity.index===c.entity.index);
        const loss=Math.max(0,(before?.health??c.health)-c.health);
        if(loss>.001) {
          cast.damage+=loss;
          cast.damaged_camps.push({id:c.entity.index,loss,before_position:before.position,distance_from_caster:distance(origin,before.position)});
        }
      }
    }
    previous=s;
    if(s.outcome)break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
  }
  const events=[...casts.values()];
  if(events.some(e=>e.centre_distance>4))throw new Error('AOE centre beyond actual range');
  rows.push({...job,replay:undefined,position_changes:positionChanges,aoe_casts:events.length,
    direct_step_damage:events.reduce((n,e)=>n+e.damage,0),
    casts_damaging_beyond4:events.filter(e=>e.damaged_camps.some(c=>c.distance_from_caster>4)).length,
    casts_damaging_multiple:events.filter(e=>new Set(e.damaged_camps.map(c=>c.id)).size>1).length,events});
  E.destroy();
}
fs.writeFileSync(output,JSON.stringify({games:rows.length,scope:'Preselected artificial-fixture direct cast-step health accounting; non-cast-step effects may be omitted, no strength claim.',rows},(k,v)=>typeof v==='bigint'?v.toString():v,2)+'\n',{flag:'wx'});
console.log(JSON.stringify(rows.map(({role,mode,map,side,aoe_casts,direct_step_damage,casts_damaging_beyond4,casts_damaging_multiple})=>({role,mode,map,side,aoe_casts,direct_step_damage,casts_damaging_beyond4,casts_damaging_multiple}))));
