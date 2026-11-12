// Engine lab probe 6: sandbox unit passed as a pointer to a small struct (kind, handle) or (handle, kind).
process.env.ENGWASM = require("path").join(__dirname, "..", "..", "tools", "viz", "v0_0_3.wasm");
const fs = require("fs");
const path = require("path");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));
const E = load();
const ex = E.ex;
const m = () => E.mem;
const err = () => E.cstr(ex.GetLastErrorMsg());
const bytes = fs.readFileSync(process.argv[2]);
const p = ex.Engine_Malloc(bytes.length);
new Uint8Array(ex.memory.buffer, p, bytes.length).set(bytes);
ex.Game_FromMapFileBytes(p, bytes.length, E.outBuf, 0);
const g = m().getBigUint64(E.outBuf, true);
ex.Game_Runner_Init(g);
const st = () => { ex.Game_Runner_GetState(g, E.args); return [0, 1, 2, 3].map((i) => m().getInt32(E.args + 4 * i, true)); };
for (let k = 0; k < 40 && st()[0] === 0; k++) {
  ex.Game_Runner_Advance(g);
  if (st()[0] !== 0) break;
  for (let c = 0; c < 12; c++) if (ex.Game_Action_Draft(g, c) === 0) break;
  ex.Game_Runner_EndTurn(g, 0);
}
ex.Game_Runner_Advance(g);
const info = E.alloc(64);
const champ = (h) => {
  ex.Game_API_Champion_Get(g, E.persp(2, 0xffffffff), h, info);
  const d = m();
  return `(${d.getInt32(info + 8, true)},${d.getInt32(info + 12, true)}) hp ${Math.round(d.getFloat32(info + 16, true))}`;
};
const h = st()[3];
const u = E.alloc(32), v = E.alloc(32);
const unit = (ptr, kind, hh) => { m().setUint32(ptr, kind, true); m().setUint32(ptr + 4, hh, true); m().setUint32(ptr + 8, 0, true); return ptr; };
const enemy = 5;
console.log("before: me", champ(h), "enemy", champ(enemy));
let r = ex.Game_Sandbox_Damage(g, unit(u, 1, h), unit(v, 1, enemy), 100.0);
console.log(`Damage(me -> enemy, 100) -> ${r}${r ? " [" + err() + "]" : ""}  enemy now ${champ(enemy)}  me ${champ(h)}`);
r = ex.Game_Sandbox_Damage(g, unit(u, 1, enemy), unit(v, 1, h), 300.0);
console.log(`Damage(enemy -> me, 300) -> ${r}${r ? " [" + err() + "]" : ""}  me now ${champ(h)}`);
ex.Game_Runner_EndTurn(g, 0); ex.Game_Runner_Advance(g);
console.log("after turn end: me", champ(h), "enemy", champ(enemy), "state", st().join(" "));
r = ex.Game_Sandbox_Teleport(g, unit(u, 1, h), 0);
console.log(`Teleport(me, 0) -> ${r}${r ? " [" + err() + "]" : ""}`);
const pos = E.alloc(16); m().setInt32(pos, 10, true); m().setInt32(pos + 4, 10, true);
r = ex.Game_Sandbox_Teleport(g, unit(u, 1, h), pos);
console.log(`Teleport(me, ptr(10,10)) -> ${r}${r ? " [" + err() + "]" : ""}  me ${champ(h)}`);