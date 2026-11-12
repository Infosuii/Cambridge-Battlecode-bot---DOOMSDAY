// Raid diagnostics (A2_RAID, E71): a bot built with A2_RAIDLOG and APEX_DENYSTATS plays team 0 against OPP on a map
// slice; counts the raid events it prints (RAIDEV ward / walk / seen / answer / hunt, LOCKUSE, TDENY).
// usage: node raid_stats.js BOT OPP MAPDIR N [SKIP]
const path = require("path"), fs = require("fs");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v2_0_0.wasm");
process.env.LAB_DRAFT_FUEL = process.env.LAB_DRAFT_FUEL || "10000000";
const { Host } = require(path.join(__dirname, "host.js"));
const w = (b) => path.join(ROOT, "v4", "bots", b, ".cambc", "build-release", "bot-injected.wasm");
const [bot, opp, dir, nS, skS] = process.argv.slice(2);
const maps = fs.readdirSync(path.resolve(ROOT, dir)).filter((f) => f.endsWith(".map26a")).sort().slice(+(skS || 0), +(skS || 0) + +nS);
(async () => {
  const H = new Host();
  const ev = {};
  let games = 0, wins = 0, wardGames = 0, bigSeen = 0;
  for (const m of maps) {
    H.stdout = [];
    const r = await H.play(w(bot), w(opp), path.resolve(ROOT, dir, m), 2000, null, {});
    games++, wins += r.gems[0] > r.gems[1] ? 1 : 0;
    const text = H.stdout.filter((s) => s.startsWith("[0/")).map((s) => s.replace(/^\[0\/[^\]]*\] /, "")).join("");
    let warded = false;
    for (const l of text.split("\n")) {
      let x = l.match(/^RAIDEV (\S+)/);
      if (x) { ev[x[1]] = (ev[x[1]] || 0) + 1; if (x[1] === "ward") warded = true; if (x[1] === "seen" && +(l.match(/gems (\d+)/) || [0, 0])[1] >= 40) bigSeen++; continue; }
      x = l.match(/^(LOCKUSE|TDENY)/);
      if (x) ev[x[1]] = (ev[x[1]] || 0) + 1;
    }
    wardGames += warded ? 1 : 0;
  }
  console.log(`${bot} vs ${opp}: ${games} games, wins ${wins}, games with the altar ward placed ${wardGames}`);
  console.log(`  events: ${Object.entries(ev).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k} ${v}`).join(", ")}; tributes seen with 40+ gems ${bigSeen}`);
})();
