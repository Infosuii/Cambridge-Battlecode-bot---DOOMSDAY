// Exact champion-turn spell availability, plus camp capture transitions, in existing engine-2 replays.
// Usage: NFS_REPLAY_ENGINE=2.0.0 node audit.mjs INNER_REPLAY OUT.json [until=500]
import fs from 'node:fs';
import {engine, defaultAssets, verifyAssets} from '../../../tools/replay/engine.mjs';
const [file, output, limit='500'] = process.argv.slice(2), until=Number(limit);
const dir=defaultAssets(); verifyAssets(dir); const E=await engine(dir);
E.load(fs.readFileSync(file));
const {X,check,dv,out:o,args,tsnap}=E;
const u=p=>dv().getUint32(p,true), i=p=>dv().getInt32(p,true);
const cheb=(a,b)=>Math.max(Math.abs(a.x-b.x),Math.abs(a.y-b.y));
check(X.Game_Visualiser_Timeline_GetMain(E.h,o)); const main=dv().getBigUint64(o,true);
check(X.Game_Visualiser_Timeline_Info(E.h,main,args,args+8,args+16)); const size=u(args);
check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
check(X.Game_API_Map_GetNumCampGroups(E.h,o)); const ng=u(o);
check(X.Game_API_Map_GetCampGroups(E.h,E.buf+2048,256,o));
const hs=[...new Uint32Array(X.memory.buffer,E.buf+2048,ng)];
const groups=hs.map(handle=>{
  check(X.Game_API_Map_CampGroup_Get(E.h,handle,o)); const gems=u(o),gold=u(o+4);
  check(X.Game_API_Map_CampGroup_GetNumCamps(E.h,handle,o)); const n=u(o);
  check(X.Game_API_Map_CampGroup_GetCampInfo(E.h,handle,E.buf+3072,256,o));
  const camps=[...new Uint32Array(X.memory.buffer,E.buf+3072,n)].map(c=>{
    check(X.Game_API_Map_CampInfo_Get(E.h,c,o)); return {id:c,x:i(o),y:i(o+4),type:i(o+8)};
  });
  return {handle,gems,gold,camps};
});
const campTiles=new Set(groups.flatMap(g=>g.camps.map(c=>`${c.x},${c.y}`)));
const kits={}, turns=[], frames=[]; let prev=null,current=null,lastRound=-1;
const lastCasts=new Map();
for (;;) {
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));
  const round=u(tsnap+8),phase=u(tsnap+24),outcome=u(tsnap+28),input=u(tsnap+56),sub=u(tsnap+104);
  const kind=u(tsnap+68),actor=u(tsnap+76),slot=u(tsnap+108),target=[i(tsnap+88),i(tsnap+92)];
  if (round>until || outcome) break;
  if ((!prev || input!==prev.input || sub!==prev.sub) && u(tsnap+72)===1 && [4,5,6,11,12,13,23].includes(kind)) {
    const a=[kind,...target,slot];
    if (current && current.id===actor) current.acts.push(a);
    if (kind===6) lastCasts.set(`${actor}:${slot}`, [round,campTiles.has(target.join(','))?'camp':'other']);
  }
  if (phase===10 && round!==lastRound) {
    const s=E.PC.I(dv(),tsnap);
    frames.push([round,s.champions.map(c=>[c.entity.index,c.team,c.position?.x??-1,c.position?.y??-1,c.alive?1:0,c.gold,c.items]),s.groups]);
    lastRound=round;
  }
  const c=u(tsnap+60);
  if (phase===10 && u(tsnap+20)!==0 && c!==0xffffffff && !(prev?.awaiting && prev.c===c && prev.round===round)) {
    check(X.Game_API_Champion_GetIdentity(E.h,E.perspective(2,0xffffffff),c,o)); const team=i(o),P=E.perspective(team,c);
    if (X.Game_API_Champion_Get(E.h,P,c,E.buf)===0 && (u(E.buf+40)&1)) {
      const x=i(E.buf+8),y=i(E.buf+12),state=u(E.buf+40),type=i(E.buf+4);
      const cds=[0,1].map(slot=>X.Game_API_Champion_GetCooldown(E.h,P,c,slot,o)===0?i(o):99);
      check(X.Game_Visualiser_ReadState(E.h,P,E.snap)); const view=E.PC.F(dv(),E.snap);
      const self=view.champions.find(k=>k.entity.index===c);
      if (self) {
        kits[type]=self.abilityProps;
        const foes=view.champions.filter(k=>k.team!==team && k.alive && k.position && k.health>0);
        const nd=Math.min(99,...foes.map(e=>cheb({x,y},e.position)));
        current={round,id:c,team,type,x,y,state,cds,nd,hp:self.health,max:self.maxHealth,
          foes:foes.map(e=>[e.entity.index,e.position.x,e.position.y]),
          recent:[0,1].map(slot=>lastCasts.get(`${c}:${slot}`)??null),acts:[]};
        turns.push(current);
      } else current=null;
    } else current=null;
  }
  prev={input,sub,round,c,awaiting:u(tsnap+20)!==0};
  if (u(tsnap+20)!==0 && input>=size) break;
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
}
fs.writeFileSync(output,JSON.stringify({until,kits,groups,turns,frames})); E.destroy();
