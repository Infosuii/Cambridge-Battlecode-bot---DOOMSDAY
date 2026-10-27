// Engine draft id -> champion, for the lab's forced drafts: draft id i first for team A (team B takes a fixed id), then
// read team A's first champion: engine type, health, strength, focus and ability kinds.
// usage: node draft_probe.js [engine wasm]
const path = require("path");
process.env.ENGWASM = process.argv[2] || path.join(__dirname, "..", "..", "tools", "viz", "v1_0_1.wasm");
const fs = require("fs");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));
const E = load(), ex = E.ex;
const map = fs.readFileSync(path.join(__dirname, "..", "..", "v3", "maps", "00fragment.map26a"));
const buf = E.alloc(4096);
for (let id = 0; id < 14; id++) {
  const p = ex.Engine_Malloc(map.length);
  new Uint8Array(ex.memory.buffer, p, map.length).set(map);
  E.check(ex.Game_FromMapFileBytes(p, map.length, E.outBuf, 0), "map");
  ex.Engine_Free(p);
  const g = E.mem.getBigUint64(E.outBuf, true);
  ex.Game_Runner_Init(g);
  let ok = null, steps = 0;
  for (;;) {
    ex.Game_Runner_Advance(g, buf);
    const st = new Int32Array(E.mem.buffer, buf, 4), phase = st[0], team = st[1];
    if (phase !== 0 || ++steps > 200) break;
    if (team === 2) continue;
    const want = team === 0 ? id : 0;
    let rc = ex.Game_Action_Draft(g, want);
    if (team === 0 && ok === null) ok = rc === 0;
    for (let k = 1; rc !== 0 && k < 14; k++) rc = ex.Game_Action_Draft(g, (want + k) % 14);
    ex.Game_Runner_EndTurn(g, 0);
  }
  const info = buf + 512;
  let out = `draft id ${id}: accepted ${ok}`;
  for (let h = 0; h < 12; h++) {
    if (ex.Game_API_Champion_Get(g, E.persp(2, 0xffffffff), h, info) !== 0) continue;
    if (E.mem.getInt32(info, true) !== 0) continue;
    const kinds = [0, 1].map((s) => (ex.Game_API_Champion_GetAbilityProps(g, E.persp(2, 0xffffffff), h, s, buf + 1024) === 0 ? E.mem.getUint32(buf + 1024, true) : -1));
    out += ` -> handle ${h} type ${E.mem.getInt32(info + 4, true)} hp ${E.mem.getFloat32(info + 20, true)} str ${E.mem.getFloat32(info + 24, true)} focus ${E.mem.getFloat32(info + 28, true)} kinds ${kinds}`;
    break;
  }
  console.log(out);
  ex.Game_Destroy(g);
}
