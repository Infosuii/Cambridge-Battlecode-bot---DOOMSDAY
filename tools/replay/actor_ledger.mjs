// Per-actor opening ledger from pinned omniscient replay states (offline analysis only; never a bot input).
// For each champion and round window: how alive rounds were spent, capture/kill income, shared captures,
// spending and emblem completion rounds. Usage: node actor_ledger.mjs <out.json> <replay.repl26a>...
import fs from 'node:fs';
import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir);
const E = await engine(dir);
const [output, ...files] = process.argv.slice(2);
const WINDOWS = [100, 250, 500, 1000];
// Bench-only optional early cutoff; whole-life reports retain the default full game.
const UNTIL = Number(process.env.NFS_LEDGER_UNTIL ?? Infinity);
// Item index = family * 6 + stat * 2 + (1 if emblem). Families: monster, power, durability, treasure, jungle, home, bruiser.
const FAM = ['monster', 'power', 'durability', 'treasure', 'jungle', 'home', 'bruiser'];
const equip = (items) => items.reduce((s, n, i) => s + n * (i % 2 ? 150 : 30), 0);
const results = [];
for (const file of files) {
  E.load(fs.readFileSync(file));
  const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  const full = () => { check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap)); return E.PC.I(dv(), tsnap); };
  let lastRound = -1, prev = null, camps = new Map(), spawn = [new Set(), new Set()], final = null;
  const actors = new Map(); // champion index -> ledger
  const act = new Map();    // champion index -> activity flags this round
  const newLedger = (c) => ({ id: c.entity.index, team: c.team, type: c.type, w: {}, first_buy: null, emblems: {},
    cap_events: [], kill_gold: 0, deaths: [], gear: {} });
  const bucket = (L, r) => { for (const W of WINDOWS) if (r <= W) { L.w[W] ??= { alive: 0, dead: 0, spawn: 0, clear: 0, pvp: 0,
    cast: 0, cast_total: 0, dash_move_steps: 0, bank: 0, travel: 0, still: 0, cap_gold: 0, cap_gems: 0, caps: 0, shared_caps: 0, kill_gold: 0, kill_gems: 0, spend: 0, gold_income: 0 }; } };
  const add = (L, r, k, v = 1) => { for (const W of WINDOWS) if (r <= W) L.w[W][k] += v; };
  const closeRound = (s, round) => {
    // Attribute last round's activity and the state change between prev and s.
    const caps = [new Map(), new Map()]; // per team: capture timestamp -> actors gaining
    for (const c of s.champions) {
      if (!actors.has(c.entity.index)) actors.set(c.entity.index, newLedger(c));
      const L = actors.get(c.entity.index); bucket(L, round);
      if (WINDOWS.includes(s.round)) L.gear[s.round] = equip(c.items);
      const p = prev?.champions.find(x => x.entity.index === c.entity.index);
      const a = act.get(c.entity.index) ?? {};
      // Independent action counts: a cast followed by an attack still belongs in the cast total.
      add(L, round, 'cast_total', a.cast_total ?? 0);
      add(L, round, 'dash_move_steps', a.dash_move_steps ?? 0);
      if (!c.alive) { add(L, round, 'dead'); if (p?.alive) L.deaths.push({ round, gems: p.gems }); continue; }
      add(L, round, 'alive');
      const onSpawn = c.position && spawn[c.team].has(`${c.position.x},${c.position.y}`);
      if (a.bank) add(L, round, 'bank'); else if (a.pvp) add(L, round, 'pvp'); else if (a.clear) add(L, round, 'clear');
      else if (a.cast) add(L, round, 'cast'); else if (onSpawn) add(L, round, 'spawn');
      else if (p?.alive && p.position && p.position.x === c.position.x && p.position.y === c.position.y) add(L, round, 'still');
      else add(L, round, 'travel');
      if (!p || !p.alive) continue;
      const spent = Math.max(0, equip(c.items) - equip(p.items)) + 10 * c.consumables.reduce((x, n, i) => x + Math.max(0, n - (p.consumables[i] ?? 0)), 0);
      if (spent) { add(L, round, 'spend', spent); if (L.first_buy === null) L.first_buy = round; }
      c.items.forEach((n, i) => { if (i % 2 && n > (p.items[i] ?? 0)) { const f = FAM[Math.floor(i / 6)]; L.emblems[f] ??= round; } });
      const earned = c.gold - p.gold + spent;
      add(L, round, 'gold_income', Math.max(0, earned));
      const killed = c.kills > p.kills;
      if (killed) { add(L, round, 'kill_gold', Math.max(0, earned)); add(L, round, 'kill_gems', Math.max(0, c.gems - p.gems)); L.kill_gold += Math.max(0, earned); }
      else if (earned > 0 || c.gems > p.gems) {
        // A capture (or Marcella's tribute gold; banks are excluded by the gem drop).
        if (c.gems < p.gems) continue;
        add(L, round, 'cap_gold', Math.max(0, earned)); add(L, round, 'cap_gems', c.gems - p.gems); add(L, round, 'caps');
        const key = 'r'; const m = caps[c.team]; if (!m.has(key)) m.set(key, []); m.get(key).push(c);
        L.cap_events.push({ round, gold: earned, gems: c.gems - p.gems, x: c.position.x, y: c.position.y });
      }
    }
    // Captures received by several allies in the same round near one another were split rewards.
    for (const t of [0, 1]) for (const list of caps[t].values()) {
      for (const c of list) {
        const near = list.filter(o => o !== c && Math.max(Math.abs(o.position.x - c.position.x), Math.abs(o.position.y - c.position.y)) <= 3);
        if (near.length) add(actors.get(c.entity.index), round, 'shared_caps');
      }
    }
    act.clear();
  };
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), kind = d.getUint32(tsnap + 68, true), actor = d.getUint32(tsnap + 76, true);
    const actorKind = d.getUint32(tsnap + 72, true);
    const phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    if ((round !== lastRound && phase === 10) || outcome) {
      const s = full();
      if (!spawn[0].size && s.champions.length) for (const c of s.champions) if (c.position) {
        for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) spawn[c.team].add(`${c.position.x + dx},${c.position.y + dy}`);
      }
      if (prev) closeRound(s, lastRound);
      camps = new Map(s.camps.filter(c => c.position).map(c => [`${c.position.x},${c.position.y}`, c]));
      prev = s; lastRound = round; final = s;
    }
    if (actorKind === 1) {
      const f = act.get(actor) ?? {}; act.set(actor, f);
      if (kind === 5) { const tx = d.getInt32(tsnap + 88, true), ty = d.getInt32(tsnap + 92, true); if (camps.has(`${tx},${ty}`)) f.clear = 1; else f.pvp = 1; }
      else if (kind === 6) { f.cast = 1; f.cast_total = (f.cast_total ?? 0) + 1; }
      // Movement-step events are not an exhaustive count of dash ability casts; use kind6/slot1 for Heart casts.
      else if (kind === 23) f.dash_move_steps = (f.dash_move_steps ?? 0) + 1;
      else if (kind === 12 || kind === 18) f.bank = 1;
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size) || round > UNTIL + 1) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  results.push({ id: path.basename(file).replace('.repl26a', ''), rounds: final.round, submitted: final.submittedGems.map(Number),
    drafts: final.drafts, actors: [...actors.values()].map(L => ({ ...L, cap_events: L.cap_events.filter(e => e.round <= 500) })) });
  E.destroy();
}
fs.writeFileSync(output, JSON.stringify(results));
console.log(JSON.stringify({ replays: results.length, out: output }));
