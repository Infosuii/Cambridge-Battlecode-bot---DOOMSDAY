// Full offline loss audit; NFS_REPLAY_ENGINE selects the match's recorded engine. Never a bot input.
// Per round, per team: contact champion-rounds (an enemy champion within 6), local numbers in contact, PvP action use
// in contact (attacks/casts aimed at enemy champions), hp lost in contact, item/shard counts and max health. Per death:
// the victim's bag, hp 5 rounds earlier, allies/enemies within 4 and 8, whether it had attacked anyone in its last 5
// rounds, its distance to the nearest altar and its spawn, and the max-health ratio of nearby enemies to nearby allies.
// Usage: NFS_REPLAY_ENGINE=2.0.0 node research/top-losses-20261026/fight_audit.mjs <out.json> <replay.repl26a>...
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { engine, PINNED, verifyAssets } from '../../tools/replay/engine.mjs';
// A new CLI cache can retain the old WASM without its matching JS decoder. Select a complete, hash-verified bundle.
const cache = path.join(os.homedir(), 'AppData/Local/cambc/assets');
const dir = fs.readdirSync(cache).map(p => path.join(cache, p, 'visualiser/assets'))
  .find(p => Object.keys(PINNED).every(k => fs.existsSync(path.join(p, k))));
if (!dir) throw new Error('complete pinned replay assets unavailable');
verifyAssets(dir);
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
  let lastRound = -1, prevSnap = null, altars = null, spawns = [[], []], finalState = null;
  const hist = new Map(), act = new Map(), respawnRound = new Map(), stalls = new Map();
  const stagnations = [];
  const team = [0, 1].map(() => ({ contact: 0, outnumbered: 0, alone: 0, contactActs: 0, contactHpLost: 0, contactHpFrac: 0,
    hurtContact: 0, curve: {}, kills: 0, aliveRounds: 0, idle: 0, onSpawn: 0, deadRounds: 0 }));
  const deaths = [];
  const turnSeen = new Map(), lastContact = new Map(), propsById = new Map(), lastSpell = new Map();
  const spellAudit = [0, 1].map(() => ({ turns: 0, contactTurns: 0, entries: 0, offensiveEntries: 0,
    entryNoOffensiveReady: 0, entryWithCampCooldown: 0, casts: 0, hostileCasts: 0, campCasts: 0,
    byType: {} }));
  const spellExamples = [];
  let currentTurn = null;
  const heroes = {}; // `${team}:${type}` -> per-hero action use
  let finalRound = 0;
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), kind = d.getUint32(tsnap + 68, true), actor = d.getUint32(tsnap + 76, true);
    const actorKind = d.getUint32(tsnap + 72, true);
    const phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    const currentId = d.getUint32(tsnap + 60, true);
    if (phase === 10 && d.getUint32(tsnap + 20, true) && currentId !== 0xFFFFFFFF && turnSeen.get(currentId) !== round) {
      turnSeen.set(currentId, round);
      const spec = E.perspective(2, 0xFFFFFFFF);
      if (X.Game_API_Champion_GetIdentity(E.h, spec, currentId, E.out) === 0) {
        const tm = dv().getInt32(E.out, true), P = E.perspective(tm, currentId);
        if (X.Game_API_Champion_Get(E.h, P, currentId, E.buf) === 0) {
          const typ = dv().getInt32(E.buf + 4, true), loc = { x: dv().getInt32(E.buf + 8, true), y: dv().getInt32(E.buf + 12, true) };
          if (!propsById.has(currentId)) {
            check(X.Game_Visualiser_ReadState(E.h, P, E.snap));
            const view = E.PC.F(dv(), E.snap);
            propsById.set(currentId, view.champions.find(c => c.entity.index === currentId)?.abilityProps ?? []);
          }
          const props = propsById.get(currentId), enemies = [];
          if (X.Game_API_Champion_GetEnemies(E.h, P, E.buf + 512, 32, E.out) === 0) {
            const n = Math.min(32, dv().getUint32(E.out, true));
            const ids = [...new Uint32Array(X.memory.buffer, E.buf + 512, n)];
            for (const id of ids) if (X.Game_API_Champion_Get(E.h, P, id, E.buf) === 0) {
              const q = { x: dv().getInt32(E.buf + 8, true), y: dv().getInt32(E.buf + 12, true) };
              if (dv().getFloat32(E.buf + 16, true) > 0 && cheb(loc, q) <= 6) enemies.push(q);
            }
          }
          const near = enemies.length > 0, prior = lastContact.get(currentId);
          const entry = near && (!prior?.near || round - prior.round > 1);
          lastContact.set(currentId, { near, round });
          const z = spellAudit[tm]; z.turns++; if (near) z.contactTurns++;
          if (entry) {
            z.entries++;
            const offensive = props.map((p, slot) => ({ p, slot })).filter(({ p }) => [1, 2, 3, 4].includes(p.type) || p.type === 6 && p.modifier > 0);
            if (offensive.length) {
              z.offensiveEntries++;
              let ready = 0, campCooling = false;
              for (const { p, slot } of offensive) {
                if (X.Game_API_Champion_GetCooldown(E.h, P, currentId, slot, E.out) !== 0) continue;
                const cd = dv().getInt32(E.out, true);
                let charged = true;
                if (p.maxCharges > 0 && X.Game_API_Champion_GetCharges(E.h, P, currentId, slot, E.out) === 0) charged = dv().getUint32(E.out, true) > 0;
                if (cd <= 0 && charged) ready++;
                const last = lastSpell.get(`${currentId}:${slot}`);
                if (cd > 0 && last?.role === 'camp') {
                  campCooling = true;
                  if (spellExamples.length < 30) spellExamples.push({ round, team: tm, champion: currentId, type: typ, slot, cooldown: cd, campCastRound: last.round });
                }
              }
              if (!ready) z.entryNoOffensiveReady++;
              if (campCooling) z.entryWithCampCooldown++;
            }
          }
          currentTurn = { id: currentId, team: tm, type: typ, props };
        }
      }
    }
    if (actorKind === 1 && kind === 6 && currentTurn?.id === actor) {
      const slot = d.getUint32(tsnap + 108, true), prop = currentTurn.props[slot] ?? {};
      const q = { x: d.getInt32(tsnap + 88, true), y: d.getInt32(tsnap + 92, true) };
      const P = E.perspective(currentTurn.team, actor);
      check(X.Game_Visualiser_ReadState(E.h, P, E.snap));
      const view = E.PC.F(dv(), E.snap), radius = [3, 6].includes(prop.type) ? prop.radius ?? 0 : 0;
      const hostileKind = [2, 3, 4].includes(prop.type) || prop.type === 6 && prop.modifier > 0;
      const hit = hostileKind && view.champions.some(c => c.team !== currentTurn.team && c.position && c.alive && cheb(c.position, q) <= radius);
      const camp = hostileKind && !hit && view.camps.some(c => c.position && c.health > 0 && cheb(c.position, q) <= radius);
      const role = hit ? 'champion' : camp ? 'camp' : 'other';
      lastSpell.set(`${actor}:${slot}`, { round, role });
      const z = spellAudit[currentTurn.team];z.casts++;if(hit)z.hostileCasts++;if(camp)z.campCasts++;
      const h = z.byType[currentTurn.type] ??= { casts: 0, hostile: 0, camp: 0 };h.casts++;if(hit)h.hostile++;if(camp)h.camp++;
    }
    if ((round !== lastRound && phase === 10) || outcome) {
      const s = full();
      finalState = { outcome: s.outcome, submittedGems: s.submittedGems.map(Number),
        champions: s.champions.map(c => ({ id: c.entity.index, team: c.team, type: c.type, kills: c.kills, gems: c.gems })) };
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
        const standing = c.alive && c.position && prev?.alive && prev.position && c.position.x === prev.position.x && c.position.y === prev.position.y &&
          !a.move && !a.pvp && !a.camp && !a.anyCast && !a.channel && !spawns[c.team].some(q => cheb(q, c.position) <= 1);
        const pending = stalls.get(c.entity.index);
        if (standing) {
          if (pending) pending.endRound = round, pending.duration = round - pending.startRound + 1;
          else stalls.set(c.entity.index, { champion: c.entity.index, team: c.team, type: c.type, startRound: round, endRound: round, duration: 1, x: c.position.x, y: c.position.y, gems: c.gems });
        } else if (pending) {
          if (pending.duration >= 80) stagnations.push(pending);
          stalls.delete(c.entity.index);
        }
        if (prev && !prev.alive && c.alive) respawnRound.set(c.entity.index, round);
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
            spawnDist: Math.min(...spawns[c.team].map(q => cheb(q, p))), sinceRespawn: respawnRound.has(c.entity.index) ? lastRound - respawnRound.get(c.entity.index) : null, x: p.x, y: p.y });
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
      else if (kind === 11 || kind === 12 || kind === 18) f.channel = 1;
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  const base = path.basename(path.dirname(file)) === 'inner' ? path.dirname(path.dirname(file)) : path.dirname(file);
  for (const pending of stalls.values()) if (pending.duration >= 80) stagnations.push(pending);
  all.push({ id: path.basename(base), file, rounds: finalRound, finalState, teams: team, deaths, heroes, spellAudit, spellExamples, stagnations, measurement: { localRadius: 6, deathRadius: 8, respawnDetectedBy: 'round-boundary alive transition', stagnation: '80+ stationary round boundaries outside spawn, without movement, attacks, casts, recall or bank actions; may include deliberate camping or capture', castTargetClassification: 'legacy heroes counts approximate; spellAudit uses own-perspective state and ability radius, omits reset/shield from hostile-cast count; cooldowns measured at visible contact entry; readiness does not establish cast legality' } });
  E.destroy();
}
fs.writeFileSync(output, JSON.stringify(all));
console.log(JSON.stringify({ replays: all.length, out: output }));
