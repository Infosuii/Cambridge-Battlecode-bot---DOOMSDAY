// One replay pass; index actions by body/round instead of searching every action per frame.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {gunzipSync} from 'node:zlib';
import {engine,defaultAssets,verifyAssets} from 'file:///C:/projects/cambridge%20battlecode/work/agentic-improvement/autonomy/replay/engine.mjs';
const [specFile,dest]=process.argv.slice(2),s=JSON.parse(fs.readFileSync(specFile,'utf8'));
const h=b=>crypto.createHash('sha256').update(b).digest('hex');
const raw=fs.readFileSync(s.replay),summary=fs.readFileSync(s.summary);
if(h(raw)!==s.sha256||h(summary)!==s.summary_sha256)throw Error('Input identity mismatch');
const n=JSON.parse(s.summary.endsWith('.gz')?gunzipSync(summary):summary),dir=defaultAssets();verifyAssets(dir);const E=await engine(dir);E.load(raw);
const {X,check,dv,out,args,tsnap}=E;check(X.Game_Visualiser_Timeline_GetMain(E.h,out));const timeline=dv().getBigUint64(out,true);
check(X.Game_Visualiser_Timeline_Info(E.h,timeline,args,args+8,args+16));const size=dv().getUint32(args,true);
check(X.Game_Visualiser_Timeline_Seek(E.h,timeline,0,0));check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));
const initial=E.PC.I(dv(),tsnap),campAt=new Map(),key=p=>`${p.x},${p.y}`,dist=(a,b)=>Math.max(Math.abs(a.x-b.x),Math.abs(a.y-b.y));
for(const c of initial.camps){check(X.Game_API_Map_CampInfo_GetGroup(E.h,c.entity.index,out));campAt.set(key(c.position),dv().getUint32(out,true));}
const sf=X[s.side?'Game_GetTeamBSpawnArea':'Game_GetTeamASpawnArea'];let spawn=null;
if(sf){check(sf(E.h,out));spawn=[0,4,8,12].map(i=>dv().getInt32(out+i,true));}
const own=n.roster.champions.filter(c=>c.team===(s.side?'teamB':'teamA'));
const fuel=new Map(own.map(c=>[c.id,new Set(n.events.filter(e=>e.kind==='fuelExhausted'&&e.owner.kind==='champion'&&e.owner.id===c.id).flatMap(e=>e.entries.map(x=>x.timestamp.round)))]));
const active=new Map(own.map(c=>[c.id,new Set()])),last=new Map(),runs=new Map(),finished=[],counts={alive_pairs:0,stationary_pairs:0,movable_idle_pairs:0,channel_pairs:0,reward_wait_pairs:0,stall_pairs:0,fuel_overlap_pairs:0,channel_restarts:0};
const finish=id=>{const r=runs.get(id);if(r&&r.end-r.start>=12)finished.push(r);runs.delete(id);};
let lastRound=-1,final,steps=0;
for(;;){
 check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const d=dv(),round=d.getUint32(tsnap+8,true),phase=d.getUint32(tsnap+24,true),outcome=d.getUint32(tsnap+28,true),pos=d.getUint32(tsnap+56,true);
 const kind=d.getUint32(tsnap+68,true),ak=d.getUint32(tsnap+72,true),id=d.getUint32(tsnap+76,true);
 if(ak===1&&[4,5,6,11,12,13].includes(kind))active.get(id)?.add(round);
 if((round!==lastRound&&phase===10)||outcome){
  const state=E.PC.I(d,tsnap);final=state;
  for(const c of state.champions.filter(c=>c.team===s.side)){
   const id=c.entity.index,p=c.position,prev=last.get(id),r={round,p,alive:c.alive,hp:c.health,maxhp:c.maxHealth,gems:c.gems,gold:c.gold};
   if(c.alive&&p){
    const perspective=E.perspective(s.side,id);check(X.Game_API_Champion_Get(E.h,perspective,id,out));const bits=dv().getUint32(out+40,true);
    r.canMove=!!(bits&8);r.channel=bits&4?'bank':bits&2?'recall':bits&(1<<12)?'teleport':null;
    if(r.channel){check(X.Game_API_Champion_GetChannelTime(E.h,perspective,id,out));r.timer=dv().getInt32(out,true);}
    r.enemy6=state.champions.some(o=>o.team!==s.side&&o.alive&&o.position&&dist(o.position,p)<=6);
    r.nearCamp=Math.min(...state.camps.filter(x=>x.health>0).map(x=>dist(x.position,p)));
    r.spawn=!!spawn&&p.x>=spawn[0]&&p.y>=spawn[1]&&p.x<=spawn[2]&&p.y<=spawn[3];
    r.lead=Number(state.submittedGems[s.side]-state.submittedGems[1-s.side]);
    const gi=campAt.get(key(p));
    if(gi!==undefined&&!X.Game_API_CampGroup_GetState(E.h,perspective,gi,out)){
      const st=dv().getUint32(out,true);r.reward=st===2;
      if(st===3&&!X.Game_API_CampGroup_GetCooldown(E.h,perspective,gi,out))r.blocked=dv().getInt32(out,true)===0;
    }
   }
   if(prev&&r.round===prev.round+1&&prev.alive&&r.alive){
    counts.alive_pairs++;
    if(prev.channel&&prev.channel===r.channel&&r.timer>prev.timer+1)counts.channel_restarts++;
    const still=prev.p&&r.p&&key(prev.p)===key(r.p)&&!active.get(id)?.has(prev.round)&&r.gems===prev.gems&&!(r.gold<prev.gold);
    if(still)counts.stationary_pairs++;
    if(still&&(r.channel||prev.channel))counts.channel_pairs++;
    if(still&&(r.reward||prev.reward))counts.reward_wait_pairs++;
    const idle=still&&prev.canMove&&r.canMove&&!r.channel&&!prev.channel&&!r.reward&&!prev.reward;
    if(idle){
      counts.movable_idle_pairs++;
      let z=runs.get(id);
      if(!z){z={id,champion:own.find(x=>x.id===id)?.name,start:prev.round,end:r.round,position:p,started:prev,ended:r,fuel_rounds:0,enemy_near_rounds:0,blocked_rounds:0,spawn_near_camp_rounds:0,trailing_rounds:0};runs.set(id,z);}
      z.end=r.round;z.ended=r;z.fuel_rounds+=fuel.get(id)?.has(prev.round)?1:0;z.enemy_near_rounds+=r.enemy6?1:0;
      z.blocked_rounds+=r.blocked?1:0;z.spawn_near_camp_rounds+=(r.spawn&&r.nearCamp<=4)?1:0;z.trailing_rounds+=r.lead<0?1:0;
    }else finish(id);
   }else if(!prev||r.round!==prev.round)finish(id);
   last.set(id,r);
  }
  lastRound=round;
 }
 if(outcome||(d.getUint32(tsnap+20,true)!==0&&pos>=size))break;
 if(++steps>2000000)throw Error('Replay did not terminate');check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
}
for(const id of runs.keys())finish(id);
if(!final||n.teams.some((t,i)=>Number(t.submittedGems)!==Number(final.submittedGems[i])))throw Error('Score parity');
for(const c of own){const b=final.champions.find(x=>x.entity.index===c.id);const tl=n.championTimelines.find(t=>t.owner.id===c.id&&t.metric==='gems');if(!b||b.team!==s.side||Number(tl.runs.at(-1).value)!==b.gems)throw Error('Roster/bag parity');}
for(const z of finished){counts.stall_pairs+=z.end-z.start;counts.fuel_overlap_pairs+=z.fuel_rounds;}
const r={match:s.match,map:s.map,version:s.version,side:s.side,parity:true,counts,spawn,fuel_events:[...fuel.values()].reduce((a,b)=>a+b.size,0),stalls:finished.sort((a,b)=>(b.end-b.start)-(a.end-a.start)),replay_sha256:s.sha256,scope:'At least 12 consecutive alive, movement-enabled, unchanged-position body-rounds without observed move/attack/cast/channel action, gold spend or gem change. Excludes sampled channels and reward stands. Signals need exact substep verification; omniscient enemy distance is diagnostic only.'};
fs.writeFileSync(dest,JSON.stringify(r));E.destroy();
