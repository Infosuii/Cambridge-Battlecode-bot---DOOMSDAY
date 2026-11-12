// Engine lab probe: create a game from a map, draft, step into play, read champions; report engine errors.
const fs = require("fs");
const path = require("path");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));
const E = load();
const ex = E.ex;
const m = () => E.mem;
const err = () => E.cstr(ex.GetLastErrorMsg());
const call = (name, ...a) => {
  const r = ex[name](...a);
  console.log(`${name}(${a.map(String).join(", ")}) -> ${r}${r !== 0 ? "  [" + err() + "]" : ""}`);
  return r;
};

const mapBytes = fs.readFileSync(process.argv[2]);
const p = ex.Engine_Malloc(mapBytes.length);
new Uint8Array(ex.memory.buffer, p, mapBytes.length).set(mapBytes);
// Game_FromMapFileBytes(ptr, len, ?, out)
let r = call("Game_FromMapFileBytes", p, mapBytes.length, E.outBuf, 0);
if (r !== 0) r = call("Game_FromMapFileBytes", p, mapBytes.length, E.outBuf, 1);
const g = m().getBigUint64(E.outBuf, true);
console.log("game handle", g);
call("Game_Runner_Init", g);
const state = () => {
  ex.Game_Runner_GetState(g, E.args);
  const w = [];
  for (let i = 0; i < 6; i++) w.push(m().getUint32(E.args + 4 * i, true));
  return w.join(" ");
};
console.log("state after init:", state());
// Try drafting a few champions: DraftChampion(g, a, b)
for (let i = 0; i < 12; i++) {
  const rr = ex.Game_Runner_DraftChampion(g, i, 0);
  console.log(`draft(${i},0) -> ${rr}${rr ? " [" + err() + "]" : ""}  state ${state()}`);
}
