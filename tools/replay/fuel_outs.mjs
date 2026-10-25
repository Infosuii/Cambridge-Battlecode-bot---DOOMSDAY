// Fuel-out turns per champion type and team (offline replay analysis only; never a bot input).
// A fuel-out is step kind 26 (the champion's turn ended because its fuel ran out). Rows: replay id, then per team a map
// champion_type -> count, with the round of each team's first fuel-out.
// Usage: node fuel_outs.mjs <out.json> <replay>...
import fs from 'node:fs'; import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const [output, ...files] = process.argv.slice(2); const all = [];
for (const file of files) {
  E.load(fs.readFileSync(file)); const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  let lastRound = -1, s = null;
  const teams = [0, 1].map(() => ({ by_type: {}, by_round: { 250: 0, 500: 0, 1000: 0, all: 0 } }));
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    const kind = d.getUint32(tsnap + 68, true), actor = d.getUint32(tsnap + 76, true), ak = d.getUint32(tsnap + 72, true);
    if ((round !== lastRound && phase === 10) || outcome) { s = E.PC.I(d, tsnap); lastRound = round; }
    if (ak === 1 && s && kind === 26) {
      const c = s.champions.find(x => x.entity.index === actor);
      if (c) {
        const t = teams[c.team]; t.by_type[c.type] = (t.by_type[c.type] ?? 0) + 1; t.by_round.all++;
        for (const r of [250, 500, 1000]) if (round <= r) t.by_round[r]++;
      }
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  all.push({ id: path.basename(file).replace('.repl26a', ''), teams }); E.destroy();
}
fs.writeFileSync(output, JSON.stringify(all)); console.log(JSON.stringify({ replays: all.length, out: output }));
