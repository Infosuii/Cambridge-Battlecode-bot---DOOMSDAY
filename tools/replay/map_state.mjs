// The map as the engine built it (offline; for the map atlas): the replay's first state with champions placed.
// Prints one JSON object: state keys and the first element of each array, or with --dump the whole first state.
// Usage: node map_state.mjs <replay> [--dump]
import fs from 'node:fs';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
E.load(fs.readFileSync(process.argv[2])); const { X, check, dv, out, tsnap } = E;
check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); check(X.Game_Visualiser_Timeline_Seek(E.h, dv().getBigUint64(out, true), 0, 0));
let s;
for (;;) {
  check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap)); s = E.PC.I(dv(), tsnap);
  if (s.champions.length && s.camps.some(c => c.position)) break;
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
}
const big = (k, v) => typeof v === 'bigint' ? v.toString() : v;
if (process.argv.includes('--dump')) { console.log(JSON.stringify(s, big)); process.exit(0); }
const shape = {};
for (const k of Object.keys(s)) {
  const v = s[k];
  shape[k] = Array.isArray(v) ? { n: v.length, first: v[0] } : v;
}
console.log(JSON.stringify(shape, big).slice(0, 4000));
