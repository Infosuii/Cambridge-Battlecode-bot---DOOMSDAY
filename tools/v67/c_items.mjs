// Item purchases and gear of every champion in an engine-2 replay (offline analysis only).
// Usage: NFS_REPLAY_ENGINE=2.0.0 node tools/v67/c_items.mjs REPLAY OUT.json
// OUT: {champs:[{id, team, type}], buys:[[round, id, item, delta, gold]], snaps:{round:[[id, maxHp, earned, items...]]}}
// item = family * 6 + stat * 2 + (1 for an emblem); families monster, power, durability, treasure, jungle, home,
// bruiser, tribute, capture, prospector, hunter, skirmish, greed, collectors. earned = gold gained so far (sum of rises).
import fs from 'node:fs';
import {engine, defaultAssets, verifyAssets} from '../replay/engine.mjs';
const [file, output] = process.argv.slice(2);
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
E.load(fs.readFileSync(file));
const {X, check, dv, out: o, args, tsnap} = E;
const u = p => dv().getUint32(p, true);
check(X.Game_Visualiser_Timeline_GetMain(E.h, o)); const main = dv().getBigUint64(o, true);
check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = u(args);
check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
const SNAPS = new Set([100, 200, 300, 400, 500, 700, 1000, 1500]);
let lastRound = -1, champs = null;
const prev = new Map(), earned = new Map(), buys = [], snaps = {};
for (;;) {
  check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
  const round = u(tsnap + 8), phase = u(tsnap + 24), outcome = u(tsnap + 28);
  if ((round !== lastRound && phase === 10) || outcome) {
    const s = E.PC.I(dv(), tsnap);
    if (!champs) champs = s.champions.map(c => ({id: c.entity.index, team: c.team, type: c.type}));
    for (const c of s.champions) {
      const id = c.entity.index, p = prev.get(id);
      if (p) {
        earned.set(id, (earned.get(id) ?? 0) + Math.max(0, c.gold - p.gold));
        c.items.forEach((n, i) => { if (n !== (p.items[i] ?? 0)) buys.push([round, id, i, n - (p.items[i] ?? 0), c.gold]); });
      }
      prev.set(id, {gold: c.gold, items: [...c.items]});
    }
    if (SNAPS.has(round)) snaps[round] = s.champions.map(c => [c.entity.index, Math.round(c.maxHealth), earned.get(c.entity.index) ?? 0, ...c.items]);
    lastRound = round;
  }
  if (outcome || (u(tsnap + 20) !== 0 && u(tsnap + 56) >= size)) break;
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
}
fs.writeFileSync(output, JSON.stringify({rounds: lastRound, champs, buys, snaps}));
E.destroy();
