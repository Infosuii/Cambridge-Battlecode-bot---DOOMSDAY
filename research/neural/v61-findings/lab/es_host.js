// Training environment run: evolution strategies over the farm scorer's learner weights (NOVA_LEARNER, 16 features),
// games played inside the engine host (host.js) â€” real bots, no rebuild per candidate. Each candidate (lab build with
// its weights) plays the combo on both sides of the generation's maps; fitness = mean gem margin / 1000 + 0.5 x
// (win rate - 0.5). Antithetic pairs; the mean moves along the fitness-weighted noise.
// usage: node es_host.js out.tsv [gens=30] [pairs=6] [maps=8] [sigma=0.5] [lr=0.25] [workers=4, max 4]
const { Worker, isMainThread, parentPort, workerData } = require("worker_threads");
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..", "..");
const LAB = path.join(ROOT, "bots", "a2c_lab", ".cambc", "build-release", "bot-injected.wasm");
const BASE = path.join(ROOT, "bots", "a2c_combo", ".cambc", "build-release", "bot-injected.wasm");

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  // One game at a time per worker: a Host holds one live game (concurrent plays would overwrite each other).
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => playJob(job)); });
  async function playJob(job) {
    // job: { id, w, map, side } side 0: lab is team A
    const weights = job.side === 0 ? [job.w, null] : [null, job.w];
    const files = job.side === 0 ? [LAB, BASE] : [BASE, LAB];
    let r;
    try { r = await H.play(files[0], files[1], job.map, 3000, weights); } catch (e) { r = { gems: [0, 0], error: String(e) }; }
    const us = r.gems[job.side], them = r.gems[1 - job.side];
    parentPort.postMessage({ id: job.id, margin: us - them, win: us > them ? 1 : us === them ? 0.5 : 0, round: r.round, error: r.error || r.abort });
  }
  return;
}

const [outFile, gensS, pairsS, mapsS, sigmaS, lrS, workersS] = process.argv.slice(2);
const GENS = +(gensS || 30), PAIRS = +(pairsS || 6), NMAPS = +(mapsS || 8), SIGMA = +(sigmaS || 0.5), LR = +(lrS || 0.25), NW = Math.min(4, +(workersS || 4)); // at most 4 workers (memory)
const mapDir = path.join(ROOT, "maps_rdev");
const allMaps = fs.readdirSync(mapDir).filter((f) => f.endsWith(".map26a")).sort().map((f) => path.join(mapDir, f));
let seed = 99;
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);
const gauss = () => Math.sqrt(-2 * Math.log(rnd() + 1e-12)) * Math.cos(2 * Math.PI * rnd());

// Memory safety: bot instances suspended at game end are not freed inside a worker (~6 MB per game), so each worker
// plays at most RECYCLE games and is then terminated (which frees everything) and replaced. Jobs go out one at a time
// per worker; the whole run aborts if the process passes MAX_RSS.
const RECYCLE = 20;
const MAX_RSS = 3e9;
const queue = [];
let aborted = null;
function abort(why) {
  if (aborted) return;
  aborted = why;
  console.log("ABORT:", why);
  fs.appendFileSync(outFile, `# ABORT ${why}\n`);
  for (const s of slots) if (s.w) s.w.terminate();
  process.exit(2);
}
const slots = Array.from({ length: NW }, () => ({ w: null, games: 0, busy: null }));
function spawn(slot) {
  slot.w = new Worker(__filename);
  slot.games = 0;
  slot.w.on("message", (m) => {
    const job = slot.busy;
    slot.busy = null;
    job.res(m);
    if (++slot.games >= RECYCLE) { const old = slot.w; slot.w = null; old.terminate().then(() => { spawn(slot); pump(); }); return; }
    pump();
  });
  slot.w.on("error", (e) => abort("worker error " + String(e)));
}
function pump() {
  if (process.memoryUsage().rss > MAX_RSS) abort(`memory ${(process.memoryUsage().rss / 1e9).toFixed(2)} GB over limit`);
  for (const s of slots) {
    if (!s.w || s.busy || !queue.length) continue;
    s.busy = queue.shift();
    s.w.postMessage(s.busy.job);
  }
}
let nextId = 0;
const run = (job) => new Promise((res) => { queue.push({ job: { ...job, id: nextId++ }, res }); pump(); });
for (const s of slots) spawn(s);

async function fitness(w, maps) {
  const jobs = [];
  for (const map of maps) for (const side of [0, 1]) jobs.push(run({ w, map, side }));
  const rs = await Promise.all(jobs);
  const margin = rs.reduce((s, r) => s + r.margin, 0) / rs.length, win = rs.reduce((s, r) => s + r.win, 0) / rs.length;
  const errs = rs.filter((r) => r.error).length;
  return { f: margin / 1000 + 0.5 * (win - 0.5), margin, win, errs };
}

(async () => {
  // Evaluation mode: ES_EVAL="w0,...,w15" plays those weights on NMAPS maps (both sides) from ES_MAPDIR and exits.
  if (process.env.ES_EVAL) {
    const w = process.env.ES_EVAL.split(",").map(Number);
    const dir = path.join(ROOT, process.env.ES_MAPDIR || "maps_dev");
    const ms = fs.readdirSync(dir).filter((f) => f.endsWith(".map26a")).sort().slice(0, NMAPS).map((f) => path.join(dir, f));
    const r = await fitness(w, ms);
    const line = `eval ${process.env.ES_MAPDIR || "maps_dev"} maps ${ms.length} games ${ms.length * 2}: margin ${r.margin.toFixed(1)} win ${r.win.toFixed(3)} errors ${r.errs}`;
    console.log(line); fs.appendFileSync(outFile, "# " + line + "\n");
    for (const s of slots) if (s.w) s.w.terminate();
    return;
  }
  let mean = new Array(16).fill(0);
  fs.appendFileSync(outFile, `# es_host ${new Date().toISOString()} gens ${GENS} pairs ${PAIRS} maps ${NMAPS} sigma ${SIGMA} lr ${LR}\n`);
  for (let gen = 0; gen < GENS; gen++) {
    const t0 = Date.now();
    const maps = Array.from({ length: NMAPS }, () => allMaps[Math.floor(rnd() * allMaps.length)]);
    const noise = Array.from({ length: PAIRS }, () => Array.from({ length: 16 }, gauss));
    const cands = [];
    for (const n of noise) { cands.push(mean.map((m, i) => m + SIGMA * n[i])); cands.push(mean.map((m, i) => m - SIGMA * n[i])); }
    const [fm, ...fs2] = await Promise.all([fitness(mean, maps), ...cands.map((c) => fitness(c, maps))]);
    // Rank-normalised antithetic gradient.
    const fvals = fs2.map((x) => x.f);
    const order = fvals.map((v, i) => [v, i]).sort((a, b) => a[0] - b[0]);
    const rank = new Array(fvals.length);
    order.forEach(([, i], k) => { rank[i] = k / (fvals.length - 1) - 0.5; });
    const grad = new Array(16).fill(0);
    noise.forEach((n, p) => { const d = rank[2 * p] - rank[2 * p + 1]; for (let i = 0; i < 16; i++) grad[i] += d * n[i]; });
    mean = mean.map((m, i) => m + (LR / (PAIRS * SIGMA)) * grad[i] * SIGMA);
    const best = Math.max(...fvals);
    const line = [gen, fm.f.toFixed(4), fm.margin.toFixed(1), fm.win.toFixed(3), best.toFixed(4), fs2.reduce((s, x) => s + x.errs, 0) + fm.errs, ((Date.now() - t0) / 1000).toFixed(1), mean.map((v) => v.toFixed(3)).join(",")].join("\t");
    fs.appendFileSync(outFile, line + "\n");
    const errs = fs2.reduce((s, x) => s + x.errs, 0) + fm.errs, games = (fs2.length + 1) * NMAPS * 2;
    if (errs > 0.05 * games) abort(`${errs}/${games} games errored in generation ${gen}`);
    console.log(`  memory ${(process.memoryUsage().rss / 1e6).toFixed(0)} MB`);
    console.log(`gen ${gen}: mean f ${fm.f.toFixed(4)} (margin ${fm.margin.toFixed(1)}, win ${fm.win.toFixed(3)}), best cand ${best.toFixed(4)}, ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
  console.log("final mean weights:", mean.map((v) => v.toFixed(4)).join(","));
  for (const s of slots) if (s.w) s.w.terminate();
})();
