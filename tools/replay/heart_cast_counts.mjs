// Successful Heart ability casts through R500, from frozen local replays. Offline analysis only.
// Usage: node heart_cast_counts.mjs <extracted ledger replay directory> <out.json>
import fs from 'node:fs';
import path from 'node:path';
import {engine, defaultAssets, verifyAssets} from './engine.mjs';
const assets = defaultAssets(); verifyAssets(assets); const E = await engine(assets);
const [input, output] = process.argv.slice(2);
const rows = [];
for (const name of fs.readdirSync(input).filter(n => n.endsWith('.repl26a')).sort()) {
  E.load(fs.readFileSync(path.join(input, name)));
  const {X, check, dv, out, args, tsnap} = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  let hearts = null;
  const counts = [0, 1].map(() => ({actors: 0, shield: 0, dash: 0, dash_adjacent_living_camp: 0}));
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap)); const d = dv();
    const r = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true);
    const kind = d.getUint32(tsnap + 68, true), actor = d.getUint32(tsnap + 76, true);
    if (!hearts && phase === 10) {
      const s = E.PC.I(d, tsnap); hearts = new Map(s.champions.filter(c => c.type === 12).map(c => [c.entity.index, c.team]));
      for (const team of hearts.values()) counts[team].actors++;
    }
    if (r > 500) break;
    if (kind === 6 && d.getUint32(tsnap + 72, true) === 1 && hearts?.has(actor)) {
      const c = counts[hearts.get(actor)], slot = d.getUint32(tsnap + 108, true);
      if (slot === 0) c.shield++;
      if (slot === 1) {
        c.dash++;
        const x = d.getInt32(tsnap + 88, true), y = d.getInt32(tsnap + 92, true), s = E.PC.I(d, tsnap);
        if (s.camps.some(c => c.position && c.health > 0 && Math.max(Math.abs(c.position.x - x), Math.abs(c.position.y - y)) <= 1))
          c.dash_adjacent_living_camp++;
      }
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && d.getUint32(tsnap + 56, true) >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  const side = name.includes('-A-seed') ? 0 : 1;
  rows.push({game: name.replace('.repl26a', ''), candidate: counts[side], opponent: counts[1 - side]});
  E.destroy();
}
const totals = {};
for (const side of ['candidate', 'opponent']) {
  const sums = Object.fromEntries(['actors', 'shield', 'dash', 'dash_adjacent_living_camp'].map(k => [k, rows.reduce((sum, r) => sum + r[side][k], 0)]));
  totals[side] = {...sums, dash_per_actor: sums.dash / sums.actors,
    camp_adjacent_dash_per_actor: sums.dash_adjacent_living_camp / sums.actors};
}
const report = {games: rows.length, until_round: 500, totals,
  note: 'Counts successful cast events by actual ability slot. Camp adjacency is a post-cast geometric marker, not causal damage attribution; lethal casts can be missed by its living-camp filter.', per_game: rows};
fs.writeFileSync(output, JSON.stringify(report, null, 1) + '\n');
console.log(JSON.stringify({games: rows.length, totals}));
