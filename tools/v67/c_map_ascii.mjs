// ASCII map of a replay with champions at one round: '#' wall, '~' hole, '"' bush, 'A' altar, camps by type digit
// (live camps only), team-0 champions 'a'-'e' and team-1 'v'-'z' in id order, spawn tiles '+'.
// Usage: NFS_REPLAY_ENGINE=2.0.0 node tools/v67/c_map_ascii.mjs REPLAY.repl26a ROUND
import fs from 'node:fs';
import {engine, defaultAssets, verifyAssets} from '../replay/engine.mjs';
const [file, roundArg] = process.argv.slice(2);
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
E.load(fs.readFileSync(file));
const {X, check, dv, out: o, args, tsnap} = E;
const u = p => dv().getUint32(p, true);
function readBoard(w, h, stride, getter) {
  check(getter(E.h, E.out)); const p = dv().getUint32(E.out, true), d = dv(), b = new Uint8Array(w * h);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const word = d.getBigUint64(p + 8 * ((y >> 3) * stride + (x >> 3)), true);
    b[y * w + x] = Number((word >> BigInt((y & 7) * 8 + (x & 7))) & 1n);
  }
  return b;
}
const meta = X.Engine_Malloc(64); check(X.Game_GetBitboardMetadata(E.h, meta));
const w = dv().getInt32(meta, true), h = dv().getInt32(meta + 4, true), stride = dv().getUint32(meta + 16, true);
const wall = readBoard(w, h, stride, X.Game_GetWallBuffer), hole = readBoard(w, h, stride, X.Game_GetHoleBuffer);
const altar = readBoard(w, h, stride, X.Game_GetAltarBuffer), bush = readBoard(w, h, stride, X.Game_GetBushBuffer);
const spawn = [0, 1].map(t => { check(X.Game_API_GetSpawnRegion(E.h, t, E.out)); return [0, 4, 8, 12].map(k => dv().getInt32(E.out + k, true)); });
check(X.Game_Visualiser_Timeline_GetMain(E.h, o)); const main = dv().getBigUint64(o, true);
check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = u(args);
check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
const want = Number(roundArg ?? 1);
for (;;) {
  check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
  const round = u(tsnap + 8), phase = u(tsnap + 24), outcome = u(tsnap + 28);
  if ((round >= want && phase === 10) || outcome) {
    const s = E.PC.I(dv(), tsnap);
    const g = [];
    for (let y = 0; y < h; y++) {
      const row = [];
      for (let x = 0; x < w; x++) {
        const i = y * w + x;
        let c = wall[i] ? '#' : hole[i] ? '~' : altar[i] ? 'A' : bush[i] ? '"' : '.';
        for (const sp of spawn) if (x >= sp[0] && x < sp[2] && y >= sp[1] && y < sp[3]) c = '+';
        row.push(c);
      }
      g.push(row);
    }
    for (const c of s.camps) if (c.health > 0 && c.position.x >= 0) g[c.position.y][c.position.x] = String(c.type);
    const ids = [[], []];
    for (const c of s.champions) ids[c.team].push(c);
    ids.forEach((list, t) => list.forEach((c, k) => {
      if (c.alive && c.position) g[c.position.y][c.position.x] = (t === 0 ? 'abcde' : 'vwxyz')[k];
    }));
    console.log(`round ${round} size ${w}x${h}`);
    console.log('    ' + Array.from({length: w}, (_, x) => x % 10).join(''));
    g.forEach((row, y) => console.log(String(y).padStart(3) + ' ' + row.join('')));
    ids.forEach((list, t) => console.log(`team ${t}: ` + list.map((c, k) => `${(t === 0 ? 'abcde' : 'vwxyz')[k]}=type${c.type}@${c.position?.x},${c.position?.y} hp${Math.round(c.health)} g${c.gems}`).join(' ')));
    break;
  }
  if (u(tsnap + 20) !== 0 && u(tsnap + 56) >= size) break;
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
}
E.destroy();
