# Handover: Agent 2, cambc 4.0.0 / engine 2.0.0 (27 Oct 2026)

Everything Agent 2 built and learned from v59 to E76, where it is, how to run it, and what to do next. The older
`HANDOFF.md` in this folder covers the v34 era (engine 1.x) and is history only.

## 1. Status in one paragraph

The best Agent 2 bot is **v61** (`v4/bots/v61`, packaged `v4/submissions/v61_engine4.zip`, not submitted by us):
55.0% ± 2.7 against the team's v60 dev (bot 5) over 340 real-engine games. Since then, 76 experiments (E56–E76:
tuning, precompute, schedule, specialist plans, 79 extra knobs, raids, imitation, gang kills, packs, rushes, learned
fight and strategy models) found **nothing that beats v61 / m62 by more than noise against v61 and bot 5**. The team's
own branch shows the same about the ladder: **v65** (platform 65 = v58 + a 48-knob vector) is their best against the
top 12 at 24 / 120, and every local gain since (v66a +52 locally) was flat or negative on the ladder. The gap to the
top teams is fighting and productive survival, which a lab that only plays our own bot family cannot measure.

## 2. Where everything is

| What | Path |
|---|---|
| Experiment log (E1–E76, read the E56+ entries first) | `agent2/EXPERIMENTS.md` |
| Platform loss analysis (11 games) | `agent2/MATCH_ANALYSIS_E63.md` |
| Research report: MOBA AI, competition bots, training methods, code and strategy audit | `reports/MOBA AI techniques for CAMBC.md` (notes in `research_notes/MOBA AI techniques for CAMBC/`) |
| Lab knob table (slots 0–142) | `agent2/KNOBS.md` |
| Engine 2.0.0 findings, plan, lab interfaces | `agent2/FINDINGS.md`, `agent2/PLAN_v4.md`, `agent2/INTERFACES.md` |
| Game rules (older, still mostly right; 4.0.0 item facts in E73) | `v3/GameRules.md`; SDK `v4/sdk/cpp/cambc.h` |
| Workspace (cambc 4.0.0) | `v4/` (`cambc.exe`, `cambc.toml`, `bots/`, `maps*/`, `submissions/`) |
| Best bot / control / development source | `v4/bots/v61` / `v4/bots/p63b` (= m62 family) / `v4/bots/p65` (all switches, see 5) |
| Precompute-all-game source | `v4/bots/p64` (A2_MP_LATE, E66) |
| Fixed opponents for testing (fresh seed 3) | `v4/bots/v61_c3`, `v4/bots/b5_c3` (training seeds `_c1`, `_c2`) |
| Platform loss replays (20 distinct games) | zips in `Downloads/match-group-*.zip`, extracted to `platform_matches/<group>/<game>/`, decoded to `platform_matches/dec/` |
| Top-team ladder replays (engine 1.x, 517 games) | `replays_db/` (`dec/`, `act/`, `raw/`); lab decodes of our bot `replays_db/dec_lab_p63b/` |
| Map suites | `v4/maps` (70 official), `v4/maps_test4` (held out), `v4/maps_new4` (training), `v4/maps_maze`, `v4/maps_mazetest` (held out) |
| Memory notes (one fact each) | `C:\Users\Iniya\.claude\projects\C--Users-Iniya-Videos-Default-Project-2\memory\` |
| GitHub | `Infosuii/neural-networkk-battlecode`, branch `agent2/v61-findings`, PR #2 (this work); team branch `claude/compare-fix-replay-decoder` (v59–v67, proxy, mimic, 502-loss audit) |

## 3. How to build and test

All from the project root in Git Bash unless noted.

```bash
cd v4 && python mkvar.py p65 mybot A2_RAID=3 && ./cambc.exe build bots/mybot --release
```

`mkvar.py SRC NAME DEF=V ...` copies a bot and overrides `#define`s in `src/common.h`. The lab plays
`bots/<name>/.cambc/build-release/bot-injected.wasm`.

```bash
SETS="v4/maps:25:0 v4/maps_mazetest:25:0" bash agent2/lab/h2h_set.sh mybot 25 4
```

200 games against v61_c3 and b5_c3, both sides (about 1 minute on 4 workers). The control **p63b scores 53.5%** on this
exact set; p65 with every switch off replays it exactly. 100-game sets: `SETS="v4/maps:13:0 v4/maps_mazetest:12:0"`
(control 57.0). Judge anything under ±4 points on 200 games as noise.

Long searches run under the RAM watchdog, from the **PowerShell tool / Terminal panel** (Bash-launched PowerShell has
scripts disabled): `& .\agent2\lab\run_guarded.ps1 -Script agent2\lab\knob_rot.js -Log out.log -Args2 "..."`.
GitHub (`git push`, `gh`) only works from the Terminal panel (`-c credential.helper="!gh auth git-credential"`).

### Lab tools (`agent2/lab/`, engine host `host.js`, env `ENGWASM=tools/viz/v2_0_0.wasm BOTS_DIR=v4/bots`)

| Tool | Use |
|---|---|
| `lab_h2h.js A B MAPDIR [n] [workers]` | Head-to-head. Env: `H2H_PER_MAP`, `H2H_KNOBS` (knob vector for A), `H2H_BOOST=g` (B gets g gold a turn), `H2H_GIFT=round:gold:gems` (A gets a one-off gift), `H2H_KILL=round:n` (n enemies die, credited to A), `H2H_MACROW` |
| `h2h_set.sh A [n] [workers]` | The standard set above (`SETS=` overrides) |
| `knob_rot.js`, `knob_ctx.js` | Evolution-strategy knob search (block / map-conditioned); E56, E63, E66 show their gains do not hold out |
| `early_stats.js BOT OPP MAPDIR N` | Deaths, banked, carried, stats per team at rounds 100 / 200 / 400 |
| `mode_stats.js`, `raid_stats.js` | Mode before death (build with `A2_MODELOG`), raid events (`A2_RAIDLOG`) |
| `dec_lab.js BOT OPP OUT` | Lab games written in the replay-decode format (17 mapinfo maps) |
| `platform_decode.js OUT replay...` | Platform replays to per-round JSON (positions, hp, stats, gems, gold, banked, items) |
| `fight_cf4.js`, `macro_es.js`, `sched_diag.js`, `item_champ.js` | Fight counterfactuals (E69), strategy switcher RL (E70), opening schedule diagnostics, per-champion items |
| `run_guarded.ps1` | RAM watchdog (kills the job under 2 GB free) |

Analysis (`tools/`): `platform_study.py` and `platform_farm.py` (E75), `next_camp.py` (E72 next-camp choice model).

## 4. What the measurements say (the important numbers)

- **Resources snowball (E73):** one-off gifts on the same 200 games (control 53.5): +150 gold per champion at
  round 100 → 84.5, +300 → 97.5, +30 gems → 67.0; one free kill at round 100 → 71.0, two → 80.5. An early lead of one
  kill or about 100 gold per champion decides most games.
- **How the platform winners beat us (E75, 20 games, rounds 0–300):** gems gained 262 vs 134, banked by round 300 191
  vs 80, kills 3.4 vs 1.9. Same time at camps and the same number of captures early, but 19.6 vs 11.6 gems per capture
  (we split big groups). Decisive games: an early fight where they arrive with 4–6 champions at full health.
  Team audit of 502 top-team losses (team branch): per loss they earn 7,173 gold vs 3,657, die 3.7 times vs 13.5,
  kill 11.7 vs 2.9.
- **What the lab says against v61 / b5:** spreading out to farm is the best response; everything that concentrates the
  team costs more farming than it gains (packs 9.8–46%, jackpot 37–43.5%, late pack 7–33%, rush 37.5–48.5%).

## 5. Switches added in p65 (all off by default; results on the 200-game set unless noted)

| Switch | Idea | Result |
|---|---|---|
| `A2_RAID` 1/2/4/8/16/32 | ward the enemy's banking altar, answer long tributes, prelock, carrier hunt, lock-only, lock first | 48–55 (100 games, control 57) |
| `A2_TOPFIX`, `A2_TF_K` | camp choice shifted toward the top teams' (next-camp logit) | 16–57, both directions lose |
| `A2_GANG` | converge on an isolated, quickly killable enemy | 46–50 (probe), unchanged kills |
| `A2_LANCH` | leave when the enemies' health × damage is k times ours | 49.8–53.5 |
| `A2_PACK` 1/2, `A2_PACK_UNTIL` | team / pairs work the leader's group | 9.8–46.2 |
| `A2_JACKPOT` | whole team on the map's biggest group early | 37.0–43.5 |
| `A2_RUSH_FROM`, `A2_RUSH_LEAD`, `A2_RUSH_ITEMS` | late pack-and-attack | 7.0–32.5 |
| `A2_MP_LATE` (p64) | draft precompute used all game + schedule knobs | 51.7–52.4 vs 52.5 |

Existing switches re-tested on engine 2.0 (E73): `APEX_STAND2` 25.5, `NOVA_FLEE_HIT` 53.5, `APEX_ESCAPE_SEARCH` 55.5,
`NOVA_EARLY_SAFE_UNTIL 200` 55.5, `UB_GOLD_UNTIL 600` 57.0.

## 6. Do not retry (against v61 / b5)

Knob searches of any kind (gains vanish on fresh seeds: best-of-many noise is about +9 points on 200 games), the draft
precompute or opening schedule, specialist plans, altar raids / carrier hunts / prelock, imitation of top-team camp
choice, packs / pairs / jackpots / rushes at any stage, standing to fight when caught, learned fight / flee / strategy
models from lab data. Each has a logged null or loss.

## 7. Next steps for large gains (in order)

1. **Measure where the gap is: the ladder-duel set, not self-play.** The team's `research/v59/duel_top1.json` (12 top
   teams × 2 groups × 5 maps, fixed maps and sides, paired, deterministic) is the only measurement that has predicted the
   ladder. Every candidate must pass it. Local self-play only screens for regressions.
2. **Rewrite the fight controller (the real gap: 14.9 deaths vs 5.1, 3.6 kills vs 13.6 against the top 12).** The team's
   `research/v62/BIG_STRATEGIES.md` section 4 has a rulebook measured from 1,317 top-team engagements; `research/proxy`
   has the top teams' measured fight style (back off 0.26 vs our 0.39 in contact, focus 0.32 vs 0.25, enter contact
   with more friends 0.64 vs 0.55). Replace the ~1,000-line `handle_enemies` with one controller and judge it on the
   duel set.
3. **Earlier combat stats.** None of 502 champion appearances in the audited losses bought a Bruiser shard by round
   300; the winners' opening (Treasure + Jungle, then Bruiser / Power) gave +33 locally as `V66_ITEMS 1`. Combine it with
   the fight controller (stats only pay if the fights are won).
4. **Stop splitting big captures.** We get 11.6 gems per capture against their 19.6 on the same groups because two of
   ours share big groups; one owner per reward (the mimic's rule: nearest visible ally owns it) is a cheap fix to test.
5. **The meta compiler (team report):** crawl top-vs-top games daily, fit small decision models (draft, items, opening
   route, engage / leave, target, bank) and compile them to tables. The mimic bot (`bots/mimic`, team branch) is the
   start of this; it also gives a better sparring partner than our own bot family.
6. **Submit candidates to platform match groups** to measure directly. Packaged and untested on the platform:
   `v4/submissions/p64_engine4.zip`, `p63sq3_engine4.zip`, `p63sq1_engine4.zip`.

## 8. Rules of the workspace

Don't modify `cambc.exe`; keep v34 frozen; never put credentials in files; push or submit only when the user asks;
one heavy lab job at a time with at least 2 GB free (watchdog); 100+ games per screening, 200+ to adopt, confirm on
fresh seeds; no engine reverse-engineering for exploits.
