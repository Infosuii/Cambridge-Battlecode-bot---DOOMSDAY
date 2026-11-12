// Fixed lineups vs a bot's own draft (engine 2.0.0 / cambc 4.0.0). Both sides run the same bot; our side's picks are
// forced to the lineup (a team with k picks takes the first k), the other side drafts itself (hook returns null).
// Above 50% = the lineup beats the bot's own draft. Maps: NU unseen (maps_test4) + NO official, both sides.
// usage: node lineup_v4.js out.json [bot=v57_c1] [nu=30] [no=20] [workers=6] [lineups=all]
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v2_0_0.wasm");
// Draft ids: ryth 0, vesper 1, vendetta 2, C&I 3, stellar 4, prism 5, marcella 6, willow 7, ren 8, varg 9, tavi 10, heart of ruin 11.
const LINEUPS = {
  L21: [11, 2, 9, 0, 6], L24: [9, 2, 11, 4, 7], melee: [2, 9, 3, 0, 8],
  tmVarg: [11, 4, 8, 0, 9], tmMarc: [11, 4, 6, 8, 0], tmVesVen: [11, 2, 8, 9, 1],
  // 4.0.0 buffs: Vesper, Vendetta, Tavi, Prism; nerfs: Heart of Ruin, Ren, Stellar.
  vesVen: [1, 2, 9, 0, 6], noHoR: [2, 9, 0, 6, 1], vendHoR: [2, 11, 9, 0, 1], tavi: [10, 2, 9, 0, 1],
  prism: [5, 2, 9, 0, 11], vesTav: [1, 10, 2, 9, 11], casterB: [10, 5, 1, 9, 0], mixB: [11, 2, 1, 10, 9],
};

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => play(job)); });
  async function play(job) {
    let n = 0;
    const hooks = { draft: (team) => (team === job.side ? LINEUPS[job.us][n++ % 5] : null) };
    let r;
    try { r = await H.play(job.bot, job.bot, job.map, 2000, null, hooks); } catch (e) { r = { gems: [0, 0], error: String(e) }; }
    const us = r.gems[job.side], them = r.gems[1 - job.side];
    parentPort.postMessage({ id: job.id, win: us > them ? 1 : us === them ? 0.5 : 0, margin: us - them, error: r.error || r.abort });
  }
  return;
}

const [outFile, botS, nuS, noS, workersS, lineS] = process.argv.slice(2);
const BOT = path.join(ROOT, "v4", "bots", botS || "v57_c1", ".cambc", "build-release", "bot-injected.wasm");
const NW = Math.min(8, +(workersS || 6));
const pick = (d, k) => fs.readdirSync(d).filter((f) => f.endsWith(".map26a")).sort().filter((_, i, a) => i % Math.max(1, Math.floor(a.length / k)) === 0).slice(0, k).map((f) => path.join(d, f));
const unseen = pick(path.join(ROOT, "v4", "maps_test4"), +(nuS || 30)), official = pick(path.join(ROOT, "v4", "maps"), +(noS || 20));
const names = lineS ? lineS.split(",") : Object.keys(LINEUPS);
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
  const out = {};
  const stat = (rs) => { const w = rs.reduce((a, r) => a + r.win, 0); return { n: rs.length, win: w / rs.length, margin: rs.reduce((a, r) => a + r.margin, 0) / rs.length }; };
  await Promise.all(names.map(async (us) => {
    const jobs = [...unseen.map((m) => ["u", m]), ...official.map((m) => ["o", m])].flatMap(([k, map]) => [0, 1].map((side) => ({ k, map, side, us, bot: BOT })));
    const rs = await Promise.all(jobs.map((j) => run(j)));
    out[us] = { all: stat(rs), unseen: stat(rs.filter((_, i) => jobs[i].k === "u")), official: stat(rs.filter((_, i) => jobs[i].k === "o")), lineup: LINEUPS[us] };
    const a = out[us];
    console.log(`${us.padEnd(9)} ${JSON.stringify(LINEUPS[us])}: ${(100 * a.all.win).toFixed(1)}% of ${a.all.n} (unseen ${(100 * a.unseen.win).toFixed(0)}%, official ${(100 * a.official.win).toFixed(0)}%), margin ${a.all.margin.toFixed(0)} | ${((Date.now() - t0) / 60000).toFixed(1)} min, errors ${errors}`);
    fs.writeFileSync(outFile, JSON.stringify(out, null, 1));
  }));
  for (const s of slots) if (s.w) s.w.terminate();
})();
