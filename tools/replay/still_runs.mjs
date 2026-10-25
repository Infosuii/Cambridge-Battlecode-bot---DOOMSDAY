// Classify stationary no-attack stretches of one team's champions (offline omniscient analysis only).
// Usage: node still_runs.mjs <team 0|1> <until round> <out.json> <replay>...
import fs from 'node:fs';
import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir);
const E = await engine(dir);
const [teamArg, untilArg, output, ...files] = process.argv.slice(2);
const UNTIL = Number(untilArg);
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const all = [];
for (const file of files) {
  const team = teamArg === 'auto' ? null : Number(teamArg);
  E.load(fs.readFileSync(file));
  const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  const full = () => { check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap)); return E.PC.I(dv(), tsnap); };
  let lastRound = -1, prev = null, campTiles = new Map(), spawn = [new Set(), new Set()];
  const acted = new Set(), runs = new Map(), done = [];
  const fuel = new Set();
  const classify = (s, c) => {
    // Context at the start of a run: nearest camp tile (any state), whether it is alive, and enemies near.
    let best = null, bd = 1e9;
    for (const [k, t] of campTiles) { const d = cheb(t.pos, c.position); if (d < bd) { bd = d; best = t; } }
    const live = s.camps.find(x => x.position && best && x.position.x === best.pos.x && x.position.y === best.pos.y && x.health > 0);
    const enemies = s.champions.filter(o => o.team !== c.team && o.alive && o.position && cheb(o.position, c.position) <= 6).length;
    const allies = s.champions.filter(o => o.team === c.team && o !== c && o.alive && o.position && cheb(o.position, c.position) <= 3).length;
    return { camp_dist: bd, camp_type: best?.type, camp_alive: !!live, enemies, allies, hp: Math.round(100 * c.health / c.maxHealth), gems: c.gems, gold: c.gold };
  };
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), kind = d.getUint32(tsnap + 68, true), actor = d.getUint32(tsnap + 76, true);
    const actorKind = d.getUint32(tsnap + 72, true);
    const phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    if ((round !== lastRound && phase === 10) || outcome) {
      const s = full();
      for (const c of s.camps) if (c.position) campTiles.set(`${c.position.x},${c.position.y}`, { pos: c.position, type: c.type });
      if (!spawn[0].size && s.champions.length) for (const c of s.champions) if (c.position)
        for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) spawn[c.team].add(`${c.position.x + dx},${c.position.y + dy}`);
      if (prev && lastRound <= UNTIL) {
        for (const c of s.champions) {
          const T = team ?? c.team; if (c.team !== T) continue;
          const p = prev.champions.find(x => x.entity.index === c.entity.index);
          const id = c.entity.index;
          const still = c.alive && p?.alive && c.position && p.position && c.position.x === p.position.x && c.position.y === p.position.y
            && !acted.has(id) && !spawn[c.team].has(`${c.position.x},${c.position.y}`);
          if (still) {
            if (!runs.has(id)) runs.set(id, { actor: id, type: c.type, start: lastRound, len: 0, fuel: 0, gold_gain: 0, ctx: classify(prev, c), gold0: p.gold, gems0: p.gems });
            const r = runs.get(id); r.len++; if (fuel.has(id)) r.fuel++;
          } else if (runs.has(id)) {
            const r = runs.get(id); runs.delete(id);
            r.gold_gain = (p?.gold ?? 0) - r.gold0; r.gem_gain = (p?.gems ?? 0) - r.gems0;
            if (r.len >= 2) done.push(r);
          }
        }
      }
      acted.clear(); fuel.clear();
      prev = s; lastRound = round;
    }
    if (actorKind === 1) { if (kind === 5 || kind === 6 || kind === 12 || kind === 18) acted.add(actor); if (kind === 26) fuel.add(actor); }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size) || round > UNTIL + 1) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  all.push({ id: path.basename(file).replace('.repl26a', ''), runs: done });
  E.destroy();
}
fs.writeFileSync(output, JSON.stringify(all));
console.log(JSON.stringify({ replays: all.length, out: output }));
