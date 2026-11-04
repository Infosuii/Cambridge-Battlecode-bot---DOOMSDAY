// Compare exact ordered champion actions on a frozen set of native development replays.
import fs from 'node:fs';
import { engine, defaultAssets, verifyAssets } from '../../tools/replay/engine.mjs';

const [manifest, output] = process.argv.slice(2);
if (!output || process.env.NFS_REPLAY_ENGINE !== '2.0.0') {
  throw new Error('Set NFS_REPLAY_ENGINE=2.0.0 and pass a manifest and output path');
}
const { reference, controls, through } = JSON.parse(fs.readFileSync(manifest, 'utf8'));
const assets = defaultAssets();
verifyAssets(assets);
const E = await engine(assets);

function trace(file) {
  E.load(fs.readFileSync(file));
  const { X, check, dv, out, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out));
  check(X.Game_Visualiser_Timeline_Seek(E.h, dv().getBigUint64(out, true), 0, 0));
  const rows = [];
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const s = E.PC.I(dv(), tsnap);
    if (s.round > through || s.outcome) break;
    const k = s.step;
    if (k.actor.kind === 1 && k.kind && k.kind !== 3 && k.round <= through) {
      rows.push({ round: k.round, actor: k.actor.index, kind: k.kind, from: k.from, to: k.to, substep: k.substep });
    }
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  E.destroy();
  return rows;
}

function firstDifference(before, after) {
  const n = Math.min(before.length, after.length);
  let i = 0;
  while (i < n && JSON.stringify(before[i]) === JSON.stringify(after[i])) i++;
  if (i === before.length && i === after.length) return null;
  return { matchedActions: i, reference: before[i] ?? null, control: after[i] ?? null };
}

const gameActions = rows => rows.filter(row => row.kind !== 26);
const original = trace(reference);
const comparisons = Object.fromEntries(Object.entries(controls).map(([name, file]) => {
  const observed = trace(file);
  return [name, { withFuel: firstDifference(original, observed), game: firstDifference(gameActions(original), gameActions(observed)) }];
}));
fs.writeFileSync(output, JSON.stringify({ through, comparisons }, null, 2) + '\n', { flag: 'wx' });
console.log(JSON.stringify(comparisons));
