// Platform replay decode (E75): every round's champion states (team, type, x, y, hp, mhp, str, foc, gems, gold, alive),
// both teams' banked gems, item counts at rounds 100 / 200 / 300 / end, the camp groups (tiles, gems, gold) and the
// walls / holes / altars / spawns, as JSON for tools/platform_study.py. Team 0 is us (team A).
// usage: node platform_decode.js OUTDIR replay.repl26a [more ...]   (ENGWASM = engine 2.0.0)
const fs = require("fs");
const path = require("path");
process.env.ENGWASM = process.env.ENGWASM || path.join(__dirname, "..", "..", "tools", "viz", "v2_0_0.wasm");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));
const [outDir, ...files] = process.argv.slice(2);
fs.mkdirSync(outDir, { recursive: true });
for (const file of files) {
  const E = load(), ex = E.ex, m = () => E.mem;
  const g = E.loadReplay(file);
  E.check(ex.Game_Visualiser_Timeline_GetMain(g, E.outBuf), "main");
  const tl = m().getBigUint64(E.outBuf, true);
  const info = E.alloc(64), items = E.alloc(400), buf = E.alloc(65536);
  const SP = () => E.persp(2, 0xffffffff);
  const u32 = (p) => m().getUint32(p, true);
  const champ = (h) => {
    if (ex.Game_API_Champion_Get(g, SP(), h, info) !== 0) return null;
    const d = m();
    const c = { h, team: d.getInt32(info, true), type: d.getInt32(info + 4, true), x: d.getInt32(info + 8, true), y: d.getInt32(info + 12, true),
      hp: Math.round(d.getFloat32(info + 16, true)), mhp: Math.round(d.getFloat32(info + 20, true)), str: Math.round(d.getFloat32(info + 24, true)), foc: Math.round(d.getFloat32(info + 28, true)) };
    c.gems = ex.Game_API_Champion_GetGems(g, SP(), h, E.outBuf) === 0 ? u32(E.outBuf) : 0;
    c.gold = ex.Game_API_Champion_GetGold(g, SP(), h, E.outBuf) === 0 ? u32(E.outBuf) : 0;
    c.alive = ex.Game_API_Champion_IsAlive(g, h, E.outBuf) === 0 ? m().getInt32(E.outBuf, true) : 0;
    return c;
  };
  const all = () => { const r = []; for (let h = 0; h < 16; h++) { const c = champ(h); if (c) r.push(c); } return r; };
  const state = () => { ex.Game_Runner_GetState(g, E.args); return u32(E.args + 8); };
  const banked = (t) => (ex.Game_API_GetSubmittedGemCount(g, t, E.outBuf) === 0 ? u32(E.outBuf) : 0);
  const itemsOf = (h) => {
    if (ex.Game_API_Champion_GetItems(g, SP(), h, items, 336) !== 0) return null;
    const out = [];
    for (let i = 0; i < 84; i++) out.push(u32(items + 4 * i));
    return out;
  };
  // Camp groups: tiles, gems, gold.
  const groups = [];
  try {
    ex.Game_API_Map_GetNumCampGroups(g, buf);
    const n = u32(buf);
    ex.Game_API_Map_GetCampGroups(g, buf + 8, n, buf + 4);
    for (let k = 0; k < n; k++) {
      const gid = u32(buf + 8 + 4 * k);
      ex.Game_API_Map_CampGroup_Get(g, gid, buf + 4000);
      const gems = u32(buf + 4000), gold = u32(buf + 4004);
      ex.Game_API_Map_CampGroup_GetNumCamps(g, gid, buf + 4100);
      const nc = u32(buf + 4100);
      ex.Game_API_Map_CampGroup_GetCampInfo(g, gid, buf + 4200, nc, buf + 4104);
      const tiles = [];
      for (let c = 0; c < nc; c++) {
        const ci = u32(buf + 4200 + 4 * c);
        ex.Game_API_Map_CampInfo_Get(g, ci, buf + 5000);
        tiles.push([m().getInt32(buf + 5000, true), m().getInt32(buf + 5004, true), m().getInt32(buf + 5008, true)]);
      }
      groups.push({ gems, gold, tiles });
    }
  } catch (e) {
    groups.length = 0;
  }
  E.check(ex.Game_Visualiser_Timeline_Seek(g, tl, 0, 0), "seek");
  let last = -1;
  const rounds = [], itemSnaps = {};
  for (let step = 0; step < 5e6; step++) {
    if (step > 0 && ex.Game_Visualiser_Timeline_ReplayNext(g, 1) !== 0) break;
    const r = state();
    if (r === last) continue;
    last = r;
    const cs = all();
    rounds.push({ round: r, champs: cs, banked: [banked(0), banked(1)] });
    if ([100, 200, 300].includes(r)) itemSnaps[r] = cs.map((c) => ({ h: c.h, team: c.team, items: itemsOf(c.h) }));
  }
  itemSnaps.end = all().map((c) => ({ h: c.h, team: c.team, items: itemsOf(c.h) }));
  const id = path.basename(path.dirname(file)) || path.basename(file);
  fs.writeFileSync(path.join(outDir, `${id}.json`), JSON.stringify({ file, groups, rounds, items: itemSnaps }));
  const fin = rounds[rounds.length - 1];
  console.log(id, "rounds", last, "banked", fin.banked.join("-"), "groups", groups.length);
}
