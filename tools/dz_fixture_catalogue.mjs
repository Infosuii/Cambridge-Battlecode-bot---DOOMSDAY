// Offline fixture selection only: find camp geometries in existing replays.
// No game policy, performance tuning or per-map strategy is generated here.
import fs from 'node:fs';
import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './replay/engine.mjs';
const directory=process.argv[2], output=process.argv[3];
const assets=defaultAssets(); verifyAssets(assets); const E=await engine(assets);
const rows=[];
for (const name of fs.readdirSync(directory).filter(x=>x.endsWith('.repl26a')).sort()) {
  E.load(fs.readFileSync(path.join(directory,name)));
  const { X,check,dv,out,tsnap }=E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h,out));
  check(X.Game_Visualiser_Timeline_Seek(E.h,dv().getBigUint64(out,true),0,0));
  let snapshot;
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h,tsnap)); snapshot=E.PC.I(dv(),tsnap);
    if (snapshot.champions.length&&snapshot.camps.some(c=>c.position)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h,1));
  }
  const camps=new Map(snapshot.camps.filter(c=>c.position).map(c=>[`${c.position.x},${c.position.y}`,c]));
  const seen=new Set(), candidates=[];
  for (const [key] of camps) {
    if (seen.has(key)) continue;
    const todo=[key], members=[]; seen.add(key);
    while (todo.length) {
      const current=todo.pop(), c=camps.get(current); members.push(c);
      for (const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]) {
        const next=`${c.position.x+dx},${c.position.y+dy}`;
        if (camps.has(next)&&!seen.has(next)) { seen.add(next); todo.push(next); }
      }
    }
    const types=members.map(c=>c.type);
    if (members.length>=2&&types.some(t=>t===2)) candidates.push({tiles:members.map(c=>c.position),types,
      harmless:types.every(t=>t===2||t===3),oneWolf:types.filter(t=>t===0).length===1&&types.every(t=>[0,2,3].includes(t))});
  }
  rows.push({map:name.replace('.repl26a',''),candidates});
}
fs.writeFileSync(output,JSON.stringify({purpose:'engine fixture geometry selection only',rows},null,2)+'\n');
console.log(rows.filter(r=>r.candidates.some(c=>c.harmless||c.oneWolf)).map(r=>({map:r.map,
  candidates:r.candidates.filter(c=>c.harmless||c.oneWolf).map(c=>({types:c.types,harmless:c.harmless,oneWolf:c.oneWolf}))})));
