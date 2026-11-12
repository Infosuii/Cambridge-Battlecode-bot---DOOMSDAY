// PvP fight review for engine-2 replays (offline omniscient analysis only; never a bot input).
// Per round, per team: contact champion-rounds (an enemy champion within 6), local numbers in contact, PvP action use
// in contact (attacks/casts aimed at enemy champions), hp lost in contact, item/shard counts and max health. Per death:
// the victim's bag, hp 5 rounds earlier, allies/enemies within 4 and 8, whether it had attacked anyone in its last 5
// rounds, its distance to the nearest altar and its spawn, and the max-health ratio of nearby enemies to nearby allies.
// Usage: NFS_REPLAY_ENGINE=2.0.0 node tools/replay/fight_review.mjs <out.json> <replay.repl26a>...
import fs from 'node:fs';
import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir);
const E = await engine(dir);
const [output, ...files] = process.argv.slice(2);
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const shards = c => c.items.reduce((a, b) => a + b, 0);
// Ranged champion types (bc::champion_type order): Vesper, Cassi, Stellar, Prism, Willow, Tavi; the rest are melee.
const RANGED = new Set([1, 3, 5, 6, 8, 11]);
const all = [];
for (const file of files) {
  E.load(fs.readFileSync(file));
  const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  const full = () => { check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap)); return E.PC.I(dv(), tsnap); };
  let lastRound = -1, prevSnap = null, altars = null, spawns = [[], []];
  const hist = new Map(), act = new Map();
  const team = [0, 1].map(() => ({ contact: 0, outnumbered: 0, alone: 0, contactActs: 0, contactHpLost: 0, contactHpFrac: 0,
    hurtContact: 0, curve: {}, kills: 0, aliveRounds: 0, idle: 0, onSpawn: 0, deadRounds: 0 }));
  const deaths = [];
  const heroes = {}; // `${team}:${type}` -> per-hero action use
  let finalRound = 0;
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), kind = d.getUint32(tsnap + 68, true), actor = d.getUint32(tsnap + 76, true);
    const actorKind = d.getUint32(tsnap + 72, true);
    const phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    if ((round !== lastRound && phase === 10) || outcome) {
      const s = full();
      if (!altars) {
        // Spawns: where each team's champions stand at the first champion phase.
        for (const c of s.champions) if (c.position) spawns[c.team].push(c.position);
        altars = [];
      }
      const alive = s.champions.filter(c => c.alive && c.position);
      for (const c of s.champions) {
        const h = hist.get(c.entity.index) ?? []; hist.set(c.entity.index, h);
        const prev = h.at(-1);
        const a = act.get(c.entity.index) ?? {};
        if (prev && prev.alive && !c.alive) {
          const p = prev.position, last = h.slice(-5);
          const near = (r, same) => prevSnap.champions.filter(o => o.alive && o.position && o.entity.index !== c.entity.index &&
            (o.team === c.team) === same && cheb(o.position, p) <= r);
          const en8 = near(8, false), al8 = near(8, true);
          const mh = xs => xs.reduce((s2, o) => s2 + o.maxHealth, 0);
          deaths.push({ round: lastRound, id: c.entity.index, team: c.team, type: c.type, gems: prev.gems, gold: prev.gold,
            hp5: last[0] ? last[0].hp / Math.max(1, last[0].max_hp) : null, maxHp: prev.max_hp, shards: prev.shards,
            enemies4: near(4, false).length, allies4: near(4, true).length, enemies8: en8.length, allies8: al8.length,
            powerRatio: (mh(en8) + 1) / (mh(al8) + prev.max_hp), pvp5: last.reduce((x, y) => x + (y.pvp ? 1 : 0), 0),
            camp5: last.reduce((x, y) => x + (y.camp ? 1 : 0), 0), moves5: last.reduce((x, y) => x + (y.move ? 1 : 0), 0),
            spawnDist: Math.min(...spawns[c.team].map(q => cheb(q, p))), x: p.x, y: p.y });
        }
        if (!c.alive) team[c.team].deadRounds++;
        if (c.alive && c.position && prev && prev.alive) {
          const t0 = team[c.team];
          t0.aliveRounds++;
          const home = spawns[c.team].some(q => cheb(q, c.position) <= 1);
          if (home) t0.onSpawn++;
          else if (!a.pvp && !a.camp && !a.cast && !a.move && prev.position && prev.position.x === c.position.x && prev.position.y === c.position.y) t0.idle++;
        }
        if (c.alive && c.position && prev && prev.alive) {
          const en = alive.filter(o => o.team !== c.team && cheb(o.position, c.position) <= 6);
          if (en.length) {
            const al = alive.filter(o => o.team === c.team && o !== c && cheb(o.position, c.position) <= 6);
            const t = team[c.team];
            t.contact++;
            if (en.length > al.length + 1) t.outnumbered++;
            if (!al.length) t.alone++;
            if (a.pvp || a.cast) t.contactActs++;
            t.contactHpLost += Math.max(0, prev.hp - c.health);
            t.contactHpFrac += c.health / Math.max(1, c.maxHealth);
            if (c.health < 0.5 * c.maxHealth) t.hurtContact++;
          }
          const hk = `${c.team}:${c.type}`;
          const H = heroes[hk] ??= { alive: 0, contact: 0, inReach: 0, inReachActed: 0, pvpAtk: 0, pvpCast: 0, campAtk: 0, casts: 0, moves: 0 };
          H.alive++;
          if (a.pvp && a.pvpAtk) H.pvpAtk++;
          if (a.pvp && a.pvpCast) H.pvpCast++;
          if (a.camp) H.campAtk++;
          if (a.anyCast) H.casts++;
          if (a.move) H.moves++;
          if (en.length) {
            H.contact++;
            const reach = RANGED.has(c.type) ? 3 : 1;
            // An enemy was in basic-attack reach at the start of this round (previous positions).
            const inReach = prevSnap.champions.some(o => o.alive && o.position && o.team !== c.team && cheb(o.position, prev.position) <= reach);
            if (inReach) { H.inReach++; if (a.pvp) H.inReachActed++; }
          }
        }
        h.push({ alive: c.alive, position: c.position, hp: c.health, max_hp: c.maxHealth, gems: c.gems, gold: c.gold, shards: shards(c), ...a });
        if (h.length > 8) h.shift();
      }
      if (round % 100 === 0 && round > 0) for (const k of [0, 1]) {
        const cs = s.champions.filter(c => c.team === k);
        team[k].curve[round] = { shards: cs.reduce((x, c) => x + shards(c), 0), maxHp: cs.reduce((x, c) => x + c.maxHealth, 0),
          carried: cs.reduce((x, c) => x + c.gems, 0), gold: cs.reduce((x, c) => x + c.gold, 0), dead: cs.filter(c => !c.alive).length };
      }
      act.clear();
      prevSnap = s;
      lastRound = round;
      finalRound = round;
    }
    if (actorKind === 1 && prevSnap) {
      const f = act.get(actor) ?? {}; act.set(actor, f);
      if (kind === 5 || kind === 6) {
        const tx = d.getInt32(tsnap + 88, true), ty = d.getInt32(tsnap + 92, true);
        const me = prevSnap.champions.find(c => c.entity.index === actor);
        const hit = prevSnap.champions.find(c => c.alive && c.position && me && c.team !== me.team && cheb(c.position, { x: tx, y: ty }) <= 1);
        if (kind === 6) f.anyCast = 1;
        if (hit) { f.pvp = 1; if (kind === 5) f.pvpAtk = 1; else f.pvpCast = 1; } else if (kind === 5) f.camp = 1; else f.cast = 1;
      } else if (kind === 4 || kind === 23) f.move = 1;
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  const base = path.basename(path.dirname(file)) === 'inner' ? path.dirname(path.dirname(file)) : path.dirname(file);
  all.push({ id: path.basename(base), file, rounds: finalRound, teams: team, deaths, heroes });
  E.destroy();
}
fs.writeFileSync(output, JSON.stringify(all));
console.log(JSON.stringify({ replays: all.length, out: output }));
