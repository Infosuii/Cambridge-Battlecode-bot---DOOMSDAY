// Offline diagnostic only: a native full-world scene at one champion turn.
import fs from 'node:fs';
import {engine,defaultAssets,verifyAssets} from './replay/engine.mjs';
if (process.env.NFS_REPLAY_ENGINE!=='2.0.0') throw new Error('Select engine 2.0.0');
const [file,roundText,bodyText,output]=process.argv.slice(2),round=+roundText,body=+bodyText;
const assets=defaultAssets();verifyAssets(assets);const E=await engine(assets);
E.load(fs.readFileSync(file));const {X,dv,check,out,tsnap}=E;
check(X.Game_GetBitboardMetadata(E.h,out));
const w=dv().getInt32(out,true),h=dv().getInt32(out+4,true),stride=dv().getUint32(out+16,true);
function board(getter) {
  check(getter(E.h,out));const pointer=dv().getUint32(out,true),tiles=[];
  for (let y=0;y<h;++y) for (let x=0;x<w;++x) {
    const word=dv().getBigUint64(pointer+8*((y>>3)*stride+(x>>3)),true);
    if ((word>>BigInt((y&7)*8+(x&7)))&1n) tiles.push([x,y]);
  }
  return tiles;
}
const walls=board(X.Game_GetWallBuffer),holes=board(X.Game_GetHoleBuffer),altars=board(X.Game_GetAltarBuffer);
check(X.Game_Visualiser_Timeline_GetMain(E.h,out));check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
let scene;
for (let step=0;step<200000;++step) {
  check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const s=E.PC.I(dv(),tsnap);
  if(s.round===round&&s.phase===14&&s.currentChampion===body){scene=s;break;}
  if(s.round>round)throw new Error('Requested turn not found');
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
}
if(!scene)throw new Error('Scene step bound exceeded');
const result={width:w,height:h,walls,holes,altars,round,body,champions:scene.champions,
  camps:scene.camps};
fs.writeFileSync(output,JSON.stringify(result));
const me=result.champions.find(c=>c.entity.index===body),p=me.position;
console.log(JSON.stringify({me,nearby_champions:result.champions.filter(c=>c.position&&Math.max(Math.abs(c.position.x-p.x),Math.abs(c.position.y-p.y))<=12),
  nearby_camps:result.camps.filter(c=>c.position&&Math.max(Math.abs(c.position.x-p.x),Math.abs(c.position.y-p.y))<=8)}));E.destroy();
