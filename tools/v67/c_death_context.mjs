// Death context from local engine-2 replays: for each champion death, the situation one round before it
// (allies/enemies within 4 and 8, local health sums, carried gems, own/enemy half, distance to own spawn).
// Usage: node tools/v67/c_death_context.mjs OUT.jsonl REPLAY.repl26a ...
// Each output line: {file, rounds, deaths:[...], teams:{...}} with team 0 = A, 1 = B.
import fs from 'node:fs';
import path from 'node:path';
import {engine, defaultAssets, verifyAssets} from '../replay/engine.mjs';
const [output, ...files] = process.argv.slice(2);
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const out = fs.createWriteStream(output);
for (const file of files) {
  E.load(fs.readFileSync(file));
  const {X, check, dv, out: o, args, tsnap} = E;
  const u = p => dv().getUint32(p, true);
  check(X.Game_Visualiser_Timeline_GetMain(E.h, o)); const main = dv().getBigUint64(o, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = u(args);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  let lastRound = -1, prev = null, spawn = {};
  const deaths = [];
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const round = u(tsnap + 8), phase = u(tsnap + 24), outcome = u(tsnap + 28);
    if ((round !== lastRound && phase === 10) || outcome) {
      const s = E.PC.I(dv(), tsnap); lastRound = round;
      const cur = s.champions.map(c => ({id: c.entity.index, team: c.team, type: c.type, alive: c.alive,
        pos: c.position, hp: c.health, maxHp: c.maxHealth, gems: c.gems, kills: c.kills}));
      for (const c of cur) if (round <= 2 && c.pos && !(c.team in spawn)) spawn[c.team] = c.pos;
      if (prev) {
        for (const c of cur) {
          const p = prev.find(x => x.id === c.id);
          if (!p || !p.alive || c.alive || !p.pos) continue;
          const near = (r, same) => prev.filter(x => x.id !== p.id && x.alive && x.pos && (x.team === p.team) === same && cheb(x.pos, p.pos) <= r);
          const hp = xs => xs.reduce((t, x) => t + x.hp, 0);
          const a4 = near(4, true), e4 = near(4, false), a8 = near(8, true), e8 = near(8, false);
          deaths.push({round, team: p.team, type: p.type, gems: p.gems, hpFrac: p.hp / Math.max(1, p.maxHp),
            allies4: a4.length, enemies4: e4.length, allies8: a8.length, enemies8: e8.length,
            hpRatio8: (p.hp + hp(a8)) / Math.max(1, hp(e8)),
            homeDist: spawn[p.team] ? cheb(p.pos, spawn[p.team]) : -1,
            enemyHomeDist: spawn[1 - p.team] ? cheb(p.pos, spawn[1 - p.team]) : -1});
        }
      }
      prev = cur;
    }
    if (outcome || (u(tsnap + 20) !== 0 && u(tsnap + 56) >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  out.write(JSON.stringify({file: path.basename(file), rounds: lastRound, deaths}) + '\n');
  E.destroy();
}
out.end();
