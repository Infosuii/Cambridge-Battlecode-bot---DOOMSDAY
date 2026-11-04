// Read one player's own view and executed actions from an engine-2 replay.
import fs from 'node:fs';
import { engine, defaultAssets, verifyAssets } from '../../tools/replay/engine.mjs';
const [replay, rArg, teamArg, actorArg, outFile] = process.argv.slice(2);
if (!outFile || process.env.NFS_REPLAY_ENGINE !== '2.0.0') {
  throw new Error('Usage: set NFS_REPLAY_ENGINE=2.0.0; node trace_turn.mjs replay round teamIndex actorIndex output');
}
const R = Number(rArg), team = Number(teamArg), actor = Number(actorArg);
const assets = defaultAssets();
verifyAssets(assets);
const E = await engine(assets);
E.load(fs.readFileSync(replay));
const { X, check, dv, out, tsnap } = E;
check(X.Game_Visualiser_Timeline_GetMain(E.h, out));
check(X.Game_Visualiser_Timeline_Seek(E.h, dv().getBigUint64(out, true), 0, 0));
let observed;
const actions = [];
for (;;) {
  check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
  const s = E.PC.I(dv(), tsnap);
  if (s.round > R || s.outcome) break;
  const k = s.step;
  if (observed && k.round === R && k.actor.kind === 1 && k.actor.index === actor && k.kind) {
    actions.push({ kind: k.kind, from: k.from, to: k.to, substep: k.substep });
  }
  if (!observed && s.round === R && s.phase === 10 && s.awaitingInput && s.currentChampion === actor) {
    check(X.Game_Visualiser_ReadState(E.h, E.perspective(team, actor), E.snap));
    const v = E.PC.F(dv(), E.snap);
    const unit = c => ({ id: c.entity.index, team: c.team, type: c.type, pos: c.position, hp: c.health,
                         max_hp: c.maxHealth, gems: c.gems, gold: c.gold, cooldowns: c.cooldowns });
    observed = { input: s.inputPosition, actor: v.champions.map(unit).find(c => c.id === actor),
      visible_enemies: v.champions.filter(c => c.team !== team && c.position && c.alive).map(unit),
      visible_camps: v.camps.filter(c => c.position).map(c => ({ id: c.entity.index, pos: c.position, hp: c.health })) };
  }
  check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
}
E.destroy();
if (!observed || !observed.actor) throw new Error('No acting observation for requested round and champion');
const result = { round: R, team, actor, observation: observed, executed_actions: actions };
fs.writeFileSync(outFile, JSON.stringify(result, (key, v) => typeof v === 'bigint' ? v.toString() : v, 2) + '\n');
console.log('round', R, 'actor', actor, 'visible enemies', observed.visible_enemies.length, 'recorded steps', actions.length);
