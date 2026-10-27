// Engine lab: exact fight testing. Sets up small fights in the real engine (v0_0_3 module), lets the bot's simulator
// (simharness.wasm, the ts:: code from tsearch.h) choose each fighting champion's turn, plays that turn in the engine
// and compares the engine's resulting state with the simulator's prediction. Also compares whole-fight outcomes.
// usage: node fight_lab.js map.map26 [fights=50] [seed=1]
process.env.ENGWASM = require("path").join(__dirname, "..", "..", "tools", "viz", "v0_0_3.wasm");
const fs = require("fs");
const path = require("path");
const { WASI } = require("wasi");
const { load } = require(path.join(__dirname, "..", "..", "tools", "viz", "eng.js"));

const mapFile = process.argv[2];
const FIGHTS = parseInt(process.argv[3] || "50", 10);
let seed = parseInt(process.argv[4] || "1", 10);
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);
const ri = (a, b) => a + Math.floor(rnd() * (b - a + 1));

// Simulator.
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

const E = load();
const ex = E.ex;
const m = () => E.mem;
const err = () => E.cstr(ex.GetLastErrorMsg());
const mapBytes = fs.readFileSync(mapFile);
const info = E.alloc(64), ua = E.alloc(16), ub = E.alloc(16), pos = E.alloc(16), wout = E.alloc(16);
const unit = (ptr, h) => { m().setUint32(ptr, 1, true); m().setUint32(ptr + 4, h, true); m().setUint32(ptr + 8, 0, true); return ptr; };

function champ(g, h) {
  if (ex.Game_API_Champion_Get(g, E.persp(2, 0xffffffff), h, info) !== 0) return null;
  const d = m();
  return { h, team: d.getInt32(info, true), type: d.getInt32(info + 4, true), x: d.getInt32(info + 8, true), y: d.getInt32(info + 12, true),
    hp: d.getFloat32(info + 16, true), maxhp: d.getFloat32(info + 20, true), str: d.getFloat32(info + 24, true), focus: d.getFloat32(info + 28, true), range: d.getInt32(info + 36, true) };
}
const abuf = E.alloc(16);
const alive = (g, h) => ex.Game_API_Champion_IsAlive(g, h, abuf) === 0 && m().getUint8(abuf) !== 0;

function newGame() {
  const p = ex.Engine_Malloc(mapBytes.length);
  new Uint8Array(ex.memory.buffer, p, mapBytes.length).set(mapBytes);
  E.check(ex.Game_FromMapFileBytes(p, mapBytes.length, E.outBuf, 0), "FromMap");
  ex.Engine_Free(p);
  const g = m().getBigUint64(E.outBuf, true);
  ex.Game_Runner_Init(g);
  for (let k = 0; k < 40 && st(g)[0] === 0; k++) {
    ex.Game_Runner_Advance(g);
    if (st(g)[0] !== 0) break;
    const start = ri(0, 11);
    for (let c = 0; c < 12; c++) if (ex.Game_Action_Draft(g, (start + c) % 12) === 0) break;
    ex.Game_Runner_EndTurn(g, 0);
  }
  ex.Game_Runner_Advance(g);
  return g;
}
function st(g) { ex.Game_Runner_GetState(g, E.args); return [0, 1, 2, 3].map((i) => m().getInt32(E.args + 4 * i, true)); }

let W = 0, H = 0, wall = null;
function readWalls(g) {
  // Map size from the walls query: probe until GetWall fails.
  if (wall) return;
  for (W = 1; W < 128 && ex.Game_GetWall(g, W, 0, wout) === 0; W++);
  for (H = 1; H < 128 && ex.Game_GetWall(g, 0, H, wout) === 0; H++);
  wall = [];
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { ex.Game_GetWall(g, x, y, wout); wall.push(m().getUint8(wout) !== 0); }
  wallOnly = wall.slice();
  { const mt = E.alloc(64); ex.Game_API_Map_GetBitboardMetadata(g, mt); bbStride = m().getInt32(mt + 16, true); }
  // Holes, altars and spawn tiles: wherever a sandbox teleport of champion 0 is refused (it is put back afterwards).
  const c0 = champ(g, 0);
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      if (wall[y * W + x] || (x === c0.x && y === c0.y)) continue;
      m().setInt32(pos, x, true); m().setInt32(pos + 4, y, true);
      if (ex.Game_Sandbox_Teleport(g, unit(ua, 0), pos) !== 0) wall[y * W + x] = true;
    }
  m().setInt32(pos, c0.x, true); m().setInt32(pos + 4, c0.y, true);
  ex.Game_Sandbox_Teleport(g, unit(ua, 0), pos);
  // Occupied spawn-row neighbours were refused too; they are far from the fights, so this is harmless.
  console.error("blocked tiles", wall.filter(Boolean).length);
}

// Fill the simulator board (walls; every other champion's tile is left free: they are far away).
function fillBoard() {
  const b = new BigUint64Array(S.memory.buffer, S.board(), 64 * 64);
  b.fill(0n);
  const stride = (W + 7) >> 3;
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++)
      if (wall[y * W + x]) b[(y >> 3) * stride + (x >> 3)] |= 1n << BigInt(((y & 7) << 3) | (x & 7));
}

function toSim(g, units, first) {
  const f = sio();
  f[0] = units.length; f[1] = W; f[2] = H; f[3] = first;
  units.forEach((h, i) => {
    const c = champ(g, h), a = alive(g, h);
    const o = 4 + 10 * i;
    f[o] = c.team; f[o + 1] = c.x; f[o + 2] = c.y; f[o + 3] = a ? c.hp : 0; f[o + 4] = c.maxhp; f[o + 5] = c.str;
    f[o + 6] = Math.max(1, c.range); f[o + 7] = a ? 1 : 0; f[o + 8] = c.type; f[o + 9] = c.focus;
  });
}
const simUnits = (n) => { const f = sio(); return Array.from({ length: n }, (_, i) => ({ x: f[5 + 10 * i], y: f[6 + 10 * i], hp: f[7 + 10 * i], alive: f[11 + 10 * i] > 0 })); };
const engUnits = (g, units) => units.map((h) => { const c = champ(g, h); const a = alive(g, h); return { x: c.x, y: c.y, hp: a ? c.hp : 0, alive: a }; });

let bushSet = null;
// Bush tiles from the wall-style query on the bush bitboard is unknown; use Game_GetBushBuffer's linear byte buffer if
// it returns a pointer, else report "?".
function bushOf(c) {
  if (bushSet === null) {
    // Chunked 8x8 bitboard (the bot's layout), stride = ceil(W / 8) words per chunk row.
    ex.Game_GetBushBuffer(gCur, E.outBuf);
    const ptr = m().getUint32(E.outBuf, true), stride = bbStride;
    bushSet = new Uint8Array(W * H);
    for (let y = 0; y < H; y++)
      for (let x = 0; x < W; x++) {
        const bit = ((y & 7) << 3) | (x & 7);
        bushSet[y * W + x] = (m().getUint8(ptr + ((y >> 3) * stride + (x >> 3)) * 8 + (bit >> 3)) >> (bit & 7)) & 1;
      }
  }
  return bushSet[c.y * W + c.x];
}
// The bot's vision model (World::vision_from): walls and bushes are opaque except the viewer's own 8-connected bush
// cluster; engine shadowcast radius 8; bush tiles of other clusters are never seen; the own cluster always is.
let visMeta = 0, visBytes = 0, visOpaque = 0, visTmp = 0, visOut = 0, clusterId = null;
function botVisionInit(g) {
  visMeta = E.alloc(64);
  ex.Game_API_Map_GetBitboardMetadata(g, visMeta);
  ex.Bitboard_GetRawBufferSize(visMeta, E.args + 300);
  visBytes = m().getUint32(E.args + 300, true);
  visOpaque = E.alloc(visBytes + 64); visTmp = E.alloc(visBytes + 64); visOut = E.alloc(visBytes + 64);
  ex.Game_GetWallBuffer(g, E.outBuf);
  const wp = m().getUint32(E.outBuf, true);
  ex.Game_GetBushBuffer(g, E.outBuf);
  const bp = m().getUint32(E.outBuf, true);
  for (let i = 0; i < visBytes; i++) m().setUint8(visOpaque + i, m().getUint8(wp + i) | m().getUint8(bp + i));
  bushOf({ x: 0, y: 0 }); // fills bushSet
  clusterId = new Int32Array(W * H).fill(-1);
  let id = 0;
  for (let i = 0; i < W * H; i++) {
    if (!bushSet[i] || clusterId[i] >= 0) continue;
    const st2 = [i]; clusterId[i] = id;
    while (st2.length) {
      const c = st2.pop(), cx2 = c % W, cy2 = (c / W) | 0;
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        const qx = cx2 + dx, qy = cy2 + dy;
        if ((dx || dy) && qx >= 0 && qy >= 0 && qx < W && qy < H && bushSet[qy * W + qx] && clusterId[qy * W + qx] < 0) { clusterId[qy * W + qx] = id; st2.push(qy * W + qx); }
      }
    }
    id++;
  }
}
let bbStride = 0; // engine chunk stride (bitboard metadata word 4: chunk columns rounded up, e.g. 9 -> 10)
const bbIndex = (x, y) => { const bit = ((y & 7) << 3) | (x & 7); return [((y >> 3) * bbStride + (x >> 3)) * 8 + (bit >> 3), bit & 7]; };
function botSees(ax, ay, bx, by, rad = 8) {
  const own = clusterId[ay * W + ax], tc = clusterId[by * W + bx];
  if (tc >= 0) return tc === own; // a bush tile: seen only from inside its cluster
  new Uint8Array(ex.memory.buffer, visTmp, visBytes).set(new Uint8Array(ex.memory.buffer, visOpaque, visBytes));
  if (own >= 0)
    for (let i = 0; i < W * H; i++) if (clusterId[i] === own) { const [o, b] = bbIndex(i % W, (i / W) | 0); m().setUint8(visTmp + o, m().getUint8(visTmp + o) & ~(1 << b)); }
  ex.Bitboard_ShadowCast(visMeta, visTmp, ax, ay, visOut, rad);
  const [o, b] = bbIndex(bx, by);
  return ((m().getUint8(visOut + o) >> b) & 1) === 1;
}
let gCur = 0n;
// Simulator vision boards (harness layout: stride ceil(W / 8)); LAB_VIS=1 turns the simulator's vision on.
function fillVisBoards() {
  const stride = (W + 7) >> 3;
  const wb = new BigUint64Array(S.memory.buffer, S.walls(), 64 * 64), bb = new BigUint64Array(S.memory.buffer, S.bushes(), 64 * 64);
  const lb = new Uint16Array(S.memory.buffer, S.labels(), 512 * 512);
  wb.fill(0n); bb.fill(0n);
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const bit = 1n << BigInt(((y & 7) << 3) | (x & 7)), k = (y >> 3) * stride + (x >> 3);
      if (wallOnly[y * W + x]) wb[k] |= bit;
      if (clusterId[y * W + x] >= 0) { bb[k] |= bit; lb[y * W + x] = clusterId[y * W + x]; }
    }
  S.set_vis(parseInt(process.env.LAB_VIS || "0", 10));
}
const info2 = E.alloc(64);
// Any wall tile on the straight segment between the two centres (sampled), as a line-of-sight proxy.
function wallBetween(a, b) {
  const n = 16;
  for (let i = 1; i < n; i++) {
    const x = Math.round(a.x + ((b.x - a.x) * i) / n), y = Math.round(a.y + ((b.y - a.y) * i) / n);
    if ((x !== a.x || y !== a.y) && (x !== b.x || y !== b.y) && wallOnly[y * W + x]) return 1;
  }
  return 0;
}
let wallOnly = null;
let bushBuf = null;
function bushAt(g, x, y) {
  if (!bushBuf) {
    const p = ex.Game_GetBushBuffer(g, E.outBuf);
    bushBuf = { p, rc: p };
  }
  // Fall back to the bush bitboard API being unknown: report via the visualiser's linear buffer pointer when non-zero.
  const ptr = m().getUint32(E.outBuf, true);
  return ptr ? m().getUint8(ptr + y * W + x) : -1;
}
const stats = { att: {}, fights: 0, turns: 0, stepMismatch: 0, rejectedMove: 0, rejectedAttack: 0, kinds: {}, outcomeSame: 0, outcomeDiff: 0, hpErr: [], orderMismatch: 0, examples: [] };
const note = (k, ex2) => { stats.kinds[k] = (stats.kinds[k] || 0) + 1; if (stats.examples.length < 25 && ex2) stats.examples.push(k + ": " + ex2); };

for (let f = 0; f < FIGHTS; f++) {
  const g = newGame();
  gCur = g;
  readWalls(g);
  fillBoard();
  if (!visMeta) { botVisionInit(g); fillVisBoards(); }
  // Champion handles and teams.
  const all = [];
  for (let h = 0; h < 32; h++) { const c = champ(g, h); if (c) all.push(c); }
  const A = all.filter((c) => c.team === 0), B = all.filter((c) => c.team === 1);
  const ka = ri(1, Math.min(3, A.length)), kb = ri(1, Math.min(3, B.length));
  // A random open spot near the centre, teams 2-5 apart, no walls in the 9x9 box.
  let cx = 0, cy = 0;
  for (let t = 0; t < 500; t++) {
    cx = ri(6, W - 7); cy = ri(6, H - 7);
    let ok = true;
    for (let y = cy - 4; y <= cy + 4 && ok; y++) for (let x = cx - 4; x <= cx + 4; x++) if (wall[y * W + x]) { ok = false; break; }
    if (ok) break;
  }
  const taken = new Set();
  const place = (c, x, y) => {
    while (taken.has(x + "," + y) || wall[y * W + x]) { x += ri(-1, 1); y += ri(-1, 1); }
    taken.add(x + "," + y);
    m().setInt32(pos, x, true); m().setInt32(pos + 4, y, true);
    const r = ex.Game_Sandbox_Teleport(g, unit(ua, c.h), pos);
    if (r) note("teleport-fail", err());
  };
  const gap = ri(2, 5);
  const fighters = [...A.slice(0, ka), ...B.slice(0, kb)];
  A.slice(0, ka).forEach((c) => place(c, cx - Math.ceil(gap / 2) + ri(-1, 0), cy + ri(-2, 2)));
  B.slice(0, kb).forEach((c) => place(c, cx + Math.floor(gap / 2) + ri(0, 1), cy + ri(-2, 2)));
  // Random health: damage from an opposing champion.
  for (const c of fighters) {
    const opp = (c.team === 0 ? B : A)[0];
    const amt = Math.floor(c.maxhp * rnd() * 0.7);
    if (amt > 0) ex.Game_Sandbox_Damage(g, unit(ua, opp.h), unit(ub, c.h), amt);
  }
  const units = fighters.map((c) => c.h);
  stats.fights++;

  // Whole-fight prediction from the start state: simulator rollout over ROUNDS rounds. The engine's round order is
  // learned on the way (first acting fighter's team); the prediction is redone below once the order is known.
  const ROUNDS = 6;
  let startState = null, firstTeam = -1, roundStart = st(g)[2];
  let lastRound = -1, teamsThisRound = [], rounds = 0, roundPos = [];
  for (let step = 0; step < 400 && rounds < ROUNDS; step++) {
    const s = st(g);
    if (s[0] !== 1) break;
    if (s[2] !== lastRound) { lastRound = s[2]; teamsThisRound = []; if (startState) rounds++; roundPos = engUnits(g, units); }
    const h = s[3];
    const idx = units.indexOf(h);
    if (idx < 0 || !alive(g, h)) { ex.Game_Runner_EndTurn(g, 0); ex.Game_Runner_Advance(g); continue; }
    if (!startState) { firstTeam = champ(g, h).team; toSim(g, units, firstTeam); startState = Float32Array.from(sio()); roundStart = s[2]; }
    teamsThisRound.push(champ(g, h).team);
    // Simulator turn for this unit from the engine's current state.
    toSim(g, units, firstTeam);
    const before = simUnits(units.length);
    S.act_unit(idx);
    const pred = simUnits(units.length);
    const me = before[idx], mp = pred[idx];
    // Translate into engine actions: a step, then a basic attack on the unit whose health dropped most.
    let tgt = -1, drop = 0.5;
    pred.forEach((u, j) => { if (j !== idx && before[j].hp - u.hp > drop) { drop = before[j].hp - u.hp; tgt = j; } });
    const moved = mp.x !== me.x || mp.y !== me.y;
    const ranged = sio()[10 + 10 * idx] > 1;
    let refused = false;
    const doAttack = () => {
      if (tgt < 0) return;
      const r = ex.Game_Action_Attack(g, unit(ub, units[tgt]));
      const d = Math.max(Math.abs(me.x - before[tgt].x), Math.abs(me.y - before[tgt].y));
      const dx = Math.abs(me.x - before[tgt].x), dy = Math.abs(me.y - before[tgt].y);
      const t0 = roundPos[tgt], tm = t0 && (t0.x !== before[tgt].x || t0.y !== before[tgt].y) ? 1 : 0;
      const tc = champ(g, units[tgt]);
      const vis = ex.Game_API_Champion_Get(g, E.persp(champ(g, units[idx]).team, units[idx]), units[tgt], info2) === 0 ? 1 : 0;
      if (!visMeta) botVisionInit(g);
      // Team vision under the bot's model: any living teammate in the fight sees the target.
      const myTeam = champ(g, units[idx]).team;
      let pv = 0;
      units.forEach((hh, j) => { const c = champ(g, hh); if (c.team === myTeam && alive(g, hh) && botSees(c.x, c.y, tc.x, tc.y)) pv = 1; });
      // The same model from round-start positions (vision refreshed once per round?) and from turn-start positions
      // (refreshed before each champion's turn: the actor's own move this turn not yet included).
      let pr = 0;
      units.forEach((hh, j) => { const c = roundPos[j]; if (c && c.alive && champ(g, hh).team === myTeam && roundPos[tgt] && botSees(c.x, c.y, roundPos[tgt].x, roundPos[tgt].y)) pr = 1; });
      let pt = 0;
      units.forEach((hh, j) => { const c = before[j]; if (c.alive && champ(g, hh).team === myTeam && botSees(c.x, c.y, before[tgt].x, before[tgt].y)) pt = 1; });
      stats.va = stats.va || {};
      for (const rad of [3, 4, 5, 6, 7, 8, 10]) {
        for (const who of ["self", "team"]) {
          let s1 = 0;
          units.forEach((hh, j) => { const c = champ(g, hh); if ((who === "team" ? c.team === myTeam : j === idx) && alive(g, hh) && botSees(c.x, c.y, tc.x, tc.y, rad)) s1 = 1; });
          const k2 = who + rad;
          stats.va[k2] = stats.va[k2] || [0, 0];
          stats.va[k2][0] += s1 === vis ? 1 : 0; stats.va[k2][1]++;
        }
      }
      {
        const ac2 = champ(g, units[idx]);
        const own = clusterId[ac2.y * W + ac2.x], tcl = clusterId[tc.y * W + tc.x];
        const bushRule = tcl >= 0 && tcl !== own ? 0 : 1;
        const dd = Math.max(Math.abs(ac2.x - tc.x), Math.abs(ac2.y - tc.y));
        const lineRule = bushRule && !(dd >= 2 && wallBetween(ac2, tc)) ? 1 : 0;
        // Cheap rule for the simulator: bush clusters, then a sampled segment on which walls and other clusters' bushes block.
        let opq = 0;
        if (dd >= 2) for (let i2 = 1; i2 < 16; i2++) {
          const x2 = Math.round(ac2.x + ((tc.x - ac2.x) * i2) / 16), y2 = Math.round(ac2.y + ((tc.y - ac2.y) * i2) / 16);
          if ((x2 === ac2.x && y2 === ac2.y) || (x2 === tc.x && y2 === tc.y)) continue;
          const cl2 = clusterId[y2 * W + x2];
          if (wallOnly[y2 * W + x2] || (cl2 >= 0 && cl2 !== own)) { opq = 1; break; }
        }
        const opqRule = bushRule && !opq ? 1 : 0;
        const selfTS = botSees(me.x, me.y, tc.x, tc.y) ? 1 : 0;           // attacker at turn start, target now
        const selfTS2 = botSees(me.x, me.y, before[tgt].x, before[tgt].y) ? 1 : 0;
        const selfRS = roundPos[idx] && roundPos[tgt] && botSees(roundPos[idx].x, roundPos[idx].y, roundPos[tgt].x, roundPos[tgt].y) ? 1 : 0;
        const ownTS = clusterId[me.y * W + me.x];
        const bushTS = tcl >= 0 && tcl !== ownTS ? 0 : 1;
        // Engine's own vision board for the attacker's perspective, and the bot model's board, compared tile by tile.
        const vb = visOut + visBytes + 0; // scratch after visOut is not allocated; use a dedicated buffer
        if (!stats.engVisBuf) stats.engVisBuf = E.alloc(visBytes + 64);
        const evr = ex.Game_API_GetVision(g, E.persp(ac2.team, units[idx]), stats.engVisBuf);
        let engSees = -1;
        if (evr === 0) {
          const [o2, b2] = bbIndex(tc.x, tc.y);
          engSees = (m().getUint8(stats.engVisBuf + o2) >> b2) & 1;
          // Model diff over the 17x17 window around the attacker (current position).
          if ((stats.diffN = (stats.diffN || 0) + 1) <= 400) {
            botSees(ac2.x, ac2.y, ac2.x, ac2.y); // fills visOut for the attacker (own tile is not bush-special when not in bush)
            new Uint8Array(ex.memory.buffer, visTmp, visBytes).set(new Uint8Array(ex.memory.buffer, visOpaque, visBytes));
            const ownC = clusterId[ac2.y * W + ac2.x];
            if (ownC >= 0) for (let i = 0; i < W * H; i++) if (clusterId[i] === ownC) { const [o, b] = bbIndex(i % W, (i / W) | 0); m().setUint8(visTmp + o, m().getUint8(visTmp + o) & ~(1 << b)); }
            ex.Bitboard_ShadowCast(visMeta, visTmp, ac2.x, ac2.y, visOut, 8);
            for (let yy = ac2.y - 8; yy <= ac2.y + 8; yy++) for (let xx = ac2.x - 8; xx <= ac2.x + 8; xx++) {
              if (xx < 0 || yy < 0 || xx >= W || yy >= H) continue;
              const [o, b] = bbIndex(xx, yy);
              let mv = (m().getUint8(visOut + o) >> b) & 1;
              const cl = clusterId[yy * W + xx];
              if (cl >= 0) mv = cl === ownC ? 1 : 0;
              const ev = (m().getUint8(stats.engVisBuf + o) >> b) & 1;
              const dk = `eng${ev}model${mv}/bush${cl >= 0 ? 1 : 0}/wall${wallOnly[yy * W + xx] ? 1 : 0}/r2_${Math.min(99, (xx - ac2.x) ** 2 + (yy - ac2.y) ** 2) > 64 ? "gt64" : "le64"}`;
              stats.tileDiff = stats.tileDiff || {};
              stats.tileDiff[dk] = (stats.tileDiff[dk] || 0) + 1;
            }
          }
        }
        stats.va.engBoard = stats.va.engBoard || [0, 0];
        stats.va.engBoard[0] += engSees === vis ? 1 : 0; stats.va.engBoard[1]++;
        if (evr !== 0 && !stats.evErr) stats.evErr = `${evr} ${err()}`;
        for (const [k2, v2] of [["simSees", (() => { toSim(g, units, firstTeam); const v0 = process.env.LAB_VIS; S.set_vis(1); const r0 = S.sees_xy(ac2.x, ac2.y, tc.x, tc.y); S.set_vis(parseInt(v0 || "0", 10)); return r0; })()], ["bushOnly", bushRule], ["bush+wallLine", lineRule], ["bush+opaqueLine", opqRule], ["always", 1], ["selfTurnStart", selfTS], ["selfTurnStartBoth", selfTS2], ["selfRoundStart", selfRS], ["bushTurnStart", bushTS]]) {
          stats.va[k2] = stats.va[k2] || [0, 0];
          stats.va[k2][0] += v2 === vis ? 1 : 0; stats.va[k2][1]++;
        }
      }
      const key = `engineVis${vis}/now${pv}`;
      stats.att[key] = stats.att[key] || [0, 0];
      stats.att[key][r ? 1 : 0]++;
      if (r) { refused = true; stats.rejectedAttack++; note("attack-rejected", `${err()} ${key}`); }
    };
    if (moved) {
      const r = ex.Game_Action_Move(g, mp.x, mp.y, E.outBuf);
      if (r) { stats.rejectedMove++; note("move-rejected", `${err()} (${me.x},${me.y})->(${mp.x},${mp.y})`); }
    }
    doAttack();
    ex.Game_Runner_EndTurn(g, 0);
    const got = engUnits(g, units);
    stats.turns++;
    let bad = false;
    got.forEach((u, j) => {
      const p = pred[j];
      if (u.alive !== p.alive) { bad = true; note("alive-diff", `unit ${j} eng ${u.alive} sim ${p.alive}`); }
      else if (u.alive && (u.x !== p.x || u.y !== p.y)) { bad = true; note("pos-diff", `unit ${j} eng (${u.x},${u.y}) sim (${p.x},${p.y})`); }
      else if (u.alive && Math.abs(u.hp - p.hp) > 0.5) { bad = true; stats.hpErr.push(u.hp - p.hp); note(j === idx ? "hp-diff-self" : "hp-diff-other", `unit ${j} eng ${u.hp.toFixed(1)} sim ${p.hp.toFixed(1)} (str ${champ(g, units[idx]).str})`); }
    });
    if (bad) stats.stepMismatch++;
    if (bad && !refused) {
      stats.otherMismatch = (stats.otherMismatch || 0) + 1;
      if ((stats.otherEx = stats.otherEx || []).length < 30)
        stats.otherEx.push(`r${s[2]} actor ${idx} rng ${sio()[10 + 10 * idx]} moved ${moved} tgt ${tgt} | ` +
          got.map((u, j) => `${j}:eng(${u.x},${u.y},${u.hp.toFixed(0)}) sim(${pred[j].x},${pred[j].y},${pred[j].hp.toFixed(0)}) pre(${before[j].x},${before[j].y},${before[j].hp.toFixed(0)})`).join(" "));
    }
    ex.Game_Runner_Advance(g);
  }
  // Outcome: replay the start state in the simulator for the same number of rounds and compare who is alive.
  if (startState) {
    sio().set(startState);
    S.roll(Math.max(0, rounds - 1));
    const simEnd = simUnits(units.length), engEnd = engUnits(g, units);
    const same = simEnd.every((u, j) => u.alive === engEnd[j].alive);
    same ? stats.outcomeSame++ : stats.outcomeDiff++;
  }
  ex.Game_Destroy(g);
}
const e = stats.hpErr;
console.log(JSON.stringify({ map: path.basename(mapFile), W, H, fights: stats.fights, turns: stats.turns, stepMismatch: stats.stepMismatch,
  rejectedMove: stats.rejectedMove, rejectedAttack: stats.rejectedAttack, outcomeSame: stats.outcomeSame, outcomeDiff: stats.outcomeDiff,
  kinds: stats.kinds, att: stats.att, va: stats.va, evErr: stats.evErr, tileDiff: stats.tileDiff, hpErrMean: e.length ? e.reduce((a, b) => a + b, 0) / e.length : 0 }, null, 1));
console.log("non-vision mismatches:", stats.otherMismatch || 0);
for (const x of stats.otherEx || []) console.log("  " + x);







