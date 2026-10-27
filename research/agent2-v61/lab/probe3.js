// Engine lab probe 3: find the call sequence that reaches a champion's input boundary, then act and end its turn.
const fs = require("fs");
const path = require("path");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));
const E = load();
const ex = E.ex;
const m = () => E.mem;
const err = () => E.cstr(ex.GetLastErrorMsg());
const rc = (name, r) => `${name}=${r}${r ? "(" + err() + ")" : ""}`;
const bytes = fs.readFileSync(process.argv[2]);
const p = ex.Engine_Malloc(bytes.length);
new Uint8Array(ex.memory.buffer, p, bytes.length).set(bytes);
ex.Game_FromMapFileBytes(p, bytes.length, E.outBuf, 0);
const g = m().getBigUint64(E.outBuf, true);
ex.Game_Runner_Init(g);
const st = () => { ex.Game_Runner_GetState(g, E.args); return [0, 1, 2, 3, 4, 5, 6, 7].map((i) => m().getInt32(E.args + 4 * i, true)).join(" "); };
for (let i = 0; i < 12; i++) if (ex.Game_Runner_DraftChampion(g, i, 0) !== 0) break;
const log = [];
for (let k = 0; k < 30; k++) {
  const before = st();
  const a = ex.Game_Runner_Advance(g);
  const s1 = st();
  const e = ex.Game_Runner_EndTurn(g, 0);
  log.push(`${k}: ${before} | ${rc("Advance", a)} -> ${s1} | ${rc("EndTurn", e)} -> ${st()}`);
  if (a !== 0 && e !== 0) {
    const b = ex.Game_Runner_BeginRound(g);
    log.push(`   ${rc("BeginRound", b)} -> ${st()}`);
  }
}
console.log(log.join("\n"));
