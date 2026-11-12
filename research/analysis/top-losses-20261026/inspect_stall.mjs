// Inspect a champion's actual legal state, visible camps and nearby allies at a recorded long stall.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {engine,PINNED,verifyAssets} from '../../tools/replay/engine.mjs';
const cache=path.join(os.homedir(),'AppData/Local/cambc/assets');
const assets=fs.readdirSync(cache).map(d=>path.join(cache,d,'visualiser/assets')).find(d=>Object.keys(PINNED).every(n=>fs.existsSync(path.join(d,n))));
verifyAssets(assets);const E=await engine(assets);
const [output,file,roundText,champText]=process.argv.slice(2),target=Number(roundText),champ=Number(champText);
E.load(fs.readFileSync(file));const{X,dv,check,out,args,tsnap}=E;
check(X.Game_Visualiser_Timeline_GetMain(E.h,out));const timeline=dv().getBigUint64(out,true);
check(X.Game_Visualiser_Timeline_Seek(E.h,timeline,0,0));
for(;;){
 check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap));const d=dv(),r=d.getUint32(tsnap+8,true),phase=d.getUint32(tsnap+24,true);
 if(r>=target&&phase===10&&d.getUint32(tsnap+20,true)&&d.getUint32(tsnap+60,true)===champ){
  check(X.Game_API_Champion_GetIdentity(E.h,E.perspective(2,0xFFFFFFFF),champ,out));const team=dv().getInt32(out,true),P=E.perspective(team,champ);
  check(X.Game_Visualiser_ReadState(E.h,P,E.snap));const view=E.PC.F(dv(),E.snap),self=view.champions.find(c=>c.entity.index===champ);
  check(X.Game_API_Champion_Get(E.h,P,champ,E.buf));const state=dv().getUint32(E.buf+40,true);
  check(X.Game_GetBitboardMetadata(E.h,args));const width=dv().getInt32(args,true),height=dv().getInt32(args+4,true),stride=dv().getUint32(args+16,true);
  const bytes=Math.max(4096,stride*dv().getUint32(args+12,true)*8),mask=X.Engine_Malloc(bytes);
  check(X.Game_API_Champion_GetMovementMask(E.h,P,champ,mask));
  const allowed=(x,y)=>x>=0&&y>=0&&x<width&&y<height&&!!(dv().getBigUint64(mask+8*((y>>3)*stride+(x>>3)),true)&(1n<<BigInt((y&7)*8+(x&7))));
  const legalNeighbors=[];
  for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++)if((dx||dy)&&allowed(self.position.x+dx,self.position.y+dy))legalNeighbors.push({x:self.position.x+dx,y:self.position.y+dy});
  X.Engine_Free(mask);
  check(X.Game_Visualiser_ReadState(E.h,E.perspective(2,0xFFFFFFFF),E.snap));const omni=E.PC.F(dv(),E.snap);
  const dist=c=>c.position&&self.position?Math.max(Math.abs(c.position.x-self.position.x),Math.abs(c.position.y-self.position.y)):9999;
  const result={round:r,team,champion:champ,infoState:state,canMove:!!(state&(1<<3)),canAttack:!!(state&(1<<4)),legalNeighbors,
   worldLiveCamps:omni.camps.filter(c=>c.health>0).length,self,
   nearbyChampions:view.champions.filter(c=>c.entity.index!==champ&&dist(c)<=8),nearbyCamps:view.camps.filter(c=>dist(c)<=8),groups:view.groups};
  fs.writeFileSync(output,JSON.stringify(result,(k,v)=>typeof v==='bigint'?Number(v):v,1));break;
 }
 if(d.getUint32(tsnap+28,true))throw new Error('requested own turn not found');
 check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
}
E.destroy();
