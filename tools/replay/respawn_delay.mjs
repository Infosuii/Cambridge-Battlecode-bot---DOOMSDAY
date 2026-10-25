// Camp respawn delays and who caused them (offline omniscient replay analysis only; never a bot input).
// Rule: any occupied spawn tile delays the whole group's respawn. For each capture (a champion on the group's tiles
// gains gold without a kill) this records the rounds until every camp of the group is back at full health, and, for
// each team, the rounds in that window in which one of its living champions stood on the group's tiles. Comparing a
// group's delays with its shortest observed delay (its timer) shows respawns held back by occupants.
// Usage: node respawn_delay.mjs <out.json> <replay>...
import fs from 'node:fs'; import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const VAL = { 0: 1350, 1: 2400, 2: 120, 3: 1, 4: 1, 5: 1 };
const [output, ...files] = process.argv.slice(2); const all = [];
for (const file of files) {
  E.load(fs.readFileSync(file)); const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  let lastRound = -1, groupOf = null, prev = null; const G = [], rows = [];
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    if ((round !== lastRound && phase === 10) || outcome) {
      const s = E.PC.I(d, tsnap);
      const campAt = new Map(s.camps.filter(c => c.position).map(c => [`${c.position.x},${c.position.y}`, c]));
      if (!groupOf) {
        groupOf = new Map();
        for (const [k] of campAt) {
          if (groupOf.has(k)) continue;
          const tiles = []; const stack = [k]; groupOf.set(k, G.length);
          while (stack.length) { const t = stack.pop(); tiles.push(t); const [x, y] = t.split(',').map(Number);
            for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const n = `${x + dx},${y + dy}`; if (campAt.has(n) && !groupOf.has(n)) { groupOf.set(n, G.length); stack.push(n); } } }
          G.push({ gi: G.length, tiles, tileSet: new Set(tiles), hp: tiles.reduce((a, t) => a + VAL[campAt.get(t).type], 0), state: 'alive', cap: null });
        }
      }
      const pg = prev ? new Map(prev.champions.map(c => [c.entity.index, c])) : null;
      for (const g of G) {
        const cs = g.tiles.map(k => campAt.get(k));
        const live = cs.filter(c => c && c.health > 0);
        const full = live.length === g.tiles.length && live.every(c => c.health >= VAL[c.type] - 0.5);
        const on = s.champions.filter(c => c.alive && c.position && g.tileSet.has(`${c.position.x},${c.position.y}`));
        if (g.state === 'alive' && !live.length) g.state = 'dead';
        else if (g.state === 'dead' && pg) {
          const gained = on.filter(c => { const p = pg.get(c.entity.index); return p && c.gold > p.gold; });
          if (gained.length) { g.state = 'respawning'; g.cap = { round, team: gained[0].team, on: [0, 0] }; }
          else if (full) g.state = 'alive'; // came back without a capture we saw
        } else if (g.state === 'respawning') {
          if (full) {
            rows.push({ group: g.gi, hp: g.hp, captured: g.cap.round, team: g.cap.team, delay: round - g.cap.round, occupied: g.cap.on });
            g.state = 'alive'; g.cap = null;
          } else for (const c of on) g.cap.on[c.team]++;
        }
      }
      prev = s; lastRound = round;
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  all.push({ id: path.basename(file).replace('.repl26a', ''), respawns: rows }); E.destroy();
}
fs.writeFileSync(output, JSON.stringify(all)); console.log(JSON.stringify({ replays: all.length, out: output }));
