# Algorithm specifications (DOOMSDAY Zero)

**Notation.**
- `t` is the round, `c` a champion, `C` a crew, `g` a camp group.
- `F_g(p)` is the walking distance from tile p to group g's spawn-tile set (engine distance field).
- `GE` is gem-equivalents.

All engine values are runtime-read (GAME_MECHANICS). Constants marked `[cal]` are calibrated by the procedures in
VALIDATION_PLAN.md. Constants marked `[default]` are starting values.

---

## 1. Shared quantities (per turn, ≤1k ops)

```
income_us     = EMA_50(Δ(banked_us + Σ ally bags known)/round)                     // gems/round, team
gem_income_them = Δ global_submitted_gems(enemy) over last 100 rounds + seen enemy bag growth
T_us   = max(0, 1000 − banked_us − 0.7·Σbags_us)   / max(ε, income_us)
T_them = max(0, 1000 − banked_them − 0.7·Σbags_them_seen) / max(ε, gem_income_them)
T_end  = min(2000, t + min(T_us, T_them));   R = T_end − t                          // remaining productive rounds
ρ̄(c)  = EMA_50 of champion c's GE income per alive round   [default prior 0.45; clamp 0.15..1.5]
```

## 2. Exchange rates

```
λ_gold(t)  = a · R(t)                      [cal: a from regression of next-100-round income on equipment value; default a = 0.25/900]
             clamp [0.02, 0.6]; when T_end==2000 (tiebreak relevant) floor 0.02
DeathCost(c) = bag_c + λ_gold·(kill_gold + hunter_bonus_enemy) + λ_tempo·respawn_time·ρ̄(c) + V_obj_lost(c)   [λ_tempo default 1, cal]
KillValue(e) = bag_e + λ_gold·(kill_gold + hunter_bonus_us)·goldmult(killer) + λ_tempo·respawn_time·ρ̄_enemy
goldmult(c)  = 1 + 0.33·[Vesper] + 0.10·[Treasure emblem]       // additive, verified
```

## 3. Economy

### 3.1 ObjModel (validated before decisions use it: VALIDATION V-M1)

```
DPS_camp(c) = str_c·(1+monster_c)·hit_c + Σ_slots dmg_s(c)/max_cooldown_s + reset_c·str_c/8 + passive terms
              hit_c = 1 (melee); ranged = 1 when standing (move or attack rule)
              Vendetta: + spell resets on credited camp kills (multi-camp groups)
              Varg: splash adds str per extra adjacent member
T_arr(c)  = F_g(pos_c)   (unknown field → 1.3·cheb, flagged low-confidence: no commitment > 30 tiles)
T_ready   = max(max_c T_arr(c), respawn_round_g − t)
T_clear   = κ_type · HP_left_g / Σ DPS_camp(c)              [κ default 1.0 single, 1.1 multi; cal]
D_taken   = Σ_m str_m · hit_rate_m · alive_rounds_m · (1−jungle)·(1−durability)   [hit_rate_m from CT-11; default 0.5 (cooldown 2)]
T_cap     = capture_time(cap) (5 or 3)
Reward_GE = gems_g·(1 + 0.25·[cluster ∧ prospector(cap)]) + λ_gold·gold_g·goldmult(cap)
Feasible  = D_taken ≤ Σ_c (hp_c − 0.25·maxhp_c)  ∨ heal plan (recall 5/3 + 1 round on spawn = full heal)
Cost      = Σ_c T_ready + |C|·T_clear + T_cap         [champion-rounds; others leave at last kill]
ρ(C,g)    = P_ok(C,g)·Reward_GE / Cost
```

`HP_left` persists across partial clears (camps don't regenerate, verified).

### 3.2 Contest probability

```
S(X) = (Σ hp)·(Σ dps)                                      // Lanchester-square strength
pressure_g(τ) = Σ_e P(e reaches g within τ)                // EnemyBelief ramp (§9)
P_ok = 1/(1+exp(−2·(ln S(C) − ln(S_enemy·pressure + ε))))  // ≈1 with no pressure
```

### 3.3 Sequential auction (each champion computes it; commits only its own slot)

```
replan(me):
  fixed = allies with fresh slot (≤3 rounds) whose objective is valid and progressing
  free  = alive allies \ fixed ∪ {me}
  cand  = per free c: top-M (M=8) by single rate, pruned by F_g ≤ 45 or static value rank ≤ 25
          ∪ BANK(c), SHOP(c), respawn-arrival windows (respawn within 25)
  repeat until free = ∅:
     for g in cand: grow crew C_g from nearest free champions while Δteam = ρ(C+c)|C+c| − ρ(C)|C| − ρ_alt(c) > 0
                    (capture-bound g: |C| = 1)
     pick (g*,C*) maximising Σρ − 0.5·regret ;  add follow-up γ·max_g' ρ({c}, g' | from g*)  (γ=0.5 [cal])
     capturer = member with farthest next objective; prefer Vesper only if gold_g ≥ gems_g·5 and Δ ≤ 3 rounds
  hysteresis: switch only if ρ(new) ≥ 1.15·ρ(current)
  publish slot: objective code, on-site flag
triggers: completion/invalidation, death, respawn, new group state seen, contact start/end, crew-mate slot change, every 8 rounds; FULL tier only
```

**Progress contract.** Each job must show progress every ≤6 rounds: distance falls by ≥1 per 2 rounds, or HP falls,
or the capture timer advances. Otherwise release it, set `avoid[g] = t+15` (40 on the second failure), and replan.

### 3.4 Cluster circuits

```
eligible(c) = map has ≥4 capture-bound groups within a 25-tile tour of c's area
next(c)     = argmax_g∈clusters gems_or_gold_value(g)·mult / (max(F_g(pos), respawn_g − t) + 1 + T_cap(c))
```
The CLUSTER_RUN role is excluded from crews unless DEFEND/ESCORT fires.

### 3.5 Partial-clear resume

A PARTIAL group (HP_left < max, persisting) keeps its reduced T_clear in ObjModel, so abandoned work is valued
correctly. It is re-wakeable: it will attack again once a champion enters range.

## 4. Banking (burglar cutoff)

```
h(c)   = h0·(1 + κ_p·pressure(pos)) · (1 + κ_hp·(1 − hp/maxhp))    [h0 = own observed deaths per alive round, prior 0.002; κ_p 3, κ_hp 1 cal]
T_next = rounds to next natural bank opportunity (altar within +4 of planned path) else full trip
C_trip = (F_altar(pos) + max(1, ceil(0.1·bag)) − detour_saved)·ρ̄(c) − [Marcella]·λ_gold·2·bag
bank   ⇔ bag·h·T_next ≥ η·C_trip  ∨  mode==ENDGAME_RACE ∧ bag≥1  ∨  banked_us + bag ≥ 1000
altar  = argmin F_altar + 5·pressure(altar) + 50·[enemy lock seen] + 30·[altar not reachable safely]
```

**Tribute execution.**
- Path to an adjacency tile, then `submit_gems`.
- Stay until done. Damage does not interrupt, so leave only by EE RETREAT (P_die_next > 0.5).
- A newly placed enemy lock cancels the tribute. Then either attack the lock (5 hits, if no threat) or choose another
  altar.

**Locks.**
- Carry one when gold ≥ 40 and the next item is not affordable.
- Place it on the enemy's nearest altar when a visible enemy carrier with bag ≥ 60 is within 6 of it, or in
  ENDGAME_RACE when `T_them ≤ 150`.

## 5. Engagement Evaluator

**Scene.**
- Allies and enemies within 10; awake camps within 5. At most 11 units, nearest first.
- **Phantoms:** `n_h = max(0, pressure(pos,5) − visible_near)` at mean visible-enemy stats (weight w_h, default 0.5).
- **C&I:** one fate unit, `hp = min(hp_C, hp_I)`.
- **Cooldowns:** use observed values where readable (CT-8). Otherwise assume ready in the pessimistic variant only.

**Stances:**
- FIGHT(t1), FIGHT(t2): the best 2 targets by `ttk/KillValue`. A "recalling" target counts as such only if channel
  age ≥ 2 (anti perma-recall).
- HOLD(objective), if on or adjacent to the objective region.
- KITE(t), if ranged and t is melee.
- DISENGAGE, toward the crew centroid or safe side.
- RETREAT, toward spawn or a recall-safe tile.
- CONTINUE.

**Attrition model** (H = 4, deterministic, two variants):
```
join(u) = max(0, cheb(u,x) − range_u − 2·dash_ready_u)
per τ: damage = Σ joined str·hit + first-use bursts (damage_amount where computable) ; focus: ours→target / lowest EHP; theirs→lowest EHP in reach (ties → bigger bag)
       stuns cancel the stunned unit's next τ (Marcella immune); shields absorb first; Ren retaliation; Heart +missing-HP; Varg splash
       C&I die together
optimistic: phantoms ×0, unobserved enemy spells on cooldown; pessimistic: phantoms ×1, all ready
V = (1−π)V_opt + πV_pess,   π = 0.5 + 0.3·[bag≥40] + 0.2·[respawned <25 rounds ago] + 0.2·[no crew stance]
```

**Value:**
```
V(s) = Σ_killed KillValue − Σ_dead DeathCost + V_obj·P_obj(s) − V_obj_lost(s) − ρ̄·rounds_diverted(s)
escape (DISENGAGE/RETREAT): pursuit rounds along flee path; D = Σ dps·n + bursts; P_die = clip((D−hp)/(0.25D)+0.5,0,1)
```

**Decision.**
- `s* = argmax V`.
- Hysteresis: leaving FIGHT or HOLD requires `V(new) > V(old) + 0.15·DeathCost(me)`; re-engaging after DISENGAGE has
  the symmetric margin.
- Override: if `P_die_next > 0.5`, any switch is allowed.

**Channels.** While channelling, the stance options are KEEP vs CANCEL+X, with the same valuation:
- tribute: damage does not interrupt it
- recall: any damage interrupts it, so cancelling is free when a hit is imminent

**Calibration (V-M2).** On recorded contacts the 4-round death Brier score must beat a baseline (HP-fraction plus
local-numbers logistic). Fit ≤8 scalars: w_h, π terms, the margin, α, the σ factor, λ_tempo, the join weight.

## 6. Action scorer (all concrete actions)

**Candidates:**
- moves: {stay} ∪ legal moves from the SDK mask
- basic attack: none or in-range targets ≤3 (enemies, camps of the objective, altar lock)
- ability: none, or a ready slot with a valid target or tile
- consumable or ward: optional

Legality rules are applied before scoring (SDK §3).

**Score:**
```
score = Σ dmg_now (engine damage_amount for spells; str·mult for basics) ·(1 + kill_bonus·[kill])
      + stun_value·[stuns a threat]   + objective_contact (camp hit / capture tile occupancy)
      − κ_r·threat(end_tile)          // Σ_e dps_e·[cheb ≤ range_e+1(+2 dash)] + ready bursts in reach + awake camp hits
      − κ_g·dist_to_goal(end_tile)    // stance/role goal
      + κ_a·[ally within 2] − reserve_penalty(spell)
```

| Stance / role | κ_r | κ_g goal | Notes |
|---|---|---|---|
| FIGHT(t) | low | t within range | Kill bonus high; focus t |
| HOLD(o) | medium | stay on o's spawn tiles | Never step off capture tiles unless P_die_next > 0.5 |
| KITE(t) | high vs melee | range+1 from t | Ranged: shoot only if t ends its turn out of reach next round |
| DISENGAGE / RETREAT | very high | safe point | Free-action rule: hit if it doesn't cost the move |
| TRAVEL (no threat) | low | `F_target` next moves | Choose among `next_moves_from` the step with the lowest danger and best bush cover |
| CLEAR (camps) | camp hits | in range of the weakest member | Tank rule: the highest effective HP (HP × (1−jungle)) champion stands nearest so camps target it |
| CAPTURE | — | a spawn tile of the group | Choose the tile with the least threat; capturer only |

**Spell policy** (from engine payload kind, not champion name):

| Kind | Policy |
|---|---|
| damage / aoe on enemies | Use when it kills, or when the stance is FIGHT/HOLD and the target will take more than 15% of its HP. AoE needs ≥2 targets, or 1 with a kill |
| damage / aoe on camps | Only if no enemy within 10 (spell reservation for fights); AoE when ≥2 members in radius |
| cc (stun) | Highest-dps enemy in reach that can act before our next turn, or a tributing or recalling enemy (interrupts the channel). Never on Marcella (immune) |
| attack_reset | Immediately after a basic attack when a second attack is legal and useful. Marcella's enhanced reset is used to stun a fighting or channelling enemy |
| dash | Gap-close in FIGHT (3 tiles from target), escape in DISENGAGE/RETREAT, or cross holes when travelling (TRAVEL only if it saves ≥2 rounds and no fight is predicted within 8 rounds). Heart's landing dash: ≥2 enemies in r1 at landing, or a fight-opening stun |
| shield | When predicted incoming damage this round ≥ 50% of the shield amount (EE scene), or before entering a camp clear as tank |
| heal (Willow) | Ally with the largest missing HP among those predicted to take damage; heal amount from `heal_amount(target)` |

**Passive-specific rules:**
- **Vendetta:** prefer last hits (camp or enemy), since a credited kill resets cooldowns.
- **Prism:** carried gems add focus, so the bank cutoff gets a −10% bias while fighting.
- **Ryth:** Health shards add strength.
- **Heart:** low HP adds damage. The EE model includes it; no suicide bias.
- **Tavi:** shard purchases in the field are allowed (the gear planner may buy anywhere).
- **Varg:** splash, so prefer targets adjacent to others.

## 7. Gear planner

**Candidates:** the next shard of each family toward its emblem, at most 2 families in progress at once;
consumables; Greed only after 3 emblems.

```
ΔGE_i over horizon R:
  Str/Focus shard: ρ̄·(growth/stat)·f_damage_bound·R   + fight term ε_f·(growth/stat)·kill_rate·KillValue·R
  Health shard: ρ̄·0.5·(growth/maxhp)·f_contact·R + death-risk reduction·DeathCost·rate
  emblem (5th shard) passive:
     Monster 0.15·f_clear·ρ̄·R ; Jungle (recalls saved/round)·6·ρ̄·R ; Durability 0.10·dmg_rate·(DeathCost/maxhp)·R
     Treasure λ_gold·0.10·gold_rate_c·R (all gold incl. kills) ; Prospector 0.25·7·cluster_rate_c·R (floor-aware)
     Capture 2·capture_rate_c·ρ̄·R ; Home 2·recall_rate_c·ρ̄·R ; Hunter λ_gold·50·kill_rate_c·R
     Tribute / Skirmish / Collectors: value 0 until CT-12/15 resolves
choose argmax ΔGE/cost; commitment: finish an emblem once 2 shards owned unless an alternative is ≥1.5×
```

The rates come from the champion's last 100 rounds. Before then, use role priors:
- **Clearer:** Monster, then Jungle.
- **Cluster runner:** Capture, then Prospector.
- **Banker (Marcella):** Jungle, then Durability.
- **Vesper:** Treasure versus Prospector, by her measured cluster and gold rates.

## 8. Race controller (TEAM_MODE)

| Mode | Trigger |
|---|---|
| ENDGAME_RACE | T_us ≤ 150 or T_them ≤ 150 |
| DEFEND_BANK | An ally with bag ≥ 60 heads to an altar with path pressure > 0.4 |
| CONTEST(g) | g in the top 20% of reward, pressure > 0.3, S ratio ≥ 1.2 |
| REGROUP | ≥2 allies dead, or average HP < 40%, with the enemy ahead |
| FARM | otherwise |

The mode is published only when it changes.

## 9. Opponent modelling

```
P(e within r of p in τ) = clip((r + τ + k_unseen − cheb(last_e, p)) / (k_unseen + τ + 1), 0, 1);  dead → 0 until dead_until
symmetry prior (before first sighting): enemy expected at mirror(our top-3 objectives) at same rounds
perma-recall detector: channel kind=recall observed and cancelled within 1 turn in ≥50% of ≥10 observations → treat 'recalling' as normal
style (R100, optional): {default, cautious, aggressive} parameter sets; <20 observations → default
```

## 10. Draft engine

**Utility of a lineup L:**
```
U(L) = w1·ClearPower(L, camp-HP mix) + w2·Sustain(L, camp damage) + w3·FightPower(L, revealed enemy picks)
     + w4·Mobility(L, value behind holes/gaps) + w5·Econ(L) + Σ synergy − RoleViolations
Econ: Vesper gold mult × expected capture-gold share; Marcella 2·expected banked gems; Prospector/Capture cluster value × cluster share of map value
Role constraints: ≥1 frontline (HP ≥ 1000), ≥1 stun/burst, dash if ≥15% value is gap-gated, ≤2 of {Cassi-pair, Stellar, Prism} on camp-heavy maps
pick = argmax_{x} max_{completion ⊇ ours+x} U      // exhaustive ≤ C(12,5)=792; draft turn 1 has 10M fuel
```

**Weights.**
- Before DZ plays: a research prior.
  - Top teams' core is Vesper, Heart, Vendetta, Marcella, plus C&I, Ryth, Tavi or Willow.
  - Default 5-pick: Vesper, Heart, Vendetta, Marcella + (C&I | Ryth), by map openness.
  - 4-pick: Vesper, Heart, Vendetta, Marcella.
  - 3-pick: Heart, Vendetta, Marcella.
- After the DZ walking skeleton plays: **league-selected per map** on DZ itself (V-T2), with LOMO to set `w` for
  unseen maps.

**Safety.** Pick within the first 1M fuel. A fallback ordered list guarantees a legal pick even if the optimiser
fails.

## 11. Opening planner (draft instance, after the lineup is final)

A 120-round economy-planner rollout from spawn, with ObjModel and no enemies, plus hill-climbing over the first 2
jobs per crew (≤200 rollouts).
- **Encoding:** per slot, 3 jobs × (7-bit group, 2-bit role, 8-bit start) in ≤32 bytes.
- **Runtime:** a ×1.3 prior inside the auction, dropped on the first mismatch.

## 12. World and pathing

- **Fields** come from the engine. `F_spawn` and `F_altar[k]` are computed at boot. `F_group[g]` is built for the
  nearest 25 groups first, then incrementally (≤N per turn by the Governor).
- **Danger-aware stepping** chooses among `next_moves_from(pos)` (all optimal steps), with ties broken by danger and
  bush cover.
- **Fallback movement** is `move_towards` when no field exists.
- **Local danger window:** 17×17 on threat turns only.

## 13. SafeMode (always-available fallback behaviour)

```
if enemy within its reach+2 and hp < 60% or outnumbered: move away from nearest enemy along F_spawn (attack first if melee & adjacent)
elif bag ≥ 30 or (bag ≥ 1 and altar ≤ 8): bank at nearest altar
elif on spawn and gold ≥ next shard: buy fixed role build
else: nearest group by F_g with no enemy seen near in last 10 rounds: clear (attack nearest member) / capture
```

## 14. Wards

- Place a ward on recharge.
- Target, in order:
  1. the approach tile to the current objective that maximises newly covered path tiles from the enemy side
     (`ward::visible_tiles_from`)
  2. when banking, the altar approach
- Publish sightings in SIGHTING messages.

## 15. Conservative defaults for unresolved engine items (until CTs close)

| Item | Default |
|---|---|
| Host-call costs | Assume 2k fuel per distance-field compute on 100×100; cap at 5 per turn |
| Enemy cooldowns unreadable | Pessimistic variant treats them as ready |
| Tribute, Skirmish and Collectors emblems | Value 0 (not bought) |
| Hunter | +50 |
| Camp hit rate | 1 hit per round (pessimistic) for feasibility; 0.5 for rate |
| Hidden enemy `is_alive` | Unknown, so use `dead_until` from observed deaths |
