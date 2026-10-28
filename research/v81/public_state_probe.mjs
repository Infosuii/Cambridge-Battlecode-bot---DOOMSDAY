// Read-only legal-perspective query audit. No spectator data is provided to the perspective calls.
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from '../../tools/replay/engine.mjs';
const [file,at='200']=process.argv.slice(2);const dir=defaultAssets();verifyAssets(dir);const E=await engine(dir);
E.load(fs.readFileSync(file));const {X,check,dv,out:o,args,tsnap}=E,u=p=>dv().getUint32(p,true);
check(X.Game_Visualiser_Timeline_GetMain(E.h,o));const main=dv().getBigUint64(o,true);
check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
for(;;){
 check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));
 if(u(tsnap+8)>=Number(at) && u(tsnap+24)===10 && u(tsnap+20)!==0){
  const c=u(tsnap+60);check(X.Game_API_Champion_GetIdentity(E.h,E.perspective(2,0xffffffff),c,o));const team=dv().getInt32(o,true),P=E.perspective(team,c);
  check(X.Game_Visualiser_ReadState(E.h,P,E.snap));const view=E.PC.F(dv(),E.snap);
  check(X.Game_API_Map_GetNumCampGroups(E.h,o));const n=u(o);check(X.Game_API_Map_GetCampGroups(E.h,E.buf+2048,256,o));
  const handles=[...new Uint32Array(X.memory.buffer,E.buf+2048,n)];
  const rows=handles.map(g=>{const state=X.Game_API_CampGroup_GetState(E.h,P,g,o),sv=state===0?u(o):null;
   const cap=X.Game_API_CampGroup_GetCaptureState(E.h,P,g,o),cv=cap===0?[dv().getInt32(o,true),dv().getInt32(o+4,true)]:null;
   return {g,state_rc:state,state:sv,capture_rc:cap,capture:cv};});
  console.log(JSON.stringify({round:u(tsnap+8),champion:c,visible_camps:view.camps.filter(x=>x.position).length,total_groups:n,rows}));break;
 }
 if(u(tsnap+28))break;check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
}E.destroy();
