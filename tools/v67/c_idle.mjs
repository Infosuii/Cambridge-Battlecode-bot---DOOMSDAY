// Idle-champion audit for local engine-2 replays: every interval of at least MIN rounds in which a champion is alive,
// away from its starting tile, and takes no action at all (no move, attack, cast, ward, buy, recall or tribute step).
// Usage: NFS_REPLAY_ENGINE=2.0.0 node tools/v67/c_idle.mjs OUT.jsonl MIN REPLAY.repl26a ...
// Output line per replay: {file, rounds, idle:[{id, team, type, from, to, x, y, hp, gems}]}.
import fs from 'node:fs';
import path from 'node:path';
import {engine, defaultAssets, verifyAssets} from '../replay/engine.mjs';
const [output, minArg, ...files] = process.argv.slice(2);
const MIN = Number(minArg);
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
// move, attack, cast, recall, tribute start, buy, ward, tribute bank, dash move, sell
const ACTIONS = new Set([4, 5, 6, 11, 12, 13, 14, 18, 23, 25]);
const out = fs.createWriteStream(output);
for (const file of files) {
  E.load(fs.readFileSync(file));
  const {X, check, dv, out: o, args, tsnap} = E;
  const u = p => dv().getUint32(p, true);
  check(X.Game_Visualiser_Timeline_GetMain(E.h, o)); const main = dv().getBigUint64(o, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = u(args);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  let lastRound = -1;
  const start = new Map(), lastAct = new Map(), state = new Map(), idle = [];
  const close = (id, round) => {
    const s = state.get(id);
    if (!s || !s.alive) return;
    const from = Math.max(lastAct.get(id) ?? 0, s.since);
    if (round - from >= MIN) idle.push({id, team: s.team, type: s.type, from, to: round, x: s.pos?.x, y: s.pos?.y, hp: s.hp, gems: s.gems});
  };
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const round = u(tsnap + 8), phase = u(tsnap + 24), outcome = u(tsnap + 28), kind = u(tsnap + 68), ak = u(tsnap + 72), actor = u(tsnap + 76);
    if (ak === 1 && ACTIONS.has(kind)) {
      // a champion action step (visualiser step kinds, as in tools/replay/decode_replays.mjs)
      if (state.get(actor)?.alive) close(actor, round);
      lastAct.set(actor, round);
    }
    if ((round !== lastRound && phase === 10) || outcome) {
      const s = E.PC.I(dv(), tsnap); lastRound = round;
      for (const c of s.champions) {
        const id = c.entity.index;
        if (!start.has(id) && c.position) start.set(id, c.position);
        const prev = state.get(id);
        const home = start.get(id) && c.position && cheb(start.get(id), c.position) <= 1;
        const alive = c.alive && !home;
        if (prev?.alive && !alive) close(id, round);
        if (!prev?.alive && alive) lastAct.set(id, round);
        state.set(id, {alive, team: c.team, type: c.type, pos: c.position, hp: c.health, gems: c.gems,
                       since: prev?.alive && alive ? prev.since : round});
      }
    }
    if (outcome || (u(tsnap + 20) !== 0 && u(tsnap + 56) >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  for (const id of state.keys()) close(id, lastRound);
  out.write(JSON.stringify({file: path.basename(file), rounds: lastRound, idle}) + '\n');
  E.destroy();
}
out.end();
