# What our DOOMSDAY bot actually does

Source audit: 11 November 2026. Reference build: **v306AltarPressureReach**, the recommended release from the recent benchmarks. This document describes the frozen bot; the audit did not change its gameplay or submit anything to the ladder.

The newer v348 experiment adds two camp-safety changes described at the end. Those changes must not be attributed to v306.

## 1. The overall design

This is a C++ bot compiled to WebAssembly. It combines a large hand-written decision system, persistent memory, short combat simulations, a neural camp selector, a separate neural draft selector, and fitted numeric models. It is not one neural network controlling every action.

Each champion runs its own Bot object and keeps its own observations, target, claims, channel history and cached calculations. Teammates coordinate through compact shared memory and local observations. The active build does not have an omniscient central commander assigning every champion's movement.

The gameplay system is primarily an ordered priority list. A higher-priority action can consume the turn before farming or ordinary banking is reached. Within combat and farming, further ordered rules and overrides apply. Some actions can be combined legally in one turn; other abilities exclude movement, and ranged/basic attack rules affect the order.

The source contains 44 files and 13 C++ translation units. The inventory records 700 distinct source macro names. That is not 700 separate features: many names are thresholds, weight arrays, helper macros or alternative presets.

### How to read feature status

- **Active:** reachable in the default release when the situation calls for it.
- **Conditional:** compiled in, but additionally gated by map, champion, runtime knob, resources, visibility or fuel.
- **Off:** its controlling default prevents it running.
- **Shadowed:** a switch may be enabled, but an earlier return or selected implementation prevents that branch from running.
- **Neutral:** machinery exists, but default weights or multipliers make its contribution zero or identity.

These are source execution descriptions, not historical experiment verdicts. A disabled feature is not automatically a failed or rejected idea. Training claims in old source comments are not independent validation of the present release.

## 2. One champion's turn, in order

The entry point dispatches draft turns to draft.cpp and gameplay turns to Bot::play_turn. Exceptions are logged and the turn ends. The Bot object persists between turns.

The normal gameplay sequence is approximately:

1. Initialise once: map records, champion identity, ability metadata, ally slots, shared claims and draft plan.
2. Apply strategy profiles and runtime tuning layers. The settings depend on map, team size, champion and score.
3. Decode shared claims and clear inappropriate on-site markers. If dead, publish that state, shop where permitted and use spare time for fields.
4. Refresh our HP, stats, range, bag, gold, cooldowns and team scores.
5. If already channeling, decide whether to preserve or cancel that channel. Remember unsafe cancellations to avoid immediately repeating them.
6. Update visible enemies, allies, camps, terrain knowledge and neural state. Share/read sightings and camp respawn events.
7. Shop when on spawn, or in the field as Tavi. Refresh item passive estimates.
8. Use eligible support spells and reactive vision. Reobserve after an action that changes what is visible.
9. If already beside an altar, try the special short safe deposit window even when enemies are visible.
10. Otherwise handle enemy contact: objective protection, threat assessment, fighting, pressure, retreat and tribute denial.
11. If contact did not consume the decision, try a winning deposit, then the late-game banking override.
12. Try home siege farming, healing/shopping travel, eligible local team support, conditional regroup/hunt systems, ordinary banking, then farming.
13. Take legal opportunistic attacks/support actions. At the tail, consider wards, turn priority and deferred distance fields. Use spare fuel for staged neural work.

Several experimental hooks appear between these stages but do nothing with this release's defaults. In particular, the compiled neural macro-option hook is dormant in the selected live/lazy inference path.

Main implementation: bot.cpp, especially play_turn near line 8036 and the final action chain near line 8780. The combat function begins near line 3526, farming near line 7331.

## 3. What the bot knows and remembers

### Static map knowledge

World caches walls, holes, bushes, spawns, altars, camp positions and camp groups. It keeps terrain-only blockage separate from temporary unit occupancy and dangerous camp tiles. It labels connected bush regions and caches line-of-sight work. Dash-capable champions can use supported one-tile gap crossings.

Distance fields give walking distances to groups, spawn and altars. These are built incrementally because large maps make full search expensive. Before every field is ready, some decisions must use cheaper estimates or retain the current target.

### Changing world knowledge

Camp groups have alive, reward-ready and respawning states. The bot tracks remaining health, respawn rounds, observed harvests and group progress. It remembers enemy sightings and their age, and uses those in several local safety decisions. Sightings are not a complete prediction of the enemy's current position.

It also checks visible enemy channel progress; observing a recall flag once is not sufficient to conclude that the enemy has actually left.

### Shared memory and teamwork messages

The main shared word encodes per-champion target claims plus a small sighting/event payload. Claims distinguish idle, dead and an actual camp target. On-site marks are available only where the group encoding has room. Claim ownership and actor order resolve ties.

The message payload can contain a recent enemy sighting or a camp respawn event. It cannot broadcast every enemy and every camp simultaneously. Fresh sightings are preserved over less urgent events; a small event backlog is kept.

Draft memory carries team size, enemy caster count, map class, largest camp reward and map classification flags. The active sweeper plan also uses draft-time memory. Some extra memory layouts exist only for the disabled economy director.

Full fog-of-war belief propagation is **off**. Ordinary remembered sightings are still used. This distinction matters: belief propagation would spread possible enemy positions over unseen terrain, whereas a sighting is a dated observation.

## 4. Drafting champions

Drafting is a mixture of lookup tables, a separate neural model and fallback rules.

- There are priority roster presets and recognised-map lineup tables.
- Configuration bits can select alternative meta rosters, but those specific bits are not set by the default team-size masks.
- A runtime-gated Heart of Ruin preference exists.
- For maps not covered by the relevant lineup tables, **smaller teams can use a neural draft scorer**. It reads map dimensions, camp composition, rewards, distances and nearby supply, together with our picks, enemy picks, pick order and team size. It scores legal candidate additions through a 64-unit hidden layer. The model declares 53 inputs.
- Five-pick teams have an earlier custom-roster condition: Vendetta, Varg, Cassi & Issac, Marcella, Heart of Ruin, skipping choices already ours. Recognised-map tables and earlier overrides can take priority.
- Fallbacks include mobility-oriented picks on maps needing gap crossings, map-specific rosters and six broad map classes.

Both teams can own the same champion. The active neural availability check excludes our own existing choices, rather than treating the opponent's picks as unavailable.

An important source detail: common.h says A2_MLDRAFT=0, but **draft.cpp explicitly overrides it to 1**. It also overrides the large-team lineup settings. Reading only common.h would misdescribe the shipped draft.

Another model, fbstyle, can score 12 combinations of lineup and behaviour from 32 map features. In the current draft implementation there is no call selecting a style through that model. Gameplay applies the forced style 0, whose behaviour adjustment is neutral. Its model file and exports do not mean adaptive fbstyle drafting is active.

## 5. Strategy profiles and adaptation

There are several tuning layers, applied in sequence:

1. Common defaults.
2. Six profiles from team size and map area, plus some map multipliers.
3. Recognised-map parameter rows and the hybrid compatibility layer.
4. Fitted corrections for 70 map fingerprints, matched using dimensions, group count and total gems.
5. Runtime knob adjustments, including champion-specific settings.
6. Team-size configuration bits, home-side preference and conditional invasion-response stance.

Consequently, a base threshold is not always the final live threshold. A table or later override can change a setting that appears elsewhere in the source.

The default team-size masks are 14377 for three/five picks and 12297 for four picks:

| Bit | Effect in current source | 3/5 picks | 4 picks |
|---|---|---|---|
| 1 | Force selected farming need to one after target selection | On | On |
| 8 | Prefer Marcella receiving appropriate completed rewards | On | On |
| 32 | Use Bruiser milestones in the late item plan | On | Off |
| 2048 | Marcella farming/combat caution and no hunting | On | Off |
| 4096 | Suppress generic redistribution to a poorer ally; explicit funnel preferences still apply | On | On |
| 8192 | Cap the ordinary carry threshold at 45 at this tuning stage | On | On |

Cassi & Issac is one draft choice but two physical champions, so pick count and the number of bodies on the map are different concepts.

Home-side preference is active: enemy-side opportunities receive a territorial discount, and the home-side layer scales aggression down. That coexists with the newer supported aggression rules. The bot is not uniformly aggressive everywhere.

Runtime switches also control pair hunting, positional combat, spacing, convergence, commander overrides, fog regroup and invasion-response stance. Recognised-map layers can change those switches; a nonzero compile flag alone does not establish that a particular game uses them.

The old a2stack per-map configuration table is **bypassed** by the explicit team-size configurations. The separate older A2_MAP_PROFILE system is **off**. The recognised-map parameter and ladfit layers above are still active. The bot therefore contains both general map analysis and historical map-specific tuning. The source does not establish that every learned/table adjustment generalises to random finals maps.

## 6. Choosing what to farm

The hand scorer ranks camp groups using an approximate return per unit of time:

`(gems + weighted gold) / (travel + respawn wait + fighting + capture time)`

That is a useful sketch, not the exact complete formula. The actual scorer also applies safety, claims, staffing, territory, ownership, current-target stickiness, capture progress, follow-up opportunities and region preferences.

### Main active components

- **Gold emphasis early:** gold is weighted more strongly early, then the extra multiplier fades. It is not just nearest-gems selection.
- **Walking-aware distance:** use actual group fields where available rather than relying entirely on straight-line distance.
- **Staffing estimate:** estimate camp damage, our effective DPS, health drain and the number of helpers needed.
- **Camp item effects:** Jungle, Durability, Monster and other passive effects feed combat/soak estimates.
- **Claims:** avoid duplicating a completed capture or opening unnecessary competing jobs.
- **Local crews:** answer existing calls where healthy teammates can actually arrive. Distant claims are not automatically treated as available assistance. Ordinary crew calls are local; some big objectives have separate allowances.
- **Stickiness:** favour continuing the current worthwhile job rather than switching for every tiny score change.
- **Two-stop lookahead:** evaluate the value of a follow-up group, not only the immediate target, within a bounded shortlist and fuel budget.
- **Enemy camp watch:** remember enemy harvesting and adjust future contest opportunities.
- **Seeded variation:** a small repeatable perturbation can break ties. This is not unrestricted random walking.

A conditional buddy-farming path pairs Cassi with Issac first, then other melee/ranged partners. On maps outside its recognised-map set, the ranged partner can join a nearby dangerous camp its melee buddy is fighting, while the closer melee body tanks. It does not automatically join harmless, respawning or reward-only jobs, and can keep an already engaged job. This is separate from the disabled permanent role-squad system. A runtime-gated raider path can also relax the enemy-side discount for one healthy champion taking a quiet group.

The staffing estimate is not a full team scheduler: the active configuration subsequently sets best_need=1. Crew-aware scoring and capture ownership still exist, but some downstream staging behaviour is bypassed by that setting.

### Sweeper regions

The active map planner can identify worthwhile loops of harmless reward/gold camps, using walking distances, rewards, respawn/capture time and travel to altars/spawn. It can assign one or two sweepers when the map's supply justifies it. The plan is stored at draft and read by the champions. This is a limited regional farming plan, not a complete commander for every champion.

### Keeping a nearly completed large camp

crew_can_finish checks whether the current group is close enough to completion that switching would waste invested work. It requires actual nearby hitters, adequate health, a small bag, no recent enemy danger and a short projected finish. Helpers who are channeling do not count.

### Small-camp downtime

For small gem camps with more than one turn left before respawn, camp_downtime_job searches for feasible side work or a better job. The respawn branch may also use spare time for banking or shopping when the trip is worthwhile. It avoids standing directly on a spawn tile, which would delay the respawn.

This is not a universal ban on waiting. If no feasible alternative is found, the original target can survive. Large camps and safety/fuel constraints can also make waiting rational. The code still has an explicit wait-respawn mode.

## 7. Fighting and capturing camps

Camp combat is more detailed than walking up and repeatedly attacking:

- Select an attackable camp and account for damage already dealt.
- Use movement/attack-compatible abilities in the right order.
- Use attack resets to obtain a legal extra hit, including after applicable kills.
- For ranged champions, use an attack ring and siege with longer-range spells where feasible.
- Estimate which champion the camp will attack, using proximity and tie rules.
- Track health drain and back off or rotate the tank when appropriate.
- Avoid known dangerous camp attack zones during movement.
- Reveal an obscured bush camp rather than repeatedly targeting something unavailable.
- Attack a blocking camp to get unstuck when there is no visible enemy threat.

Once the group is dead, occupying a reward tile advances capture. The bot tries to leave one owner capturing while helpers move on. It can yield the reward to an eligible nearby recipient, particularly Marcella under the active funnel bit.

Objective-aware contact rules run before ordinary combat:

1. **Camp contact:** finish sufficiently safe, already engaged work despite distant enemy contact.
2. **Capture anchor:** a healthy, lightly loaded champion can keep capturing rather than abandoning the reward merely because enemies are visible. Prefer an eligible Vesper anchor, then stable actor ID. It may attack or use stationary spells while retaining position.
3. **Capture footwork:** move within the reward region to a safer adjacent tile if that preserves capture and reduces danger.
4. **Deny capture:** a healthy nearby helper can step onto an enemy's nearly available reward with immediate support. This is a local contest, not a long remote chase.

An optional sole-gem-camp lead-lock strategy deliberately occupies its spawn tile to deny respawn while ahead. V54_HOLD is defined as enabled, but **the default FB_FLAGS=10 includes bit 2, which suppresses this behaviour**. It should not be described as active.

## 8. Movement and why it can look indirect

The normal navigator follows downhill steps in a distance field. Valid routes account for terrain and temporary blockage. Among equal-distance choices it uses tie scores, including target geometry and combat preferences. It can use travel dashes, supported gap crossings and teleport crystals when the saved travel exceeds their setup cost.

The fallbacks are layered: normal field route, terrain-only/alternative search when blocked, bounded search admitted by the fuel governor, then a greedy legal step when appropriate. Group fields are cached and created across turns.

Stall handling includes:

- Four consecutive movement-enabled failures on the same tile can abandon the job for 40 rounds, with an altar-gated-map exception.
- Longer approaches without progress can cause avoidance/reselection.
- A statically unreachable capture can be avoided for hundreds of rounds.
- A valid gap crossing may wait for a real dash cooldown, but does not wait forever for an impossible landing.
- Bridge and capture blockage have dedicated handling.

There is no single immutable route followed to completion. The target, danger, local occupancy and tie preferences can be recomputed. Combat kiting may deliberately move sideways; a switch from farming to banking or fleeing can reverse direction. Thus a jagged trace is not proof of random choice, and a straight-line opponent does not prove our field route is longer. Equal-length ties, changing targets and genuine stalls require different diagnoses.

The larger threat-aware detour systems are **off** globally. Banking still has its own sighting-aware routing, and immediate combat retreat still evaluates multiple threats. Those independent systems must not be conflated.

## 9. Deciding whether to fight or flee

There are several stages, and later ones can override earlier ones.

### Formula assessment

The bot estimates target kill time, our survival time, nearby ally contribution, enemy damage, spell burst, HP, bag risk and special champion interactions. It discounts allies that cannot contribute promptly. Some fitted Lanchester-style power modelling is runtime-gated. One-turn ready-burst safety is active; the separate two-turn stun-chain burst experiment is off.

Cassi/Issac receive special handling because losing one body can lose the other and its bag. The weaker linked body's health matters; there is also a close-pressure guard against fighting badly outnumbered.

### Active short combat simulation

APEX_TS_DECIDE=1 is independent of APEX_TSEARCH=0. The active short simulator compares **fight versus run**, normally over a small horizon under one or two enemy models. It represents nearby units and champion kits. It values lives, HP and carried gems. Large scenes or insufficient fuel can shorten the horizon, reduce models or return no verdict.

A safety-authority check prevents a positive fight verdict from erasing formula danger when reachable enemies were omitted, a linked pair is incompletely represented, or an awake camp creates danger that the simulation does not model. A run verdict may still be accepted.

The much larger search over candidate actions is off. The simple separate fight.cpp skirmish simulator is also off.

### Team support and aggression

- **A3_BACKOFF:** with a local numbers edge, sufficient HP, a manageable bag and a plausible favourable kill race, a danger verdict can be cleared. Its name means backing off less.
- **Squad strike:** the v306 supported attack can recognise two-versus-one and three-versus-one opportunities. It counts actual ready hitters and reachable firing squares, rather than merely nearby bodies. Two helpers cannot both be credited with the same free tile. It excludes channels, obvious camp danger, enemy spawn traps and risky bush approaches.
- **Isolated-target pressure:** take an immediate supported shot or a bounded setup step. The commitment is short and lets a retreating enemy go rather than following indefinitely.
- **Carrier peel:** a lightly loaded ally can hit the sole immediate pursuer of a loaded/depositing teammate. This is close protection, not an endless escort chase.
- **Join fight:** a healthy, lightly loaded champion can move toward a visible nearby ally under contact when the fight is not already comfortably staffed.

The default bot is therefore more willing to use real support, but it does not use the blanket rule “we have more champions, always attack.” Arrival times, legal attacks, bags and terrain still matter.

### Carrying out combat

Caster micro is active. It scores holding position to shoot versus stepping, using expected damage, kills, stuns, ally cover, enemy reach, dash/spell readiness and awake camp danger. Cassi's micro has an additional lineup condition. Other layers handle kiting, opportunistic hits, gap-closing dashes, attack resets, healing and shielding. A late shield pass can use an otherwise unspent ability after combat movement.

Melee champions can hit an adjacent opponent before fleeing when the rules permit both. Standard retreat considers multiple visible threats and home progress. Hidden-bush recall is available when appropriate. The optional deeper escape search, extra stand-and-fight modes and several burst-holding experiments are off. Some of those inactive modes have source bodies but their bit flags are not enabled.

There is also a short post-flee cover rule that can prefer one cover step over immediately walking back into the same fight. That can produce an intentional apparent reversal.

## 10. Banking, getting home and stopping enemy deposits

### When our bot banks

Ordinary banking uses a carry threshold adjusted by profiles/knobs, map supply, distance and time remaining. It can bank smaller bags opportunistically, prioritise a winning bag, and lower the effective threshold late. The default team configuration caps the ordinary threshold at 45 at one tuning stage; this is not a guarantee that every champion deposits at exactly 45.

Banking has dedicated recent-sighting avoidance and altar selection. A route that fails to progress can time out and temporarily defer another trip. The altar fix permits a champion already in submission range to score despite that route timeout. Locked altars are handled separately; an accessible alternative may be used.

**The visible-enemy deposit window is active.** A champion already beside an altar can submit a bag of at least 20 when HP, camp danger, predicted submission duration and enemy arrival/cooldowns permit it. It is restricted to short channels and checks very recent sightings for an unaccounted opponent. This branch runs before ordinary enemy handling, so “enemy visible” does not automatically forbid a deposit.

### Channel guard and retry memory

The bot monitors recall/submission danger and can cancel rather than remaining helpless through a dangerous channel. A cancellation is remembered with location and kind; retry logic avoids starting the same unsafe channel repeatedly without a meaningful safety change. Teleport channels have separate handling.

In **v306**, the relevant channel danger check accounts for enemies but does not include the later camp-damage correction. See the version section.

### Returning home

Low health, enough spendable gold, existing home intent, and travel cost can trigger a return. The bot tries not to abandon a worthwhile nearby capture/finish unnecessarily. It may walk out of danger before recalling. Spawn healing can keep it still until an appropriate health target. Completed item builds are remembered so gold does not keep causing pointless shopping trips. Tavi can shop in the field.

Home siege lets a champion attack a suitable reachable camp while benefiting from spawn healing, instead of spending every healing turn inactive. It requires actual reach and appropriate local safety.

### Denying their banking

The active tribute-denial routine inspects the opponent's channel timer and actor order, estimates whether we and nearby allies can kill in time, and compares that with reaching altar-lock/stun range. It can hit a channeling enemy while delaying the interrupt until the last useful turn, unless a kill is available earlier. This preserves the window in which the opponent cannot act.

Altar locks can also be used opportunistically when leaving. The separate proactive prelocking system and V58 objective-lock helper are off.

## 11. Gold, items and who receives rewards

The active V58_ITEM_PLAN constructs a champion-aware sequence of shard milestones. It distinguishes focus users, physical attackers and Heart of Ruin, and has specific active treatment for champions such as Marcella, Prism and Tavi.

The general plan mixes economy, camp efficiency, survival and capture items before late stat stacking. Three/five-pick configurations add Bruiser milestones; the four-pick configuration follows the Greed continuation. Alternative top-team builds are present behind bits 16/512 but are not selected by the default masks.

Purchasing counts already combined emblems, respects actual item prices, handles the same item at multiple milestones and tracks purchases within the visit. It reserves early item progress before some consumables, buys altar locks and useful teleport crystals where allowed, and records terminal/completed shopping states.

It does not freely redistribute gold between champions. It can change who captures an available reward, which changes future gold distribution. Marcella has an explicit recipient preference. The generic poorer-ally rule exists, but the default configuration suppresses its ordinary non-funnel version. The Vesper-specific and central carry-director funnel systems are separate and off by default.

**Shadowed item code:** later V58_KIT_MARCELLA/TAVI/HEART plans, V54 item presets, older UB plans, the old APEX_BUILD families and the lab-supplied build-table override sit below the active V58_ITEM_PLAN return. With this release's settings they do not choose the build. Their flags, comments and weight tables should not be counted as additional stacked item policies.

## 12. Vision, bushes and hidden information

Reactive ward reveal, forward ward consideration and bush-camp reveal have independent active paths. The bot can reobserve after revealing a bush. Bush combat includes ambush/counter-ambush behaviour and hidden recall decisions, each with its own safety conditions.

The ordinary blanket ward-drop switch APEX_WARDS is off, but that does **not** turn off every ward use. V58 objective vision and the fb end-of-turn ward-spam option are also off. The older full hidden-enemy belief and altar-score inference systems are off.

The bot is consequently better described as using local observations, cached terrain and dated sightings than as tracking the exact positions of every unseen enemy.

## 13. What the neural systems do

### Main entity network: active for camp ranking

The deployed input layout has 500 feature slots:

| Block | Slots |
|---|---:|
| Global | 16 |
| Self | 44 |
| Five allies | 60 |
| Eight enemies | 128 |
| Ten candidate camps | 220 |
| Four altars | 32 |

Each entity type has an encoder producing 16 values. Global/self encodings and mean/max entity pooling form a 160-value summary, followed by two 64-unit shared layers. Pointer-style heads score available entities rather than depending on fixed map IDs. Champion types are encoded separately from continuous features.

The network contains ten output families in the source: behaviour, movement step, spell choice, spell timing, utility, shop, macro option, camp target, attack target and spell target. **Having those heads does not mean they control those decisions in v306.** The active deployment primarily uses the camp-target output. Movement, item buying and combat execution remain rule/simulator driven.

It is blended with the hand camp selector. The neural choice needs sufficient advantage, and invalid/stale choices are filtered. There is a Cassi/Issac partner-preservation veto. It is not blindly following the neural winner every turn.

### Inference scheduling and fuel

The selected path is fast, live and lazy. It updates cheaper changing camp features and reuses slower summaries where necessary. Work is staged across turns. Incremental cached encoders, 16-bit quantised inference and WebAssembly SIMD reduce cost. Cost estimates and safety margins determine whether a refresh fits. Refused/incomplete work should not publish a partial new decision.

### Dormant heads and alternative models

- **Neural bank gate:** A2_NN_BEH=0; ordinary banking rules remain in charge.
- **Macro options:** hunt/home/regroup/bank code exists, but the chosen live/lazy path returns before filling that option state. Its initial value stays neutral in this default deployment.
- **Direct fight/run policy:** the separate PPO-style A2_POLICY network is off. It has both a small 24-input version and a larger per-unit version in source.
- **Residual campnet:** a separate 18-to-16-to-1 camp policy is off. It is not the same as the active 500-feature network.
- **Linear farm residual:** A2_LAB compiles the corrector on, but its 16 writable weights initialise to zero, making its default multiplier identity.
- **Movement, tile, assessment and enemy-action models:** additional model headers exist, but their relevant switches are off.
- **Episode policy:** encounter logging and episode aggression selection are off.

The release uses fixed model weights. It does not train itself during ladder games. Updating cached observations or measured inference cost is not gradient learning. The project contains offline training/recording hooks, but a full provenance audit of every frozen weight is outside this source walkthrough. Recent gameplay fixes should not be described as retraining those weights.

## 14. Experimental systems that are off or dormant

This groups the major dormant mechanisms by purpose. The complete macro appendix includes the associated parameters and per-file overrides.

| Family | What exists | Current state |
|---|---|---|
| Economy director | Elected coordinator; carry recipient; fixed crew selection; early-game assignments; primary/secondary camp rotation; capture handoff | V58_DIRECTOR=0; dependent route/carry-shopping features off |
| Global team assignment | Joint camp assignment rather than individual scoring | A2_PLAN=0 |
| Draft opening rollout | Precomputed opening camp route/rollouts | A2_DPLAN=0 |
| Learned macro plan | Choose preset global farming/banking/fighting styles | A2_MLPLAN=0 |
| Bank/shop route planning | Search multi-step farm/bank/shop schedules | APEX_PLAN=0; two-stop farm route lookahead remains active |
| Full tactical action search | Simulate candidate attacks, steps and spells, then execute the best | APEX_TSEARCH=0; binary fight/run simulation remains active |
| Simple fight simulator | Separate small skirmish model in fight.cpp | APEX_FIGHT_SIM=0 |
| Escape search | Multi-step escape sequence with threat/dash modelling | APEX_ESCAPE_SEARCH=0; normal retreat remains active |
| Alternate search models | Learned local value, action/enemy models, phantom enemies, camp simulation, calibration and extended snapshots | Main optional switches off |
| Full fog beliefs | Propagate possible unseen enemy areas and expected reinforcements | APEX_BELIEF=0 and A2_BELIEF=0 |
| Opponent behaviour learning | Estimate opponent retreat tendencies for simulation | APEX_OPP_MODEL=0 |
| Permanent packs | Fixed role squads, generic pairs, automatic caster escorts | Base APEX_ROLE_SQUAD/SQUADS/PAIR/ESCORT all 0; other limited duo/local-support paths separate |
| Remote distress response | Long-distance response and ally-directed fleeing | Base distress/flee-ally switches 0 |
| Pair hunter/commander/fog regroup | Extra runtime team behaviour | Compiled but knob/map gated; not universally on |
| Two-turn burst/stun guard | Predict longer burst and stun chains before leaving | A2_BURST2=0 |
| Dedicated burst-kill planner | Search a special immediate burst-kill sequence before ordinary contact handling | APEX_BURST=0; normal offensive spells still active |
| Burst holding/disengagement | Reserve burst and special retreat thresholds | Relevant A2 experiments off |
| Extra chase/target policies | Dedicated loaded-target sniping, alternative wounded/threat scoring, extra generic numbers modifiers and dash reservation | Main APEX_SNIPE/NOVA_TGT/APEX_NUMBERS/APEX_SAVE_DASH switches neutral or off |
| Opening rush | Coordinated early rush with its own leader and target | NOVA_RUSH_UNTIL=0 |
| Dedicated altar ambusher | Park a chosen champion near an enemy-side altar | A2_AMBUSH=0 |
| Threat/danger maps | More expansive path detours, zone allocation and danger scoring | APEX_THREAT_PATH/A2_THREAT/A2_DANGERMAP/A2_ZONES off |
| Proactive altar controls | Prelocks, stale-bag altar watches, extra objective lock helper | Base prelock/stale-bag and V58_LOCKS off |
| Alternate banking styles | Ratio bank gate, mono/race-specific bank switches, recall as general travel shortcut | Main switches off; ordinary/endgame/safe-window banking active |
| Neural movement/control | Direct learned movement, tile scoring, fight/run assessment, PPO action override | Main model switches off |
| Neural shop/utility/cast heads | Learned choices for most action categories | Present in model architecture, not authoritative in selected deployment |
| Camp score experiments | Older Q-style and residual camp corrections | UB_QCAMP/UB_CAMPFIX off; separate zero-weight residual neutral |
| General ward spam | Blanket ward drop, extra objective vision, fb ward-spam flag | Off; reactive ward paths independent |
| Lead-lock respawn denial | Hold the sole gem camp's spawn while ahead | Compiled but suppressed by FB_FLAGS bit 2 |
| Fake recall experiment | Start a recall at turn end and cancel next turn | FB_FLAGS bit 4 unset |
| Adaptive fbstyle | Learned map feature style/lineup choice | Model retained; current draft does not call selection; forced behaviour 0 neutral |
| Old item presets | Multiple character builds and earlier Treasure/Bruiser alternatives | Shadowed by active item-plan return |
| Detailed diagnostics | Profiling, fuel logs, death traces, neural recording, micrologs and episode logs | Main logging switches off; selected ordinary diagnostics may still exist |

P19_TRIP and P19_RALLY are not defined in this release, so their conditional blocks are off. P19_FADE=1 is present as a definition but has no other source reference; it does not activate a separate fade mechanism. Likewise, some labels are retained even when their mechanism is unconditional elsewhere or no longer called. Source presence needs a call-site check.

## 15. Why there can still be an apparently idle turn

The code has several distinct causes; one mode label is insufficient to identify a bug:

1. Capture progress requires staying on a reward tile.
2. Recall, teleport and submission consume channel turns.
3. Spawn healing can deliberately wait for health.
4. A small camp may remain the best feasible choice after the downtime search; respawn waiting is still supported.
5. A stationary ranged attack or movement-exclusive spell can be the selected productive action.
6. A bridge may require a near-ready dash cooldown.
7. Staging/ownership can wait or yield to another champion, although current configuration bypasses some staffing waits.
8. Insufficient fuel can preserve the old target or refuse optional work. The farming path can return false with no valid target.
9. A blocked or invalid action can fail; stall logic generally needs repeated evidence before abandoning the job.
10. Initialisation and deferred field creation can consume substantial early-turn work.

The safety code reduces some wasted loops; it does not prove that every idle-looking turn is now productive. Likewise, the presence of a feature does not prove a current benchmark gain from that feature in isolation.

## 16. CPU/fuel engineering

Fuel is a game instruction budget. Running out can suspend the bot and lose useful action time. The bot therefore admits optional work only when a reserve remains.

Active engineering includes a movement/ward fuel governor, capped search depth, incremental field creation, deterministic tactical budgets, cached map/bush/group work, reused aligned allocation blocks, vectorised/quantised neural inference and staged neural refresh. Combat can take priority over camp rescoring, and the current target can be kept after simulation consumed its budget.

These are performance protections, not a guarantee of zero exhaustion. First-turn map setup is especially expensive. This audit did not rerun the benchmark suite or alter the frozen compiled release.

## 17. v306 versus newer camp-safety experiments

The walkthrough uses v306 because it remained the recommended release from the completed comparisons. A higher version number does not automatically mean a better benchmark result.

- **v320:** adds awake-camp damage to the relevant channel/start safety checks, addressing channels that were considered safe against champions while a camp could still hit.
- **v348:** includes that correction and a narrow camp-finishing spell exception. Before walking away, a ranged champion may use a movement-exclusive spell predicted to kill a dangerous camp with a safety margin. This is not a general enablement of every act-before-walk experiment.

Other experimental checkouts and teammate archives are not all compiled into v306. This document covers the files actually present in the frozen release, including their inactive branches. It does not claim every historical branch in the workspace has been merged.

## 18. File-by-file map

| Files | Purpose |
|---|---|
| main.cpp | Draft/game dispatch, persistent bot, end-turn boundary, exception handling, lab exports and aligned allocator pool |
| bot.h / bot.cpp | Champion state; movement; claims; items; combat; farming; banking; main priority chain |
| common.h | Shared types/helpers, compile switches and numeric tuning defaults |
| world.h / world.cpp | Terrain, visible entities, camps, sightings, bush knowledge and cached path fields |
| strategy.h | Draft summary, map classification, six profiles and score-based tuning |
| draft.h / draft.cpp | Pick legality, roster tables, neural draft path and fallbacks |
| draft_net.h | Frozen draft scorer weights |
| mapplan.h | Draft-time harmless-camp region/sweeper planning and memory format |
| pressure.cpp | Capture anchor/footwork, nearby capture denial and safe camp-contact finish |
| deny.cpp | Opponent tribute timing, damage window and interrupt logic |
| tactics.cpp | Additional action-order, vision, locking and survival helper implementations; several are disabled |
| economy.cpp | Disabled central economy/carry/crew director and dependent route work |
| fight.h / fight.cpp | Disabled simple skirmish simulation and related shared support |
| tsearch.h / tsearch.cpp | Kit-aware simulation; active binary fight/run decision and caster micro; optional full action search |
| runtime_budget.h | Optional-stage admission, reserves and affordable search depth |
| channel_retry.h | State for unsafe channel cancellation/retry |
| nnrec.cpp | Entity features, neural deployment, camp blend, recording and alternative learning hooks |
| nn_infer.h / nn_weights.h | Main entity network math and frozen weights, cached/quantised/SIMD paths |
| neural_policy.h / neural_policy.cpp / neural_weights.h | Separate residual camp network and tracing hooks, main policy off |
| learner.h | Sixteen-feature farm residual; zero default lab weights |
| lab.h | Runtime knob arrays, controls, logs, candidate weights and experiment exports |
| a2stack.h / a2stack_table.h | Configuration bit selection; old per-map table bypassed by team-size presets |
| a2map.h | Older optional map-profile switch corrections, off |
| ladfit.h | Recognised-map fitted corrections |
| fbstyle.h / fbstyle_model.h | Alternative feature-driven lineup/playstyle selector and behaviour deltas, currently dormant/neutral |
| ml_plan.h | Disabled learned macro-plan presets |
| lanch_model.h | Fitted local force assessment coefficients, conditionally used |
| local_model.h / act_model.h / assess_model.h | Optional learned tactical value/action/fight assessment |
| move_model.h / tile_model.h | Optional learned movement/tile scorers |
| episode.cpp / ep_model.h | Disabled encounter/episode logging and aggression policy |

## 19. Reproducibility and additional references

Frozen source SHA-256: `7f3dadb1d3876137ddd4606f340eb64f1fed67c9e4d6a70defa93c2c59a75d3e`.

Release Wasm SHA-256: `9e335df552156d37ff5b3e0befafcbfe98c56d0a63004cab4335b20efefaab32`.

The companion files in this audit directory are:

- CONFIGURATION-APPENDIX.md: all 700 source macro names, effective release preprocessing values and differences between translation units.
- RUNTIME-KNOBS.md: baked knob values and source use references.
- SOURCE-METHOD-INDEX.md: source definitions of Bot and World methods, including disabled alternatives.
- inventory.json: structured source declarations and effective macro environments.
- Per-translation-unit effective-macros snapshots, plus selected preprocessed source files for tracing actual compiled branches.

The compiler snapshots use the release target and defines. They establish preprocessing, not that a particular branch executed in a particular match. Runtime conditions and earlier returns were inspected separately for the important interactions described above.

Source directory: `C:/projects/cambridge battlecode/work/doomsday-movement-20261110/arena/bots/v306AltarPressureReach/src`.

Frozen release receipt: `C:/projects/cambridge battlecode/work/doomsday-movement-20261110/arena/bots/v306AltarPressureReach/release-build.json`.
