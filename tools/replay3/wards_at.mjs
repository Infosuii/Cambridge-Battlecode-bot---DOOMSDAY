// Print the wards and control wards near a tile at chosen rounds. usage: node wards_at.mjs replay x y r1,r2,...
import fs from 'node:fs';
import {engine, defaultAssets, verifyAssets} from './engine.mjs';
const [file, xs, ys, rs] = process.argv.slice(2);
const X0 = +xs, Y0 = +ys, want = new Set(rs.split(',').map(Number));
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
E.load(fs.readFileSync(file));
const {X, check, dv, out, args, tsnap} = E;
check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
let last = -1, n = 0, shownKeys = false;
const ser = v => JSON.stringify(v, (k, x) => typeof x === 'bigint' ? Number(x) : x);
for (;;) {
  check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap)); const d = dv();
  const round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
  if (round !== last && phase === 10 && want.has(round)) {
    const s = E.PC.I(d, tsnap); last = round;
    const near = o => o.position && Math.max(Math.abs(o.position.x - X0), Math.abs(o.position.y - Y0)) <= 3;
    if (!shownKeys && s.wards.length) { console.log('ward fields:', Object.keys(s.wards[0]).join(',')); shownKeys = true; }
    console.log('round', round, 'wards near:', ser(s.wards.filter(near)), 'control:', ser(s.controlWards.filter(near)), 'all wards', s.wards.length);
  }
  if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
  if (++n > 4000000) break;
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
}
