// Fight style from engine-2 replays (offline omniscient analysis only; never a bot input). Measures, per champion
// round in contact, what the champion saw and what it did, so a team's fighting can be described and compared with
// a local proxy's: tools/proxy/style_report.py turns the rows into curves.
//
// A round is "in contact" for a champion when an enemy champion is alive within 8 at the start of the round, not
// counting enemies standing on their own spawn (they heal there; nobody fights them). For each such champion round:
//   row = [round, team, type, id, hp% (0-100), maxHealth, gems carried, d (Chebyshev distance to the nearest enemy),
//          foes6 (enemies within 6), friends5 (allies within 5 with at least 40% health, the champion included),
//          hpRatio% (allied health within 6, ours included, over enemy health within 6, x100, capped at 999),
//          reach (enemies within attack range + 1 step: they can be hit this turn without a dash; engine ranges are 3
//          for ranged heroes and 1 for melee, move speed 1), attack (basic attack on an
//          enemy champion), cast (an ability aimed at an enemy champion's tile), camp (attacked a camp),
//          step (own movement against the nearest enemy's start tile: -1 closer, 0 same, +1 further), recall,
//          pick (attack target among enemies in reach: bit0 lowest health fraction, bit1 closest, bit2 lowest health;
//          -1 when no champion attack), shared (another ally hit the same enemy this round: 1/0, -1 no attack),
//          died (first seen dead within the next 5 rounds: 1/0), alone8 (no ally within 8),
//          hitDist (start-of-round distance to the first champion it hit, -1 none), inRange (an enemy already within
//          attack range)]
// Per team: deaths, kills, earned gold proxy (gold gained while alive, summed), submitted gems, rounds alive; and off
// spawn (alive, not within 1 of the own spawn): rounds, rounds below 50% and 30% health, rounds with an ally within 5,
// arrivals at spawn and their summed health fraction (how hurt champions are when they get home).
// Usage: NFS_REPLAY_ENGINE=2.0.0 node tools/proxy/fight_style.mjs <out.jsonl> <replay.repl26a | dir>...
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { engine, PINNED, verifyAssets } from '../replay/engine.mjs';

if (process.env.NFS_REPLAY_ENGINE !== '2.0.0') throw new Error('set NFS_REPLAY_ENGINE=2.0.0 (engine-2 replays only)');
const cache = path.join(os.homedir(), 'AppData/Local/cambc/assets');
const dir = fs.readdirSync(cache).map(p => path.join(cache, p, 'visualiser/assets'))
  .find(p => Object.keys(PINNED).every(k => fs.existsSync(path.join(p, k))));
if (!dir) throw new Error('complete pinned replay assets unavailable');
verifyAssets(dir);
const E = await engine(dir);
const [output, ...inputs] = process.argv.slice(2);
const files = inputs.flatMap(p => fs.statSync(p).isDirectory()
  ? fs.readdirSync(p).filter(f => f.endsWith('.repl26a')).sort().map(f => path.join(p, f)) : [p]);
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
// Ranged champion types (bc::champion_type order): Vesper, Cassi, Stellar, Prism, Willow, Tavi; the rest are melee.
const RANGED = new Set([1, 3, 5, 6, 8, 11]);
const rangeOf = t => RANGED.has(t) ? 3 : 1;
const sink = fs.openSync(output, 'w');
let n = 0;
for (const file of files) {
  E.load(fs.readFileSync(file));
  const { X, check, dv, out, args, tsnap } = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, args, args + 8, args + 16)); const size = dv().getUint32(args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  let lastRound = -1, prev = null, spawns = null, final = null;
  const act = new Map();             // champion -> actions since the last round boundary
  const deathRounds = new Map();     // champion -> rounds at whose boundary it was first seen dead
  const rows = [];
  const team = [0, 1].map(() => ({ deaths: 0, kills: 0, gold: 0, aliveRounds: 0, contactRounds: 0, offSpawn: 0, hurt50: 0,
    hurt30: 0, grouped5: 0, homeArrivals: 0, homeHp: 0 }));
  const emit = (s0, s1) => {
    // s0: state at the start of the round, s1: at its end; act: what each champion did in between.
    const alive = s0.champions.filter(c => c.alive && c.position);
    const hitBy = new Map(); // enemy index -> set of attacker indices this round
    for (const c of alive) for (const t of act.get(c.entity.index)?.hits ?? []) {
      if (!hitBy.has(t)) hitBy.set(t, new Set());
      hitBy.get(t).add(c.entity.index);
    }
    for (const c of alive) {
      const after = s1.champions.find(o => o.entity.index === c.entity.index);
      const foes = alive.filter(o => o.team !== c.team && !spawns[o.team].some(q => cheb(q, o.position) <= 1));
      let near = null, d = 99;
      for (const o of foes) { const k = cheb(o.position, c.position); if (k < d) { d = k; near = o; } }
      if (!near || d > 8) continue;
      team[c.team].contactRounds++;
      const allies = alive.filter(o => o.team === c.team && o !== c);
      const foes6 = foes.filter(o => cheb(o.position, c.position) <= 6);
      const friends5 = 1 + allies.filter(o => cheb(o.position, c.position) <= 5 && o.health >= 0.4 * o.maxHealth).length;
      const hpUs = c.health + allies.filter(o => cheb(o.position, c.position) <= 6).reduce((x, o) => x + o.health, 0);
      const hpThem = foes6.reduce((x, o) => x + o.health, 0);
      const inReach = foes.filter(o => cheb(o.position, c.position) <= rangeOf(c.type) + 1);
      const a = act.get(c.entity.index) ?? {};
      let step = 0;
      if (after?.alive && after.position) step = Math.sign(cheb(after.position, near.position) - d);
      let pick = -1, shared = -1, hitDist = -1;
      if (a.hits?.length) {
        const t = alive.find(o => o.entity.index === a.hits[0]);
        if (t) hitDist = cheb(t.position, c.position);
        if (t && inReach.length) {
          const frac = o => o.health / Math.max(1, o.maxHealth);
          pick = (inReach.every(o => frac(t) <= frac(o)) ? 1 : 0) |
                 (inReach.every(o => cheb(t.position, c.position) <= cheb(o.position, c.position)) ? 2 : 0) |
                 (inReach.every(o => t.health <= o.health) ? 4 : 0);
        }
        shared = [...new Set(a.hits)].some(t => (hitBy.get(t)?.size ?? 0) > 1) ? 1 : 0;
      }
      rows.push([s0.round, c.team, c.type, c.entity.index, Math.round(100 * c.health / Math.max(1, c.maxHealth)), c.maxHealth,
        c.gems, d, foes6.length, friends5, Math.min(999, Math.round(100 * hpUs / Math.max(1, hpThem))), inReach.length,
        a.atk ? 1 : 0, a.cast ? 1 : 0, a.camp ? 1 : 0, step, a.recall ? 1 : 0, pick, shared, -1,
        allies.some(o => cheb(o.position, c.position) <= 8) ? 0 : 1, hitDist, d <= rangeOf(c.type) ? 1 : 0]);
    }
  };
  for (;;) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), kind = d.getUint32(tsnap + 68, true), actor = d.getUint32(tsnap + 76, true);
    const actorKind = d.getUint32(tsnap + 72, true);
    const phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true), pos = d.getUint32(tsnap + 56, true);
    if ((round !== lastRound && phase === 10) || outcome) {
      check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
      const s = E.PC.I(dv(), tsnap);
      s.round = round;
      if (!spawns) {
        // Spawns: where each team's champions stand at the first champion phase.
        spawns = [[], []];
        for (const c of s.champions) if (c.position) spawns[c.team].push(c.position);
      }
      if (prev) {
        emit(prev, s);
        for (const c of s.champions) {
          const p = prev.champions.find(o => o.entity.index === c.entity.index);
          if (!p) continue;
          if (p.alive && !c.alive) { team[c.team].deaths++; (deathRounds.get(c.entity.index) ?? deathRounds.set(c.entity.index, []).get(c.entity.index)).push(round); }
          if (c.kills > p.kills) team[c.team].kills += c.kills - p.kills;
          if (c.alive && p.alive) { team[c.team].aliveRounds++; if (c.gold > p.gold) team[c.team].gold += c.gold - p.gold; }
          if (c.alive && p.alive && c.position && p.position) {
            const T = team[c.team], home = q => spawns[c.team].some(z => cheb(z, q) <= 1);
            if (!home(c.position)) {
              const f = c.health / Math.max(1, c.maxHealth);
              T.offSpawn++; T.hurt50 += f < 0.5; T.hurt30 += f < 0.3;
              T.grouped5 += s.champions.some(o => o !== c && o.team === c.team && o.alive && o.position && cheb(o.position, c.position) <= 5);
            } else if (!home(p.position)) { T.homeArrivals++; T.homeHp += p.health / Math.max(1, p.maxHealth); }
          }
        }
      }
      final = { outcome: s.outcome, submittedGems: s.submittedGems.map(Number), round };
      act.clear();
      prev = s;
      lastRound = round;
    }
    if (actorKind === 1 && prev) {
      const f = act.get(actor) ?? {}; act.set(actor, f);
      if (kind === 5 || kind === 6) {
        const q = { x: d.getInt32(tsnap + 88, true), y: d.getInt32(tsnap + 92, true) };
        // Match the aimed tile against where enemies stand now (they may have moved earlier this round).
        const now = E.PC.I(d, tsnap), me = prev.champions.find(c => c.entity.index === actor);
        const where = c => now.champions.find(o => o.entity.index === c.entity.index)?.position ?? c.position;
        const hit = me && prev.champions.find(c => c.alive && c.position && c.team !== me.team && cheb(where(c), q) <= (kind === 5 ? 0 : 1));
        if (hit) {
          if (kind === 5) { f.atk = 1; (f.hits ??= []).push(hit.entity.index); } else f.cast = 1;
        } else if (kind === 5) f.camp = 1;
      } else if (kind === 11) f.recall = 1;
    }
    if (outcome || (d.getUint32(tsnap + 20, true) !== 0 && pos >= size)) break;
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  // died: the champion is first seen dead at a boundary in (round, round + 5].
  for (const r of rows) r[19] = (deathRounds.get(r[3]) ?? []).some(k => k > r[0] && k <= r[0] + 5) ? 1 : 0;
  fs.writeSync(sink, JSON.stringify({ match: path.basename(file, '.repl26a'), rounds: final.round, outcome: final.outcome,
    submittedGems: final.submittedGems, teams: team, rows }) + '\n');
  E.destroy();
  n++;
}
fs.closeSync(sink);
console.log(JSON.stringify({ replays: n, out: output }));
