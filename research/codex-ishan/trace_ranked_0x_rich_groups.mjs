// Read fixed first-champion-phase snapshots for public reward access diagnostics.
import fs from 'node:fs';
import { engine, defaultAssets, verifyAssets } from '../../tools/replay/engine.mjs';
if (process.env.NFS_REPLAY_ENGINE !== '3.0.0') throw new Error('Explicit engine 3 required');
const [input, output] = process.argv.slice(2);
const jobs = JSON.parse(fs.readFileSync(input, 'utf8'));
const assets = defaultAssets();
verifyAssets(assets);
const E = await engine(assets);
const rows = [];
for (const job of jobs) {
  E.load(fs.readFileSync(job.replay));
  const { X, check, dv, out, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out));
  check(X.Game_Visualiser_Timeline_Seek(E.h, dv().getBigUint64(out, true), 0, 0));
  const wanted = new Set(job.rounds);
  const limit = Math.max(...job.rounds);
  const snapshots = [];
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv();
    const round = d.getUint32(tsnap + 8, true);
    const phase = d.getUint32(tsnap + 24, true);
    const outcome = d.getUint32(tsnap + 28, true);
    if (outcome || round > limit) break;
    if (wanted.has(round) && phase === 10) {
      const snap = E.PC.I(d, tsnap);
      if (snap.awaitingInput) {
        const camps = job.camps.map(c => {
          const observed = snap.camps.find(s => s.entity.index === c.handle);
          if (!observed || observed.type !== c.type ||
              observed.position.x !== c.x || observed.position.y !== c.y) {
            throw new Error('Runtime camp identity mismatch');
          }
          return { id: c.handle, hp: observed.health };
        });
        const actors = snap.champions.filter(c => c.alive && c.position).map(c => ({
          id: c.entity.index, team: c.team, type: c.type, x: c.position.x, y: c.position.y,
          hp: c.health, gems: c.gems, gold: c.gold,
          chebyshev: Math.min(...job.camps.map(t => Math.max(Math.abs(c.position.x - t.x), Math.abs(c.position.y - t.y)))),
        }));
        snapshots.push({ round, input: snap.inputPosition, group: snap.groups[job.group], camps, actors });
        wanted.delete(round);
      }
    }
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  E.destroy();
  rows.push({ match: job.match, group: job.group, snapshots, unavailable: [...wanted] });
}
fs.writeFileSync(output, JSON.stringify(rows, null, 2) + '\n', { flag: 'wx' });
