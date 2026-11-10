# DOOMSDAY build plan (10 Nov 2026, lock 23:59 UTC)

Written for someone who has not followed the session. Every step names the file, the anchor text to search for, the
code to add, the values to try and how to check it. Line numbers are for the three source trees listed in section 3;
search for the anchor text, the numbers drift once patches are applied.

## 1. What decides our games

Data: 265 decoded ranked games from today (v137 to v141, 104+ maps, 21 opponents). "ALL" is all 265; "CURRENT" is
the 75 games of v140/v141 (the v220-based bots).

**Ladder record by version:** v137 49-46, v138 5-5, v139 44-41 (together 52% of 190); v140 3-12, v141 27-33
(together 40% of 75). The opponents and hours differ, so this is a signal and not proof, but the v220-based bots
are not doing better on the ladder than the v139 line, although v220 beat v139 61% head to head.

**The game is mostly decided by round 150.** Win rate by who leads early:

| We ... | ALL: win if yes / if no | CURRENT: win if yes / if no |
|---|---|---|
| have more gold by round 150 | 71% / 29% | 64% / 16% |
| have fewer deaths by round 150 | 69% / 26% | 58% / 22% |
| have fewer deaths by round 300 | 68% / 29% | 61% / 10% |
| suffer the first death of the game | 36% (the other side: 64%) | 33% (52%) |
| have more of our champions with a purchase by round 150 | 60% / 34% | 56% / 31% |
| have more golem + monolith gems in rounds 300-800 | 75% / 14% | 67% / 0% |

**A kill before round 300 pays the killers 76 gold and 6 gems on average** (1,108 kills). A team's whole gold income
in rounds 0-150 is about 450-600, so one early kill is a 13-17% swing plus the victim's respawn time.

**How the first fight goes** (first champion-on-champion attack: median round 54-60, in the middle of the map in
210 of 232 games):

| Who starts it, bodies within 6 tiles | Games | The attacker's side dies first |
|---|---|---|
| we start, we have more | 38 | 15% |
| we start, level | 46 | 47% |
| we start, we have fewer | 34 | 76% |
| they start, they have more | 48 | 26% |
| they start, level | 51 | 44% |

v141 starts the first fight in 59% of its games, and in 16 of those 42 it has fewer bodies there.

**How we die before round 300** (353 deaths ALL, 134 CURRENT): 82% to enemy champions, 9-11% to camps; 70-73% in
the middle of the map; 60% while attacking a champion; mean bag 7-8 gems. On v141, 48% of these victims had no
teammate within 5 tiles. Vendetta is 20-25% of them.

**What does NOT separate wins from losses** (do not spend time here):
- Where the turns go: moving, hitting monsters, capturing, recalling and waiting are within 1-2 points between us
  and the opponent. We wait slightly less than opponents on 23 of 24 maps. Only "dead" differs.
- Wards: we place fewer in 179 of 205 games and still broke even; teams that out-ward us lose as often as they win.
- Crew size on wolves and elks: the top team we studied (Tatakai) solos them as often as we do.
- Copying an opponent's item build (already tried before today without success).

**v141-specific:** in its losses it is behind on gem-cluster gems in every phase (30 v 40, 29 v 44, 45 v 69,
48 v 85) and spends less time hitting monsters from round 150 (14.7% v 16.7%) because it is dead more (10.8% v 7.3%).

## 2. Three facts about the current code (all three source trees)

1. The outnumbered rule is switched OFF: `NOVA_EARLY_SAFE_UNTIL 0` and `APEX_OUTNUMBERED 0`, so `outnumbered_k`
   is 0 and the block in `Bot::handle_enemies` never runs.
2. A gold-only shopping trip needs **126 gold** (`APEX_SHOP_GOLD 126`, read into `tune::kShopGold` every turn by
   `brain::adapt`). One shard costs 30.
3. A new crew call is capped at `UB_JOB_MAX 2` / `CREW_MAX 4` bodies and needs the crew already in sight within 12
   tiles, so golems (5,000 HP, 120 strength, range 4) and monoliths are rarely started.

## 3. Source trees and which to build on

All under `C:\Users\info\neural-networkk-battlecode\artifacts\tmp\`:

| Tree | What it is |
|---|---|
| `rl_env_1104/v139src/src` | v139 (Om), byte-identical to the uploaded archive |
| `rl_env_1104/v141src/src` | v141 (live, Om): v220 gameplay + v139 draft + 4 fixes, byte-identical |
| `upload_final/src` | v139 + all modules of section 6 (zip: `doomsday_final_v139plus.zip`). Compiles; never scored |

Recommendation: do steps A1 and A2 on **v139** first (two knobs, lowest risk, the line with the better ladder
record), then stack section 6 and steps B. If the team prefers to stay on v141, the same anchors exist there
(names differ only for the crew knobs: `P19_CREW_MAX` / `P19_CREW_RADIUS` instead of `CREW_MAX` / `CREW_RADIUS`).

New `#define`s go in `common.h` directly after the line `#define A2_KITFIX 31` (it exists once in every tree and
every patch script of this session uses it).

## 4. Steps A: knob-level, do these first

### A1. Early outnumber rule (first 300 rounds)
- **Why:** starting or taking the first fight with fewer bodies gets us killed first 76% of the time; the first death
  decides 64% v 36%; the rule that prevents it exists and is off.
- **Change:** `common.h`: `#define NOVA_EARLY_SAFE_UNTIL 0` -> `#define NOVA_EARLY_SAFE_UNTIL 300`. Leave
  `NOVA_EARLY_SAFE_K 1`.
- **What it does:** in `Bot::handle_enemies` (anchor `const int outnumbered_k = round < NOVA_EARLY_SAFE_UNTIL`):
  enemies within 8 >= our healthy bodies within 5 (self included) + 1, and no kill this turn -> `in_danger = true`,
  `winning = false` (the champion retreats).
- **Variants to test:** 300 (default), 150, and 2001 (always on; v141 dies 1.31 v 0.78 times in rounds 150-300 of
  its losses).
- **Risk:** carriers and capturers leave more often. Watch gems gained in rounds 0-300.

### A2. Shop from 60 gold in the first 300 rounds
- **Why:** the side with more champions equipped by round 150 wins 60% v 34%; our first purchase comes at round
  163-170 in losses (opponents 158-160); the 126-gold threshold is two kills' worth of gold held idle.
- **Change 1** (`common.h`, after `#define A2_KITFIX 31`):
  ```cpp
  #define CL_EARLY_SHOP_UNTIL 300
  #define CL_EARLY_SHOP_GOLD 60
  ```
- **Change 2** (`bot.cpp`, `Bot::play_turn`; anchor, exists once:
  `if (tune::kEarlyCarry > 0 && round < tune::kEarlyUntil) tune::kTributeCarry = std::min(tune::kTributeCarry, tune::kEarlyCarry);`).
  Add directly after it:
  ```cpp
  if (round < CL_EARLY_SHOP_UNTIL) tune::kShopGold = std::min(tune::kShopGold, CL_EARLY_SHOP_GOLD); // CL: equip early
  ```
  `brain::adapt` resets `tune::kShopGold` earlier in the same function every turn, so this needs no restore.
- **Change 3** (`bot.cpp`, respawn-wait branch; anchor `if (gold >= 90 && !shop_done && wait > home_trip + 4`):
  replace `90` with `(round < CL_EARLY_SHOP_UNTIL ? CL_EARLY_SHOP_GOLD : 90)`. The line occurs once in v139 and
  `upload_final` and twice in v141 (change both).
- **Variants:** 60 (default), 90, 30.
- **Risk:** more trips home. `tune::kShopWalkDist` decides walk v recall (a recall takes 5 turns).

### A3. Lineups: stop fielding Ren and Ryth (medium confidence, map-confounded)
- **Why (our win rate by our lineup, ALL):** HoR + Cassi&Issac + Marcella + Varg + Vendetta 53% of 108;
  HoR + Marcella + Varg + Vendetta + Willow 46% of 24; HoR + Marcella + Varg + Vendetta 47% of 19;
  Cassi&Issac + Ren + Ryth + Varg + Vendetta 38% of 16 (0 of 5 on v141); HoR + Marcella + Ryth + Varg + Vendetta
  38% of 13; HoR + Marcella + Ren + Vendetta 20% of 10. With Ren on our team 38% of 39; with Ryth 43% of 47.
- **Change:** `draft.cpp`. In `pick_from` (top of the file) skip `cd::ren` and `cd::ryth` unless no other pick is
  left, and add the same skip where `ml_draft_pick` scores its candidates (v141 forces `A2_MLDRAFT 1`, the net
  drafts every map below `A3_BIG_SIZE`). Fallback order: Vendetta, Varg, Heart of Ruin, Marcella, Cassi&Issac.
- **Risk:** the Ren/Ryth lineups come from per-map tables, so their bad record may be the maps. Test alone.

## 5. Steps B: small code changes

### B1. Engage gate: no level or losing champion fights before round 300
- **Why:** a level first fight is a coin flip (47% / 44%); with one body more the attacker's side dies first only
  15-26% of the time. A1 only stops fights we are losing by a body; this also stops level ones.
- **Change 1** (`common.h`): `#define CL_FF_UNTIL 300`
- **Change 2** (`bot.cpp`, `Bot::handle_enemies`). Find the outnumbered block of A1; it ends with
  ```cpp
              if (threat_on_me <= 0) threat_on_me = 1.0f;
          }
      }
  ```
  Directly after that closing brace (before the `A2_LANCH2` comment) add:
  ```cpp
      // CL_FIRSTFIGHT: before round CL_FF_UNTIL a champion fight needs a body advantage within 6 tiles.
      if (CL_FF_UNTIL > 0 && round < CL_FF_UNTIL && !w.enemies.empty()) {
          int foes6 = 0, friends6 = 1;
          for (const auto& e : w.enemies) foes6 += cheb(e.pos, pos) <= 6;
          for (const auto& a : w.allies) friends6 += cheb(a.pos, pos) <= 6 && a.hp >= a.max_hp * 0.4f;
          const bool sure = target && target_ttk <= 1.0f;
          if (foes6 > 0 && friends6 <= foes6 && !sure) winning = false;      // level: do not commit
          if (foes6 > friends6 && !sure) {                                   // behind: leave
              in_danger = true;
              if (threat_on_me <= 0) threat_on_me = 1.0f;
          }
      }
  ```
  `target`, `target_ttk`, `winning`, `in_danger`, `threat_on_me` are locals of that function at this point.
- **Change 3** (`bot.cpp`, first line of `bool Bot::hunt() {`):
  ```cpp
      if (CL_FF_UNTIL > 0 && round < CL_FF_UNTIL) { // CL_FIRSTFIGHT: never hunt alone early
          bool buddy = false;
          for (const auto& a : w.allies) buddy = buddy || (cheb(a.pos, pos) <= 6 && a.hp >= a.max_hp * 0.4f);
          if (!buddy) return false;
      }
  ```
- **Check:** in a debug game print `round, my_id, foes6, friends6` when the gate fires; it should fire around
  rounds 40-120 near the middle.
- **Risk:** we concede the middle early when alone. That is intended: 73% of early deaths happen there.

### B2. Collapse on a lone enemy (optional, harder)
- **Why:** 39-40% of the opponents' early deaths are champions with no friend within 5 tiles; with a body
  advantage the attacker wins the first death 74-85% of the time; a kill pays 76 gold.
- **Change:** when the B1 counts give `friends6 > foes6` and `foes6 == 1`, publish the target with
  `share_sighting(true)` (shared-memory sighting, bits 42-62; `tools/rl_env_1104/v130/trib_patch.py` shows the
  exact pattern for the tribute alert) and let healthy allies within 10 tiles that cannot see it walk there in
  `hunt()` (the branch that answers a teammate's call). Stop after round `CL_FF_UNTIL`.
- **Risk:** pulls champions off camps. Cap it: bag below 20, health above 65%, at most 10 tiles.

### B3. Golem and monolith crews from round 300
- **Why:** the side with more golem + monolith gems in rounds 300-800 wins 75% v 14% (CURRENT 67% v 0%). In our
  losses the opponent takes 18 and 41 golem gems in rounds 300-500 and 500-800 to our 5 and 16.
- **Prerequisite:** the staging-ring fix (`ring_patch.py`, section 6). The old fixed 5-tile ring is empty around a
  range-5 monolith and the crew stands still.
- **Change** (`bot.cpp`, `Bot::score_groups_full`, and `common.h`):
  ```cpp
  #define CL_HEAVY_FROM 300   // round from which golem / monolith groups are whole-team jobs
  #define CL_HEAVY_MULT 1.5f  // their value from then on
  #define CL_HEAVY_RADIUS 25  // crew calls for them are answered from this far
  ```
  1. After `need = champions_needed(g, hp_left);` compute once per group:
     ```cpp
     bool heavy = false;
     if (round >= CL_HEAVY_FROM)
         for (int ci : g.camps) {
             const auto t = w.camps[static_cast<std::size_t>(ci)].type;
             heavy = heavy || t == bc::camp_type::golem || t == bc::camp_type::monolith;
         }
     ```
  2. In the `answering` branch replace the radius test `dist > CREW_RADIUS` (v141: `P19_CREW_RADIUS`) with
     `dist > (heavy ? CL_HEAVY_RADIUS : CREW_RADIUS)`.
  3. In the `initiating` branch: `const int cap = (big || heavy) ? team_size : ...` (keep the rest), and change
     the crew-in-sight line to `if (!big && !heavy && need - 1 > crew_near) continue;`.
  4. Where the value multipliers are applied (anchor `value *= mid_mult;`) add `if (heavy) value *= CL_HEAVY_MULT;`.
- **Risk:** an undermanned crew at a golem. The existing staging logic waits for `need` bodies; do not weaken it.

### B4. Vendetta enters second (optional)
- **Why:** Vendetta is 20-25% of our early deaths, the most of any champion.
- **Change:** in the B1 block, for `type == bc::champion_type::vendetta` require `friends6 >= foes6 + 2` before
  round 150 (replace `friends6 <= foes6` by `friends6 <= foes6 + 1` for Vendetta).

## 6. Modules already written this session (patch scripts, `tools/rl_env_1104/v130/`)

Build any combination with
`python tools/rl_env_1104/v130/combo139.py <repo> <base src> <out dir> [flags]`.
Results are paired games against v139 on two panels (636 + 498 games) unless stated.

| Flag | Module | Result | Verdict |
|---|---|---|---|
| `--plan 25` | Draft-turn map plan: gem/gold cluster sweep regions, 1-2 sweepers, bank at 28, Capture then Prospector | +38 (+28, +10) | Keep. Targets v141's cluster deficit |
| `--plan 57` / `61` | the same + dynamic sweepers (bit 32) / + carry risk (bit 4) | bit 4 alone +21; bit 32 untested | Keep, verify |
| `--bt` | Blocked-tile memory + tribute alert | +23 (+19, +4) | Keep |
| `--frc` | Fake-recall check (57 of 58 top opponents fake recalls; see v221 notes) | not measurable locally | Keep |
| `--ring` | Staging ring from the camps' real reach; release on failure | untested | Keep (needed for B3) |
| `--port141` | Om's four v141 fixes on the v139 line | untested on v139 | Keep |
| `--bankfix` | Big bags retry banking after 15 rounds, bank 15+ near an altar with no enemy in sight | untested | Keep, verify |
| `--crew 1` | Crew size by efficiency on wolves and elks | untested; opponents solo these | Low priority |
| `--follow` | Crew-forming respawns as route follow-ups | +27 alone, **-40 on top of sweepers** | Do not combine with `--plan` |
| `--plan` bit 2 | Heal-trip and bank-trip cost in the group score | +21 alone, **-10 with sweepers** | Do not combine |
| knob `APEX_HP_COST=30.0f` | Health cost in the group score | +34 on one panel, **-9 held-out** | No |
| knobs carry 48, bank ratio 1.5 | Banking thresholds | about 0 | No |

`upload_final` = v139 + `--bt --plan 61 --frc --ring --crew 1 --port141 --bankfix`.

## 7. Build order and how to test

1. **Build 1:** v139 + A1 + A2. **Build 2:** `upload_final` + A1 + A2. **Build 3:** Build 2 + B1 (+ B4).
   **Build 4:** Build 3 + B3. Add A3 and B2 last, each alone.
2. Compile check: `cambc build <dir> --release --output x.wasm`. Crash check:
   `cambc run <dir> artifacts/tmp/rl_env_1104/v141src --map artifacts/tmp/ladderpool_maps/03colosseum.map26a --rounds 300 --release -o <out>`.
3. Local paired test, two candidates at a time, about 25 minutes:
   `bash tools/rl_env_1104/eval/seq.sh <run name> b139b v139 A=<dir A> B=<dir B>` (A is paired against v139's stored
   games, B against A; both panels). Keep a step only if it is not behind on either panel.
4. **Caveat:** the local opponents do not fight like ladder teams, so A1, B1 and B2 will show less locally than
   they are worth. Their real test is the ladder. After 20+ ranked games:
   ```
   python -I tools/rl_env_1104/ladder_pull.py --since <upload time> --window vNEW=<upload time> --cache artifacts/tmp/ladder_1110
   python -I tools/rl_env_1104/ladder_decode.py --cache artifacts/tmp/ladder_1110 --versions vNEW --workers 3
   python -I tools/rl_env_1104/time_budget.py --cache artifacts/tmp/ladder_1110 --versions vNEW --json tb.json
   python -I tools/rl_env_1104/early_deaths.py artifacts/tmp/ladder_1110 tb.json vNEW
   python -I tools/rl_env_1104/more_levers.py artifacts/tmp/ladder_1110 vNEW
   ```
   Targets against v141's numbers: deaths before round 150 below 0.71 per game; "first death is ours" below 49% of
   games; champions with a purchase by round 150 above 55%; gold in rounds 0-150 above the opponent's.
5. Uploading: `cambc submit <dir> --note "..."`. The site is in "pinned version" mode (Om pinned v141), so a new
   upload does not go live until someone runs `cambc submissions activate <version>`. Post every switch in issue #5.

## 8. Analysis tools (all in `tools/rl_env_1104/`)

- `time_budget.py`: where the turns go and where gems and gold come from, by phase, wins v losses.
- `early_deaths.py`: which early leads predict the result; anatomy of deaths before round 300.
- `more_levers.py`: record by version and opponent, lineups, openings, first contact, kill rewards.
- `h2h_anatomy.py`: two teams side by side for chosen games (used on the five Tatakai losses).
- `wipe_anatomy.py`: three-plus deaths within 15 rounds.
