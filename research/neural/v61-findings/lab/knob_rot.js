// Block-rotation black-box search (k64 knob expansion, agent2/KNOBS.md): evolution strategies like knob_ctx.js, but
// only the knobs of one block (ES_BLOCK) are perturbed and updated; every other knob stays at its KNOB_INIT value.
// Every generation draws fresh training maps (stratified per directory when quotas are given), plays the centre and
// every antithetic candidate on the same games (paired) and ranks candidates by mean (win + margin / 2000).
// usage: node knob_rot.js out.tsv [gens=15] [pairs=12] [maps=25] [sigma=0.25] [lr=0.10] [workers=3]
// env: LAB_BOT (default k64)  ES_OPPS=name=bot,.. (default v61=v61_c2,b5=b5_c2)  BOTS_DIR  ENGWASM  LAB_DRAFT_FUEL
//      KNOB_INIT=k0,k1,.. or @file (padded with 0 to ES_NK)  ES_NK (default 160)  ES_SEED (default 41)
//      ES_BLOCK=a-b[,c-d..] (knob indices searched; required)
//      ES_MAPDIRS=dir:count[:quota],.. (first `count` maps of each dir; with quotas, each generation takes `quota` maps
//      from each dir and the maps argument is ignored)  ES_MAPLIST=file (one map per line, as knob_ctx.js)
// out.tsv: gen, win_centre, s_centre, best_gain, mean_gain, then all ES_NK knobs (the row is a full resume point).
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v2_0_0.wasm");
const wasmOf = (b) => path.join(process.env.BOTS_DIR || path.join(ROOT, "v4", "bots"), b, ".cambc", "build-release", "bot-injected.wasm");
const LAB = wasmOf(process.env.LAB_BOT || "k64");
const OPPS = {};
for (const kv of (process.env.ES_OPPS || "v61=v61_c2,b5=b5_c2").split(",")) { const [k, v] = kv.split("="); OPPS[k] = wasmOf(v); }
const NK = +(process.env.ES_NK || 160);

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
    parentPort.postMessage({ id: job.id, s: win + (us - them) / 2000, win, error: r.error || r.abort });
  }
  return;
}

const [outFile, gensS, pairsS, mapsS, sigmaS, lrS, workersS] = process.argv.slice(2);
const GENS = +(gensS || 15), PAIRS = +(pairsS || 12), NMAPS = +(mapsS || 25), SIGMA = +(sigmaS || 0.25), LR = +(lrS || 0.10), NW = Math.min(8, +(workersS || 3));
const readList = (s) => (s.startsWith("@") ? fs.readFileSync(path.resolve(ROOT, s.slice(1)), "utf8") : s).trim().split(/[\s,]+/).filter(Boolean).map(Number);
// Block mask.
if (!process.env.ES_BLOCK) { console.log("ES_BLOCK is required (e.g. 64-88)"); process.exit(2); }
const mask = [];
for (const part of process.env.ES_BLOCK.split(",")) {
  const [a, b] = part.split("-").map(Number);
  for (let i = a; i <= (Number.isFinite(b) ? b : a); i++) if (i >= 0 && i < NK && !mask.includes(i)) mask.push(i);
}
// Training maps: strata of [dir files, quota] (quota 0 = pooled, drawn uniformly up to NMAPS).
let strata;
if (process.env.ES_MAPLIST) {
  strata = [[fs.readFileSync(path.resolve(ROOT, process.env.ES_MAPLIST), "utf8").split("\n").map((s) => s.trim()).filter(Boolean).map((f) => path.resolve(ROOT, f)), 0]];
} else {
  strata = (process.env.ES_MAPDIRS || "v4/maps:70:10,v4/maps_maze:150:10,v4/maps_new4:150:5").split(",").map((s) => {
    const [d, k, q] = s.split(":");
    const dir = path.resolve(ROOT, d);
    return [fs.readdirSync(dir).filter((f) => f.endsWith(".map26a")).sort().slice(0, +k).map((f) => path.join(dir, f)), +(q || 0)];
  });
}
const quotas = strata.some(([, q]) => q > 0);
let seed = +(process.env.ES_SEED || 41);
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);
const gauss = () => Math.sqrt(-2 * Math.log(rnd() + 1e-12)) * Math.cos(2 * Math.PI * rnd());
function drawMaps() {
  const take = (pool, n) => { const p = pool.slice(), out = []; while (out.length < n && p.length) out.push(p.splice(Math.floor(rnd() * p.length), 1)[0]); return out; };
  if (quotas) return strata.flatMap(([files, q]) => take(files, q));
  return take(strata.flatMap(([files]) => files), NMAPS);
}

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
  const theta = process.env.KNOB_INIT ? readList(process.env.KNOB_INIT) : [];
  while (theta.length < NK) theta.push(0);
  theta.length = NK;
  const header = ["gen", "win_centre", "s_centre", "best_gain", "mean_gain", ...theta.map((_, i) => `k${i}`)].join("\t") + "\n";
  if (!fs.existsSync(outFile)) fs.writeFileSync(outFile, header);
  console.log(`block ${process.env.ES_BLOCK} (${mask.length} knobs), ${strata.map(([f, q]) => `${f.length}${q ? "/" + q : ""}`).join(" + ")} maps, ${Object.keys(OPPS).join("+")}, ${PAIRS} pairs, sigma ${SIGMA}, lr ${LR}, ${NW} workers`);
  for (let g = 1; g <= GENS; g++) {
    const maps = drawMaps();
    const games = [];
    for (const map of maps) for (const side of [0, 1]) for (const opp of Object.keys(OPPS)) games.push({ map, side, opp });
    const eps = Array.from({ length: PAIRS }, () => mask.map(() => gauss()));
    const centreP = play(theta.slice(), games);
    const fs_ = [];
    const cands = eps.flatMap((e, p) => [1, -1].map(async (sg) => {
      const k = theta.slice();
      mask.forEach((i, j) => { k[i] += sg * SIGMA * e[j]; });
      const rs = await play(k, games);
      fs_[2 * p + (sg > 0 ? 0 : 1)] = mean(rs, (r) => r.s);
    }));
    const centre = await centreP;
    await Promise.all(cands);
    const sc = mean(centre, (r) => r.s);
    const order = fs_.map((f, i) => [f, i]).sort((a, b) => a[0] - b[0]);
    const rank = new Array(fs_.length);
    order.forEach(([, i], r) => { rank[i] = r / (fs_.length - 1) - 0.5; });
    mask.forEach((i, j) => {
      let gsum = 0;
      for (let p = 0; p < PAIRS; p++) gsum += (rank[2 * p] - rank[2 * p + 1]) * eps[p][j];
      theta[i] += LR * gsum / (PAIRS * SIGMA); // as knob_ctx.js (centred ranks, antithetic pairs)
    });
    const best = Math.max(...fs_) - sc, mg = mean(fs_, (f) => f) - sc;
    fs.appendFileSync(outFile, [g, mean(centre, (r) => r.win).toFixed(4), sc.toFixed(4), best.toFixed(4), mg.toFixed(4), ...theta.map((t) => t.toFixed(4))].join("\t") + "\n");
    const moved = mask.map((i) => [i, theta[i]]).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 4).map(([i, v]) => `k${i} ${v.toFixed(2)}`).join(", ");
    console.log(`gen ${g}: centre win ${(100 * mean(centre, (r) => r.win)).toFixed(1)}% on ${games.length} games | best candidate ${best >= 0 ? "+" : ""}${best.toFixed(3)} | top ${moved} | ${((Date.now() - t0) / 60000).toFixed(1)} min, errors ${errors}, memory ${(process.memoryUsage().rss / 1e6).toFixed(0)} MB`);
  }
  console.log("final knobs:", theta.map((t) => t.toFixed(4)).join(","));
  for (const s of slots) if (s.w) s.w.terminate();
})();
