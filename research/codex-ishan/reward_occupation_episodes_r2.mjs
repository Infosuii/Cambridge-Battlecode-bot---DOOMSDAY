// EXP289 read-only public occupation census; no unknown API signatures or game edits.
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from '../../tools/replay/engine.mjs';
if(process.env.NFS_REPLAY_ENGINE!=='3.0.0')throw new Error('Explicit engine3');
const [input,output]=process.argv.slice(2),jobs=JSON.parse(fs.readFileSync(input,'utf8'));
const assets=defaultAssets();verifyAssets(assets);const E=await engine(assets),rows=[];
for(const job of jobs){
 E.load(fs.readFileSync(job.replay));const {X,check,dv,out,tsnap}=E;
 check(X.Game_Visualiser_Timeline_GetMain(E.h,out));check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
 const tiles=job.groups.map(g=>new Set(g.camps.map(c=>`${c.x},${c.y}`)));
 if(job.groups.some((g,i)=>g.handle!==i))throw new Error('Non-indexed groups unsupported');
 const active=new Map(),episodes=[],actions=new Map();let previous=null,lastRound=-1,samples=0,missing=0;
 const end=(gid,censored=false)=>{const e=active.get(gid);if(e){e.censored=censored;e.duration=e.end-e.start+1;episodes.push(e);active.delete(gid);}};
 function finish(next){
  if(!previous)return;
  const s=previous;
  for(let gi=0;gi<job.groups.length;++gi){
   const onsite=s.champions.filter(c=>c.alive&&c.position&&tiles[gi].has(`${c.position.x},${c.position.y}`));
   const counts=[0,1].map(t=>onsite.filter(c=>c.team===t).length);
   if(!s.groups[gi].rewardAvailable||counts.some(n=>n===0)){end(gi);continue;}
   if(active.has(gi)&&active.get(gi).end+1!==s.round)end(gi,true);
   if(!active.has(gi))active.set(gi,{group:gi,base_gems:job.groups[gi].gems,members:job.groups[gi].count,start:s.round,end:s.round,
      occupant_rounds:[0,0],extra_occupant_rounds:[0,0],stationary_resource_flat_no_known_action:[0,0],missing_resource_samples:0});
   const e=active.get(gi);e.end=s.round;
   for(let t=0;t<2;++t){e.occupant_rounds[t]+=counts[t];e.extra_occupant_rounds[t]+=Math.max(0,counts[t]-1);}
   for(const c of onsite){
    if(!next){++missing;++e.missing_resource_samples;continue;}
    const after=next?.champions.find(a=>a.entity.index===c.entity.index),key=`${s.round}:${c.entity.index}`;
    if(!after?.alive||!after.position)continue;
    if(['health','gold','gems'].some(k=>!Number.isFinite(c[k])||!Number.isFinite(after[k]))){++missing;++e.missing_resource_samples;continue;}
    if(!actions.has(key)&&c.position.x===after.position.x&&c.position.y===after.position.y&&['health','gold','gems'].every(k=>c[k]===after[k]))++e.stationary_resource_flat_no_known_action[c.team];
   }
  }
  ++samples;
 }
 for(;;){
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const d=dv(),round=d.getUint32(tsnap+8,true),phase=d.getUint32(tsnap+24,true),outcome=d.getUint32(tsnap+28,true),kind=d.getUint32(tsnap+68,true);
  let snap=null;
  if([4,5,6,23].includes(kind)){snap=E.PC.I(d,tsnap);const k=snap.step;if(k.actor.kind===1)actions.set(`${k.round}:${k.actor.index}`,true);}
  if((phase===10&&round!==lastRound)||outcome){
   snap??=E.PC.I(d,tsnap);finish(outcome?null:snap);
   if(outcome||round>800){previous=null;break;}
   previous=snap;lastRound=round;
  }
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
 }
 for(const gi of [...active.keys()])end(gi,true);
 rows.push({...job,replay:undefined,groups:undefined,samples,episodes,missing_resource_samples:missing});E.destroy();
 if(rows.length%15===0)console.log(`${rows.length}/${jobs.length}`);
}
fs.writeFileSync(output,JSON.stringify({games:rows.length,scope:'First champion-phase snapshots, physical presence and specified action/resource flags only; no SDKcontest/private target/causal win claim.',rows},(k,v)=>typeof v==='bigint'?v.toString():v,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({games:rows.length,episodes:rows.reduce((n,r)=>n+r.episodes.length,0)}));
