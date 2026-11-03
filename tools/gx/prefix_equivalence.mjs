// Hash every native timeline snapshot through the start of a selected round.
import crypto from 'node:crypto';
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from './replay_engine.mjs';
const dir=defaultAssets();
verifyAssets(dir);
const E=await engine(dir);
const jobs=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));

function prefix(path,through) {
    E.load(fs.readFileSync(path));
    const {X,check,dv,out,args,tsnap,tsize}=E;
    check(X.Game_Visualiser_Timeline_GetMain(E.h,out));
    const main=dv().getBigUint64(out,true);
    check(X.Game_Visualiser_Timeline_Info(E.h,main,args,args+8,args+16));
    const size=dv().getUint32(args,true);
    check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
    const sha=crypto.createHash('sha256');
    let count=0, input=null;
    for (;;) {
        check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));
        const d=dv();
        const r=d.getUint32(tsnap+8,true), phase=d.getUint32(tsnap+24,true);
        sha.update(Buffer.from(d.buffer,tsnap,tsize));
        count++;
        if (r===through && phase===10) {
            input=d.getUint32(tsnap+56,true);
            break;
        }
        if (d.getUint32(tsnap+28,true) || r>through ||
            (d.getUint32(tsnap+20,true)!==0 && d.getUint32(tsnap+56,true)>=size)) {
            throw Error('Replay never reached requested first champion phase');
        }
        check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
    }
    E.destroy();
    return {sha256:sha.digest('hex'),snapshots:count,input};
}
for (const j of jobs) {
    const left=prefix(j.base,j.round), right=prefix(j.candidate,j.round);
    console.log(JSON.stringify({cell:j.cell,round:j.round,left,right,identical:left.sha256===right.sha256}));
}
