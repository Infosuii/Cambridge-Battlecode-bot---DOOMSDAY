// Outcome/context audit, never live-bot prediction inputs.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {engine,defaultAssets,verifyAssets} from './replay/engine.mjs';
if(process.env.NFS_REPLAY_ENGINE!=='2.0.0')throw new Error('Select pinned engine2.0.0');
const [file,output,firstText='16',lastText='26']=process.argv.slice(2),first=Number(firstText),last=Number(lastText);
if(!output||!Number.isInteger(first)||!Number.isInteger(last)||first<1||last<first||fs.existsSync(output))throw new Error('Usage: replay fresh_output first_round last_round');
const assets=defaultAssets();verifyAssets(assets);const E=await engine(assets),{X,check,dv,out,tsnap}=E;
E.load(fs.readFileSync(file));check(X.Game_Visualiser_Timeline_GetMain(E.h,out));
check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
const records=[],seen=new Set();let ended=false;
for(let i=0;i<2000000;++i){
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const s=E.PC.I(dv(),tsnap);
  if(s.round>last||s.outcome!==0){ended=true;break;}
  const me=s.champions.find(c=>c.entity.index===s.currentChampion),key=`${s.round}:${s.currentChampion}`;
  if(s.round>=first&&s.phase===14&&me&&[10,12].includes(me.type)&&!seen.has(key)){
    seen.add(key);const stats=[];
    for(const c of s.champions.filter(c=>[10,12].includes(c.type)&&c.alive)){
      const p=E.perspective(me.team,me.entity.index),cooldowns=[];
      for(let slot=0;slot<2;++slot){check(X.Game_API_Champion_GetCooldown(E.h,p,c.entity.index,slot,out));cooldowns.push(dv().getInt32(out,true));}
      check(X.Game_API_Champion_GetBuffData(E.h,p,c.entity.index,E.buf,64,out));
      const n=dv().getUint32(out,true);if(n>64)throw new Error('Buff buffer overflow');const shields=[];
      for(let j=0;j<n;++j)if(dv().getUint32(E.buf+12*j,true)===0)shields.push({duration:dv().getInt32(E.buf+12*j+4,true),value:dv().getFloat32(E.buf+12*j+8,true)});
      stats.push({body:c.entity.index,team:c.team,type:c.type,hp:c.health,cooldowns,shields});
    }records.push({round:s.round,acting_team:me.team,acting_body:me.entity.index,stats});
  }check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
}
if(!ended||!records.length)throw new Error('Incomplete or empty phase audit');
fs.writeFileSync(output,JSON.stringify({scope:'Retrospective controlled order/SDK state audit, not prospective accuracy',records,
  source:{replay_sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),
    reader_sha256:crypto.createHash('sha256').update(fs.readFileSync(new URL(import.meta.url))).digest('hex'),engine:'2.0.0',pinned_assets_verified:true}},null,2)+'\n');
console.log(JSON.stringify({owner_starts:records.length,first_round:first,last_round:last}));E.destroy();
