// Annotate an actual local replay's accepted inputs and bounded actor round states.
import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {engine,defaultAssets,verifyAssets,VERSION} from '../engine.mjs';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../..'),STUDY=path.join(ROOT,'research/deep-2026-10-28');
const [specFile]=process.argv.slice(2),assert=(x,m)=>{if(!x)throw new Error(m);};assert(VERSION==='2.0.0'&&specFile,'Engine2 and local script JSON required');
const spec=JSON.parse(fs.readFileSync(specFile,'utf8'));
const entry=JSON.parse(fs.readFileSync(path.join(STUDY,'CANDIDATE_MANIFEST.json'),'utf8')).rows.find(r=>r.match_id===spec.match_id);
assert(entry&&['calibration-excluded','examined'].includes(entry.partition),'No held-out script labels');
const raw=path.resolve(ROOT,spec.raw_replay);assert(raw.startsWith(path.join(ROOT,'artifacts')+path.sep),'Actual replay must be local artifacts');
const dir=defaultAssets();verifyAssets(dir);const E=await engine(dir),{X,check,dv}=E;E.load(fs.readFileSync(raw));
check(X.Game_Visualiser_Timeline_GetMain(E.h,E.out));const main=dv().getBigUint64(E.out,true);check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
const labels=new Map(),observations=[];let started=false,final=null;
for(;;){check(X.Game_Visualiser_ReadTimelineState(E.h,E.tsnap));const d=dv(),r=d.getInt32(E.tsnap+8,true),phase=d.getUint32(E.tsnap+24,true),outcome=d.getUint32(E.tsnap+28,true),input=d.getUint32(E.tsnap+56,true),current=d.getUint32(E.tsnap+60,true),ready=!!d.getUint32(E.tsnap+20,true);
 if(phase===10)started=true;
 if(ready&&input<spec.inputs.length)labels.set(input+1,{r,phase,actor:current===0xffffffff?null:current});
 if(started&&(phase===0||outcome)&&spec.window&&r>=spec.window[0]&&r<=spec.window[1]){
  check(X.Game_Visualiser_ReadState(E.h,E.perspective(2,0xffffffff),E.snap));const v=E.PC.F(dv(),E.snap),c=v.champions.find(c=>c.entity.index===spec.actor);
  observations.push({r,id:spec.actor,p:c.position??null,hp:c.health,bag:c.gems,gold:c.gold,alive:c.alive,channel:c.channelType,timer:c.channelTimer,banked:v.submittedGems});
 }
 if(outcome||(ready&&input>=spec.inputs.length)){final={round:r,outcome,input};break;}check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
}
assert(labels.size===spec.inputs.length,'Not all accepted inputs were labelled');
spec.inputs=spec.inputs.map(row=>({...row,...labels.get(row.input)}));spec.observations=observations;spec.final=final;
fs.writeFileSync(specFile,JSON.stringify(spec,(k,v)=>typeof v==='bigint'?v.toString():v)+'\n');E.destroy();
console.log(JSON.stringify({match_id:spec.match_id,inputs:spec.inputs.length,observations:observations.length}));
