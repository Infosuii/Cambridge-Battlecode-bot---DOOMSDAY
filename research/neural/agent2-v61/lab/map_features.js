// Per-map features for draft/build rules on unseen maps: size, picks, camp groups and their gems/gold, camp types,
// bush and blocked shares, gem density, room per pick, camp spread. Reads each map through the engine (v0_0_3.wasm).
// usage: node map_features.js MAPDIR out.json
process.env.ENGWASM = process.env.ENGWASM || require("path").join(__dirname, "..", "..", "tools", "viz", "v0_0_3.wasm");
const fs = require("fs");
const path = require("path");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));
const [dirArg, outFile] = process.argv.slice(2);
const dir = path.resolve(dirArg);
const E = load(), ex = E.ex;
const buf = E.alloc(1 << 16);
const u32 = (p) => E.mem.getUint32(p, true), i32 = (p) => E.mem.getInt32(p, true);
const out = {};
for (const f of fs.readdirSync(dir).filter((x) => x.endsWith(".map26a")).sort()) {
  const bytes = fs.readFileSync(path.join(dir, f));
  const p = ex.Engine_Malloc(bytes.length);
  new Uint8Array(ex.memory.buffer, p, bytes.length).set(bytes);
  E.check(ex.Game_FromMapFileBytes(p, bytes.length, E.outBuf, 0), "map");
  ex.Engine_Free(p);
  const g = E.mem.getBigUint64(E.outBuf, true);
  ex.Game_Runner_Init(g); // camp groups exist once the runner is set up
  const meta = E.alloc(64);
  ex.Game_API_Map_GetBitboardMetadata(g, meta);
  const W = i32(meta), H = i32(meta + 4), stride = i32(meta + 16);
  const bb = (fn) => { fn(g, E.outBuf); return u32(E.outBuf); };
  const bit = (ptr, x, y) => { const b = ((y & 7) << 3) | (x & 7); return (E.mem.getUint8(ptr + ((y >> 3) * stride + (x >> 3)) * 8 + (b >> 3)) >> (b & 7)) & 1; };
  const wp = bb(ex.Game_GetWallBuffer), hp = bb(ex.Game_GetHoleBuffer), ap = bb(ex.Game_GetAltarBuffer), bp = bb(ex.Game_GetBushBuffer);
  let blocked = 0, bush = 0;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { if (bit(wp, x, y) || bit(hp, x, y) || bit(ap, x, y)) blocked++; else if (bit(bp, x, y)) bush++; }
  ex.Game_API_Draft_GetNumRounds(g, buf);
  const picks = u32(buf);
  E.mem.setUint32(buf, 0, true);
  const rcG = ex.Game_API_Map_GetNumCampGroups(g, buf);
  const ng = rcG === 0 ? u32(buf) : 0;
  ex.Game_API_Map_GetCampGroups(g, buf, 256, buf + 2048);
  const groups = Array.from({ length: Math.min(ng, 256) }, (_, i) => u32(buf + 4 * i));
  let gems = 0, gold = 0, maxGems = 0;
  const types = {}, centres = [];
  for (const gi of groups) {
    ex.Game_API_Map_CampGroup_Get(g, gi, buf + 4096);
    const ge = u32(buf + 4096), go = u32(buf + 4100);
    gems += ge; gold += go; maxGems = Math.max(maxGems, ge);
    ex.Game_API_Map_CampGroup_GetCampInfo(g, gi, buf + 8192, 64, buf + 8448);
    const nc = u32(buf + 8448);
    let cx = 0, cy = 0;
    for (let c = 0; c < nc; c++) {
      ex.Game_API_Map_CampInfo_Get(g, u32(buf + 8192 + 4 * c), buf + 8500);
      const x = i32(buf + 8500), y = i32(buf + 8504), t = i32(buf + 8508);
      types[t] = (types[t] || 0) + 1; cx += x; cy += y;
    }
    if (nc) centres.push([cx / nc, cy / nc, ge]);
  }
  // Camp spread: mean distance of gem value from the map centre, as a share of the half-diagonal.
  const mx = (W - 1) / 2, my = (H - 1) / 2, half = Math.hypot(mx, my);
  const spread = centres.reduce((s, [x, y, ge]) => s + ge * Math.hypot(x - mx, y - my), 0) / Math.max(1, gems) / half;
  const open = W * H - blocked;
  out[f.replace(".map26a", "")] = { W, H, area: W * H, picks, groups: ng, gems, gold, maxGems, types, blocked: blocked / (W * H), bush: bush / Math.max(1, open),
    density: gems / (W * H), room: W * H / Math.max(1, picks), perGroup: W * H / Math.max(1, ng), maxShare: maxGems / Math.max(1, gems), spread, aspect: Math.max(W, H) / Math.min(W, H) };
  ex.Game_Destroy(g);
}
fs.writeFileSync(outFile, JSON.stringify(out, null, 1));
console.log(`${Object.keys(out).length} maps`);
