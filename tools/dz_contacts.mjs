// V-M2 contact dataset (offline only; never a bot input). For each turn of a team-A champion with a living enemy
// within 8 tiles, record that body's hp/max_hp/strength, allies within 6 and enemies within 8 (same stats), and
// whether the body dies within the next 4 rounds. Stats come from each unit's own perspective (retrospective
// calibration data; the bot sees only what its own vision shows).
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from './replay/engine.mjs';
if(process.env.NFS_REPLAY_ENGINE!=='2.0.0')throw new Error('Select engine 2.0.0');
const [file,output,teamText='0']=process.argv.slice(2),team=Number(teamText);
if(!file||!output)throw new Error('Usage: dz_contacts.mjs INNER_REPLAY OUTPUT_JSON [team 0|1]');
const assets=defaultAssets();verifyAssets(assets);const E=await engine(assets);
try {
 E.load(fs.readFileSync(file));const {X,dv,check,out,tsnap}=E;
 check(X.Game_Visualiser_Timeline_GetMain(E.h,out));const timeline=dv().getBigUint64(out,true);
 check(X.Game_Visualiser_Timeline_Info(E.h,timeline,E.args,E.args+8,E.args+16));
 const size=dv().getUint32(E.args,true);
 check(X.Game_Visualiser_Timeline_Seek(E.h,timeline,0,0));
 const stats=c=>{
  check(X.Game_API_Champion_Get(E.h,E.perspective(c.team,c.entity.index),c.entity.index,E.buf));
  return {id:c.entity.index,type:c.type,hp:c.health,max_hp:c.maxHealth,strength:dv().getFloat32(E.buf+24,true),
   x:c.position.x,y:c.position.y,gems:c.gems};
 };
 const rows=[],deaths=new Map();let last='',completed=false;
 for(let step=0;step<2000000;++step) {
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const s=E.PC.I(dv(),tsnap);
  for(const c of s.champions) if(c.team===team&&!c.alive&&!deaths.has(`${c.entity.index}:${s.round}`)) deaths.set(`${c.entity.index}:${s.round}`,true);
  const key=`${s.round}:${s.currentChampion}`;
  if(s.phase===14&&key!==last) {
   last=key;const me=s.champions.find(c=>c.entity.index===s.currentChampion);
   if(me&&me.team===team&&me.alive&&me.position) {
    const d=c=>Math.max(Math.abs(c.position.x-me.position.x),Math.abs(c.position.y-me.position.y));
    const enemies=s.champions.filter(c=>c.team!==team&&c.alive&&c.position&&d(c)<=8);
    if(enemies.length) {
     const allies=s.champions.filter(c=>c.team===team&&c.alive&&c.position&&c.entity.index!==me.entity.index&&d(c)<=6);
     rows.push({round:s.round,me:stats(me),allies:allies.map(stats),enemies:enemies.map(c=>({...stats(c),d:d(c)}))});
    }
   }
  }
  if(s.outcome||(s.awaitingInput&&s.inputPosition>=size)){completed=true;break;}
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
 }
 if(!completed) throw new Error('Timeline step bound exceeded');
 // Label: the body is dead at some round in (round, round+4].
 const deadAt=new Map();for(const k of deaths.keys()){const [id,r]=k.split(':').map(Number);if(!deadAt.has(id))deadAt.set(id,[]);deadAt.get(id).push(r);}
 for(const r of rows) r.dies4=(deadAt.get(r.me.id)??[]).some(t=>t>r.round&&t<=r.round+4);
 fs.writeFileSync(output,JSON.stringify(rows));console.log(`${rows.length} contact samples -> ${output}`);
} finally { E.destroy(); }
