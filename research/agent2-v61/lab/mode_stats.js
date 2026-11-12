// Mode diagnostics (E65): a bot built with A2_MODELOG plays team 0 against OPP on a map slice; counts the last mode
// before each of our deaths (MODEDEATH) and the modes of hurt champions near enemies (MODEHURT).
// usage: node mode_stats.js BOT OPP MAPDIR N [SKIP]
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
  const death = {}, hurt = {};
  let deaths = 0, games = 0, wins = 0;
  for (const m of maps) {
    H.stdout = [];
    const r = await H.play(w(bot), w(opp), path.resolve(ROOT, dir, m), 2000, null, {});
    games++, wins += r.gems[0] > r.gems[1] ? 1 : 0;
    const text = H.stdout.filter((s) => s.startsWith("[0/")).map((s) => s.replace(/^\[0\/[^\]]*\] /, "")).join("");
    for (const l of text.split("\n")) {
      let x = l.match(/^MODEDEATH r\d+ slot \d+ mode (\S*) hp (\d+)/);
      if (x) { deaths++; death[x[1] || "-"] = (death[x[1] || "-"] || 0) + 1; continue; }
      x = l.match(/^MODEHURT r\d+ slot \d+ mode (\S*)/);
      if (x) hurt[x[1] || "-"] = (hurt[x[1] || "-"] || 0) + 1;
    }
  }
  const top = (o) => Object.entries(o).sort((a, b) => b[1] - a[1]).slice(0, 18).map(([k, v]) => `${k} ${v}`).join(", ");
  console.log(`${bot} vs ${opp}: ${games} games, wins ${wins}, our deaths ${deaths}`);
  console.log(`  last mode before death: ${top(death)}`);
  console.log(`  modes while hurt (<60%) near enemies (turns): ${top(hurt)}`);
})();
