// Offline replay analysis. Actor visibility and damage attribution require a separate replay trace.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { defaultAssets, engine, verifyAssets } from '../../../tools/replay/engine.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const cache = path.resolve(here, '../../../artifacts/codex-p0/uk-targets-1104');
const sample = JSON.parse(fs.readFileSync(path.join(here, 'SAMPLE.json'), 'utf8')).matches;
const output = path.join(here, 'EARLY_CAMP_EXPOSURE.json');
if (process.env.NFS_REPLAY_ENGINE !== '2.0.0' || sample.length !== 30) {
  throw new Error('The frozen 30-game sample and engine 2.0.0 are required');
}
const assets = defaultAssets();
verifyAssets(assets);
const replay = await engine(assets);

const distance = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const nearest = (from, to) => to.reduce((min, pos) => Math.min(min, distance(from, pos)), Infinity);

function snapshot(state) {
  const camps = state.camps.filter(c => c.position && c.health > 0).map(c => c.position);
  const living = state.champions.filter(c => c.alive && c.position);
  return new Map(state.champions.map(c => [c.entity.index, {
    team: c.team, type: c.type, alive: c.alive, pos: c.position, hp: c.health, maxHp: c.maxHealth, gems: c.gems,
    campDist: c.position ? nearest(c.position, camps) : Infinity,
    enemyDist: c.position ? nearest(c.position, living.filter(e => e.team !== c.team).map(e => e.position)) : Infinity,
  }]));
}

function frames(file) {
  replay.load(fs.readFileSync(file));
  const { X, check, dv, out, args, tsnap } = replay;
  check(X.Game_Visualiser_Timeline_GetMain(replay.h, out));
  const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(replay.h, main, args, args + 8, args + 16));
  const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(replay.h, main, 0, 0));
  const observed = new Map();
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(replay.h, tsnap));
    const data = dv();
    const round = data.getUint32(tsnap + 8, true);
    const phase = data.getUint32(tsnap + 24, true);
    const outcome = data.getUint32(tsnap + 28, true);
    const atEnd = data.getUint32(tsnap + 20, true) !== 0 && data.getUint32(tsnap + 56, true) >= size;
    if (round >= 1 && round <= 158 && phase === 10 && !observed.has(round)) {
      observed.set(round, snapshot(replay.PC.I(data, tsnap)));
    }
    if (round > 158 || outcome || atEnd) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(replay.h, 1));
  }
  replay.destroy();
  return observed;
}

function episodes(observed) {
  const taken = new Set();
  const found = [];
  for (let round = 6; round <= 150; ++round) {
    const now = observed.get(round);
    if (!now) continue;
    for (const [id, end] of now) {
      if (taken.has(id)) continue;
      const window = Array.from({ length: 6 }, (_, step) => observed.get(round - 5 + step)?.get(id));
      if (window.some(c => !c?.alive || c.maxHp !== end.maxHp || c.campDist > 3 || c.enemyDist <= 6)) continue;
      const start = window[0];
      if (start.hp - end.hp < end.maxHp / 4) continue;
      taken.add(id);
      const horizon = Array.from({ length: 8 }, (_, i) => observed.get(round + i + 1));
      const subsequent = horizon.map(frame => frame?.get(id));
      const future = subsequent.at(-1);
      found.push({ id, team: end.team, type: end.type, round, startHp: start.hp, endHp: end.hp,
        maxHp: end.maxHp, pos: end.pos, gems: end.gems, campDist: end.campDist,
        diedWithin8: subsequent.every(Boolean) ? subsequent.some(c => !c.alive) : null,
        balanceDelta: future?.alive ? future.gems - end.gems : null,
        displacement: future?.alive && future.pos ? distance(future.pos, end.pos) : null });
    }
  }
  return found;
}

const rows = sample.map(m => ({ id: m.id, rival: m.opponent, result: m.result, side: m.side,
  episodes: episodes(frames(path.join(cache, 'replays/rep', `${m.id}.repl26a`))) }));
const totals = Object.fromEntries(['loss', 'win'].map(result => {
  const games = rows.filter(r => r.result === result);
  const own = games.map(r => r.episodes.filter(e => e.team === Number(r.side.toUpperCase() === 'B')));
  const rival = games.map(r => r.episodes.filter(e => e.team !== Number(r.side.toUpperCase() === 'B')));
  return [result, { games: games.length, ourEvents: own.flat().length, rivalEvents: rival.flat().length,
    gamesWithMoreOwn: games.filter((_, i) => own[i].length > rival[i].length).length,
    gamesWithMoreRival: games.filter((_, i) => own[i].length < rival[i].length).length }];
}));
fs.writeFileSync(output, `${JSON.stringify({ totals, rows }, null, 2)}\n`, { flag: 'wx' });
console.log(JSON.stringify(totals));
