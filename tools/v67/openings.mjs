// Offline opening routes from official replay states. No omniscient data enters a bot.
import fs from 'node:fs';
import path from 'node:path';
import {engine, defaultAssets, verifyAssets} from '../replay/engine.mjs';
const [output, ...files] = process.argv.slice(2);
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const cheb = (a,b) => Math.max(Math.abs(a.x-b.x), Math.abs(a.y-b.y));
const results=[];
for (const file of files) {
  E.load(fs.readFileSync(file));
  const {X,check,dv,out,args,buf,tsnap}=E;
  const u=o=>dv().getUint32(o,true), i=o=>dv().getInt32(o,true);
  check(X.Game_API_Map_GetNumCampGroups(E.h,out)); const ng=u(out);
  check(X.Game_API_Map_GetCampGroups(E.h,buf+2048,256,out));
  const handles=[...new Uint32Array(X.memory.buffer,buf+2048,ng)];
  const tileGroup=new Map(), groups=[];
  for (const h of handles) {
    check(X.Game_API_Map_CampGroup_Get(E.h,h,out)); const gems=u(out),gold=u(out+4);
    check(X.Game_API_Map_CampGroup_GetRespawnTime(E.h,h,out)); const respawn=i(out);
    check(X.Game_API_Map_CampGroup_GetNumCamps(E.h,h,out)); const n=u(out);
    check(X.Game_API_Map_CampGroup_GetCampInfo(E.h,h,buf+3072,256,out));
    const tiles=[];
    for (const c of [...new Uint32Array(X.memory.buffer,buf+3072,n)]) {
      check(X.Game_API_Map_CampInfo_Get(E.h,c,out));
      const at={x:i(out),y:i(out+4),type:i(out+8)}; tiles.push(at);
      tileGroup.set(at.x+','+at.y,groups.length);
    }
    groups.push({gems,gold,respawn,tiles});
  }
  check(X.Game_Visualiser_Timeline_GetMain(E.h,out)); const main=dv().getBigUint64(out,true);
  check(X.Game_Visualiser_Timeline_Info(E.h,main,args,args+8,args+16)); const size=u(args);
  check(X.Game_Visualiser_Timeline_Seek(E.h,main,0,0));
  let lastRound=-1,s=null,prev=null,firstFight=null;
  const actors=new Map(), hitters=new Map(), contests=new Set(), blocks=new Map();
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));
    const round=u(tsnap+8), phase=u(tsnap+24), outcome=u(tsnap+28), kind=u(tsnap+68), ak=u(tsnap+72),actor=u(tsnap+76);
    if ((round!==lastRound && phase===10)||outcome) {
      s=E.PC.I(dv(),tsnap); lastRound=round;
      for (const c of s.champions) {
        if (!actors.has(c.entity.index)) actors.set(c.entity.index,{id:c.entity.index,team:c.team,type:c.type,route:[],capture:[],firstContact:null,spawn:c.position});
        const a=actors.get(c.entity.index), p=prev?.champions.find(x=>x.entity.index===c.entity.index);
        if (c.alive&&c.position) {
          if (!a.firstContact && s.champions.some(e=>e.team!==c.team&&e.alive&&e.position&&cheb(e.position,c.position)<=6))
            a.firstContact={round,x:c.position.x,y:c.position.y};
          if (p?.alive && c.gems>p.gems && c.kills===p.kills) {
            const gi=tileGroup.get(c.position.x+','+c.position.y);
            if (gi!==undefined) a.capture.push({round,group:gi,gems:c.gems-p.gems,gold:Math.max(0,c.gold-p.gold)});
          }
          const gi=tileGroup.get(c.position.x+','+c.position.y);
          if (gi!==undefined && s.groups[gi] && !s.groups[gi].rewardAvailable &&
              !s.camps.some(cp=>cp.position&&tileGroup.get(cp.position.x+','+cp.position.y)===gi&&cp.health>0)) {
            const key=c.team+':'+gi; blocks.set(key,(blocks.get(key)??0)+1);
          }
        }
      }
      prev=s;
    }
    if (round>150||outcome||(u(tsnap+20)!==0&&u(tsnap+56)>=size)) break;
    if (ak===1&&kind===5&&s) {
      const a=actors.get(actor), x=i(tsnap+88),y=i(tsnap+92),gi=tileGroup.get(x+','+y);
      if (a && gi!==undefined) {
        if (a.route.at(-1)?.group!==gi) a.route.push({round,group:gi});
        const key=gi+':'+Math.floor(round/15); if(!hitters.has(key)) hitters.set(key,new Set());
        hitters.get(key).add(actor);
        if ([...hitters.get(key)].some(id=>actors.get(id)?.team!==a.team)) contests.add(gi);
      } else if (a&&!firstFight) firstFight={round,x,y,team:a.team};
    }
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
  }
  const crew={};
  for(const [key,ids] of hitters) {
    const group=key.split(':')[0];
    for(const team of [0,1]) {
      const n=[...ids].filter(id=>actors.get(id)?.team===team).length;
      if(n) crew[team+':'+group]=Math.max(crew[team+':'+group]??0,n);
    }
  }
  results.push({id:path.basename(file,'.repl26a'),groups,actors:[...actors.values()],firstFight,crew,contested:[...contests],spawnOccupancy:[...blocks]});
  E.destroy();
}
fs.writeFileSync(output,JSON.stringify(results));
console.log(JSON.stringify({replays:results.length,output}));
