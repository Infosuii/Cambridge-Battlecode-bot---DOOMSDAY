// Home (spawn) visits per team (offline omniscient replay analysis only). A visit is an alive champion arriving on
// its team's spawn area from off-spawn (respawns after death excluded): "recalled" when it jumped more than 2 tiles
// in one round, otherwise walked. Records hp fraction and carried gold just before arriving, rounds since its last
// visit, and the hp fraction when it next leaves spawn.
// Usage: node home_trips.mjs <out.json> <replay>...
import fs from 'node:fs'; import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const [output, ...files] = process.argv.slice(2); const all = [];
for (const file of files) {
  E.load(fs.readFileSync(file)); const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  let lastRound = -1, prev = null, spawn = null;
  const T = [0, 1].map(() => ({ visits: 0, recalled: 0, walked: 0, hp_in: 0, gold_in: 0, gap: 0, gaps: 0, visits500: 0, hp_out: 0, outs: 0 }));
  const lastVisit = new Map(), onSpawn = new Map();
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    if (round !== lastRound && phase === 10) {
      const s = E.PC.I(d, tsnap); lastRound = round;
      if (!spawn && s.champions.length) spawn = [0, 1].map(t => s.champions.filter(c => c.team === t && c.position).map(c => c.position));
      const isSp = (c) => c.position && Math.min(...spawn[c.team].map(p => cheb(p, c.position))) <= 1;
      if (prev) for (const c of s.champions) {
        const p = prev.find(x => x.entity.index === c.entity.index);
        if (!p) continue;
        const was = onSpawn.get(c.entity.index) ?? true, now = c.alive && isSp(c);
        if (p.alive && c.alive && !was && now) {
          const t = T[c.team]; t.visits++; if (round <= 500) t.visits500++;
          if (cheb(p.position, c.position) > 2) t.recalled++; else t.walked++;
          t.hp_in += p.health / Math.max(1, p.maxHealth); t.gold_in += p.gold;
          if (lastVisit.has(c.entity.index)) { t.gap += round - lastVisit.get(c.entity.index); t.gaps++; }
          lastVisit.set(c.entity.index, round);
        }
        if (was && c.alive && !now && p.alive) { const t = T[c.team]; t.hp_out += c.health / Math.max(1, c.maxHealth); t.outs++; }
        onSpawn.set(c.entity.index, !c.alive || now);
      }
      prev = s.champions;
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  all.push({ id: path.basename(file).replace('.repl26a', ''), teams: T }); E.destroy();
}
fs.writeFileSync(output, JSON.stringify(all)); console.log(JSON.stringify({ replays: all.length, out: output }));
