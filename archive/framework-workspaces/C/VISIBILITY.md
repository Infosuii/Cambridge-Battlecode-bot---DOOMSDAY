# Observation legality audit (C follow-up, 2026-10-24)

This is a source audit of the current observation schema, glue and SDK. It does not certify new
engine captures or fuel measurements. The original C implementation is reviewed here by the
Wave-2 D worker under a separate C follow-up assignment; this is not an independent review of D's
own code. No C++ or schema changes were made in this follow-up.

The capture path uses own state, public information, immutable map data, current team vision and
this guest's lawful memory. No hidden enemy live state or future outcomes were found in the
runtime input path. Several freshness descriptions are stronger than the implementation supports;
those findings are stated below instead of being treated as verified temporal guarantees.

## Source evidence and classes

The authoritative feature list is [observation.json](../../../schemas/observation.json). Expansions
(champion type, ability kind, state flags, objective state) inherit the provenance of their parent
feature. The tables below cover every schema feature, including all four objective slots.

| Key | Meaning and concrete evidence |
|---|---|
| O | Own authenticated champion state. `nn_obs_glue.cpp:201-240` queries self `sdk_champion` and wards, then uses Bot state for other own fields. SDK `cambc.h:4088` identifies self; gold is self-only at `3740-3746`. |
| P | Public identity, alive flags, round, submitted score or constants. SDK `cambc.h:4094-4107` returns all handles outside vision; `3931-3935` permits identity of hidden/dead champions; `3530-3537` queries alive; `4317-4330` exposes submitted score and round. Glue `67-140` reads only these public attributes of unseen champions. |
| S | Immutable map or deterministic static route computation. SDK map masks/spawns at `cambc.h:4398-4440`; `World::init` at `world.cpp:43-143`; glue `192-225,286-330`. Capture reads existing fields and never constructs a new field. Availability flags are local computation state, not proof of a visible target. |
| V | Visible World snapshot. `world.cpp:566-588` builds champion records only from `vision::champion_tiles` and successful `sdk_champion`; hidden champion live records throw per SDK `cambc.h:3921-3928`. Visible ward clusters come from `world.cpp:726-733`. |
| M | Own earlier entity observation, with explicit known/visible/age. Glue `141-158` updates from visible World records; `333-372` exports remembered rows. `known` expires after 60 rounds. Encoder `nn_obs.cpp:233-335` excludes remembered stats/positions when unknown while retaining public identity and alive status. |
| T | This team's shared memory, not opponent memory. Glue reads Bot's decoded claim/sighting/distress state. `bot.cpp:408-482` implements the original word protocol; SDK `cambc.h:5023-5080` exposes only this team's bounded bytes. |
| H | Sampled own/public history with explicit age or validity. Glue `160-170,242-265`; encoder `nn_obs.cpp:141-177`. Sampling is lazy, as detailed below. |
| R | Legal World camp memory or inference, without a matching state/health observation age in the encoded objective slot. `world.cpp:460-543` updates from own vision/shared events and advances unseen predictions. This is not current hidden camp state. |
| D | Deterministic computation of the preceding classes, with no extra information source. Coordinate transforms use public symmetry/spawns. |

Source files: [glue](../../../bot/src/nn_obs_glue.cpp), [encoder](../../../bot/src/nn_obs.cpp),
[World](../../../bot/src/world.cpp), [Bot protocol](../../../bot/src/bot.cpp),
[SDK](../../../sdk/cpp/cambc.h), [raw ABI](../../../sdk/cpp/imports.h).

## Self and global features

| Features (each expansion included) | Actual class and freshness |
|---|---|
| `self.alive` | O: this turn's Bot dead flag. |
| `self.hp_frac`, `self.max_hp`, `self.strength`, `self.focus` | O: fresh self `champion_info` when capture succeeds, otherwise Bot snapshot. Schema descriptions mentioning only Bot fields omit this live refresh. |
| `self.gems`, `self.gems_vs_carry`, `self.gold`, `self.attack_range`, `self.melee`, `self.type.*` | O: Bot snapshot and teacher threshold; no enemy private query. |
| `self.spell0.present`, `self.spell0.ready`, `self.spell0.cooldown`, `self.spell0.range`, `self.spell0.kind.*` | O: teacher-cached kit/cooldowns plus `cast_done`. No fresh cooldown query is added by capture. |
| `self.spell1.present`, `self.spell1.ready`, `self.spell1.cooldown`, `self.spell1.range`, `self.spell1.kind.*` | O: same rule for slot one. |
| `self.cast_done` | O: Bot's action flag at first admitted capture. |
| `self.state.{recalling,submitting_gems,teleporting,can_move,can_attack,can_cast}` | O: fresh self state bits at capture; fallback derives permissive flags from own snapshot. Later execution must still query deterministic SDK legality. |
| `self.items` | O/D: `Bot::my_items()` estimates own shard-equivalent holdings from own stats; not an enemy inventory query. |
| `self.camp_taken_mult`, `self.camp_dealt_mult` | O: cached own emblem effects. |
| `self.ward_charges`, `self.ward_cooldown` | O: self wards import at capture, legal regardless of enemy visibility. |
| `self.pos_x`, `self.pos_y` | O/S/D: fresh self position transformed into canonical frame; own public spawn centre is used while dead. |
| `self.spawn_dist` | O/S/D: existing static spawn field at own position. |
| `self.altar_known`, `self.altar_dist` | O/S/D: local field-ready bit and existing field; unknown distance remains sentinel. Altar access field can incorporate known/predicted camp-gate state, so it is not purely timeless terrain. |
| `self.enemy_spawn_cheb`, `self.enemy_spawn_walk_known`, `self.enemy_spawn_walk` | S/O/D: public spawn geometry and locally built terrain field; no live enemy position. |
| `self.in_bush`, `self.on_own_spawn`, `self.in_enemy_zone` | O/S/D: own position against immutable geometry. |
| `self.in_hot_zone` | O/R/D: reach computed from World camp memory (`world.cpp:705-720`), including remembered damaged camps. Schema `visible-now` is too strong. |
| `self.heading_home`, `self.has_target` | O: own teacher intent; not actual teammate/opponent intent. |
| `self.hp_delta_turn` | O/H/D: current capture health minus previous Bot turn health. Capturing after an action can include that action's effect. |
| `self.hist10_valid`, `self.hp_delta_10`, `self.gems_delta_10`, `self.hist10_age` | O/H/D: newest stored sample at least ten rounds old, not necessarily exactly ten; explicit age accompanies deltas. |
| `glob.round_frac` | P/D: current round divided by public max rounds. |
| `glob.ally_score`, `glob.enemy_score`, `glob.score_diff` | P/D: current submitted scores queried in observe; not final outcomes. |
| `glob.gems_to_win`, `glob.win_now` | P/O/D: public winning threshold and current own carried bag. |
| `glob.rate50_valid`, `glob.ally_rate50`, `glob.enemy_rate50` | P/H/D: sampled public scores with actual elapsed age denominator, at least fifty rounds old. |
| `glob.rate200_valid`, `glob.ally_rate200`, `glob.enemy_rate200` | P/H/D: same at least two hundred rounds. No future score is read. |
| `glob.alive_us`, `glob.alive_them`, `glob.team_size`, `glob.enemy_count` | P/D: public alive/identity roster at observation opportunity. Cached on SDK errors; no visibility-limited stats needed. |
| `glob.ally_deaths_50`, `glob.enemy_deaths_50`, `glob.ally_deaths_total`, `glob.enemy_deaths_total` | P/H/D: observed alive-to-dead transitions only. These may undercount actual deaths between lazy samples. |
| `glob.map_w`, `glob.map_h`, `glob.size_class.*`, `glob.symmetry.*`, `glob.n_groups` | S/P/D: public map definitions. |
| `glob.fields_frac` | O/D: local precomputation progress; not map or opponent knowledge. |
| `glob.vis_enemies`, `glob.vis_allies` | V/D: current cached World visible entity list sizes; zero while dead. |
| `glob.sight_n5`, `glob.sight_n20` | M/T/D: counts of lawful own/team sightings with age cutoffs. |
| `glob.sight_valid`, `glob.sight_dx`, `glob.sight_dy`, `glob.sight_dist`, `glob.sight_age` | M/T/D: nearest stored sighting and actual age; not current hidden enemy location. |
| `glob.distress_valid`, `glob.distress_dx`, `glob.distress_dy`, `glob.distress_age` | T/M/D: teammate-published distress location, accepted only within ten rounds. |
| `glob.enemy_wards` | V/D: count of visible enemy-ward bush clusters, not all enemy wards or enemy private ward resources. |

## Each objective slot `obj[0..3]`

Slot zero is the already committed teacher target, if any; slots one through three are nearest other
groups by an existing static field or straight-line fallback. No privileged replay selector is used.
The schema's objective `repeat_doc`, glue `286-330` and encoder `208-230` agree on this selection.

| Feature | Actual class and freshness |
|---|---|
| `valid` | O/S/D: slot was filled from a known static group definition. |
| `dx`, `dy`, `dist`, `dist_is_walk`, `unreachable` | O/S/D: static group anchor relative to self and existing field status. `dist` falls back to Chebyshev, which does not prove reachability. |
| `gems`, `gold` | S: configured capture rewards, public map metadata (SDK `cambc.h:4479-4483`). |
| `state.{alive,reward,respawning}` | R/V/T/D: last observed or predicted state, not current hidden state. **No group-state observation age is encoded.** |
| `respawn_in` | R/V/T/D: timer prediction from remembered/shared ready round; can be inferred after an unseen reward ages out. **No source-age or confidence flag is encoded.** |
| `hp_left_frac` | R/V/D: sum of remembered camp health, zero for remembered reward, full hp for predicted respawn. **No health observation age is encoded.** |
| `max_hp`, `harmless` | S: configured camp designs; legal without current visibility. |
| `ally_claims` | T/D: count of current teammate claim codes for that group. Claims carry no separate age. |
| `enemy_seen`, `enemy_age` | M/D: whether/when a visible enemy was near that group. This age belongs to the enemy-near-group event, **not** the camp state or health sample. |

SDK `cambc.h:4485-4505` requires a visible member tile for current group lifecycle queries.
World enforces the visibility check before raw imports (`world.cpp:482-543`) and advances its own
predictions when unseen (`498-509`). `apply_event` accepts only the team's existing shared event
protocol (`460-479`). Thus the freshness omission is an epistemic/schema issue, not evidence of
access to hidden engine state.

## Ally rows (all five slots, excluding self)

| Feature | Actual class and freshness |
|---|---|
| `alive`, `type.*` | P: public alive status and immutable identity; retained outside vision and after memory expiration. |
| `visible` | V/M: the last Seen update occurred during this round's first observation opportunity. |
| `known`, `age` | M/D: remembered position valid through sixty rounds; age zero for visible, unknown sentinel otherwise. |
| `dx`, `dy`, `dist` | V/M/D: last legally seen position; unknown clears displacement and saturates distance. |
| `hp_frac`, `max_hp`, `strength`, `focus`, `range` | V/M: only copied from visible World ally records, otherwise remembered until expiry. Never refreshed by an unseen ally live-state query. |
| `gems_known`, `gems` | V/M: `sdk_champion_gems` is called only after this ally appeared in the visible World list (`glue:151-156`); a failed query yields unknown. |
| `claim.*`, `claim_is_my_target` | T/O/D: shared seven-bit claim decoded as group/idle/dead/other and compared to own target. It is a declared intent, not proof the ally reached the group. |
| `claim_dist_known`, `claim_dist` | T/M/S/D: static distance from the ally's **last known** position to the claim, only when both are usable. Schema's `ally-shared` alone omits the remembered-position dependency. |
| `claim_gems` | T/S/D: configured reward of the claimed group; no private ally carried-value inference. |
| `acts_before_me` | P/O/D: `ally.slot < self.slot`, a fixed claim-protocol seniority feature. It does **not** query or guarantee actual runtime execution priority after `set_priority`. |

## Enemy rows (all six bodies)

| Feature | Actual class and freshness |
|---|---|
| `alive`, `type.*` | P: public status and identity; no enemy live-stat query outside vision. |
| `visible`, `known`, `age` | V/M/D: first-observation World membership, sixty-round memory validity and explicit last-seen age. Observed death clears memory. |
| `dx`, `dy`, `dist` | V/M/D: own last lawful sighting, never a fresh hidden position. Unknown clears displacements and saturates distance. |
| `hp_frac`, `max_hp`, `strength`, `focus`, `range`, `gems` | V/M: visible World record copied into Seen, then age-tagged memory. No hidden stats/inventory/gold import is used. |
| `recalling`, `tributing` | V/M: state bits when last seen; age must be used to avoid interpreting an old channel as current. |
| `in_my_range`, `threatens_me` | V/O/D: emitted only when the enemy is currently marked visible and self alive. Range checks remain approximate features; SDK execution legality is deterministic elsewhere. |

Raw handles are stable row-sort/record identifiers, not a hidden-state channel. Padded `present=0`
rows encode all zeros and mask zero; present dead or unknown enemies keep their public identity
and an explicit alive/known flag (`nn_obs.cpp:291-335`). Sorting uses visibility, knowledge,
distance and handle. The encoder does not treat padded values as observable entities.

## Temporal cadence and snapshot limits

`nnobs::observe` exists, but there is **no per-turn call site** in main/Bot. The only current caller
of `nn_obs_access::observe` is `capture` at glue line 177. `nnh::ensure_context` calls capture only
for the first admitted shared-context head (`nn_head.cpp:149-173`). The context is then cached for
the turn serial/round. Therefore:

- The 16-entry fine ring contains **observed context opportunities**, not all engine rounds.
- The 32-entry score ring adds a sample on an observed opportunity at least ten rounds after its
  last sample. Fifty/two-hundred-round features use the sample's actual age and may span more time.
- Death totals mean sampled alive-to-dead transitions. A death followed by respawn between observed
  contexts can be missed; a sampled transition's timestamp can also lag the real death.
- Last-seen tables update only on those opportunities. A visible enemy on an unencoded turn may
  never enter the neural memory, even though World knew it then.
- A second `capture` in the same round does not re-run observe. Mid-turn actions or a later ward
  reveal can make World newer than the Seen table. Shared context remains the first admitted
  snapshot; exact action APIs must recheck legality after state changes.

Adding a per-turn memory tick would change fuel before teacher decisions. It is a separately
measured integration change, not a documentation fix or a neutrality assumption.

## Excluded information and future targets

Runtime inputs do not contain final outcome, terminal margin, future enemy sightings, unseen
enemy position/health/resources/cooldowns/items/gold, enemy private memory, opponent policy weights,
or omniscient replay state. Static camp spawn definitions are public map data, not hidden live camps.
Remembered entity state originates only from this guest's legal vision; team sightings originate
only from this team's shared bytes. Public alive flags do not authorize refreshing hidden stats.

The schema's belief definition is a **training target only**: future sightings over the next ten
rounds. It is not a RawTurn field or encoded input. Any future dataset builder must keep it under
targets, reconstruct this team's legal observation, and label censoring/missing future observation
coverage explicitly. An unseen enemy is not automatically a verified negative for a presence label.

## Eight-byte shared memory and concrete intent proposal

The SDK exposes capacity at `cambc.h:131-135`; A's saved runtime probe reports **8 bytes shared** and
1024 bytes frozen draft memory ([sdk_facts.json](../A/sdk_facts.json), `shared_and_draft_memory`).
This audit did not run a new probe. The current implementation keeps the original shared word:

| Bits | Current use |
|---|---|
| 0-41 | Six seven-bit claim slots: group id, 126 dead, 127 idle; optional existing fight orders112-118. |
| 42-48 | Sighting x, or group id when the high event discriminator is set. |
| 49-55 | Sighting y (shared-event ready-round packing also uses bit56). |
| 56-61 | Sighting round modulo64 (overlaps the event alternative's timer field by design). |
| 62 | Distress for sighting messages. |
| 63 | Existing APEX_EVENTS discriminator. It is **not a spare role bit**. |

The misleading old comment at `bot.cpp:418-419` says eight bits and255/254; the actual constants and
bit operations are seven bits and127/126 (`bot.h:21-28`, `bot.cpp:420-424`). The code is the evidence.

**Current compatible intent design:** publish the chosen group through the existing claim slot,
derive grouping/conflicts from those claims, and keep neural roles local. This already fits eight
bytes and preserves sightings/distress/events. No new blackboard or writes were added by this audit.

**Optional explicit-role protocol proposal, not implemented:** in an opt-in versioned profile where
`n_groups <= 112`, keep bits42-63 byte-for-byte as today and repurpose unused seven-bit claim codes:

| Per-slot code | Proposed interpretation |
|---|---|
| 0-111 | Assigned farm/contest group. |
| 112-117 | Existing engage-target index0-5 in the public enemy-handle roster. |
| 118 | Existing disengage order. |
| 119 | Banking; releases the old group claim. |
| 120 | Going home/healing. |
| 121 | Escorting; partner is deterministically the lowest-slot active carrier visible locally. |
| 122 | Regrouping; anchor is the lowest-slot living group leader. |
| 123 | Scouting. |
| 124 | Defending/responding to the existing distress message. |
| 125 | Holding/waiting. |
| 126,127 | Dead,idle, unchanged. |

Every same-team guest must select the same versioned profile. If groups exceed112, retain the
original group-only protocol and local roles; do not reinterpret valid group ids as intents.
This proposal trades away simultaneous target-plus-role encoding in one slot: role changes must
release stale group assignments. Writes must freshly read-modify-write only the writer's seven
bits, preserving the entire upper message region. Unknown codes must decode safely as other/idle.
Before implementation, test all128 codes, groups0/111/112/125, dead/respawn, message overlap, event
round wrap and multi-champion update ordering, then measure fuel and teacher equivalence. Frozen
draft memory can select a protocol version at draft time but cannot be a live team bus.

## Belief output dimension mismatch

`observation.json.belief.n_sectors` is **9**. `transforms.sector_of` returns0-7 compass sectors or8
for far/outside. `configs/model/fs_v1.json` currently requests **8** belief outputs. There is no
`schemas/heads/belief.json` at this audit snapshot; `models/config.py:110-114` uses the eight-output
default unless that head schema supplies `n_sectors`.

Proposed resolution: define the belief head schema with nine outputs matching the existing target
definition, change the model default to9, regenerate synthetic untrained exports/manifests/registry,
and test labels0..8, transforms, native output dimensions and export/runtime parity. Keep future
targets outside observations. Do not silently drop sector8 or reclassify unknown as a compass
sector. No schema/model change was made during this audit.

## Pending evidence

Real RawTurn fixtures, capture cost, visibility transitions in the actual engine, and integration
after action effects remain pending because official builds are permission-denied in this session.
Existing randomized/native parity tests validate encoding math and shape, not legal engine capture.
No synthetic fixture was renamed or presented as a real engine observation.
