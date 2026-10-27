// Turn order in the engine around the micro lab's start round: which champions (team, draft order) act, in order,
// in rounds 3-5 of one game. Shows who has already acted when micro_lab.js captures its start state.
// usage: node order_probe.js [map]
const fs = require("fs");
const path = require("path");
const { Host } = require(path.join(__dirname, "host.js"));
const ROOT = path.join(__dirname, "..", "..");
const BOT = path.join(ROOT, "bots", process.env.DUEL_BOT || "a2c_combo", ".cambc", "build-release", "bot-injected.wasm");
const MAPS = path.join(ROOT, "maps_rdev");
const map = process.argv[2] || fs.readdirSync(MAPS).filter((f) => f.endsWith(".map26a")).sort()[0];
(async () => {
  const H = new Host();
  const team = (h) => {
    const info = H.arena + 2048;
    return H.ex.Game_API_Champion_Get(H.g, H.E.persp(2, 0xffffffff), h, info) === 0 ? H.m.getInt32(info, true) : -1;
  };
  const seq = [];
  await H.play(BOT, BOT, path.join(MAPS, map), 6, null, {
    afterTurn: (round, champ) => { if (round >= 3 && round <= 5) seq.push(`r${round}:T${team(champ)}h${champ}`); return round > 5; },
  });
  console.log(map);
  for (let r = 3; r <= 5; r++) console.log(seq.filter((s) => s.startsWith(`r${r}:`)).map((s) => s.slice(3)).join(" "));
})();
