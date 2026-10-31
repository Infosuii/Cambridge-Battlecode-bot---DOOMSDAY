// Dedicated correctness maps, encoded and integrity-checked by the official
// engine's MapBuilder API. They are separate from the 70 competition maps.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { engine, defaultAssets, verifyAssets, PINNED } from './replay/engine.mjs';
if (process.env.NFS_REPLAY_ENGINE!=='2.0.0') throw new Error('Set NFS_REPLAY_ENGINE=2.0.0');
const assets=defaultAssets(); verifyAssets(assets);
const E=await engine(assets), {X,check,dv,out}=E;
const destination=path.resolve(process.argv[2]??'tests/dz/maps');
const key=process.argv[3]??'isolated-monolith';
const layouts={
  'isolated-monolith':[[4,10,10]],
  'isolated-wolf':[[0,10,10]],
  'four-pick':[[0,10,10]],
  'isolated-elk':[[1,10,10]],
  'isolated-golem':[[5,10,10]],
  'cluster-line':Array.from({length:12},(_,i)=>[3,6+i,6]),
  'prospector':[...Array.from({length:12},(_,i)=>[3,6+i,6]),[2,8,12],[2,8,16],[2,9,16],[3,5,15],[0,8,22]],
  'camp-modifiers':[...Array.from({length:24},(_,i)=>[3,6+i%6,6+Math.floor(i/6)]),[0,12,14]],
  'tribute-passive':[...Array.from({length:12},(_,i)=>[3,6+i,6]),...Array.from({length:14},(_,i)=>[2,6+i,12]),[2,5,15],[2,8,15],[2,9,15]],
  'tribute-passive-mid':[...Array.from({length:12},(_,i)=>[3,6+i,6]),...Array.from({length:5},(_,i)=>[2,6+i,12]),[2,5,15],[2,8,15],[2,9,15]],
  'tribute-passive-boundary':[...Array.from({length:12},(_,i)=>[3,6+i,6]),...Array.from({length:10},(_,i)=>[2,6+i,12]),[2,5,15],[2,8,15],[2,9,15]],
  'group-visibility':Array.from({length:12},(_,i)=>[3,6+i,12]),
  'recovery-shop':[...Array.from({length:12},(_,i)=>[3,6+i,6]),[0,10,12]],
  'capture-contest':[[2,14,15],[2,15,15]],
  'siege-ring-golem':[[5,14,15]],
  'siege-two-layer':[[2,12,15],[5,14,15]],
};
if (!Object.hasOwn(layouts,key)) throw new Error('Unknown fixture '+key);
fs.mkdirSync(destination,{recursive:true});
check(X.MapBuilder_Create(31,31,2,out)); // Rotational180, matching official editor enum.
const builder=dv().getBigUint64(out,true);
try {
  const picks=key==='four-pick'?4:3;
  check(X.MapBuilder_SetNumChampsPerTeam(builder,picks));
  [1,1,4,4].forEach((value,index)=>dv().setInt32(out+index*4,value,true));
  check(X.MapBuilder_SetTeamASpawnArea(builder,out));
  const altar=key==='capture-contest'?[15,10]:[15,15];
  check(X.MapBuilder_AddAltar(builder,...altar));
  const walls=key==='siege-ring-golem'?[[14,14],[15,14],[16,14],[14,16],[15,16],[16,16]]:
    key==='siege-two-layer'?Array.from({length:7},(_,i)=>[[12+i,14],[12+i,16]]).flat():[];
  for(const tile of walls)check(X.MapBuilder_AddWall(builder,...tile));
  for (const [kind,x,y] of layouts[key]) check(X.MapBuilder_AddCamp(builder,kind,x,y,out));
  check(X.MapBuilder_VerifyIntegrity(builder));
  check(X.MapBuilder_Encode(builder,out,out+4));
  const pointer=dv().getUint32(out,true), length=dv().getUint32(out+4,true);
  const bytes=Buffer.from(new Uint8Array(X.memory.buffer,pointer,length));
  const name=key+'.map26a';
  fs.writeFileSync(path.join(destination,name),bytes,{flag:'wx'});
  const manifest={purpose:'controlled engine conformance only; no strategy or strength claims',engine:'2.0.0',
    generator_sha256:crypto.createHash('sha256').update(fs.readFileSync(new URL(import.meta.url))).digest('hex'),
    official_assets:PINNED,width:31,height:31,symmetry:'rotational180',picks,spawnA:[1,1,4,4],
    altar,camps:layouts[key],automatic_symmetry:true,terrain:walls.length?'walled altar pocket; see exact camps and walls below':'open ground; no walls, bushes or holes',
    ...(walls.length?{walls}:{}),
    file:name,bytes:length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')};
  fs.writeFileSync(path.join(destination,key==='isolated-monolith'?'manifest.json':key+'.manifest.json'),JSON.stringify(manifest,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify(manifest));
} finally { X.MapBuilder_Destroy(builder); }
