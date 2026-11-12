// EXP278: independent official-engine replay HP/action accounting.
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from '../../tools/replay/engine.mjs';
if(process.env.NFS_REPLAY_ENGINE!=='3.0.0')throw new Error('Explicit engine3 required');
const [input,output]=process.argv.slice(2),jobs=JSON.parse(fs.readFileSync(input,'utf8'));
const assets=defaultAssets();verifyAssets(assets);const E=await engine(assets),rows=[];
for(const job of jobs){
 E.load(fs.readFileSync(job.replay));const {X,check,dv,out,tsnap}=E;
 check(X.Game_Visualiser_Timeline_GetMain(E.h,out));check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
 let previous=null;const attacks=new Map(),casts=new Map();
 for(;;){
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const s=E.PC.I(dv(),tsnap),k=s.step;
  if(k.actor.kind===1&&(k.kind===5||k.kind===6)){
   const id=`${k.round}:${k.inputPosition}:${k.actor.index}:${k.kind}:${k.to.x}:${k.to.y}`;
   const records=k.kind===5?attacks:casts;
   if(!records.has(id))records.set(id,{actor:k.actor.index,round:k.round,from:k.from,to:k.to,damage:[]});
   if(previous)for(const camp of s.camps){
    const before=previous.camps.find(c=>c.entity.index===camp.entity.index);
    if(before&&before.health>camp.health+.001)records.get(id).damage.push({id:camp.entity.index,before:before.health,after:camp.health,position:before.position});
   }
  }
  previous=s;if(s.outcome)break;check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
 }
 rows.push({...job,replay:undefined,attacks:[...attacks.values()],casts:[...casts.values()]});E.destroy();
}
fs.writeFileSync(output,JSON.stringify({games:rows.length,rows},(k,v)=>typeof v==='bigint'?v.toString():v,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({games:rows.length,attacks:rows.map(r=>r.attacks.length),casts:rows.map(r=>r.casts.length)}));
