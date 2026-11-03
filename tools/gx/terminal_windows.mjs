// Observe which losing teams already had enough live carried gems near the end.
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from './replay_engine.mjs';
const dir=defaultAssets();
verifyAssets(dir);
const E=await engine(dir);
const jobs=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const windows=[12,25,50,100];
const cheb=(p,q)=>Math.max(Math.abs(p.x-q[0]),Math.abs(p.y-q[1]));

for (const {id,side,last,altars,path} of jobs) {
    E.load(fs.readFileSync(path));
    const {X,check,dv,out,args,tsnap}=E;
    check(X.Game_Visualiser_Timeline_GetMain(E.h,out));
    const main=dv().getBigUint64(out,true);
    check(X.Game_Visualiser_Timeline_Info(E.h,main,args,args+8,args+16));
    const size=dv().getUint32(args,true);
    check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
    let r0=-1;
    const rows=windows.map(length=>({length,max_bank_bags:0,max_bank_single:0,
        max_bank_near:0,max_bank_at:0,max_bank_with_horizon:0,first_total:null,first_at:null}));
    let finish=null;
    for (;;) {
        check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));
        const d=dv();
        const round=d.getUint32(tsnap+8,true), phase=d.getUint32(tsnap+24,true),
            done=d.getUint32(tsnap+28,true) || (d.getUint32(tsnap+20,true)!==0 && d.getUint32(tsnap+56,true)>=size);
        if ((phase===10 && round!==r0 && round>=last-100) || done) {
            const s=E.PC.I(d,tsnap);
            r0=round;
            const banks=s.submittedGems.map(Number), bank=banks[side];
            const own=s.champions.filter(c=>c.alive && c.team===side && c.gems>0 && c.position);
            const bags=own.map(c=>{
                const dist=Math.max(0,Math.min(...altars.map(q=>cheb(c.position,q)))-1);
                return {gems:c.gems,dist};
            });
            const add=pred=>bank+bags.reduce((a,c)=>a+(pred(c)?c.gems:0),0);
            const total=add(()=>true), single=bank+Math.max(0,...bags.map(c=>c.gems));
            const near=add(c=>c.dist<=5), at=add(c=>c.dist===0);
            // Two-tiles-per-round travel estimate plus approximate channel.
            // Existing channels and cooldowns are unavailable in this snapshot.
            const fit=add(c=>Math.ceil(c.dist/2)+Math.max(1,Math.ceil(c.gems/10))<=last-round);
            for (const x of rows) if (round>=last-x.length) {
                x.max_bank_bags=Math.max(x.max_bank_bags,total);
                x.max_bank_single=Math.max(x.max_bank_single,single);
                x.max_bank_near=Math.max(x.max_bank_near,near);
                x.max_bank_at=Math.max(x.max_bank_at,at);
                x.max_bank_with_horizon=Math.max(x.max_bank_with_horizon,fit);
                if (total>=1000 && x.first_total===null) x.first_total=round;
                if (at>=1000 && x.first_at===null) x.first_at=round;
            }
            if (done) finish={round,banks,bags};
        }
        if (done) break;
        check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
    }
    console.log(JSON.stringify({id,finish,rows}));
    E.destroy();
}
