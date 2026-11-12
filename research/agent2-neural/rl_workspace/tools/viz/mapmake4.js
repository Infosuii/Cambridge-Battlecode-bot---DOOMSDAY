// Build random maps with the engine 2.0.0 MapBuilder (cambc 3.0.2 rules: golems) and save as .map26a.
// mapmake4.js = mapmake3.js on engine 2.0.0 (cambc 4.0.0); REAL=1 and CLEAN=1 as there.
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
const seed = parseInt(seedS || "20261016", 10);
fs.mkdirSync(outdir, { recursive: true });
let done = 0, tries = 0;
while (done < +count && tries < +count * 6) {
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
    const wallD = 0.05 + rng() * 0.07, bushD = 0.03 + rng() * 0.05;
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
    fs.writeFileSync(path.join(outdir, `new_${seed + tries}.map26a`), bytes);
    done++;
  } catch (e) {
    console.error(`try ${tries} failed: ${e.message}`);
  }
}
console.log(`built ${done}/${count} maps in ${tries} tries`);
