// Minimal fixed-frequency extraction; reserved partition requires examined equivalence receipt.
import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';import {fileURLToPath} from 'node:url';
import {engine,defaultAssets,verifyAssets,VERSION} from './engine.mjs';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),S=path.join(ROOT,'research/deep-2026-10-28'),L=path.join(ROOT,'artifacts/local-only/deep-2026-10-28');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex'),assert=(x,m)=>{if(!x)throw new Error(m);};
const [part,outarg]=process.argv.slice(2),out=path.resolve(outarg??'');assert(VERSION==='2.0.0'&&['calibration-excluded','examined','hands-off'].includes(part),'Explicit engine2 and partition required');assert(out.startsWith(path.join(ROOT,'artifacts')+path.sep),'Local output only');
const code=hash(fs.readFileSync(fileURLToPath(import.meta.url))),plan=hash(fs.readFileSync(path.join(S,'FINAL_CONFIRMATION_PLAN.json')));
if(part==='hands-off'){const v=JSON.parse(fs.readFileSync(path.join(S,'FINAL_VALIDATION.json'),'utf8'));assert(v.passed===385&&v.calibration_passed===5&&v.m1_equivalent&&v.d3_equivalent&&v.action_code_sha256===code&&v.plan_sha256===plan,'Current locked equivalence validation required');}
const entries=JSON.parse(fs.readFileSync(path.join(S,'CANDIDATE_MANIFEST.json'),'utf8')).rows.filter(r=>r.partition===part);fs.mkdirSync(out,{recursive:true});
const dir=defaultAssets();verifyAssets(dir);const E=await engine(dir),{X,check,dv}=E;let passed=0;
for(const row of entries){
 E.load(fs.readFileSync(path.join(L,'replays',part,row.match_id+'.repl26a')));const actions=[];let started=false,final;
 try{check(X.Game_Visualiser_Timeline_GetMain(E.h,E.out));const main=dv().getBigUint64(E.out,true);check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
  for(;;){check(X.Game_Visualiser_ReadTimelineState(E.h,E.tsnap));const p=E.tsnap,d=dv(),r=d.getInt32(p+8,true),phase=d.getUint32(p+24,true),outcome=d.getUint32(p+28,true),kind=d.getUint32(p+68,true),ak=d.getUint32(p+72,true),actor=d.getUint32(p+76,true);
   if(phase===10)started=true;
   if(started&&ak===1&&[4,5,6,11,16,22].includes(kind)){
    // Match the existing M1 screen exactly, including no-op kind4/22 exclusions.
    actions.push({r:d.getInt32(p+96,true),actor,kind});
   }
   if(outcome){final={round:r,outcome,input:d.getUint32(p+56,true)};break;}check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
  }
 }finally{E.destroy();}
 fs.writeFileSync(path.join(out,row.match_id+'.json'),JSON.stringify({match_id:row.match_id,partition:part,action_code_sha256:code,plan_sha256:plan,actions,final})+'\n');passed++;if(passed%50===0)console.log(JSON.stringify({part,processed:passed,total:entries.length}));
}
const receipt={partition:part,passed,failed:0,action_code_sha256:code,plan_sha256:plan};fs.writeFileSync(path.join(out,'run.json'),JSON.stringify(receipt,null,2)+'\n');console.log(JSON.stringify(receipt));
