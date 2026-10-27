// Map-conditioned black-box search (A2_CTX lab build): evolution strategies over 24 base knobs + 24 slopes per map
// feature (team size, ln area, ln gem density, ln groups, monolith; bot.cpp / lab.h), so the bot's settings become a
// function of what it reads on turn one and carry to unseen maps. Every generation draws a fresh sample of training maps
// (maps_new 150 + official 35; maps_test3 is never used), plays the centre and every antithetic candidate on the same
// games (paired), and ranks candidates by mean (win + margin / 2000) minus the centre's.
// usage: node knob_ctx.js out.tsv [gens=30] [pairs=12] [maps=32] [sigma=0.25] [lr=0.12] [workers=6]
// env: LAB_BOT (default a2c_ctx)  ES_OPPS=name=bot,.. (default nb2=knkf_c1,ext=sb_ext_c1)  KNOB_INIT (padded with 0)
//      BOTS_DIR  ES_MAPDIRS  CTX_F (features, default 5; knobs = 24 (1 + CTX_F))  SLOPE_SIGMA (sigma multiplier for slopes, default 1)  ES_SEED (default 41)
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v1_0_1.wasm");
const wasmOf = (b) => path.join(process.env.BOTS_DIR || path.join(ROOT, "v3", "bots"), b, ".cambc", "build-release", "bot-injected.wasm"); // BOTS_DIR: e.g. v4/bots
const LAB = wasmOf(process.env.LAB_BOT || "a2c_ctx");
const OPPS = {};
for (const kv of (process.env.ES_OPPS || "nb2=knkf_c1,ext=sb_ext_c1").split(",")) { const [k, v] = kv.split("="); OPPS[k] = wasmOf(v); }
const NF = +(process.env.CTX_F || 5), NK = 24 * (1 + NF);

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => play(job)); });
  async function play(job) {
    const files = job.side === 0 ? [LAB, OPPS[job.opp]] : [OPPS[job.opp], LAB];
    H.knobs = job.side === 0 ? [job.k, null] : [null, job.k];
    let r;
    try { r = await H.play(files[0], files[1], job.map, 2000, null, {}); } catch (e) { r = { gems: [0, 0], error: String(e) }; }
    H.knobs = null;
    const us = r.gems[job.side], them = r.gems[1 - job.side];
    const win = us > them ? 1 : us === them ? 0.5 : 0;
    // ES_SCORE=farm (E68): solo farm speed against an idle opponent: (2000 - round at 1,000 banked) / 1000, or the
    // banked share - 1 if we never got there.
    const s = process.env.ES_SCORE === "farm" ? (us >= 1000 ? (2000 - r.round) / 1000 : us / 1000 - 1) : win + (us - them) / 2000;
    parentPort.postMessage({ id: job.id, s, win, error: r.error || r.abort });
  }
  return;
}

const [outFile, gensS, pairsS, mapsS, sigmaS, lrS, workersS] = process.argv.slice(2);
const GENS = +(gensS || 30), PAIRS = +(pairsS || 12), NMAPS = +(mapsS || 32), SIGMA = +(sigmaS || 0.25), LR = +(lrS || 0.12), NW = Math.min(8, +(workersS || 6));
const SLOPE_SIGMA = +(process.env.SLOPE_SIGMA || 1);
// ES_MAPDIRS=dir:count,..: training maps (default v3/maps_new:150,v3/maps:35); never the held-out test set.
// ES_MAPLIST=file: training maps listed one per line (relative to the project root), e.g. one map cluster (plan_clusters.py).
const all = process.env.ES_MAPLIST ? fs.readFileSync(path.resolve(ROOT, process.env.ES_MAPLIST), "utf8").split("\n").map((s) => s.trim()).filter(Boolean).map((f) => path.resolve(ROOT, f)) : (process.env.ES_MAPDIRS ? process.env.ES_MAPDIRS.split(",").map((s) => { const [d, k] = s.split(":"); return [path.resolve(ROOT, d), +k]; })
  : [[path.join(ROOT, "v3", "maps_new"), 150], [path.join(ROOT, "v3", "maps"), 35]])
  .flatMap(([d, k]) => fs.readdirSync(d).filter((f) => f.endsWith(".map26a")).sort().slice(0, k).map((f) => path.join(d, f)));
let seed = +(process.env.ES_SEED || 41);
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
const play = (k, games) => Promise.all(games.map((g) => run({ ...g, k })));
const mean = (rs, f) => rs.reduce((a, r) => a + f(r), 0) / rs.length;

(async () => {
  const t0 = Date.now();
  const theta = process.env.KNOB_INIT ? process.env.KNOB_INIT.split(",").map(Number) : [];
  while (theta.length < NK) theta.push(0);
  const sig = Array.from({ length: NK }, (_, i) => SIGMA * (i < 24 ? 1 : SLOPE_SIGMA));
  fs.writeFileSync(outFile, ["gen", "win_centre", "s_centre", "best_gain", "mean_gain", ...theta.map((_, i) => `k${i}`)].join("\t") + "\n");
  for (let g = 1; g <= GENS; g++) {
    // Fresh maps every generation (without replacement within the generation).
    const pool = all.slice();
    const maps = [];
    while (maps.length < NMAPS && pool.length) maps.push(pool.splice(Math.floor(rnd() * pool.length), 1)[0]);
    const games = [];
    for (const map of maps) for (const side of [0, 1]) for (const opp of Object.keys(OPPS)) games.push({ map, side, opp });
    const eps = Array.from({ length: PAIRS }, () => Array.from({ length: NK }, gauss));
    const centreP = play(theta.slice(), games);
    const fs_ = [];
    const cands = eps.flatMap((e, p) => [1, -1].map(async (sg) => {
      const rs = await play(theta.map((t, i) => t + sg * sig[i] * e[i]), games);
      fs_[2 * p + (sg > 0 ? 0 : 1)] = mean(rs, (r) => r.s);
    }));
    const centre = await centreP;
    await Promise.all(cands);
    const sc = mean(centre, (r) => r.s);
    const order = fs_.map((f, i) => [f, i]).sort((a, b) => a[0] - b[0]);
    const rank = new Array(fs_.length);
    order.forEach(([, i], r) => { rank[i] = r / (fs_.length - 1) - 0.5; });
    for (let i = 0; i < NK; i++) {
      let gsum = 0;
      for (let p = 0; p < PAIRS; p++) gsum += (rank[2 * p] - rank[2 * p + 1]) * eps[p][i];
      theta[i] += LR * (sig[i] / SIGMA) * gsum / (PAIRS * SIGMA); // as knob_es2.js, scaled per knob by its sigma
    }
    const best = Math.max(...fs_) - sc, mg = mean(fs_, (f) => f) - sc;
    fs.appendFileSync(outFile, [g, mean(centre, (r) => r.win).toFixed(4), sc.toFixed(4), best.toFixed(4), mg.toFixed(4), ...theta.map((t) => t.toFixed(4))].join("\t") + "\n");
    const slopeNorm = Math.sqrt(theta.slice(24).reduce((a, v) => a + v * v, 0));
    console.log(`gen ${g}: centre win ${(100 * mean(centre, (r) => r.win)).toFixed(1)}% on ${games.length} games | best candidate ${best >= 0 ? "+" : ""}${best.toFixed(3)} | slope norm ${slopeNorm.toFixed(2)} | ${((Date.now() - t0) / 60000).toFixed(1)} min, errors ${errors}, memory ${(process.memoryUsage().rss / 1e6).toFixed(0)} MB`);
  }
  console.log("final knobs:", theta.map((t) => t.toFixed(4)).join(","));
  for (const s of slots) if (s.w) s.w.terminate();
})();
