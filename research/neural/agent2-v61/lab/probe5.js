// Engine lab probe 5: find the sandbox unit encoding and teleport position format.
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
console.log('create', ex.Game_FromMapFileBytes(p, bytes.length, E.outBuf, parseInt(process.argv[3] || '1')), err());
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
const encs = [h, h + 1, 0, 1, 2];
for (const u of encs) {
  const r = ex.Game_Sandbox_Damage(g, u >>> 0, u >>> 0, 50.0);
  console.log(`Damage(unit=0x${(u >>> 0).toString(16)}) -> ${r}${r ? " [" + err() + "]" : ""}  champion ${champ(h)}`);
  const r2 = ex.Game_Sandbox_Damage(g, u >>> 0, 0, 50.0);
  console.log(`Damage(unit, 0) -> ${r2}${r2 ? " [" + err() + "]" : ""}  champion ${champ(h)}`);
}
