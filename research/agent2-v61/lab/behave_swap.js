// Which simulated behaviour costs move-ranking agreement? For every labelled 1v1 option with a recorded 2-round
// continuation (micro_lab.js MICRO_TRAJ=1), the simulator starts from the engine's state right after the probe move and
// plays the recorded turns in the engine's order; each turn is either the real recorded actions or the simulator's own
// policy (ts::act). Options are valued like the labels and ranked against the engine label of the same variant.
// usage: node behave_swap.js traj.jsonl [--vis] [--flee 0.5,0.2] [--aggr 1.0,0] [--half 0|1]
process.env.ENGWASM = require("path").join(__dirname, "..", "..", "tools", "viz", "v0_0_3.wasm");
const fs = require("fs");
const path = require("path");
const { WASI } = require("wasi");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));

const args = process.argv.slice(2);
const opt = (k, d) => (args.includes(k) ? args[args.indexOf(k) + 1] : d);
const FLEE = opt("--flee", "0.5,0.2").split(",").map(Number), AGGR = opt("--aggr", "1.0,0").split(",").map(Number);
const VIS = args.includes("--vis"), HALF = +opt("--half", "-1"), TILE = +opt("--tilenet", "0"), MOVE = +opt("--movenet", "0"), MB = opt("--mbias", "0,0").split(",").map(Number); // mbias: away, stay score shifts // movenet: team mask (1 ours, 2 enemy) + 4 = kite

function loadSim() {
  const wasi = new WASI({ version: "preview1", args: [], env: {}, returnOnExit: true });
  const mod = new WebAssembly.Module(fs.readFileSync(path.join(__dirname, process.env.SIMWASM || "simharness2.wasm")));
  const env = {};
  for (const i of WebAssembly.Module.imports(mod)) if (i.module === "env" && i.kind === "function") env[i.name] = () => 0;
  env.__cpp_exception = new WebAssembly.Tag({ parameters: ["i32"] });
  const inst = new WebAssembly.Instance(mod, { env, wasi_snapshot_preview1: wasi.wasiImport });
  wasi.initialize(inst);
  return inst.exports;
}
const S = loadSim();
const KF = 28;
const sio = () => new Float32Array(S.memory.buffer, S.io(), 4 + KF * 8);
const sops = () => new Float32Array(S.memory.buffer, S.ops(), 40);

const E = load(), ex = E.ex;
let curMap = null, W = 0, H = 0;
function mapBoards(mapName) {
  if (curMap === mapName) return;
  curMap = mapName;
  const bytes = fs.readFileSync(path.join(__dirname, "..", "..", "maps_rdev", mapName));
  const p = ex.Engine_Malloc(bytes.length);
  new Uint8Array(ex.memory.buffer, p, bytes.length).set(bytes);
  E.check(ex.Game_FromMapFileBytes(p, bytes.length, E.outBuf, 0), "map");
  const g = E.mem.getBigUint64(E.outBuf, true);
  const meta = E.alloc(64);
  ex.Game_API_Map_GetBitboardMetadata(g, meta);
  W = E.mem.getInt32(meta, true); H = E.mem.getInt32(meta + 4, true);
  const stride = E.mem.getInt32(meta + 16, true);
  const bit = (ptr, x, y) => { const b = ((y & 7) << 3) | (x & 7); return (E.mem.getUint8(ptr + ((y >> 3) * stride + (x >> 3)) * 8 + (b >> 3)) >> (b & 7)) & 1; };
  const buf = (fn) => { fn(g, E.outBuf); return E.mem.getUint32(E.outBuf, true); };
  const wp = buf(ex.Game_GetWallBuffer), hp = buf(ex.Game_GetHoleBuffer), bp = buf(ex.Game_GetBushBuffer), ap = buf(ex.Game_GetAltarBuffer);
  const hs = (W + 7) >> 3;
  const blk = new BigUint64Array(S.memory.buffer, S.board(), 64 * 64), wb = new BigUint64Array(S.memory.buffer, S.walls(), 64 * 64),
    bb = new BigUint64Array(S.memory.buffer, S.bushes(), 64 * 64), lb = new Uint16Array(S.memory.buffer, S.labels(), 512 * 512);
  blk.fill(0n); wb.fill(0n); bb.fill(0n);
  const bush = new Uint8Array(W * H), cl = new Int32Array(W * H).fill(-1);
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const k = (y >> 3) * hs + (x >> 3), m = 1n << BigInt(((y & 7) << 3) | (x & 7));
      if (bit(wp, x, y) || bit(hp, x, y) || bit(ap, x, y)) blk[k] |= m;
      if (bit(wp, x, y)) wb[k] |= m;
      if (bit(bp, x, y)) { bb[k] |= m; bush[y * W + x] = 1; }
    }
  let id = 0;
  for (let i = 0; i < W * H; i++) {
    if (!bush[i] || cl[i] >= 0) continue;
    const st = [i]; cl[i] = id;
    while (st.length) { const c = st.pop(), cx = c % W, cy = (c / W) | 0; for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) { const qx = cx + dx, qy = cy + dy, q = qy * W + qx; if ((dx || dy) && qx >= 0 && qy >= 0 && qx < W && qy < H && bush[q] && cl[q] < 0) { cl[q] = id; st.push(q); } } }
    id++;
  }
  for (let i = 0; i < W * H; i++) if (cl[i] >= 0) lb[i] = cl[i];
  ex.Game_Destroy(g);
  S.set_vis(VIS ? 1 : 0);
}
function spellFields(k, type, focus) {
  if (!k) return [0, 99, 0, 0, 0, 0];
  let flags = 0;
  if (k.attrs & 1) flags |= 1;
  if (k.targets & 2) flags |= 4;
  if (k.targets & 4) flags |= 8;
  if (k.kind === 4 || (k.kind === 3 && type === 0)) flags |= 2;
  if (k.kind === 1 && type === 7) flags |= 16;
  let range = Math.round(k.range || 0);
  if (k.kind === 6 && range <= 0) range = 2;
  return [k.kind, -1, range, Math.round(k.radius || 0), (k.mod || 0) * focus, flags];
}
function fill(units, meTeam) {
  const f = sio();
  f[0] = units.length; f[1] = W; f[2] = H; f[3] = 0;
  units.forEach((u, i) => {
    const o = 4 + KF * i, s0 = spellFields(u.kit && u.kit[0], u.type, u.focus), s1 = spellFields(u.kit && u.kit[1], u.type, u.focus);
    s0[1] = Math.max(0, (u.cd || [0, 0])[0]); s1[1] = Math.max(0, (u.cd || [0, 0])[1]);
    const vals = [u.team === meTeam ? 0 : 1, u.x, u.y, u.alive ? u.hp : 0, u.maxhp, u.str, Math.max(1, u.range), u.alive ? 1 : 0, u.type, u.focus,
      u.shield || 0, u.shield ? 3 : 0, u.stun ? 1 : 0, u.enh ? 1 : 0, 0, ...s0, ...s1, 0];
    for (let k = 0; k < KF; k++) f[o + k] = vals[k];
  });
  new Float32Array(S.memory.buffer, S.camps(), 25)[0] = 0;
}
function opsFromActs(units, acts) {
  const ops = sops(); let n = 0;
  const idx = (h) => units.findIndex((u) => u.h === h);
  for (const a of acts) {
    if (a[a.length - 1] !== 0 || n >= 8) continue;
    const nm = a[0].replace("_with_result", "");
    if (nm === "move_to") ops.set([1, a[1], a[2], 0, 0], 5 * n++);
    else if (nm === "attack" && a[1] === 1) { const t = idx(a[2]); if (t >= 0) ops.set([2, t, 0, 0, 0], 5 * n++); }
    else if (nm === "cast") { const t = a[2] === 1 ? idx(a[3]) : -1; ops.set([3, a[1], t, a[4], a[5]], 5 * n++); }
  }
  return n;
}
const rankCorr = (a, b) => {
  const r = (x) => { const o = x.map((v, i) => [v, i]).sort((p, q) => p[0] - q[0]); const rk = new Array(x.length); o.forEach(([, i], k) => { rk[i] = k; }); return rk; };
  const ra = r(a), rb = r(b), m = (ra.length - 1) / 2;
  let num = 0, da = 0, db = 0;
  for (let i = 0; i < ra.length; i++) { num += (ra[i] - m) * (rb[i] - m); da += (ra[i] - m) ** 2; db += (rb[i] - m) ** 2; }
  return da && db ? num / Math.sqrt(da * db) : NaN;
};

// Play one option's continuation; usePol(turnIndex, unitIndex, isOurs) says whether the simulator's policy plays it.
function playOption(start, o, usePol) {
  const n = start.length, meTeam = start[0].team;
  fill(o.post, meTeam);
  const pp = new Float32Array(S.memory.buffer, S.pol(), 16);
  pp.fill(0); pp[12] = MB[0]; pp[13] = MB[1]; pp[0] = FLEE[0]; pp[1] = FLEE[1]; pp[2] = AGGR[0]; pp[3] = AGGR[1]; pp[8] = TILE; pp[11] = MOVE;
  let round = null;
  o.tr.forEach((t, ti) => {
    const ai = start.findIndex((u) => u.h === t.actor);
    if (ai < 0) return;
    const f = sio();
    if (t.round !== round) { round = t.round; for (let i = 0; i < n; i++) f[4 + KF * i + 27] = 0; }
    if (f[4 + KF * ai + 7] <= 0) return; // dead in the simulator
    pp[5] = t.round;
    if (usePol(ti, ai, start[ai].team === meTeam)) { f[4 + KF * ai + 27] = 0; S.act_unit(ai); }
    else S.apply_ops(ai, opsFromActs(t.pre, t.acts));
  });
  const f = sio();
  return start.reduce((s, u, i) => { const o2 = 4 + KF * i; return s + (u.team === meTeam ? 1 : -1) * (f[o2 + 7] > 0 ? 25 + 12 * f[o2 + 3] / Math.max(1, u.maxhp) : 0); }, 0);
}

// --diag: the enemy's first reply (turn 1), simulator policy vs real: where it stands and what it does.
function diag(rows) {
  const c = {};
  const bump = (k) => { c[k] = (c[k] || 0) + 1; };
  let n = 0;
  for (const r of rows) {
    mapBoards(r.map);
    for (const o of r.options) {
      if (!o.tr || !o.post || !o.tr.length) continue;
      const t = o.tr[0], ai = r.start.findIndex((u) => u.h === t.actor);
      if (ai < 0 || r.start[ai].team === r.start[0].team || !t.post) continue;
      fill(o.post, r.start[0].team);
      const pp = new Float32Array(S.memory.buffer, S.pol(), 12);
      pp.fill(0); pp[0] = FLEE[0]; pp[1] = FLEE[1]; pp[2] = AGGR[0]; pp[3] = AGGR[1]; pp[5] = t.round; pp[8] = TILE; pp[11] = MOVE;
      const f0 = sio(), me0 = { x: f0[4 + 1], y: f0[4 + 2], hp: f0[4 + 3] };
      const ex0 = f0[4 + KF * ai + 1], ey0 = f0[4 + KF * ai + 2], cd0 = [f0[4 + KF * ai + 16], f0[4 + KF * ai + 22]];
      S.act_unit(ai);
      const f = sio(), sx = f[4 + KF * ai + 1], sy = f[4 + KF * ai + 2], sDmg = me0.hp - f[4 + 3];
      const rp = t.post[ai], rDmg = t.pre[0].hp - t.post[0].hp;
      const d = (x, y) => Math.max(Math.abs(x - me0.x), Math.abs(y - me0.y)), d0 = d(ex0, ey0);
      const mv = (x, y) => (x === ex0 && y === ey0 ? "stay" : d(x, y) < d0 ? "closer" : d(x, y) > d0 ? "away" : "side");
      const rc = t.acts.some((a) => a[0].startsWith("cast") && a[a.length - 1] === 0), ra = t.acts.some((a) => a[0] === "attack" && a[a.length - 1] === 0);
      const sc = [16, 22].some((k, i) => f[4 + KF * ai + k] > cd0[i]);
      n++;
      bump(`move real ${mv(rp.x, rp.y)} / sim ${mv(sx, sy)}`);
      bump(`hit us: real ${ra || rDmg > 0.5 ? "yes" : "no"} / sim ${sDmg > 0.5 ? "yes" : "no"}`);
      bump(`spell: real ${rc ? "yes" : "no"} / sim ${sc ? "yes" : "no"}`);
      bump(`damage to us: |real - sim| ${Math.abs(rDmg - sDmg) < 1 ? "<1" : Math.abs(rDmg - sDmg) < 60 ? "1-60" : ">60"}`);
    }
  }
  console.log(`${n} enemy first replies`);
  for (const [k, v] of Object.entries(c).sort()) console.log(`  ${k.padEnd(40)} ${v} (${(100 * v / n).toFixed(1)}%)`);
}

const rows = fs.readFileSync(args[0], "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l)).filter((r) => r.options && r.start.length === 2);
if (args.includes("--diag")) { diag(rows); process.exit(0); }
const conds = {
  "all real (rules check)": () => false,
  "all simulator policy": () => true,
  "our unit policy, enemy real": (ti, ai, ours) => ours,
  "enemy policy, our unit real": (ti, ai, ours) => !ours,
};
for (let k = 0; k < 4; k++) conds[`only turn ${k + 1} by policy`] = (ti) => ti === k;
const res = Object.fromEntries(Object.keys(conds).map((k) => [k, []]));
let used = 0;
rows.forEach((r, ri) => {
  if (HALF >= 0 && ri % 2 !== HALF) return;
  const opts = r.options.filter((o) => o.tr && o.post && o.v0 !== null);
  if (opts.length < 3) return;
  mapBoards(r.map);
  used++;
  const ev = opts.map((o) => o.v0);
  for (const [k, fn] of Object.entries(conds)) res[k].push(rankCorr(opts.map((o) => playOption(r.start, o, fn)), ev));
});
const mean = (a) => { const b = a.filter((x) => !Number.isNaN(x)); return b.reduce((x, y) => x + y, 0) / b.length; };
console.log(`${used} 1v1 positions; rank correlation with the engine's 2-round value (same variant); flee ${FLEE} aggr ${AGGR}${TILE ? " tilenet " + TILE : ""}${MOVE ? " movenet " + MOVE : ""}`);
for (const k of Object.keys(conds)) console.log(`  ${k.padEnd(32)} ${mean(res[k]).toFixed(3)}`);
