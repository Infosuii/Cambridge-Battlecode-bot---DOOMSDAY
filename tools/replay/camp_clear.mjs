// Camp-clearing efficiency per team (offline omniscient replay analysis only; never a bot input).
// Camp groups are 4-connected camp tiles of the first state. A clear runs from the first round any camp of the group
// has lost health to the round the last one dies. It is attributed to a team when only that team's champions made
// basic attacks on the group during it ("solo clears"); contested clears are counted separately.
// For each solo clear: group max health, gold/gems value, duration, attackers, and the team's "engaged" champion-rounds
// (alive champions within attack range + 1 of a live camp of the group, no enemy champion within 6). Per champion-round
// while engaged: whether it made a basic attack on the group, cast anything, or moved.
// Usage: node camp_clear.mjs <out.json> <replay>...
import fs from 'node:fs'; import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const RANGED = new Set([1, 3, 5, 6, 8, 11]);
const VAL = { 0: [40, 4, 1350], 1: [90, 15, 2400], 2: [0, 7, 120], 3: [20, 0, 120], 4: [300, 200, 20000], 5: [160, 36, 5000] };
const [output, ...files] = process.argv.slice(2); const all = [];
for (const file of files) {
  E.load(fs.readFileSync(file)); const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  let lastRound = -1, groupOf = null, groups = [], s = null, spawn0 = null;
  const G = []; // per group: state
  const T = [0, 1].map(() => ({ solo_clears: 0, contested: 0, hp: 0, gold: 0, gems: 0, duration: 0, engaged: 0, engaged_attack: 0,
    engaged_cast: 0, engaged_move: 0, attackers: 0, hp_harmless: 0, by_type: {} }));
  let acts = new Map(); // actor -> {attackTiles:Set, cast, moved}
  const finishRound = (st) => {
    // engaged accounting for the round just played (state st = start-of-round state)
    for (const g of G) {
      if (!g.active) continue;
      const live = g.tiles.map(k => st.campAt.get(k)).filter(c => c && c.health > 0);
      if (!live.length) continue;
      for (const c of st.s.champions) {
        if (!c.alive || !c.position) continue;
        const rng = RANGED.has(c.type) ? 3 : 1; // champion_type: Vesper, Cassi, Stellar, Prism, Willow, Tavi are ranged
        const near = live.some(cp => cheb(cp.position, c.position) <= Math.max(1, rng) + 1 + 2);
        if (!near) continue;
        if (st.s.champions.some(o => o.team !== c.team && o.alive && o.position && cheb(o.position, c.position) <= 6)) continue;
        const a = acts.get(c.entity.index) ?? {};
        g.eng[c.team]++;
        if (a.attack && [...a.attack].some(k => g.tileSet.has(k))) { g.att[c.team]++; g.attackers[c.team].add(c.entity.index); }
        else if (a.cast) g.cast[c.team]++;
        else if (a.moved) g.move[c.team]++;
      }
    }
  };
  let st = null;
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    const kind = d.getUint32(tsnap + 68, true), actor = d.getUint32(tsnap + 76, true), ak = d.getUint32(tsnap + 72, true);
    if ((round !== lastRound && phase === 10) || outcome) {
      s = E.PC.I(d, tsnap);
      if (st) finishRound(st);
      acts = new Map();
      const campAt = new Map(s.camps.filter(c => c.position).map(c => [`${c.position.x},${c.position.y}`, c]));
      if (!groupOf) {
        groupOf = new Map();
        for (const [k] of campAt) {
          if (groupOf.has(k)) continue;
          const gi = groups.length; groups.push([]); const stack = [k]; groupOf.set(k, gi);
          while (stack.length) { const t = stack.pop(); groups[gi].push(t); const [x, y] = t.split(',').map(Number);
            for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const n = `${x + dx},${y + dy}`; if (campAt.has(n) && !groupOf.has(n)) { groupOf.set(n, gi); stack.push(n); } } }
          const types = groups[gi].map(t => campAt.get(t).type);
          G.push({ tiles: groups[gi], tileSet: new Set(groups[gi]), types, hp: types.reduce((a, t) => a + VAL[t][2], 0),
            gold: types.reduce((a, t) => a + VAL[t][0], 0), gems: types.reduce((a, t) => a + VAL[t][1], 0),
            harmless: types.every(t => t === 2 || t === 3), active: false });
        }
      }
      for (const g of G) {
        const cs = g.tiles.map(k => campAt.get(k));
        const live = cs.filter(c => c && c.health > 0);
        const damaged = live.some(c => c.health < VAL[c.type][2] - 0.5) || (live.length && live.length < g.tiles.length);
        if (!g.active && damaged && live.length) {
          g.active = true; g.start = round; g.eng = [0, 0]; g.att = [0, 0]; g.cast = [0, 0]; g.move = [0, 0];
          g.attackers = [new Set(), new Set()]; g.hitters = new Set(); g.hp0 = new Map(); g.hpmin = new Map(); g.died = new Set();
          for (const c of s.champions) if (c.alive) { g.hp0.set(c.entity.index, c.health); g.hpmin.set(c.entity.index, c.health); }
        } else if (g.active && live.length) {
          for (const c of s.champions) {
            if (!g.hp0.has(c.entity.index)) { if (c.alive) { g.hp0.set(c.entity.index, c.health); g.hpmin.set(c.entity.index, c.health); } continue; }
            if (!c.alive) g.died.add(c.entity.index); else g.hpmin.set(c.entity.index, Math.min(g.hpmin.get(c.entity.index), c.health));
          }
        }
        if (g.active && !live.length) {
          g.active = false;
          const teams = [...g.hitters];
          if (teams.length === 1) {
            const t = T[teams[0]]; t.solo_clears++;
            {
              // Where: the group's nearest camp tile against each team's starting positions (own half / enemy half / middle).
              const sp = [0, 1].map(tm => spawn0.filter(c => c.team === tm).map(c => c.position));
              const dist = tm => Math.min(...g.tiles.map(k => { const [x, y] = k.split(',').map(Number); return Math.min(...sp[tm].map(p => cheb(p, { x, y }))); }));
              const own = dist(teams[0]), opp = dist(1 - teams[0]);
              const side = own < opp * 0.8 ? 'own' : opp < own * 0.8 ? 'enemy' : 'middle';
              t[`clears_${side}`] = (t[`clears_${side}`] ?? 0) + 1; t[`gold_${side}`] = (t[`gold_${side}`] ?? 0) + g.gold; t[`gems_${side}`] = (t[`gems_${side}`] ?? 0) + g.gems;
              if (round - g.start >= 0 && g.start <= 500) t[`early_${side}`] = (t[`early_${side}`] ?? 0) + 1;
            } t.hp += g.hp; t.gold += g.gold; t.gems += g.gems; t.duration += round - g.start;
            t.engaged += g.eng[teams[0]]; t.engaged_attack += g.att[teams[0]]; t.engaged_cast += g.cast[teams[0]]; t.engaged_move += g.move[teams[0]];
            t.attackers += g.attackers[teams[0]].size; if (g.harmless) t.hp_harmless += g.hp;
            const key = g.harmless ? 'harmless' : g.types.includes(4) ? 'monolith' : g.types.includes(5) ? 'golem' : g.types.includes(1) ? 'elk' : 'wolf';
            const b = t.by_type[key] ??= { n: 0, hp: 0, engaged: 0, duration: 0, attack: 0 };
            b.n++; b.hp += g.hp; b.engaged += g.eng[teams[0]]; b.duration += round - g.start; b.attack += g.att[teams[0]];
            if (g.attackers[teams[0]].size === 1 && !g.harmless) {
              const id = [...g.attackers[teams[0]]][0], c = s.champions.find(x => x.entity.index === id);
              (t.solo1 ??= []).push({ key, type: c?.type, hp_lost: (g.hp0.get(id) ?? 0) - (g.hpmin.get(id) ?? 0), max_hp: c?.maxHealth,
                died: g.died.has(id), dur: round - g.start, round: g.start, camp_hp: g.hp, str: g.types.reduce((a, ty) => a + ({0: 20, 1: 60, 5: 120, 4: 200}[ty] ?? 0), 0) });
            }
          } else if (teams.length > 1) { T[0].contested++; T[1].contested++; }
        }
      }
      if (!spawn0 && s.champions.some(c => c.position)) spawn0 = s.champions.filter(c => c.position).map(c => ({ team: c.team, position: c.position }));
      st = { s, campAt }; lastRound = round;
    }
    if (ak === 1 && s) {
      const c = s.champions.find(x => x.entity.index === actor);
      if (c) {
        const a = acts.get(actor) ?? {}; acts.set(actor, a);
        if (kind === 5) { const tx = d.getInt32(tsnap + 88, true), ty = d.getInt32(tsnap + 92, true); const k = `${tx},${ty}`;
          (a.attack ??= new Set()).add(k); const gi = groupOf?.get(k); if (gi !== undefined && G[gi].active) G[gi].hitters.add(c.team); }
        else if (kind === 6) a.cast = true; else if (kind === 4 || kind === 23) a.moved = true;
      }
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  all.push({ id: path.basename(file).replace('.repl26a', ''), teams: T }); E.destroy();
}
fs.writeFileSync(output, JSON.stringify(all)); console.log(JSON.stringify({ replays: all.length, out: output }));
