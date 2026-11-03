// Compare paired authoritative replay states at the first champion phase of each round.
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from './replay_engine.mjs';
const dir=defaultAssets();
verifyAssets(dir);
const E=await engine(dir);

function decode(path,side) {
    E.load(fs.readFileSync(path));
    const {X,check,dv,out,args,tsnap}=E;
    check(X.Game_Visualiser_Timeline_GetMain(E.h,out));
    const main=dv().getBigUint64(out,true);
    check(X.Game_Visualiser_Timeline_Info(E.h,main,args,args+8,args+16));
    const size=dv().getUint32(args,true);
    check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
    const rows=new Map();
    let prior=-1, finishReady=null, finishMax=0, roster=null;
    for (;;) {
        check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));
        const d=dv();
        const r=d.getUint32(tsnap+8,true), phase=d.getUint32(tsnap+24,true);
        if (phase===10 && r!==prior) {
            const s=E.PC.I(d,tsnap);
            prior=r;
            if (!roster) roster=s.champions.map(c=>[c.entity.index,c.team,c.type]);
            const own=s.champions.filter(c=>c.team===side&&c.alive);
            const due=Number(s.submittedGems[side])+Math.max(0,...own.map(c=>c.gems));
            finishMax=Math.max(finishMax,due);
            if (due>=1000 && finishReady===null) finishReady=r;
            const units=s.champions.map(c=>[c.entity.index,c.position?.x??-1,c.position?.y??-1,
                c.alive,c.health,c.maxHealth,c.gems,c.gold,c.kills]);
            rows.set(r,{units,bank:s.submittedGems.map(Number),ownPotential:due});
        }
        if (d.getUint32(tsnap+28,true) || (d.getUint32(tsnap+20,true)!==0 && d.getUint32(tsnap+56,true)>=size)) break;
        check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
    }
    E.destroy();
    return {rows,finishReady,finishMax,roster};
}

const argv=process.argv.slice(2);
if (argv.length%4) throw new Error('Expected groups of four: name side replay-base replay-test');
for (let i=0; i<argv.length; i+=4) {
    const [name,letter,before,after]=argv.slice(i,i+4);
    const side=letter==='A'?0:1;
    const a=decode(before,side), b=decode(after,side);
    let first=null;
    const sameRoster=JSON.stringify(a.roster)===JSON.stringify(b.roster);
    if (!sameRoster) first={round:0,draft:true};
    else for (const [r,before] of a.rows) {
        const after=b.rows.get(r);
        if (!after) break;
        if (JSON.stringify(before)!==JSON.stringify(after)) {
            first={round:r,bankBefore:before.bank,bankAfter:after.bank,
                ownPotentialBefore:before.ownPotential,ownPotentialAfter:after.ownPotential};
            break;
        }
    }
    console.log(JSON.stringify({name,side:letter,sameRoster,first,finishReady:[a.finishReady,b.finishReady],
        finishMax:[a.finishMax,b.finishMax]}));
}
