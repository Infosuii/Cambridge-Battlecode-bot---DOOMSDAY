// Teleport hops by one team and what follows (offline omniscient analysis only). For each hop: origin, landing,
// distance of the landing from both spawns, enemies within 8 of the landing within the next 10 rounds, whether the
// hopper died within 30 rounds. Team = 'A'/'B' side of the candidate taken from the file name (-A- or -B-).
// Usage: node tp_effects.mjs <out.json> <replay>...
import fs from 'node:fs'; import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const [output, ...files] = process.argv.slice(2); const all = [];
for (const file of files) {
  const cand = /-A[-.]/.test(path.basename(file)) ? 0 : 1;
  E.load(fs.readFileSync(file)); const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  let lastRound = -1, s = null, spawn = null; const hops = [], open = [];
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), kind = d.getUint32(tsnap + 68, true), actor = d.getUint32(tsnap + 76, true), round = d.getUint32(tsnap + 8, true);
    const pos = d.getUint32(tsnap + 56, true), outcome = d.getUint32(tsnap + 28, true), phase = d.getUint32(tsnap + 24, true);
    if (round !== lastRound && phase === 10) {
      s = E.PC.I(d, tsnap); lastRound = round;
      if (!spawn) spawn = [0, 1].map(t => s.champions.filter(c => c.team === t && c.position).map(c => c.position));
      for (const h of open) {
        if (round > h.round + 30) continue;
        const c = s.champions.find(x => x.entity.index === h.actor);
        if (!c.alive && !h.died) h.died = round - h.round;
        if (round <= h.round + 13) for (const e of s.champions) if (e.team !== cand && e.alive && e.position && cheb(e.position, h.to) <= 8) h.enemies_near = (h.enemies_near ?? 0) + 1;
      }
    }
    if (kind === 22 && s) {
      const c = s.champions.find(x => x.entity.index === actor);
      if (c && c.team === cand) {
        const st = E.PC.I(d, tsnap).step;
        const dmin = (pts) => Math.min(...pts.map(p => cheb(p, st.to)));
        const h = { round, actor, type: c.type, from: c.position, to: st.to, own_spawn: dmin(spawn[cand]), enemy_spawn: dmin(spawn[1 - cand]), gems: c.gems };
        hops.push(h); open.push(h);
      }
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  all.push({ id: path.basename(file).replace('.repl26a', ''), hops }); E.destroy();
}
fs.writeFileSync(output, JSON.stringify(all)); console.log(JSON.stringify({ replays: all.length, out: output }));
