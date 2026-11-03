// How each team played a game (offline omniscient replay analysis only; never a bot input), for learning what the
// teams that beat us did. Per team: opening route (first camp groups worked, with round and team members working
// together), clears by round, territory (share of alive champion-rounds nearer the own spawn) per phase, spread
// (mean distance to the nearest ally) and grouping (share of rounds with an ally within 4), first contact (round,
// allies / enemies / hp at that moment), kills and deaths by phase, first blood, recalls (a jump of 3+ tiles onto
// the own spawn), time near the enemy spawn (within 10), gold at rounds 100 / 200 / 400 / 600.
// Groups are the 4-connected camp clusters of the first state; a group is "worked" by a champion within 2 of one of
// its camps in a round where that group lost health.
// Usage: node winner_profile.mjs <out.json> <replay>...
import fs from 'node:fs'; import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const [output, ...files] = process.argv.slice(2); const all = [];
const PH = [[0, 150], [150, 400], [400, 800], [800, 5000]];
const phaseOf = r => PH.findIndex(([a, b]) => r >= a && r < b);
for (const file of files) {
  try {
    E.load(fs.readFileSync(file));
  } catch (e) { all.push({ id: path.basename(file), error: String(e) }); continue; }
  const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  let lastRound = -1; const hist = []; let groupOf = null, groups = null, spawn = null, mapW = 0, mapH = 0, drafts = null;
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    if (round !== lastRound && phase === 10) {
      const s = E.PC.I(d, tsnap); lastRound = round;
      if (!groupOf && s.camps.some(c => c.position) && s.champions.length) {
        // camp groups: 4-connected clusters
        const key = p => `${p.x},${p.y}`; const tiles = new Map(s.camps.filter(c => c.position).map(c => [key(c.position), c]));
        groupOf = new Map(); groups = []; const seen = new Set();
        for (const [k] of tiles) {
          if (seen.has(k)) continue; const st = [k], mem = []; seen.add(k);
          while (st.length) {
            const t = st.pop(); mem.push(t); const [x, y] = t.split(',').map(Number);
            for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const n = `${x + dx},${y + dy}`; if (tiles.has(n) && !seen.has(n)) { seen.add(n); st.push(n); } }
          }
          const gi = groups.length; groups.push(mem.map(t => { const [x, y] = t.split(',').map(Number); return { x, y }; }));
          for (const t of mem) groupOf.set(tiles.get(t).entity.index, gi);
        }
        spawn = [0, 1].map(t => { const cs = s.champions.filter(c => c.team === t && c.position); return { x: cs.reduce((a, c) => a + c.position.x, 0) / Math.max(1, cs.length), y: cs.reduce((a, c) => a + c.position.y, 0) / Math.max(1, cs.length) }; });
        drafts = s.drafts;
        mapW = Math.max(...s.camps.filter(c => c.position).map(c => c.position.x)) + 1; mapH = Math.max(...s.camps.filter(c => c.position).map(c => c.position.y)) + 1;
      }
      hist.push({ round, ch: s.champions.map(c => ({ id: c.entity.index, team: c.team, type: c.type, alive: c.alive, p: c.position, hp: c.health / Math.max(1, c.maxHealth), gold: c.gold, gems: c.gems, kills: c.kills })),
        camps: s.camps.map(c => ({ id: c.entity.index, p: c.position, hp: c.health })) });
    }
    if (outcome || (dv().getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  E.destroy();
  if (!groupOf || hist.length < 3) { all.push({ id: path.basename(file), error: 'no state' }); continue; }
  const T = [0, 1].map(t => ({
    route: [], clears: [0, 0, 0, 0], terr: [[0, 0], [0, 0], [0, 0], [0, 0]], spread: [[0, 0], [0, 0], [0, 0], [0, 0]], grouped: [[0, 0], [0, 0], [0, 0], [0, 0]],
    first_contact: null, kills: [0, 0, 0, 0], deaths: [0, 0, 0, 0], first_blood: null, recalls: [0, 0, 0, 0], near_enemy_spawn: [[0, 0], [0, 0], [0, 0], [0, 0]],
    gold: {}, group_work: {}, workers_together: [0, 0],
  }));
  const prevAlive = new Map(), prevPos = new Map(); let firstBlood = null;
  for (let r = 1; r < hist.length; ++r) {
    const H = hist[r], P = hist[r - 1], ph = phaseOf(H.round);
    const lost = new Set(); // groups that lost health this round
    const ph_ = new Map(P.camps.map(c => [c.id, c.hp]));
    for (const c of H.camps) if (ph_.has(c.id) && c.hp < ph_.get(c.id) && groupOf.has(c.id)) lost.add(groupOf.get(c.id));
    for (const c of P.camps) if (!H.camps.find(x => x.id === c.id) && groupOf.has(c.id)) lost.add(groupOf.get(c.id));
    const working = [new Map(), new Map()];
    for (const c of H.ch) {
      const t = T[c.team];
      const was = prevAlive.get(c.id);
      if (was === true && !c.alive) {
        t.deaths[ph]++; T[1 - c.team].kills[ph]++;
        if (!firstBlood) { firstBlood = { round: H.round, by: 1 - c.team }; }
      }
      prevAlive.set(c.id, c.alive);
      if (!c.alive || !c.p) { prevPos.delete(c.id); continue; }
      const own = cheb(c.p, spawn[c.team]), opp = cheb(c.p, spawn[1 - c.team]);
      t.terr[ph][0] += own < opp ? 1 : 0; t.terr[ph][1]++;
      t.near_enemy_spawn[ph][0] += opp <= 10 ? 1 : 0; t.near_enemy_spawn[ph][1]++;
      const allies = H.ch.filter(o => o.team === c.team && o.id !== c.id && o.alive && o.p);
      const nd = allies.length ? Math.min(...allies.map(o => cheb(o.p, c.p))) : 0;
      t.spread[ph][0] += nd; t.spread[ph][1]++; t.grouped[ph][0] += nd <= 4 ? 1 : 0; t.grouped[ph][1]++;
      const pp = prevPos.get(c.id);
      if (pp && cheb(pp, c.p) >= 3 && own <= 2) t.recalls[ph]++;
      prevPos.set(c.id, c.p);
      if (!t.first_contact && own > 4) { // off our spawn: spawns can start in sight of each other
        const en = H.ch.filter(o => o.team !== c.team && o.alive && o.p && cheb(o.p, c.p) <= 6);
        if (en.length) t.first_contact = { round: H.round, allies4: allies.filter(o => cheb(o.p, c.p) <= 4).length + 1, enemies6: en.length,
          hp: +c.hp.toFixed(2), enemy_hp: +(en.reduce((a, o) => a + o.hp, 0) / en.length).toFixed(2), own_side: own < opp };
      }
      for (const gi of lost) if (groups[gi].some(q => cheb(q, c.p) <= 2)) { working[c.team].set(gi, (working[c.team].get(gi) ?? 0) + 1); }
    }
    for (const tm of [0, 1]) {
      for (const [gi, n] of working[tm]) {
        const t = T[tm]; t.group_work[gi] = (t.group_work[gi] ?? 0) + 1;
        if (t.route.length < 8 && !t.route.find(x => x.g === gi)) {
          const g = groups[gi]; const cx = g.reduce((a, q) => a + q.x, 0) / g.length, cy = g.reduce((a, q) => a + q.y, 0) / g.length;
          const c = { x: cx, y: cy };
          t.route.push({ g: gi, round: H.round, workers: n, own_side: cheb(c, spawn[tm]) < cheb(c, spawn[1 - tm]), dist_own: Math.round(cheb(c, spawn[tm])), size: g.length });
        }
        if (H.round < 300) { t.workers_together[0] += n; t.workers_together[1]++; }
      }
    }
    // clears: a group whose camps are all gone or at 0 this round but not last round
    if (r > 1) for (const gi of lost) {
      const ids = [...groupOf].filter(([, g]) => g === gi).map(([id]) => id);
      const alive = H.camps.filter(c => ids.includes(c.id) && c.hp > 0).length, palive = P.camps.filter(c => ids.includes(c.id) && c.hp > 0).length;
      if (alive === 0 && palive > 0) {
        const w = [0, 1].map(tm => working[tm].get(gi) ?? 0);
        if (w[0] !== w[1]) T[w[0] > w[1] ? 0 : 1].clears[ph]++;
      }
    }
    for (const tm of [0, 1]) for (const R of [100, 200, 400, 600]) if (H.round === R) T[tm].gold[R] = H.ch.filter(c => c.team === tm).reduce((a, c) => a + (c.gold ?? 0), 0);
  }
  const fin = x => x.map(([a, b]) => b ? +(a / b).toFixed(3) : null);
  for (const t of T) {
    t.terr = fin(t.terr); t.spread = fin(t.spread); t.grouped = fin(t.grouped); t.near_enemy_spawn = fin(t.near_enemy_spawn);
    t.workers_together = t.workers_together[1] ? +(t.workers_together[0] / t.workers_together[1]).toFixed(2) : null;
    delete t.group_work;
  }
  all.push({ id: path.basename(path.dirname(file)) + '/' + path.basename(file), rounds: hist[hist.length - 1].round, first_blood: firstBlood,
    drafts, types: [0, 1].map(tm => [...new Set(hist[0].ch.filter(c => c.team === tm).map(c => c.type))]), teams: T });
}
fs.writeFileSync(output, JSON.stringify(all)); console.log(JSON.stringify({ replays: all.length, out: output }));
