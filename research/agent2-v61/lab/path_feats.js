// Walking-distance map features (E60 follow-up): the 16 draft features use straight-line (Chebyshev) distances, but
// official maps are mazes. Uses the engine's own distance field (what the SDK's distance_field::compute calls: 8-way
// steps over walls | holes | altars) from each team's spawn region.
// Per map and side: [walk/straight to camp groups (gem-weighted), spawn-to-spawn walk/straight, share of gems
// unreachable on foot, blocked tile share, gem-weighted walk distance to groups / 100, spawn-to-spawn walk / 100].
// usage: node path_feats.js out.json DIR [DIR..]   (keys "<dir basename>/<file>", as mld_feats_v4.json)
const path = require("path");
const fs = require("fs");
process.env.ENGWASM = process.env.ENGWASM || path.join(__dirname, "..", "..", "tools", "viz", "v2_0_0.wasm");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));
const [outFile, ...dirs] = process.argv.slice(2);
const E = load(), ex = E.ex;
const buf = E.alloc(1 << 16), meta = E.alloc(64);
const u32 = (p) => E.mem.getUint32(p, true), i32 = (p) => E.mem.getInt32(p, true);
const UNR = 65535;
const out = {};
for (const dir of dirs) for (const f of fs.readdirSync(dir).filter((x) => x.endsWith(".map26a")).sort()) {
  const bytes = fs.readFileSync(path.join(dir, f));
  const p = ex.Engine_Malloc(bytes.length);
  new Uint8Array(ex.memory.buffer, p, bytes.length).set(bytes);
  E.check(ex.Game_FromMapFileBytes(p, bytes.length, E.outBuf, 0), "map");
  ex.Engine_Free(p);
  const g = E.mem.getBigUint64(E.outBuf, true);
  ex.Game_Runner_Init(g);
  ex.Game_API_Map_GetBitboardMetadata(g, meta);
  const W = i32(meta), H = i32(meta + 4);
  ex.Bitboard_GetRawBufferSize(meta, buf); const R = u32(buf);
  ex.DistanceField_GetRawBufferSize(meta, buf); const D = u32(buf);
  const bb = (fn) => { fn(g, E.outBuf); return u32(E.outBuf); };
  const wp = bb(ex.Game_GetWallBuffer), hp = bb(ex.Game_GetHoleBuffer), ap = bb(ex.Game_GetAltarBuffer);
  const blocked = E.alloc(R), roots = E.alloc(R), vis = E.alloc(R), dist = E.alloc(D), cnt = E.alloc(8), tb = E.alloc(8);
  E.check(ex.Bitboard_Union(meta, wp, hp, blocked), "union");
  E.check(ex.Bitboard_Union(meta, blocked, ap, blocked), "union");
  const isSet = (b, x, y) => (ex.Bitboard_Test(meta, b, x, y, tb), u32(tb) & 1);
  let nb = 0;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) nb += isSet(blocked, x, y);
  // camp groups: centre (mean camp tile) and gems
  E.mem.setUint32(buf, 0, true);
  const ng = ex.Game_API_Map_GetNumCampGroups(g, buf) === 0 ? u32(buf) : 0;
  ex.Game_API_Map_GetCampGroups(g, buf, 256, buf + 2048);
  const groups = [];
  for (const gi of Array.from({ length: Math.min(ng, 256) }, (_, i) => u32(buf + 4 * i))) {
    ex.Game_API_Map_CampGroup_Get(g, gi, buf + 4096);
    const gems = u32(buf + 4096);
    ex.Game_API_Map_CampGroup_GetCampInfo(g, gi, buf + 8192, 64, buf + 8448);
    const nc = u32(buf + 8448), tiles = [];
    for (let c = 0; c < nc; c++) { ex.Game_API_Map_CampInfo_Get(g, u32(buf + 8192 + 4 * c), buf + 8500); tiles.push([i32(buf + 8500), i32(buf + 8504)]); }
    if (nc) groups.push({ gems, tiles, cx: tiles.reduce((a, t) => a + t[0], 0) / nc, cy: tiles.reduce((a, t) => a + t[1], 0) / nc });
  }
  const spawn = [0, 1].map((t) => { ex.Game_API_GetSpawnRegion(g, t, buf); return [i32(buf), i32(buf + 4), i32(buf + 8), i32(buf + 12)]; });
  const sides = [];
  for (const t of [0, 1]) {
    const [x0, y0, x1, y1] = spawn[t];
    ex.Bitboard_Zero(meta, roots);
    for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) ex.Bitboard_Set(meta, roots, x, y, 1);
    E.check(ex.DistanceField_ComputeWithExpansionCount(meta, blocked, roots, vis, dist, UNR, cnt), "df");
    const dget = (x, y) => (ex.DistanceField_Get(meta, dist, x, y, tb) === 0 ? E.mem.getUint16(tb, true) : UNR);
    // straight-line (Chebyshev) distance from the spawn rectangle
    const cheb = (x, y) => Math.max(Math.max(x0 - x, 0, x - (x1 - 1)), Math.max(y0 - y, 0, y - (y1 - 1)));
    // a group's walking distance: its nearest camp tile's free neighbour (camp tiles themselves may be blocked)
    const walkTo = (tiles) => {
      let best = UNR;
      for (const [x, y] of tiles) for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        const X = x + dx, Y = y + dy;
        if (X < 0 || Y < 0 || X >= W || Y >= H) continue;
        const d = dget(X, Y);
        if (d !== UNR) best = Math.min(best, d + (dx || dy ? 1 : 0));
      }
      return best;
    };
    let gw = 0, ratio = 0, walk = 0, unreach = 0, tot = 0;
    for (const G of groups) {
      tot += G.gems;
      const w = walkTo(G.tiles), s = Math.max(1, Math.min(...G.tiles.map(([x, y]) => cheb(x, y))));
      if (w === UNR) { unreach += G.gems; continue; }
      gw += G.gems; ratio += G.gems * Math.min(w / s, 6); walk += G.gems * w;
    }
    const [ex0, ey0, ex1, ey1] = spawn[1 - t];
    const eTiles = [];
    for (let y = ey0; y < ey1; y++) for (let x = ex0; x < ex1; x++) eTiles.push([x, y]);
    const sw = walkTo(eTiles), ss = Math.max(1, Math.min(...eTiles.map(([x, y]) => cheb(x, y))));
    sides.push([gw ? ratio / gw : 1, sw === UNR ? 6 : Math.min(sw / ss, 6), tot ? unreach / tot : 0, nb / (W * H), gw ? walk / gw / 100 : 0, sw === UNR ? 3 : sw / 100].map((v) => +v.toFixed(4)));
  }
  out[path.basename(dir) + "/" + f] = sides;
  ex.Game_Destroy(g);
  for (const q of [blocked, roots, vis, dist, cnt, tb]) ex.Engine_Free(q);
}
fs.writeFileSync(outFile, JSON.stringify(out));
console.log(`${Object.keys(out).length} maps`);
