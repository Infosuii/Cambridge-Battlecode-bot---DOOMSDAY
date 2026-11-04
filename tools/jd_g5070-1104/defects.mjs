// Offline replay defect extraction (FEAT-004; omniscient analysis only, never a bot input).
// Usage: NFS_REPLAY_ENGINE=2.0.0 node defects.mjs <out.jsonl> <inner replay>...
// One JSON line per replay with, for both teams: deaths (context of the last 5 alive rounds), contact-round
// histograms (retreat moves with/without a basic attack by distance to the nearest enemy, outnumbered rounds) and
// movement runs out of contact (no-progress windows, A-B-A oscillation, idle runs). defects.py aggregates them.
import fs from 'node:fs';
import path from 'node:path';
import {engine, defaultAssets, verifyAssets} from '../replay/engine.mjs';
if (process.env.NFS_REPLAY_ENGINE !== '2.0.0') throw new Error('Select engine 2.0.0 (NFS_REPLAY_ENGINE=2.0.0)');
const [output, ...files] = process.argv.slice(2);
const assets = defaultAssets(); verifyAssets(assets);
const E = await engine(assets);
const cheb = (a, b) => Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y));
const K_MOVE = 4, K_ATTACK = 5, K_CAST = 6, K_RECALL = 11, K_BANK = 12, K_DEPOSIT = 18;
const NOPROG_W = 8, IDLE_MIN = 10;
const lines = [];
for (const file of files) {
  E.load(fs.readFileSync(file));
  const {X, check, dv, out, tsnap} = E;
  check(X.Game_Visualiser_Timeline_GetMain(E.h, out)); const main = dv().getBigUint64(out, true);
  check(X.Game_Visualiser_Timeline_Info(E.h, main, E.args, E.args + 8, E.args + 16)); const size = dv().getUint32(E.args, true);
  check(X.Game_Visualiser_Timeline_Seek(E.h, main, 0, 0));
  const rounds = []; // per round: {r, ch: [{i,team,type,pos,hp,max,gems,alive}], camps:Set}
  let act = new Map(); // champion index -> {move:[from,to], atk_pvp, atk_camp, cast, bank, recall}
  let lastRound = -1, campTiles = new Set();
  const atkDist = {}; // type -> max pvp attack distance seen
  for (let step = 0; step < 5000000; ++step) {
    check(X.Game_Visualiser_ReadTimelineState(E.h, tsnap));
    const d = dv(), round = d.getUint32(tsnap + 8, true), phase = d.getUint32(tsnap + 24, true), outcome = d.getUint32(tsnap + 28, true);
    if ((round !== lastRound && phase === 10) || outcome) {
      if (rounds.length) rounds[rounds.length - 1].act = act;
      act = new Map();
      const s = E.PC.I(dv(), tsnap);
      campTiles = new Set(s.camps.filter(c => c.position).map(c => c.position.x * 1000 + c.position.y));
      rounds.push({r: round, ch: s.champions.map(c => ({i: c.entity.index, team: c.team, type: c.type, pos: c.position ? {x: c.position.x, y: c.position.y} : null,
        hp: c.health, max: c.maxHealth, gems: c.gems, alive: c.alive})), camps: [...campTiles]});
      lastRound = round;
      if (outcome) break;
    }
    const kind = d.getUint32(tsnap + 68, true), ak = d.getUint32(tsnap + 72, true), sp = d.getUint32(tsnap + 64, true);
    if (ak === 1 && sp === 10) {
      const actor = d.getUint32(tsnap + 76, true);
      const f = act.get(actor) ?? {}; act.set(actor, f);
      const from = {x: d.getInt32(tsnap + 80, true), y: d.getInt32(tsnap + 84, true)}, to = {x: d.getInt32(tsnap + 88, true), y: d.getInt32(tsnap + 92, true)};
      if (kind === K_MOVE) { if (!f.from) f.from = from; f.to = to; f.moves = (f.moves ?? 0) + 1; }
      else if (kind === K_ATTACK) { if (campTiles.has(to.x * 1000 + to.y)) f.camp = 1; else { f.pvp = (f.pvp ?? 0) + 1; f.pvpd = Math.max(f.pvpd ?? 0, cheb(from, to)); } }
      else if (kind === K_CAST) f.cast = 1;
      else if (kind === K_BANK || kind === K_DEPOSIT) f.bank = 1;
      else if (kind === K_RECALL) f.recall = 1;
    }
    if ((d.getUint32(tsnap + 20, true) !== 0 && d.getUint32(tsnap + 56, true) >= size)) { if (rounds.length) rounds[rounds.length - 1].act = act; break; }
    check(X.Game_Visualiser_Timeline_ReplayNext(E.h, 1));
  }
  if (rounds.length && !rounds[rounds.length - 1].act) rounds[rounds.length - 1].act = act;
  // Per-team analysis.
  const ids = [...new Set(rounds.flatMap(R => R.ch.map(c => c.i)))];
  const team = {0: newTeam(), 1: newTeam()};
  const spawn = new Map();
  for (const R of rounds) for (const c of R.ch) if (c.alive && c.pos && !spawn.has(c.i)) spawn.set(c.i, c.pos);
  for (const R of rounds) for (const c of R.ch) { const a = R.act?.get(c.i); if (a?.pvp) atkDist[c.type] = Math.max(atkDist[c.type] ?? 0, a.pvpd); }
  for (const id of ids) {
    const hist = []; // per round view of this champion
    let T = null, type = null;
    for (let k = 0; k < rounds.length; ++k) {
      const R = rounds[k]; const c = R.ch.find(x => x.i === id); if (!c) continue;
      T = c.team; type = c.type;
      const a = R.act?.get(id) ?? {};
      let ne = null, nd = 99, foes5 = 0, friends5 = 1, foes8 = 0;
      if (c.alive && c.pos) for (const o of R.ch) {
        if (!o.alive || !o.pos || o.i === id) continue;
        const dd = cheb(o.pos, c.pos);
        if (o.team !== c.team) { if (dd < nd) nd = dd, ne = o; foes5 += dd <= 5; foes8 += dd <= 8; }
        else friends5 += dd <= 5;
      }
      let retreat = 0;
      if (a.from && a.to && ne && nd <= 5) retreat = cheb(a.to, ne.pos) > cheb(a.from, ne.pos) ? 1 : (cheb(a.to, ne.pos) < cheb(a.from, ne.pos) ? -1 : 0);
      hist.push({r: R.r, alive: c.alive, pos: c.pos, hp: c.hp, max: c.max, gems: c.gems, nd, foes5, friends5, foes8, retreat, a});
    }
    if (T === null) continue;
    const t = team[T];
    const sp0 = spawn.get(id);
    // Deaths.
    for (let k = 1; k < hist.length; ++k) {
      const h = hist[k], p = hist[k - 1];
      if (!(p.alive && !h.alive)) continue;
      const last = hist.slice(Math.max(0, k - 5), k);
      let back = k; while (back < hist.length && !hist[back].alive) back++;
      const pvp = last.reduce((s, x) => s + (x.a.pvp ? 1 : 0), 0);
      let fleeStart = -1; for (let j = last.length - 1; j >= 0 && last[j].retreat === 1; --j) fleeStart = j;
      const fs0 = fleeStart >= 0 ? last[fleeStart] : null;
      const outn = last.some(x => x.nd <= 4 && x.foes5 > x.friends5);
      t.deaths.push({r: p.r, type, gems: p.gems, hp5: last[0].hp / Math.max(1, last[0].max), enemies: p.foes5, allies: p.friends5 - 1, nd: p.nd,
        pvp, camp: last.reduce((s, x) => s + (x.a.camp ? 1 : 0), 0), retreats: last.filter(x => x.retreat === 1).length, flee_len: fleeStart >= 0 ? last.length - fleeStart : 0,
        flee_hp: fs0 ? fs0.hp / Math.max(1, fs0.max) : null, flee_nd: fs0 ? fs0.nd : null, outn: outn ? 1 : 0,
        dead_rounds: back < hist.length ? hist[back].r - h.r : null, far_spawn: sp0 && p.pos ? cheb(sp0, p.pos) : null});
    }
    // Contact rounds: key team|type|nd|retreat|attacked.
    for (const h of hist) {
      if (!h.alive || h.nd > 5) continue;
      const key = `${type}|${h.nd}|${h.retreat}|${h.a.pvp ? 1 : 0}|${h.a.cast ? 1 : 0}`;
      t.contact[key] = (t.contact[key] ?? 0) + 1;
      if (h.nd <= 4) { t.contact_rounds++; if (h.foes5 > h.friends5) t.outn_rounds++; if (h.foes5 >= h.friends5 + 2) t.outn2_rounds++; }
    }
    // Movement out of contact.
    const busy = h => !h.alive || !h.pos || h.nd <= 6 || h.a.pvp || h.a.camp || h.a.cast || h.a.bank || h.a.recall;
    let runStart = -1;
    const flush = (s, e) => { // [s, e) quiet rounds
      if (e - s < 2) return;
      const seg = hist.slice(s, e);
      // A-B-A oscillation.
      for (let j = 2; j < seg.length; ++j) {
        const a0 = seg[j - 2].pos, a1 = seg[j - 1].pos, a2 = seg[j].pos;
        if (a0 && a1 && a2 && a0.x === a2.x && a0.y === a2.y && (a1.x !== a0.x || a1.y !== a0.y)) t.osc_rounds++;
      }
      // No-progress windows (>= 4 moves, net displacement <= 2 over NOPROG_W rounds).
      const flag = new Array(seg.length).fill(0);
      for (let j = 0; j + NOPROG_W <= seg.length; ++j) {
        let mv = 0; for (let q = j; q < j + NOPROG_W; ++q) mv += seg[q].a.moves ? 1 : 0;
        if (mv >= 4 && cheb(seg[j].pos, seg[j + NOPROG_W - 1].pos) <= 2) for (let q = j; q < j + NOPROG_W; ++q) flag[q] = 1;
      }
      let run = 0;
      for (let j = 0; j <= seg.length; ++j) {
        if (j < seg.length && flag[j]) { run++; continue; }
        if (run) { t.noprog_runs++; t.noprog_rounds += run; t.noprog_gems += seg[j - 1].gems; run = 0; }
      }
      // Idle runs (no move, no action) away from the own spawn; split at a camp (waiting for a respawn) or elsewhere.
      let idle = 0, atCamp = 0;
      const campsNow = new Set(rounds.find(R => R.r === seg[0].r)?.camps ?? []);
      for (let j = 0; j <= seg.length; ++j) {
        const h = seg[j];
        const isIdle = h && !h.a.moves && !(sp0 && cheb(sp0, h.pos) <= 3);
        if (isIdle) { idle++; let near = 0; for (const ct of campsNow) { const cx = Math.floor(ct / 1000), cy = ct % 1000; if (Math.max(Math.abs(cx - h.pos.x), Math.abs(cy - h.pos.y)) <= 2) { near = 1; break; } } atCamp += near; continue; }
        if (idle >= IDLE_MIN) { if (atCamp * 2 >= idle) { t.idle_camp_runs++; t.idle_camp_rounds += idle; } else { t.idle_runs++; t.idle_rounds += idle; } }
        idle = 0; atCamp = 0;
      }
      t.quiet_rounds += seg.length;
    };
    for (let k = 0; k <= hist.length; ++k) {
      const q = k < hist.length && !busy(hist[k]);
      if (q && runStart < 0) runStart = k;
      if (!q && runStart >= 0) { flush(runStart, k); runStart = -1; }
    }
    for (const h of hist) if (h.alive) t.alive_rounds++;
  }
  lines.push(JSON.stringify({id: path.basename(file).replace(/\.repl26a$/, ''), rounds: rounds.length ? rounds[rounds.length - 1].r : 0, atk_dist: atkDist, teams: team}));
  E.destroy();
}
fs.writeFileSync(output, lines.join('\n') + '\n');
console.log(JSON.stringify({replays: lines.length, out: output}));

function newTeam() {
  return {deaths: [], contact: {}, contact_rounds: 0, outn_rounds: 0, outn2_rounds: 0, osc_rounds: 0, noprog_runs: 0, noprog_rounds: 0,
    noprog_gems: 0, idle_runs: 0, idle_rounds: 0, idle_camp_runs: 0, idle_camp_rounds: 0, quiet_rounds: 0, alive_rounds: 0};
}
