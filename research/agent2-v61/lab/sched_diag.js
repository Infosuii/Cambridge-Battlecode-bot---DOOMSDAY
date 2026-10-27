// Schedule diagnostics (E62): bots built with A2_SCHED_DIAG play team 0 against OPP for 201 rounds on a map list and
// print SCHEDDIAG lines at round 200 (per champion: turns with a live schedule step, turns following it, carried gems
// and gold, team banked gems). Prints per bot: banked gems, carried gems + gold, follow rate.
// usage: node sched_diag.js OPP MAPDIR:N[:SKIP] [MAPDIR:N[:SKIP]..] -- BOT [BOT..]   (bots in v4/bots; LAB_DRAFT_FUEL set)
const path = require("path"), fs = require("fs");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v2_0_0.wasm");
process.env.LAB_DRAFT_FUEL = process.env.LAB_DRAFT_FUEL || "10000000";
const { Host } = require(path.join(__dirname, "host.js"));
const w = (b) => path.join(ROOT, "v4", "bots", b, ".cambc", "build-release", "bot-injected.wasm");
const args = process.argv.slice(2), cut = args.indexOf("--");
const opp = args[0], sets = args.slice(1, cut), bots = args.slice(cut + 1);
const maps = sets.flatMap((s) => { const [d, n, k] = s.split(":"); return fs.readdirSync(path.resolve(ROOT, d)).filter((f) => f.endsWith(".map26a")).sort().slice(+(k || 0), +(k || 0) + +n).map((f) => path.resolve(ROOT, d, f)); });
(async () => {
  const H = new Host();
  for (const b of bots) {
    let banked = 0, carried = 0, steps = 0, follow = 0, games = 0;
    for (const m of maps) {
      H.stdout = [];
      await H.play(w(b), w(opp), m, 201, null, {});
      const text = H.stdout.filter((s) => s.startsWith("[0/")).join("");
      let bk = 0;
      for (const l of text.split("\n")) {
        const r = l.match(/SCHEDDIAG slot \d+ steps (\d+) follow (\d+) gems (-?\d+) gold (-?\d+) banked (\d+)/);
        if (!r) continue;
        steps += +r[1], follow += +r[2], carried += +r[3] + 0.1 * +r[4], bk = Math.max(bk, +r[5]);
      }
      banked += bk, games++;
    }
    console.log(`${b}: ${games} games | banked gems at r200 ${(banked / games).toFixed(1)} | carried gems + 0.1 gold ${(carried / games).toFixed(1)} | schedule follow ${steps ? (100 * follow / steps).toFixed(0) : "-"}% of ${(steps / games).toFixed(0)} step-turns/game`);
  }
})();
