// Map fingerprints a bot can compute in its draft turn: width, height, camp-group count, total group gems and gold.
// Reads one local replay per map (engine 2) and prints JSON {map: [w, h, groups, gems, gold]}.
// Usage: NFS_REPLAY_ENGINE=2.0.0 node tools/v67/c_map_keys.mjs OUT.json REPLAY... (file names start with the map name)
import fs from 'node:fs';
import path from 'node:path';
import {engine, defaultAssets, verifyAssets} from '../replay/engine.mjs';
const [output, ...files] = process.argv.slice(2);
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const res = {};
for (const file of files) {
  const map = path.basename(file).replace(/-[ab]-\d+\.repl26a$/, '');
  if (res[map]) continue;
  E.load(fs.readFileSync(file));
  const {X, check, dv, out, buf, tsnap} = E;
  const u = o => dv().getUint32(o, true);
  check(X.Game_API_Map_GetNumCampGroups(E.h, out)); const ng = u(out);
  check(X.Game_API_Map_GetCampGroups(E.h, buf + 2048, 256, out));
  const handles = [...new Uint32Array(X.memory.buffer, buf + 2048, ng)];
  let gems = 0, gold = 0;
  for (const h of handles) { check(X.Game_API_Map_CampGroup_Get(E.h, h, out)); gems += u(out); gold += u(out + 4); }
  check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
  const s = E.PC.I(dv(), tsnap);
  res[map] = [s.width ?? null, s.height ?? null, ng, gems, gold];
  E.destroy();
}
fs.writeFileSync(output, JSON.stringify(res, null, 1));
console.log(Object.keys(res).length, 'maps');
