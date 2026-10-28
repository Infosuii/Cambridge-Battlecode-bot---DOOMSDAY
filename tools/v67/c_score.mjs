// Banked gems of both teams every round of a raw engine-2 replay. Usage: node c_score.mjs REPLAY OUT.json -> [[round, a, b]]
import fs from 'node:fs';
import {engine, defaultAssets, verifyAssets} from '../replay/engine.mjs';
const [file, output] = process.argv.slice(2);
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
E.load(fs.readFileSync(file));
const {X, check, dv, out: o, args, tsnap} = E;
const u = p => dv().getUint32(p, true);
check(X.Game_Visualiser_Timeline_GetMain(E.h, o)); const main = dv().getBigUint64(o, true);
check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = u(args);
check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
const rows = []; let last = -1;
for (;;) {
  check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
  const round = u(tsnap + 8), phase = u(tsnap + 24), outcome = u(tsnap + 28);
  if ((round !== last && phase === 10) || outcome) { const s = E.PC.I(dv(), tsnap); rows.push([round, ...s.submittedGems.map(Number)]); last = round; }
  if (outcome || (u(tsnap + 20) !== 0 && u(tsnap + 56) >= size)) break;
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
}
fs.writeFileSync(output, JSON.stringify(rows)); E.destroy();
