"""Package the stopped research state; never builds, tests, pushes or submits."""
from pathlib import Path
import json,hashlib,shutil,zipfile,datetime
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
DEST=ROOT.parent/'handoff-botx3';DEST.mkdir(exist_ok=True)
suites=['team-work','team-transfer','team-final','team-robust','team-tail','team-unseen','team-bank','team-bank-controlled','team-comms','team-intents']
records={}
for name in suites:
    p=BASE/name/'summary.json'
    if p.exists():records[name]=json.loads(p.read_text())
table=['| Suite | Arm | Wins/games | Fuel-outs | Faults |','|---|---|---:|---:|---:|']
for name,arms in records.items():
    for arm,s in arms.items():table.append(f"| {name} | {arm} | {s['wins']}/{s['games']} | {s['fuel']} | {s['faults']} |")
status='''# STOPPED — botx3 continuation handoff

The user explicitly requested stopping because of usage limits and asked for a portable handoff and fresh-agent prompt. Do not resume any job in this chat. All running experiment drivers were stopped or had already completed. The final active driver was `team_contract.py`, interrupted while compiling: `transport` built, `farm` was being prepared; no completed contract matrix exists. Latest source is X3_TEAM=12 and is **unvalidated**. Modes up to 11 have frozen completed experiments.

## Objective and restrictions

The main task is the full attached Cambridge Battlecode next-generation brief, especially a coordinated map-independent economic planner. The user previously objected to stopping after narrow heuristics. Continue implementation/diagnosis/validation, not just a plan or protocol update. NEVER submit, publish, activate, or push a bot to the official ladder. Local development and dedicated local branches are permitted. Follow the mandatory failure protocol: verify activation and inputs, inspect interactions/replays, make approximately 2–3 mechanism-driven focused repairs, test combinations and environmental scope; do not reject on one failed benchmark. Classifications: Accepted / Retry required / Conditionally useful / Parked / Rejected.

## Repository / portability

Repository: https://github.com/Infosuii/neural-networkk-battlecode

Local authoritative development source: `x1work/bots/botx3/src`. Research is `x1work/research/botx3-20261102`. Source and experiments are uncommitted. A clean local branch/worktree `dev/botx3-team-economy-20261102` was created at base `ba5802ed`, in `work/botx3-team-economy`, but **the new code was not copied into or committed on that branch before stopping**. A fresh system cannot fetch the work from that branch. The ZIP overlay is authoritative for transport. Do not assume any local-only branch was pushed.

On a fresh system clone the repository, check out base `ba5802ed` (or inspect newer changes before integrating), create a dedicated local development branch, and extract the ZIP at the repository root. Preserve existing work if using a non-clean checkout. Read the archive manifest. The overlay includes exact current source, frozen sources/binaries for important candidates, the actual local runner, scripts, generated maps, complete per-game result matrices, selected native replay evidence, and original x1 references. Full raw game directories remain on the original computer; they are intentionally omitted due to size. Regenerate specific missing replays from exact frozen binaries and map bytes if necessary.

Native toolchain used: cambc CLI 4.0.0, engine 2.0.0, SDK 4.0.0, WASI SDK 33 / Clang 22.1.0. C++20 host checks used GCC. CLI/toolchain binaries are not bundled; install the official tools. Windows paths in existing manifests are provenance, not portable path assumptions. Embedded Python 3.12 was used; ordinary Python 3.12 is preferable. Map generation requires wasmtime 50.0.1 and the installed engine-2.0.0 map-editor WASM. `team_maps.py` and `team_unseen_maps.py` currently contain a Windows asset path: adapt asset discovery on a fresh system before running. Engine assets, accounts and credentials are not included. `tools/dz.py` is the exact local runner, including pre-existing local build-cache changes, included for reproducibility rather than attributed as new work.

## Frozen baselines / prior research

Original x1 Wasm SHA256: `1746f2bb7fa341530f41bd8c8c4896b35172783f35eacee8e4a4b6ac0ceea183`.
x1c1 parent: `22e6067a423356e29e6738438f47b22d05b554767757717e58bf350392e16b13`.
Original x1 production source was never edited; its source ZIP and hashes are included. Disabled builds repeatedly reproduced original x1 byte for byte. Latest exact verification was before the unvalidated mode-12 contract edit; repeat it after resumption.

K004–K009 are complete; no universal replacement for original x1 was established. K009 parent gained 40 wins over x1 on 716 x2-build cells, lost 28 on the 720-cell v86h/v81hl robustness pool. K010 is complete (snapshot included): parent late-game economic stall attributed to indefinite home-only plan 4; historical ladder comparisons are repeated maps and different dates, not independent new trials. Original x1 remains the competitive reference. v92 was downloaded through connected GitHub and all 35 source blobs verified modulo line endings (receipts included).

The old `REPORT.md` describes the EARLIER narrow x1 experiments, not the latest team-planner work. Its findings remain historical evidence. `initial-campaign/` freezes its original matrices. Do not present the old report as a summary of this continuation.

## Implemented team planner

- `team_scheduler.h`: pure bounded greedy team auction. Visible workers bid in small crews; costs include synchronized arrival, camp clearing, respawn waiting, a single reward owner, and amortized banking. Crews are disjoint and a completed reward gets one owner. Unknown/invisible teammates retain reservations; no hidden inventory is read.
- `team_economy.cpp`: legal-view adapter, public alive-based leader election, shared assignments, local safety/capture/retreat overrides, eight-turn commitments, and budget admission.
- Draft computation: use static legal map data and actual walking fields to pass 512 bytes at draft-memory offset 480 (bank/spawn summaries, version/count/signature). Native trace measured 47,016 fuel on gold-rush and successful reads by all three champions. Large distance fields remain per-VM and are not falsely assumed shared.
- Modes 1–3: independently computed assignments; measured inconsistency and fuel overuse. Mode 4 made assignments authoritative but replaced upper-bit sightings/events. Mode 5 added dominant-resource priority preservation. Modes 7/8 moved optional computation after actions / after distance-field work. Mode 8 `team_after_fields` is the earlier promising but non-generalizing frozen prototype.
- Mode 9: visible-bag bank-cohort planner, plus four-arm transport/farm/bank/joint ablation. It selects earliest visible bank arrivals sufficient to finish the race and preserves an active capture. Bank orders are admitted before hunting. This does NOT read hidden ally bags and cannot promise a win when routes take longer than the remaining race.
- Mode 10 attempted to preserve legacy sightings/events without an explicit command tag. It confounded commands with ordinary claims; treat it as a diagnostic implementation, not a recommended protocol.
- Mode 11 uses command-intent bits in the UNUSED sixth claim slot for teams with at most five physical bodies. It preserves all upper-bit sightings/events and on-site codes, ignores the reserved slot as a phantom claimant, consumes intent on own claim writes, and preserves opening orders across later actors' initialization. Six-body teams deliberately fall back. This is the latest fully benchmarked protocol.
- Mode 12 (LATEST, UNVALIDATED): coordinator proposals are passed through the existing native `score_groups` health/risk/ownership/territory evaluator before acceptance; at most 10% local score opportunity cost is admitted. It explicitly scores a proposal before pruning and records accepted/refused contract telemetry. Verify the patch is in the correct scoring loop, compile, test activation, then resume its frozen matrix. Do not assume it improves performance.

All X3 flags default off. `X3_TEAM_FARM` and `X3_TEAM_RACE` use nonzero tagged volatile initializers to preserve executable-code and layout identity across 0/1 ablation arms. `same-code-proof.json` verifies identical Wasm code sections for modes 9 controlled, 10, and 11. Initial untagged banking builds had different code sections; they are superseded for causal interpretation. Comparing wins to original x1 alone is insufficient: protocol/hook changes can themselves alter deterministic outcomes.

## Failure evidence / interpretation

The first independent team auction spent roughly 60k fuel in a large call and repeatedly replanned idle assignments every turn. A six-job limit and idle cooldown repaired these costs. Authoritative commands repaired part of the independent-view mismatch. Draft transfer, actual commands and executor reads were confirmed in separate native diagnostic builds. Mode 5 diagnostic maximum planner cost was 34,897 fuel; mean approximately 28,118. Mode 8's diagnostic only issued three orders in 550 rounds on the inspected map, so its apparent win gain must not be attributed solely to intended planning activation.

An actual incomplete-bush-ID bug was reproduced and repaired behind X3_COVER_SAFE; native paused-flood probe returns unknown until completion. It did not demonstrate a competitive gain over BP. The stale hidden-recall report did not apply to the inspected source, which already refreshed the world before the check. Do not reapply that obsolete fix blindly.

On v92/rows-side-A native replays, the coordinated prototype had fewer idle turns but fewer completed deposits than x1, and high earned gold with inadequate banked gems. Less waiting does not automatically mean better economics. Eight losses on the new resource-layout suite had collected >=1000 but not banked enough. The inspected perimeter-banking loss first had an omniscient sufficient cohort only at R1027, with the game ending R1030: sufficient bags alone do not prove timely banking was feasible, and omniscient cohorts are not legal controller inputs. `race_snapshot.mjs` labels this limitation explicitly.

## Main results and protected-data accounting

`team-tail`: 28 development/regression maps, 224 cells/arm, x1/x2/v86h/v92, both sides. Original 100 wins /150 fuel-outs; x1c1 109/153; mode 8 114/182. Mode-8 opponent wins 32/27/28/27 versus x1 28/23/28/21. This is a promising development score with unresolved fuel and causal/transfer concerns, NOT accepted.

`team-transfer`: eight new open-grid/gated-stripe development maps, four opponents, both sides: mode 5 38/64, original 27/64, parent 36/64; mode 5 zero fuel-outs. `team-final`: eight terrain-family held-outs (cellular/rings), mode 5 tied original 33/64. Caveat: these reused resource-layout patterns across families, so this only tests terrain-family transfer, not wholly unfamiliar resource layouts.

`team-unseen`: six separately frozen new resource/bank layouts (recursive rooms/perimeter banking), four opponents, both sides. Original 24/48, parent 23/48, mode 5 12/48, mode 8 16/48. These maps are NOW SPENT DIAGNOSTIC DATA. Do not tune using them and claim they are still final validation. All prior generated suites are likewise spent. A new frozen generator/layout family set is required for another genuine final test.

Mode-11 four-arm `team-intents`, 112 development cells/arm: transport 67 wins, farm 51, bank 65, joint 50 (original 56; parent 57). All four arms share identical code sections and have 118 fuel-outs, zero own faults. The +11 transport-vs-original difference is NOT proof of farming improvement; actual farming is -16 versus its proper control and bank is -2. This motivated the mode-12 native execution contract. Mode-9 controlled bank was +4 versus its control, but the result did not reliably transfer across protocol changes.

No new strategic candidate has been accepted or submitted. Do not claim that botx3 is already stronger on unseen maps. Classify the current planner as Retry required; older insufficient models can be Parked without rejecting coordinated planning as an idea.

## Next concrete actions

1. Read source, this handoff, exact result matrices and the user's full brief. Inspect newer branch research before claiming baseline currency. Do not run historical g5070 worker scripts that can push messages.
2. Validate the untested mode-12 contract: check score capture placement and proposal pruning bypass, host scheduler tests, disabled binary identity, four-arm code-section identity, native X3_CONTRACT acceptance/refusal telemetry and preservation of capture/retreat priorities. Review potential interaction with deterministic candidate limits.
3. Resume `team_contract.py` only after checking its partial build state. It freezes existing named snapshots and refuses to change them; if source changes, use new labels rather than silently overwrite old artifacts. No matches from this matrix were completed before interruption.
4. Compare against SAME-CODE transport controls, original x1 and x1c1, by opponent and map family. Inspect gained/lost games and runtime, not only totals. No arbitrary threshold grid to rescue the auction.
5. If the native contract is still weak, investigate task service forecasts, actual champion-specific DPS, arrival synchronization versus staging timeouts, and whether bank opportunity value is missing from the auction. Preserve known-good combat/territory decisions. Do not keep expanding a naive global replacement of those decisions.
6. Freeze genuinely new resource/terrain/bank families before any final use. Existing final suites are spent. Report uncertainty with map/family grouping; tiny or selected samples do not establish superiority.

## Reproduction entry points

Build/run through `tools/dz.py` / official local `cambc build` and `cambc run`. Core host test: compile `research/botx3-20261102/team_scheduler_test.cpp` with C++20 and include `bots/botx3/src`. It checks distinct assignments, pooled crews, no overstaffing, capture ownership, unreachable/unavailable actors, and banking cohorts with legal visibility and active-capture exclusions.

Experiments: `team_screen.py`, `team_retry.py`, `team_coordinator.py`, `team_transfer.py`, `team_final.py`, `team_robust.py`, `team_tail.py`, `team_tail_final.py`, `team_unseen.py`, `team_bank_controlled.py`, `team_intent_protocol.py`, and pending `team_contract.py`. Read each before executing; many intentionally require previous exact frozen inputs. `screen.py` provides shared build/match/cache infrastructure, asserts original and parent identities, runs both sides and records hashes/receipts. Do not run `prepare.py` on the existing source; it is a one-time historical preparation script.

Native audits: `team_verify.py`, `team_final_checks.py`, `race_snapshot.mjs`; use NFS_REPLAY_ENGINE=2.0.0. `team_final_checks.py` was last successful for mode 8, before later mode-11/12 edits. Repeat relevant checks on the current source rather than implying old checks cover new code.
'''
status+='\n## Complete saved suite summaries\n\n'+'\n'.join(table)+'\n'
(DEST/'HANDOFF.md').write_text(status,encoding='utf-8')
prompt='''Continue Cambridge Battlecode botx3 development from the attached portable handoff ZIP.

First read HANDOFF.md and MANIFEST.json. The prior agent stopped because I explicitly requested stopping for usage limits. You are on a fresh system: do not assume any original absolute paths, installed tools, credentials, or uncommitted branch contents are present.

Repository: https://github.com/Infosuii/neural-networkk-battlecode. Base used: ba5802ed. Extract the ZIP overlay into a clean dedicated development checkout, preserving original x1. The new work was NOT pushed. The locally created dev/botx3-team-economy-20261102 branch did not yet contain the new code; use the archive.

Your main objective is to develop the map-independent coordinated economic planner described in DEVELOPMENT_BRIEF.md. Continue actual implementation and experiments, not just documentation or another plan. Do not submit, publish, activate or upload any bot to the official ladder. Local builds, tests and dedicated local commits are allowed.

The latest source is X3_TEAM=12, an UNVALIDATED native execution-contract repair. The last driver, team_contract.py, was interrupted during compilation before any completed match matrix. Modes up to 11 have frozen results. Read the exact failure history before retrying: independent auctions had fuel and coordination issues; early protocols displaced sightings/events; mode 11 fixed command intent and opening initialization, but farming still lost versus its same-code control. Mode 12 checks coordinator proposals with the existing executor's economic/safety model before accepting them. Validate this path and its activation first, then resume its controlled comparisons.

Never reject a strategy based solely on its first negative benchmark. Verify build/configuration, inputs and activation, inspect dependencies and replays, make approximately 2–3 justified focused repairs, test plausible combinations and conditional environments. Use Accepted / Retry required / Conditionally useful / Parked / Rejected accurately. No arbitrary rescue grids.

Original x1 hash: 1746f2bb7fa341530f41bd8c8c4896b35172783f35eacee8e4a4b6ac0ceea183. x1c1 parent: 22e6067a423356e29e6738438f47b22d05b554767757717e58bf350392e16b13. Preserve both. K004–K009 are completed; K010 is completed and snapshotted. Read newer relevant research where available. v92 source verification is bundled.

Do not mistake development gains for generalization: mode 8 scored 114/224 versus x1 100/224, but had 182 versus 150 fuel-outs and lost 16/48 versus x1 24/48 on genuinely new resource layouts. All prior held-out maps are now spent diagnostic data; freeze a fresh independent family/layout set before any new final validation. No new strategy has been accepted or submitted.

Use the saved frozen sources, binaries, result matrices and selected native replays. Restore the actual toolchain (cambc 4.0.0 / engine 2.0.0 / SDK 4.0.0 / WASI SDK 33), adapt Windows-specific asset paths, and verify provenance. Do not rerun reproducible reference cells without reason. Keep a concise log, prioritize code and evidence, and continue toward a reliably stronger economic planner.
'''
(DEST/'FRESH_AGENT_PROMPT.md').write_text(prompt,encoding='utf-8')
# Small source/result overlay, omitting bulky compiler caches and raw full campaigns.
files={}
def add(path,arc=None):
    path=Path(path)
    if path.is_file():files[arc or path.relative_to(ROOT).as_posix()]=path
for bot in ['botx3','v92']:
    for p in (ROOT/'bots'/bot/'src').rglob('*'):add(p)
    add(ROOT/'bots'/bot/'README.md')
add(ROOT/'tools/dz.py')
for p in BASE.glob('*'):
    if p.suffix in ['.py','.mjs','.cpp','.md','.json','.zip']:add(p)
for name in suites+['team-contract']:
    folder=BASE/name
    for fn in ['rows.json','summary.json','manifest.json','same-code-proof.json','final-source-verification.json']:add(folder/fn)
    for p in (folder/'diagnostics').rglob('*.json'):add(p)
for folder in ['team-maps','team-unseen-maps']:
    for p in (BASE/folder).rglob('*'):
        if p.suffix in ['.json','.map26a']:add(p)
frozen=[('builds','off'),('builds','parent'),('team-transfer/builds','team_guarded'),('team-tail/builds','team_after_fields')]
frozen += [(f'team-intents/builds',a) for a in ['transport','farm','bank','joint']]
frozen += [(f'team-contract/builds',a) for a in ['transport','farm']]
for sub,label in frozen:
    folder=BASE/sub/label
    for p in (folder/'src').rglob('*'):add(p)
    for fn in ['bot.wasm','identity.json','bot.build.log']:add(folder/fn)
for p in (BASE/'team-work/replay-audit').glob('*'):add(p)
for p in (BASE/'team-bank/audit').glob('*'):add(p)
for fn in ['FAILURE_PROTOCOL.md','RETRY_QUEUE.md']:add(ROOT/'research/x1'/fn)
add(ROOT.parent/'AGENTS.md','AGENTS.md')
brief=Path('C:/Users/omdha/.codex/attachments/2c838acd-4182-4d33-becf-8f856d12d8bc/Pasted text.txt')
add(brief,'DEVELOPMENT_BRIEF.md')
for fn in ['HANDOFF.md','FRESH_AGENT_PROMPT.md']:add(DEST/fn,fn)
manifest={name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for name,p in sorted(files.items())}
(DEST/'MANIFEST.json').write_text(json.dumps(dict(state='Stopped at user request; X3_TEAM=12 unvalidated',files=manifest),indent=2)+'\n')
archive=DEST/'BOTX3_CONTINUATION.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name,p in sorted(files.items()):z.write(p,name)
    z.write(DEST/'MANIFEST.json','MANIFEST.json')
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
(DEST/'ARCHIVE_SHA256.txt').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
print(json.dumps(dict(folder=str(DEST),archive=str(archive),files=len(files),bytes=archive.stat().st_size),indent=2))
