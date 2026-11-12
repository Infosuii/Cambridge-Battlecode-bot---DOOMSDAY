// PPO for policy v2 (A2_POLICY=2 lab build, lab.h): per-unit inputs (64) -> 48 tanh -> verdict head (fight, run, keep)
// and target head (4 enemy slots, keep). OpenAI Five ingredients (1912.06680): scale (large batches, long runs),
// a league (current policy, a pool of past versions, nb1, the provided bot), domain randomisation (random forced
// lineups for both teams in half the games; 150 generated + 35 official maps), zero-sum team reward with a win bonus,
// reward normalisation, GAE, clipping, entropy bonus, start from the bot's own behaviour ("keep" preferred).
// usage: node ppo2_lab.js OUT.json [iters=200] [games=256] [workers=6]
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v1_0_1.wasm");
const NI = 64, NH = 48, KV = 3, KT = 5;
const O_B1 = NI * NH, O_WV = O_B1 + NH, O_BV = O_WV + NH * KV, O_WT = O_BV + KV, O_BT = O_WT + NH * KT, NW_POL = O_BT + KT;
const ENTRY = NI + 5;
const BOTS = {
  lab: path.join(ROOT, "v3", "bots", "a2c_pol2", ".cambc", "build-release", "bot-injected.wasm"),
  nb1: path.join(ROOT, "v3", "bots", "sb_nb1_c1", ".cambc", "build-release", "bot-injected.wasm"),
  ext: path.join(ROOT, "v3", "bots", "sb_ext_c1", ".cambc", "build-release", "bot-injected.wasm"),
};
// Draft ids: ryth 0, vesper 1, vendetta 2, C&I 3, stellar 4, prism 5, marcella 6, willow 7, ren 8, varg 9, tavi 10, HoR 11.
const LINEUPS = [[3, 4, 8, 0, 9], [11, 2, 9, 0, 6], [9, 2, 11, 4, 7], [3, 4, 11, 0, 9], [4, 10, 5, 9, 0], [2, 9, 3, 0, 8], [11, 2, 7, 6, 9], [1, 11, 9, 4, 0]];

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => play(job)); });
  async function play(job) {
    const ex = H.ex, ci = H.arena + 2048, o = H.arena + 2300, ab = H.arena + 2200;
    const P = () => H.E.persp(2, 0xffffffff);
    const score = () => {
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
    const n = [0, 0];
    const hooks = { afterTurn: (round) => { if (round !== last) { last = round; S[round] = score(); } return false; } };
    if (job.lineups) hooks.draft = (team) => { const l = job.lineups[team]; return l[n[team]++ % l.length]; };
    const both = job.opp === "self" || job.opp === "pool";
    const oppFile = both ? BOTS.lab : BOTS[job.opp];
    const files = job.side === 0 ? [BOTS.lab, oppFile] : [oppFile, BOTS.lab];
    const wOpp = job.opp === "pool" ? job.wPool : job.w;
    H.polW = job.side === 0 ? [job.w, both ? wOpp : null] : [both ? wOpp : null, job.w];
    H.polMode = [job.mode, job.mode];
    H.polSeed = job.seed;
    let r;
    try { r = await H.play(files[0], files[1], job.map, 2000, null, hooks); } catch (e) { r = { gems: [0, 0], error: String(e) }; }
    H.polW = null;
    const keep = job.opp === "self" ? () => true : (l) => l.team === job.side; // pool opponents are not trained on
    const logs = (r.polLogs || []).filter(keep);
    parentPort.postMessage({ id: job.id, gems: r.gems, final: score(), S, logs, error: r.error || r.abort });
  }
  return;
}

// ---------------------------------------------------------------- main: PPO with a league
const [outFile, itersS, gamesS, workersS] = process.argv.slice(2);
const ITERS = +(itersS || 200), GAMES = +(gamesS || 256), NWK = Math.min(8, +(workersS || 6));
const mapList = [[path.join(ROOT, "v3", "maps_new"), 150], [path.join(ROOT, "v3", "maps"), 35]]
  .flatMap(([d, k]) => fs.readdirSync(d).filter((f) => f.endsWith(".map26a")).sort().slice(0, k).map((f) => path.join(d, f)));
let seed = 424242;
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);
const gauss = () => Math.sqrt(-2 * Math.log(rnd() + 1e-12)) * Math.cos(2 * Math.PI * rnd());

function initPolicy() {
  const w = new Array(NW_POL).fill(0);
  for (let i = 0; i < O_B1; i++) w[i] = 0.04 * gauss();
  for (let i = O_WV; i < O_BV; i++) w[i] = 0.04 * gauss();
  for (let i = O_WT; i < O_BT; i++) w[i] = 0.04 * gauss();
  w[O_BV + 2] = 3.0; // verdict: keep the bot's
  w[O_BT + 4] = 3.0; // target: keep the bot's
  return w;
}
const NV = NI * NH + NH + NH + 1;
const initValue = () => Array.from({ length: NV }, (_, i) => (i < NI * NH || (i >= NI * NH + NH && i < NI * NH + 2 * NH) ? 0.04 * gauss() : 0));
function forward(w, f) {
  const h = new Array(NH), zv = w.slice(O_BV, O_BV + KV), zt = w.slice(O_BT, O_BT + KT);
  for (let j = 0; j < NH; j++) {
    let v = w[O_B1 + j];
    for (let i = 0; i < NI; i++) v += f[i] * w[i * NH + j];
    h[j] = Math.tanh(v);
    for (let c = 0; c < KV; c++) zv[c] += h[j] * w[O_WV + j * KV + c];
    for (let c = 0; c < KT; c++) zt[c] += h[j] * w[O_WT + j * KT + c];
  }
  for (let k = 0; k < 4; k++) if (f[12 + 10 * k] < 0.5) zt[k] = -1e9;
  const sm = (z) => { const m = Math.max(...z), e = z.map((x) => Math.exp(x - m)), s = e.reduce((a, b) => a + b, 0); return e.map((x) => x / s); };
  return { h, pv: sm(zv), pt: sm(zt) };
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
  if (process.memoryUsage().rss > MAX_RSS) abort("memory over 4.5 GB");
  for (const s of slots) { if (!s.w || s.busy || !queue.length) continue; s.busy = queue.shift(); s.w.postMessage(s.busy.job); }
}
let nextId = 0;
const run = (job) => new Promise((res) => { queue.push({ job: { ...job, id: nextId++ }, res }); pump(); });
for (const s of slots) spawn(s);

function transitions(res) {
  const out = [];
  const rounds = Object.keys(res.S).map(Number).sort((a, b) => a - b);
  const at = (r) => { let v = 0; for (const k of rounds) { if (k > r) break; v = res.S[k]; } return v; };
  for (const l of res.logs) {
    const sign = l.team === 0 ? 1 : -1, E = l.entry, n = l.data.length / E;
    const won = res.gems[l.team] > res.gems[1 - l.team] ? 1 : res.gems[l.team] < res.gems[1 - l.team] ? -1 : 0;
    for (let k = 0; k < n; k++) {
      const e = l.data.slice(k * E, (k + 1) * E);
      const r0 = e[NI + 3], r1 = k + 1 < n ? l.data[(k + 1) * E + NI + 3] : Infinity, end = k + 1 === n;
      out.push({ f: e.slice(0, NI), av: e[NI] | 0, at: e[NI + 1] | 0, logp: e[NI + 2], rew: sign * ((end ? res.final : at(r1)) - at(r0)) / 100 + (end ? 5 * won : 0), end });
    }
  }
  return out;
}

(async () => {
  const saved = fs.existsSync(outFile) ? JSON.parse(fs.readFileSync(outFile, "utf8")) : null;
  const W = saved ? saved.w : initPolicy(), V = saved ? saved.v : initValue();
  const pool = saved && saved.pool ? saved.pool : [];
  const history = saved ? saved.history : [];
  let rs2 = saved && saved.rs2 ? saved.rs2 : 1, rsn = saved && saved.rsn ? saved.rsn : 0;
  const optW = {}, optV = {};
  const evalMaps = mapList.filter((_, i) => i % 9 === 0);
  const startIter = history.length;
  const t0 = Date.now();
  async function evaluate(w) {
    const jobs = evalMaps.flatMap((map) => [0, 1].map((side) => ({ w, map, side, opp: "nb1", mode: 0, seed: 1 })));
    const rs = await Promise.all(jobs.map(run));
    let wins = 0;
    rs.forEach((r, i) => { const s = jobs[i].side; wins += r.gems[s] > r.gems[1 - s] ? 1 : r.gems[s] === r.gems[1 - s] ? 0.5 : 0; });
    return { p: wins / rs.length, n: rs.length };
  }
  if (startIter === 0) { const e0 = await evaluate(W); console.log(`start: greedy vs nb1 ${(100 * e0.p).toFixed(1)}% on ${e0.n} games | ${((Date.now() - t0) / 60000).toFixed(1)} min`); }
  for (let it = 1; it <= ITERS; it++) {
    const gi = startIter + it;
    const jobs = Array.from({ length: GAMES }, (_, g) => {
      const u = rnd();
      const opp = u < 0.35 ? "self" : u < 0.55 && pool.length ? "pool" : u < 0.85 ? "nb1" : "ext";
      const lineups = rnd() < 0.5 ? [LINEUPS[Math.floor(rnd() * LINEUPS.length)], LINEUPS[Math.floor(rnd() * LINEUPS.length)]] : null;
      return { w: W, wPool: pool.length ? pool[Math.floor(rnd() * pool.length)] : null, map: mapList[Math.floor(rnd() * mapList.length)], side: g % 2, opp, lineups, mode: 1, seed: gi * 1000 + g };
    });
    const rs = await Promise.all(jobs.map(run));
    let tr = [], wins = 0, nv = 0;
    rs.forEach((r, i) => {
      if (r.error) return;
      tr = tr.concat(transitions(r));
      if (jobs[i].opp === "nb1") { const s = jobs[i].side; wins += r.gems[s] > r.gems[1 - s] ? 1 : 0; nv++; }
    });
    for (const t of tr) { rsn++; rs2 += (t.rew * t.rew - rs2) / Math.min(rsn, 200000); }
    const rscale = Math.sqrt(rs2) + 1e-6;
    for (const t of tr) t.rew /= rscale;
    const warm = gi <= 3;
    const vals = tr.map((t) => valForward(V, t.f).out);
    const adv = new Array(tr.length), ret = new Array(tr.length);
    let gae = 0;
    for (let i = tr.length - 1; i >= 0; i--) {
      if (tr[i].end) gae = 0;
      const delta = tr[i].rew + 0.99 * (tr[i].end ? 0 : vals[i + 1]) - vals[i];
      gae = delta + 0.99 * 0.95 * gae;
      adv[i] = gae; ret[i] = gae + vals[i];
    }
    const am = adv.reduce((a, b) => a + b, 0) / adv.length, as = Math.sqrt(adv.reduce((a, b) => a + (b - am) ** 2, 0) / adv.length) + 1e-6;
    const idx = tr.map((_, i) => i);
    let clipped = 0;
    for (let ep = 0; ep < 3; ep++) {
      for (let i = idx.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [idx[i], idx[j]] = [idx[j], idx[i]]; }
      for (let b0 = 0; b0 < idx.length; b0 += 512) {
        const batch = idx.slice(b0, b0 + 512);
        const gW = new Array(NW_POL).fill(0), gV = new Array(NV).fill(0);
        for (const i of batch) {
          const t = tr[i], A = (adv[i] - am) / as;
          const { h, pv, pt } = forward(W, t.f);
          const ratio = Math.exp(Math.log(Math.max(pv[t.av], 1e-8)) + Math.log(Math.max(pt[t.at], 1e-8)) - t.logp);
          const clip = (A > 0 && ratio > 1.2) || (A < 0 && ratio < 0.8);
          if (clip) clipped++;
          const dl = clip || warm ? 0 : -A * ratio;
          const ent = (p) => -p.reduce((s, q) => s + (q > 0 ? q * Math.log(q) : 0), 0);
          const Hv = ent(pv), Ht = ent(pt), eb = warm ? 0 : 0.01;
          const dzv = pv.map((q, c) => dl * ((c === t.av ? 1 : 0) - q) + eb * q * (Math.log(q + 1e-8) + Hv));
          const dzt = pt.map((q, c) => (q === 0 ? 0 : dl * ((c === t.at ? 1 : 0) - q) + eb * q * (Math.log(q + 1e-8) + Ht)));
          for (let c = 0; c < KV; c++) gW[O_BV + c] += dzv[c];
          for (let c = 0; c < KT; c++) gW[O_BT + c] += dzt[c];
          for (let j = 0; j < NH; j++) {
            let dh = 0;
            for (let c = 0; c < KV; c++) { gW[O_WV + j * KV + c] += dzv[c] * h[j]; dh += dzv[c] * W[O_WV + j * KV + c]; }
            for (let c = 0; c < KT; c++) { gW[O_WT + j * KT + c] += dzt[c] * h[j]; dh += dzt[c] * W[O_WT + j * KT + c]; }
            dh *= 1 - h[j] * h[j];
            if (dh === 0) continue;
            gW[O_B1 + j] += dh;
            for (let k = 0; k < NI; k++) if (t.f[k] !== 0) gW[k * NH + j] += dh * t.f[k];
          }
          const vf = valForward(V, t.f), dv = vf.out - ret[i];
          gV[NI * NH + 2 * NH] += dv;
          for (let j = 0; j < NH; j++) {
            gV[NI * NH + NH + j] += dv * vf.h[j];
            const dh = dv * V[NI * NH + NH + j] * (1 - vf.h[j] * vf.h[j]);
            gV[NI * NH + j] += dh;
            for (let k = 0; k < NI; k++) if (t.f[k] !== 0) gV[k * NH + j] += dh * t.f[k];
          }
        }
        adam(W, gW.map((g) => g / batch.length), optW, 5e-4);
        adam(V, gV.map((g) => g / batch.length), optV, 1e-3);
      }
    }
    if (gi % 10 === 0) { pool.push(W.slice()); if (pool.length > 10) pool.shift(); }
    const frac = (k, v) => tr.filter((t) => t[k] === v).length / Math.max(1, tr.length);
    let line = `iter ${gi}: ${GAMES} games, ${tr.length} decisions, verdict fight ${(100 * frac("av", 0)).toFixed(0)}% run ${(100 * frac("av", 1)).toFixed(0)}% keep ${(100 * frac("av", 2)).toFixed(0)}%, target override ${(100 * (1 - frac("at", 4))).toFixed(0)}%, sampled vs nb1 ${(100 * wins / Math.max(1, nv)).toFixed(0)}% (${nv}), clipped ${(100 * clipped / (3 * Math.max(1, tr.length))).toFixed(0)}%`;
    if (gi % 10 === 0 || it === ITERS) { const e = await evaluate(W); line += ` | greedy vs nb1 ${(100 * e.p).toFixed(1)}% (${e.n})`; }
    line += ` | ${((Date.now() - t0) / 60000).toFixed(1)} min, errors ${errors}, memory ${(process.memoryUsage().rss / 1e6).toFixed(0)} MB`;
    console.log(line);
    history.push(line);
    fs.writeFileSync(outFile, JSON.stringify({ w: W, v: V, pool, history, rs2, rsn }));
  }
  for (const s of slots) if (s.w) s.w.terminate();
})();
