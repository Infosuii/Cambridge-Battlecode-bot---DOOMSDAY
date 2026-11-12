# cambc 4.0.0 improvement plan (26 Oct 2026)

Base: **v57** (team bot = nb4 + v54–v57 + learned draft net + camp net). On engine 2.0.0 it beats nb4 66% (unseen) /
62% (official). Lab: `ENGWASM=tools/viz/v2_0_0.wasm BOTS_DIR=v4/bots`; held-out maps `v4/maps_test4`; 100 games per test.

## Running now
1. **Black-box search** on v57's 48 knobs (`knob_v4_run1.*`, E49).
2. **Self-play draft-net retrain**: `draft_data4.js` (4,400 random-lineup games on 220 training maps, v57 both sides) →
   `draft_fit4.py` (fine-tune draft_net.h from the shipped weights, L2 pull toward them, validation on unseen maps) →
   v57 + new draft_net.h vs v57, 100 games on maps_test4. The shipped net barely predicts lab outcomes (val log-loss
   0.689 vs 0.693 chance on a smoke set), so there is room.
3. Next after the draft: the same loop for the **camp net** (neural_policy: 18 features → 16 → 1). It needs a lab
   export of the per-decision candidates and the outcome (ngp::trace exists for this, `kTraining`).

## Powerful techniques (ranked by expected gain per hour)
1. **Draft lookahead with the net** (10x draft fuel): instead of greedy "best next pick", search the rest of the draft:
   for each of our candidate picks, expect the opponent's likely replies (their net or ladder pick rates) and our
   follow-ups; pick by expected final P(win). Cheap: 12 candidates x a few replies x 64-unit net ≈ tens of thousands
   of fuel. Only the first draft turn has 10x, so precompute map features + the full lookahead table then.
2. **Exploits of the rules (all legal, test each in the lab with 100 games):**
   - **Respawn denial:** "any occupied spawn tile delays the entire group". Park one champion on the spawn tile of the
     enemy's best gem camp (V54_HOLD only does this for our own sole camp when ahead). Extend it to the
     enemy-side camps when the map has few big gem groups.
   - **Capture reset:** "admitting an enemy resets progress". Step one tile into an enemy capture region during
     their 5-turn timer; it costs a step and wastes their whole clear.
   - **Altar-lock channel cancel:** placing a lock cancels every tribute channel at that altar, and clearing it takes 5
     attacks. Always carry one (10 gold) and place it when an enemy starts a long tribute (≥ 20 gems = 2+ turns).
     Late game this also protects a lead.
   - **One-tick big-bag tribute:** duration uses the bag at the *start*, completion tributes the *whole* bag, and
     captures resolve before channels. Where a camp spawn tile is within 1 of an altar, start a tribute with a tiny
     bag the turn before the capture completes, and the whole capture is banked in one tick.
   - **Stun breaks tributes, damage doesn't:** focus stuns on enemy tributers (Ren/Ryth/Prism/Tavi/C&I), and tribute
     with Marcella (stun-immune) when contested.
   - **Turn priority:** `set_priority` reorders our champions from the next round. Put the stunner first in fights
     and the tributer first when banking.
   - **Tiebreak:** at round 2000 lifetime gold earned breaks gem ties (refunds don't count). When a close game reaches
     ~1,900 rounds, farm gold clusters and kills.
3. **Glitch fuzzer** (novel): the lab can run the engine with scripted actions. Fuzz edge cases (dash over holes onto
   spawn edges, teleport-crystal targets, ward on occupied tiles, tribute + capture same round, lock + tribute same
   turn, dead-champion shopping, Tavi buy/sell loops) and check invariants (gems or gold gained without a capture, kill
   or tribute; illegal tiles reached). Any confirmed glitch becomes a scripted exploit.
4. **League training** (PSRO-lite): keep a pool of strong but different bots (v57, nb4, nb2, provided bot, old meta
   lineups, exploit variants) and tune against the mixture, not just v57, so gains carry to the ladder.
5. **Map-aware knobs** (A2_CTX, built and checked on 3.0.2): re-run on 4.0.0 once the 48-knob search settles.

## Best use of the 10x draft fuel (1M on the first draft turn)
Fuel is not the bottleneck during play (v57 lost 0 and 2 turns to fuel in two full real games), so the draft turn
should buy *better decisions*, not rescue lost turns:
1. **Draft lookahead** (above): the biggest direct lever, since the draft is v57's largest learned gain (+8).
2. **Map analysis written to the 1024-byte draft memory**: distance tables from both spawns to every camp group and
   altar (walking + dash bridges), contested-middle groups, unreachable altars and islands. Champions then skip
   rebuilding fields (fields built from spare fuel "never arrived on islands", A2_FIELDFIRST) and spend the saved fuel
   on a deeper fight search (raise APEX_DET_TS_BUDGET / the playout horizon).
3. **Map-conditioned plan**: choose a knob preset per map (ml_plan presets or the map-aware knobs) and pass it in a
   draft-memory byte (A2_MLPLAN does this from the draft net; currently off). Test once the knob search ends.
4. **Opening schedule** (A2_DPLAN rollouts): earlier result: short own-half plans neutral to positive, long plans
   lose. Low priority.
