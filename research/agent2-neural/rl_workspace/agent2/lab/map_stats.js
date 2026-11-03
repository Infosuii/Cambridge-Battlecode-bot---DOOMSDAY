// Map suite statistics (engine 2.0.0): how pool-like is a map set? Per map: width, height, aspect, wall / hole / bush
// shares (of all tiles), bush clusters, altars, camp groups, total gems, symmetry, and the maze ratio (gem-weighted
// walking / straight-line distance from our spawn, as mapmake5.js measures it). Prints per-suite quantiles.
// usage: node map_stats.js DIR [DIR..] [--json out.json]
const fs = require("fs");
const path = require("path");
process.env.ENGWASM = process.env.ENGWASM || path.join(__dirname, "..", "..", "tools", "viz", "v2_0_0.wasm");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));
const args = process.argv.slice(2);
const jsonOut = args.includes("--json") ? args[args.indexOf("--json") + 1] : null;
const dirs = args.filter((a, i) => !a.startsWith("--") && args[i - 1] !== "--json");
const E = load(), ex = E.ex;
const buf = E.alloc(1 << 16);
const u32 = (p) => E.mem.getUint32(p, true), i32 = (p) => E.mem.getInt32(p, true);
const all = {};
for (const dir of dirs) {
  const rows = [];
  for (const f of fs.readdirSync(dir).filter((x) => x.endsWith(".map26a")).sort()) {
    const bytes = fs.readFileSync(path.join(dir, f));
    const p = ex.Engine_Malloc(bytes.length);
    new Uint8Array(ex.memory.buffer, p, bytes.length).set(bytes);
    if (ex.Game_FromMapFileBytes(p, bytes.length, E.outBuf, 0) !== 0) { ex.Engine_Free(p); continue; }
    ex.Engine_Free(p);
    const g = E.mem.getBigUint64(E.outBuf, true);
    ex.Game_Runner_Init(g);
    const meta = E.alloc(64);
    ex.Game_API_Map_GetBitboardMetadata(g, meta);
    const W = i32(meta), H = i32(meta + 4), stride = i32(meta + 16);
    const bb = (fn) => { fn(g, E.outBuf); return u32(E.outBuf); };
    const bit = (ptr, x, y) => { const b = ((y & 7) << 3) | (x & 7); return (E.mem.getUint8(ptr + ((y >> 3) * stride + (x >> 3)) * 8 + (b >> 3)) >> (b & 7)) & 1; };
    const wp = bb(ex.Game_GetWallBuffer), hp = bb(ex.Game_GetHoleBuffer), ap = bb(ex.Game_GetAltarBuffer), bp = bb(ex.Game_GetBushBuffer);
    let walls = 0, holes = 0, bush = 0, altars = 0;
    const isB = new Uint8Array(W * H), blocked = new Uint8Array(W * H);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const w = bit(wp, x, y), h = bit(hp, x, y), a = bit(ap, x, y), b = bit(bp, x, y);
      walls += w; holes += h; altars += a;
      if (w || h || a) blocked[y * W + x] = 1; else if (b) { bush++; isB[y * W + x] = 1; }
    }
    // bush clusters (8-connected)
    let clusters = 0;
    const seen = new Uint8Array(W * H);
    for (let i = 0; i < W * H; i++) {
      if (!isB[i] || seen[i]) continue;
      clusters++;
      const st = [i]; seen[i] = 1;
      while (st.length) {
        const c = st.pop(), cx = c % W, cy = (c / W) | 0;
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
          const nx = cx + dx, ny = cy + dy;
          if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
          const n = ny * W + nx;
          if (isB[n] && !seen[n]) { seen[n] = 1; st.push(n); }
        }
      }
    }
    ex.Game_API_Map_GetNumCampGroups(g, buf);
    const ng = u32(buf);
    ex.Game_API_Map_GetCampGroups(g, buf + 8, ng, buf + 4);
    let gems = 0;
    const cents = [];
    for (let k = 0; k < ng; k++) {
      const gid = u32(buf + 8 + 4 * k);
      ex.Game_API_Map_CampGroup_Get(g, gid, buf + 4000);
      const ge = u32(buf + 4000);
      gems += ge;
      ex.Game_API_Map_CampGroup_GetNumCamps(g, gid, buf + 4100);
      const nc = u32(buf + 4100);
      ex.Game_API_Map_CampGroup_GetCampInfo(g, gid, buf + 4200, nc, buf + 4104);
      let cx = 0, cy = 0;
      for (let c = 0; c < nc; c++) { ex.Game_API_Map_CampInfo_Get(g, u32(buf + 4200 + 4 * c), buf + 5000); cx += i32(buf + 5000); cy += i32(buf + 5004); }
      cents.push([Math.round(cx / Math.max(1, nc)), Math.round(cy / Math.max(1, nc)), ge]);
    }
    ex.Game_API_GetSpawnRegion(g, 0, buf);
    const sx = Math.floor((i32(buf) + i32(buf + 8) - 1) / 2), sy = Math.floor((i32(buf + 4) + i32(buf + 12) - 1) / 2);
    // BFS walking distance from our spawn centre (8-connected, blocked tiles impassable; camp tiles passable here)
    const dist = new Int32Array(W * H).fill(-1);
    const q = [sy * W + sx]; dist[sy * W + sx] = 0;
    for (let qi = 0; qi < q.length; qi++) {
      const c = q[qi], cx = c % W, cy = (c / W) | 0;
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        const nx = cx + dx, ny = cy + dy;
        if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
        const n = ny * W + nx;
        if (blocked[n] || dist[n] >= 0) continue;
        dist[n] = dist[c] + 1; q.push(n);
      }
    }
    let wsum = 0, ssum = 0;
    for (const [cx, cy, ge] of cents) {
      let best = -1;
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        const nx = cx + dx, ny = cy + dy;
        if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
        const d = dist[ny * W + nx];
        if (d >= 0 && (best < 0 || d < best)) best = d;
      }
      const s = Math.max(Math.abs(cx - sx), Math.abs(cy - sy));
      if (best > 0 && s > 0) { wsum += ge * best; ssum += ge * s; }
    }
    ex.Game_API_Map_GetSymmetry(g, buf);
    const sym = i32(buf);
    const n = W * H;
    rows.push({ map: f, W, H, aspect: Math.max(W, H) / Math.min(W, H), walls: walls / n, holes: holes / n, bush: bush / n,
      clusters, altars, groups: ng, gems, sym, maze: ssum ? wsum / ssum : 0 });
    ex.Game_Destroy(g);
  }
  all[path.basename(dir)] = rows;
  const keys = ["W", "H", "aspect", "walls", "holes", "bush", "clusters", "altars", "groups", "gems", "maze"];
  const qs = (v) => { const s = [...v].sort((a, b) => a - b); return [0.1, 0.5, 0.9].map((p) => s[Math.min(s.length - 1, Math.floor(p * s.length))]); };
  const fmt = (x) => (Math.abs(x) < 1 ? x.toFixed(3) : x.toFixed(x < 10 ? 2 : 0));
  console.log(`${path.basename(dir)} (${rows.length} maps): ` + keys.map((k) => `${k} ${qs(rows.map((r) => r[k])).map(fmt).join("/")}`).join(", ") +
    `, symmetry ${JSON.stringify(rows.reduce((a, r) => ((a[r.sym] = (a[r.sym] || 0) + 1), a), {}))}`);
}
if (jsonOut) fs.writeFileSync(jsonOut, JSON.stringify(all));
