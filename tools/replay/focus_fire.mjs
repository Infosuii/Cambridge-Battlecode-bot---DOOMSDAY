// Damage exchange in champion fights (offline omniscient replay analysis only). Per team: basic attacks on enemy
// champions, rounds with at least one such attack, attacks per such round, distinct targets per round (focus), the
// share of attacks on the enemy that ends the round with the lowest hp fraction among those attacked, and enemy
// champion health lost per round of contact (from round-to-round health drops of enemies within 6 of one of us).
// Usage: node focus_fire.mjs <out.json> <replay>...
import fs from 'node:fs'; import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const [output, ...files] = process.argv.slice(2); const all = [];
for (const file of files) {
  E.load(fs.readFileSync(file)); const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  let lastRound = -1, s = null, prev = null;
  const T = [0, 1].map(() => ({ attacks: 0, attack_rounds: 0, targets: 0, contact_rounds: 0, dmg_dealt: 0, dmg_taken: 0 }));
  let cur = [new Map(), new Map()];
  const flush = () => {
    for (const t of [0, 1]) if (cur[t].size) { T[t].attack_rounds++; T[t].targets += cur[t].size; for (const v of cur[t].values()) T[t].attacks += v; }
    cur = [new Map(), new Map()];
  };
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    const kind = d.getUint32(tsnap + 68, true), actor = d.getUint32(tsnap + 76, true), ak = d.getUint32(tsnap + 72, true);
    if (round !== lastRound && phase === 10) {
      flush(); prev = s; s = E.PC.I(d, tsnap); lastRound = round;
      if (prev) for (const t of [0, 1]) {
        const ours = s.champions.filter(c => c.team === t && c.alive && c.position);
        const foes = s.champions.filter(c => c.team !== t);
        let contact = false;
        for (const e of foes) {
          const p = prev.champions.find(x => x.entity.index === e.entity.index);
          if (!p || !p.alive || !p.position || !ours.some(o => cheb(o.position, p.position) <= 6)) continue;
          contact = true;
          const lost = e.alive ? Math.max(0, p.health - e.health) : p.health;
          T[t].dmg_dealt += lost;
        }
        if (contact) T[t].contact_rounds++;
      }
    }
    if (ak === 1 && kind === 5 && s) {
      const tx = d.getInt32(tsnap + 88, true), ty = d.getInt32(tsnap + 92, true);
      const a = s.champions.find(c => c.entity.index === actor);
      const v = s.champions.find(c => c.alive && c.position && c.position.x === tx && c.position.y === ty);
      if (a && v && v.team !== a.team) cur[a.team].set(v.entity.index, (cur[a.team].get(v.entity.index) ?? 0) + 1);
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  flush();
  all.push({ id: path.basename(file).replace('.repl26a', ''), teams: T }); E.destroy();
}
fs.writeFileSync(output, JSON.stringify(all)); console.log(JSON.stringify({ replays: all.length, out: output }));
