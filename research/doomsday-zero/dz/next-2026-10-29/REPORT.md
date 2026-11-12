# Bounded pathology check and Z14 draft screen — 2026-10-29

The selected default release is preserved byte-for-byte:
`4ee9731c53c76e65bb43b4285a092664803e7011fd86359636f1258de11bcaa4`.
No experimental policy or draft table was promoted. Prospector/JOB_GEAR stays off.
88 new full local games completed with zero candidate native faults/fuel-outs;
the six trace games also have zero caught action/module errors. No ladder action.
All eight new capsules and five restored foundation capsules pass dz.py verify.
33 Python tests pass. Native host tests were not rerun: this device lacks g++.
A WASI substitute compiled after matching the repository's exception flags, but
the available Python Wasmtime could not execute exception-reference modules;
that attempt is not a passing host check. Production release builds succeed.

## Three pathologies: stop after this bounded check

`DZ_CREW_REACH=1` rejects known unreachable fields in the leader crew pass and
contract retention. Cold approximate distance remains an estimate, not proof.
The default is zero. Frozen source in each capsule defines the exact experiment.

The six-map-side trace removed the original islands-A alarm, but produced a new
islands-B alarm: R1055, slot0, group41, (26,0), distance25, respawning. Corridors-B
and famine-A retained their original alarms. Total remains three. Across 30
matching R1000 body snapshots, stalled time fell 0.4201 percentage points and
idle fell 0.1971 points. This is a small targeted diagnostic, not a full-pool result.

Release checks regress: versus the selected foundation on matching six cells,
banked delta is -45.5 (descriptive SE35.35) against v65 and -38.33 (SE25.20) against
v76. All changes are on islands; corridors/famine release cells are identical.
Do not enable the reach gate on this evidence. Reachability of a camp tile can
also differ from reachability of an attack position, which needs separate modelling.

Corridors: the unchanged R879 Bank alarm and the scorer confirm that the disabled
reach-only branch's comment is not the active policy: active scoring still uses
proximity danger. The previous full-pool reach-only regression rules out simply
switching branches. No relaxation of real enemy reach was made.

Famine: an offline pinned-engine scene at R135 confirms Vendetta alive/full HP at
(10,64), live camps at (9,64) and (10,65), with native camp0 at (8,64). The trace
still reports no cached group field, field budget30300, approximate distance2.
Cold-field/root selection remains unresolved; group membership and the body's
personal visibility still need confirmation. Adjacency alone must not be counted
as work on group0. No productivity reclassification was made.
Reproduce with dz_extract_replay.py from dz-resume-cold-retry-productivity-01,
02famine A, then dz_scene.mjs at R135/body0 with NFS_REPLAY_ENGINE=2.0.0.

## Z14 progress

Added opt-in draft variants 4 Willow core, 5 Prism/Tavi, 6 linked duo core, and
7 Ryth/Tavi. Their candidate sets come from the supplied elite composition
research, not opponent code. Variant-specific additions compile out of the
default, preserving its exact binary. Existing variants0–3 and table remain.
These are draft screens using existing kit/shop logic, not dedicated kit tuning.

Prespecified development maps: 00expanse, 00lanes, 01fracture, 02treasure-box,
01boss-battle, 00eight, 00dunes; both sides. None is a registered held-out map.
Frozen v65 supplied selection results; only aggregate winner7 was confirmed
against frozen v76. No release holdout or new seeds were used.

| Variant | v65 banked delta / descriptive SE (14 cells) |
|---|---:|
| 4 Willow | -56.43 /65.36 |
| 5 Prism/Tavi | +27.29 /60.44 |
| 6 linked duo | -6.00 /31.73 |
| 7 Ryth/Tavi | +50.50 /65.61 |

Variant7 v76: 259.79 versus251.79 banked, +8.00 /15.48 SE, zero wins either side.
Deaths24.50 versus24.07. The aggregate gain is uncertain and does not justify
promotion. A per-map v65 shortlist suggests7 on dunes/eight/expanse and5 on
treasure-box; this *mixed* table has NOT been confirmed against v76. It is only
a hypothesis, never installed. Do not reinterpret variant7's confirmation as
validation of that mixed table. No competitive parity or strength gain claimed.

dz_draft_select.py now accepts explicit IDs (--variants 0 4 5 6 7), rejects
duplicate/incomplete/faulty map-side evidence, and excludes HOLDOUT.md's registered
every-fifth maps. Four tests cover those safeguards. Its hypothetical total gain
is normalized over the baseline pool, not an independently measured new pool.
Use the saved dz_compare.py outputs and RESULTS.json for paired comparisons.

## Setup and next work

Fresh source checkout: work/pure-zero-filtered on the requested branch/checkpoint.
The named C:\projects checkout was absent. This is a sparse partial clone because
the original archive/full-history transfers were slow. Completed remote experiments
remain in Git; absent working-tree paths are sparse, not deleted.
2,931 supporting files were restored with dz_support.py verify/restore. Five
foundation capsules were restored and hash-verified, including both productivity
pools and the frozen idle/v65/v76 binaries. Installed pinned runtime verification
is recorded separately: all build-toolchain entries match; an old asset bundle
had228 absent/different files.188 were reconstructed in a workspace overlay from
hash-identical local assets;40 remain unavailable. This is not a full archive
restoration. Current engine identities match the baseline, replay assets pass
the pinned reader checks, and the default Wasm matches exactly. The original
23-part archive was not downloaded wholesale.
config/paths.json was preserved. Research-archive SHA256s are in RESULTS.json.
Research documents supply hypotheses; their historical authorisation statements
do not override the user's current request. No old bot implementation was copied.

Next focus: Z6/V-M1 clear/arrival/damage calibration on real executed jobs before
enabling the auction, EE or marginal gear planner. Existing objective arithmetic
receipts remain restricted primitives, not a completed V-M1 gate. For Z14, test
the frozen mixed-table hypothesis separately against v76, then idle/productivity
and broader release pools before considering promotion. Keep the 14 held-out
maps out of selection and the registered release holdout unspent. Do not loop
indefinitely on the three pathologies; the failed narrow fix is now documented.
