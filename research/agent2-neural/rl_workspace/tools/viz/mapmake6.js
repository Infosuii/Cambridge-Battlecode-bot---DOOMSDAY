// Pool-calibrated random maps (engine 2.0.0 MapBuilder), from mapmake5.js. Every property is drawn from the 70 official
// pool maps (agent2/lab/map_stats.js on v4/maps): size and aspect from a random pool map +-10%, symmetry at pool
// frequencies (rotational 63%), wall share as structures (bars / blocks), hole share (none on ~35% of maps, lakes and
// bands on the rest), bushes as a few large patches (pool: 2-16 clusters, 1-11% of tiles), pool altar counts, camp
// groups as mapmake5 REAL=1 on free tiles (bushes never under camps). Keeps a map only if the game loader accepts it,
// both spawns connect and the gem-weighted walk / straight-line ratio falls in the pool's buckets at the pool's shares.
// usage: node mapmake6.js OUTDIR COUNT SEED
const fs = require("fs");
const path = require("path");
const { WASI } = require("wasi");
const wasi = new WASI({ version: "preview1", args: [], env: {}, returnOnExit: true });
const mod = new WebAssembly.Module(fs.readFileSync(path.join(__dirname, "v2_0_0.wasm")));
const inst = new WebAssembly.Instance(mod, {
  wasi_snapshot_preview1: wasi.wasiImport,
  deep_wasm: { on_assert_fail_impl: (m, f, l, s) => { console.error(`assert: ${read(m)}:${read(l)}`); return 1; } },
});
function read(p) { const u = new Uint8Array(inst.exports.memory.buffer); let s = ""; while (u[p]) s += String.fromCharCode(u[p++]); return s; }
const ex = inst.exports;
wasi.initialize(inst);
const outBuf = ex.Engine_Malloc(64);
const E = {
  mem: () => new DataView(ex.memory.buffer),
  alloc: (n) => ex.Engine_Malloc(n),
  err: () => read(ex.GetLastErrorMsg()),
  check(code, what) { if (code !== 0) throw new Error(`${what}: ${code}: ${E.err()}`); },
};
function makeMap(w, h, symmetry, champs) {
  E.check(ex.MapBuilder_Create(w, h, symmetry, outBuf), "Create");
  const b = E.mem().getBigUint64(outBuf, true);
  E.check(ex.MapBuilder_SetNumChampsPerTeam(b, champs), "Champs");
  return b;
}
function box(b, x0, y0, x1, y1) {
  E.mem().setInt32(outBuf, x0, true); E.mem().setInt32(outBuf + 4, y0, true);
  E.mem().setInt32(outBuf + 8, x1, true); E.mem().setInt32(outBuf + 12, y1, true);
}
const KIND = { WOLF: 0, ELK: 1, GEM_CLUSTER: 2, GOLD_CLUSTER: 3, MONOLITH: 4, GOLEM: 5 };
const SYM = { HORIZONTAL: 0, VERTICAL: 1, ROTATIONAL180: 2 };
const [outdir, count, seedS] = process.argv.slice(2);

// Gem-weighted walk / straight-line distance from team A's spawn to the camp groups (destroys the game); NaN if the
// spawns do not connect or over 35% of the gems cannot be reached on foot. (mapmake5.js)
function mazeRatio(g) {
  const m = () => E.mem(), u32 = (p) => m().getUint32(p, true), i32 = (p) => m().getInt32(p, true);
  const buf = E.alloc(1 << 16), meta = E.alloc(64), tb = E.alloc(8);
  ex.Game_Runner_Init(g);
  ex.Game_API_Map_GetBitboardMetadata(g, meta);
  const W = i32(meta), H = i32(meta + 4);
  ex.Bitboard_GetRawBufferSize(meta, buf); const R = u32(buf);
  ex.DistanceField_GetRawBufferSize(meta, buf); const D = u32(buf);
  const bb = (fn) => { fn(g, outBuf); return u32(outBuf); };
  const blocked = E.alloc(R), roots = E.alloc(R), vis = E.alloc(R), dist = E.alloc(D), cnt = E.alloc(8);
  ex.Bitboard_Union(meta, bb(ex.Game_GetWallBuffer), bb(ex.Game_GetHoleBuffer), blocked);
  ex.Bitboard_Union(meta, blocked, bb(ex.Game_GetAltarBuffer), blocked);
  const spawn = [0, 1].map((t) => { ex.Game_API_GetSpawnRegion(g, t, buf); return [i32(buf), i32(buf + 4), i32(buf + 8), i32(buf + 12)]; });
  const [x0, y0, x1, y1] = spawn[0];
  ex.Bitboard_Zero(meta, roots);
  for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) ex.Bitboard_Set(meta, roots, x, y, 1);
  ex.DistanceField_ComputeWithExpansionCount(meta, blocked, roots, vis, dist, 65535, cnt);
  const dget = (x, y) => (x < 0 || y < 0 || x >= W || y >= H ? 65535 : ex.DistanceField_Get(meta, dist, x, y, tb) === 0 ? m().getUint16(tb, true) : 65535);
  const cheb = (x, y) => Math.max(Math.max(x0 - x, 0, x - (x1 - 1)), Math.max(y0 - y, 0, y - (y1 - 1)));
  const walkTo = (tiles) => { let best = 65535; for (const [x, y] of tiles) for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const d = dget(x + dx, y + dy); if (d !== 65535) best = Math.min(best, d + (dx || dy ? 1 : 0)); } return best; };
  const [a0, b0, a1, b1] = spawn[1], et = [];
  for (let y = b0; y < b1; y++) for (let x = a0; x < a1; x++) et.push([x, y]);
  let res = walkTo(et) === 65535 ? NaN : 0;
  if (res === 0) {
    m().setUint32(buf, 0, true);
    const ng = ex.Game_API_Map_GetNumCampGroups(g, buf) === 0 ? u32(buf) : 0;
    ex.Game_API_Map_GetCampGroups(g, buf, 256, buf + 2048);
    let tot = 0, gw = 0, rs = 0;
    for (let i = 0; i < Math.min(ng, 256); i++) {
      const gi = u32(buf + 4 * i);
      ex.Game_API_Map_CampGroup_Get(g, gi, buf + 4096);
      const gems = Math.max(1, u32(buf + 4096));
      ex.Game_API_Map_CampGroup_GetCampInfo(g, gi, buf + 8192, 64, buf + 8448);
      const tiles = [];
      for (let c = 0; c < u32(buf + 8448); c++) { ex.Game_API_Map_CampInfo_Get(g, u32(buf + 8192 + 4 * c), buf + 8500); tiles.push([i32(buf + 8500), i32(buf + 8504)]); }
      if (!tiles.length) continue;
      tot += gems;
      const w = walkTo(tiles), s = Math.max(1, Math.min(...tiles.map(([x, y]) => cheb(x, y))));
      if (w !== 65535) { gw += gems; rs += gems * Math.min(w / s, 6); }
    }
    res = gw && gw >= 0.65 * tot ? rs / gw : NaN;
  }
  ex.Game_Destroy(g);
  for (const q of [buf, meta, tb, blocked, roots, vis, dist, cnt]) ex.Engine_Free(q);
  return res;
}

// pool distributions (agent2/lab/map_stats.json, v4/maps)
const POOL_WH = [[29, 29], [29, 29], [30, 30], [30, 30], [30, 30], [30, 30], [30, 30], [30, 30], [30, 30], [30, 80], [31, 31], [31, 31],
  [31, 31], [31, 31], [31, 31], [33, 33], [35, 29], [35, 31], [35, 35], [37, 31], [40, 30], [40, 40], [40, 40], [40, 40], [40, 40],
  [41, 30], [41, 41], [41, 41], [41, 61], [45, 30], [45, 35], [45, 45], [45, 45], [45, 45], [50, 40], [50, 40], [50, 40], [50, 41],
  [50, 46], [50, 50], [50, 50], [50, 50], [50, 50], [50, 50], [50, 65], [51, 31], [51, 40], [51, 51], [51, 51], [51, 51], [51, 85],
  [60, 50], [60, 60], [60, 60], [61, 61], [61, 61], [61, 71], [71, 71], [79, 79], [80, 80], [80, 80], [89, 71], [90, 30], [91, 75],
  [93, 93], [99, 99], [100, 80], [100, 100], [100, 100], [100, 100]];
const POOL_WALLS = [0, 0, 0, 0, 0, 0, 0.011, 0.019, 0.035, 0.05, 0.058, 0.069, 0.086, 0.1, 0.116, 0.15, 0.18];
const POOL_HOLES = [0, 0, 0, 0, 0, 0, 0.003, 0.004, 0.01, 0.019, 0.036, 0.044, 0.085, 0.125, 0.215, 0.3];
const POOL_ALTARS = [1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 3, 4, 4, 4, 5, 6, 6, 10];
const pickOf = (rng, a) => a[Math.floor(rng() * a.length)];

if (process.env.MEASURE) {
  // MEASURE=DIR: print this generator's walk / straight-line ratio for every map in DIR (to set BUCKETS)
  const vals = [];
  for (const f of fs.readdirSync(process.env.MEASURE).filter((x) => x.endsWith(".map26a"))) {
    const bytes = fs.readFileSync(path.join(process.env.MEASURE, f));
    const qp = ex.Engine_Malloc(bytes.length);
    new Uint8Array(ex.memory.buffer, qp, bytes.length).set(bytes);
    if (ex.Game_FromMapFileBytes(qp, bytes.length, outBuf, 0) === 0) vals.push(mazeRatio(E.mem().getBigUint64(outBuf, true)));
    ex.Engine_Free(qp);
  }
  console.log(JSON.stringify(vals.map((v) => +v.toFixed(3)).sort((a, b) => a - b)));
  process.exit(0);
}
const seed = parseInt(seedS || "20261103", 10);
fs.mkdirSync(outdir, { recursive: true });
const ratios = [];
// walk / straight-line buckets with the pool's shares (1.0..5.4, median 1.2 on this metric): each map is built for one bucket
const BUCKETS = [[0, 1.03, 18], [1.03, 1.2, 13], [1.2, 1.5, 14], [1.5, 2.2, 11], [2.2, 9, 12]]; // pool, this metric (MEASURE=v4/maps)
const quota = BUCKETS.map(([, , n]) => Math.round((n / 68) * +count)), filled = BUCKETS.map(() => 0);
let done = 0, tries = 0;
while (done < +count && tries < +count * 60) {
  tries++;
  const rng = ((s) => () => { s = (s * 1103515245 + 12345) >>> 0; return s / 2 ** 32; })(seed + tries * 977);
  const bk = filled.findIndex((f, i) => f < quota[i]);
  if (bk < 0) break;
  try {
    const [pw, ph] = pickOf(rng, POOL_WH);
    const jf = 0.9 + 0.2 * rng(), jit = (v) => Math.max(26, Math.min(100, Math.round(v * jf))); // one factor: squares stay square
    const sr = rng(), sym = sr < 0.63 ? SYM.ROTATIONAL180 : sr < 0.86 ? SYM.HORIZONTAL : SYM.VERTICAL;
    const b = makeMap(jit(pw), pw === ph ? jit(pw) : jit(ph), sym, 3 + Math.floor(rng() * 3));
    box(b, 1, 1, 5, 5); // spawn rect the play loader accepts
    E.check(ex.MapBuilder_SetTeamASpawnArea(b, outBuf), "SpawnArea");
    const meta = E.alloc(32);
    E.check(ex.MapBuilder_GetBitboardMetadata(b, meta), "Meta");
    const W = E.mem().getInt32(meta, true), H = E.mem().getInt32(meta + 4, true), clear = E.mem().getInt32(meta + 8, true);
    const inCorner = (x, y) => (x < clear + 1 || x > W - 2 - clear) && (y < clear + 1 || y > H - 2 - clear);
    const get = (fn, x, y) => { fn(b, x, y, outBuf); return E.mem().getUint8(outBuf); };
    const tileFree = (x, y) => !get(ex.MapBuilder_GetWall, x, y) && !get(ex.MapBuilder_GetHole, x, y) && !get(ex.MapBuilder_GetAltar, x, y);
    let nWall = 0, nHole = 0;
    const put = (x, y, kind) => {
      if (x < 0 || y < 0 || x >= W || y >= H || inCorner(x, y) || !tileFree(x, y)) return;
      if (kind === 2) { E.check(ex.MapBuilder_AddHole(b, x, y), "hole"); nHole++; } else { E.check(ex.MapBuilder_AddWall(b, x, y), "wall"); nWall++; }
    };
    const segment = (x0, y0, x1, y1, t, kind, doors) => {
      const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0));
      const gaps = Array.from({ length: doors }, () => [Math.floor(rng() * n), 2 + Math.floor(rng() * 3)]);
      for (let i = 0; i <= n; i++) {
        if (gaps.some(([s, gw]) => i >= s && i < s + gw)) continue;
        const x = Math.round(x0 + ((x1 - x0) * i) / Math.max(1, n)), y = Math.round(y0 + ((y1 - y0) * i) / Math.max(1, n));
        for (let a = 0; a < t; a++) for (let c = 0; c < t; c++) put(x + a, y + c, kind);
      }
    };
    const blob = (kind, r) => {
      const cx = Math.floor(rng() * W), cy = Math.floor(rng() * H);
      for (let y = cy - r; y <= cy + r; y++) for (let x = cx - r; x <= cx + r; x++)
        if ((x - cx) ** 2 + (y - cy) ** 2 <= r * r * (0.6 + 0.4 * rng())) put(x, y, kind);
    };
    // the builder mirrors every tile: targets are per half
    const area = W * H;
    const wallT = (pickOf(rng, POOL_WALLS) * (bk === 1 || bk === 2 ? 1 + 0.5 * bk : 1) * area) / 2;
    const holeT = (pickOf(rng, POOL_HOLES) * area) / 2;
    if (bk >= 3) {
      // cuts: long thick barriers across the map (mostly holes) with one or two gaps - the pool's detour maps
      const nb = (bk === 4 ? 3 : 2) + Math.floor(rng() * 3), diag = rng() < 0.5;
      for (let k = 0; k < nb; k++) {
        const t = 2 + Math.floor(rng() * 2), kind = rng() < 0.7 ? 2 : 1, doors = rng() < 0.75 ? 1 : 2;
        if (diag) { const o = Math.floor((rng() - 0.5) * W * 1.4); segment(o, 0, o + H, H - 1, t, kind, doors); }
        else if (rng() < 0.5) { const x = 5 + Math.floor(rng() * (W - 10)); segment(x, 0, x, H - 1, t, kind, doors); }
        else { const y = 5 + Math.floor(rng() * (H - 10)); segment(0, y, W - 1, y, t, kind, doors); }
      }
    }
    for (let guard = 0; nHole < holeT && guard < 200; guard++) {
      if (rng() < 0.6) blob(2, 2 + Math.floor(rng() * Math.max(2, Math.sqrt(holeT) / 2)));
      else {
        const t = 1 + Math.floor(rng() * 3);
        if (rng() < 0.5) { const x = 4 + Math.floor(rng() * (W - 8)); segment(x, Math.floor((rng() * H) / 3), x, H - 1 - Math.floor((rng() * H) / 3), t, 2, 1); }
        else { const y = 4 + Math.floor(rng() * (H - 8)); segment(Math.floor((rng() * W) / 3), y, W - 1 - Math.floor((rng() * W) / 3), y, t, 2, 1); }
      }
    }
    // rooms on some walled maps (pool maps are mazes: walk / straight 1.17 median)
    if (wallT > 0 && rng() < (bk === 1 || bk === 2 ? 0.6 : 0.25)) {
      const cw = 8 + Math.floor(rng() * 10), ch = 8 + Math.floor(rng() * 10);
      for (let x = cw; x < W - 2 && nWall < wallT; x += cw) for (let y = 0; y < H; y += ch) if (rng() < 0.7) segment(x, y, x, Math.min(H - 1, y + ch), 1, 1, 1);
      for (let y = ch; y < H - 2 && nWall < wallT; y += ch) for (let x = 0; x < W; x += cw) if (rng() < 0.7) segment(x, y, Math.min(W - 1, x + cw), y, 1, 1, 1);
    }
    for (let guard = 0; nWall < wallT && guard < 400; guard++) {
      const s = rng(), len = 6 + Math.floor(rng() * Math.max(4, Math.min(W, H) * 0.7));
      const x = Math.floor(rng() * W), y = Math.floor(rng() * H), t = rng() < 0.3 ? 2 : 1;
      if (s < 0.45) segment(x, y, Math.min(W - 1, x + len), y, t, 1, rng() < 0.5 ? 1 : 0);
      else if (s < 0.9) segment(x, y, x, Math.min(H - 1, y + len), t, 1, rng() < 0.5 ? 1 : 0);
      else blob(1, 1 + Math.floor(rng() * 3));
    }
    // camp groups (mapmake5 REAL=1 rules) on free tiles
    const kinds = [KIND.WOLF, KIND.ELK, KIND.GEM_CLUSTER, KIND.GOLD_CLUSTER, KIND.MONOLITH, KIND.GOLEM];
    const weights = [1, 1.2, 1.6, 1.2, 0.4, 0.8];
    const pick = () => { let r = rng() * weights.reduce((a, c) => a + c), i = 0; for (; i < weights.length - 1; i++) { if (r < weights[i]) break; r -= weights[i]; } return kinds[i]; };
    const ngroups = 5 + Math.floor(rng() * rng() * 14) + Math.floor(area / 1200);
    const campCells = [], taken = [];
    const DANGER = new Set([KIND.WOLF, KIND.ELK, KIND.MONOLITH, KIND.GOLEM]);
    const mirrors = (x, y) => [[x, y], [W - 1 - x, y], [x, H - 1 - y], [W - 1 - x, H - 1 - y]];
    const near = (ax, ay, bx, by, d) => Math.max(Math.abs(ax - bx), Math.abs(ay - by)) <= d;
    let placed = 0;
    for (let gtry = 0; placed < ngroups && gtry < ngroups * 10; gtry++) {
      const cx = Math.floor(rng() * W), cy = Math.floor(rng() * H);
      const kind = pick(), dangerous = DANGER.has(kind);
      const n = kind === KIND.MONOLITH ? 1 : kind === KIND.GOLEM ? 1 + Math.floor(rng() * 2) : 1 + Math.floor(rng() * 4);
      const cells = [[cx, cy, kind]];
      const grow = (k) => {
        for (let t = 0; t < 20; t++) {
          const [bx, by] = cells[Math.floor(rng() * cells.length)];
          const [dx, dy] = [[1, 0], [-1, 0], [0, 1], [0, -1]][Math.floor(rng() * 4)];
          const x = bx + dx, y = by + dy;
          if (x < 0 || y < 0 || x >= W || y >= H || cells.some(([px, py]) => px === x && py === y)) continue;
          cells.push([x, y, k]);
          return;
        }
      };
      while (cells.length < n) { const before = cells.length; grow(kind); if (cells.length === before) break; }
      if (dangerous && rng() < 0.5) { const extra = 1 + Math.floor(rng() * 2), side = rng() < 0.6 ? KIND.GEM_CLUSTER : KIND.GOLD_CLUSTER; for (let i = 0; i < extra; i++) grow(side); }
      let ok = true;
      for (const [x, y] of cells) {
        if (x < 0 || y < 0 || x >= W || y >= H || !tileFree(x, y) || inCorner(x, y)) { ok = false; break; }
        for (const [mx, my] of mirrors(x, y).slice(1)) if (!(mx === x && my === y) && cells.some(([px, py]) => near(px, py, mx, my, 3))) ok = false;
        for (const [tx, ty, td] of taken) if ((dangerous || td) && near(tx, ty, x, y, 3)) ok = false;
      }
      if (!ok) continue;
      for (const [x, y, k] of cells) {
        E.check(ex.MapBuilder_AddCamp(b, k, x, y, outBuf), "AddCamp");
        campCells.push([x, y]);
        for (const [mx, my] of mirrors(x, y)) taken.push([mx, my, dangerous]);
      }
      placed++;
    }
    const campAt = new Set();
    for (const [cx, cy] of campCells) for (const [mx, my] of mirrors(cx, cy)) campAt.add(my * W + mx);
    // bushes: a few large connected patches, never under camps
    const nClusters = 1 + Math.floor(rng() * 8), bushT = ((0.015 + rng() * rng() * 0.12) * area) / 2;
    let nBush = 0;
    for (let c = 0; c < nClusters && nBush < bushT; c++) {
      let x = Math.floor(rng() * W), y = Math.floor(rng() * H);
      const size = Math.max(3, Math.round((bushT / nClusters) * (0.5 + rng())));
      for (let s = 0, guard = 0; s < size && guard < size * 6; guard++) {
        if (!inCorner(x, y) && tileFree(x, y) && !campAt.has(y * W + x) && !get(ex.MapBuilder_GetBush, x, y)) {
          E.check(ex.MapBuilder_AddBush(b, x, y), "bush");
          s++; nBush++;
        }
        const [dx, dy] = [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [-1, -1]][Math.floor(rng() * 6)];
        x = Math.max(0, Math.min(W - 1, x + dx)); y = Math.max(0, Math.min(H - 1, y + dy));
      }
    }
    const altT = pickOf(rng, POOL_ALTARS);
    for (let i = 0, guard = 0; i < Math.ceil(altT / 2) && guard < 100; guard++) {
      const x = Math.floor(rng() * W), y = Math.floor(rng() * H);
      if (inCorner(x, y) || !tileFree(x, y) || campAt.has(y * W + x)) continue;
      E.check(ex.MapBuilder_AddAltar(b, x, y), "AddAltar");
      i++;
    }
    E.check(ex.MapBuilder_VerifyIntegrity(b), "VerifyIntegrity");
    E.check(ex.MapBuilder_Encode(b, outBuf, outBuf + 4), "Encode");
    const ptr = E.mem().getUint32(outBuf, true), len = E.mem().getUint32(outBuf + 4, true);
    const bytes = new Uint8Array(ex.memory.buffer, ptr, len).slice();
    const qp = ex.Engine_Malloc(bytes.length);
    new Uint8Array(ex.memory.buffer, qp, bytes.length).set(bytes);
    const q = ex.Game_FromMapFileBytes(qp, bytes.length, outBuf, 0);
    ex.Engine_Free(qp);
    if (q !== 0) throw new Error(`game loader rejected: ${q}`);
    const r = mazeRatio(E.mem().getBigUint64(outBuf, true));
    if (!(r >= BUCKETS[bk][0] && r < BUCKETS[bk][1])) throw new Error(`maze ratio ${r} not in bucket ${bk}`);
    ratios.push(r);
    filled[bk]++;
    fs.writeFileSync(path.join(outdir, `pool_${seed + tries}.map26a`), bytes);
    done++;
  } catch (e) {
    if (process.env.VERBOSE) console.error(`try ${tries} failed: ${e.message}`);
  }
}
console.log(`built ${done}/${count} maps in ${tries} tries, buckets ${filled.join("/")} of ${quota.join("/")}` + (ratios.length ? `; walk/straight ratio mean ${(ratios.reduce((a, r) => a + r, 0) / ratios.length).toFixed(2)}` : ""));
