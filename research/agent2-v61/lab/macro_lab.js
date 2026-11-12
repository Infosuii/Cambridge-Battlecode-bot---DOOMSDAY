// Engine lab, macro: are the bot's camp choices and bank timing right? Real bot games in the host (deterministic, so
// every variant is identical up to round R). At round R one champion (lab build, lab.h) either keeps its choices
// (recorded), is barred from its current camp target for 20 rounds (it takes its next choice), banks now, or holds
// its bag for 30 rounds. Team gems (banked + carried) 150 rounds later against the untouched game is the value.
// usage: node macro_lab.js out.jsonl states [seed=1] [workers=3]
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
const LAB = path.join(ROOT, "bots", "a2c_lab", ".cambc", "build-release", "bot-injected.wasm");
const MAPS = path.join(ROOT, "maps_rdev");
const HORIZON = 150;
const KINDS = [["forbid", 1, 20], ["bank", 2, 12], ["hold", 3, 30]]; // each against its own record-only baseline (-kind)

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => runJob(job).then((r) => parentPort.postMessage(r), (e) => parentPort.postMessage({ id: job.id, error: String(e) }))); });
  async function runJob(job) {
    const ex = H.ex;
    H.labCtl = { champ: job.champ, round: job.round, kind: job.kind, len: job.len };
    H.labRead = null;
    let rec = null, snap = null;
    const totals = () => {
        const tot = [0, 0], ci = H.arena + 2048, o = H.arena + 2300;
        for (let t = 0; t < 2; t++) if (ex.Game_API_GetSubmittedGemCount(H.g, t, o) === 0) tot[t] += H.m.getUint32(o, true);
        let team = -1;
        for (let h = 0; h < 8; h++) {
          if (ex.Game_API_Champion_Get(H.g, H.E.persp(2, 0xffffffff), h, ci) !== 0) continue;
          const t = H.m.getInt32(ci, true);
          if (h === job.champ) team = t;
          if (ex.Game_API_Champion_GetGems(H.g, H.E.persp(2, 0xffffffff), h, o) === 0) tot[t] += H.m.getUint32(o, true);
        }
        return { tot, team };
    };
    const hooks = {
      // Score HORIZON rounds after the intervention actually started (rec_round), then stop.
      afterTurn: (round) => {
        if (H.labRead) rec = H.labRead();
        if (rec && rec[9] >= 0 && round >= rec[9] + HORIZON) { snap = totals(); return true; }
        return false;
      },
      final: () => {
        if (snap) return snap;
        const tot = [0, 0], ci = H.arena + 2048, o = H.arena + 2300;
        for (let t = 0; t < 2; t++) if (ex.Game_API_GetSubmittedGemCount(H.g, t, o) === 0) tot[t] += H.m.getUint32(o, true);
        let team = -1;
        for (let h = 0; h < 8; h++) {
          if (ex.Game_API_Champion_Get(H.g, H.E.persp(2, 0xffffffff), h, ci) !== 0) continue;
          const t = H.m.getInt32(ci, true);
          if (h === job.champ) team = t;
          if (ex.Game_API_Champion_GetGems(H.g, H.E.persp(2, 0xffffffff), h, o) === 0) tot[t] += H.m.getUint32(o, true);
        }
        return { tot, team };
      },
    };
    const r = await H.play(LAB, LAB, path.join(MAPS, job.map), job.round + HORIZON + 200, null, hooks);
    H.labCtl = null;
    return { id: job.id, tot: r.final ? r.final.tot : null, team: r.final ? r.final.team : -1, rec, round: r.round };
  }
  return;
}

const [outFile, nS, seedS, workersS] = process.argv.slice(2);
const N = +(nS || 50), NW = Math.min(4, +(workersS || 3));
let seed = +(seedS || 1);
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);
const maps = fs.readdirSync(MAPS).filter((f) => f.endsWith(".map26a")).sort();
const RECYCLE = 40, MAX_RSS = 3e9;
const queue = [];
const slots = Array.from({ length: NW }, () => ({ w: null, games: 0, busy: null }));
function abort(why) { console.log("ABORT:", why); for (const s of slots) if (s.w) s.w.terminate(); process.exit(2); }
function spawn(slot) {
  slot.w = new Worker(__filename); slot.games = 0;
  slot.w.on("message", (m) => { const job = slot.busy; slot.busy = null; job.res(m); if (++slot.games >= RECYCLE) { const old = slot.w; slot.w = null; old.terminate().then(() => { spawn(slot); pump(); }); return; } pump(); });
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
  const states = Array.from({ length: N }, () => ({ map: maps[Math.floor(rnd() * maps.length)], round: 40 + Math.floor(rnd() * 260), champ: Math.floor(rnd() * 8) }));
  let done = 0;
  await Promise.all(states.map(async (s) => {
    const rs = await Promise.all(KINDS.flatMap(([, kind, len]) => [run({ ...s, kind: -kind, len }), run({ ...s, kind, len })]));
    const rec = { ...s };
    KINDS.forEach(([name], i) => {
      const base = rs[2 * i], alt = rs[2 * i + 1];
      if (!base.tot || base.team < 0 || !base.rec || base.rec[9] < 0 || !alt.tot) return;
      const t = base.team, val = (r) => r.tot[t] - r.tot[1 - t];
      rec.team = t;
      rec[name] = { d: val(alt) - val(base), carried: base.rec[6], hp: base.rec[7], target: base.rec[4], dist: base.rec[8], at: base.rec[9], alt: alt.rec ? alt.rec[5] : null };
    });
    if (rec.team === undefined) return;
    fs.appendFileSync(outFile, JSON.stringify(rec) + "\n");
    if (++done % 25 === 0) console.log(`${done} states, memory ${(process.memoryUsage().rss / 1e6).toFixed(0)} MB`);
  }));
  const rows = fs.readFileSync(outFile, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l));
  const mean = (a) => a.reduce((x, y) => x + y, 0) / Math.max(1, a.length);
  const se = (a) => { const m = mean(a); return Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / Math.max(1, a.length - 1) / Math.max(1, a.length)); };
  for (const k of ["forbid", "bank", "hold"]) {
    const a = rows.filter((r) => r[k]).map((r) => r[k].d);
    console.log(`${k}: team gem margin change ${mean(a).toFixed(1)} Â± ${se(a).toFixed(1)} (n ${a.length}); better than the bot in ${a.filter((x) => x > 0).length}, worse in ${a.filter((x) => x < 0).length}`);
  }
  for (const s of slots) if (s.w) s.w.terminate();
})();
