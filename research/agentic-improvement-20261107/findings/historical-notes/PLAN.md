# Autonomous Battlecode improvement: inventory and implementation contract

Prepared 5 November 2026. This is a staged plan, not a claim of an operational
unattended improvement service or a proven bot upgrade.

## Verified access and inputs

- Official CLI login works for DOOMSDAY, team
  `fcf5f666-ea55-4da0-b8d4-97c64bb37236`. Active version 111, nnrc10.
  Snapshot rank 58; unranked quota 0/50 used. Quota must be checked before each
  new group; its reset time was not supplied, so do not assume a reset schedule.
- GitHub read access works; Git transport also works. The similarly named local
  top-level folder is an incomplete checkout. Do not repair it by overwriting it.
- Recent activity includes `claude/rl-env-1104` (51f3e88, 5 November 22:24 UTC),
  `ishan/codex-20261104` (fe01bea, 21:41), and
  `johndoe/rl-learner-e3-1104` (1345fed, 21:05). Main is historical.
- A sparse, separate clone of the RL environment branch is in `source-rl-env`.
- Official CLI 5.0.0 downloaded from the official distribution endpoint and
  verified against the site's SHA-256:
  `4a94c15027d94c4702e1b84471cb25110a5d2c4e3c67976e65439d93582e774c`.
  New SDK/project and 128 maps are in `arena`. Old CLIs remain intact.
- Both recent downloaded ranked summaries report engine 3.0.0. CLI 4 produced
  unknown champion/phase/item labels. CLI 5 resolves these on the same games.
  A five-round starter release smoke test runs successfully. This is a runtime
  check, not a completed-game or strategic benchmark.
- Recovered v111 builds successfully against the new SDK. Injected release Wasm
  SHA-256 `0896a189a0bb99452b72617307ea86a4cfda82df76daa91482febef58039c423`
  matches the release identity in the recent branch baseline report. A complete
  v111 self-play game on 00ambush finishes at round 1272 with zero crashes.
  Same-bot self-play verifies execution, not competitive improvement.
- RTX 5070 Ti laptop GPU: 12,227 MiB reported memory. Global Python has numpy,
  but not torch or pytest. No GPU training environment has been validated.
- User permits unattended operation on this laptop and identifies this Codex
  session as today's AI account. Other daily account assignments are unresolved.

## Supplied files

- `auto.zip`: seven Python modules, config, daily prompt, RL plan and historical
  data. Contains 994 compact game rows and two experiment ledger entries.
  It has useful scaffolding, but cannot be treated as deployment-ready.
- p144/p145: text-replacement patches for an external agent2 tree. Not executed.
- `zip 111.zip`: 292 text run manifests only; no source, outcomes or weights.
- `submissions.zip`: 94,861 entries, mostly bot folders/build caches; selectively
  extracted only five source archives, avoiding wholesale cache extraction.
- v111 source archive: 40 files, 720806 bytes, SHA-256
  `72e9a198135d9b42361a223be505e379b1cf286e1223ee3daf1fbb90a34f8463`.
  Matches the archive identity documented in recent v111/v109 baseline evidence.
  Original bytes and per-file hashes are saved in `reference`.
  This establishes consistency with supplied evidence, not a remote source download.
- Also prepared nnm4, nnfinal, v86h and v92 source copies under `arena/bots`.
- No nn_rl6.py, student_10.pt or resumable optimizer state in submissions.zip.

## Important findings to retain

The archive ledger reports nnm4 at -2.0 percentage points (SE 3.7, 200 pairs)
and nnrc10 at -5.0 (SE 3.5, 200 pairs) against v109. It calls both rejected.
Those labels do not satisfy the workspace failure-investigation protocol by
themselves. Keep the historical ledger immutable; new investigations begin as
Retry required. V111 is currently live despite that historical archive result.
Do not infer an unauthorized teammate change, or automatically roll back from
that old result.

Recent branch evidence is newer and different: stock v111 vs v109 local panel
52/90 vs 49/90; family interval for the +0.033 difference is [-0.089,+0.167].
It reports 466 vs 297 fuel-out entries. This does not establish an upgrade and
does not establish that every loss is caused by fuel. A later configuration
screen's apparent development improvement reversed on held-out maps. Do not
repeat that selection mistake or reuse those maps as untouched holdouts.

Archive shortcomings requiring repair:

1. Build-cache identity is bot name only; experiment keys omit extra flags and
   source contents. Hash all source, SDK, flags, weights and compiler inputs.
2. First failing gate removes the experiment from future consideration and
   records rejected. Implement explicit investigation and focused repairs.
3. No exclusive writer lease; queue/state updates can race between RL and loop.
   Use SQLite transactions, one controller and a GPU/local-game resource lock.
4. CLI mutations retry after ambiguous errors. Never blindly retry submissions
   or match creation; reconcile remote receipts first.
5. Rollback/switch logic needs persisted recovery and team-owner checks. A
   process crash or STOP during a test must not silently leave a candidate live.
6. Fetch loses raw evidence, only takes one page, and attaches current ratings
   to historical matches. Retain raw files, page cursors, rating snapshot time,
   exact match policy identity where available, and unknowns explicitly.
7. Correlations and damage deficits are hypotheses, not causal explanations.
   Missing metrics must not become zero; truncated games need explicit handling.
8. Temporary activation for unranked testing also affects ranked games. Verify
   current platform capabilities before designing any version-isolated test.

## Shared controller for both bots

Persistent stages: collect -> validate -> diagnose -> propose -> build -> smoke
-> paired development evaluation -> investigate/repair -> freeze -> confirmation
-> platform test -> promote/restore -> monitor. Persist every transition and
receipt. A STOP file stops new work; recovery records explain outstanding remote
actions. Never overwrite frozen x1 or another checkout. Use separate copies.

One AI identity per London calendar day, selected explicitly. Store account
labels and budget state, not credentials. Battlecode quotas are team-level and
separate from AI allowances. Multiple available identities must not multiply
assumed game quota. If a provider allowance is exhausted, checkpoint and pause
AI work rather than auto-switch identities or buy credits. Local collection,
statistics and simulations can continue within machine/resource budgets.

Expensive reasoning reads a compact evidence pack: current baseline hashes,
rating/opponent/map strata, five representative failures, prior experiments,
and a limited set of exact code locations. Deterministic tools perform bulk
decoding and calculations. Do not send whole replay archives to the model.
No paid API fallback is enabled. Subscription usage and API billing differ:
https://developers.openai.com/codex/pricing

## Analysis agent

For each selected loss, save match identity, policy/version uncertainty, map,
side, engine hash, observed decisions, timeline and evidence pointers. Diagnose
crash, fuel starvation, action legality, feature freshness and logging overhead
before attributing strategy. Then inspect farm/route productivity, carry losses,
bank timing, contested resources, purchases, draft, and coordination. Compare
with a matched win and stronger opponents on comparable maps and team sizes.

Every hypothesis includes supporting and conflicting observations, a proposed
mechanism, a measurable prediction and the smallest discriminating experiment.
Use paired maps/sides/seeds/opponents, family-clustered uncertainty and separate
opponent reports. Test base/A/B/A+B for plausible dependencies. Avoid a single
pooled score hiding a regression against the actual champion.

Experience means a versioned case library of confirmed mechanisms and failed
predictions, not endlessly rereading summaries. Periodically evaluate diagnosis
precision against reviewed games; measure whether proposed repairs actually fix
the predicted event. Keep a temporally later evaluation set for the analyst.
Update experiment priorities from confirmed intervention outcomes, shrinking
sparse opponent/rating strata toward shared estimates. Preserve older cases
across engine revisions but do not mix incompatible measurements.

Failed promising experiments get approximately 2–3 focused, mechanism-driven
repairs after validating build/config/activation/order/shared state and replays.
Outcome labels: Accepted, Retry required, Conditionally useful, Parked, Rejected.
Require evidence and reasonable repair attempts for Rejected. A gate failure
alone is not rejection. Save environment scope and remaining uncertainty.

## Source-bot loop

Start by reproducing stock v111 under SDK5/engine3 with source and Wasm hashes.
Use supplied reference bots plus independently sourced current opponents where
available. Establish a frozen paired baseline at platform fuel settings.
Select one mechanism supported by current replay evidence. Generate an isolated
candidate, verify its intended code/config executes, then apply the shared
evaluation/investigation protocol. Promotion requires reliable improvement and
no unexplained runtime regression. Upload only the exact frozen artifact tested.

Reserve team game capacity and poll actual quota. Choose a panel stratified by
rating gap and play both sides. Persist baseline group IDs/opponent versions;
verify pairing from returned results rather than assuming command success.
Use group/map-family uncertainty and a fixed sample/stopping policy. Detect any
teammate live-version change and release ownership; do not overwrite their work.
After promotion, monitor version-attributed games and compare matched conditions;
do not roll back merely because opponents became stronger.

## RL loop

Prefer the recent branch's rlenv-2 trajectory contract and engine3 collectors
over porting an old logger blindly. Verify actor/export parity, feature scales,
legal masks, timestamps, recurrent reset, executed actions, per-round discounts,
termination/truncation and bootstrap rules. Test logging overhead separately.

Keep three distinct data products:

- Full simulator trajectories: own observations, masks, actions, actual behaviour
  probabilities when logged, rewards and boundary states. Eligible for the
  intended on-policy algorithm only when policy provenance supports it.
- Own ladder logs: usable for offline/value/imitation learning according to
  actual fields. No invented behaviour probabilities; historical deterministic
  decisions are not fresh PPO rollouts.
- Public opponent replays: observed legal-view action imitation/style/value
  supervision where reconstruction is possible. Hidden inputs and private model
  state remain unknown; omniscient replay state cannot leak into the actor.

Partition by episode and map family, time, opponent and engine before extracting
rows. Never put the same game or its near-duplicate in train and evaluation.
Learn from stronger and diverse opponents while retaining older league members.
Sample weak development strata without touching confirmation maps. Separate
diagnostic high-fuel runs from normal-fuel promotion evidence.

Train bounded jobs in a dedicated GPU environment; checkpoint weights, optimizer,
normalization, RNG, schemas and league. Export and verify the deployed inference
policy, including argmax/sampling, commitments, quantization and overhead. RL
candidates enter the same gate as source candidates. Training scores are not
promotion evidence. Stop expanding a failing training run to investigate its
data, reward and deployment semantics; do not automatically restart forever.

## Remaining access/configuration

The trainer has now been reconstructed as described below. Need the precise
checkpoint location if resuming nnrc10 is required; otherwise a new training
route must be explicitly identified as such. No need
to send passwords. AI account assignments after today remain to be specified;
available subscription balance is not exposed by the tools audited here.
GitHub read/clone is verified; push permissions have not been tested. No push is
necessary for local development. Live submission/activation capability has not
been exercised during the audit.

## Delivered and not yet implemented

Delivered: repeatable read-only collector, audit snapshots, two raw replay and
summary pairs with old/new decoder evidence, archive identities, selective source
recovery, current runtime/SDK/maps, starter smoke test, mutation-boundary tests.
Not yet delivered: complete controller, adaptive analyst, training job manager,
statistical promotion implementation, unattended account scheduling, proven
candidate improvement, or a new upload. Nothing here promises permanent
background execution after the chat ends.

## Scratchpad recovery update

The supplied scratchpad.zip has 931 entries, including six replays, 422 match
summaries, patch scripts, a separate experimental bot source and 89 task output
logs. Archive file inventory and hash: `reference/scratchpad-index.json`.
Summary inventory: `reference/scratchpad-summaries.json`.

326 summaries report engine2; 96 report engine3. Every engine3 summary contains
unknown champion or phase labels from an incompatible decoder. Preserve these
as historical evidence, but re-download/re-decode before using their identities
or event semantics. Do not merge all 422 rows into training blindly. Summary
count does not establish the number of independent episodes or usable RL rows.

Recovered the pinned agent2-neural branch (6c2244e) base trainer nn_rl4.py,
nn_model.py, nn_mkbot.py and nn_export.py. Applied the inspected p142 and p144
patches to an isolated copy: all patch assertions passed and reconstructed
nn_rl6.py parses successfully. This reconstructs the supplied patch sequence;
it does not establish byte identity with an unavailable original trainer.
No training script was imported or training started.

Recovered three historical model files as data: student_i2m.pt,
student_i2m_xf.pt and nn_rl5_student_4.pt. They have not been deserialized,
validated for shape/export parity, or identified as v111's checkpoint.
Hashes and source commit are in `recovered-rl/provenance.json`.

Still missing for exact nnrc10 continuation: agent2/nn_rl6/student_10.pt and any
associated optimizer/RNG state if saved by the original trainer. Warm-starting
from an older recovered model is possible to investigate but must not be called
an exact continuation. The recovered trainer still assumes the historical v4
layout, opponent copies and generated-map directories, and needs a reviewed
engine3 integration and GPU environment before running.

## v4.zip inventory update — 6 November 2026

v4.zip is the game workspace, not the sibling agent2 training directory. It is
6,295,146,560 bytes compressed, with 181,767 entries and 63,111,307,561 bytes
expanded. Inspected its directory and selected contents without expanding it.

Most expanded data is historical bench_out (56.1 GB); bots/build caches account
for another 4.85 GB. The archive contains 13,410 replay files and 2,451 map files,
including maps_pool86, maps_real250 and maps_pooltrain referenced by the
reconstructed trainer. These are file counts, not independent game counts or
verified training rows. Several pools have been used in earlier evaluations;
do not declare them new holdouts.

All 40 v4/bots/nnrc10/src files match the previously preserved v111 source
manifest exactly. No nn_rl6.py, .pt, .pth or .ckpt files are in this archive.
bench_out/nnr6 exists only as an empty directory. Keep the archive as a source
for selective recovery rather than extracting 63 GB into the working checkout.
Inventory is saved in reference/v4-inventory.json.

The missing original training files belong under the sibling agent2 folder:
agent2/lab/nn_rl6.py and agent2/nn_rl6/student_10.pt (plus the run's other
checkpoints, logs and any persisted optimizer/RNG state). Recovering that folder
would close the exact-checkpoint gap; it is not necessary to send v4 again.

## lab_kit_agent2.zip update — 6 November 2026

This is the older engine2 analysis/simulation kit, not the current neural
training directory. It has 105 ZIP entries, 1,271,691 expanded bytes, and a
handover dated 27 October 2026 (CLI4/engine2). It supplies replay analysis,
combat/farming counterfactuals, a scriptable engine host, older PPO experiments
and an engine2 Wasm. It has no nn_rl6.py or .pt/.pth/.ckpt files.

Preserved separately under reference/lab-kit-engine2 with an archive/per-file
hash manifest. No scripts from this kit were executed. Its handover's suggested
actions and 'do not retry' claims are historical reference material; current
user instructions and the mandatory failure-investigation protocol govern work.

The host explicitly does not meter fuel: it reports the turn budget instead.
It also hardcodes engine2 structure sizes and imports. It cannot provide
engine3/platform-fuel competitive evidence without reviewed changes and parity
checks. Retain its analysis ideas, but use the verified current official runtime
for acceptance. This kit does not close the exact v111 checkpoint gap; that gap
does not prevent source-bot improvements or a clearly labelled new training run
from the historical models already recovered.

## nn_rl6.zip recovery — exact v111 checkpoint found

The supplied nn_rl6.zip contains student_10.pt, value_10.pt, student_w_10.h,
the run log, checkpoints 0–14, best.pt and state.json. Preserved original files
under reference/nn-rl6-original with an archive and per-file hash manifest.

student_w_10.h is byte-for-byte identical to deployed v111/src/nn_weights.h:
SHA-256 f1555e37775fd32d99aa82463bbe30b3181e9e96e9c2caa898959b7e85c8d0ec.
This closes the missing v111 checkpoint/package identity gap. Tensor loading and
re-export parity still require validation in the GPU environment.

The recorded run finished iteration14; its best checkpoint by its own local
selection score was iteration12 (56.1%), while deployed v111 uses iteration10
(54.1%). Do not silently replace v111 with best.pt; these scores used the same
local selection pool repeatedly and do not establish ladder improvement.

The reconstructed trainer saves actor/critic state_dicts and iteration/best
metadata, but does not save Adam state or complete RNG state. Therefore continuing
from the exact v111 model/critic weights is now possible to validate; a bitwise
continuation of the original optimization run is not supported by the saved
format. No need for more archives to close the checkpoint gap. Training and
new bot submission have not started during this inventory phase.

## Training started — 6 November 2026

The inventory phase is complete. See TRAINING.md for commands and scope, and
TRAINING_LOG.md for setup failures, focused repairs and pilot evidence. The
isolated CUDA environment and engine3 pilot passed, including a real GPU update
and saved resume state. The supervisor started the ten-iteration continuation.
Training is a local background process with progress/stop controls, not a cloud
automation. It makes no AI/API calls and performs no ladder mutations.

## Autonomous routine implemented — 6 November 2026

See AUTONOMY.md and autonomy/ for the persistent collection, unranked sampling,
evidence analysis, bounded signed-in reasoning, isolated patch/build/paired
validation, platform trial and recovery implementation. The controller is running;
127 decoded games and15 unranked matches have been processed. The first training
run is complete; seven follow-up variants were tested with frozen evidence.
The route-depth candidate has a reviewable ZIP and positive opponent-panel
evidence but has not cleared the direct-v111 gate. Upload/activation is disabled
because automatic approval review rejected the combined online action under the
earlier AGENTS.md restriction. No new bot has been submitted or activated.
