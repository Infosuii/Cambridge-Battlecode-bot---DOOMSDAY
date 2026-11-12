// Engine lab, offline fight solving: real fight states sampled from bench replays (turn starts of a champion with an
// enemy within 4), each played forward 3 rounds in the real engine twice â€” the acting champion always fighting, then
// always running; everyone else in the fight follows the bot's simulator policy (simharness.wasm, vision on). The
// engine's value difference (fight - run) is the label; the simulator's own prediction from the same state is compared.
// usage: node solve_lab.js out.jsonl perReplay replay1.repl26a [replay2 ...]   (raw inner replay files)
process.env.ENGWASM = require("path").join(__dirname, "..", "..", "tools", "viz", "v0_0_3.wasm");
const fs = require("fs");
const path = require("path");
const { WASI } = require("wasi");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));

const [outFile, perReplayS, ...replays] = process.argv.slice(2);
const PER = parseInt(perReplayS, 10);
const ROUNDS = 3;
let seed = 12345;
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);

function loadSim() {
  const wasi = new WASI({ version: "preview1", args: [], env: {}, returnOnExit: true });
  const mod = new WebAssembly.Module(fs.readFileSync(path.join(__dirname, "simharness.wasm")));
  const env = {};
  for (const i of WebAssembly.Module.imports(mod)) if (i.module === "env" && i.kind === "function") env[i.name] = () => 0;
  env.__cpp_exception = new WebAssembly.Tag({ parameters: ["i32"] });
  const inst = new WebAssembly.Instance(mod, { env, wasi_snapshot_preview1: wasi.wasiImport });
  wasi.initialize(inst);
  return inst.exports;
}
const S = loadSim();
const sio = () => new Float32Array(S.memory.buffer, S.io(), 4 + 80);
const spol = () => new Float32Array(S.memory.buffer, S.pol(), 5);

const E = load();
const ex = E.ex;
const m = () => E.mem;
const info = E.alloc(64), ua = E.alloc(16), abuf = E.alloc(16), gemb = E.alloc(16);
const unit = (ptr, h) => { m().setUint32(ptr, 1, true); m().setUint32(ptr + 4, h, true); m().setUint32(ptr + 8, 0, true); return ptr; };
let g = 0n, tl = 0n, W = 0, H = 0, stride = 0;
const st = () => { ex.Game_Runner_GetState(g, E.args + 400); return [0, 1, 2, 3].map((i) => m().getInt32(E.args + 400 + 4 * i, true)); };
function champ(h) {
  if (ex.Game_API_Champion_Get(g, E.persp(2, 0xffffffff), h, info) !== 0) return null;
  const d = m();
  const alive = ex.Game_API_Champion_IsAlive(g, h, abuf) === 0 && d.getUint8(abuf) !== 0;
  const gems = ex.Game_API_Champion_GetGems(g, E.persp(2, 0xffffffff), h, gemb) === 0 ? d.getUint32(gemb, true) : 0;
  return { h, team: d.getInt32(info, true), type: d.getInt32(info + 4, true), x: d.getInt32(info + 8, true), y: d.getInt32(info + 12, true),
    hp: alive ? d.getFloat32(info + 16, true) : 0, maxhp: d.getFloat32(info + 20, true), str: d.getFloat32(info + 24, true),
    focus: d.getFloat32(info + 28, true), range: Math.max(1, d.getInt32(info + 36, true)), alive, gems };
}
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));

// Map boards for the simulator (walls+holes blocked; walls and bushes for vision) from the engine's buffers.
function mapBoards() {
  const meta = E.alloc(64);
  ex.Game_API_Map_GetBitboardMetadata(g, meta);
  W = m().getInt32(meta, true); H = m().getInt32(meta + 4, true); stride = m().getInt32(meta + 16, true);
  const bitAt = (ptr, x, y) => { const bit = ((y & 7) << 3) | (x & 7); return (m().getUint8(ptr + ((y >> 3) * stride + (x >> 3)) * 8 + (bit >> 3)) >> (bit & 7)) & 1; };
  const get = (fn) => { fn(g, E.outBuf); return m().getUint32(E.outBuf, true); };
  const wp = get(ex.Game_GetWallBuffer), hp = get(ex.Game_GetHoleBuffer), bp = get(ex.Game_GetBushBuffer), ap = get(ex.Game_GetAltarBuffer);
  const hs = (W + 7) >> 3;
  const blk = new BigUint64Array(S.memory.buffer, S.board(), 64 * 64), wb = new BigUint64Array(S.memory.buffer, S.walls(), 64 * 64),
    bb = new BigUint64Array(S.memory.buffer, S.bushes(), 64 * 64), lb = new Uint16Array(S.memory.buffer, S.labels(), 512 * 512);
  blk.fill(0n); wb.fill(0n); bb.fill(0n);
  const bush = new Uint8Array(W * H), cl = new Int32Array(W * H).fill(-1);
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const k = (y >> 3) * hs + (x >> 3), bit = 1n << BigInt(((y & 7) << 3) | (x & 7));
      const wall = bitAt(wp, x, y);
      if (wall || bitAt(hp, x, y) || bitAt(ap, x, y)) blk[k] |= bit;
      if (wall) wb[k] |= bit;
      if (bitAt(bp, x, y)) { bb[k] |= bit; bush[y * W + x] = 1; }
    }
  let id = 0;
  for (let i = 0; i < W * H; i++) {
    if (!bush[i] || cl[i] >= 0) continue;
    const s2 = [i]; cl[i] = id;
    while (s2.length) {
      const c = s2.pop(), cx = c % W, cy = (c / W) | 0;
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        const qx = cx + dx, qy = cy + dy, q = qy * W + qx;
        if ((dx || dy) && qx >= 0 && qy >= 0 && qx < W && qy < H && bush[q] && cl[q] < 0) { cl[q] = id; s2.push(q); }
      }
    }
    id++;
  }
  for (let i = 0; i < W * H; i++) if (cl[i] >= 0) lb[i] = cl[i];
  S.set_vis(1);
  const p = spol(); p[0] = 0.35; p[1] = 0.35; p[2] = 1.4; p[3] = 1.4; p[4] = 0; // the bot's verdict models (tsearch.cpp)
}

// Units -> simulator state; team 0 = the root's team, unit 0 = the root.
function toSim(units, rootTeam, first) {
  const f = sio();
  f[0] = units.length; f[1] = W; f[2] = H; f[3] = first;
  units.forEach((c, i) => {
    const o = 4 + 10 * i;
    f[o] = c.team === rootTeam ? 0 : 1; f[o + 1] = c.x; f[o + 2] = c.y; f[o + 3] = c.alive ? c.hp : 0; f[o + 4] = c.maxhp; f[o + 5] = c.str;
    f[o + 6] = c.range; f[o + 7] = c.alive ? 1 : 0; f[o + 8] = c.type; f[o + 9] = c.focus;
  });
}
const simOut = (n) => { const f = sio(); return Array.from({ length: n }, (_, i) => ({ x: f[5 + 10 * i], y: f[6 + 10 * i], hp: f[7 + 10 * i], alive: f[11 + 10 * i] > 0 })); };
// Value for the root's team: each unit alive 25 + 12 x health fraction (+ carried gems in the engine), ours minus theirs.
function value(units, rootTeam, withGems) {
  let v = 0;
  for (const c of units) {
    const s = c.team === rootTeam ? 1 : -1;
    v += s * ((c.alive ? 25 : 0) + (c.alive ? 12 * c.hp / Math.max(1, c.maxhp) : 0) + (withGems && c.alive ? c.gems / 10 : 0));
  }
  return v;
}

// Play ROUNDS rounds from the current engine state: fight units act by the simulator policy (root under `mode`).
function playEngine(handles, rootTeam, mode) {
  const startRound = st()[2];
  let first = -1;
  for (let step = 0; step < 300; step++) {
    const s = st();
    if (s[0] !== 1 || s[2] >= startRound + ROUNDS) break;
    if (s[1] === 2 || s[3] < 0) { ex.Game_Runner_Advance(g); continue; }
    const idx = handles.indexOf(s[3]);
    const cur = handles.map(champ);
    if (idx < 0 || !cur[idx].alive) { ex.Game_Runner_EndTurn(g, 0); ex.Game_Runner_Advance(g); continue; }
    if (first < 0) first = cur[idx].team === rootTeam ? 0 : 1;
    toSim(cur, rootTeam, first);
    spol()[4] = mode;
    const before = simOut(cur.length);
    S.act_unit(idx);
    const pred = simOut(cur.length);
    let tgt = -1, drop = 0.5;
    pred.forEach((u, j) => { if (j !== idx && before[j].hp - u.hp > drop) { drop = before[j].hp - u.hp; tgt = j; } });
    let rm = -9, ra = -9;
    if (pred[idx].x !== before[idx].x || pred[idx].y !== before[idx].y) rm = ex.Game_Action_Move(g, pred[idx].x, pred[idx].y, E.outBuf);
    if (tgt >= 0) ra = ex.Game_Action_Attack(g, unit(ua, handles[tgt]));
    const re = ex.Game_Runner_EndTurn(g, 0);
    if (process.env.SOLVE_DEBUG) console.error(`mode ${mode} r${s[2]} actor ${idx} move ${rm} atk ${ra} end ${re} ${E.cstr(ex.GetLastErrorMsg())} | ${before[idx].x},${before[idx].y} -> ${pred[idx].x},${pred[idx].y} tgt ${tgt}`);
    ex.Game_Runner_Advance(g);
  }
  return value(handles.map(champ), rootTeam, true);
}

const out = fs.openSync(outFile, "a");
let solved = 0;
for (const rp of replays) {
  try { g = E.loadReplay(rp); } catch (e) { console.error("skip", rp, e.message); continue; }
  ex.Game_Visualiser_Timeline_GetMain(g, E.outBuf); tl = m().getBigUint64(E.outBuf, true);
  ex.Game_Visualiser_Timeline_Info(g, tl, E.args, E.args + 8, E.args + 16);
  const N = m().getUint32(E.args, true);
  mapBoards();
  let got = 0;
  for (let tries = 0; tries < 4000 && got < PER; tries++) {
    const i = 1 + Math.floor(rnd() * (N - 50));
    ex.Game_Visualiser_Timeline_Seek(g, tl, i - 1, 0); const a = st();
    ex.Game_Visualiser_Timeline_Seek(g, tl, i, 0); const b = st();
    if (b[0] !== 1 || b[3] < 0 || (a[2] === b[2] && a[3] === b[3])) continue; // not a turn start
    const all = [];
    for (let h = 0; h < 16; h++) { const c = champ(h); if (c) all.push(c); }
    const root = all.find((c) => c.h === b[3]);
    if (!root || !root.alive) continue;
    const enemies = all.filter((c) => c.alive && c.team !== root.team && cheb(c, root) <= 8);
    if (!enemies.some((c) => cheb(c, root) <= 4)) continue;
    const allies = all.filter((c) => c.alive && c.team === root.team && c.h !== root.h && cheb(c, root) <= 7);
    const units = [root, ...allies, ...enemies].slice(0, 8);
    const handles = units.map((c) => c.h);
    // Simulator prediction (same state, same models, 3 rounds after this one).
    toSim(units, root.team, 0);
    const v0 = value(units, root.team, false);
    const sim = {};
    for (const [name, mode] of [["fight", 1], ["run", 2]]) {
      toSim(units, root.team, 0); spol()[4] = mode; S.roll(ROUNDS - 1);
      const o = simOut(units.length);
      sim[name] = value(units.map((c, j) => ({ ...c, hp: o[j].hp, alive: o[j].alive })), root.team, false);
    }
    // Engine, both plans from the same replay state.
    const eng = {};
    for (const [name, mode] of [["fight", 1], ["run", 2]]) {
      ex.Game_Visualiser_Timeline_Seek(g, tl, i, 0);
      ex.Game_Visualiser_Timeline_Branch(g, tl, i, E.outBuf); // a live copy of the replay state (seeking main restores)
      ex.Game_Runner_Advance(g);
      eng[name] = playEngine(handles, root.team, mode);
    }
    const near = Math.min(...enemies.map((c) => cheb(c, root)));
    const rec = { rp: path.basename(path.dirname(rp)), i, round: b[2], type: root.type, hpf: +(root.hp / root.maxhp).toFixed(3), range: root.range,
      nAllies: allies.length, nEnemies: enemies.length, near, ourHp: allies.reduce((s, c) => s + c.hp, root.hp), theirHp: enemies.reduce((s, c) => s + c.hp, 0),
      gems: root.gems, v0: +v0.toFixed(2), simF: +sim.fight.toFixed(2), simR: +sim.run.toFixed(2), engF: +eng.fight.toFixed(2), engR: +eng.run.toFixed(2) };
    fs.writeSync(out, JSON.stringify(rec) + "\n");
    got++; solved++;
  }
  ex.Game_Destroy(g);
  console.error(path.basename(path.dirname(rp)), "states", got);
}
console.error("solved", solved);
