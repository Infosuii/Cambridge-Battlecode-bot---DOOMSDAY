// Early-game probe (E73): BOT vs OPP on a map slice (both sides); at rounds 100, 200 and 400 records per team the deaths
// so far, banked gems, carried gems and total gold held + spent (champion stats proxy: max health and strength sums).
// Prints the means for BOT's team and the opponent's, and BOT's win rate.
// usage: node early_stats.js BOT OPP MAPDIR N [SKIP]
const path = require("path"), fs = require("fs");
const ROOT = path.join(__dirname, "..", "..");
process.env.ENGWASM = process.env.ENGWASM || path.join(ROOT, "tools", "viz", "v2_0_0.wasm");
process.env.LAB_DRAFT_FUEL = process.env.LAB_DRAFT_FUEL || "10000000";
const { Host } = require(path.join(__dirname, "host.js"));
const w = (b) => path.join(ROOT, "v4", "bots", b, ".cambc", "build-release", "bot-injected.wasm");
const [bot, opp, dir, nS, skS] = process.argv.slice(2);
const maps = fs.readdirSync(path.resolve(ROOT, dir)).filter((f) => f.endsWith(".map26a")).sort().slice(+(skS || 0), +(skS || 0) + +nS);
const MARKS = [100, 200, 400];
(async () => {
  const H = new Host();
  const acc = {}; // acc[mark][us|them] = {deaths, banked, carried, str, hp, n}
  for (const m of MARKS) acc[m] = { us: { deaths: 0, banked: 0, carried: 0, str: 0, hp: 0, n: 0 }, them: { deaths: 0, banked: 0, carried: 0, str: 0, hp: 0, n: 0 } };
  let games = 0, wins = 0;
  for (const m of maps) for (const side of [0, 1]) {
    const deaths = [0, 0], wasAlive = {};
    let last = -1;
    const ci = H.arena + 2048, ab = H.arena + 2200;
    const hooks = {
      beforeTurn: (round) => {
        if (round === last) return;
        last = round;
        const ex = H.ex, d = H.m, st = [{ carried: 0, str: 0, hp: 0 }, { carried: 0, str: 0, hp: 0 }];
        for (let h = 0; h < 12; h++) {
          if (ex.Game_API_Champion_Get(H.g, H.E.persp(2, 0xffffffff), h, ci) !== 0) continue;
          const team = d.getInt32(ci, true);
          const alive = ex.Game_API_Champion_IsAlive(H.g, h, ab) === 0 && d.getUint8(ab) !== 0;
          if (wasAlive[h] && !alive) deaths[team]++;
          wasAlive[h] = alive;
          if (ex.Game_API_Champion_GetGems(H.g, H.E.persp(2, 0xffffffff), h, ab) === 0) st[team].carried += d.getUint32(ab, true);
          st[team].hp += d.getFloat32(ci + 20, true);
          if (ex.Game_API_Champion_Get(H.g, H.E.persp(2, 0xffffffff), h, ci) === 0) st[team].str += d.getFloat32(ci + 24, true);
        }
        if (!MARKS.includes(round)) return;
        for (const t of [0, 1]) {
          const a = acc[round][t === side ? "us" : "them"];
          let banked = 0;
          if (ex.Game_API_GetSubmittedGemCount(H.g, t, H.arena + 2300) === 0) banked = d.getUint32(H.arena + 2300, true);
          a.deaths += deaths[t], a.banked += banked, a.carried += st[t].carried, a.str += st[t].str, a.hp += st[t].hp, a.n++;
        }
      },
    };
    const files = side === 0 ? [w(bot), w(opp)] : [w(opp), w(bot)];
    const r = await H.play(files[0], files[1], path.resolve(ROOT, dir, m), 2000, null, hooks);
    games++, wins += r.gems[side] > r.gems[1 - side] ? 1 : r.gems[side] === r.gems[1 - side] ? 0.5 : 0;
  }
  console.log(`${bot} vs ${opp}: ${games} games, win ${(100 * wins / games).toFixed(1)}%`);
  for (const mk of MARKS) {
    const f = (a) => a.n ? `deaths ${(a.deaths / a.n).toFixed(2)} banked ${(a.banked / a.n).toFixed(0)} carried ${(a.carried / a.n).toFixed(0)} maxhp ${(a.hp / a.n).toFixed(0)} str ${(a.str / a.n).toFixed(0)}` : "-";
    console.log(`  r${mk}: us ${f(acc[mk].us)} | them ${f(acc[mk].them)}`);
  }
})();
