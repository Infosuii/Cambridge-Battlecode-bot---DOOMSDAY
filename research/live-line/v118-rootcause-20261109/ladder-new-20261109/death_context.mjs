// Death context for our champions: the 8 rounds before each death, from the official decoder (offline).
// Usage: node death_context.mjs spec.json out.json   spec = [{replay, side, deaths:[{id, round, killer}]}]
import fs from 'node:fs';
import {engine, defaultAssets, verifyAssets} from 'file:///C:/projects/cambridge%20battlecode/work/agentic-improvement/autonomy/replay/engine.mjs';
const [specFile, dest] = process.argv.slice(2);
const specs = JSON.parse(fs.readFileSync(specFile, 'utf8'));
const dir = defaultAssets(); verifyAssets(dir);
const dist = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const results = [];
for (const s of specs) {
  const E = await engine(dir); E.load(fs.readFileSync(s.replay));
  const {X, check, dv, out, args, tsnap} = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const tl = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, tl, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, tl, 0, 0)); let steps = 0;
  const want = new Set(); for (const d of s.deaths) for (let r = d.round - 8; r <= d.round; ++r) want.add(r);
  const frames = new Map(); let last = -1;
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    if (round !== last && phase === 10 && want.has(round)) {
      const st = E.PC.I(d, tsnap); last = round;
      frames.set(round, {champs: st.champions.map(c => ({id: c.entity.index, team: c.team, alive: c.alive, p: c.position, hp: c.health, max: c.maxHealth, gems: c.gems, type: c.type})),
        camps: st.camps.filter(c => c.health > 0).map(c => c.position)});
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    if (++steps > 3000000) throw Error('Replay did not terminate');
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  for (const dth of s.deaths) {
    const rows = [];
    for (let r = dth.round - 8; r <= dth.round; ++r) {
      const f = frames.get(r); if (!f) continue;
      const me = f.champs.find(c => c.id === dth.id); if (!me || !me.alive || !me.p) continue;
      const k = f.champs.find(c => c.id === dth.killer);
      const allies = f.champs.filter(c => c.team === s.side && c.id !== dth.id && c.alive && c.p && dist(c.p, me.p) <= 6).length;
      const enemies = f.champs.filter(c => c.team !== s.side && c.alive && c.p && dist(c.p, me.p) <= 6).length;
      rows.push({r, hp: me.hp, max: me.max, gems: me.gems, p: me.p, dk: k && k.alive && k.p ? dist(k.p, me.p) : null, allies, enemies,
                 camp3: f.camps.some(c => dist(c, me.p) <= 3)});
    }
    results.push({match: s.match, map: s.map, side: s.side, id: dth.id, name: dth.name, killer: dth.killerName, round: dth.round, rows});
  }
}
fs.writeFileSync(dest, JSON.stringify(results));
console.log('deaths', results.length);
