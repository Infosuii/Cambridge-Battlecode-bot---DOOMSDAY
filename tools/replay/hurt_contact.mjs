// What champions do when hurt in contact (offline omniscient replay analysis only). For each champion-round with an
// enemy within 6 and hp below 50%, look 5 rounds ahead: died, escaped (alive with no enemy within 6), still engaged;
// change in distance to the nearest living ally and to its own spawn; back on its spawn (recall or walk); and whether
// it attacked an enemy champion in those rounds. Counts only the first round of each hurt-contact episode.
// Usage: node hurt_contact.mjs <out.json> <replay>...
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
  let lastRound = -1, camps = new Set(); const hist = [], pvp = []; let cur = new Set();
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    const kind = d.getUint32(tsnap + 68, true), actor = d.getUint32(tsnap + 76, true), ak = d.getUint32(tsnap + 72, true);
    if (round !== lastRound && phase === 10) {
      const s = E.PC.I(d, tsnap); lastRound = round; pvp.push(cur); cur = new Set();
      camps = new Set(s.camps.filter(c => c.position).map(c => `${c.position.x},${c.position.y}`));
      hist.push(s.champions.map(c => ({ id: c.entity.index, team: c.team, alive: c.alive, p: c.position, hp: c.health / Math.max(1, c.maxHealth) })));
    }
    if (ak === 1 && kind === 5) { const tx = d.getInt32(tsnap + 88, true), ty = d.getInt32(tsnap + 92, true); if (!camps.has(`${tx},${ty}`)) cur.add(actor); }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  pvp.push(cur); pvp.shift();
  const spawn = [0, 1].map(t => hist[0].filter(c => c.team === t && c.p).map(c => c.p));
  const sdist = (t, p) => Math.min(...spawn[t].map(q => cheb(q, p)));
  const T = [0, 1].map(() => ({ episodes: 0, died: 0, escaped: 0, engaged: 0, ally_closer: 0, home_closer: 0, on_spawn: 0, hit_back: 0,
    died_hit_back: 0, died_no_hit: 0, hp_sum: 0 }));
  const inEp = new Set();
  for (let r = 0; r + 5 < hist.length; ++r) {
    for (const c of hist[r]) {
      const key = c.id;
      const en = c.alive && c.p ? hist[r].filter(o => o.team !== c.team && o.alive && o.p && cheb(o.p, c.p) <= 6) : [];
      const hurt = c.alive && c.p && en.length && c.hp < 0.5;
      if (!hurt) { inEp.delete(key); continue; }
      if (inEp.has(key)) continue;
      inEp.add(key);
      const t = T[c.team]; t.episodes++; t.hp_sum += c.hp;
      const ally0 = Math.min(99, ...hist[r].filter(o => o.team === c.team && o.id !== c.id && o.alive && o.p).map(o => cheb(o.p, c.p)));
      let died = false, hit = false;
      for (let k = 0; k < 5; ++k) if (pvp[r + k]?.has(c.id)) hit = true;
      for (let k = 1; k <= 5; ++k) { const f = hist[r + k].find(o => o.id === c.id); if (!f.alive) { died = true; break; } }
      if (hit) t.hit_back++;
      if (died) { t.died++; if (hit) t.died_hit_back++; else t.died_no_hit++; continue; }
      const f = hist[r + 5].find(o => o.id === c.id);
      const en5 = hist[r + 5].filter(o => o.team !== c.team && o.alive && o.p && cheb(o.p, f.p) <= 6).length;
      if (en5) t.engaged++; else t.escaped++;
      const ally5 = Math.min(99, ...hist[r + 5].filter(o => o.team === c.team && o.id !== c.id && o.alive && o.p).map(o => cheb(o.p, f.p)));
      if (ally5 < ally0) t.ally_closer++;
      if (sdist(c.team, f.p) < sdist(c.team, c.p)) t.home_closer++;
      if (sdist(c.team, f.p) <= 1) t.on_spawn++;
    }
  }
  all.push({ id: path.basename(file).replace('.repl26a', ''), teams: T }); E.destroy();
}
fs.writeFileSync(output, JSON.stringify(all)); console.log(JSON.stringify({ replays: all.length, out: output }));
