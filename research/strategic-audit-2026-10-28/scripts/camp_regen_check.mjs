// Usage: NFS_REPLAY_ENGINE=2.0.0 node camp_regen_check.mjs <inner replay.repl26a files extracted from bundles>
// Result 2026-10-28 on 6 SA-P-base replays: {"up":0,"same":1846,"down":0} (damaged camps never regain HP while no champion is within 9).
// ENG-1: do damaged living camps regain health while no champion is near? Offline replay check.
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';
const T = 'C:/projects/cambridge battlecode/work/neural-full-stack/tools/replay/engine.mjs';
const { engine, defaultAssets, verifyAssets } = await import(pathToFileURL(T).href);
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const stats = { up: 0, same: 0, down: 0, samples: [], states: {} };
for (const file of process.argv.slice(2)) {
  E.load(fs.readFileSync(file)); const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  let lastRound = -1; const prev = new Map(); let printed = false;
  for (let it = 0; it < 4e6; it++) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), pos = d.getUint32(tsnap + 56, true), round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true);
    if ((round !== lastRound && phase === 10) || outcome) {
      const s = E.PC.I(d, tsnap); lastRound = round;
      if (!printed) { printed = true; console.error('camp keys', Object.keys(s.camps[0] || {}).join(','), 'champ keys', Object.keys(s.champions[0] || {}).join(',')); }
      for (const c of s.camps) {
        if (!c.position) continue;
        const k = `${c.position.x},${c.position.y}`;
        const near = s.champions.some(h => h.alive && h.position && cheb(h.position, c.position) <= 9);
        const p = prev.get(k);
        if (p && p.round === round - 1 && c.health > 0 && p.health > 0 && c.health < ({0:1350,1:2400,2:120,3:120,4:20000,5:5000})[c.type] - 0.5 && p.near === false && !near) {
          if (c.health > p.health + 0.5) { stats.up++; if (stats.samples.length < 8) stats.samples.push({ file: file.slice(-40), round, k, from: p.health, to: c.health, type: c.type }); }
          else if (c.health < p.health - 0.5) stats.down++; else stats.same++;
        }
        prev.set(k, { round, health: c.health, near });
      }
      if (outcome) break;
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
}
console.log(JSON.stringify(stats));
