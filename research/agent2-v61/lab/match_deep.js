// Deep replay analysis (E63): per game the map's camp groups and gems, each champion's items at the end and stats over
// time, and every death with its context (round, carried gems lost, enemies within 4, our allies within 4, health a
// round before). We are team 0.  usage: node match_deep.js replay.repl26a [more ...]   (ENGWASM = engine 2.0.0)
const path = require("path");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));
const NAMES = ["Ryth", "Vesper", "Vendetta", "Cassi", "Issac", "Stellar", "Prism", "Marcella", "Willow", "Ren", "Varg", "Tavi", "Heart"];
const FAM = ["monster", "power", "durability", "treasure", "jungle", "home", "bruiser", "tribute", "capture", "prospector", "hunter", "skirmish", "greed", "collectors"];
const STAT = ["str", "str*", "foc", "foc*", "hp", "hp*"];
for (const file of process.argv.slice(2)) {
  const E = load(), ex = E.ex, m = () => E.mem;
  const g = E.loadReplay(file);
  E.check(ex.Game_Visualiser_Timeline_GetMain(g, E.outBuf), "main");
  const tl = m().getBigUint64(E.outBuf, true);
  E.check(ex.Game_Visualiser_Timeline_Info(g, tl, E.args, E.args + 8, E.args + 16), "info");
  const size = m().getUint32(E.args, true);
  const info = E.alloc(64), items = E.alloc(400), buf = E.alloc(4096);
  const SP = () => E.persp(2, 0xffffffff);
  const champ = (h) => {
    if (ex.Game_API_Champion_Get(g, SP(), h, info) !== 0) return null;
    const d = m();
    const c = { h, team: d.getInt32(info, true), type: d.getInt32(info + 4, true), x: d.getInt32(info + 8, true), y: d.getInt32(info + 12, true),
      hp: d.getFloat32(info + 16, true), mhp: d.getFloat32(info + 20, true), str: d.getFloat32(info + 24, true), foc: d.getFloat32(info + 28, true) };
    c.gems = ex.Game_API_Champion_GetGems(g, SP(), h, E.outBuf) === 0 ? m().getUint32(E.outBuf, true) : 0;
    c.gold = ex.Game_API_Champion_GetGold(g, SP(), h, E.outBuf) === 0 ? m().getUint32(E.outBuf, true) : 0;
    c.alive = ex.Game_API_Champion_IsAlive(g, h, E.outBuf) === 0 ? m().getInt32(E.outBuf, true) : 0;
    return c;
  };
  const all = () => { const r = []; for (let h = 0; h < 16; h++) { const c = champ(h); if (c) r.push(c); } return r; };
  const state = () => { ex.Game_Runner_GetState(g, E.args); return m().getUint32(E.args + 8, true); };
  // map summary
  ex.Game_API_Map_GetNumCampGroups(g, buf);
  const ng = m().getUint32(buf, true);
  // walk the timeline once, snapshot every round
  E.check(ex.Game_Visualiser_Timeline_Seek(g, tl, 0, 0), "seek");
  let last = -1, prev = null, prev2 = null;
  const deaths = [], series = {};
  for (let step = 0; step < 5e6; step++) {
    if (step > 0 && ex.Game_Visualiser_Timeline_ReplayNext(g, 1) !== 0) break;
    const r = state();
    if (r === last) continue;
    last = r;
    const cs = all();
    if (prev) for (const c of cs) {
      const p = prev.find((q) => q.h === c.h), p2 = (prev2 || prev).find((q) => q.h === c.h) || p;
      if (p && p.alive && !c.alive) {
        const near = (team) => prev.filter((q) => q.team === team && q.alive && q.h !== c.h && Math.max(Math.abs(q.x - p.x), Math.abs(q.y - p.y)) <= 4).length;
        deaths.push({ r, team: c.team, type: NAMES[c.type], lost: p.gems, enemies: near(1 - c.team), allies: near(c.team), hp: Math.round(p2.hp), mhp: Math.round(p.mhp), x: p.x, y: p.y });
      }
    }
    if (r % 100 === 0 || r === 1) for (const c of cs) (series[c.h] = series[c.h] || []).push([r, Math.round(c.str), Math.round(c.foc), Math.round(c.mhp), c.gold]);
    prev2 = prev, prev = cs;
  }
  const fin = all();
  console.log(`\n##### ${path.basename(file)}  camp groups ${ng}  rounds ${last}`);
  for (const c of fin) {
    let txt = "";
    if (ex.Game_API_Champion_GetItems(g, SP(), c.h, items, 336) === 0) {
      const parts = [];
      for (let i = 0; i < 84; i++) { const n = m().getUint32(items + 4 * i, true); if (n) parts.push(`${FAM[Math.floor(i / 6)]}-${STAT[i % 6]}x${n}`); }
      txt = parts.join(" ");
    }
    const s = series[c.h] || [];
    const pick = (rr) => { const e = s.find((q) => q[0] >= rr); return e ? `${e[1]}/${e[2]}/${e[3]}` : "-"; };
    console.log(`  ${c.team === 0 ? "US  " : "THEM"} ${NAMES[c.type].padEnd(9)} str/foc/hp r200 ${pick(200)} r500 ${pick(500)} end ${Math.round(c.str)}/${Math.round(c.foc)}/${Math.round(c.mhp)} | ${txt}`);
  }
  for (const t of [0, 1]) {
    const ds = deaths.filter((d) => d.team === t);
    const lost = ds.reduce((a, d) => a + d.lost, 0);
    const outn = ds.filter((d) => d.enemies > d.allies + 1).length, solo = ds.filter((d) => d.allies === 0).length, noenemy = ds.filter((d) => d.enemies === 0).length;
    console.log(`  ${t === 0 ? "US  " : "THEM"} deaths ${ds.length}, gems lost ${lost}, outnumbered by 2+ ${outn}, alone ${solo}, no enemy within 4 (camps?) ${noenemy}`);
    if (t === 0) for (const d of ds.slice(0, 40)) console.log(`     r${d.r} ${d.type} lost ${d.lost} gems, enemies ${d.enemies} allies ${d.allies}, hp a round before ${d.hp}/${d.mhp} at (${d.x},${d.y})`);
  }
}
