// Black-box search v2 (engine 1.0.1): evolution strategies over 24 lab knobs (lab.h; 0-15 tuning, 16-21 targeting
// weights, 22-23 melee / ranged aggression), our bot with fixed item builds (lab builds table). Every candidate plays
// the same games (paired): MAPS maps x 2 sides x opponents nb1 and the provided bot, plus a league opponent (a past
// winner, our lab bot with its knobs) whose baseline is replayed each generation. Fitness = mean (win + margin / 2000)
// minus the zero-knob baseline on the same games.
// usage: node knob_es2.js out.tsv [gens=30] [pairs=8] [maps=48] [sigma=0.3] [lr=0.15] [workers=6]
// env: KNOB_INIT=k0,..,k23  BUILDS=file.json (the 16 x 17 build table)  LAB_BOT  ES_OPPS  KNOB_N (see below)
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v1_0_1.wasm");
const wasmOf = (b) => path.join(ROOT, "v3", "bots", b, ".cambc", "build-release", "bot-injected.wasm");
// LAB_BOT: the A2_LAB build whose knobs are searched (default a2c_klab = nb1 + A2_LAB).
// ES_OPPS=name=bot,..: the fixed opponents (default nb1=sb_nb1_c1,ext=sb_ext_c1); each plays every map on both sides.
const LAB = wasmOf(process.env.LAB_BOT || "a2c_klab");
const OPPS = { league: LAB };
for (const kv of (process.env.ES_OPPS || "nb1=sb_nb1_c1,ext=sb_ext_c1").split(",")) { const [k, v] = kv.split("="); OPPS[k] = wasmOf(v); }
const FIXED_OPPS = Object.keys(OPPS).filter((k) => k !== "league");
const NK = +(process.env.KNOB_N || 24); // must match lab.h knobs[] length

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => play(job)); });
  async function play(job) {
    const files = job.side === 0 ? [LAB, OPPS[job.opp]] : [OPPS[job.opp], LAB];
    const lg = job.opp === "league";
    H.knobs = job.side === 0 ? [job.k, lg ? job.kOpp : null] : [lg ? job.kOpp : null, job.k];
    H.builds = job.side === 0 ? [job.builds, lg ? job.builds : null] : [lg ? job.builds : null, job.builds];
    let r;
    try { r = await H.play(files[0], files[1], job.map, 2000, null, {}); } catch (e) { r = { gems: [0, 0], error: String(e) }; }
    H.knobs = null; H.builds = null;
    const us = r.gems[job.side], them = r.gems[1 - job.side];
    parentPort.postMessage({ id: job.id, s: (us > them ? 1 : us === them ? 0.5 : 0) + (us - them) / 2000, win: us > them ? 1 : us === them ? 0.5 : 0, error: r.error || r.abort });
  }
  return;
}

const [outFile, gensS, pairsS, mapsS, sigmaS, lrS, workersS] = process.argv.slice(2);
const GENS = +(gensS || 30), PAIRS = +(pairsS || 8), NMAPS = +(mapsS || 48), SIGMA = +(sigmaS || 0.3), LR = +(lrS || 0.15), NW = Math.min(8, +(workersS || 6));
const BUILDS = process.env.BUILDS ? JSON.parse(fs.readFileSync(process.env.BUILDS, "utf8")) : null;
const all = [[path.join(ROOT, "v3", "maps_new"), 150], [path.join(ROOT, "v3", "maps"), 35]]
  .flatMap(([d, k]) => fs.readdirSync(d).filter((f) => f.endsWith(".map26a")).sort().slice(0, k).map((f) => path.join(d, f)));
const step = Math.max(1, Math.floor(all.length / NMAPS));
const maps = all.filter((_, i) => i % step === 0).slice(0, NMAPS);
const FIXED = [];
for (const map of maps) for (const side of [0, 1]) for (const opp of FIXED_OPPS) FIXED.push({ map, side, opp });
const LEAGUE = maps.filter((_, i) => i % 3 === 0).flatMap((map) => [0, 1].map((side) => ({ map, side, opp: "league" })));
let seed = 31;
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);
const gauss = () => Math.sqrt(-2 * Math.log(rnd() + 1e-12)) * Math.cos(2 * Math.PI * rnd());

const RECYCLE = 40, MAX_RSS = 4.5e9;
const queue = [];
const slots = Array.from({ length: NW }, () => ({ w: null, games: 0, busy: null }));
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

async function play(k, games, kOpp) { return Promise.all(games.map((g) => run({ ...g, k, kOpp, builds: BUILDS }))); }
const fitness = (rs, base) => rs.reduce((a, r, i) => a + r.s - base[i].s, 0) / rs.length;
const winrate = (rs) => rs.reduce((a, r) => a + r.win, 0) / rs.length;

(async () => {
  const t0 = Date.now();
  const zero = new Array(NK).fill(0);
  const baseFixed = await play(zero, FIXED, null);
  console.log(`baseline (zero knobs, builds ${BUILDS ? "from file" : "default"}): ${FIXED.length} games vs the fixed opponents, win ${(100 * winrate(baseFixed)).toFixed(1)}% | ${((Date.now() - t0) / 60000).toFixed(1)} min`);
  const theta = process.env.KNOB_INIT ? process.env.KNOB_INIT.split(",").map(Number) : zero.slice();
  while (theta.length < NK) theta.push(0);
  const pool = [zero.slice()];
  fs.writeFileSync(outFile, ["gen", "f_mean", "win_fixed", "win_base", "best", ...theta.map((_, i) => `k${i}`)].join("\t") + "\n");
  for (let g = 1; g <= GENS; g++) {
    const kOpp = pool[Math.floor(rnd() * pool.length)];
    const baseLeague = await play(zero, LEAGUE, kOpp);
    const games = FIXED.concat(LEAGUE), base = baseFixed.concat(baseLeague);
    const eps = Array.from({ length: PAIRS }, () => Array.from({ length: NK }, gauss));
    const fs_ = [];
    await Promise.all(eps.flatMap((e, p) => [1, -1].map(async (sg) => {
      const rs = await play(theta.map((t, i) => t + sg * SIGMA * e[i]), games, kOpp);
      fs_[2 * p + (sg > 0 ? 0 : 1)] = fitness(rs, base);
    })));
    const order = fs_.map((f, i) => [f, i]).sort((a, b) => a[0] - b[0]);
    const rank = new Array(fs_.length);
    order.forEach(([, i], r) => { rank[i] = r / (fs_.length - 1) - 0.5; });
    for (let i = 0; i < NK; i++) {
      let gsum = 0;
      for (let p = 0; p < PAIRS; p++) gsum += (rank[2 * p] - rank[2 * p + 1]) * eps[p][i];
      theta[i] += LR * gsum / (PAIRS * SIGMA);
    }
    let line = { f: NaN, w: NaN };
    if (g % 2 === 0 || g === GENS) {
      const rs = await play(theta.slice(), games, kOpp);
      line = { f: fitness(rs, base), w: winrate(rs.slice(0, FIXED.length)) };
      if (line.f > 0) { pool.push(theta.slice()); if (pool.length > 8) pool.splice(1, 1); }
    }
    fs.appendFileSync(outFile, [g, line.f, line.w, winrate(baseFixed), Math.max(...fs_), ...theta.map((t) => t.toFixed(3))].join("\t") + "\n");
    console.log(`gen ${g}: best candidate ${Math.max(...fs_).toFixed(3)}${Number.isNaN(line.f) ? "" : ` | mean knobs: fitness ${line.f.toFixed(3)}, win vs fixed opponents ${(100 * line.w).toFixed(1)}% (baseline ${(100 * winrate(baseFixed)).toFixed(1)}%)`} | ${((Date.now() - t0) / 60000).toFixed(1)} min, errors ${errors}, memory ${(process.memoryUsage().rss / 1e6).toFixed(0)} MB`);
  }
  console.log("final knobs:", theta.map((t) => t.toFixed(3)).join(","));
  for (const s of slots) if (s.w) s.w.terminate();
})();
