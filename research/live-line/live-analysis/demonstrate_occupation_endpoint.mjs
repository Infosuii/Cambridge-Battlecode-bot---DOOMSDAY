import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from '../../tools/replay/engine.mjs';
if(process.env.NFS_REPLAY_ENGINE!=='3.0.0')throw new Error('Explicit engine3');
const [replay,output]=process.argv.slice(2);const assets=defaultAssets();verifyAssets(assets);const E=await engine(assets);E.load(fs.readFileSync(replay));
const {X,check,dv,out,tsnap}=E;check(X.Game_Visualiser_Timeline_GetMain(E.h,out));check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
let old=null,correct=null;
for(;;){check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const s=E.PC.I(dv(),tsnap);if(s.outcome)throw new Error('Ended before comparable endpoint');
 if(s.round>800&&!old)old={round:s.round,phase:s.phase,input:s.inputPosition};
 if(s.round>800&&s.phase===10){correct={round:s.round,phase:s.phase,input:s.inputPosition};break;}
 check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));}
E.destroy();if(old.phase===correct.phase)throw new Error('No phase difference demonstrated');
fs.writeFileSync(output,JSON.stringify({old_stop:old,comparable_stop:correct},(k,v)=>typeof v==='bigint'?v.toString():v,2)+'\n',{flag:'wx'});console.log(JSON.stringify({old,correct}));
