import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from '../../tools/replay/engine.mjs';
const dir=defaultAssets();verifyAssets(dir);const E=await engine(dir);E.load(fs.readFileSync(process.argv[2]));
const {X,check,dv,out,tsnap}=E;check(X.Game_Visualiser_Timeline_GetMain(E.h,out));check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
let count=0;const rows=[];
for(let i=0;i<5000;i++){
 check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const s=E.PC.I(dv(),tsnap);
 if(s.round>2||s.outcome)break;
 if(s.awaitingInput||s.step?.kind===26){rows.push({round:s.round,phase:s.phase,awaiting:s.awaitingInput,current:s.currentChampion,input:s.inputPosition,step:s.step});if(++count>=20)break;}
 check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
}
console.log(JSON.stringify(rows));E.destroy();
