// Camp groups of a raw engine-2 replay at a given round: everything the state exposes per group, plus spawns.
// Usage: NFS_REPLAY_ENGINE=2.0.0 node tools/v67/c_groups.mjs REPLAY [ROUND]
import fs from 'node:fs';
import {engine, defaultAssets, verifyAssets} from '../replay/engine.mjs';
const [file, at = '2'] = process.argv.slice(2);
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
E.load(fs.readFileSync(file));
const {X, check, dv, out: o, tsnap} = E;
const u = p => dv().getUint32(p, true);
check(X.Game_Visualiser_Timeline_GetMain(E.h, o)); const main = dv().getBigUint64(o, true);
check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
const J = v => JSON.stringify(v, (k, x) => typeof x === 'bigint' ? Number(x) : x);
for (;;) {
  check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
  if (u(tsnap + 8) >= Number(at) && u(tsnap + 24) === 10) {
    const s = E.PC.I(dv(), tsnap);
    console.log('GROUP0', J(s.groups[0]).slice(0, 1500));
    console.log('CAMP0', J(s.camps[0]).slice(0, 800));
    s.groups.forEach((g, i) => console.log('G', i, J(Object.fromEntries(Object.entries(g).filter(([k, v]) => typeof v !== 'object' || (Array.isArray(v) && v.length < 12)))).slice(0, 400)));
    break;
  }
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
}
E.destroy();
