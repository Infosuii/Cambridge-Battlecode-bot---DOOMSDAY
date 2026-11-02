import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from '../../tools/replay/engine.mjs';
const dir=defaultAssets();verifyAssets(dir);const E=await engine(dir);
E.load(fs.readFileSync(process.argv[2]));
const {X,check,dv,out,args,tsnap}=E;
check(X.Game_Visualiser_Timeline_GetMain(E.h,out));const main=dv().getBigUint64(out,true);
check(X.Game_Visualiser_Timeline_Info(E.h,main,args,args+8,args+16));const size=dv().getUint32(args,true);
check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
let last=-1,first=null,end=null;const windows=[];
for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));
    const d=dv(),round=d.getUint32(tsnap+8,true),phase=d.getUint32(tsnap+24,true),outcome=d.getUint32(tsnap+28,true),pos=d.getUint32(tsnap+56,true);
    if ((round!==last && phase===10)||outcome) {
        const s=E.PC.I(d,tsnap);
        const carriers=s.champions.filter(c=>c.team===0 && c.alive && c.position && c.gems>0);
        const bag=carriers.reduce((a,c)=>a+c.gems,0);
        const own=Number(s.submittedGems[0]);
        end={round,banked:own,carried:bag,carriers:carriers.map(c=>({id:c.entity.index,gems:c.gems,position:c.position}))};
        if (own<1000 && own+bag>=1000) {if (!first)first=end;if (windows.length<8)windows.push(end);}
        last=round;
    }
    if (outcome || (d.getUint32(tsnap+20,true)!==0 && pos>=size))break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
}
console.log(JSON.stringify({scope:'Omniscient replay diagnostic only; availability to a legal coordinator is not asserted.',first_potential_cohort:first,end,early_windows:windows},null,2));
