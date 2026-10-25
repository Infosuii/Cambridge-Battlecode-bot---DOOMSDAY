// Camp groups of a map from a replay's first state: 4-connected camp tiles, centroid, camp types, gems and gold, and
// Chebyshev distance from each team's spawn (offline; for reading maps). Usage: node map_groups.mjs <replay>
import fs from 'node:fs';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const VAL = { 0: [40, 4], 1: [90, 15], 2: [0, 7], 3: [20, 0], 4: [300, 200], 5: [160, 36] }; // wolf elk gem gold monolith golem
const NAME = ['wolf', 'elk', 'gem', 'gold', 'monolith', 'golem'];
E.load(fs.readFileSync(process.argv[2])); const { X, check, dv, out, tsnap } = E;
check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); check(X.Game_Visualiser_Timeline_Seek(E.h, dv().getBigUint64(out, true), 0, 0));
let s;
for (;;) { check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap)); s = E.PC.I(dv(), tsnap); if (s.champions.length && s.camps.some(c => c.position)) break; check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1)); }
const camps = new Map(s.camps.filter(c => c.position).map(c => [`${c.position.x},${c.position.y}`, c]));
const seen = new Set(); const sp = [0, 1].map(t => s.champions.filter(c => c.team === t).map(c => c.position));
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
let gi = 0;
for (const [k, c0] of camps) {
  if (seen.has(k)) continue;
  const st = [k], mem = []; seen.add(k);
  while (st.length) { const t = st.pop(); mem.push(camps.get(t)); const [x, y] = t.split(',').map(Number);
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const n = `${x + dx},${y + dy}`; if (camps.has(n) && !seen.has(n)) { seen.add(n); st.push(n); } } }
  const cx = Math.round(mem.reduce((a, c) => a + c.position.x, 0) / mem.length), cy = Math.round(mem.reduce((a, c) => a + c.position.y, 0) / mem.length);
  const types = {}; let gold = 0, gems = 0; for (const c of mem) { types[NAME[c.type]] = (types[NAME[c.type]] ?? 0) + 1; gold += VAL[c.type][0]; gems += VAL[c.type][1]; }
  const c = { x: cx, y: cy };
  console.log(`grp${gi++} at(${cx},${cy}) camps ${mem.length} ${JSON.stringify(types)} gems ${gems} gold ${gold} dA ${Math.min(...sp[0].map(p => cheb(p, c)))} dB ${Math.min(...sp[1].map(p => cheb(p, c)))}`);
}
console.log('map', s.champions.length, 'champions; spawnA', JSON.stringify(sp[0][0]), 'spawnB', JSON.stringify(sp[1][0]));
