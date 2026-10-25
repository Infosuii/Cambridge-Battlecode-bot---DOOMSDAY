# Build v58: a coordinated team economy that can beat Claudus Maximus

You are working in `C:\projects\cambridge battlecode\work\neural-full-stack` (branch
`claude/compare-fix-replay-decoder`). Build **bots/v58** from **bots/v57**, the live ladder bot (platform version 56).
The goal is a large step, not a tweak: v57 beats the field (~70% against everyone else) but went **1-79 against
Claudus Maximus (rank 4)**. Losing every game to one team means a whole layer of play is missing. That layer is
described below, with the evidence for it, what has already been tried and failed, the architecture to add, and how
to prove it works.

Read first, in this order: `artifacts/claude_ops/V58_CLAUDUS_FINDINGS.md`, `artifacts/claude_ops/V57_BUG_AUDIT.md`,
`artifacts/claude_ops/V55_LADDER_ANALYSIS.md`, `artifacts/claude_ops/V57_FRESH_MAPS.md`, `bots/v57/CHANGES.md`,
`ops/HANDOFF.md` (§3 findings, §12-16), `../../game rules/GameRules.md` (the engine contract).

## 0. Hard rules

1. **Submission is pre-authorised by the user, but only through the release gate (§6.5).** If and only if a frozen
   v58 candidate passes every condition there, submit it once with `tools/vendor/cambc.exe submit bots/v58 --note
   "<≤ 80 chars>"` and record it as §7.6 says. Do not submit anything that misses a condition, do not submit
   intermediate variants, and do not resubmit after a ladder dip without new evidence. Never enter credentials;
   the CLI is already logged in. Do not queue match groups (they spend the team's shared quota) unless the user tells
   you to.
2. Do not modify frozen bots: v48-v57 and `artifacts/baselines/heuristic-v1`. Make v58 with `cp -r bots/v57 bots/v58`
   and delete any copied `.cambc/` folder (a copied CMake cache breaks the build). A `bots/v58` folder may already
   exist as an untracked Claude Code experiment (meta draft + opening pack, both rejected; diff in
   `artifacts/claude_ops/rejected/v58-meta-draft-open-pack-vs-v57.diff`): move it to
   `artifacts/tmp/v58-claude-experiment` first, then copy from v57.
3. Never commit `config/paths.json`. Another agent (Claude Code) works in this same checkout: `git add` only files you
   created or changed, never `git add -A`. Commit and push after every accepted mechanism.
4. Raw replays and downloads stay in `artifacts/local-only/` (git-ignored). Never commit replays.
5. **Holdout discipline.** The 12 registered holdout maps (the `final` partition of
   `evaluation/schedules/map_partitions.json`; run with `HOLDOUT=1 MAPS_OVERRIDE="<those 12 names>" bash
   artifacts/claude_ops/bench3.sh ...`) and the 15 fresh pool maps
   (`bench3_fresh.sh`) are for one final check of a frozen candidate. Never tune on them. The fresh 15 maps have been
   used once each by v55, v56 and v57.
6. **Fuel.** Every champion turn has 100k fuel; fuel-outs cost games (an inert-looking hot-path addition has lost
   games before). Keep new logic out of per-group and per-camp loops in `score_groups` and the movement code;
   compute once per turn, once per N rounds, or once per game, and cache. Report fuel-outs per game for every
   variant (bench summary `fuel exhausted A vs B`). v57 runs at about 1 fuel-out per game.
7. Source files are CRLF. Edit with `tools/patch_text.py` (`patch(path, [(old, new), ...])`, each `old` must occur
   exactly once; it keeps line endings) or restore endings with `tools/eol_like.py`. Bash heredocs in this
   environment turn `\n` inside strings into real newlines; write scripts to files.
8. Every mechanism is a `#define V58_<NAME>` switch in `src/common.h` (`#ifndef` default block, one-line comment), so
   any variant can be built by flipping defines. Keep v57 behaviour exactly when a switch is 0.

## 1. Tools you will use

* Build: `python -c "from pathlib import Path; from nfs import engine; engine.official_build(Path('<bot dir>'), Path('<out>.wasm'))"`
  with `PYTHONPATH=python`. The platform builds the same way (`cambc build --release`, -O3).
* Bench (cached builds, verified and retried shards): `bash artifacts/claude_ops/bench3.sh <abs cand dir> <abs opp dir>
  <abs out prefix> 1 2 3 4` runs 28 development maps × 2 sides × seeds, about 4-5 minutes per 4 seeds.
  `bench3_fresh.sh` (same arguments) uses the fresh 15 maps. `MAPS_OVERRIDE="a b c"` restricts the maps.
* Statistics: `tools/bench_bayes.py <prefix> [<prefix B>]` is a hierarchical Bayesian model (map random effect,
  Student-t noise). ACCEPT when P(>0) ≥ 0.95 and the mean is ≥ 25 gems; REJECT when P(>0) ≤ 0.05.
  `tools/bench_compare.py` gives the map-cluster bootstrap and `tools/bench_maps.py` per-map tables. Inert changes
  swing single maps by ±100 gems and ±4 wins in 12; do not read single maps.
* Replay analysis (offline only, never bot input). Local bench replays are zips: extract `replay.repl26a` first
  (see `tools/replay/ledger_bench.py`, or the snippet in `V58_CLAUDUS_FINDINGS.md`).
  * `tools/replay/ledger_bench.py <bench prefix>`: per-champion economy, candidate against opponent.
  * `actor_ledger.mjs`: capture gold, time allocation and emblem rounds per champion.
  * `capture_funnel.mjs`: who hit each camp group and who captured it.
  * `camp_clear.mjs`: solo clears, own / middle / enemy half.
  * `sanity_audit.mjs`: attacks, casts, idle turns, wards, deaths, bag losses.
  * `respawn_delay.mjs`, `fuel_outs.mjs`, `death_context.mjs`, `hurt_contact.mjs`, `focus_fire.mjs`,
    `still_runs.mjs`, `home_trips.mjs`.
* Ladder data: `tools/replay/fetch_since.py --since <iso> --out <dir>` downloads listings and replays with the
  logged-in CLI (read-only). The 80 Claudus replays are in `artifacts/local-only/v55-ladder/replays`, with ids in
  `artifacts/local-only/v55-ladder/out/claudus_ids.txt`. Our team is `DOOMSDAY`; theirs is `Claudus Maximus`.
* Debug output: `A2_MICLOG 1` makes champions print to stdout. Logs are inside each local replay bundle as
  `team-a.stdout` / `team-b.stdout`.

## 2. The evidence: what Claudus does that we do not

All from the 80 decoded games (medians or per-game means; details in `V58_CLAUDUS_FINDINGS.md`):

1. **One carry.** Draft is always Vesper + Heart of Ruin + Vendetta (+ Ryth or Tavi, + Marcella). Vesper gains +33%
   gold (+53% with the Treasure emblem), completes Treasure at **R88**, and earns 466 capture gold by R250, 1128 by
   R500 and 2829 by R1000. That is 44-49% of the team's gold, with a median of 0 deaths. Our best earner has 185 by
   R250. About a third of Vesper's gold comes from groups teammates mostly cleared: rewards are *routed* to her.
2. **Elk-size groups early, cleared by several champions.** Before R250 they capture 4.0 groups of 2400+ health per
   game for 655 gold, with 2.7 hitters and 23-round clears. We capture 2.3 for 266, with 27-29-round clears.
   Their first such clear starts at R21 with 3.7 champions (captured R50); ours at R36 with 2.7 (captured R80). This
   is almost the whole R250 income gap (994 vs 614 gold per game).
3. **They hold the middle.** Middle-group clears per game: 14.4 for 455 gems against our 7.9 for 117.
4. **They survive.** Deaths per game 5.6 vs our 15.5. P(die within 5 rounds | contact) 0.023 vs 0.080. Enemy health
   lost per contact round 59 vs our 31. Deaths carrying 40+ gems 0.30 vs 0.7-1.2 per game.
5. **They act more.** Basic attacks per 100 alive rounds 26.6 vs 21. Casts: Ryth 8.5 vs 4.5, Tavi 9.8 vs 6.4,
   Marcella 8.2 vs 6.8. Idle turns 18.7% vs 21-24%.
6. **They see more.** Wards per game 115 vs 54-69. They place 2-5 altar locks per game; we place 0-1.
7. Gear follows income: equipment R250 / R500 is 1050 / 3000 against our 510 / 1230; banks per game 30 vs 10.

Basic mechanics are verified sound (`V57_BUG_AUDIT.md`: clean strict compile, correct spell kits and item
handling, no hoarding, no spawn sticking, no respawn blocking). The gap is strategy and coordination, not a broken
primitive.

## 3. What already failed: do not repeat these naive versions

All results against v57, 28 maps × 2 sides × 4 seeds:

| Tried | Result | Why it failed (measured) |
|---|---|---|
| Claudus draft alone (`V58_META_DRAFT` in the rejected diff) | −89 | our Vesper earns 206 by R250 (theirs 485); team gold unchanged |
| + gold funnel (`UB_GOLD_FUNNEL` 1: allies leave rewards to Vesper) | −141 | allies wait or walk away while Vesper is not coming; time lost > +33% |
| + `UB_JOB_MAX` 4 | −129 | |
| + `A2_DPLAN` 1 (static draft-turn team plan) | −217 | a fixed plan made at the draft turn goes stale in a few rounds |
| Opening pack (whole team on the best own-side elk group) | −52 | worked as built (first elk capture R40 instead of R80, 4.1 hitters), but R250 gold 628 vs 630: after the opening the greedy per-champion loop takes over again |
| `V57_TP_BRIDGE` (teleport over hole gaps) | islands −345 to −414 | single-use crystals on chains of gaps |
| Older: `UB_CAMPFIX` (camp-choice correction fitted to top teams), `UB_QCAMP` (offline-RL camp values), `A2_ZONES`, `APEX_PAIR`, `APEX_C*_HUNT` | all off in v57 | each failed the self-play gate |

The lesson: Claudus's advantage is a **loop**: team clears of high-value groups, rewards routed to the carry, an
early carry Treasure, and repetition through R250. Any one piece added to v57's greedy per-champion farming costs
more than it returns. v58 must replace the early-game farming decision with a coordinated one, and must be judged by
whether the loop's numbers move, not only by margin against v57.

## 4. v58 architecture (new layers)

v57's farming is per-champion greedy: each champion scores groups (`Bot::score_groups`, branch and bound over
distance-ordered groups) and coordinates only through 7-bit claim slots in the 8-byte shared memory, plus job calls.
Add the following layers. Each is a switch; together they form the v58 loop.

### 4.1 Team Economy Director (`V58_DIRECTOR`): the core change

A deterministic team schedule that **every champion computes identically** from shared knowledge, so no messaging is
needed beyond what exists:

* **Inputs** (identical on every champion): static map data (groups, camp types, positions, respawn timers via
  `sdk_bc_camp_group_max_respawn`, spawn/altar distance fields), the round, the claim slots, and a compact shared
  "group state" summary. If shared memory is too small for the summary, use deterministic estimates: our own captures
  are known to the capturer and can be written into the claim slot as an "on-site" code (existing codes 64+group on
  maps with ≤ 48 groups), and respawn rounds follow from timers.
* **Output:** for each champion slot, a current assignment (group, role: `clear` / `capture` / `escort`) and the next
  one. Replan every 10 rounds and on events (group cleared, champion died, enemy contact), never inside the per-group
  loop.
* **Planner:** a greedy-with-lookahead schedule over the next ~60 rounds. Assign 2-4 champions to the best
  value-per-team-round elk-size group (gold + gems, team kill time from summed dps, travel, 5-round capture) and the
  rest to wolves or small groups next to it, so the pack stays within ~8 tiles (cohesion is also survival). Value
  respawning groups at their respawn round (arrive on time instead of waiting beside them; dead-camp waiting is our
  biggest measured waste). Prefer our half until R~150, then contest the middle (§2.3).
* **Budget:** amortised. Run the plan once per 10 rounds on the lowest-slot living champion's turn, with a
  `bc::fuel_remaining()` guard, and cache it in a static. Everyone else reads the cached plan, recomputed
  deterministically if their cached round is stale. Target: under 15k fuel per replan, 0 extra fuel-outs.
* **Integration:** while the director is active (to R~300, then decide by measurement), `score_groups` returns the
  director's assignment early, as `A2_SOLE_GEM` does today (see `V58_OPEN_PACK` in the rejected diff for the
  pattern). Combat, retreat, tribute and shopping keep priority over it.
* Why this should work where `A2_DPLAN` failed: it replans from live state, it covers R1-300 (not the opening only),
  and it builds in reward routing (4.2) and the carry's shopping (4.3).

### 4.2 Reward routing (`V58_ROUTE`)

The capturer of each cleared group is chosen by the director, not by "the poorest ally on the tile":

* The carry (Vesper; otherwise the champion furthest from finishing its Treasure emblem) captures if it can reach the
  region before the clearers would have finished capturing it themselves plus 3 rounds. Otherwise the nearest
  clearer captures. Never leave a reward unattended (the `UB_GOLD_FUNNEL` failure).
* Clearers leave the moment the last camp dies and the capturer is on the tiles: one champion per capture, never two
  splitting a reward and both spending 5 rounds.
* Measure: the carry's share of team capture gold (Claudus 44-49%), split captures (<5%), capture delay (Claudus
  median 5 rounds).

### 4.3 Carry build and shopping (`V58_CARRY_SHOP`)

* The carry completes Treasure first (Vesper's build already starts with it, `bot.cpp build_for`) and is routed home
  to shop the moment it has 150 gold and is within a short trip of spawn, or rides a tribute or respawn trip.
  Target: carry Treasure ≤ R120 (Claudus R88; ours never by R450 in some games).
* Everyone else: Treasure, then Jungle / Durability, then Bruiser stacks, as now, but shop trips piggy-back on
  tributes and deaths (dead champions shop) instead of separate walks.

### 4.4 Draft (`V58_DRAFT`)

* Draft Vesper + Heart + Vendetta (+ Ryth or Tavi, + Marcella) **only together with 4.1-4.3**. The meta draft alone
  is −89. Test both drafts under the director; keep the ML draft (`A2_MLDRAFT`) as the fallback on maps where the
  director is off.
* The draft is not exclusive (both teams may pick the same champion), so it is always available.

### 4.5 Survival model (`V58_SURVIVE`)

* Before and during contact, estimate fight value from visible enemy stats (max health, strength and focus are
  observable; Claudus's gear is ~2× ours), local numbers, health and stuns ready. Disengage early when outgeared
  (retreat toward allies or the spawn, dash away), and never stay in contact under 35% health while carrying 30+
  gems.
* Bag discipline: with enemies seen in the last 15 rounds within 12 tiles, bank at 30-40 gems instead of the usual
  carry target; route the trip away from the last sightings (`A2_THREAT` zone code exists).
* Measure: deaths per game, P(die5 | contact) (`hurt_contact.mjs`, `death_context.mjs`), gems lost per death,
  40+-gem deaths (`sanity_audit.mjs`).

### 4.6 Action density (`V58_ACT`)

* Excludes-walk spells (Ryth area stun, Tavi stun, Marcella and Ren damage, Prism and Stellar): when a camp or enemy
  is in spell range and the target is not fleeing, stand and cast instead of stepping. Today a melee champion often
  steps and loses the cast.
* Use attack resets on camps whenever a basic attack has just landed and a reset is ready (Vesper, Vendetta, Ryth,
  Varg, Tavi, Marcella), and on champions in fights. Check for turns where an attack was possible but none was made
  (`sanity_audit.mjs` idle share) and fix the causes found.
* Targets: ≥ 25 basic attacks per 100 alive rounds; Ryth ≥ 8, Tavi ≥ 9 casts per 100.

### 4.7 Vision and objectives (`V58_VISION`, `V58_LOCKS`)

* Wards: keep one on the contested middle group cluster and one on the altar we bank at, re-placing every 10 turns
  as the charge recharges. Target ≥ 100 wards per game.
* Altar locks (10 gold consumable; place within 2 tiles of an altar; blocks enemy tributes and cancels their channel;
  5 basic attacks remove it): lock the enemy's main altar when an enemy carrier with a big bag heads to it, and
  pre-lock contested altars late in races. The existing code is `prelock_altars` / `try_lock_altar`; measure lock
  count and enemy tribute delays.

## 5. Brand-new strategies to try (each its own switch, after the loop works)

1. **Capture denial** (`V58_DENY_CAP`). Rule: "leaving the region empty or admitting an enemy resets progress". When
   an enemy champion sits on a cleared group's region (a 5-round capture) within dash range of a healthy champion of
   ours that is not carrying, step or dash onto the region. Their 5 rounds are wasted, and if they leave we capture.
   Claudus routes most of its gold through one Vesper capture at a time, so each denial hits their carry.
2. **Carry hunting** (`V58_HUNT_CARRY`). Detect a carry comp from the enemy draft (visible in draft memory; Vesper
   picked). Vesper solo-clears 2.5 elk groups per game and ends each at about 80% health with a bag. A 2-3 champion
   pick-off at a group about to finish (camp watch `A2_CAMPWATCH` has the timing logic) kills their economy and
   steals the bag (carried gems drop on death). Only with a local numbers advantage, per 4.5.
3. **Respawn-timer arrival**: covered in 4.1. Arrive as a group respawns, instead of waiting beside it.
4. **Tribute timing**: the tribute channel is not stopped by damage, only by stun, death or an altar lock. Bank under
   pressure when no enemy stun is ready, and stun enemy tributers (Ryth, Ren, Tavi, Prism, Marcella stuns) at
   altars: a stun cancels the channel.
5. **Race endgame**: the first team to 1000 tributed gems wins at once (Claudus games ended ~R979). At round 2000
   the tiebreakers are tributed gems, then lifetime gold earned, then kills. Bank early and in smaller bags when
   behind on the ladder curve; when ahead, deny instead of farm. `A2_RACE` code exists; re-measure under the
   director.
6. **Map-specific openings from replays** (later, optional): distil each official map's first-60-round targets from
   the decoded top-team replays into a small table read by the director. Use it only after the director wins
   without it.

## 6. How to prove it: a test bed that can see Claudus-style play

Self-play against our own lineage punishes Claudus-style changes (§3). Use these layers of evidence:

1. **Mechanism targets** (local, each variant against v57, `ledger_bench.py` + `capture_funnel.mjs` +
   `sanity_audit.mjs`): R250 team capture gold ≥ 900 (v57 ~630); elk-size captures by R250 ≥ 3.5 (v57 2.7);
   carry share of capture gold ≥ 40%; carry Treasure ≤ R120; deaths per game −30%; fuel-outs ≤ 2 per game.
   A variant that misses its own mechanism target is broken, whatever its margin.
2. **Strength gates** against v57 (`bench3.sh`, 28 maps × 2 sides, 4 seeds to screen, 12 to confirm, `bench_bayes.py`):
   * a non-inferiority gate for a loop component while the loop is incomplete (posterior mean ≥ −25,
     P(> −50) ≥ 0.9);
   * to keep a mechanism: ACCEPT (P(>0) ≥ 0.95, mean ≥ 25) and 0 faults;
   * for release and submission: the stricter release gate in §6.5.
3. **A Claudus proxy opponent.** Once a v58 configuration reaches the R250 economy target (~1000 gold, carry ≥ 40%),
   freeze it as `artifacts/baselines/proxy-claudus` and bench every later variant against both v57 and the proxy.
   The final v58 must beat both. Report how closely the proxy matches Claudus's signature (§2 numbers) to state how
   far to trust it.
4. **Ladder.** After a submission (§6.5) the user can queue unranked match groups against Claudus
   (`cambc match-groups create <team id> --maps a,b,c,d,e`; quota 50 groups per day). The baseline is 1 win in 80,
   so 3+ wins in 20 games is a real signal. Pull the new ladder games with `fetch_since.py` and report v58's record
   against Claudus and against the field.
5. **Release gate: submit only if all of these hold** for the frozen candidate (no edits after the checks):
   * development vs v57, 12 seeds (672 games): `bench_bayes.py` ACCEPT with **posterior mean ≥ +50 gems and
     P(>0) ≥ 0.95**, map-cluster bootstrap 95% interval above 0, win rate ≥ 53%;
   * against the Claudus proxy if one exists (§6.3): posterior mean ≥ 0;
   * 12-map holdout once and fresh 15-map holdout once: each ≥ 50% wins and ≥ 0 margin (if one misses narrowly,
     do not submit; report it to the user);
   * 0 native faults for both teams in every run; fuel-outs ≤ 2 per game;
   * mechanism targets (§6.1) met, or the shortfall explained in `CHANGES.md`;
   * a clean independent build (from a copy of `src/`, no `.cambc/`) byte-identical to the benchmarked seed-1 wasm,
     and the `cambc bundle bots/v58 --output <zip>` bundle containing exactly `src/` with the benchmarked source
     hash.

## 7. Order of work

1. Copy v57 to v58 (rule 2), add the switches with every default 0, and confirm v58 equals v57 (byte-identical wasm,
   or bench neutral ±10 over 4 seeds).
2. **V58_DIRECTOR + V58_ROUTE** on our current draft. Iterate on the mechanism targets first (R250 gold, elk count,
   capture delay), then on strength. Expect several iterations; log each in `artifacts/claude_ops/V58_BUILD_LOG.md`
   with the numbers.
3. Add **V58_CARRY_SHOP** and **V58_DRAFT** (meta draft): the full Claudus loop. Measure against v57 and against
   step 2.
4. **V58_SURVIVE**, then **V58_ACT**, then **V58_VISION / V58_LOCKS**. Each must move its own metric and pass
   non-inferiority.
5. Freeze the best configuration as the proxy (§6.3). Then the new strategies (§5), one at a time, against both
   v57 and the proxy.
6. Final candidate: 12 seeds against v57, the holdouts once, a clean independent build that matches the bench wasm,
   source hash (sorted name + NUL + bytes of `src/`), and a `bots/v58/CHANGES.md` in the style of
   `bots/v57/CHANGES.md`. Write `artifacts/claude_ops/V58_RELEASE.json` (model: `V57_RELEASE.json`: source and
   per-file hashes, wasm hashes, bundle size and hash, every gate result).
7. **If the release gate (§6.5) passes:** commit and push the record first, then submit once, save the CLI response
   to `artifacts/claude_ops/results/v58-submit.txt`, check that the uploaded byte count equals the verified bundle
   size and that the source hash is unchanged, and set the record's status to "submitted" with the platform version
   and UTC time. Update `bots/v58/CHANGES.md`, `bots/README.md` and the version table in `ops/HANDOFF.md` (v58 live,
   v57 frozen). Commit and push. **If it does not pass:** status "not submitted", list which conditions failed, and
   stop; the user decides.

At every step: one mechanism at a time, numbers before opinions, rejected diffs saved in
`artifacts/claude_ops/rejected/` with their results, and honest reporting. A loss is a result; say so plainly. If a
layer cannot reach its mechanism target after a fair effort, report why with data and move on rather than tuning
blindly.

## 8. Deliverables

* `bots/v58/` (source, `CHANGES.md`), with every mechanism behind a switch.
* `artifacts/claude_ops/V58_BUILD_LOG.md`: every variant, command, result (Bayes + bootstrap) and mechanism metrics.
* `artifacts/claude_ops/V58_RELEASE.json` with the gate results and status (submitted, with the platform version, or
  not submitted, with the failed conditions).
* Any new analysis tools under `tools/replay/` with a usage header like the existing ones.
* `ops/HANDOFF.md`: a new section summarising v58 and what is still open.
