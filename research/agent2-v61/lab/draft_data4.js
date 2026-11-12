// Self-play draft data on engine 2.0.0: both teams get a random lineup (forced picks), the same bot plays both sides,
// and every pick is recorded in order with the final result. Rows for draft_fit4.py: the draft net's inputs at the
// moment of each pick (map features, our picks with this one, their picks so far, team size, picking first, progress).
// usage: node draft_data4.js out.jsonl GAMES_PER_MAP [bot=v57_c1] [workers=3] [seed=7] DIR [DIR..]
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v2_0_0.wasm");

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => play(job)); });
  async function play(job) {
    const n = [0, 0], seq = [];
    const hooks = { draft: (team) => { const c = job.lineups[team][n[team]++ % 5]; seq.push([team, c]); return c; } };
    let r;
    try { r = await H.play(job.bot, job.bot, job.map, 2000, null, hooks); } catch (e) { r = { gems: [0, 0], error: String(e) }; }
    parentPort.postMessage({ id: job.id, gems: r.gems, seq, error: r.error || r.abort });
  }
  return;
}

const [outFile, perMapS, botS, workersS, seedS, ...dirs] = process.argv.slice(2);
const BOT = path.join(ROOT, "v4", "bots", botS || "v57_c1", ".cambc", "build-release", "bot-injected.wasm");
const NW = Math.min(8, +(workersS || 3));
let seed = +(seedS || 7);
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);
const lineup = () => { const a = [...Array(12).keys()]; for (let i = 11; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a.slice(0, 5); };
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

(async () => {
  const t0 = Date.now();
  const maps = dirs.flatMap((d) => fs.readdirSync(d).filter((f) => f.endsWith(".map26a")).sort().map((f) => ({ key: path.basename(d) + "/" + f, file: path.join(d, f) })));
  const jobs = maps.flatMap((m) => Array.from({ length: +perMapS }, () => ({ map: m.file, key: m.key, lineups: [lineup(), lineup()], bot: BOT })));
  const out = fs.createWriteStream(outFile, { flags: "a" });
  let done = 0;
  await Promise.all(jobs.map(async (j) => {
    const r = await run(j);
    out.write(JSON.stringify({ map: j.key, lineups: j.lineups, seq: r.seq, gems: r.gems, error: r.error || null }) + "\n");
    if (++done % 200 === 0) console.log(`${done}/${jobs.length} games | ${((Date.now() - t0) / 60000).toFixed(1)} min, errors ${errors}`);
  }));
  out.end();
  for (const s of slots) if (s.w) s.w.terminate();
  console.log(`done ${done} games, errors ${errors}`);
})();
