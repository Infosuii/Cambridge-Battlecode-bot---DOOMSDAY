// Simulator move ranking against engine labels (micro_lab.js output): each labelled option of the probe turn is
// applied in the bot's simulator (simharness2.wasm, ts:: code), played forward with a chosen policy and horizon, and
// scored like the lab (lives x 25 + health x 12, ours minus theirs). Per scenario: rank correlation with the engine's
// option values, and the engine shortfall of the simulator's top pick (against the bot's own turn).
// usage: node sim_rank.js labels.jsonl [--rounds R] [--policy greedy|learned|static] [--vis] [--max N]
process.env.ENGWASM = require("path").join(__dirname, "..", "..", "tools", "viz", "v0_0_3.wasm");
const fs = require("fs");
const path = require("path");
const { WASI } = require("wasi");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));

const args = process.argv.slice(2);
const file = args[0], MAX = args.includes("--max") ? +args[args.indexOf("--max") + 1] : 100000;
const ROUNDS = args.includes("--rounds") ? +args[args.indexOf("--rounds") + 1] : 2, POLICY = args.includes("--policy") ? args[args.indexOf("--policy") + 1] : "greedy";
const VIS = args.includes("--vis"), DUMP = args.includes("--dump") ? +args[args.indexOf("--dump") + 1] : 0;
const TYPE = ["ryth", "vesper", "vendetta", "cassi", "issac", "stellar", "prism", "marcella", "willow", "ren", "varg", "tavi"];
const KIND = ["none", "reset", "damage", "aoe", "cc", "heal", "dash", "shield"];

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

// Map boards (blocked = walls, holes, altars; vision boards) per map, from the engine.
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

// Spell slot -> harness fields (as the bot's kit_of in tsearch.cpp).
function spellFields(k, type, focus) {
  if (!k) return [0, 99, 0, 0, 0, 0];
  let flags = 0;
  if (k.attrs & 1) flags |= 1;          // SF_EXCL_WALK
  if (k.targets & 2) flags |= 4;        // SF_ENEMY
  if (k.targets & 4) flags |= 8;        // SF_ALLY
  if (k.kind === 4 || (k.kind === 3 && type === 0)) flags |= 2; // SF_STUN (cc; Ryth's area stun)
  if (k.kind === 1 && type === 7) flags |= 16; // SF_ENH (Marcella)
  let range = Math.round(k.range || 0);
  if (k.kind === 6 && range <= 0) range = 2;
  return [k.kind, -1, range, Math.round(k.radius || 0), (k.mod || 0) * focus, flags];
}
const FLEE = (args.includes("--flee") ? args[args.indexOf("--flee") + 1] : "0.35,0.35").split(",").map(Number);
const AGGR = (args.includes("--aggr") ? args[args.indexOf("--aggr") + 1] : "1.4,1.4").split(",").map(Number);
const DIRS = [[-1, -1], [0, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1]];
// Fighters -> simulator (actor first, its team = 0).
function fillMicro(start) {
  const me = start[0];
  const f = sio();
  f[0] = start.length; f[1] = W; f[2] = H; f[3] = 0;
  start.forEach((u, i) => {
    const o = 4 + KF * i, s0 = spellFields(u.kit && u.kit[0], u.type, u.focus), s1 = spellFields(u.kit && u.kit[1], u.type, u.focus);
    s0[1] = Math.max(0, (u.cd || [0, 0])[0]); s1[1] = Math.max(0, (u.cd || [0, 0])[1]);
    const vals = [u.team === me.team ? 0 : 1, u.x, u.y, u.alive ? u.hp : 0, u.maxhp, u.str, Math.max(1, u.range), u.alive ? 1 : 0, u.type, u.focus,
      u.shield || 0, u.shield ? 3 : 0, u.stun ? 1 : 0, u.enh ? 1 : 0, 0, ...s0, ...s1, 0];
    for (let k = 0; k < KF; k++) f[o + k] = vals[k];
  });
  new Float32Array(S.memory.buffer, S.camps(), 25)[0] = 0;
}
const readU = (n) => { const f = sio(); return Array.from({ length: n }, (_, i) => { const o = 4 + KF * i; return { hp: f[o + 3], alive: f[o + 7] > 0 }; }); };
// An option string -> ops for unit 0, in its order.
function opsOf(start, acts) {
  const me = start[0], enemies = [], allies = [];
  start.forEach((u, i) => { if (u.team !== me.team && u.alive) enemies.push(i); else if (i && u.alive) allies.push(i); });
  const ops = sops(); let n = 0, x = me.x, y = me.y;
  for (const a of (acts && acts !== "pass" ? acts.split(" ") : [])) {
    if (n >= 8) break;
    if (a.startsWith("move")) { const d = DIRS[+a.slice(4)]; x += d[0]; y += d[1]; ops.set([1, x, y, 0, 0], 5 * n++); }
    else if (a.startsWith("attack")) { const e = enemies[+a.slice(6)]; if (e !== undefined) ops.set([2, e, 0, 0, 0], 5 * n++); }
    else if (a.startsWith("cast")) {
      const [s, tgt] = a.slice(4).split(":");
      let t = -1, px = x, py = y;
      if (tgt.startsWith("enemy")) { t = enemies[+tgt.slice(5)]; if (t === undefined) continue; px = start[t].x; py = start[t].y; }
      else if (tgt.startsWith("ally")) { t = allies[+tgt.slice(4)]; if (t === undefined) continue; }
      else if (tgt === "self") t = 0;
      else if (tgt.startsWith("ground")) { const e = enemies[+tgt.slice(6)]; if (e === undefined) continue; px = start[e].x; py = start[e].y; }
      ops.set([3, +s, t, px, py], 5 * n++);
    }
  }
  return n;
}
// --models "f0,f1,a0,a1,net;..." : an ensemble of opponent models (flee, engagement factor per team; net = learned
// behaviour for both teams); an option's value is the mean over the models. --featto FILE: per option, the simulated
// outcome under every model (team health shares, alive counts, own state) for an engine-calibrated evaluator.
const MODELS = (args.includes("--models") ? args[args.indexOf("--models") + 1] : `${FLEE[0]},${FLEE[1]},${AGGR[0]},${AGGR[1]},${POLICY === "learned" ? 1 : 0},${POLICY === "tilenet" ? 3 : 0}`)
  .split(";").map((s) => s.split(",").map(Number))
  // --samples K: a model with a tile temperature (7th field) is played K times with seeds 0..K-1 (8th field).
  .flatMap((m) => (m[6] > 0 ? Array.from({ length: args.includes("--samples") ? +args[args.indexOf("--samples") + 1] : 1 }, (_, k) => [...m.slice(0, 7), k]) : [m]));
// --half 0|1: alternate scenarios (train / test split for tuning the settings).
const HALF = args.includes("--half") ? +args[args.indexOf("--half") + 1] : -1;
function simOutcome(start, acts, mdl) {
  fillMicro(start);
  const pp = new Float32Array(S.memory.buffer, S.pol(), 12);
  pp[0] = mdl[0]; pp[1] = mdl[1]; pp[2] = mdl[2]; pp[3] = mdl[3]; pp[5] = 3; pp[6] = mdl[4] || 0; pp[7] = mdl[4] || 0;
  pp[8] = mdl[5] || 0; pp[9] = mdl[6] || 0; pp[10] = mdl[7] || 0; // learned tile model: team mask, temperature, seed
  S.apply_ops(0, opsOf(start, acts));
  // --cut: the last round ends after our own turn, as the labels do (they stop right after the probe unit's turn).
  if (POLICY !== "static") { if (args.includes("--cut")) S.roll_cut(ROUNDS, 1); else S.roll(ROUNDS); }
  const u = readU(start.length), me = start[0];
  let ourHp = 0, theirHp = 0, ourN = 0, theirN = 0;
  start.forEach((v, i) => { const h = u[i].alive ? u[i].hp / Math.max(1, v.maxhp) : 0; if (v.team === me.team) { ourHp += h; ourN += u[i].alive; } else { theirHp += h; theirN += u[i].alive; } });
  return [ourHp, theirHp, ourN, theirN, u[0].alive ? 1 : 0, u[0].alive ? u[0].hp / Math.max(1, me.maxhp) : 0];
}
function simValueEns(start, acts, feats) {
  let v = 0;
  for (const mdl of MODELS) {
    const o = simOutcome(start, acts, mdl);
    if (feats) feats.push(...o);
    v += 25 * (o[2] - o[3]) + 12 * (o[0] - o[1]);
  }
  return v / MODELS.length;
}
function simValue(start, acts) {
  fillMicro(start);
  const pp = new Float32Array(S.memory.buffer, S.pol(), 10);
  pp[5] = 3; pp[6] = POLICY === "learned" ? 1 : 0; pp[7] = POLICY === "learned" ? 1 : 0; pp[8] = POLICY === "tilenet" ? 3 : 0;
  pp[0] = FLEE[0]; pp[1] = FLEE[1]; pp[2] = AGGR[0]; pp[3] = AGGR[1];
  S.apply_ops(0, opsOf(start, acts));
  if (POLICY !== "static") S.roll(ROUNDS);
  const u = readU(start.length);
  const me = start[0];
  return start.reduce((s, v, i) => s + (v.team === me.team ? 1 : -1) * (u[i].alive ? 25 + 12 * u[i].hp / Math.max(1, v.maxhp) : 0), 0);
}
const rankCorr = (a, b) => {
  const r = (x) => { const o = x.map((v, i) => [v, i]).sort((p, q) => p[0] - q[0]); const rk = new Array(x.length); o.forEach(([, i], k) => { rk[i] = k; }); return rk; };
  const ra = r(a), rb = r(b), m = (ra.length - 1) / 2;
  let num = 0, da = 0, db = 0;
  for (let i = 0; i < ra.length; i++) { num += (ra[i] - m) * (rb[i] - m); da += (ra[i] - m) ** 2; db += (rb[i] - m) ** 2; }
  return da && db ? num / Math.sqrt(da * db) : NaN;
};
const rows = fs.readFileSync(file, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l)).filter((r) => r.options).slice(0, MAX);
const corrs = [], shortSim = [], shortOwn = []; let hitSim = 0, hitOwn = 0, n = 0;
const FEATF = args.includes("--featto") ? args[args.indexOf("--featto") + 1] : null;
const featRows = [];
const DUMPF = args.includes("--dumpto") ? args[args.indexOf("--dumpto") + 1] : null;
const dumpRows = [];
let ri = -1;
for (const r of rows) {
  if (!r.start || r.start.length > 8) continue;
  if (HALF >= 0 && (++ri & 1) !== HALF) continue;
  mapBoards(r.map);
  // --rootonly: options the bot's current search can express (spells before the step, attack after the step; a reset only right after an attack).
  const ok = (a) => { const s = a && a !== "pass" ? a.split(" ") : []; const mi = s.findIndex((x) => x.startsWith("move")); return !s.some((x, i) => (x.startsWith("attack") && mi >= 0 && i < mi) || (x.startsWith("cast") && mi >= 0 && i > mi && !(i > 0 && s[i - 1].startsWith("attack")))); };
  const opts = args.includes("--rootonly") ? r.options.filter((o) => ok(o.acts)) : r.options;
  if (opts.length < 2) continue;
  const fts = opts.map(() => []);
  const ev = opts.map((o) => o.v), sv = opts.map((o, i) => simValueEns(r.start, o.acts, FEATF ? fts[i] : null));
  if (FEATF) featRows.push({ start: r.start, acts: opts.map((o) => o.acts), ev, own: r.own.v, best: Math.max(...r.options.map((o) => o.v)), sim: fts });
  const best = Math.max(...r.options.map((o) => o.v)); // best over all engine options (the true best)
  const pick = ev[sv.indexOf(Math.max(...sv))];
  n++;
  const c = rankCorr(sv, ev); if (!Number.isNaN(c)) corrs.push(c);
  shortSim.push(best - pick); shortOwn.push(best - r.own.v);
  if (DUMPF) {
    // The bot's own recorded turn in the option notation (null when it recalled), scored by the simulator too.
    const me = r.start[0], foes = r.start.filter((u) => u.team !== me.team && u.alive), mates = r.start.filter((u, i) => i && u.team === me.team && u.alive);
    let x = me.x, y = me.y, own = [];
    for (const a of r.own.acts) {
      if (a[0] === "recall" || a[0] === "submit_gems") { own = null; break; }
      if (a[0].startsWith("move_to")) { const k = DIRS.findIndex((d) => d[0] === a[1] - x && d[1] === a[2] - y); if (k < 0) { own = null; break; } own.push("move" + k); x = a[1]; y = a[2]; }
      else if (a[0] === "attack") { const e = foes.findIndex((u) => u.h === a[2]); if (e >= 0) own.push("attack" + e); }
      else if (a[0].startsWith("cast")) {
        const e = a[1 + 1] ? foes.findIndex((u) => u.h === a[3]) : -1, m2 = a[2] ? mates.findIndex((u) => u.h === a[3]) : -1;
        const tgt = e >= 0 ? "enemy" + e : m2 >= 0 ? "ally" + m2 : a[2] && a[3] === me.h ? "self" : a[4] >= 0 ? "ground" + Math.max(0, foes.findIndex((u) => u.x === a[4] && u.y === a[5])) : "self";
        own.push(`cast${a[1]}:${tgt}`);
      }
    }
    const ownActs = own && (own.join(" ") || "pass");
    dumpRows.push({ k: r.k, start: r.start, acts: opts.map((o) => o.acts), ev, sv, best, own_acts: ownActs, own_ev: r.own.v, own_sv: own ? simValueEns(r.start, ownActs, null) : null });
  }
  hitSim += best - pick < 0.5; hitOwn += best - r.own.v < 0.5;
}
const mean = (a) => a.reduce((x, y) => x + y, 0) / a.length, med = (a) => [...a].sort((p, q) => p - q)[a.length >> 1];
if (FEATF) fs.writeFileSync(FEATF, featRows.map((x) => JSON.stringify(x)).join("\n") + "\n");
if (DUMPF) fs.writeFileSync(DUMPF, dumpRows.map((x) => JSON.stringify(x)).join("\n") + "\n");
console.log(`${n} scenarios; simulator policy ${POLICY}, ${ROUNDS} rounds after the move${VIS ? ", vision on" : ""}`);
console.log(`  rank correlation with the engine: mean ${mean(corrs).toFixed(3)}, median ${med(corrs).toFixed(3)}  (labels agree with themselves at 0.90)`);
console.log(`  simulator's top pick: within 0.5 of best ${(100 * hitSim / n).toFixed(0)}%, shortfall mean ${mean(shortSim).toFixed(2)} median ${med(shortSim).toFixed(2)}`);
console.log(`  bot's own turn:       within 0.5 of best ${(100 * hitOwn / n).toFixed(0)}%, shortfall mean ${mean(shortOwn).toFixed(2)} median ${med(shortOwn).toFixed(2)}`);