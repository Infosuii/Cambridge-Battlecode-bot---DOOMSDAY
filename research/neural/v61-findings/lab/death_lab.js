// Engine lab, death what-ifs: which response before one of our deaths pays off? The combo lab build (team A) plays an
// opponent bot on official maps in the host (deterministic). Pass 1 records when our champions die. Pass 2 replays the
// identical game and, LEAD rounds before a death, the dying champion is made to run (lab kind 5), regroup with the
// nearest ally (6), walk home (7) or fight (4) for LEN rounds. Value: team gem margin (banked + carried, ours - theirs)
// HORIZON rounds after the death, against the untouched game; also whether that champion still died near that round.
// usage: node death_lab.js out.jsonl [opp=sparexp] [games=34] [deathsPerGame=3] [workers=3]
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
const LAB = path.join(ROOT, "bots", "a2c_lab", ".cambc", "build-release", "bot-injected.wasm");
const MAPS = path.join(ROOT, "maps");
const HORIZON = 100;
const ACTIONS = [["run", 5, 10], ["regroup", 6, 10], ["home", 7, 15], ["fight", 4, 10]];
const LEADS = [3, 8];

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => runJob(job).then((r) => parentPort.postMessage(r), (e) => parentPort.postMessage({ id: job.id, error: String(e) }))); });
  async function runJob(job) {
    const ex = H.ex, ci = H.arena + 2048, o = H.arena + 2300, ab = H.arena + 2200;
    const P = () => H.E.persp(2, 0xffffffff);
    const teamOf = (h) => (ex.Game_API_Champion_Get(H.g, P(), h, ci) === 0 ? H.m.getInt32(ci, true) : -1);
    const alive = (h) => ex.Game_API_Champion_IsAlive(H.g, h, ab) === 0 && H.m.getUint8(ab) !== 0;
    const margin = () => {
      const tot = [0, 0];
      for (let t = 0; t < 2; t++) if (ex.Game_API_GetSubmittedGemCount(H.g, t, o) === 0) tot[t] += H.m.getUint32(o, true);
      for (let h = 0; h < 12; h++) {
        const t = teamOf(h);
        if (t < 0) continue;
        if (ex.Game_API_Champion_GetGems(H.g, P(), h, o) === 0) tot[t] += H.m.getUint32(o, true);
      }
      return tot[0] - tot[1];
    };
    H.labCtl = job.kind ? { champ: job.champ, round: job.round, kind: job.kind, len: job.len } : null;
    const deaths = [], wasAlive = {};
    let score = null, diedNear = false, ended = null;
    const hooks = {
      afterTurn: (round, champ) => {
        if (job.find) {
          for (let h = 0; h < 12; h++) {
            if (teamOf(h) !== 0) continue;
            const a = alive(h);
            if (wasAlive[h] && !a) deaths.push({ champ: h, round });
            wasAlive[h] = a;
          }
          return false;
        }
        if (job.champ !== undefined && round >= job.round && round <= job.death + 5 && !alive(job.champ)) diedNear = true;
        if (round >= job.death + HORIZON) { score = margin(); return true; }
        return false;
      },
      final: () => { ended = margin(); return null; },
    };
    const r = await H.play(LAB, job.opp, path.join(MAPS, job.map), job.find ? 2000 : job.death + HORIZON + 5, null, hooks);
    H.labCtl = null;
    return { id: job.id, deaths, score: score !== null ? score : ended, diedNear, rounds: r.round };
  }
  return;
}

const [outFile, oppS, gamesS, perS, workersS] = process.argv.slice(2);
const OPP = path.join(ROOT, "bots", `sb_${oppS || "sparexp"}_b1`, ".cambc", "build-release", "bot-injected.wasm");
const NG = +(gamesS || 34), PER = +(perS || 3), NW = Math.min(4, +(workersS || 3));
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
  const games = Array.from({ length: NG }, (_, i) => maps[i % maps.length]);
  let done = 0;
  await Promise.all(games.map(async (map) => {
    const found = await run({ map, opp: OPP, find: true });
    if (found.error) { console.log("error", found.error); return; }
    // Deaths after the opening, spread over the game: every k-th one.
    const ds = found.deaths.filter((d) => d.round >= 40 && d.round + HORIZON < found.rounds);
    const step = Math.max(1, Math.floor(ds.length / PER));
    for (const d of ds.filter((_, i) => i % step === 0).slice(0, PER)) {
      const base = await run({ map, opp: OPP, champ: d.champ, round: 0, death: d.round, kind: 0 });
      const rec = { map, champ: d.champ, death: d.round, base: base.score };
      await Promise.all(LEADS.flatMap((lead) => ACTIONS.map(async ([name, kind, len]) => {
        const r = await run({ map, opp: OPP, champ: d.champ, round: d.round - lead, death: d.round, kind, len });
        rec[`${name}@${lead}`] = { d: r.score - base.score, died: r.diedNear };
      })));
      fs.appendFileSync(outFile, JSON.stringify(rec) + "\n");
      if (++done % 10 === 0) console.log(`${done} deaths, memory ${(process.memoryUsage().rss / 1e6).toFixed(0)} MB`);
    }
  }));
  const rows = fs.readFileSync(outFile, "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l));
  const mean = (a) => a.reduce((x, y) => x + y, 0) / Math.max(1, a.length);
  const se = (a) => { const m = mean(a); return Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / Math.max(1, a.length - 1) / Math.max(1, a.length)); };
  console.log(`${rows.length} deaths (combo vs ${oppS || "sparexp"}); gem margin ${HORIZON} rounds after the death vs the untouched game`);
  for (const lead of LEADS)
    for (const [name] of ACTIONS) {
      const k = `${name}@${lead}`, a = rows.filter((r) => r[k]).map((r) => r[k].d);
      const avoided = rows.filter((r) => r[k] && !r[k].died).length;
      console.log(`  ${k.padEnd(11)} margin change ${mean(a).toFixed(1).padStart(6)} +- ${se(a).toFixed(1)} | better ${a.filter((x) => x > 0).length}, worse ${a.filter((x) => x < 0).length} | death avoided ${avoided}/${a.length}`);
    }
  for (const s of slots) if (s.w) s.w.terminate();
})();
