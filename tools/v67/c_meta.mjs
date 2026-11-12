// Replay metadata for a raw engine-2 replay: top-level state fields at the first and last round (map size, scores,
// outcome). Usage: NFS_REPLAY_ENGINE=2.0.0 node tools/v67/c_meta.mjs REPLAY
import fs from 'node:fs';
import {engine, defaultAssets, verifyAssets} from '../replay/engine.mjs';
const [file] = process.argv.slice(2);
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
E.load(fs.readFileSync(file));
const {X, check, dv, out: o, args, tsnap} = E;
const u = p => dv().getUint32(p, true);
check(X.Game_Visualiser_Timeline_GetMain(E.h, o)); const main = dv().getBigUint64(o, true);
check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = u(args);
check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
let first = null, last = null, lastRound = -1, outcome = 0;
const scal = s => Object.fromEntries(Object.entries(s).filter(([k, v]) => typeof v !== 'object' || (Array.isArray(v) && v.length <= 4 && v.every(x => typeof x !== 'object'))).map(([k, v]) => [k, typeof v === 'bigint' ? Number(v) : v]));
for (;;) {
  check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
  const round = u(tsnap + 8), phase = u(tsnap + 24); outcome = u(tsnap + 28);
  if ((round !== lastRound && phase === 10) || outcome) {
    const s = E.PC.I(dv(), tsnap);
    if (!first) first = {keys: Object.keys(s), ...scal(s)};
    last = scal(s); lastRound = round;
  }
  if (outcome || (u(tsnap + 20) !== 0 && u(tsnap + 56) >= size)) break;
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
}
console.log(JSON.stringify({first, last, lastRound, outcome}, (k, v) => typeof v === 'bigint' ? Number(v) : v));
E.destroy();
