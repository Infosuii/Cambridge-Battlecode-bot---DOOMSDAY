// Lab games decoded like replays_db/dec (E72): BOT plays OPP on the 17 maps that mapinfo/ covers, both sides; every round
// the state of all champions (h, team, type, x, y, hp, mhp, gems, alive) is written in the decode format, and the meta
// marks BOT's side "top" so tools/next_camp_data.py reads our choices the same way as the top teams'.
// usage: node dec_lab.js BOT OPP OUTDIR [seedsuffix=c3]   (BOT / OPP: v4/bots folder names)
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v2_0_0.wasm");
process.env.LAB_DRAFT_FUEL = process.env.LAB_DRAFT_FUEL || "10000000";
const { Host } = require(path.join(__dirname, "host.js"));
const w = (b) => path.join(ROOT, "v4", "bots", b, ".cambc", "build-release", "bot-injected.wasm");
const [bot, opp, outDir] = process.argv.slice(2);
fs.mkdirSync(path.resolve(ROOT, outDir), { recursive: true });
const maps = fs.readdirSync(path.join(ROOT, "mapinfo")).filter((f) => f.endsWith(".txt")).map((f) => f.slice(0, -4));
(async () => {
  const H = new Host();
  for (const m of maps) {
    const file = [`${m}.map26a`, `00${m}.map26a`, `01${m}.map26a`, `02${m}.map26a`].map((f) => path.join(ROOT, "v4", "maps", f)).find((f) => fs.existsSync(f)) || "";
    if (!file) { console.log("no map", m); continue; }
    for (const side of [0, 1]) {
      const rounds = [];
      let last = -1;
      const ci = H.arena + 2048, ab = H.arena + 2200;
      const snap = (round) => {
        const ex = H.ex, d = H.m, champs = [];
        for (let h = 0; h < 12; h++) {
          if (ex.Game_API_Champion_Get(H.g, H.E.persp(2, 0xffffffff), h, ci) !== 0) continue;
          const alive = ex.Game_API_Champion_IsAlive(H.g, h, ab) === 0 && d.getUint8(ab) !== 0 ? 1 : 0;
          const gems = ex.Game_API_Champion_GetGems(H.g, H.E.persp(2, 0xffffffff), h, ab) === 0 ? d.getUint32(ab, true) : 0;
          champs.push({ h, team: d.getInt32(ci, true), type: d.getInt32(ci + 4, true), x: alive ? d.getInt32(ci + 8, true) : -1,
            y: alive ? d.getInt32(ci + 12, true) : -1, hp: +d.getFloat32(ci + 16, true).toFixed(0), mhp: +d.getFloat32(ci + 20, true).toFixed(0), gems, alive });
        }
        rounds.push({ round, champs, sub: [-1, -1] });
      };
      const hooks = { beforeTurn: (round) => { if (round !== last) { last = round; snap(round); } } };
      const files = side === 0 ? [w(bot), w(opp)] : [w(opp), w(bot)];
      const r = await H.play(files[0], files[1], file, 2000, null, hooks);
      const id = `${m}__${side}`;
      const meta = { id, map: m, rounds: rounds.length, sides: { [side]: { top: true, result: r.gems[side] > r.gems[1 - side] ? "win" : "loss", name: bot },
        [1 - side]: { top: false, name: opp } }, kind: "lab" };
      fs.writeFileSync(path.resolve(ROOT, outDir, `${id}.json`), JSON.stringify({ rounds }));
      fs.writeFileSync(path.resolve(ROOT, outDir, `${id}.meta.json`), JSON.stringify(meta));
      console.log(id, r.gems.join("-"), rounds.length);
    }
  }
})();
