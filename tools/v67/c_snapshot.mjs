// Print the game state at one round of a local replay: champions (team, type, position, health, gems) and the camp
// groups with a reward available or living camps near a point.
// Usage: NFS_REPLAY_ENGINE=2.0.0 node tools/v67/c_snapshot.mjs REPLAY.repl26a ROUND [X Y RADIUS]
import fs from 'node:fs';
import {engine, defaultAssets, verifyAssets} from '../replay/engine.mjs';
const [file, roundArg, xa, ya, ra] = process.argv.slice(2);
const want = Number(roundArg), cx = Number(xa ?? -1), cy = Number(ya ?? -1), rad = Number(ra ?? 99);
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
E.load(fs.readFileSync(file));
const {X, check, dv, out: o, args, tsnap} = E;
const u = p => dv().getUint32(p, true);
check(X.Game_Visualiser_Timeline_GetMain(E.h, o)); const main = dv().getBigUint64(o, true);
check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = u(args);
check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
for (;;) {
  check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
  const round = u(tsnap + 8), phase = u(tsnap + 24), outcome = u(tsnap + 28);
  if ((round >= want && phase === 10) || outcome) {
    const s = E.PC.I(dv(), tsnap);
    console.log('round', round, 'keys', Object.keys(s).join(','));
    for (const c of s.champions)
      console.log('champ team', c.team, 'type', c.type, 'alive', c.alive, 'pos', JSON.stringify(c.position), 'hp', c.health, 'gems', c.gems);
    const near = p => p && (cx < 0 || Math.max(Math.abs(p.x - cx), Math.abs(p.y - cy)) <= rad);
    const live = s.camps.filter(c => c.health > 0 && near(c.position));
    console.log('live camps near', live.length);
    (s.groups || []).forEach((g, i) => { if (g.rewardAvailable) console.log('group', i, 'reward available', JSON.stringify(g).slice(0, 200)); });
    break;
  }
  if (u(tsnap + 20) !== 0 && u(tsnap + 56) >= size) break;
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
}
E.destroy();
