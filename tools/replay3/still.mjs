// Standing-still audit per team from engine-3 replays (raw .repl26a, or a bundle zip's replay.repl26a extracted first).
// usage: node tools/replay3/still.mjs list.json out.json
//   list.json: [{"id": "...", "replay": "path/to/replay.repl26a", "us": 0|1, "tag": "v114"}, ...]
// Per team: alive samples; still = alive in consecutive round samples on the same tile; quiet = still with no
// attack (5) or cast (6) step between the samples; long = quiet samples inside runs of >= 8; plus action-step counts
// by kind (4 move, 5 attack, 6 cast, 11/12/13 other actions such as channels and banking).
import fs from 'node:fs';
import {engine, defaultAssets, verifyAssets} from './engine.mjs';

const list = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const dir = defaultAssets();
verifyAssets(dir);
const E = await engine(dir);
const same = (a, b) => a && b && a.x === b.x && a.y === b.y;
const out = [];
for (const item of list) {
  E.load(fs.readFileSync(item.replay));
  const {X, check, dv, out: o, args, tsnap} = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, o));
  const main = dv().getBigUint64(o, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16));
  const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  const frames = [], acts = [];
  let lastRound = -1, lastKey = '', steps = 0;
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv();
    const round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true);
    const pos = d.getUint32(tsnap + 56, true), kind = d.getUint32(tsnap + 68, true), ak = d.getUint32(tsnap + 72, true);
    const actor = d.getUint32(tsnap + 76, true);
    const key = [round, pos, kind, ak, actor, d.getUint32(tsnap + 100, true)].join(':');
    if (key !== lastKey) {
      lastKey = key;
      if (ak === 1 && [4, 5, 6, 11, 12, 13].includes(kind)) acts.push({round, kind, id: actor});
    }
    if ((round !== lastRound && phase === 10) || outcome) {
      const s = E.PC.I(d, tsnap);
      frames.push({round, ch: s.champions.map(c => ({id: c.entity.index, team: c.team, alive: c.alive, p: c.position}))});
      lastRound = round;
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    if (++steps > 3000000) throw Error('Replay did not terminate');
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  const team = [0, 1].map(() => ({alive: 0, still: 0, quiet: 0, long: 0, kinds: {}}));
  const teamOf = new Map();
  for (const c of frames[0].ch) teamOf.set(c.id, c.team);
  for (const a of acts) {
    const t = teamOf.get(a.id);
    if (t === undefined) continue;
    team[t].kinds[a.kind] = (team[t].kinds[a.kind] ?? 0) + 1;
  }
  const fight = new Map(); // id -> Set of rounds with an attack or cast step
  for (const a of acts) if (a.kind === 5 || a.kind === 6) {
    if (!fight.has(a.id)) fight.set(a.id, new Set());
    fight.get(a.id).add(a.round);
  }
  for (const [id, t] of teamOf) {
    let run = 0;
    const flush = () => { if (run >= 8) team[t].long += run; run = 0; };
    for (let i = 1; i < frames.length; ++i) {
      const a = frames[i - 1].ch.find(c => c.id === id), b = frames[i].ch.find(c => c.id === id);
      if (!a || !b || !b.alive) { flush(); continue; }
      team[t].alive++;
      if (!(a.alive && same(a.p, b.p))) { flush(); continue; }
      team[t].still++;
      let acted = false;
      const f = fight.get(id);
      if (f) for (let r = frames[i - 1].round; r < frames[i].round && !acted; ++r) acted = f.has(r);
      if (acted) { flush(); continue; }
      team[t].quiet++;
      run++;
    }
    flush();
  }
  out.push({...item, rounds: frames.at(-1).round, us_team: team[item.us], them_team: team[1 - item.us]});
  console.log(JSON.stringify({id: item.id, tag: item.tag, rounds: frames.at(-1).round, us: team[item.us]}));
}
fs.writeFileSync(process.argv[3], JSON.stringify(out, null, 1));
E.destroy();
