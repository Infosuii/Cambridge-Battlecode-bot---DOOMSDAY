// Who clears a camp group versus who captures its reward (offline omniscient replay analysis only; never a bot input).
// A clear runs from the first round any camp of the group has lost health to the round the last one dies; its
// attackers are the champions whose basic attacks hit the group, with hit counts. The capture is the first later round
// in which a champion standing on the group's tiles gains gold without a kill; every champion of that team on the
// tiles that round is a capturer (the reward is split between them). One row per capture.
// Usage: node capture_funnel.mjs <out.json> <replay>...
import fs from 'node:fs'; import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const VAL = { 0: [40, 4, 1350], 1: [90, 15, 2400], 2: [0, 7, 120], 3: [0, 1, 1], 4: [0, 0, 1], 5: [0, 0, 1] };
const [output, ...files] = process.argv.slice(2); const all = [];
for (const file of files) {
  E.load(fs.readFileSync(file)); const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  let lastRound = -1, groupOf = null, s = null, prev = null, spawn0 = null;
  const G = [], rows = [], types = new Map(); const killsThisRound = new Set();
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    const kind = d.getUint32(tsnap + 68, true), actor = d.getUint32(tsnap + 76, true), ak = d.getUint32(tsnap + 72, true);
    if ((round !== lastRound && phase === 10) || outcome) {
      s = E.PC.I(d, tsnap);
      const campAt = new Map(s.camps.filter(c => c.position).map(c => [`${c.position.x},${c.position.y}`, c]));
      if (!groupOf) {
        groupOf = new Map();
        for (const [k] of campAt) {
          if (groupOf.has(k)) continue;
          const tiles = []; const stack = [k]; groupOf.set(k, G.length);
          while (stack.length) { const t = stack.pop(); tiles.push(t); const [x, y] = t.split(',').map(Number);
            for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const n = `${x + dx},${y + dy}`; if (campAt.has(n) && !groupOf.has(n)) { groupOf.set(n, G.length); stack.push(n); } } }
          const ty = tiles.map(t => campAt.get(t).type);
          G.push({ tiles, tileSet: new Set(tiles), gold: ty.reduce((a, t) => a + VAL[t][0], 0), gems: ty.reduce((a, t) => a + VAL[t][1], 0),
            hp: ty.reduce((a, t) => a + VAL[t][2], 0), state: 'idle', hits: new Map() });
        }
      }
      if (!spawn0 && s.champions.some(c => c.position)) spawn0 = s.champions.filter(c => c.position).map(c => ({ team: c.team, position: c.position }));
      for (const c of s.champions) types.set(c.entity.index, c.type);
      // capture detection against the previous round's gold
      if (prev) {
        const pg = new Map(prev.champions.map(c => [c.entity.index, c]));
        for (const g of G) {
          if (g.state !== 'dead') continue;
          const on = s.champions.filter(c => c.alive && c.position && g.tileSet.has(`${c.position.x},${c.position.y}`));
          const gained = on.filter(c => { const p = pg.get(c.entity.index); return p && c.gold > p.gold && !killsThisRound.has(c.entity.index); });
          if (!gained.length) continue;
          const team = gained[0].team, caps = on.filter(c => c.team === team);
          const sp = [0, 1].map(tm => spawn0.filter(c => c.team === tm).map(c => c.position));
          const dist = tm => Math.min(...g.tiles.map(k => { const [x, y] = k.split(',').map(Number); return Math.min(...sp[tm].map(p => cheb(p, { x, y }))); }));
          const own = dist(team), opp = dist(1 - team);
          rows.push({ round, team, gold: g.gold, gems: g.gems, hp: g.hp, side: own < opp * 0.8 ? 'own' : opp < own * 0.8 ? 'enemy' : 'middle',
            clear_start: g.start, clear_end: g.end, capturers: caps.map(c => ({ id: c.entity.index, type: c.type, gain: c.gold - (pg.get(c.entity.index)?.gold ?? c.gold) })),
            hitters: [...g.hits].map(([id, n]) => ({ id, type: types.get(id), team: g.hitTeam.get(id), hits: n })) });
          g.state = 'idle'; g.hits = new Map();
        }
      }
      for (const g of G) {
        const live = g.tiles.map(k => campAt.get(k)).filter(c => c && c.health > 0);
        const damaged = live.some(c => c.health < VAL[c.type][2] - 0.5) || (live.length && live.length < g.tiles.length);
        if (g.state === 'idle' && damaged && live.length) { g.state = 'clearing'; g.start = round; g.hits = new Map(); g.hitTeam = new Map(); }
        else if (g.state === 'clearing' && !live.length) { g.state = 'dead'; g.end = round; }
        else if (g.state === 'dead' && live.length && live.length === g.tiles.length && !damaged) g.state = 'idle'; // respawned uncaptured
      }
      killsThisRound.clear();
      prev = s; lastRound = round;
    }
    if (ak === 1 && s && kind === 5) {
      const c = s.champions.find(x => x.entity.index === actor);
      const k = `${d.getInt32(tsnap + 88, true)},${d.getInt32(tsnap + 92, true)}`, gi = groupOf?.get(k);
      if (c && gi !== undefined && G[gi].state === 'clearing') { G[gi].hits.set(actor, (G[gi].hits.get(actor) ?? 0) + 1); G[gi].hitTeam.set(actor, c.team); }
      // a basic attack on a champion tile may be a kill; its gold is not a capture
      if (c && s.champions.some(o => o.team !== c.team && o.position && `${o.position.x},${o.position.y}` === k)) killsThisRound.add(actor);
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  all.push({ id: path.basename(file).replace('.repl26a', ''), captures: rows }); E.destroy();
}
fs.writeFileSync(output, JSON.stringify(all)); console.log(JSON.stringify({ replays: all.length, out: output }));
