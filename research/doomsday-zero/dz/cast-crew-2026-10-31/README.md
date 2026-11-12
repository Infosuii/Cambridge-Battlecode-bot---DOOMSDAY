# Resumable crew geometry and cast-aware objective work — 2026-10-31

Default-off `DZ_ECONOMY_V2=0`. **Unpromoted; competitive screening still fails.**

## Implemented

- Fixed the observed Vesper R9 cold-path fuel exhaustion. A truncated diagnostic
  with cheap volatile markers reproduces crew quotation returning with only 34
  fuel, then resuming in R10. COLD_PATH.zip freezes its source, binary, build log
  and native replay; COLD_PATH.json contains verified hashes. No match outcome is
  claimed for this diagnostic. Full profiler overhead had hidden the branch.
- Route scoring reads each home score once, outside sort comparators; geometry
  checks physical fuel at work boundaries. Merely bounding the old whole-search
  retry made elk production stall (03: 0/0). That failed source is retained.
- `FormationSearch` persists front-tile, exit-ray and helper-placement cursors.
  Each budget stop keeps a checked search prefix, never a partial executable
  formation. Roster/gear, scene/topology and expiry invalidate work. A different
  speculative quote cannot erase an unfinished job. Auction retries keep that
  coalition size and revisit pending geometry instead of restarting each turn.
  Completed geometry remains cached. Recovery and role-execution safeguards stay.
- `objective_cast.h` models owner-turn basics, reset/direct-damage casts, proactive
  self shields, one-cast collisions, cooldowns, shield expiry and credited damaging
  monster kill resets. Budget/horizon/unsupported cases return the basic fallback.
  Each living monster hits this body; no ally protection or imagined splash/CC.
- Production integrates this conditional cast schedule for ONE live monster into
  self bids, retained work, renewable quotes and wake admission. Existing multi-
  monster/crew bounds remain. Future renewal does not reuse a present shield or
  assume ready cooldowns. Exact self kit decoding is reused within the turn.
- Executor shields before the wake; a forecast requiring that first shield must
  observe its actual value before attacking. Failed casts decline the attack.
  Travelling toward a visible camp neither requires the wake shield yet nor
  spends it on a distant, out-of-range threat. Generic safeguards still own escape.

## Checked and unproven

All TEN host suites pass. New tests compare 1,500 ordered reset/phase projections
with independently derived closed-form clocks/exposure, and check shield phases,
cast collisions, arrival and budget fallback. Geometry tests resume tiny work
slices to completion and reject blocked layouts. Selected and combined Wasm build;
selected-default Mac SHA remains 437f91c3… (full hashes in BUILD.json).

Final native06: wolf 272/272, elk 570/570, layered 502/127; all six cells have zero
faults/fuel-outs, p99 fuel 81,680. Elk records 266/305 formed attacks. The unmodified
strict layered withdrawal audit passes 45/22 complete escape/heal-return cycles,
with no recorded withdrawal deaths. Mixed full-run audit is false because wolf/
elk correctly have no siege cycles. All six development capsules verify.

Final untraced Famine05 is runtime-clean but banks only 14/17 versus the selected-
source control's 400/236 (`dz-mac-control-dev-01`). Earlier01 fixed runtime but
banked 21/41; cast02 banked 70/28. These variants are not independent confirmation.
Stop larger competitive screens: fixture success has not solved contested income.

The cast timeline is conditional on a stationary focus/cast policy. Ordered multi-
target host references do NOT establish dynamic multi-monster or multi-ally V-M1.
The native logs exercise cast-aware quotes; no DZ_CAST_FUNDED line was retained,
so the shield-funded admission transaction still needs explicit native coverage.
No general runtime, combat, recovery-handoff or concurrent-crew acceptance follows.
No validation/release partition, online action or promotion was used here.

## Next source work

1. Replace the fixed-formation whole-group assumption: joint sequential focus,
   member-to-member movement, regrouping and retained partial work. Current crews
   can execute changing focuses, but quotes reject monsters outside the initial
   poses' reach. This is a central mixed-camp access/economy gap, not a retreat weight.
2. Native phase-check the production cast policy/required-shield transaction, then
   extend ability-aware bounds to changing multi-monster/crew geometry with explicit
   uncertainty. Retain the basic fallback; do not treat these restricted tests as
   general model certification. Reaudit future damage/passive/cooldown assumptions.
3. Finish siege/crew ownership, independent crews, recovery handoff, group conversion,
   equipment/income progression and bank scheduling; then joint combat/action,
   opening/map integration and the remaining conformance/release gates.

No candidate is selected. The full Z architecture/parity goal remains active.
