// Offline native replay diagnostic: one full-world sample per champion turn.
// Never used by the bot. Assets and engine version are pinned by engine.mjs.
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from './replay/engine.mjs';
if(process.env.NFS_REPLAY_ENGINE!=='2.0.0') throw new Error('Select engine 2.0.0');
const [file,output]=process.argv.slice(2);
if(!file||!output) throw new Error('Usage: dz_trajectory.mjs INNER_REPLAY OUTPUT_JSON');
const assets=defaultAssets();verifyAssets(assets);const E=await engine(assets);
try {
 E.load(fs.readFileSync(file));const {X,dv,check,out,tsnap}=E;
 check(X.Game_Visualiser_Timeline_GetMain(E.h,out));const timeline=dv().getBigUint64(out,true);
 check(X.Game_Visualiser_Timeline_Info(E.h,timeline,E.args,E.args+8,E.args+16));
 const size=dv().getUint32(E.args,true);
 check(X.Game_Visualiser_Timeline_Seek(E.h,timeline,0,0));
 const rows=[];let last='',completed=false;
 for(let step=0;step<500000;++step) {
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const s=E.PC.I(dv(),tsnap);
  const key=`${s.round}:${s.currentChampion}`;
  if(s.phase===14&&key!==last) {
   last=key;const me=s.champions.find(c=>c.entity.index===s.currentChampion);
   if(me) rows.push({round:s.round,body:s.currentChampion,me,
    nearby:s.champions.filter(c=>c.alive&&c.position&&me.position&&
     Math.max(Math.abs(c.position.x-me.position.x),Math.abs(c.position.y-me.position.y))<=8)});
  }
  if(s.outcome||(s.awaitingInput&&s.inputPosition>=size)){completed=true;break;}
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
 }
 if(!completed) throw new Error('Timeline step bound exceeded');
 fs.writeFileSync(output,JSON.stringify(rows));console.log(`${rows.length} turn samples -> ${output}`);
} finally { E.destroy(); }
