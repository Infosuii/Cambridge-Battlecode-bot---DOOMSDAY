// Per ladder replay: runs of rounds in which a camp group's reward stays available, by captureTeam value.
// Usage: node group_stalls.mjs out.json replay1 [replay2 ...]   (engine 3.0.0 pinned assets via engine.mjs)
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from './engine.mjs';
const [output,...files]=process.argv.slice(2);
const dir=defaultAssets();verifyAssets(dir);const E=await engine(dir);
const res=[];
for(const f of files){
 E.load(fs.readFileSync(f));const {X,check,dv,out,tsnap}=E;
 check(X.Game_Visualiser_Timeline_GetMain(E.h,out));const main=dv().getBigUint64(out,true);
 check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
 let last=-1,steps=0;const runs=[];const open=new Map();
 for(;;){check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const d=dv();
  const round=d.getUint32(tsnap+8,true),phase=d.getUint32(tsnap+24,true),outcome=d.getUint32(tsnap+28,true);
  if((round!==last&&phase===10)||outcome){
   const s=E.PC.I(d,tsnap);
   s.groups.forEach((g,i)=>{
    const key=g.rewardAvailable?String(g.captureTeam):null;
    const cur=open.get(i);
    if(cur&&cur.key!==key){runs.push({group:i,ct:cur.key,start:cur.start,end:round});open.delete(i);}
    if(key!==null&&!open.has(i))open.set(i,{key,start:round});
   });
   last=round;if(outcome)break;
  }
  if(++steps>3000000)break;
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
 }
 for(const [i,c] of open)runs.push({group:i,ct:c.key,start:c.start,end:last});
 res.push({file:f.split(/[\/]/).pop(),rounds:last,runs:runs.filter(r=>r.end-r.start>=3)});
 console.log(f.split(/[\/]/).pop(),last,runs.length);
}
fs.writeFileSync(output,JSON.stringify(res));
