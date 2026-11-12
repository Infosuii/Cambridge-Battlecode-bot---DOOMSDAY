// EXP286: read-only official runtime map ABI, using public SDK imports.h layouts.
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets,PINNED} from '../../tools/replay/engine.mjs';
if(process.env.NFS_REPLAY_ENGINE!=='3.0.0')throw new Error('Explicit engine3 required');
const [input,output]=process.argv.slice(2),jobs=JSON.parse(fs.readFileSync(input,'utf8'));
const assets=defaultAssets();verifyAssets(assets);const E=await engine(assets),rows=[];
const arities={Game_API_Map_GetNumCampGroups:2,Game_API_Map_GetCampGroups:4,Game_API_Map_CampGroup_GetNumCamps:3,
 Game_API_Map_CampGroup_GetCampInfo:5,Game_API_Map_CampGroup_Get:3,Game_API_Map_CampInfo_Get:3,
 Game_API_Map_CampInfo_GetGroup:3,Game_API_Map_CampGroup_GetRespawnTime:3};
for(const [n,a] of Object.entries(arities))if(E.X[n]?.length!==a)throw new Error('Unexpected ABI '+n);
for(const job of jobs){
 E.load(fs.readFileSync(job.replay));const {X,check,dv,out,args,buf,tsnap}=E;
 check(X.Game_API_Map_GetNumCampGroups(E.h,out));const n=dv().getUint32(out,true);if(n>1024)throw new Error('Group capacity');
 check(X.Game_API_Map_GetCampGroups(E.h,buf,1024,out));if(dv().getUint32(out,true)!==n)throw new Error('Group count');
 const ids=Array.from({length:n},(_,i)=>dv().getUint32(buf+4*i,true)),groups=[];
 for(const id of ids){
  check(X.Game_API_Map_CampGroup_Get(E.h,id,args));const g={handle:id,gems:dv().getUint32(args,true),gold:dv().getUint32(args+4,true)};
  check(X.Game_API_Map_CampGroup_GetRespawnTime(E.h,id,out));g.respawn=dv().getInt32(out,true);
  check(X.Game_API_Map_CampGroup_GetNumCamps(E.h,id,out));g.count=dv().getUint32(out,true);if(g.count>1024)throw new Error('Camp capacity');
  check(X.Game_API_Map_CampGroup_GetCampInfo(E.h,id,buf,1024,out));if(dv().getUint32(out,true)!==g.count)throw new Error('Camp count');
  const camps=Array.from({length:g.count},(_,i)=>dv().getUint32(buf+4*i,true));g.camps=[];
  for(const cid of camps){
   check(X.Game_API_Map_CampInfo_Get(E.h,cid,args));const c={handle:cid,x:dv().getInt32(args,true),y:dv().getInt32(args+4,true),type:dv().getInt32(args+8,true)};
   check(X.Game_API_Map_CampInfo_GetGroup(E.h,cid,out));if(dv().getUint32(out,true)!==id)throw new Error('Membership');g.camps.push(c);
  }
  groups.push(g);
 }
 check(X.Game_Visualiser_Timeline_GetMain(E.h,out));check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
 check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const snap=E.PC.I(dv(),tsnap);
 if(snap.groups.length!==groups.length)throw new Error('Snapshot groups');
 const camps=groups.flatMap(g=>g.camps);if(camps.length!==snap.camps.length)throw new Error('Snapshot camps');
 for(const c of camps){const s=snap.camps.find(s=>s.entity.index===c.handle);if(!s||s.type!==c.type||s.position.x!==c.x||s.position.y!==c.y)throw new Error('Snapshot camp mismatch');}
 rows.push({...job,replay:undefined,groups,initial_snapshot_camps_match:true});E.destroy();
}
fs.writeFileSync(output,JSON.stringify({engine_assets:PINNED,arities,games:rows.length,rows},null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({games:rows.length,groups:rows.reduce((n,r)=>n+r.groups.length,0)}));
