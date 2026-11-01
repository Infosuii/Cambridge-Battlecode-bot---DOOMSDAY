// Focused first-250-round reference: ordered native actions plus personal views.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {engine,defaultAssets,verifyAssets} from './replay/engine.mjs';
if(process.env.NFS_REPLAY_ENGINE!=='2.0.0')throw new Error('Select engine 2.0.0');
const [file,output]=process.argv.slice(2),assets=defaultAssets();verifyAssets(assets);
const E=await engine(assets),bytes=fs.readFileSync(file);E.load(bytes);
try {
 const {X,dv,check,out,tsnap}=E;check(X.Game_Visualiser_Timeline_GetMain(E.h,out));
 check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
 const turns=[],actions=[],seen=new Set();let last='',groups,initial;
 for(let n=0;n<1000000;++n) {
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const s=E.PC.I(dv(),tsnap);
  if(s.round>250)break;
  if(!initial&&s.champions.length){initial=s.champions;groups=s.groups;}
  const a=s.step,key=JSON.stringify([a.round,a.inputPosition,a.substep,a.kind,a.actor]);
  if(a.actor.kind===1&&[4,5,6,11,12,13,18,23].includes(a.kind)&&!seen.has(key)) {
   seen.add(key);actions.push(a);
  }
  const turn=`${s.round}:${s.currentChampion}`;
  if(s.phase===14&&turn!==last) {
   last=turn;const me=s.champions.find(c=>c.entity.index===s.currentChampion);
   if(me&&me.alive&&me.position) {
    check(X.Game_Visualiser_ReadState(E.h,E.perspective(me.team,me.entity.index),E.snap));
    const v=E.PC.F(dv(),E.snap);
    turns.push({round:s.round,body:me.entity.index,view:v});
   }
  }
  const rc=X.Game_Visualiser_Timeline_ReplayNext(E.h,1);if(rc===18)break;check(rc);
 }
 const result={replay_sha256:crypto.createHash('sha256').update(bytes).digest('hex'),engine:'2.0.0',
  initial,groups,turns,actions,note:'Personal views are legal actor perspectives; initial roster/group metadata is offline reference only. Native event 23 is blocked movement, not a dash.'};
 fs.writeFileSync(output,JSON.stringify(result,(k,v)=>typeof v==='bigint'?v.toString():v));console.log(JSON.stringify({turns:turns.length,actions:actions.length,output}));
} finally {E.destroy();}
