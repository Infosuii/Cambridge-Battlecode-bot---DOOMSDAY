// Paired replay diagnosis of the historic hooks crystal anomaly. Offline only; no bot input.
// Usage: node crystal_divergence.mjs <replay folder> <output.json>
import fs from 'node:fs'; import path from 'node:path'; import crypto from 'node:crypto';
import {engine,defaultAssets,verifyAssets} from './engine.mjs';
const dir=defaultAssets();verifyAssets(dir);const E=await engine(dir);
const [input,output]=process.argv.slice(2);
const gear=items=>items.reduce((s,n,i)=>s+n*(i%2?150:30),0);
function trace(file,t) {
 E.load(fs.readFileSync(file));const {X,check,dv,out,args,tsnap}=E;
 check(X.Game_Visualiser_Timeline_GetMain(E.h,out));const main=dv().getBigUint64(out,true);
 check(X.Game_Visualiser_Timeline_Info(E.h,main,args,args+8,args+16));const size=dv().getUint32(args,true);
 check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
 const rounds=new Map(),acts=new Map(),purchases=[],fuel=[],tp=[];let last=-1,teams=new Map(),final;
 for(;;) {
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const d=dv();
  const r=d.getUint32(tsnap+8,true),kind=d.getUint32(tsnap+68,true),actor=d.getUint32(tsnap+76,true),ak=d.getUint32(tsnap+72,true);
  const phase=d.getUint32(tsnap+24,true),outcome=d.getUint32(tsnap+28,true),pos=d.getUint32(tsnap+56,true);
  if((r!==last&&phase===10)||kind===13||outcome) {
   const s=E.PC.I(d,tsnap);final=s;
   if(!teams.size&&s.champions.length) teams=new Map(s.champions.map(c=>[c.entity.index,c.team]));
   if(r!==last&&phase===10) {
    rounds.set(r,{score:s.submittedGems.map(Number),c:s.champions.map(c=>({id:c.entity.index,team:c.team,type:c.type,p:c.position,hp:c.health,alive:c.alive,gold:c.gold,gems:c.gems,gear:gear(c.items),items:c.items,cons:c.consumables}))});last=r;
   }
   if(kind===13&&teams.get(actor)===t) {
    const c=s.champions.find(c=>c.entity.index===actor);
    if(c)purchases.push({round:r,actor,type:c.type,gold:c.gold,gear:gear(c.items),items:c.items,cons:c.consumables});
   }
  }
  if(ak===1&&teams.get(actor)===t) {
   if(kind===26)fuel.push({round:r,actor});if(kind===21)tp.push({round:r,actor});
   if([4,5,6,11,12,14,18,23].includes(kind)) {
    if(!acts.has(r))acts.set(r,[]);
    acts.get(r).push([actor,kind,...[88,92].map(off=>d.getInt32(tsnap+off,true))]);
   }
  }
  if(outcome||(d.getUint32(tsnap+20,true)!==0&&pos>=size))break;
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
 }
 E.destroy();return {rounds,acts,purchases,fuel,tp,score:final.submittedGems.map(Number)};
}
const rows=[];
for(const name of fs.readdirSync(input).filter(n=>/^buyonly-01hooks-[AB]-s\d+\.repl26a$/.test(n))) {
 const other=name.replace('buyonly-','nobuy-');if(!fs.existsSync(path.join(input,other)))continue;
 const side=name.includes('-A-')?0:1;const a=trace(path.join(input,name),side),b=trace(path.join(input,other),side);
 const fields={position:c=>[c.id,c.alive,c.p],hp:c=>[c.id,c.hp],equipment:c=>[c.id,c.gear,c.items],gold:c=>[c.id,c.gold]};
 const first={};
 for(const r of [...a.rounds.keys()].sort((x,y)=>x-y)) {
  if(!b.rounds.has(r))continue;
  const ac=a.rounds.get(r).c.filter(c=>c.team===side),bc=b.rounds.get(r).c.filter(c=>c.team===side);
  for(const [k,f] of Object.entries(fields))if(!first[k]&&JSON.stringify(ac.map(f))!==JSON.stringify(bc.map(f)))first[k]={round:r,buy:ac.map(f),no_buy:bc.map(f)};
  if(!first.actions&&JSON.stringify(a.acts.get(r)??[])!==JSON.stringify(b.acts.get(r)??[]))first.actions={round:r,buy:a.acts.get(r),no_buy:b.acts.get(r)};
 }
 rows.push({seed:Number(name.match(/-s(\d+)/)[1]),side:side?'B':'A',input_sha256:[name,other].map(n=>crypto.createHash('sha256').update(fs.readFileSync(path.join(input,n))).digest('hex')),
  score:[a.score[side]-a.score[1-side],b.score[side]-b.score[1-side]],first,buy_first_purchases:a.purchases.slice(0,12),no_buy_first_purchases:b.purchases.slice(0,12),fuel:[a.fuel,b.fuel],teleports:[a.tp.length,b.tp.length]});
 console.log(name,JSON.stringify(Object.fromEntries(Object.entries(first).map(([k,v])=>[k,v.round]))));
}
fs.writeFileSync(output,JSON.stringify(rows,null,1)+'\n');console.log('pairs',rows.length);
