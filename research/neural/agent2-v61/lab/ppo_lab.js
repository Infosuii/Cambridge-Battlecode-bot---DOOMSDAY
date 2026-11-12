// PPO for the fight/run policy (A2_POLICY lab build; lab.h: 24 features -> 32 tanh -> 2 logits), following OpenAI
// Five (1912.06680): shaped zero-sum team reward with team spirit 1 and a win bonus, GAE, PPO clipping, entropy bonus,
// opponents mixed between the target bot, another bot and self-play, and a start from the existing behaviour.
// Games run in the engine host (engine 1.0.1, ~1 s per game). Weights saved to OUT.json after every iteration.
// usage: node ppo_lab.js OUT.json [iters=30] [games=64] [workers=4]
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v1_0_1.wasm");
const NI = 24, NH = 32, K = 3, NW_POL = NI * NH + NH + NH * K + K, ENTRY = NI + 3; // actions: fight, run, keep the bot's verdict
const BOTS = {
  lab: path.join(ROOT, "v3", "bots", "a2c_pol", ".cambc", "build-release", "bot-injected.wasm"),
  nb1: path.join(ROOT, "v3", "bots", "sb_nb1_c1", ".cambc", "build-release", "bot-injected.wasm"),
  ext: path.join(ROOT, "v3", "bots", "sb_ext_c1", ".cambc", "build-release", "bot-injected.wasm"),
};

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => play(job)); });
  async function play(job) {
    // job: { id, w, map, side (lab team), opp: nb1 | ext | self, mode (1 sample, 0 argmax), seed }
    const ex = H.ex, ci = H.arena + 2048, o = H.arena + 2300, ab = H.arena + 2200;
    const P = () => H.E.persp(2, 0xffffffff);
    const score = () => { // team 0 minus team 1: banked + carried gems + 40 per living champion
      const tot = [0, 0];
      for (let t = 0; t < 2; t++) if (ex.Game_API_GetSubmittedGemCount(H.g, t, o) === 0) tot[t] += H.m.getUint32(o, true);
      for (let h = 0; h < 12; h++) {
        if (ex.Game_API_Champion_Get(H.g, P(), h, ci) !== 0) continue;
        const t = H.m.getInt32(ci, true);
        if (ex.Game_API_Champion_GetGems(H.g, P(), h, o) === 0) tot[t] += H.m.getUint32(o, true);
        if (ex.Game_API_Champion_IsAlive(H.g, h, ab) === 0 && H.m.getUint8(ab)) tot[t] += 40;
      }
      return tot[0] - tot[1];
    };
    const S = {};
    let last = -1;
    const hooks = { afterTurn: (round) => { if (round !== last) { last = round; S[round] = score(); } return false; } };
    const self = job.opp === "self";
    const files = job.side === 0 ? [BOTS.lab, self ? BOTS.lab : BOTS[job.opp]] : [self ? BOTS.lab : BOTS[job.opp], BOTS.lab];
    H.polW = [job.side === 0 || self ? job.w : null, job.side === 1 || self ? job.w : null];
    H.polMode = [job.mode, job.mode];
    H.polSeed = job.seed;
    let r;
    try { r = await H.play(files[0], files[1], job.map, 2000, null, hooks); } catch (e) { r = { gems: [0, 0], error: String(e) }; }
    H.polW = null;
    const logs = (r.polLogs || []).filter((l) => self || l.team === job.side);
    parentPort.postMessage({ id: job.id, gems: r.gems, final: score(), S, logs, error: r.error || r.abort });
  }
  return;
}

// ---------------------------------------------------------------- main: PPO
const [outFile, itersS, gamesS, workersS] = process.argv.slice(2);
const ITERS = +(itersS || 30), GAMES = +(gamesS || 64), NWK = Math.min(8, +(workersS || 4));
const mapDirs = [path.join(ROOT, "v3", "maps"), path.join(ROOT, "v3", "maps_real")];
const maps = mapDirs.flatMap((d) => fs.readdirSync(d).filter((f) => f.endsWith(".map26a")).sort().slice(0, d.endsWith("maps") ? 1000 : 64).map((f) => path.join(d, f)));
let seed = 12345;
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);
const gauss = () => Math.sqrt(-2 * Math.log(rnd() + 1e-12)) * Math.cos(2 * Math.PI * rnd());

// Networks: policy (NI -> NH tanh -> 2) and value (NI -> NH tanh -> 1), plain arrays.
function initPolicy() {
  const w = new Float32Array(NW_POL);
  for (let i = 0; i < NI * NH; i++) w[i] = 0.05 * gauss();
  const W2 = NI * NH + NH;
  for (let j = 0; j < NH * K; j++) w[W2 + j] = 0.05 * gauss();
  // Start from the existing behaviour (paper: surgery): "keep the bot's verdict" strongly preferred (~90%).
  w[NW_POL - 1] = 3.0;
  return Array.from(w);
}
const initValue = () => Array.from({ length: NI * NH + NH + NH + 1 }, (_, i) => (i < NI * NH || (i >= NI * NH + NH && i < NI * NH + 2 * NH) ? 0.05 * gauss() : 0));
function polForward(w, f) {
  const h = new Array(NH);
  const z = Array.from({ length: K }, (_, c) => w[NW_POL - K + c]);
  for (let j = 0; j < NH; j++) {
    let v = w[NI * NH + j];
    for (let i = 0; i < NI; i++) v += f[i] * w[i * NH + j];
    h[j] = Math.tanh(v);
    for (let c = 0; c < K; c++) z[c] += h[j] * w[NI * NH + NH + j * K + c];
  }
  const m = Math.max(...z), e = z.map((x) => Math.exp(x - m)), s = e.reduce((a, b) => a + b, 0);
  return { h, p: e.map((x) => x / s) };
}
function valForward(v, f) {
  const h = new Array(NH);
  let out = v[NI * NH + 2 * NH];
  for (let j = 0; j < NH; j++) {
    let s = v[NI * NH + j];
    for (let i = 0; i < NI; i++) s += f[i] * v[i * NH + j];
    h[j] = Math.tanh(s);
    out += h[j] * v[NI * NH + NH + j];
  }
  return { h, out };
}
function adam(params, grads, st, lr) {
  st.t = (st.t || 0) + 1;
  st.m = st.m || new Array(params.length).fill(0);
  st.v = st.v || new Array(params.length).fill(0);
  for (let i = 0; i < params.length; i++) {
    const g = Math.max(-5, Math.min(5, grads[i]));
    st.m[i] = 0.9 * st.m[i] + 0.1 * g; st.v[i] = 0.999 * st.v[i] + 0.001 * g * g;
    params[i] -= lr * (st.m[i] / (1 - 0.9 ** st.t)) / (Math.sqrt(st.v[i] / (1 - 0.999 ** st.t)) + 1e-8);
  }
}

const RECYCLE = 40, MAX_RSS = 4.5e9;
const queue = [];
const slots = Array.from({ length: NWK }, () => ({ w: null, games: 0, busy: null }));
let errors = 0;
function abort(why) { console.log("ABORT:", why); for (const s of slots) if (s.w) s.w.terminate(); process.exit(2); }
function spawn(slot) {
  slot.w = new Worker(__filename); slot.games = 0;
  slot.w.on("message", (m) => { const job = slot.busy; slot.busy = null; if (m.error) errors++; job.res(m); if (++slot.games >= RECYCLE) { const old = slot.w; slot.w = null; old.terminate().then(() => { spawn(slot); pump(); }); return; } pump(); });
  slot.w.on("error", (e) => abort("worker error " + String(e)));
}
function pump() {
  if (process.memoryUsage().rss > MAX_RSS) abort("memory over 3 GB");
  for (const s of slots) { if (!s.w || s.busy || !queue.length) continue; s.busy = queue.shift(); s.w.postMessage(s.busy.job); }
}
let nextId = 0;
const run = (job) => new Promise((res) => { queue.push({ job: { ...job, id: nextId++ }, res }); pump(); });
for (const s of slots) spawn(s);

// One game's decisions -> transitions with rewards (team-shared, zero-sum, per champion in round order).
function transitions(res, labSide, opp) {
  const out = [];
  const rounds = Object.keys(res.S).map(Number).sort((a, b) => a - b);
  const at = (r) => { let v = 0; for (const k of rounds) { if (k > r) break; v = res.S[k]; } return v; };
  for (const l of res.logs) {
    const sign = l.team === 0 ? 1 : -1;
    const n = l.data.length / ENTRY;
    const won = (res.gems[l.team] > res.gems[1 - l.team]) ? 1 : res.gems[l.team] < res.gems[1 - l.team] ? -1 : 0;
    for (let k = 0; k < n; k++) {
      const e = l.data.slice(k * ENTRY, (k + 1) * ENTRY);
      const r0 = e[NI + 2], r1 = k + 1 < n ? l.data[(k + 1) * ENTRY + NI + 2] : Infinity;
      const end = k + 1 === n;
      const rew = sign * ((end ? res.final : at(r1)) - at(r0)) / 100 + (end ? 5 * won : 0);
      out.push({ f: e.slice(0, NI), a: e[NI], logp: e[NI + 1], rew, end });
    }
  }
  return out;
}

(async () => {
  const saved = fs.existsSync(outFile) ? JSON.parse(fs.readFileSync(outFile, "utf8")) : null;
  const W = saved ? saved.w : initPolicy(), V = saved ? saved.v : initValue();
  const optW = {}, optV = {};
  // Running reward scale (paper: rewards normalised by a running estimate of their standard deviation).
  let rs2 = saved && saved.rs2 ? saved.rs2 : 1, rsn = saved && saved.rsn ? saved.rsn : 0;
  const WARMUP = +(process.env.PPO_WARMUP || 3), startIter = saved ? saved.history.length : 0;
  const evalMaps = maps.filter((_, i) => i % 7 === 0).slice(0, 35);
  const history = saved ? saved.history : [];
  const t0 = Date.now();
  async function evaluate(w) {
    const jobs = evalMaps.flatMap((map) => [0, 1].map((side) => ({ w, map, side, opp: "nb1", mode: 0, seed: 1 })));
    const rs = await Promise.all(jobs.map(run));
    let wins = 0;
    rs.forEach((r, i) => { const s = jobs[i].side; wins += r.gems[s] > r.gems[1 - s] ? 1 : r.gems[s] === r.gems[1 - s] ? 0.5 : 0; });
    return wins / rs.length;
  }
  const base = await evaluate(W);
  console.log(`start: greedy policy vs nb1 ${(100 * base).toFixed(1)}% on ${evalMaps.length * 2} games | ${((Date.now() - t0) / 60000).toFixed(1)} min`);
  for (let it = 1; it <= ITERS; it++) {
    // Rollouts: opponents nb1 50%, ext 25%, self-play 25%.
    const jobs = Array.from({ length: GAMES }, (_, g) => {
      const u = rnd();
      return { w: W, map: maps[Math.floor(rnd() * maps.length)], side: g % 2, opp: u < 0.5 ? "nb1" : u < 0.75 ? "ext" : "self", mode: 1, seed: it * 1000 + g };
    });
    const rs = await Promise.all(jobs.map(run));
    let tr = [], wins = 0, n = 0;
    rs.forEach((r, i) => {
      if (r.error) return;
      tr = tr.concat(transitions(r, jobs[i].side, jobs[i].opp));
      if (jobs[i].opp !== "self") { const s = jobs[i].side; wins += r.gems[s] > r.gems[1 - s] ? 1 : 0; n++; }
    });
    for (const t of tr) { rsn++; rs2 += (t.rew * t.rew - rs2) / Math.min(rsn, 100000); }
    const rscale = Math.sqrt(rs2) + 1e-6;
    for (const t of tr) t.rew /= rscale;
    const warm = it <= WARMUP && startIter === 0; // value-only iterations at the start of a fresh run
    // GAE per decision sequence (transitions are in sequence order per champion; `end` closes a sequence).
    const gamma = 0.99, lam = 0.95;
    const vals = tr.map((t) => valForward(V, t.f).out);
    const adv = new Array(tr.length), ret = new Array(tr.length);
    let gae = 0;
    for (let i = tr.length - 1; i >= 0; i--) {
      const nextV = tr[i].end ? 0 : vals[i + 1];
      if (tr[i].end) gae = 0;
      const delta = tr[i].rew + gamma * nextV - vals[i];
      gae = delta + gamma * lam * gae;
      adv[i] = gae; ret[i] = gae + vals[i];
    }
    const am = adv.reduce((a, b) => a + b, 0) / adv.length, as = Math.sqrt(adv.reduce((a, b) => a + (b - am) ** 2, 0) / adv.length) + 1e-6;
    // PPO epochs over minibatches (manual gradients for both small networks).
    const idx = tr.map((_, i) => i);
    let clipped = 0, ent = 0;
    for (let ep = 0; ep < 4; ep++) {
      for (let i = idx.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [idx[i], idx[j]] = [idx[j], idx[i]]; }
      for (let b0 = 0; b0 < idx.length; b0 += 256) {
        const batch = idx.slice(b0, b0 + 256);
        const gW = new Array(W.length).fill(0), gV = new Array(V.length).fill(0);
        for (const i of batch) {
          const t = tr[i], A = (adv[i] - am) / as;
          const { h, p } = polForward(W, t.f);
          const a = t.a | 0, ratio = Math.exp(Math.log(Math.max(p[a], 1e-8)) - t.logp);
          const clip = (A > 0 && ratio > 1.2) || (A < 0 && ratio < 0.8);
          if (clip) clipped++;
          // d(-surrogate)/d logit, plus the entropy bonus 0.01.
          const dlogp = clip || warm ? 0 : -A * ratio;
          const H_ = -p.reduce((s, q) => s + q * Math.log(q + 1e-8), 0);
          ent += H_;
          const dz = p.map((q, c) => dlogp * ((c === a ? 1 : 0) - q) + (warm ? 0 : 0.01 * q * (Math.log(q + 1e-8) + H_)));
          const o2 = NI * NH + NH;
          for (let c = 0; c < K; c++) gW[NW_POL - K + c] += dz[c];
          for (let j = 0; j < NH; j++) {
            let dh = 0;
            for (let c = 0; c < K; c++) { gW[o2 + j * K + c] += dz[c] * h[j]; dh += dz[c] * W[o2 + j * K + c]; }
            dh *= 1 - h[j] * h[j];
            gW[NI * NH + j] += dh;
            for (let k = 0; k < NI; k++) gW[k * NH + j] += dh * t.f[k];
          }
          // Value: squared error to the return.
          const vf = valForward(V, t.f), dv = (vf.out - ret[i]);
          gV[NI * NH + 2 * NH] += dv;
          for (let j = 0; j < NH; j++) {
            gV[NI * NH + NH + j] += dv * vf.h[j];
            const dh = dv * V[NI * NH + NH + j] * (1 - vf.h[j] * vf.h[j]);
            gV[NI * NH + j] += dh;
            for (let k = 0; k < NI; k++) gV[k * NH + j] += dh * t.f[k];
          }
        }
        adam(W, gW.map((g) => g / batch.length), optW, 1e-3);
        adam(V, gV.map((g) => g / batch.length), optV, 2e-3);
      }
    }
    const fights = tr.filter((t) => t.a === 0).length / Math.max(1, tr.length), runs = tr.filter((t) => t.a === 1).length / Math.max(1, tr.length);
    let line = `iter ${it}: ${tr.length} decisions, fight ${(100 * fights).toFixed(0)}% run ${(100 * runs).toFixed(0)}% keep ${(100 * (1 - fights - runs)).toFixed(0)}%, sampled win vs others ${(100 * wins / Math.max(1, n)).toFixed(0)}%, clipped ${(100 * clipped / (4 * tr.length)).toFixed(0)}%, entropy ${(ent / (4 * tr.length)).toFixed(2)}`;
    if (it % 10 === 0 || it === ITERS) line += ` | greedy vs nb1 ${(100 * (await evaluate(W))).toFixed(1)}%`;
    line += ` | ${((Date.now() - t0) / 60000).toFixed(1)} min, errors ${errors}, memory ${(process.memoryUsage().rss / 1e6).toFixed(0)} MB`;
    console.log(line);
    history.push(line);
    fs.writeFileSync(outFile, JSON.stringify({ w: W, v: V, history, rs2, rsn }));
  }
  for (const s of slots) if (s.w) s.w.terminate();
})();
