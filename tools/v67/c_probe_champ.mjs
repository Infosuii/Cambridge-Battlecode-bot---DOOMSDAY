// Print the fields of one champion in a replay state (decoder schema probe). Usage: node c_probe_champ.mjs REPLAY ROUND
import fs from 'node:fs';
import {engine, defaultAssets, verifyAssets} from '../replay/engine.mjs';
const [file, at] = process.argv.slice(2);
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
E.load(fs.readFileSync(file));
const {X, check, dv, out: o, args, tsnap} = E;
check(X.Game_Visualiser_Timeline_GetMain(E.h, o)); const main = dv().getBigUint64(o, true);
check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
for (;;) {
  check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
  const round = dv().getUint32(tsnap + 8, true), phase = dv().getUint32(tsnap + 24, true);
  if (round >= Number(at) && phase === 10) {
    const s = E.PC.I(dv(), tsnap);
    const c = s.champions[0];
    console.log(JSON.stringify(c, (k, v) => typeof v === 'bigint' ? Number(v) : v).slice(0, 3000));
    break;
  }
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
}
E.destroy();
