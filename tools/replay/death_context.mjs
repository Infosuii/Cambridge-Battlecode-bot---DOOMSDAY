// Context of every champion death before a round limit (offline omniscient replay analysis only; never a bot input).
// For each death: the victim's activity over its last 5 alive rounds (camp attacks, PvP attacks, casts, moves), hp a
// few rounds earlier, gems lost, enemy and allied champions within 4 tiles, and whether an awake camp was adjacent.
// Usage: node death_context.mjs <until round> <out.json> <replay>...
import fs from 'node:fs';
import path from 'node:path';
import { engine, defaultAssets, verifyAssets } from './engine.mjs';
const dir = defaultAssets(); verifyAssets(dir);
const E = await engine(dir);
const [untilArg, output, ...files] = process.argv.slice(2);
const UNTIL = Number(untilArg);
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const all = [];
for (const file of files) {
  E.load(fs.readFileSync(file));
  const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  const full = () => { check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap)); return E.PC.I(dv(), tsnap); };
  let lastRound = -1, camps = new Map();
  const hist = new Map(); // champion -> ring of last states/activity
  const cur = new Map();
  const deaths = [];
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), kind = d.getUint32(tsnap + 68, true), actor = d.getUint32(tsnap + 76, true);
    const actorKind = d.getUint32(tsnap + 72, true);
    const phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    if ((round !== lastRound && phase === 10) || outcome) {
      const s = full();
      for (const c of s.champions) {
        const h = hist.get(c.entity.index) ?? []; hist.set(c.entity.index, h);
        const prev = h.at(-1);
        if (prev && prev.alive && !c.alive && lastRound <= UNTIL) {
          const last = h.slice(-5);
          const p = prev.position;
          const enemies = s.champions.filter(o => o.team !== c.team && o.alive && o.position && p && cheb(o.position, p) <= 4).length;
          const allies = s.champions.filter(o => o.team === c.team && o !== c && o.alive && o.position && p && cheb(o.position, p) <= 4).length;
          deaths.push({ round: lastRound, id: c.entity.index, team: c.team, type: c.type, gems: prev.gems, gold: prev.gold,
            hp5: last[0]?.hp ?? null, max_hp: prev.max_hp, enemies4: enemies, allies4: allies,
            camp_attacks: last.reduce((a, x) => a + (x.clear ? 1 : 0), 0), pvp_attacks: last.reduce((a, x) => a + (x.pvp ? 1 : 0), 0),
            casts: last.reduce((a, x) => a + (x.cast ? 1 : 0), 0), x: p?.x, y: p?.y });
        }
        const a = cur.get(c.entity.index) ?? {};
        h.push({ alive: c.alive, position: c.position, hp: c.health, max_hp: c.maxHealth, gems: c.gems, gold: c.gold, ...a });
        if (h.length > 8) h.shift();
      }
      cur.clear();
      camps = new Map(s.camps.filter(c => c.position).map(c => [`${c.position.x},${c.position.y}`, c]));
      lastRound = round;
    }
    if (actorKind === 1) {
      const f = cur.get(actor) ?? {}; cur.set(actor, f);
      if (kind === 5) { const tx = d.getInt32(tsnap + 88, true), ty = d.getInt32(tsnap + 92, true); if (camps.has(`${tx},${ty}`)) f.clear = 1; else f.pvp = 1; }
      else if (kind === 6) f.cast = 1;
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size) || round > UNTIL + 1) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  all.push({ id: path.basename(file).replace('.repl26a', ''), deaths });
  E.destroy();
}
fs.writeFileSync(output, JSON.stringify(all));
console.log(JSON.stringify({ replays: all.length, out: output }));
