// Build random maps with the engine 2.0.0 MapBuilder (cambc 3.0.2 rules: golems) and save as .map26a.
// mapmake5.js = mapmake4.js + MAZE=1: official maps are mazes (walk / straight-line distance 1.3-2.8, E60) while
// mapmake4 maps are open (1.00). MAZE=1 adds walled rooms with doors (ambush-like), long barrier bands with a few gaps
// (cuts-like) and hole lakes (islands-like), places camps only on free tiles, and keeps a map only if both spawns
// connect and the gem-weighted walk / straight ratio lies in MAZE_MIN..MAZE_MAX (default 1.15..3.2), measured with
// the engine's distance field (what the SDK's distance_field::compute calls).
// usage: node mapmake.js OUTDIR COUNT SEED [BASEMAP]
// CLEAN=1 in the environment: no camp stands on a bush tile (like every official map).
// With BASEMAP: copies the map and randomises terrain/camps on top (same dims).
// Without: builds a map from scratch.
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
  alloc: n => ex.Engine_Malloc(n),
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
const KIND = { NONE: -1, WOLF: 0, ELK: 1, GEM_CLUSTER: 2, GOLD_CLUSTER: 3, MONOLITH: 4, GOLEM: 5 };
const SYM = { HORIZONTAL: 0, VERTICAL: 1, ROTATIONAL180: 2 };

const [outdir, count, seedS, baseS] = process.argv.slice(2);
const ratios = [];
// Gem-weighted walk / straight-line distance from team A's spawn to the camp groups of a loaded game (destroys it);
// NaN if the spawns do not connect or over 35% of the gems cannot be reached on foot.
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
const seed = parseInt(seedS || "20261016", 10);
fs.mkdirSync(outdir, { recursive: true });
let done = 0, tries = 0;
while (done < +count && tries < +count * (process.env.MAZE === "1" ? 20 : 6)) {
  tries++;
  const rng = (s => () => { s = (s * 1103515245 + 12345) >>> 0; return s / 2 ** 32; })(seed + tries * 977);
  try {
    let b;
    if (baseS) {
      const bytes = fs.readFileSync(baseS);
      const p = ex.Engine_Malloc(bytes.length);
      new Uint8Array(ex.memory.buffer, p, bytes.length).set(bytes);
      E.check(ex.MapBuilder_FromFileBytes(p, bytes.length, outBuf), "FromFile");
      ex.Engine_Free(p);
      b = E.mem().getBigUint64(outBuf, true);
      // Remove every existing camp, then rebuild new random ones (terrain and altars stay).
      for (;;) {
        E.check(ex.MapBuilder_GetNumCamps(b, outBuf), "NumCamps");
        const total = E.mem().getUint32(outBuf, true);
        if (total === 0) break;
        E.check(ex.MapBuilder_GetCampHandle(b, total - 1, outBuf), "CampHandle");
        E.check(ex.MapBuilder_RemoveCamp(b, E.mem().getBigUint64(outBuf, true)), "RemoveCamp");
      }
    } else {
      const w = 30 + Math.floor(rng() * 12) * 10, h = 30 + Math.floor(rng() * 12) * 10;
      const sym = Math.floor(rng() * 3);
      const champs = 3 + Math.floor(rng() * 3);
      b = makeMap(w, h, sym, champs);
    }
    box(b, 1, 1, 5, 5); // spawn rect the play loader accepts (4..5 spans fail smaller/bigger)
    E.check(ex.MapBuilder_SetTeamASpawnArea(b, outBuf), "SpawnArea2");
    // Terrain: sprinkle walls (density 5-12%) and bushes (3-8%).
    const meta = E.alloc(32);
    E.check(ex.MapBuilder_GetBitboardMetadata(b, meta), "Meta");
    const W = E.mem().getInt32(meta, true), H = E.mem().getInt32(meta + 4, true);
    const clear = E.mem().getInt32(meta + 8, true);
    if (W < 20 || W > 110 || H < 20 || H > 110) throw new Error("bad dims");
    const MAZE = process.env.MAZE === "1";
    const inCorner = (x, y) => (x < clear || x > W - 1 - clear) && (y < clear || y > H - 1 - clear);
    if (MAZE) {
      // Structure on the whole map (the builder mirrors every tile itself). kind: 1 wall, 2 hole.
      const put = (x, y, kind) => {
        if (x < 0 || y < 0 || x >= W || y >= H || inCorner(x, y)) return;
        E.check(kind === 2 ? ex.MapBuilder_AddHole(b, x, y) : ex.MapBuilder_AddWall(b, x, y), "maze");
      };
      // A straight or diagonal segment with door gaps; thickness t.
      const segment = (x0, y0, x1, y1, t, kind, doors) => {
        const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0));
        const gaps = Array.from({ length: doors }, () => [Math.floor(rng() * n), 2 + Math.floor(rng() * 3)]);
        for (let i = 0; i <= n; i++) {
          if (gaps.some(([s, w]) => i >= s && i < s + w)) continue;
          const x = Math.round(x0 + ((x1 - x0) * i) / Math.max(1, n)), y = Math.round(y0 + ((y1 - y0) * i) / Math.max(1, n));
          for (let a = 0; a < t; a++) for (let c = 0; c < t; c++) put(x + a, y + c, kind);
        }
      };
      const style = rng();
      if (style < 0.45) {
        // rooms: cell boundaries become walls with 1-2 doors each, some boundaries dropped
        const cw = 8 + Math.floor(rng() * 8), ch = 8 + Math.floor(rng() * 8);
        const holeWalls = rng() < 0.3;
        for (let x = cw; x < W - 2; x += cw) for (let y = 0; y < H; y += ch)
          if (rng() < 0.85) segment(x, y, x, Math.min(H - 1, y + ch), 1, holeWalls && rng() < 0.3 ? 2 : 1, 1);
        for (let y = ch; y < H - 2; y += ch) for (let x = 0; x < W; x += cw)
          if (rng() < 0.85) segment(x, y, Math.min(W - 1, x + cw), y, 1, holeWalls && rng() < 0.3 ? 2 : 1, 1);
      } else if (style < 0.8) {
        // bands: long thick barriers (mostly holes) across the map with few gaps
        const nb = 3 + Math.floor(rng() * 4), diag = rng() < 0.6;
        for (let k = 0; k < nb; k++) {
          const t = 2 + Math.floor(rng() * 2), kind = rng() < 0.75 ? 2 : 1, doors = rng() < 0.7 ? 1 : 2;
          if (diag) { const o = Math.floor((rng() - 0.5) * W * 1.4); segment(o, 0, o + H, H - 1, t, kind, doors); }
          else if (rng() < 0.5) { const x = 6 + Math.floor(rng() * (W - 12)); segment(x, 0, x, H - 1, t, kind, doors); }
          else { const y = 6 + Math.floor(rng() * (H - 12)); segment(0, y, W - 1, y, t, kind, doors); }
        }
      }
      // lakes: hole blobs (any style; more on the open-ish third)
      const nl = (style >= 0.8 ? 2 : 0) + Math.floor(rng() * 3);
      for (let k = 0; k < nl; k++) {
        const cx = Math.floor(rng() * W), cy = Math.floor(rng() * H), r = 3 + Math.floor(rng() * 7);
        for (let y = cy - r; y <= cy + r; y++) for (let x = cx - r; x <= cx + r; x++)
          if ((x - cx) ** 2 + (y - cy) ** 2 <= r * r * (0.7 + 0.3 * rng())) put(x, y, 2);
      }
    }
    const wallD = MAZE ? 0.01 + rng() * 0.03 : 0.05 + rng() * 0.07, bushD = 0.03 + rng() * 0.05;
    const tileFree = (x, y) => {
      for (const fn of [ex.MapBuilder_GetWall, ex.MapBuilder_GetHole, ex.MapBuilder_GetAltar]) { fn(b, x, y, outBuf); if (E.mem().getUint8(outBuf)) return false; }
      return true;
    };
    const cells = [];
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) cells.push([x, y]);
    const chosen = cells.filter(() => rng() < wallD + bushD);
    for (const [x, y] of chosen) {
      const corner = (x < clear || x > W - 1 - clear) && (y < clear || y > H - 1 - clear); // all corners: spawn + mirror
      if (corner) continue;
      if (rng() < wallD / (wallD + bushD)) E.check(ex.MapBuilder_AddWall(b, x, y), "AddWall");
      else E.check(ex.MapBuilder_AddBush(b, x, y), "AddBush");
    }
    // Camps: 8-22 groups; each group = 2-8 camps of one kind near a centre.
    const kinds = [KIND.WOLF, KIND.ELK, KIND.GEM_CLUSTER, KIND.GOLD_CLUSTER, KIND.MONOLITH, KIND.GOLEM];
    const weights = [1, 1.2, 1.6, 1.2, 0.4, 0.8];
    const pick = () => { let r = rng() * weights.reduce((a, c) => a + c), i = 0; for (; i < weights.length - 1; i++) { if (r < weights[i]) break; r -= weights[i]; } return kinds[i]; };
    const ngroups = 8 + Math.floor(rng() * 14);
    const campCells = [];
    // REAL=1: groups look like the official ones: one cardinally connected blob per group (dangerous
    // kinds sometimes carry gem/gold clusters), and dangerous groups at least 4 tiles from every other
    // group, mirrors included (no official map has two dangerous groups touching).
    if (process.env.REAL === "1") {
      const DANGER = new Set([KIND.WOLF, KIND.ELK, KIND.MONOLITH, KIND.GOLEM]);
      const taken = []; // [x, y, dangerous] of placed camps and their mirror tiles
      const mirrors = (x, y) => [[x, y], [W - 1 - x, y], [x, H - 1 - y], [W - 1 - x, H - 1 - y]];
      const near = (ax, ay, bx, by, d) => Math.max(Math.abs(ax - bx), Math.abs(ay - by)) <= d;
      for (let g = 0; g < ngroups; g++) {
        const cx = Math.floor(rng() * W), cy = Math.floor(rng() * H);
        const kind = pick();
        const dangerous = DANGER.has(kind);
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
        if (dangerous && rng() < 0.5) {
          const extra = 1 + Math.floor(rng() * 2), side = rng() < 0.6 ? KIND.GEM_CLUSTER : KIND.GOLD_CLUSTER;
          for (let i = 0; i < extra; i++) grow(side);
        }
        let ok = true;
        for (const [x, y] of cells) {
          if (MAZE && !tileFree(x, y)) ok = false;
          if ((x < clear || x > W - 1 - clear) && (y < clear || y > H - 1 - clear)) ok = false;
          for (const [mx, my] of mirrors(x, y).slice(1))
            if (!(mx === x && my === y) && cells.some(([px, py]) => near(px, py, mx, my, 3))) ok = false; // straddles an axis
          for (const [tx, ty, td] of taken) if ((dangerous || td) && near(tx, ty, x, y, 3)) ok = false;
        }
        if (!ok) continue;
        for (const [x, y, k] of cells) {
          E.check(ex.MapBuilder_AddCamp(b, k, x, y, outBuf), "AddCamp");
          campCells.push([x, y]);
          for (const [mx, my] of mirrors(x, y)) taken.push([mx, my, dangerous]);
        }
      }
    }
    for (let g = 0; g < (process.env.REAL === "1" ? 0 : ngroups); g++) {
      const cx = Math.floor(rng() * W), cy = Math.floor(rng() * H);
      if ((cx < clear || cx > W - 1 - clear) && (cy < clear || cy > H - 1 - clear)) continue;
      const kind = pick();
      const n = 1 + Math.floor(rng() * 5);
      for (let i = 0; i < n; i++) {
        const x = Math.min(W - 1, Math.max(0, cx + Math.floor(rng() * 5) - 2));
        const y = Math.min(H - 1, Math.max(0, cy + Math.floor(rng() * 5) - 2));
        E.check(ex.MapBuilder_AddCamp(b, kind, x, y, outBuf), "AddCamp");
        campCells.push([x, y]);
      }
    }
    // CLEAN=1: official maps never put a camp on a bush tile; clear the bush (and its mirror) under each camp.
    if (process.env.CLEAN === "1") {
      for (const [x, y] of campCells) {
        const mirrors = [[x, y], [W - 1 - x, y], [x, H - 1 - y], [W - 1 - x, H - 1 - y]];
        for (const [mx, my] of mirrors) ex.MapBuilder_RemoveBush(b, mx, my);
      }
    }
    // Altars: 3-6 per map.
    const nAlt = 3 + Math.floor(rng() * 4);
    for (let i = 0; i < nAlt; i++) {
      const x = Math.floor(rng() * W), y = Math.floor(rng() * H);
      if ((x < clear || x > W - 1 - clear) && (y < clear || y > H - 1 - clear)) continue;
      if (MAZE && !tileFree(x, y)) continue;
      E.check(ex.MapBuilder_AddAltar(b, x, y), "AddAltar");
    }
    E.check(ex.MapBuilder_VerifyIntegrity(b), "VerifyIntegrity");
    E.check(ex.MapBuilder_Encode(b, outBuf, outBuf + 4), "Encode");
    const ptr = E.mem().getUint32(outBuf, true), len = E.mem().getUint32(outBuf + 4, true);
    const bytes = new Uint8Array(ex.memory.buffer, ptr, len).slice();
    // Only keep maps the GAME loader accepts (stricter than VerifyIntegrity).
    const qp = ex.Engine_Malloc(bytes.length);
    new Uint8Array(ex.memory.buffer, qp, bytes.length).set(bytes);
    const q = ex.Game_FromMapFileBytes(qp, bytes.length, outBuf, 0);
    ex.Engine_Free(qp);
    if (q !== 0) throw new Error(`game loader rejected: ${q}`);
    if (MAZE) {
      const r = mazeRatio(E.mem().getBigUint64(outBuf, true));
      if (!(r >= +(process.env.MAZE_MIN || 1.15) && r <= +(process.env.MAZE_MAX || 3.2))) throw new Error(`maze ratio ${r.toFixed(2)} out of range`);
      ratios.push(r);
    }
    fs.writeFileSync(path.join(outdir, `new_${seed + tries}.map26a`), bytes);
    done++;
  } catch (e) {
    console.error(`try ${tries} failed: ${e.message}`);
  }
}
console.log(`built ${done}/${count} maps in ${tries} tries` + (ratios.length ? `; walk/straight ratio mean ${(ratios.reduce((a, r) => a + r, 0) / ratios.length).toFixed(2)}, min ${Math.min(...ratios).toFixed(2)}, max ${Math.max(...ratios).toFixed(2)}` : ""));
