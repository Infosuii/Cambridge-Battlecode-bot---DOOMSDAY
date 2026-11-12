// Dump an engine-3 replay: one frame per round (every champion's position, hp, gems, gold, consumables), every action
// step except Tick / End turn (round, kind name, actor, from, to), and each champion's final item counts.
// usage: node dump.mjs replay.repl26a out.json
import fs from 'node:fs';
import {engine, defaultAssets, verifyAssets} from './engine.mjs';
const KIND = 'Phase.Respawn.Capture.Tick.Move.Attack.Cast ability.Input.End turn.Set priority..Recall.Submit gems.Shop.Place ward.Consumable.Cancel channel.Sandbox.Gems submitted.Draft champion.Place altar lock.Teleport channel.Teleport complete.Movement blocked.Resign.Sell item.Turn rollover.Bot error'.split('.');
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
E.load(fs.readFileSync(process.argv[2]));
const {X, check, dv, out, args, tsnap} = E;
check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
const frames = [], steps = []; let lastRound = -1, lastKey = '', n = 0, final = null, camps0 = null;
for (;;) {
  check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap)); const d = dv();
  const round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
  const kind = d.getUint32(tsnap + 68, true), ak = d.getUint32(tsnap + 72, true), actor = d.getUint32(tsnap + 76, true);
  const key = [round, pos, kind, ak, actor, d.getUint32(tsnap + 100, true)].join(':');
  if (key !== lastKey) {
    lastKey = key;
    if (ak === 1 && kind !== 3 && kind !== 8)
      steps.push([round, KIND[kind] ?? String(kind), actor, d.getInt32(tsnap + 80, true), d.getInt32(tsnap + 84, true), d.getInt32(tsnap + 88, true), d.getInt32(tsnap + 92, true)]);
  }
  if ((round !== lastRound && phase === 10) || outcome) {
    const s = E.PC.I(d, tsnap); final = s;
    if (!camps0) camps0 = s.camps.map(c => [c.entity.index, c.position.x, c.position.y, c.health]);
    frames.push([round, s.champions.map(c => [c.entity.index, c.team, c.type, c.position ? c.position.x : null, c.position ? c.position.y : null,
      c.health, c.alive ? 1 : 0, c.gems, c.gold, ...c.consumables])]);
    lastRound = round;
  }
  if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
  if (++n > 4000000) throw Error('replay did not terminate');
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
}
const items = final.champions.map(c => [c.entity.index, c.team, c.type, c.items]);
fs.writeFileSync(process.argv[3], JSON.stringify({frames, steps, items, camps0, kinds: KIND}));
console.log('frames', frames.length, 'steps', steps.length);
E.destroy();
