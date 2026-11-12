# Varg mechanics and restricted shield forecast

Production remains unchanged: default release5cf28cb7 and ordinary productivity
traceb4bc106c reproduce exactly from exported source/SDK/CMake. TRACE_MODEL and
TRACE_SHIELD default0. No survival, objective-price, item or draft change.

## Mechanics, measured separately from forecasts

Four existing idle role games are reanalyzed; no new matches for this audit.
Corrected-02 derives the candidate body from frozen SDK quotes (A1/B6). The
first pass mistakenly used body1 on sideB; its empty/opponent audit and the
type-assertion failure are retained and excluded from the corrected summary.

413 camp-target basics contain168 collateral camp hits, including41 diagonals.
All153 eligible full-damage comparisons match; no radius/amplitude anomalies.
This confirms the public SDK's radius1 as Chebyshev splash, with full damage
to these untruncated camp neighbours.53 shield casts show51 zero-duration
expirations and2 positive-duration depletions. Duration0 absorbs the camp phase
and is removed at owner start; depleted shields disappear immediately.

Example: expanse-A R155 has one live wolf1189HP, Varg820HP, raw hit80.5,
reset cooldown7/8, shield250 with duration5 and cooldown0/8. Raw/reset timing
gives14 owner rounds and260 future incoming HP. Two shields each absorb five
20-damage camp phases, leaving exactly60HP loss. The older quantized/no-reset
upper bound was300. Subtracting nominal shield capacity would be incorrect:
most of each250-point shield expires unused.

## Bounded diagnostic implementation

shield_clear.h handles one stationary live damaging member, constant raw damage,
current reset/shield cooldowns, existing shield, strict85%-HP shield trigger,
and one cast per turn with reset priority. It models death and a96-turn horizon.
It does not model splash, movement, other actors, healing or Heart's passive.
10,000 exposure/cast-coupling invariants plus native phase examples pass through
WASI/Node; the existing14,544 clock and10,000 reset-damage checks also pass.
This is arithmetic/logic coverage, not native host ABI coverage.

Quotes use only personal SDK observations, remembered member HP and public
metadata. Native replay states supply outcomes and membership sanity checks.
Late single-live samples are marked and excluded from baseline first-contact
timing metrics; each model family is scored within its own quoted window.

## Instrumentation failures remain visible

52 new diagnostic games have zero native faults. The initial12-game pilot has
two fuel-outs, quadrants A/B at R10, before any shield projection there. It is
rejected for clean calibration. Extensive unissued fields were formatted on a
cold turn under the former22k admission gate; the new gate requires45k.

Fresh quadrants controls and a subsequent12-game run are runtime clean, but
the trace formatting cap suppressed second-record shield metadata. That cohort
has n0/null shield accuracy, not zero error. Those outputs remain intact.

Version2 compact atomic quotes preserve old-format reader compatibility, fit
within the existing512-byte line reservation and avoid a second trace call.
Final contested records have maximum lengths296/294 bytes. The final two
contested capsules total12 games; another12 use idle. All40 games after the
initial rejected pilot are runtime clean. No unlogged prediction is recovered
from future outcomes. tools/dz_compare.py records runtime-control comparisons;
diagnostic banking is not release-strength evidence.

## Prospective results and limits

The final v76 cohort issues27 forecasts:20 clear,6 change goals,1 predicted-dead
window changes goals. Most completed windows have real helper damage or shared
tanking. Only one positive-damage window meets the strict unshared criteria;
it matches clear time, HP loss and both shield casts. Two additional no-exposure
clears are not counted in the positive-damage metric.

The unchanged model on six idle development geometries yields11 eligible
unshared positive-damage clears,1226 observed HP loss. All11 clear times and HP
losses match exactly; predicted/observed shield casts15/15. The older unshielded
estimate has128.71% positive bias on these SAME windows. Both full reports keep
assisted, changed-goal, dead and censored outcomes explicit.

These completed windows are conditional on the existing planner accepting and
finishing the job; they do not validate admission of previously rejected jobs.
This supports the restricted single-live mechanism. Contested coverage is sparse,
and the model covers remaining clears after earlier damage, not an entire
splash-group job. Full V-M1 remains OPEN. No safety relaxation, global discount,
new seed independence, formal parity or policy promotion is claimed.56 local
capsules verify;50 Python and12 Node tests pass. All selected controls and
config/paths.json are preserved. Prospector/advanced auction/EE/gear remain off.

Next: a bounded stationary splash-group model with explicit per-member HP and
public geometry, then separate prospective validation. Preserve cast priority,
physical fuel checks and fresh run names. Heart's health-dependent damage and
shielding, internal movement and crews remain separate missing mechanisms.
