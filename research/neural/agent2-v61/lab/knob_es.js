// Joint search over 16 runtime knobs (lab.h knobs, applied in bot.cpp after the brain layer; 0 = the combo's own play).
// Evolution strategies with antithetic pairs and rank-shaped fitness. Every candidate plays the same training games:
// MAPS unseen maps (maps_real) x both sides x opponents (the combo build sb_a2combo_c1, sparexp,
// farm). Fitness is paired against the zero-knob games on the same map / side / opponent (computed once, cached):
// mean of (win + gem margin / 2000) minus the baseline's. Real bots in the engine host (deterministic, no fuel meter).
// usage: node knob_es.js out.tsv [gens=20] [pairs=6] [maps=24] [sigma=0.6] [lr=0.3] [workers=4]
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
const LAB = path.join(ROOT, "bots", "a2c_lab", ".cambc", "build-release", "bot-injected.wasm");
const OPPS = { combo: path.join(ROOT, "bots", "sb_a2combo_c1", ".cambc", "build-release", "bot-injected.wasm"), sparexp: path.join(ROOT, "bots", "sb_sparexp_b1", ".cambc", "build-release", "bot-injected.wasm"),
  farm: path.join(ROOT, "bots", "sb_farm_b1", ".cambc", "build-release", "bot-injected.wasm") };
const NK = 16;

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => play(job)); });
  async function play(job) {
    // job: { id, k (knobs or null), map, side (0: lab is team A), opp }
    const files = job.side === 0 ? [LAB, OPPS[job.opp]] : [OPPS[job.opp], LAB];
    H.knobs = job.k ? (job.side === 0 ? [job.k, null] : [null, job.k]) : null;
    let r;
    try { r = await H.play(files[0], files[1], job.map, 3000, null, {}); } catch (e) { r = { gems: [0, 0], error: String(e) }; }
    H.knobs = null;
    const us = r.gems[job.side], them = r.gems[1 - job.side];
    parentPort.postMessage({ id: job.id, s: (us > them ? 1 : us === them ? 0.5 : 0) + (us - them) / 2000, win: us > them ? 1 : 0, error: r.error || r.abort });
  }
  return;
}

const [outFile, gensS, pairsS, mapsS, sigmaS, lrS, workersS] = process.argv.slice(2);
const GENS = +(gensS || 20), PAIRS = +(pairsS || 6), NMAPS = +(mapsS || 24), SIGMA = +(sigmaS || 0.6), LR = +(lrS || 0.3), NW = Math.min(8, +(workersS || 4));
const mapDir = path.join(ROOT, "maps_real");
const allMaps = fs.readdirSync(mapDir).filter((f) => f.endsWith(".map26a")).sort().slice(0, 75); // maps 76-125 held out
const step = Math.floor(allMaps.length / NMAPS);
const maps = Array.from({ length: NMAPS }, (_, i) => path.join(mapDir, allMaps[i * step]));
const GAMES = [];
// KNOB_OPPS="combo": train against a subset of the opponents (default all).
const OPP_LIST = process.env.KNOB_OPPS ? process.env.KNOB_OPPS.split(",") : Object.keys(OPPS);
for (const map of maps) for (const side of [0, 1]) for (const opp of OPP_LIST) GAMES.push({ map, side, opp });
let seed = 7;
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
  if (process.memoryUsage().rss > MAX_RSS) abort("memory over 3 GB");
  for (const s of slots) { if (!s.w || s.busy || !queue.length) continue; s.busy = queue.shift(); s.w.postMessage(s.busy.job); }
}
let nextId = 0;
const run = (job) => new Promise((res) => { queue.push({ job: { ...job, id: nextId++ }, res }); pump(); });
for (const s of slots) spawn(s);

async function evaluate(k, base) {
  const rs = await Promise.all(GAMES.map((g) => run({ ...g, k })));
  if (!base) return rs;
  const d = rs.map((r, i) => r.s - base[i].s);
  return { f: d.reduce((a, b) => a + b, 0) / d.length, win: rs.reduce((a, r) => a + r.win, 0) / rs.length,
    winBase: base.reduce((a, r) => a + r.win, 0) / base.length, changed: d.filter((x) => x !== 0).length };
}

(async () => {
  const t0 = Date.now();
  const base = await evaluate(null, null);
  console.log(`baseline: ${GAMES.length} games, win ${(100 * base.reduce((a, r) => a + r.win, 0) / base.length).toFixed(1)}%, ${((Date.now() - t0) / 1000).toFixed(0)} s, errors ${errors}`);
  // KNOB_INIT="k0,k1,...": start from an earlier run's knobs.
  const theta = process.env.KNOB_INIT ? process.env.KNOB_INIT.split(",").map(Number) : new Array(NK).fill(0);
  fs.writeFileSync(outFile, ["gen", "f_mean", "win", "win_base", "changed", "best_pair_f", ...theta.map((_, i) => `k${i}`)].join("\t") + "\n");
  for (let g = 1; g <= GENS; g++) {
    const eps = Array.from({ length: PAIRS }, () => Array.from({ length: NK }, gauss));
    const evals = await Promise.all(eps.flatMap((e) => [
      evaluate(theta.map((t, i) => t + SIGMA * e[i]), base), evaluate(theta.map((t, i) => t - SIGMA * e[i]), base)]));
    // Rank shaping over all 2 x PAIRS candidates, then the antithetic gradient.
    const fs_ = evals.map((e) => e.f), order = fs_.map((f, i) => [f, i]).sort((a, b) => a[0] - b[0]);
    const rank = new Array(fs_.length);
    order.forEach(([, i], r) => { rank[i] = r / (fs_.length - 1) - 0.5; });
    for (let i = 0; i < NK; i++) {
      let gsum = 0;
      for (let p = 0; p < PAIRS; p++) gsum += (rank[2 * p] - rank[2 * p + 1]) * eps[p][i];
      theta[i] += LR * gsum / (PAIRS * SIGMA);
    }
    let line = { f: NaN, win: NaN, winBase: NaN, changed: NaN };
    if (g % 3 === 0 || g === GENS) line = await evaluate(theta.slice(), base);
    const bestPair = Math.max(...fs_);
    fs.appendFileSync(outFile, [g, line.f, line.win, line.winBase, line.changed, bestPair, ...theta.map((t) => t.toFixed(3))].join("\t") + "\n");
    console.log(`gen ${g}: best candidate ${bestPair.toFixed(3)}${Number.isNaN(line.f) ? "" : ` | mean knobs: fitness ${line.f.toFixed(3)}, win ${(100 * line.win).toFixed(1)}% vs baseline ${(100 * line.winBase).toFixed(1)}%`} | ${((Date.now() - t0) / 60000).toFixed(1)} min, errors ${errors}, memory ${(process.memoryUsage().rss / 1e6).toFixed(0)} MB`);
    if (errors > 0.05 * GAMES.length * (2 * PAIRS + 1) * g) abort("too many game errors");
  }
  console.log("final knobs:", theta.map((t) => t.toFixed(3)).join(","));
  for (const s of slots) if (s.w) s.w.terminate();
})();
