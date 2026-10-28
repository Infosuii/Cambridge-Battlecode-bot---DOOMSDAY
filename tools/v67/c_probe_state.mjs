// Print the decoded per-round state fields of one champion at a given round (field discovery helper).
// Usage: NFS_REPLAY_ENGINE=2.0.0 node tools/v67/c_probe_state.mjs REPLAY ROUND
import fs from 'node:fs';
import {engine, defaultAssets, verifyAssets} from '../replay/engine.mjs';
const [file, roundArg] = process.argv.slice(2);
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
E.load(fs.readFileSync(file));
const {X, check, dv, out: o, args, tsnap} = E;
const u = p => dv().getUint32(p, true);
check(X.Game_Visualiser_Timeline_GetMain(E.h, o)); const main = dv().getBigUint64(o, true);
check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = u(args);
check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
for (;;) {
  check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
  const round = u(tsnap + 8), phase = u(tsnap + 24);
  if (round >= Number(roundArg) && phase === 10) {
    const s = E.PC.I(dv(), tsnap);
    console.log(Object.keys(s));
    console.log(JSON.stringify(s.camps[0]).slice(0,600)); console.log(JSON.stringify(s.groups[0]).slice(0,600)); console.log(JSON.stringify(s.champions[0], (k, v) => typeof v === 'bigint' ? Number(v) : v).slice(0, 3000));
    break;
  }
  if (u(tsnap + 20) !== 0 && u(tsnap + 56) >= size) break;
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
}
