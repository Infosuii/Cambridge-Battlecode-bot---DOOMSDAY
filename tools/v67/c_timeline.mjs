// Round-by-round timeline of an engine-2 replay, for loss forensics.
// Usage: NFS_REPLAY_ENGINE=2.0.0 node tools/v67/c_timeline.mjs REPLAY OUT.json
// OUT: {rounds, champs:[{id, team, type}], camps:[{x, y}], frames:[[round, [[id, x, y, hp, maxHp, alive, gold, gems,
// shards, acts]...], [[campIndex, hp]...]]]} where acts lists this round's steps [kind, tx, ty, slot]
// (4 move, 5 attack, 6 cast, 11 recall, 12 tribute, 13 buy, 14 ward, 16 cancel, 18 bank, 23 dash step, 25 sell).
// Only living camps with health below maximum are listed (camps being fought).
import fs from 'node:fs';
import {engine, defaultAssets, verifyAssets} from '../replay/engine.mjs';
const [file, output] = process.argv.slice(2);
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const ACTIONS = new Set([4, 5, 6, 11, 12, 13, 14, 16, 18, 23, 25]);
E.load(fs.readFileSync(file));
const {X, check, dv, out: o, args, tsnap} = E;
const u = p => dv().getUint32(p, true), s32 = p => dv().getInt32(p, true);
check(X.Game_Visualiser_Timeline_GetMain(E.h, o)); const main = dv().getBigUint64(o, true);
check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = u(args);
check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
let lastRound = -1, champs = null, camps = null, campMax = null;
const frames = [], acts = new Map();
let lastIn = -1, lastSub = -1;
for (;;) {
  check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
  const round = u(tsnap + 8), phase = u(tsnap + 24), outcome = u(tsnap + 28), kind = u(tsnap + 68), ak = u(tsnap + 72);
  const input = u(tsnap + 56), sub = u(tsnap + 104);
  if (ak === 1 && ACTIONS.has(kind) && !(input === lastIn && sub === lastSub)) {
    const actor = u(tsnap + 76);
    if (!acts.has(actor)) acts.set(actor, []);
    acts.get(actor).push([kind, s32(tsnap + 88), s32(tsnap + 92), u(tsnap + 108)]);
  }
  lastIn = input; lastSub = sub;
  if ((round !== lastRound && phase === 10) || outcome) {
    const s = E.PC.I(dv(), tsnap);
    if (!champs) {
      champs = s.champions.map(c => ({id: c.entity.index, team: c.team, type: c.type}));
      camps = s.camps.map(c => ({x: c.position.x, y: c.position.y, type: c.type}));
      campMax = s.camps.map(c => c.health);
    }
    // Actions logged since the previous frame belong to the previous round.
    if (frames.length) {
      const f = frames[frames.length - 1];
      for (const row of f[1]) row.push(acts.get(row[0]) ?? []);
    }
    acts.clear();
    const rows = s.champions.map(c => [c.entity.index, c.position?.x ?? -1, c.position?.y ?? -1, Math.round(c.health),
      Math.round(c.maxHealth), c.alive ? 1 : 0, c.gold, c.gems, c.items.reduce((a, b) => a + b, 0)]);
    const hurt = [];
    s.camps.forEach((c, k) => { campMax[k] = Math.max(campMax[k], c.health); if (c.health > 0 && c.health < campMax[k]) hurt.push([k, Math.round(c.health)]); });
    frames.push([round, rows, hurt]);
    lastRound = round;
  }
  if (outcome || (u(tsnap + 20) !== 0 && u(tsnap + 56) >= size)) break;
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
}
if (frames.length) for (const row of frames[frames.length - 1][1]) if (row.length === 9) row.push(acts.get(row[0]) ?? []);
fs.writeFileSync(output, JSON.stringify({rounds: lastRound, champs, camps, frames}));
E.destroy();
