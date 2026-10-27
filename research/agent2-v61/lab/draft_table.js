// Lineup-vs-lineup win table per map (OpenAI Five's drafting idea: precomputed matchup win probabilities). Our bot
// plays itself on every map with forced drafts: every candidate lineup against every other, both sides. A team with
// k picks takes the first k of its lineup. Engine 1.0.1 in the host (deterministic, no fuel meter).
// usage: node draft_table.js out.json MAPDIR [bot=v3/bots/sb_nb1_c1] [workers=4] [maxMaps]
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v1_0_1.wasm");
// Draft ids (engine 1.0.1 = SDK champion_draft): ryth 0, vesper 1, vendetta 2, C&I 3, stellar 4, prism 5, marcella 6,
// willow 7, ren 8, varg 9, tavi 10, heart of ruin 11.
const LINEUPS = {
  meta: [3, 4, 8, 0, 9], L21: [11, 2, 9, 0, 6], L24: [9, 2, 11, 4, 7], L23: [3, 4, 11, 0, 9],
  caster: [4, 10, 5, 9, 0], melee: [2, 9, 3, 0, 8], mix: [11, 2, 7, 6, 9], vesper: [1, 11, 9, 4, 0],
  // Top-15 ladder lineups on engine 1.0.1 (agent2/lab/ladder_new.jsonl, 21 Oct): the field to beat, in their pick order.
  tmVarg: [11, 4, 8, 0, 9], tmMarc: [11, 4, 6, 8, 0], tmCI: [11, 4, 8, 0, 3], tmVesVen: [11, 2, 8, 9, 1], tmVesMarc: [11, 4, 6, 1, 0],
};

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => play(job)); });
  async function play(job) {
    const n = [0, 0];
    const hooks = { draft: (team) => { const l = LINEUPS[team === job.side ? job.us : job.them]; return l[n[team]++ % l.length]; } };
    let r;
    try { r = await H.play(job.bot, job.bot, job.map, 2000, null, hooks); } catch (e) { r = { gems: [0, 0], error: String(e) }; }
    const us = r.gems[job.side], them = r.gems[1 - job.side];
    parentPort.postMessage({ id: job.id, win: us > them ? 1 : us === them ? 0.5 : 0, margin: us - them, error: r.error || r.abort });
  }
  return;
}

const [outFile, mapDirS, botS, workersS, maxMapsS] = process.argv.slice(2);
const BOT = path.join(ROOT, botS || "v3/bots/sb_nb1_c1", ".cambc", "build-release", "bot-injected.wasm");
const NW = Math.min(8, +(workersS || 4));
const mapDir = path.resolve(mapDirS || path.join(ROOT, "v3", "maps"));
const maps = fs.readdirSync(mapDir).filter((f) => f.endsWith(".map26a")).sort().slice(0, +(maxMapsS || 1000));
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

(async () => {
  const names = Object.keys(LINEUPS);
  // DRAFT_OPPS=meta,L21,...: the opponent field (default every lineup).
  const opps = process.env.DRAFT_OPPS ? process.env.DRAFT_OPPS.split(",") : names;
  const out = fs.existsSync(outFile) ? JSON.parse(fs.readFileSync(outFile, "utf8")) : { lineups: LINEUPS, maps: {} };
  const t0 = Date.now();
  for (const m of maps) {
    if (out.maps[m]) continue;
    const jobs = [];
    for (const us of names) for (const them of opps) for (const side of [0, 1]) jobs.push({ map: path.join(mapDir, m), bot: BOT, us, them, side });
    const rs = await Promise.all(jobs.map((j) => run(j)));
    const W = {}, M = {};
    for (const us of names) { W[us] = {}; M[us] = {}; for (const them of opps) { W[us][them] = 0; M[us][them] = 0; } }
    rs.forEach((r, i) => { const j = jobs[i]; W[j.us][j.them] += r.win / 2; M[j.us][j.them] += r.margin / 2; });
    out.maps[m] = { W, M };
    fs.writeFileSync(outFile, JSON.stringify(out));
    const mean = names.map((u) => [u, opps.reduce((a, t) => a + W[u][t], 0) / opps.length]).sort((a, b) => b[1] - a[1]);
    console.log(`${m}: best ${mean.slice(0, 3).map(([u, v]) => `${u} ${(100 * v).toFixed(0)}%`).join(", ")} | ${((Date.now() - t0) / 60000).toFixed(1)} min, errors ${errors}, memory ${(process.memoryUsage().rss / 1e6).toFixed(0)} MB`);
  }
  for (const s of slots) if (s.w) s.w.terminate();
})();
