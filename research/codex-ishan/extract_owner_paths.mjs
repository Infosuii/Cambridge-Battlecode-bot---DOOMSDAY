// EXP242: passive full-replay owner inputs; no policy or private-state reconstruction.
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from '../../tools/replay/engine.mjs';
const [input]=process.argv.slice(2);
if(process.env.NFS_REPLAY_ENGINE!=='3.0.0')throw new Error('Requires explicit engine3');
const jobs=JSON.parse(fs.readFileSync(input,'utf8'));
const assets=defaultAssets();verifyAssets(assets);const E=await engine(assets);
for(const [index,job] of jobs.entries()) {
  E.load(fs.readFileSync(job.replay));
  const {X,check,dv,out,tsnap}=E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h,out));
  check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
  const samples=[],actions=new Map(),seen=new Set();
  for(;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const d=dv();
    const round=d.getUint32(tsnap+8,true),phase=d.getUint32(tsnap+24,true),outcome=d.getUint32(tsnap+28,true);
    if(round>800)break;
    const kind=d.getUint32(tsnap+68,true),actorKind=d.getUint32(tsnap+72,true),actor=d.getUint32(tsnap+76,true),stepRound=d.getUint32(tsnap+96,true);
    if(actorKind===1&&(kind===5||kind===6)&&stepRound>=1&&stepRound<=800) {
      const key=`${stepRound}:${actor}`;
      if(!actions.has(key))actions.set(key,new Set());actions.get(key).add(kind);
    }
    if(round>=1&&phase===10&&d.getUint32(tsnap+20,true)!==0) {
      const current=d.getUint32(tsnap+60,true),key=`${round}:${current}`;
      if(!seen.has(key)) {
        const s=E.PC.I(d,tsnap),c=s.champions.find(c=>c.entity.index===current);
        if(c) {
          samples.push({actor:current,team:c.team,type:c.type,round,x:c.position?.x??-1,y:c.position?.y??-1,
                        hp:c.health,gold:Number(c.gold),gems:Number(c.gems),alive:c.alive});
          seen.add(key);
        }
      }
    }
    if(outcome)break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
  }
  if(!samples.length)throw new Error(`No owner samples ${job.matchId}`);
  fs.writeFileSync(job.output,JSON.stringify({matchId:job.matchId,samples,combat_actions:[...actions].map(([key,kinds])=>({key,kinds:[...kinds]}))})+'\n',{flag:'wx'});
  E.destroy();
  if((index+1)%10===0||index+1===jobs.length)console.log(`${index+1}/${jobs.length} owner paths`);
}
