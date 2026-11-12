// Expert-iteration data for macro choices (camp / bank / hold / regroup / home): at random decision points (random map,
// round, one of our first champions) the identical game is replayed once per option (lab.h kinds: -1 keep = record only,
// 1 forbid the current camp, 2 bank now, 3 hold the bag, 6 regroup, 7 home). Each option's team margin (banked +
// carried gems + 40 per living champion, ours minus theirs) HORIZON rounds later minus keep's is its gain. The bot's
// features at the decision point come from lab.h macro_feat. Points are sampled uniformly (no selection bias).
// usage: node exit_lab.js out.jsonl [points=600] [workers=6] [seed=1]
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v1_0_1.wasm");
const LAB = path.join(ROOT, "v3", "bots", "a2c_mlab", ".cambc", "build-release", "bot-injected.wasm");
const OPPS = { nb1: path.join(ROOT, "v3", "bots", "sb_nb1_c1", ".cambc", "build-release", "bot-injected.wasm"),
  ext: path.join(ROOT, "v3", "bots", "sb_ext_c1", ".cambc", "build-release", "bot-injected.wasm") };
const HORIZON = 150;
const OPTIONS = [["keep", -1, 0], ["forbid", 1, 25], ["bank", 2, 12], ["hold", 3, 30], ["regroup", 6, 12], ["home", 7, 15]];

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => play(job)); });
  async function play(job) {
    const ex = H.ex, ci = H.arena + 2048, o = H.arena + 2300, ab = H.arena + 2200;
    const P = () => H.E.persp(2, 0xffffffff);
    const teamOf = (h) => (ex.Game_API_Champion_Get(H.g, P(), h, ci) === 0 ? H.m.getInt32(ci, true) : -1);
    const margin = () => {
      const tot = [0, 0];
      for (let t = 0; t < 2; t++) if (ex.Game_API_GetSubmittedGemCount(H.g, t, o) === 0) tot[t] += H.m.getUint32(o, true);
      for (let h = 0; h < 12; h++) {
        const t = teamOf(h);
        if (t < 0) continue;
        if (ex.Game_API_Champion_GetGems(H.g, P(), h, o) === 0) tot[t] += H.m.getUint32(o, true);
        if (ex.Game_API_Champion_IsAlive(H.g, h, ab) === 0 && H.m.getUint8(ab)) tot[t] += 40;
      }
      return tot[0] - tot[1];
    };
    H.labCtl = { champ: job.champ, round: job.round, kind: job.kind, len: job.len };
    H.labRead = null; H.macroRead = null;
    let score = null, feats = null, rec = null, team = -1;
    const hooks = {
      afterTurn: (round) => {
        if (round >= job.round + HORIZON) {
          score = margin(); team = teamOf(job.champ);
          if (H.macroRead) feats = H.macroRead();
          if (H.labRead) rec = H.labRead();
          return true;
        }
        return false;
      },
    };
    let r;
    try { r = await H.play(LAB, OPPS[job.opp], job.map, job.round + HORIZON + 5, null, hooks); } catch (e) { r = { error: String(e) }; }
    H.labCtl = null;
    parentPort.postMessage({ id: job.id, score, feats, applied: rec ? rec[9] >= 0 : false, team, error: r.error || r.abort });
  }
  return;
}

const [outFile, pointsS, workersS, seedS] = process.argv.slice(2);
const NPTS = +(pointsS || 600), NW = Math.min(8, +(workersS || 6));
let seed = +(seedS || 1) * 7919;
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);
const dirs = [[path.join(ROOT, "v3", "maps_new"), 120], [path.join(ROOT, "v3", "maps"), 35]];
const maps = dirs.flatMap(([d, n]) => fs.readdirSync(d).filter((f) => f.endsWith(".map26a")).sort().slice(0, n).map((f) => path.join(d, f)));
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
  let done = 0, kept = 0;
  const points = Array.from({ length: NPTS }, () => ({ map: maps[Math.floor(rnd() * maps.length)], round: 60 + Math.floor(rnd() * 740), champ: Math.floor(rnd() * 3), opp: rnd() < 0.7 ? "nb1" : "ext" }));
  await Promise.all(points.map(async (pt) => {
    const rs = await Promise.all(OPTIONS.map(([, kind, len]) => run({ ...pt, kind, len })));
    const base = rs[0];
    done++;
    if (base.score === null || !base.feats || base.feats[20] < 0 || base.team !== 0) return;
    const rec = { map: path.basename(pt.map), round: pt.round, champ: pt.champ, opp: pt.opp, feats: base.feats.slice(0, 20), base: base.score, gain: {}, applied: {} };
    OPTIONS.slice(1).forEach(([name], i) => { const r = rs[i + 1]; if (r.score !== null) { rec.gain[name] = r.score - base.score; rec.applied[name] = r.applied; } });
    fs.appendFileSync(outFile, JSON.stringify(rec) + "\n");
    kept++;
    if (done % 50 === 0) console.log(`${done}/${NPTS} points (${kept} usable), ${((Date.now() - t0) / 60000).toFixed(1)} min, errors ${errors}, memory ${(process.memoryUsage().rss / 1e6).toFixed(0)} MB`);
  }));
  const rows = fs.readFileSync(outFile, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l));
  for (const [name] of OPTIONS.slice(1)) {
    const g = rows.filter((r) => r.applied[name]).map((r) => r.gain[name]);
    const m = g.reduce((a, b) => a + b, 0) / Math.max(1, g.length);
    console.log(`  ${name.padEnd(8)} applied ${g.length}/${rows.length}, mean gain ${m.toFixed(1)}, better ${g.filter((x) => x > 0).length}, worse ${g.filter((x) => x < 0).length}`);
  }
  for (const s of slots) if (s.w) s.w.terminate();
})();
