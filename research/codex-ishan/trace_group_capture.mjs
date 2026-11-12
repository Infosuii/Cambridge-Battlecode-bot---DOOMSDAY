// EXP288 read-only exact group state and fixed current-actor own-view capture queries.
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from '../../tools/replay/engine.mjs';
if(process.env.NFS_REPLAY_ENGINE!=='3.0.0')throw new Error('Explicit engine3');
const [replay,planFile,output]=process.argv.slice(2),plan=JSON.parse(fs.readFileSync(planFile,'utf8'));
const assets=defaultAssets();verifyAssets(assets);const E=await engine(assets);E.load(fs.readFileSync(replay));const {X,check,dv,out,args,tsnap}=E;
const arity=X.Game_API_CampGroup_GetCaptureState?.length;
check(X.Game_Visualiser_Timeline_GetMain(E.h,out));check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
const queried=new Set(),queries=[],rounds=[];let lastRound=-1;
for(;;){
 check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const s=E.PC.I(dv(),tsnap);
 if(s.round>559||s.outcome)break;
 if(s.phase===10&&s.awaitingInput){
  if(s.round>=62&&s.round!==lastRound){
   lastRound=s.round;rounds.push({round:s.round,input:s.inputPosition,group:s.groups[0],
    actors:s.champions.map(c=>({id:c.entity.index,team:c.team,type:c.type,alive:c.alive,position:c.position,hp:c.health,gems:c.gems}))});
  }
  for(const [team,actor,round] of plan.jobs){
   const key=`${team}:${actor}:${round}`;
   if(queried.has(key)||s.round!==round||s.currentChampion!==actor)continue;
   queried.add(key);check(X.Game_Visualiser_ReadState(E.h,E.perspective(team,actor),E.snap));const v=E.PC.F(dv(),E.snap);
   let sdk=null;
   if(arity===3){const rc=X.Game_API_CampGroup_GetCaptureState(E.h,0,args);sdk=rc===0?{timer:dv().getInt32(args,true),state:dv().getInt32(args+4,true)}:{error:rc};}
   queries.push({team,actor,round,input:s.inputPosition,snapshot_group:s.groups[0],sdk_capture:sdk,
                 view_keys:Object.keys(v),view_groups:v.groups??null});
  }
 }
 check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
}
E.destroy();
fs.writeFileSync(output,JSON.stringify({arity,queries,rounds},(k,v)=>typeof v==='bigint'?v.toString():v,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({arity,queries:queries.map(({team,actor,round,snapshot_group,sdk_capture,view_keys,view_groups})=>({team,actor,round,snapshot_group,sdk_capture,view_keys,view_groups})),rounds:rounds.length}));
