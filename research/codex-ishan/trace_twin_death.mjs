// Offline exact engine-step health transitions for a frozen discovery twin event.
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from '../../tools/replay/engine.mjs';
const [manifest,output]=process.argv.slice(2);
if(!output||process.env.NFS_REPLAY_ENGINE!=='3.0.0')throw Error('Need engine3,case manifest,output');
const c=JSON.parse(fs.readFileSync(manifest,'utf8'));
const assets=defaultAssets();verifyAssets(assets);const E=await engine(assets);
E.load(fs.readFileSync(c.replay));
const {X,check,dv,out,tsnap}=E;
check(X.Game_Visualiser_Timeline_GetMain(E.h,out));
check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
let previous;const transitions=[];
for(;;){
 check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const s=E.PC.I(dv(),tsnap);
 if((s.phase!==12&&s.round>c.round+1)||s.outcome)break;
 if(s.phase!==12&&s.round>=c.round-8){
  const twins=s.champions.filter(x=>x.team===c.team&&[3,4].includes(x.type)).map(x=>({id:x.entity.index,type:x.type,alive:x.alive,hp:x.health,max_hp:x.maxHealth,pos:x.position,gems:x.gems,gold:x.gold}));
  const value=JSON.stringify(twins);
  if(value!==previous){transitions.push({round:s.round,phase:s.phase,input:s.inputPosition,step:s.step,twins});previous=value;}
 }
 check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
}
E.destroy();
fs.writeFileSync(output,JSON.stringify({case:c,transitions},(_,v)=>typeof v==='bigint'?v.toString():v,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({match:c.matchId,transitions:transitions.length}));
