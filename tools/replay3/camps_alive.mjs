// Per round, which camps are alive (health > 0): one '0'/'1' string per round (camp order as in the replay state),
// plus the camp positions. usage: node camps_alive.mjs replay.repl26a out.json
import fs from 'node:fs';
import {engine, defaultAssets, verifyAssets} from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
E.load(fs.readFileSync(process.argv[2]));
const {X, check, dv, out, args, tsnap} = E;
check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
const rounds = {}; let last = -1, n = 0, pos0 = null;
for (;;) {
  check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap)); const d = dv();
  const round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
  if ((round !== last && phase === 10) || outcome) {
    const s = E.PC.I(d, tsnap); last = round;
    if (!pos0) pos0 = s.camps.map(c => [c.entity.index, c.position.x, c.position.y, c.health]);
    rounds[round] = s.camps.map(c => (c.health > 0 ? '1' : '0')).join('');
  }
  if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
  if (++n > 4000000) throw Error('replay did not terminate');
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
}
fs.writeFileSync(process.argv[3], JSON.stringify({camps: pos0, alive: rounds}));
console.log('rounds', Object.keys(rounds).length, 'camps', pos0.length);
E.destroy();
