// How much health a champion regains per round while standing on its own spawn region (offline rules probe).
// Usage: NFS_REPLAY_ENGINE=2.0.0 node tools/replay/spawn_heal_probe.mjs <replay>...
import fs from 'node:fs';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const gains = [];
for (const file of process.argv.slice(2)) {
  E.load(fs.readFileSync(file)); const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  let last = -1, prev = null, spawns = null;
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    if (round !== last && phase === 10) {
      const s = E.PC.I(d, tsnap);
      if (!spawns) spawns = [0, 1].map(t => s.champions.filter(c => c.team === t && c.position).map(c => c.position));
      if (prev) for (const c of s.champions) {
        const p = prev.find(o => o.entity.index === c.entity.index);
        if (!p || !p.alive || !c.alive || !p.position || !c.position) continue;
        const onSpawn = q => spawns[c.team].some(z => cheb(z, q) <= 0);
        if (onSpawn(p.position) && onSpawn(c.position) && p.health < p.maxHealth) gains.push({ before: p.health / p.maxHealth, after: c.health / c.maxHealth });
      }
      prev = s.champions; last = round;
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size) || gains.length > 400) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  E.destroy();
}
const full = gains.filter(g => g.after >= 0.999).length;
console.log(JSON.stringify({ samples: gains.length, fullHealNextRound: full, mean_before: gains.reduce((a, g) => a + g.before, 0) / Math.max(1, gains.length),
  mean_after: gains.reduce((a, g) => a + g.after, 0) / Math.max(1, gains.length) }));
