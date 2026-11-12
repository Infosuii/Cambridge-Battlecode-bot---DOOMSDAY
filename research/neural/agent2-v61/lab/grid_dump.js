// Terrain around each labelled fight (micro_lab.js output) for the spatial move model (spatial_fit.py): a 9x9 window
// centred on the probe champion, 1 = wall/hole/altar (blocked), 2 = bush, 0 = open; out-of-map counts as blocked.
// usage: node grid_dump.js micro.jsonl grids.jsonl
process.env.ENGWASM = require("path").join(__dirname, "..", "..", "tools", "viz", "v0_0_3.wasm");
const fs = require("fs");
const path = require("path");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));
const [inFile, outFile] = process.argv.slice(2);
const E = load(), ex = E.ex;
const cache = new Map();
function terrain(map) {
  if (cache.has(map)) return cache.get(map);
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
  const ptrs = [buf(ex.Game_GetWallBuffer), buf(ex.Game_GetHoleBuffer), buf(ex.Game_GetAltarBuffer)], bp = buf(ex.Game_GetBushBuffer);
  const bit = (ptr, x, y) => { const b = ((y & 7) << 3) | (x & 7); return (E.mem.getUint8(ptr + ((y >> 3) * stride + (x >> 3)) * 8 + (b >> 3)) >> (b & 7)) & 1; };
  const t = new Uint8Array(W * H);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) t[y * W + x] = ptrs.some((q) => bit(q, x, y)) ? 1 : bit(bp, x, y) ? 2 : 0;
  ex.Game_Destroy(g);
  const out = { W, H, t };
  cache.set(map, out);
  return out;
}
const lines = fs.readFileSync(inFile, "utf8").split("\n").filter(Boolean);
const out = [];
for (const l of lines) {
  const r = JSON.parse(l);
  if (!r.options || !r.start) continue;
  const { W, H, t } = terrain(r.map);
  const me = r.start[0], grid = [];
  for (let dy = -4; dy <= 4; dy++) for (let dx = -4; dx <= 4; dx++) {
    const x = me.x + dx, y = me.y + dy;
    grid.push(x < 0 || y < 0 || x >= W || y >= H ? 1 : t[y * W + x]);
  }
  out.push(JSON.stringify({ k: r.k, map: r.map, x: me.x, y: me.y, grid }));
}
fs.writeFileSync(outFile, out.join("\n") + "\n");
console.log(`${out.length} grids written`);
