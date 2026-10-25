// Per-team counts of champion action kinds by round window (offline replay analysis only): moves, attacks, casts,
// recalls, tribute starts/banks, purchases, wards, dashes, teleport starts (21), altar-lock placements (20).
// Usage: node team_kinds.mjs <out.json> <replay>...
import fs from 'node:fs'; import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const NAME = { 4: 'move', 5: 'attack', 6: 'cast', 11: 'recall', 12: 'submit_start', 13: 'buy', 14: 'ward', 18: 'submit_bank', 20: 'lock', 21: 'teleport', 23: 'dash', 26: 'fuel_out' };
const [output, ...files] = process.argv.slice(2); const all = [];
for (const file of files) {
  E.load(fs.readFileSync(file)); const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  let team = new Map(); const c = [{}, {}];
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), kind = d.getUint32(tsnap + 68, true), actor = d.getUint32(tsnap + 76, true), ak = d.getUint32(tsnap + 72, true);
    const round = d.getUint32(tsnap + 8, true), pos = d.getUint32(tsnap + 56, true), outcome = d.getUint32(tsnap + 28, true), phase = d.getUint32(tsnap + 24, true);
    if (!team.size && phase === 10) { const s = E.PC.I(d, tsnap); team = new Map(s.champions.map(x => [x.entity.index, x.team])); }
    if (ak === 1 && team.has(actor) && NAME[kind]) {
      const t = c[team.get(actor)], w = round <= 250 ? 'r250' : round <= 500 ? 'r500' : 'late';
      t[NAME[kind]] = (t[NAME[kind]] ?? 0) + 1; t[NAME[kind] + '_' + w] = (t[NAME[kind] + '_' + w] ?? 0) + 1;
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  all.push({ id: path.basename(file).replace('.repl26a', ''), teams: c }); E.destroy();
}
fs.writeFileSync(output, JSON.stringify(all)); console.log(JSON.stringify({ replays: all.length, out: output }));
