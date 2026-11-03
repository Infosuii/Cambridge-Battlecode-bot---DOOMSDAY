# Lead handover: team DOOMSDAY, CAMBC 2026 (state at 3 Nov 2026, ~22:15 UTC)

Facts only: how the competition and the game work, the code, the tools, everything measured, and the state of the
work. Deeper detail lives in the linked files (all on branch `build/z-plan` unless noted).

---

## 1. Competition and platform

- **Platform:** https://2026a.battlecode.co.uk (Cambridge Battlecode, "CAMBC"). Team **DOOMSDAY**, team id
  `fcf5f666-ea55-4da0-b8d4-97c64bb37236`.
- **Ladder (3 Nov ~14:00 UTC):** DOOMSDAY rank 68, rating 2016 (2,945 matches). Mite 2599, Intercontinental Fish 2568,
  Univardisty of Shingtonwash 2509 at the top; rank 30 ~2173, rank 50 ~2069, rank 70 ~1998. Snapshots:
  `data/ladder/duel/ladder_20261103_p*.json`, `data/ladder/losses48/ladder.json`.
- **Toolchain:** C++ compiled to wasm by the official CLI `cambc` 4.0.0 (`tools/vendor/cambc.exe`), engine 2.0.0.
- **Submissions:** `cambc submit bots/NAME --note ...`. A new upload cancels any other compile still queued. In mode
  "follow newest ready version" each compiled upload becomes live; `cambc submissions activate N` pins a version.
  `cambc submissions list --json` gives createdAt / status / statusAt per version.
- **Match groups (unranked, 5 games):** `cambc match-groups create <teamId> --maps m1,..,m5 --sides a,b,... [--source-group <groupId>]`.
  They always play our **active** version. `--source-group` pins the opponent's bot to the one it ran in that earlier
  group. Quota: **50 groups per rolling hour**, shared with the website.
- **Data:** `cambc ladder --json --page N`, `cambc matches list --team me --kind ranked|unranked --json [--cursor]`
  (also other teams), `cambc matches summary --json -o F <id>` (fast; rate-limited, HTTP 429 with "retry after N
  seconds"), `cambc matches download <id> -o F.zip` (~12 s each; zip with `replay.repl26a` and our team's logs),
  `cambc match-groups download <groupId>` (5 game zips). Match listings do not say which of our versions played.
- **Login:** `cambc login` (browser approval; the session lasts 7 days). Only the PC is logged in.
- **Platform character ids** in listings differ from the SDK enum (`data/ladder/char_ids.json`): 0 Ryth, 1 Vesper Vale,
  2 Vendetta, 3 Cassi + Issac, 5 Prism, 6 Marcella, 7 Willow, 8 Ren, 9 Varg, 10 Tavi, 11 Heart of Ruin.

## 2. The game (engine 2.0.0)

Sources: rules `v3/GameRules.md` (Agent 2 branch), Agent 2's first-principles analysis
(`origin/agent2-neural:research/agent2-neural/docs/game_analysis_2026-11-03.md`), SDK `sdk/cpp/cambc.h`.

- **Teams and maps:** 3-5 champions a side; maps 30x30 to 100x100; 86 maps in the competition pool
  (`maps/ladder-pool`, from `cambc maps`). Map files may hold only the authored half; the engine mirrors by symmetry
  (horizontal / vertical / rotational). A group whose mirror shares a tile with it is one group.
- **Draft:** alternating picks (each side's picks visible); 12 champion choices.
- **Win:** first team to **1,000 tributed (banked) gems**; at round 2,000 the most tributed gems (then lifetime gold,
  then kills). Strong-team games last ~1,200-1,700 rounds (~0.6-0.8 banked gems per round as a team).
- **Camps and groups:** camps sit in groups; kill every monster, then stand on the group's region 5 rounds uncontested;
  the reward is split among allies standing there. Camps hit the nearest champion.

| Camp | Health | Hits for | Range | Gems | Gold | Respawn (rounds) |
|---|---|---|---|---|---|---|
| Gem cluster | 120 | 0 | - | 7 | 0 | 50 |
| Gold cluster | 120 | 0 | - | 0 | 20 | 50 |
| Wolf | 1,350 | 20 | 3 | 4 | 40 | 40 |
| Elk | 2,400 | 60 | 4 | 15 | 90 | 60 |
| Golem | 5,000 | 120 | 4 | 36 | 160 | 80 |
| Monolith | 20,000 | 200 | 5 | 200 | 300 | 150 |

- **Banking:** gems are carried until tributed at an altar; a bag of g gems takes ceil(g/10) turns; a stun, a death or
  an **altar lock** (consumable, 10 gold; 5 basic attacks clear it) cancels it; damage does not.
- **Death:** 60 rounds out; the killer takes **every carried gem plus 100 gold** (`bots/x3/src/common.h` ~2032).
- **Gold and items:** gold from camps (and kills / assists / passive income); spent on the own spawn. Shards cost 30
  gold and add the champion's growth of one stat; 5 shards combine into an emblem with a passive. Families: monster
  (+15% camp damage), power (counts as 6 shards), durability (-10% damage taken), treasure (+10% gold), jungle (-30%
  camp damage taken), home, bruiser (5 of the stat + 1 of each other), tribute, capture (capture 5 -> 3), prospector,
  hunter (+50 gold per kill), skirmish, greed, collectors. Consumables: teleport crystal, altar lock.
- **Snowball (Agent 2, E73, 200 games each, control 53.5%):** +150 gold per champion at round 100 -> 84.5% win;
  +300 -> 97.5%; +30 gems -> 67%; one free kill at round 100 -> 71%; two -> 80.5%; +150 gold at round 400 -> 76.8%.
- **Combat:** melee range 1 (walk and attack), ranged range 3 (walk or attack); one spell per turn, 8-turn cooldowns,
  scaled by focus; fights follow Lanchester's square law (numbers squared). Heart of Ruin up to +50% damage at low
  health; Vendetta resets cooldowns on kills; Marcella is stun-immune.
- **Vision:** 8 tiles, raycast; bushes block from outside; **no shared vision**. Wards: free charges that recharge
  (`bc::constants::ward_cooldown`), an active-ward limit, a lifetime and a vision radius
  (`bc::constants::ward_vision_radius`, `ward_placement_radius`).
- **Shared memory:** 8 bytes during play (claims, sightings, respawn events) + 1,024 bytes written in the draft.
- **Fuel:** counted per wasm instruction; 100k per turn, 10x on the first draft turn, 2x on the first play turn.
  Running out suspends the turn ("fuel-out"; a `fuelExhausted` event with its round in the summary). Host-side calls
  (bitboards, distance fields) are cheap relative to wasm loops.
- **Determinism:** a game is fully determined by (map, side, both binaries). Any compiled change can shift fuel and
  later decisions; a do-nothing code change flipped 4-7 of 172 local games; a behaviour change flips ~40%.

### Champions (2.0.0 changes vs 1.0.3, Agent 2 E115)
Ryth, Vesper Vale, Vendetta, Cassi + Issac (one pick, two bodies sharing fate), Stellar, Prism, Marcella, Willow, Ren,
Varg, Tavi, Heart of Ruin. Nerfed in 2.0.0: Vesper strength 55 -> 45, Marcella growth 5 / 15 -> 4.5 / 14, Heart of
Ruin 3.5 / 12 -> 3 / 10, Ryth strength growth 5 -> 4.5. Buffed: Varg and Issac strength 40 -> 45, Cassi focus 70 -> 100,
Willow focus 120 -> 140, Stellar focus growth 7 -> 8.5, Prism health growth 60 -> 65, Ren and Tavi abilities. Economic
roles: Vesper +33% gold, Marcella +2 gold per gem she banks. Agent 2 self-play pick effects vs v92: Vendetta +10.9,
Varg +7.3, Marcella +6.7, Ren +5.8, Vesper +3.3, Ryth +2.9, Cassi / Issac 0, Heart -1.6, Prism -2.4, Willow -8.8.

## 3. Code and bots

- **Repository:** https://github.com/Infosuii/neural-networkk-battlecode ; local clone
  `C:\projects\cambridge battlecode\work\neural-full-stack`. Working branch **`build/z-plan`**. Helper branches
  `build/z-plan-5060`, `-5070`, `-g3`. Agent 2: `agent2/v61-findings`, `agent2-neural` (auto-synced). GX (separate
  agent): `max/gigabot`. Comms branch `comms/x1` (clone `C:\projects\cambridge battlecode\work\x1-comms`; folders
  `pc/` `g5060/` `g5070/` `g3/` `gmax/`; jobs `pc/jobs/`). Audit: `research/x1-audit-2026-11-02`.
- **v92** (`bots/v92/src`, platform v75 / v80, build 5704d7ba41ac): Agent 2's experiments E79-E89 on the v81hl line.
- **x3** (`bots/x3/src`): the development source. Its default build is **byte-identical to v92** (5704d7ba41ac);
  every experiment is a `#define` in `x1_config.h` / `common.h`, off by default. Some v92 values are forced unguarded
  in `common.h` (`A3_FOCUS 0.0f`, `A3_NUMBERS 0`, `A3_ONE_OWNER 0`, `A3_ITEMS 0`; in portfolio builds `A3_ITEMS 1`).
- **Key places in `bots/x3/src`:** `handle_enemies` (fights, flee, regroup; `bot.cpp` ~3244), `tactical_decide` /
  `tsearch.*` (fight search, uses leftover fuel), camp choice / `route_search` / scoring (~6100-6400), `farm`,
  `tribute_if_needed` (banking), `shop` + `build_for` (items, ~60-300 and ~772), `draft.cpp` (lineups `kLineups`,
  per-map `kNovaMapLineup`, ladder tables v70, `A3_BIG_PICKS`), `world.cpp` (world model, distance fields), shared
  memory claims (`write_claim`, `read_sighting`, `decode_claims`), wards (`ward_ahead`, `ward_reveal`).
- **v92 facts found in the code:** pair farming (`NOVA_DUO 5`) is built but `NOVA_DUO_MAPS 1` turns it off on all
  official maps; the draft uses near-fixed lineups (`A3_BIG_PICKS` Vendetta, Varg, Cassi + Issac, Marcella, Heart of
  Ruin for big teams; Vesper Vale late in most lineups); `A2_LAB 1` forces the learner on despite `NOVA_LEARNER 0`.
- **Other bots:** `x3mf` (v78; 13-map knob table), `x3mf2` (25-map table), `x3ctr` (v77; counter table vs v92),
  `x3ctr3` (v79; counter table vs x3mf), `x3inv` (invader sparring partner), `pf0`..`pf13` (portfolio, one profile
  forced), `v92af`, `v92a3i`, `v92bru`, `v92own`, `v92foc`, `v92num`, `v92fn`, `v92gold`, `v92esc`, `v92safe`
  (v92 + one change), `v92vesper` (winners' draft order), `v92audit` (all audit fixes), plus older lineage bots.

### The map-category / portfolio system (all switches off by default)
- `x1_atlas.h` (`X1_ATLAS`): ~25 map features from the bot's own world model; exact on 86 / 86 maps.
- `x1_categories.h`: 7 categories (generated by `tools/mapatlas/gen_categories.py` from
  `research/x3/atlas/categories_rules.json`); runtime classification matched offline on 28 / 28 games.
- `x1_portfolio.h` (`X1_PORTFOLIO`, `X1_PORTFOLIO_FORCE`): category -> profile at the first turn from round 3 with
  70k fuel left (the analysis costs 12-54k); 14 profiles as volatile data; fields: territory (+ ramp), aggression,
  bank threshold (+ until), hunt, raid, numbers edge, focus fire, antifeed, item plan, vision wards, cohesion, pack
  play, buddy camp weight. Details: `research/x3/MAP_IDEA_FINDINGS.md`.
- `X1_DRAFT_WIN` (`draft.cpp`): draft Vesper Vale, Marcella, Heart of Ruin, Vendetta, Ryth, Tavi, Willow, Cassi +
  Issac, Varg, Ren, Stellar, Prism first on every map (after the mobility draft on gap-crossing maps).

## 4. Tools

| Purpose | Tool |
|---|---|
| Local games | `python tools/dz.py smoke --name RUN --pool --map-dir maps/ladder-pool --opponent BOT --candidate-bot BOT --workers N [--set FLAG=V]` -> `research/dz/runs/RUN/results.json` + `evidence.zip` (all game summaries); wrapper `tools/x1_gate.sh` |
| Ladder duel | `tools/replay/ladder_duel.py plan|run|report|restore`; `tools/replay/duel_pipeline.py --plan P --base 80 --cands ... --recheck NAME` (uploads each candidate before its arm, pins opponents to the base arm's groups, single-instance lock, flags contaminated arms). Plans `research/x3/duel/duel_20261103*.json`, logs `pipeline*.log` |
| Recent losses | `tools/ladder/losses_recent.py`, `summary_profile.py`, `archetypes.py`, `loss_study.py` |
| Replay analysis | `tools/replay/*.mjs` with `NFS_REPLAY_ENGINE=2.0.0`: `winner_profile`, `death_context`, `camp_clear`, `contact_cohesion`, `focus_fire`, `hurt_contact`, `home_trips`, `map_state`, ... |
| Map atlas | `tools/mapatlas/collect.py` (bot's own features), `categorise.py`, `gen_categories.py`, `portfolio_eval.py`, `behaviour_check.py` |
| Process control | stop native Windows processes with PowerShell `Stop-Process`; Git Bash `pkill` does not reach them |

## 5. Findings (with numbers)

### 5.1 Local tests vs the ladder
- Self-play against our own bot family did not predict the ladder: x3mf +30 / 516 and +14 on "held-out" (still our
  family) -> ladder level with v92 (+0.9% +- 6%); counter tables +37 to +89 in sample -> about 0 out of sample
  (left-out-opponent estimates -20 to +3; `research/x3/ANTI_OVERFIT.md`); x3ctr 171 / 172 vs v92 -> ladder +2.0% +-
  2.8% vs v92's period (29 opponents).
- Per-category choice among the 30 counter-search variants did not transfer to unseen maps (-19 to -29 / 688,
  `research/x3/atlas/PORTFOLIO_EXISTING_VARIANTS.md`).
- Agent 2 (`agent2/v61-findings`, HANDOVER): every local self-play gain since v61 was flat or negative on the ladder;
  the only predictive measurement was a paired ladder-duel set.

### 5.2 Ladder record by period (raw, opponent mix differs)
v92 (2 Nov day) 751 / 1290 = 58.2%; v92 (22:23-03:35) 288 / 555 = 51.9%; x3ctr (03:35-10:54) 355 / 645 = 55.0%;
x3mf (11:04-) 108 / 195 = 55.4%. Same-opponent comparisons: all within a few % of v92.

### 5.3 Paired ladder duels
Plan a (12 teams rated 2050-2171, v92 52 / 120): x3mf2 50 (118 / 120 games identical), one owner 50, Bruiser build
44, antifeed 43, A3 items 42.
Plan b / c (the 12 teams rated >= 2000 that beat us most: 0xDEADBEEF, QS2isLaw, an iq too high, we were fed fish,
Shawarma, Nameless, bbas, 剑桥夜爬者, Beehive, will think later, smurphy, EggsAfter11AM; v92 57 / 120):

| Profile | Wins | Notes |
|---|---|---|
| 1 vision (ward + world refresh) | 47 | round-1 fuel bug |
| 2 raid and bank | 47 | round-1 fuel bug |
| 3 stat fighter | 42 | round-1 fuel bug |
| 4 early bank | 57 | round-1 fuel bug |
| 13 pack play (fixed, clean, pinned) | **29** | +4 / -32 games; z -4.7 |
| 4 early bank (fixed, clean, pinned) | **51** | +15 / -21; ahead on C2 / C3 / C7, behind on C1 / C4 / C5 |
| 10 pack opening | running at handover | |

Arms played 19:10-20:40 UTC on 3 Nov are invalid (a second pipeline uploaded mid-arm; `PLAYBOOK.md` section 10).

### 5.4 How the 2000+ teams beat us (898 losses, 48 h to 3 Nov 15:44 UTC)
`research/x3/losses48/` (ARCHETYPES.md, REPLAY_FINDINGS.md, PLAYBOOK.md), `research/x3/ECONOMY_GAP.md`.
- **Economy:** in losses we fall behind from round ~150-300; gold at round 150 in v92's duel losses 440 vs 591 with no
  deaths yet; solo camp clears 36 vs 47 per game, 22 vs 18 rounds per clear; late game (C1 after round 800) clears
  9.8 vs 22.5, own-half time 0.92 vs 0.68.
- **Draft:** winners pick **Vesper Vale in 66-84%** of games in every category (we 0-53%), also Ryth and Tavi more;
  we pick Vendetta 100%, Varg (C5 87% vs 14%), Cassi + Issac (46-80% vs 15-38%).
- **Vision:** 2-3x our wards in every category. **Banking:** first deposit 50-290 rounds earlier, 1.4-2.9x more
  deposits. **Items:** Bruiser 3-10 shards by round 300 (us 0), Treasure opening ~30% (us 0%); we buy ~2x the
  teleport crystals.
- **Movement (replays):** grouped 68% vs 57% early, 1.72 vs 1.44 champions per camp, 2.1 vs 1.7 allies at first
  contact, own-half time 0.83 -> 0.70 over the game (ours 0.86 -> 0.83), 20-30% more recalls.
- **Nine archetypes (overlapping):** our-half killers 244, Treasure openers 163, raiders 126, contested farmers 122,
  pacifist racers 80, Bruiser openers 64, hoarders 54, early brawlers 32, Power invaders 13. Teams have house styles
  (top archetype 22-60% of a team's wins).
- **Deaths:** about even (9.8 vs 9.1 per game in v92's duel games), but 46% of our deaths with no hit back (theirs
  36%). Agent 2: v92's duel move is no better than a random legal option in staged duels (E115 C pilot).
- **Example (v78 vs 剑桥夜爬者, 1:4):** 24-40 deaths vs 1-7 kills per game; our gold flat after round 200.

### 5.5 Map categories (bot features; `research/x3/atlas/CATEGORIES.md`)
C1 18 maps (small, close, fighting camps), C2 4 (small, close, harmless), C3 24 (small, spread, dangerous), C4 13
(small, spread, mixed), C5 21 (large, far), C6 3 (large, rich home), C7 3 (large, harmless). Maps vary continuously
(silhouette ~0.15). In the duels v92 is strongest on C1 and C5.

### 5.6 Defects found on 3 Nov
- Portfolio builds ran the map analysis in round 1: 30 fuel-outs / 28 games vs v92's 6 (24 in round 1); fixed by
  deferring to round >= 3 with 70k fuel left.
- `ward_vision` with a world refresh per ward cost ~10 games on the ladder; vision 2 (spare fuel, no refresh) exists.
- The combo profile (vision light + raid + stat fighter): 452 fuel-outs / 172 games, 46 / 172 vs v92.

### 5.7 The x1 audit (ishanp765, `research/x1-audit-2026-11-02`, diagnosis only)
F01 flee / farm alternation (camp target survives a flee; carriers lost 73 and 42 gems in two traced games); F02 camp
deployment splits between groups (9 of 11 losses behind on collection); F03 collected gems not banked in time (win-now
tests one bag); B01 Heart dash / missing-health absent from the fight forecast; B02 camp danger truncated at 12
members (02the-pack has 48 wolves); B03 prune bound excludes later bonuses; B04 partial siege cache accepted; H01 a
stale respawn event (mod 256) can decode as a future respawn; H02 a claim need not mean the claimant works the group;
C01 some "off" switches do not disable dependent work (`A2_LAB` forces the learner; a neural residual has 321 trained
non-zero weights; the forecast stays on while action search is off). Fix switches in x3: `X1_FLEEFIX` (targeted
F01 + H02), `X1_FLEEDROP` / `X1_FLEEHOLD` (blunt F01; self-play -13 to -20), `X1_TEAMWIN` (F03), `X1_HEARTFIX` (B01),
`X1_SOAK64` (B02), `X1_PRUNEFIX` (B03), `X1_SIEGE_STRICT` (B04), `X1_RESPAWNFIX` (H01).

### 5.8 Agent 2's neural bot (`origin/agent2-neural:research/agent2-neural/`)
Entity encoders + pooling + pointer heads; recorder bot logs 500 features and every action at engine speed; DAgger
imitation of v92: target head 45% on ladder maps / 52.3% pool-like vs v92; target + banking student 43.6% / 54.7%;
fuel ignored (teacher ~2M fuel per turn). PPO from the DAgger teacher against v92 / x1 / x3ctr was running (rollout
wins vs v92 40-65%, no trend after 8 iterations). A pool-like map generator (`mapmake6.js`) made 300 test + 600
training maps matching the pool's distributions.

## 6. State at handover
- **Live:** whichever profile the duel queue is testing (`research/x3/duel/pipeline_c2.log`; plan c); the queue
  restores v80 (v92) at its end. Queue order: pack play (done 29), early bank (done 51), pack opening (running),
  progressive expansion, vision light, 2, 3, 1, 5, 6, 7, 11, 12, v92 re-run.
- **Built, not yet tested on the ladder:** `v92vesper` (5f217ae19dac), `v92audit` (045d77959ec3, all audit fixes).
- **Package sent for local tests elsewhere:** v92, early bank (v99), x3mf2, v92vesper (`candidates_20261103.zip`).
- **Helpers:** 5060 silent since ~02:30 UTC 3 Nov; g3 silent since ~13:00 UTC; 5070 off overnight.
- **Leads not yet tested:** draft by category (Vesper Vale); the audit-fix bundle on the ladder; opponent-style
  detection from early sightings; fight-move quality (Agent 2's duel finding).
