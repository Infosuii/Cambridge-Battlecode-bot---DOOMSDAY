// Engine lab probe 4 (v0_0_3 module): draft, reach a champion's turn, teleport/move/damage/attack and read the result.
process.env.ENGWASM = require("path").join(__dirname, "..", "..", "tools", "viz", "v0_0_3.wasm");
const fs = require("fs");
const path = require("path");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));
const E = load();
const ex = E.ex;
const m = () => E.mem;
const err = () => E.cstr(ex.GetLastErrorMsg());
const rc = (name, r) => console.log(`${name} -> ${r}${r ? " [" + err() + "]" : ""}`);
const bytes = fs.readFileSync(process.argv[2]);
const p = ex.Engine_Malloc(bytes.length);
new Uint8Array(ex.memory.buffer, p, bytes.length).set(bytes);
rc("FromMap", ex.Game_FromMapFileBytes(p, bytes.length, E.outBuf, 0));
const g = m().getBigUint64(E.outBuf, true);
rc("Init", ex.Game_Runner_Init(g));
const st = () => { ex.Game_Runner_GetState(g, E.args); return [0, 1, 2, 3].map((i) => m().getInt32(E.args + 4 * i, true)); };
// Draft: alternate Advance + Draft until play starts.
for (let k = 0; k < 40 && st()[0] === 0; k++) {
  ex.Game_Runner_Advance(g);
  if (st()[0] !== 0) break;
  for (let c = 0; c < 12; c++) if (ex.Game_Action_Draft(g, c) === 0) break;
  ex.Game_Runner_EndTurn(g, 0);
}
console.log("after draft", st().join(" "));
const info = E.alloc(64);
const champ = (h) => {
  if (ex.Game_API_Champion_Get(g, E.persp(2, 0xffffffff), h, info) !== 0) return null;
  const d = m();
  return { h, team: d.getInt32(info, true), x: d.getInt32(info + 8, true), y: d.getInt32(info + 12, true), hp: Math.round(d.getFloat32(info + 16, true)) };
};
rc("Advance", ex.Game_Runner_Advance(g));
let s = st();
console.log("turn state", s.join(" "), "champion", JSON.stringify(champ(s[3])));
const me = champ(s[3]);
rc("Teleport(x,y)", ex.Game_Sandbox_Teleport(g, 20, 20));
console.log("after teleport", JSON.stringify(champ(s[3])));
rc("Move(x,y,out)", ex.Game_Action_Move(g, 21, 21, E.outBuf));
console.log("after move", JSON.stringify(champ(s[3])));
rc("Damage(h, h, 100)", ex.Game_Sandbox_Damage(g, s[3], s[3], 100.0));
console.log("after damage", JSON.stringify(champ(s[3])));
rc("EndTurn", ex.Game_Runner_EndTurn(g, 0));
rc("Advance", ex.Game_Runner_Advance(g));
s = st();
console.log("next turn", s.join(" "), JSON.stringify(champ(s[3])));
rc("Teleport next to first", ex.Game_Sandbox_Teleport(g, 22, 21));
rc("Attack first", ex.Game_Action_Attack(g, me.h));
console.log("first champion after attack", JSON.stringify(champ(me.h)));
