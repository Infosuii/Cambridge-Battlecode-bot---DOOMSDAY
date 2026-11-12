// Offline outcomes only. Native hidden state never supplies bot predictions.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {engine,defaultAssets,verifyAssets} from './replay/engine.mjs';
import {ModelAudit,parseQuotes} from './replay/model_audit_core.mjs';
if(process.env.NFS_REPLAY_ENGINE!=='2.0.0')throw new Error('Select pinned engine2.0.0');
const [file,stdout,output,lastText='500']=process.argv.slice(2),last=Number(lastText);
if(!output||!Number.isInteger(last)||last<1)throw new Error('Usage: replay stdout output [last_round]');
const quotes=parseQuotes(fs.readFileSync(stdout,'utf8'));
const assets=defaultAssets();verifyAssets(assets);const E=await engine(assets);
E.load(fs.readFileSync(file));const {X,check,dv,out,tsnap}=E;
// Game_GetCampGroup describes the map-editor template BEFORE mirroring.
// The SDK Map API enumerates the physical mirrored groups used by the bot.
check(X.Game_API_Map_GetNumCampGroups(E.h,out));const count=dv().getUint32(out,true),groups=[];
const buffer=X.Engine_Malloc(Math.max(count,2000)*4);
check(X.Game_API_Map_GetCampGroups(E.h,buffer,count,out));
const groupIds=Array.from({length:count},(_,i)=>dv().getUint32(buffer+4*i,true));
if(groupIds.some((id,i)=>id!==i))throw new Error('SDK group ordering needs an explicit handle quote');
for(const group of groupIds) {
  check(X.Game_API_Map_CampGroup_GetCampInfo(E.h,group,buffer,2000,out));
  const n=dv().getUint32(out,true),members=Array.from({length:n},(_,i)=>dv().getUint32(buffer+4*i,true)),ids=[];
  for(const id of members) {
    check(X.Game_API_Map_CampInfo_Get(E.h,id,out));
    ids.push({id,x:dv().getInt32(out,true),y:dv().getInt32(out+4,true)});
  }
  groups.push(ids);
}
X.Engine_Free(buffer);
// SDK imports.h: unit_definition is88 bytes, camp_stats follows; range is
// int32 at+8 and base strength float at+20. Query the pinned engine metadata.
const campDesigns=new Map();
for(let type=0;type<6;++type) {
  check(X.Game_API_Camp_Design(E.h,type,E.buf));
  const range=dv().getInt32(E.buf+96,true),strength=dv().getFloat32(E.buf+108,true);
  if(!Number.isInteger(range)||range<0||range>100||!Number.isFinite(strength)||strength<0)throw new Error('Invalid camp design ABI');
  campDesigns.set(type,{range,strength});
}
const audit=new ModelAudit(quotes,groups.map(g=>g.map(c=>c.id)),last,campDesigns,
  new Map(groups.flat().map(c=>[c.id,{x:c.x,y:c.y}])));
check(X.Game_Visualiser_Timeline_GetMain(E.h,out));check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
let ended=false,verified=false,visibilityDenials=0;
for(let n=0;n<2000000;++n) {
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const s=E.PC.I(dv(),tsnap);
  if(!verified&&s.camps.length) {
    const camps=new Map(s.camps.map(c=>[c.entity.index,c]));
    for(const g of groups)for(const c of g) {
      const native=camps.get(c.id);
      if(!native||native.position.x!==c.x||native.position.y!==c.y)throw new Error('Camp handle/index mapping failed');
    }
    verified=true;
  }
  audit.consume(s,(id,c)=>{
    const camp=s.camps.find(x=>x.entity.index===id);
    const rc=X.Game_API_HasCamp(E.h,E.perspective(c.team,c.entity.index),camp.position.x,camp.position.y,out);
    if(rc===97) { ++visibilityDenials;return false; } // SDK has_camp returns false in personal fog.
    if(rc!==0)throw new Error(`Personal camp visibility query rejected: ${rc}`);
    return !!dv().getInt32(out,true);
  });
  if(s.round>last||s.outcome!==0) { ended=true;break; }
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
}
if(!ended||!verified)throw new Error('Audit timeline incomplete');
const result=audit.finish();result.quote_count=quotes.length;result.last_round=last;result.personal_visibility_denials=visibilityDenials;
result.camp_designs=Object.fromEntries(campDesigns);
result.source={replay_sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),
  stdout_sha256:crypto.createHash('sha256').update(fs.readFileSync(stdout)).digest('hex'),engine:'2.0.0',
  reader_sha256:crypto.createHash('sha256').update(fs.readFileSync(new URL(import.meta.url))).digest('hex'),
  core_sha256:crypto.createHash('sha256').update(fs.readFileSync(new URL('./replay/model_audit_core.mjs',import.meta.url))).digest('hex')};
fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({quotes:quotes.length,records:result.records.length,frames:result.frames,
  outcomes:result.records.reduce((a,r)=>(a[r.outcome]=(a[r.outcome]??0)+1,a),{})}));E.destroy();
