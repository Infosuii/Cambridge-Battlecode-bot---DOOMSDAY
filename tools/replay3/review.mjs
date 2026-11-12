// Offline full-state diagnostics. Never supplies privileged information to a bot.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {engine,defaultAssets,verifyAssets} from './engine.mjs';
const panel=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const output=process.argv[3],dir=defaultAssets();verifyAssets(dir);const E=await engine(dir);
const cheb=(a,b)=>a&&b?Math.max(Math.abs(a.x-b.x),Math.abs(a.y-b.y)):Infinity;
const same=(a,b)=>a&&b&&a.x===b.x&&a.y===b.y;
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const all=[];
for(const item of panel){
 const bytes=fs.readFileSync(item.replay);if(hash(bytes)!==item.sha256)throw Error('Changed replay');
 const nativeBytes=fs.readFileSync(item.summary);if(hash(nativeBytes)!==item.summary_sha256)throw Error('Changed summary');
 const native=JSON.parse(nativeBytes);if(native.match.engineVersion!=='3.0.0')throw Error('Wrong engine');
 E.load(bytes);const {X,check,dv,out,args,tsnap}=E;
 check(X.Game_Visualiser_Timeline_GetMain(E.h,out));const main=dv().getBigUint64(out,true);
 check(X.Game_Visualiser_Timeline_Info(E.h,main,args,args+8,args+16));const size=dv().getUint32(args,true);
 check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
 const frames=[],actions=[],kinds={},byId=new Map();let lastRound=-1,lastAction='',steps=0,final;
 for(;;){
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const d=dv();
  const round=d.getUint32(tsnap+8,true),phase=d.getUint32(tsnap+24,true),outcome=d.getUint32(tsnap+28,true),pos=d.getUint32(tsnap+56,true);
  const kind=d.getUint32(tsnap+68,true),ak=d.getUint32(tsnap+72,true),actor=d.getUint32(tsnap+76,true);
  const key=[round,pos,kind,ak,actor,d.getUint32(tsnap+100,true)].join(':');
  if(key!==lastAction){
   kinds[kind]=(kinds[kind]??0)+1;lastAction=key;
   if(ak===1&&[4,5,6,11,12,13].includes(kind))actions.push({round,pos,kind,id:actor,from:{x:d.getInt32(tsnap+80,true),y:d.getInt32(tsnap+84,true)},to:{x:d.getInt32(tsnap+88,true),y:d.getInt32(tsnap+92,true)}});
  }
  if((round!==lastRound&&phase===10)||outcome){
   const s=E.PC.I(d,tsnap);final=s;
   const f={round,submitted:s.submittedGems.map(Number),champions:s.champions.map(c=>({id:c.entity.index,team:c.team,type:c.type,alive:c.alive,
    p:c.position,hp:c.health,maxhp:c.maxHealth,gems:c.gems,gold:c.gold,
    enemies4:s.champions.filter(o=>o.team!==c.team&&o.alive&&cheb(o.position,c.position)<=4).length,
    allies4:s.champions.filter(o=>o.team===c.team&&o.entity.index!==c.entity.index&&o.alive&&cheb(o.position,c.position)<=4).length,
    live_camp_distance:Math.min(...s.camps.filter(o=>o.health>0).map(o=>cheb(o.position,c.position)??Infinity))})),
    live_camps:s.camps.filter(c=>c.health>0).map(c=>[c.entity.index,c.position.x,c.position.y,c.health])};
   // Null distances remain unknown for dead/unpositioned bodies, not zero.
   for(const c of f.champions)if(!c.p){c.enemies4=null;c.allies4=null;c.live_camp_distance=null;}
   frames.push(f);lastRound=round;
  }
  if(outcome||(d.getUint32(tsnap+20,true)!==0&&pos>=size))break;
  if(++steps>2000000)throw Error('Replay did not terminate');
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
 }
 const expected=native.teams.map(t=>Number(t.submittedGems));
 if(!final||expected.some((s,i)=>s!==Number(final.submittedGems[i])))throw Error('Score parity failed');
 for(const c of native.roster.champions){
  const body=final.champions.find(b=>b.entity.index===c.id);if(!body||body.team!==(c.team==='teamA'?0:1))throw Error('Roster parity failed');
  const tl=native.championTimelines.find(t=>t.owner.id===c.id&&t.metric==='gems');
  if(Number(tl.runs.at(-1).value)!==body.gems)throw Error('Final bag parity failed');
  const history=frames.map(f=>({round:f.round,...f.champions.find(b=>b.id===c.id)})).filter(f=>f.id!==undefined);
  const ownActions=actions.filter(a=>a.id===c.id);const counts={};for(const a of ownActions)counts[a.kind]=(counts[a.kind]??0)+1;
  let stationary=0,moved=0,oscillations=0;const stationaryRuns=[];let start=null;
  for(let i=1;i<history.length;++i){const a=history[i-1],b=history[i];
   const noAct=!ownActions.some(e=>e.round>=a.round&&e.round<b.round&&[5,6,11,12,13].includes(e.kind));
   const still=a.alive&&b.alive&&same(a.p,b.p)&&noAct;
   if(still){stationary++;if(start===null)start=i-1;}else if(start!==null){if(i-start>=8)stationaryRuns.push(history.slice(start,i));start=null;}
   if(a.alive&&b.alive&&!same(a.p,b.p))moved++;
   if(i>=2&&noAct&&a.alive&&b.alive&&history[i-2].alive&&same(history[i-2].p,b.p)&&!same(a.p,b.p))oscillations++;
  }
  if(start!==null&&history.length-start>=8)stationaryRuns.push(history.slice(start));
  const collections=native.events.filter(e=>e.owner.id===c.id&&e.owner.kind==='champion'&&e.kind==='gemCollection').flatMap(e=>e.entries.map(x=>({round:x.timestamp.round,value:Number(x.value),context:x.context,target:x.target})));
  const deaths=native.events.filter(e=>e.owner.id===c.id&&e.kind==='death').flatMap(e=>e.entries.map(x=>({round:x.timestamp.round,context:x.context,
    before:history.filter(f=>f.round<x.timestamp.round&&f.round>=x.timestamp.round-8&&f.alive),
    actions:ownActions.filter(a=>a.round>=x.timestamp.round-5&&a.round<=x.timestamp.round)})));
  byId.set(c.id,{...c,actions:counts,alive_samples:history.filter(h=>h.alive).length,stationary_no_attack_cast_or_channel_samples:stationary,moved_samples:moved,oscillation_samples:oscillations,
    stationary_runs:stationaryRuns.sort((a,b)=>b.length-a.length).slice(0,5).map(r=>({start:r[0].round,end:r.at(-1).round,position:r[0].p,
     hp_start:r[0].hp,hp_end:r.at(-1).hp,gems:r[0].gems,gold:r[0].gold,nearest_camp:r[0].live_camp_distance,enemies4:r[0].enemies4,allies4:r[0].allies4})),collections,deaths,history});
 }
 const result={...item,engine:'3.0.0',asset_hashes:'autonomy/replay/engine.mjs::PINNED',score_roster_bag_parity:true,
  steps,kinds,round_samples:frames.length,final_scores:expected,bodies:[...byId.values()],
  limits:['Per-round snapshots can miss multiple same-round state changes. Actions are observed replay steps, not complete intended commands.',
   'Stationary and oscillation signals may be deliberate waits or dodges. Need code/instrumentation and controlled trials.',
   'Nearby units use omniscient replay state, not a claim that the actor could see them.']};
 fs.writeFileSync(output.replace('.json','-'+item.match+'.json'),JSON.stringify(result));
 all.push({...item,score_roster_bag_parity:true,steps,round_samples:frames.length,bodies:[...byId.values()].map(({history,deaths,collections,...r})=>({...r,death_count:deaths.length,camp_gems:collections.filter(c=>c.context==='campGroup').reduce((a,c)=>a+c.value,0)}))});
 console.log(JSON.stringify({match:item.match,map:item.map,steps,frames:frames.length,parity:true}));E.destroy();
}
fs.writeFileSync(output,JSON.stringify(all,null,2));
