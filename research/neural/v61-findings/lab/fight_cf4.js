// Fight / flee / regroup counterfactuals on engine 2.0.0 (E69). Our lab bot (team 0) plays an opponent (v61_c2 or
// b5_c2, half the games with the H2H_BOOST-style gold handicap for them); from a random round R, at the first turn our
// champion c has an enemy within 4 (bot.cpp lab kinds 4 / 5), the game is played four ways from that exact turn
// (the lab is deterministic up to it): the bot's own verdict (recorded with its 24 fight features), forced fight and
// forced run for LEN rounds, and regroup (lab kind 6: walk to the nearest living ally) for LEN rounds.
// Per branch: team gem margin (banked + carried) change over the next H rounds, deaths of both teams in that window,
// and the final result. Rows for fight_fit.py.
// usage: node fight_cf4.js out.jsonl SAMPLES [workers=5] [seed=1]   (env FCF_BOT=p63b, FCF_LEN=5, FCF_H=100)
const { Worker, isMainThread, parentPort } = require("worker_threads");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v2_0_0.wasm");
process.env.LAB_DRAFT_FUEL = process.env.LAB_DRAFT_FUEL || "10000000";
const wasm = (b) => path.join(ROOT, "v4", "bots", b, ".cambc", "build-release", "bot-injected.wasm");
const LEN = +(process.env.FCF_LEN || 5), HZ = +(process.env.FCF_H || 100);

if (!isMainThread) {
  const { Host } = require(path.join(__dirname, "host.js"));
  const H = new Host();
  let chain = Promise.resolve();
  parentPort.on("message", (job) => { chain = chain.then(() => branch(job).then((r) => parentPort.postMessage({ id: job.id, ...r }), (e) => parentPort.postMessage({ id: job.id, error: String(e) }))); });
  // Team totals from the engine (spectator view): banked, carried, living champions.
  function totals() {
    const ex = H.ex, P = H.E.persp(2, 0xffffffff), A = H.arena + 4096;
    const t = [{ bank: 0, carry: 0, alive: 0 }, { bank: 0, carry: 0, alive: 0 }];
    for (const k of [0, 1]) if (ex.Game_API_GetSubmittedGemCount(H.g, k, A) === 0) t[k].bank = H.m.getUint32(A, true);
    for (let h = 0; h < 16; h++) {
      if (ex.Game_API_Champion_Get(H.g, P, h, A) !== 0) continue;
      const team = H.m.getInt32(A, true);
      if (team !== 0 && team !== 1) continue;
      if (ex.Game_API_Champion_IsAlive(H.g, h, A + 64) === 0 && H.m.getInt32(A + 64, true)) t[team].alive++;
      if (ex.Game_API_Champion_GetGems(H.g, P, h, A + 128) === 0) t[team].carry += H.m.getUint32(A + 128, true);
    }
    return t;
  }
  async function branch(job) {
    H.labCtl = { champ: job.champ, team: 0, round: job.round, kind: job.kind, len: LEN };
    H.labRead = null; H.fightRead = null;
    let rec = -1, start = null, end = null, feats = null, deaths = [0, 0], lastAlive = null, lastRound = -1;
    const HS = [10, 25, 50], at = {};
    const hooks = {
      beforeTurn: (round, champ, team) => {
        if (job.boost > 0 && team === 1) { const g = Math.floor(round * job.boost) - Math.floor((round - 1) * job.boost); if (g > 0) H.ex.Game_Sandbox_GiveGold(H.g, champ, g); }
      },
      afterTurn: (round) => {
        if (round === lastRound) return false;
        lastRound = round;
        if (rec < 0 && H.labRead) {
          const v = H.labRead();
          if (v[9] >= 0) { rec = v[9]; start = totals(); lastAlive = [start[0].alive, start[1].alive]; if (H.fightRead) feats = H.fightRead(); }
        }
        if (rec >= 0 && !end) {
          const t = totals();
          for (const k of [0, 1]) { if (t[k].alive < lastAlive[k]) deaths[k] += lastAlive[k] - t[k].alive; lastAlive[k] = t[k].alive; }
          for (const h of HS) if (!at[h] && round >= rec + h) {
            const A = H.arena + 6000, P = H.E.persp(2, 0xffffffff);
            const hp = H.ex.Game_API_Champion_Get(H.g, P, job.champ, A) === 0 ? H.m.getFloat32(A + 16, true) / Math.max(1, H.m.getFloat32(A + 20, true)) : 0;
            at[h] = { m: t[0].bank + t[0].carry - t[1].bank - t[1].carry, deaths: deaths.slice(), hp: +hp.toFixed(3) };
          }
          if (round >= rec + HZ) end = t;
        }
        return false;
      },
    };
    const files = [wasm(job.us), wasm(job.opp)];
    let r;
    try { r = await H.play(files[0], files[1], job.map, 2000, null, hooks); } catch (e) { return { error: String(e) }; }
    H.labCtl = null;
    const fin = r.gems;
    const own = H.labRead ? H.labRead() : null;
    const m = (t) => t[0].bank + t[0].carry - t[1].bank - t[1].carry;
    const m0 = start ? m(start) : 0;
    const hz = {};
    for (const h of HS) if (at[h]) hz[h] = { d: at[h].m - m0, deaths: at[h].deaths, hp: at[h].hp };
    return { rec, recAfter: own ? own[5] : null, feats, hz, d: start && end ? m(end) - m(start) : null, deaths, final: fin, win: fin[0] > fin[1] ? 1 : fin[0] === fin[1] ? 0.5 : 0, error: r.abort || null };
  }
  return;
}

const [outFile, samplesS, workersS, seedS] = process.argv.slice(2);
const NW = Math.min(8, +(workersS || 5));
let seed = +(seedS || 1);
const rnd = () => ((seed = (seed * 1103515245 + 12345) >>> 0) >>> 8) / (1 << 24);
const maps = ["maps_new4", "maps", "maps_maze"].flatMap((d) => fs.readdirSync(path.join(ROOT, "v4", d)).filter((f) => f.endsWith(".map26a")).map((f) => path.join(ROOT, "v4", d, f)));
const US = process.env.FCF_BOT || "p63b";
const queue = [], slots = Array.from({ length: NW }, () => ({ w: null, games: 0, busy: null }));
function spawn(slot) {
  slot.w = new Worker(__filename); slot.games = 0;
  slot.w.on("message", (m) => { const job = slot.busy; slot.busy = null; job.res(m); if (++slot.games >= 40) { const old = slot.w; slot.w = null; old.terminate().then(() => { spawn(slot); pump(); }); return; } pump(); });
  slot.w.on("error", (e) => { console.log("worker error", String(e)); process.exit(2); });
}
function pump() {
  if (process.memoryUsage().rss > 4.5e9) { console.log("ABORT: memory"); process.exit(2); }
  for (const s of slots) { if (!s.w || s.busy || !queue.length) continue; s.busy = queue.shift(); s.w.postMessage(s.busy.job); }
}
let nextId = 0;
const run = (job) => new Promise((res) => { queue.push({ job: { ...job, id: nextId++ }, res }); pump(); });
for (const s of slots) spawn(s);
(async () => {
  const t0 = Date.now(), out = fs.createWriteStream(outFile, { flags: "a" });
  let done = 0, kept = 0;
  const one = async (k) => {
    const base = { map: maps[Math.floor(rnd() * maps.length)], opp: rnd() < 0.5 ? "v61_c2" : "b5_c2", boost: rnd() < 0.5 ? 0.25 : 0, champ: Math.floor(rnd() * 3), us: US };
    const R = 30 + Math.floor(rnd() * 870);
    const own = await run({ ...base, round: R, kind: -4 });
    if (own.error || own.rec < 0 || !own.feats || own.d === null) { done++; return; }
    const br = await Promise.all([4, 5, 6].map((kind) => run({ ...base, round: own.rec, kind })));
    const ok = br.every((b) => !b.error && b.rec === own.rec && b.d !== null);
    if (ok) {
      kept++;
      out.write(JSON.stringify({ map: path.relative(ROOT, base.map), opp: base.opp, boost: base.boost, champ: base.champ, rec: own.rec, own_verdict: own.recAfter, f: own.feats.slice(0, 24),
        d: { own: own.d, fight: br[0].d, run: br[1].d, regroup: br[2].d }, deaths: { own: own.deaths, fight: br[0].deaths, run: br[1].deaths, regroup: br[2].deaths },
        win: { own: own.win, fight: br[0].win, run: br[1].win, regroup: br[2].win },
        hz: { own: own.hz, fight: br[0].hz, run: br[1].hz, regroup: br[2].hz } }) + "\n");
    }
    if (++done % 50 === 0) console.log(`${done}/${samplesS} samples, kept ${kept} | ${((Date.now() - t0) / 60000).toFixed(1)} min`);
  };
  const N = +samplesS;
  let next = 0;
  await Promise.all(Array.from({ length: NW }, async () => { while (next < N) await one(next++); }));
  out.end();
  console.log(`done ${done}, kept ${kept} | ${((Date.now() - t0) / 60000).toFixed(1)} min`);
  for (const s of slots) if (s.w) s.w.terminate();
})();
