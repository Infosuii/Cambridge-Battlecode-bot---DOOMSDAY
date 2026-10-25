// Offline altar-lock counts and tribute-attempt timing; these correlations do not establish lock causality.
// Usage: node v58_lock_audit.mjs <out.json> <replay>...
import fs from 'node:fs';
import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir); const E = await engine(dir);
const [output, ...files] = process.argv.slice(2), rows = [];
for (const file of files) {
  E.load(fs.readFileSync(file)); const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  const teams = [0, 1].map(() => ({ locks: 0, starts: 0, banks: 0, restarts: 0, latency_rounds: [] }));
  const pending = new Map(); let actors = null;
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true);
    const kind = d.getUint32(tsnap + 68, true), actor = d.getUint32(tsnap + 76, true), ak = d.getUint32(tsnap + 72, true);
    if (!actors && phase === 10) actors = new Map(E.PC.I(d, tsnap).champions.map(c => [c.entity.index, c.team]));
    if (ak === 1 && actors?.has(actor)) {
      const t = teams[actors.get(actor)];
      if (kind === 20) t.locks++;
      if (kind === 12) { t.starts++; if (pending.has(actor)) t.restarts++; pending.set(actor, round); }
      if (kind === 18) {
        t.banks++; if (pending.has(actor)) t.latency_rounds.push(round - pending.get(actor)); pending.delete(actor);
      }
    }
    if (d.getUint32(tsnap + 28, true) || (d.getUint32(tsnap + 20, true) !== 0 && d.getUint32(tsnap + 56, true) >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  rows.push({ id: path.basename(file).replace('.repl26a', ''), teams }); E.destroy();
}
fs.writeFileSync(output, JSON.stringify(rows));
