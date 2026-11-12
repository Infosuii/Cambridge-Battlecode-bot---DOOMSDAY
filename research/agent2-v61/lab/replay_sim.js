// Replay diagnostic (replay_lab.js trajectories): the engine's recorded actions applied in the simulator, per turn
// from the real state and accumulated from the first turn; divergences classified. Shares the setup of sim_rank.js.
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
const MODELS = (args.includes("--models") ? args[args.indexOf("--models") + 1] : `${FLEE[0]},${FLEE[1]},${AGGR[0]},${AGGR[1]},${POLICY === "learned" ? 1 : 0}`)
  .split(";").map((s) => s.split(",").map(Number));
const TN = ["ryth", "vesper", "vendetta", "cassi", "issac", "stellar", "prism", "marcella", "willow", "ren", "varg", "tavi"];
const KN = ["none", "reset", "damage", "aoe", "cc", "heal", "dash", "shield"];
// Recorded actions of one turn -> ops (absolute tiles; targets by handle).
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
function fillUnits(units, actorH) {
  // Actor's team = 0; the harness keeps the unit order (the actor is found by index).
  const me = units.find((u) => u.h === actorH);
  const f = sio();
  f[0] = units.length; f[1] = W; f[2] = H; f[3] = 0;
  units.forEach((u, i) => {
    const o = 4 + KF * i, s0 = spellFields(u.kit && u.kit[0], u.type, u.focus), s1 = spellFields(u.kit && u.kit[1], u.type, u.focus);
    s0[1] = Math.max(0, (u.cd || [0, 0])[0]); s1[1] = Math.max(0, (u.cd || [0, 0])[1]);
    const vals = [u.team === me.team ? 0 : 1, u.x, u.y, u.alive ? u.hp : 0, u.maxhp, u.str, Math.max(1, u.range), u.alive ? 1 : 0, u.type, u.focus,
      u.shield || 0, u.shield ? 3 : 0, u.stun ? 1 : 0, u.enh ? 1 : 0, 0, ...s0, ...s1, 0];
    for (let k = 0; k < KF; k++) f[o + k] = vals[k];
  });
  new Float32Array(S.memory.buffer, S.camps(), 25)[0] = 0;
}
const readAll = (n) => { const f = sio(); return Array.from({ length: n }, (_, i) => { const o = 4 + KF * i; return { x: f[o + 1], y: f[o + 2], hp: f[o + 3], alive: f[o + 7] > 0, cd: [f[o + 16], f[o + 22]] }; }); };
const rows = fs.readFileSync(file, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l)).slice(0, MAX);
const per = { turns: 0, ok: 0, causes: {} }, acc = { games: 0, finalErr: [], firstDiv: [], causes: {} };
const exs = [];
const note = (bag, k, e) => { bag[k] = (bag[k] || 0) + 1; if (e && exs.length < 40 && !exs.some((x) => x.startsWith(k))) exs.push(k + " | " + e); };
for (const r of rows) {
  mapBoards(r.map);
  const t0 = r.traj[0];
  const n = t0.pre.length;
  // --- per turn, from the real state
  for (const t of r.traj) {
    const ai = t.pre.findIndex((u) => u.h === t.actor);
    if (ai < 0 || !t.post) continue;
    fillUnits(t.pre, t.actor);
    S.apply_ops(ai, opsFromActs(t.pre, t.acts));
    const got = readAll(n);
    per.turns++;
    let bad = false;
    t.post.forEach((p, j) => {
      const g = got[j], pre = t.pre[j];
      if (g.alive !== p.alive) { bad = true; note(per.causes, "death", `${TN[t.pre[ai].type]} acts ${JSON.stringify(t.acts.map((a) => a[0]))} unit ${TN[pre.type]}`); }
      else if (p.alive && Math.abs(g.hp - p.hp) > 1) {
        bad = true;
        const d = p.hp - g.hp, self = j === ai;
        const k = self ? (d > 0 && d <= 6 ? "health: own regen" : "health: own other") : (pre.team === t.pre[ai].team ? "health: ally" : "health: enemy");
        note(per.causes, k, `${TN[t.pre[ai].type]} -> ${TN[pre.type]} sim ${g.hp.toFixed(0)} eng ${p.hp.toFixed(0)} pre ${pre.hp.toFixed(0)} acts ${JSON.stringify(t.acts.map((a) => a.slice(0, -1)))}`);
      } else if (p.alive && (g.x !== p.x || g.y !== p.y)) { bad = true; note(per.causes, "position", `${TN[pre.type]} sim (${g.x},${g.y}) eng (${p.x},${p.y})`); }
      if (j === ai && p.alive) for (let s = 0; s < 2; s++) if (pre.kit && pre.kit[s] && Math.max(0, p.cd[s]) !== Math.max(0, g.cd[s]) && Math.max(0, p.cd[s]) !== Math.max(0, g.cd[s]) + 1) { bad = true; note(per.causes, `cooldown ${KN[pre.kit[s].kind]}`, `${TN[pre.type]} pre ${pre.cd[s]} sim ${g.cd[s]} eng ${p.cd[s]}`); }
    });
    if (!bad) per.ok++;
  }
  // --- accumulated from the first turn
  fillUnits(t0.pre, t0.actor);
  acc.games++;
  let firstDiv = -1;
  r.traj.forEach((t, ti) => {
    const ai = t.pre.findIndex((u) => u.h === t.actor);
    if (ai < 0) return;
    // A unit the engine says is stunned/dead etc. keeps the simulator's own state: only the actions are replayed.
    S.apply_ops(ai, opsFromActs(t.pre, t.acts));
    if (!t.post) return;
    const got = readAll(n);
    const div = t.post.some((p, j) => got[j].alive !== p.alive || (p.alive && Math.abs(got[j].hp - p.hp) > 25));
    if (div && firstDiv < 0) { firstDiv = ti; note(acc.causes, `first big divergence at turn ${Math.min(ti, 12)}`, null); }
  });
  const last = r.traj[r.traj.length - 1];
  if (last.post) {
    const got = readAll(n), me = t0.pre.find((u) => u.h === t0.actor);
    const val = (arr) => arr.reduce((s, u, j) => s + (t0.pre[j].team === me.team ? 1 : -1) * (u.alive ? 25 + 12 * u.hp / Math.max(1, t0.pre[j].maxhp) : 0), 0);
    acc.finalErr.push(Math.abs(val(got) - val(last.post)));
  }
  acc.firstDiv.push(firstDiv);
}
// --- behaviour: the simulator's own choice for each recorded turn (from the real state) against the real action.
const B = { n: 0, tile: 0, atk: 0, cast: 0, all: 0, n2: 0, tile2: 0 };
for (const [ri, r] of rows.entries()) {
  if (args.includes("--heldout") && ri % 5) continue; // behave2_fit.py held out every 5th fight
  mapBoards(r.map);
  for (const t of r.traj) {
    const ai = t.pre.findIndex((u) => u.h === t.actor);
    if (ai < 0 || !t.post || t.pre[ai].stun) continue;
    const ok = t.acts.filter((a) => a[a.length - 1] === 0);
    if (ok.some((a) => ["recall", "submit_gems", "use_consumable_with_result"].includes(a[0]))) continue;
    fillUnits(t.pre, t.actor);
    const pp = new Float32Array(S.memory.buffer, S.pol(), 10);
    pp[0] = FLEE[0]; pp[1] = FLEE[1]; pp[2] = AGGR[0]; pp[3] = AGGR[1]; pp[5] = t.round; pp[6] = POLICY === "learned" ? 1 : 0; pp[7] = pp[6]; pp[8] = POLICY === "tilenet" ? 3 : 0;
    const before = readAll(t.pre.length);
    S.act_unit(ai);
    const g = readAll(t.pre.length);
    // Real: final tile, attack target (handle), cast slot.
    const mv = ok.filter((a) => a[0].startsWith("move_to")).pop();
    const rx = mv ? mv[1] : t.pre[ai].x, ry = mv ? mv[2] : t.pre[ai].y;
    const ra = ok.find((a) => a[0] === "attack" && a[1] === 1), rAtt = ra ? t.pre.findIndex((u) => u.h === ra[2]) : -1;
    const rc = ok.find((a) => a[0].startsWith("cast")), rCast = rc ? rc[1] : -1;
    let pAtt = -1, drop = 0.5;
    g.forEach((u, j) => { if (j !== ai && t.pre[j].team !== t.pre[ai].team && before[j].hp - u.hp > drop) { drop = before[j].hp - u.hp; pAtt = j; } });
    const pCast = [0, 1].find((s) => before[ai].cd[s] === 0 && g[ai].cd[s] > 0) ?? -1;
    B.n++;
    const tileOk = g[ai].x === rx && g[ai].y === ry, atkOk = pAtt === rAtt, castOk = pCast === rCast;
    // The tile model's own sample set: final tile (post) within one step, enemies alive.
    const px = t.post[ai].x, py = t.post[ai].y, me = t.pre[ai];
    if (Math.max(Math.abs(px - me.x), Math.abs(py - me.y)) <= 1 && t.pre.some((u) => u.alive && u.team !== me.team)) { B.n2++; B.tile2 += g[ai].x === px && g[ai].y === py; }
    B.tile += tileOk; B.atk += atkOk; B.cast += castOk; B.all += tileOk && atkOk && castOk;
  }
}
console.log(`BEHAVIOUR (${POLICY}, flee ${FLEE} aggr ${AGGR}) on ${B.n} turns: same tile ${(100 * B.tile / B.n).toFixed(1)}%, same attack target ${(100 * B.atk / B.n).toFixed(1)}%, same spell slot ${(100 * B.cast / B.n).toFixed(1)}%, all three ${(100 * B.all / B.n).toFixed(1)}% | model sample set ${B.n2} turns: same tile ${(100 * B.tile2 / B.n2).toFixed(1)}%`);
const mean = (a) => a.reduce((x, y) => x + y, 0) / Math.max(1, a.length);
console.log(`${rows.length} recorded fights, ${per.turns} turns`);
console.log(`PER TURN (real state in, real actions applied): exact ${(100 * per.ok / per.turns).toFixed(1)}%`);
for (const [k, v] of Object.entries(per.causes).sort((a, b) => b[1] - a[1])) console.log(`   ${k}: ${v}`);
console.log(`ACCUMULATED (from turn 0, real actions only): fights with no big divergence ${acc.firstDiv.filter((x) => x < 0).length}/${acc.games}; mean |value error| at the end ${mean(acc.finalErr).toFixed(2)}`);
for (const [k, v] of Object.entries(acc.causes).sort((a, b) => b[1] - a[1]).slice(0, 8)) console.log(`   ${k}: ${v}`);
for (const e of exs) console.log("  EX " + e);