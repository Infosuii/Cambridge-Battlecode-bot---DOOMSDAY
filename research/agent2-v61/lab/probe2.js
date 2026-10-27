// Engine lab probe 2: draft, step into play, read champions, then teleport/damage one and watch the next steps.
const fs = require("fs");
const path = require("path");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));
const E = load();
const ex = E.ex;
const m = () => E.mem;
const err = () => E.cstr(ex.GetLastErrorMsg());
const ok = (name, r) => { if (r !== 0) console.log(`  ${name} -> ${r} [${err()}]`); return r === 0; };

const bytes = fs.readFileSync(process.argv[2]);
const p = ex.Engine_Malloc(bytes.length);
new Uint8Array(ex.memory.buffer, p, bytes.length).set(bytes);
ok("FromMap", ex.Game_FromMapFileBytes(p, bytes.length, E.outBuf, 0));
const g = m().getBigUint64(E.outBuf, true);
ok("Init", ex.Game_Runner_Init(g));
const st = () => { ex.Game_Runner_GetState(g, E.args); return [0, 1, 2, 3, 4, 5].map((i) => m().getInt32(E.args + 4 * i, true)); };
for (let i = 0; i < 12 && st()[0] === 0; i++) ok(`draft ${i}`, ex.Game_Runner_DraftChampion(g, i, 0));
console.log("after draft state", st().join(" "));
const info = E.alloc(64);
const champs = () => {
  const out = [];
  for (let h = 0; h < 16; h++) {
    if (ex.Game_API_Champion_Get(g, E.persp(2, 0xffffffff), h, info) !== 0) continue;
    const d = m();
    out.push({ h, team: d.getInt32(info, true), type: d.getInt32(info + 4, true), x: d.getInt32(info + 8, true), y: d.getInt32(info + 12, true),
      hp: Math.round(d.getFloat32(info + 16, true)), mhp: Math.round(d.getFloat32(info + 20, true)) });
  }
  return out;
};
// Step forward a little and log state transitions.
for (let k = 0; k < 40; k++) {
  const s = st();
  if (k < 12 || k % 10 === 0) console.log(`step ${k} state ${s.join(" ")}`);
  if (!ok("Step", ex.Game_Runner_Step(g))) break;
  const s2 = st(); if (s2.join() === s.join()) ok("EndTurn", ex.Game_Runner_EndTurn(g, 0));
}
console.log("champions:", JSON.stringify(champs()));
// Sandbox: teleport champion 0 next to champion with team 1, damage it, then read.
const cs = champs();
const a = cs.find((c) => c.team === 0), b = cs.find((c) => c.team === 1);
if (a && b) {
  console.log("teleport", a.h, "to", b.x + 1, b.y);
  const vp = E.alloc(16); m().setInt32(vp, b.x + 1, true); m().setInt32(vp + 4, b.y, true); ok("Teleport ptr", ex.Game_Sandbox_Teleport(g, a.h, vp));
  console.log("after teleport:", JSON.stringify(champs().find((c) => c.h === a.h)));
  ok("Damage", ex.Game_Sandbox_Damage(g, a.h, a.h, 200.0));
  console.log("after damage(a,a,200):", JSON.stringify(champs().find((c) => c.h === a.h)));
}
