// Contact cohesion per team (offline omniscient replay analysis only; never a bot input). A champion-round is "in
// contact" when an enemy champion is within 6. For those rounds: allies within 4, enemies within 6, alone (no ally
// within 4), outnumbered (enemies within 6 > allies within 4 + 1), and whether the champion dies in the next 5 rounds.
// Usage: node contact_cohesion.mjs <until round> <out.json> <replay>...
import fs from 'node:fs'; import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const [untilArg, output, ...files] = process.argv.slice(2); const UNTIL = Number(untilArg); const all = [];
for (const file of files) {
  E.load(fs.readFileSync(file)); const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  let lastRound = -1; const hist = []; // per round: champions
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    if (round !== lastRound && phase === 10) {
      const s = E.PC.I(d, tsnap); lastRound = round;
      hist.push(s.champions.map(c => ({ id: c.entity.index, team: c.team, alive: c.alive, p: c.position, hp: c.health / Math.max(1, c.maxHealth) })));
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size) || round > UNTIL + 6) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  const T = [0, 1].map(() => ({ contact: 0, alone: 0, outnumbered: 0, allies: 0, enemies: 0, die5: 0, die5_alone: 0, die5_supported: 0,
    alone_rounds: 0, supported_rounds: 0, deaths: 0, low: 0, die5_low: 0, die5_high: 0, hp_sum: 0,
    hpq: [0, 0, 0, 0], hpq_die: [0, 0, 0, 0], ratio_q: [0, 0, 0], ratio_q_die: [0, 0, 0] }));
  for (let r = 0; r < hist.length - 5 && r < UNTIL; ++r) {
    const cs = hist[r];
    for (const c of cs) {
      if (!c.alive || !c.p) continue;
      const en = cs.filter(o => o.team !== c.team && o.alive && o.p && cheb(o.p, c.p) <= 6).length;
      if (!en) continue;
      const al = cs.filter(o => o.team === c.team && o.id !== c.id && o.alive && o.p && cheb(o.p, c.p) <= 4).length;
      const t = T[c.team]; t.contact++; t.allies += al; t.enemies += en;
      if (al === 0) t.alone++; if (en > al + 1) t.outnumbered++;
      let dies = false; for (let k = 1; k <= 5; ++k) { const f = hist[r + k].find(o => o.id === c.id); if (f && !f.alive) { dies = true; break; } }
      if (dies) { t.die5++; if (al === 0) t.die5_alone++; else t.die5_supported++; }
      if (al === 0) t.alone_rounds++; else t.supported_rounds++;
      t.hp_sum += c.hp; const q = Math.min(3, Math.floor(c.hp * 4)); t.hpq[q]++; if (dies) t.hpq_die[q]++;
      // Local health ratio: our hp fractions within 4 (incl. us) against theirs within 6.
      const mine = c.hp + cs.filter(o => o.team === c.team && o.id !== c.id && o.alive && o.p && cheb(o.p, c.p) <= 4).reduce((x, o) => x + o.hp, 0);
      const theirs = cs.filter(o => o.team !== c.team && o.alive && o.p && cheb(o.p, c.p) <= 6).reduce((x, o) => x + o.hp, 0);
      const rq = mine < 0.8 * theirs ? 0 : mine <= 1.25 * theirs ? 1 : 2; t.ratio_q[rq]++; if (dies) t.ratio_q_die[rq]++;
    }
  }
  all.push({ id: path.basename(file).replace('.repl26a', ''), teams: T }); E.destroy();
}
fs.writeFileSync(output, JSON.stringify(all)); console.log(JSON.stringify({ replays: all.length, out: output }));
