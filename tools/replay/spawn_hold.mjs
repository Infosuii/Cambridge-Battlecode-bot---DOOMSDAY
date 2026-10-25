// Spawn-occupancy check (offline omniscient analysis; a rules test, never a bot input). Camp groups are the
// 4-connected components of the camp tiles in the first state. For each group, logs every respawn (a dead camp tile
// gets a live camp again) with the number of rounds since the group's last kill and whether any champion stood on one
// of its tiles in each of the preceding rounds, plus the longest unbroken occupation of a dead group.
// Usage: node spawn_hold.mjs <out.json> <replay>...
import fs from 'node:fs';
import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir);
const E = await engine(dir);
const [output, ...files] = process.argv.slice(2);
const all = [];
for (const file of files) {
  E.load(fs.readFileSync(file));
  const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  const full = () => { check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap)); return E.PC.I(dv(), tsnap); };
  let lastRound = -1, groupOf = null, groups = [];
  const info = []; // per group
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true);
    const phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    if ((round !== lastRound && phase === 10) || outcome) {
      const s = full();
      const live = new Set(s.camps.filter(c => c.position && c.health > 0).map(c => `${c.position.x},${c.position.y}`));
      if (!groupOf && live.size) {
        groupOf = new Map();
        const tiles = [...live];
        for (const t of tiles) {
          if (groupOf.has(t)) continue;
          const gi = groups.length; groups.push([]);
          const st = [t]; groupOf.set(t, gi);
          while (st.length) {
            const c = st.pop(); groups[gi].push(c);
            const [x, y] = c.split(',').map(Number);
            for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
              const k = `${x + dx},${y + dy}`;
              if (live.has(k) && !groupOf.has(k)) { groupOf.set(k, gi); st.push(k); }
            }
          }
          info.push({ tiles: groups[gi].length, alive: true, dead_since: -1, occ_run: 0, max_occ_run: 0, occ_dead_rounds: 0, dead_rounds: 0, respawns: [] });
        }
      }
      if (groupOf) {
        const occ = new Set(s.champions.filter(c => c.alive && c.position).map(c => `${c.position.x},${c.position.y}`));
        groups.forEach((tiles, gi) => {
          const g = info[gi];
          const anyLive = tiles.some(t => live.has(t));
          const occupied = tiles.some(t => occ.has(t));
          if (g.alive && !anyLive) { g.alive = false; g.dead_since = round; g.occ_run = 0; g.window = []; }
          else if (!g.alive && anyLive) {
            g.alive = true;
            g.respawns.push({ round, dead_for: round - g.dead_since, occupied_last5: g.window.slice(-5).filter(Boolean).length,
              occupied_rounds: g.window.filter(Boolean).length });
          }
          if (!g.alive) {
            g.dead_rounds++; g.window.push(occupied);
            if (occupied) { g.occ_dead_rounds++; g.occ_run++; g.max_occ_run = Math.max(g.max_occ_run, g.occ_run); } else g.occ_run = 0;
          }
        });
      }
      lastRound = round;
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  all.push({ id: path.basename(file).replace('.repl26a', ''), groups: info.map(g => ({ tiles: g.tiles, dead_rounds: g.dead_rounds,
    occ_dead_rounds: g.occ_dead_rounds, max_occ_run: g.max_occ_run, respawns: g.respawns })) });
  E.destroy();
}
fs.writeFileSync(output, JSON.stringify(all));
console.log(JSON.stringify({ replays: all.length, out: output }));
