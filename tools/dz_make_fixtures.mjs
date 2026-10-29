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
fs.mkdirSync(destination,{recursive:true});
check(X.MapBuilder_Create(31,31,2,out)); // Rotational180, matching official editor enum.
const builder=dv().getBigUint64(out,true);
try {
  check(X.MapBuilder_SetNumChampsPerTeam(builder,3));
  [1,1,4,4].forEach((value,index)=>dv().setInt32(out+index*4,value,true));
  check(X.MapBuilder_SetTeamASpawnArea(builder,out));
  check(X.MapBuilder_AddAltar(builder,15,15));
  check(X.MapBuilder_AddCamp(builder,4,10,10,out)); // Monolith; editor mirrors it.
  check(X.MapBuilder_VerifyIntegrity(builder));
  check(X.MapBuilder_Encode(builder,out,out+4));
  const pointer=dv().getUint32(out,true), length=dv().getUint32(out+4,true);
  const bytes=Buffer.from(new Uint8Array(X.memory.buffer,pointer,length));
  const name='isolated-monolith.map26a';
  fs.writeFileSync(path.join(destination,name),bytes,{flag:'wx'});
  const manifest={purpose:'controlled engine conformance only; no strategy or strength claims',engine:'2.0.0',
    generator_sha256:crypto.createHash('sha256').update(fs.readFileSync(new URL(import.meta.url))).digest('hex'),
    official_assets:PINNED,width:31,height:31,symmetry:'rotational180',picks:3,spawnA:[1,1,4,4],
    altar:[15,15],monolith:[10,10],automatic_symmetry:true,terrain:'open ground; no walls, bushes or holes',
    file:name,bytes:length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')};
  fs.writeFileSync(path.join(destination,'manifest.json'),JSON.stringify(manifest,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify(manifest));
} finally { X.MapBuilder_Destroy(builder); }
