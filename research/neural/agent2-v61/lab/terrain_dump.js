// Whole-map terrain for the behaviour model (behave2_fit.py): per map in the trajectories, W, H and a row-major array
// (0 open, 1 blocked: wall / hole / altar, 2 bush).
// usage: node terrain_dump.js traj.jsonl terrain.json
process.env.ENGWASM = require("path").join(__dirname, "..", "..", "tools", "viz", "v0_0_3.wasm");
const fs = require("fs");
const path = require("path");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));
const [inFile, outFile] = process.argv.slice(2);
const E = load(), ex = E.ex;
const maps = new Set(fs.readFileSync(inFile, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l).map));
const out = {};
for (const map of maps) {
  const bytes = fs.readFileSync(path.join(__dirname, "..", "..", "maps_rdev", map));
  const p = ex.Engine_Malloc(bytes.length);
  new Uint8Array(ex.memory.buffer, p, bytes.length).set(bytes);
  E.check(ex.Game_FromMapFileBytes(p, bytes.length, E.outBuf, 0), "map");
  ex.Engine_Free(p);
  const g = E.mem.getBigUint64(E.outBuf, true);
  const meta = E.alloc(64);
  ex.Game_API_Map_GetBitboardMetadata(g, meta);
  const W = E.mem.getInt32(meta, true), H = E.mem.getInt32(meta + 4, true), stride = E.mem.getInt32(meta + 16, true);
  const buf = (fn) => { fn(g, E.outBuf); return E.mem.getUint32(E.outBuf, true); };
  const blk = [buf(ex.Game_GetWallBuffer), buf(ex.Game_GetHoleBuffer), buf(ex.Game_GetAltarBuffer)], bp = buf(ex.Game_GetBushBuffer);
  const bit = (ptr, x, y) => { const b = ((y & 7) << 3) | (x & 7); return (E.mem.getUint8(ptr + ((y >> 3) * stride + (x >> 3)) * 8 + (b >> 3)) >> (b & 7)) & 1; };
  const t = [];
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) t.push(blk.some((q) => bit(q, x, y)) ? 1 : bit(bp, x, y) ? 2 : 0);
  out[map] = { W, H, t };
  ex.Game_Destroy(g);
}
fs.writeFileSync(outFile, JSON.stringify(out));
console.log(`${Object.keys(out).length} maps`);
