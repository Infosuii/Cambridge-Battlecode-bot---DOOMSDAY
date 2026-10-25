// Basic-behaviour audit per champion (offline omniscient replay analysis only; never a bot input).
// Looks for the cheap failure patterns: gold carried instead of spent, alive turns with no action, waiting on the
// spawn at full health, gems lost on death, how often each champion type casts, wards, tributes and purchases.
// Step kinds: 4 move, 5 attack, 6 cast, 12 tribute start, 13 buy, 14 ward, 18 bank, 23 dash, 26 fuel-out.
// Usage: node sanity_audit.mjs <out.json> <replay>...
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
  let lastRound = -1, s = null, prev = null, spawn0 = null, acted = new Map();
  const A = new Map(); // actor -> stats
  const get = (c) => {
    let a = A.get(c.entity.index);
    if (!a) A.set(c.entity.index, a = { id: c.entity.index, team: c.team, type: c.type, alive: 0, idle: 0, fuel_out: 0,
      spawn_full_idle: 0, spawn_full_idle_max_run: 0, run: 0, casts: 0, attacks: 0, moves: 0, buys: 0, wards: 0,
      tributes: 0, banks: 0, deaths: 0, gems_lost: 0, big_bag_deaths: 0, gold_at: {}, gold_hoard_rounds: 0, max_gems: 0 });
    return a;
  };
  const finish = (st) => { // per-round accounting for the round that st began
    for (const c of st.champions) {
      const a = get(c);
      if (!c.alive || !c.position) { a.run = 0; continue; }
      a.alive++;
      const k = acted.get(c.entity.index) ?? 0;
      if (!k) a.idle++;
      const onSpawn = spawn0.some(p => p.team === c.team && cheb(p.position, c.position) <= 1);
      if (onSpawn && c.health >= c.maxHealth - 0.5 && !(k & 1)) { a.spawn_full_idle++; a.run++; a.spawn_full_idle_max_run = Math.max(a.spawn_full_idle_max_run, a.run); }
      else a.run = 0;
      if (c.gold >= 300) a.gold_hoard_rounds++;
      a.max_gems = Math.max(a.max_gems, c.gems);
    }
  };
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    const kind = d.getUint32(tsnap + 68, true), actor = d.getUint32(tsnap + 76, true), ak = d.getUint32(tsnap + 72, true);
    if ((round !== lastRound && phase === 10) || outcome) {
      const ns = E.PC.I(d, tsnap);
      if (!spawn0 && ns.champions.some(c => c.position)) spawn0 = ns.champions.filter(c => c.position).map(c => ({ team: c.team, position: c.position }));
      if (s && spawn0) finish(s);
      if (s) {
        const pm = new Map(s.champions.map(c => [c.entity.index, c]));
        for (const c of ns.champions) {
          const p = pm.get(c.entity.index); if (!p) continue;
          if (p.alive && !c.alive) { const a = get(c); a.deaths++; a.gems_lost += p.gems; if (p.gems >= 40) a.big_bag_deaths++; }
        }
      }
      for (const c of ns.champions) for (const r of [250, 500, 750]) if (round === r && c.alive) get(c).gold_at[r] = c.gold;
      prev = s; s = ns; lastRound = round; acted = new Map();
    }
    if (ak === 1 && s) {
      const c = s.champions.find(x => x.entity.index === actor);
      if (c) {
        const a = get(c);
        const bit = { 4: 1, 23: 1, 5: 2, 6: 4, 13: 8, 14: 16, 12: 32, 18: 64 }[kind] ?? 0;
        if (bit) acted.set(actor, (acted.get(actor) ?? 0) | bit);
        if (kind === 4) a.moves++; else if (kind === 5) a.attacks++; else if (kind === 6) a.casts++; else if (kind === 13) a.buys++;
        else if (kind === 14) a.wards++; else if (kind === 12) a.tributes++; else if (kind === 18) a.banks++; else if (kind === 26) a.fuel_out++;
      }
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  all.push({ id: path.basename(file).replace('.repl26a', ''), rounds: lastRound, actors: [...A.values()].map(({ run, ...r }) => r) }); E.destroy();
}
fs.writeFileSync(output, JSON.stringify(all)); console.log(JSON.stringify({ replays: all.length, out: output }));
