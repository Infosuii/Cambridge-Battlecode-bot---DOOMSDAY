// Print the champion snapshot fields at one round of an engine-2 replay (schema probe; offline only).
// Usage: NFS_REPLAY_ENGINE=2.0.0 node probe_snapshot.mjs <replay.repl26a> <round>
import fs from 'node:fs';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const [file, roundArg] = process.argv.slice(2); const R = Number(roundArg);
E.load(fs.readFileSync(file)); const { X, check, dv, out, args, tsnap } = E;
check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
for (;;) {
  check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
  const d = dv(), round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true);
  if (round >= R && phase === 10) {
    const s = E.PC.I(d, tsnap);
    console.log(Object.keys(s));
    console.log(JSON.stringify(s.champions[0], (k, v) => typeof v === 'bigint' ? Number(v) : v, 1).slice(0, 4000));
    break;
  }
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
}
