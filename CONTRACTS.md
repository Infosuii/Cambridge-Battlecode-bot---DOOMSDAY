# Shared contracts (lead-owned; read before editing anything)

Workspace root: `C:\projects\cambridge battlecode\work\neural-full-stack` (below: `ROOT`).
This file is the single source of truth for interfaces and file ownership during the build. If a contract is wrong,
write the problem and your proposed change into `agents/<you>/CONTRACT_ISSUES.md`; do not silently diverge.

## Lead integration amendments (2026-10-24 checkpoint)

- Wave2 original gameplay hooks remain staged, not applied. `tools/stage_wave2.py` creates scratch integration copies.
  Current official byte verification is blocked by compiler execution policy; native tests are not a substitute.
- The lead integrated runtime/model/training fixes. D/E/F ownership still governs their modules. The explicit C
  audit follow-up and H2/F review assignments are recorded in AGENT_RECORD.md; no additional worker runs are implied.
- NFS1 kind0 prefixes RawTurn with u32 byte count. Decision v1 appends u32 action_hash, u16 call, i16 net, f32 logit[K].
  Canonical adapters are `nfs.records.decode_stdout` (numeric wire fields) and `nfs.obs.encode_bytes` plus OBS_DIM/hash.
- Head semantic hashing includes schema version, feature descriptions/scales, option semantics and output units for
  all kinds (including value/belief/leaf). Combined dataset/checkpoint action hashes include every per-head schema.
- Value margin unit is fixed submitted-gem difference /1000, independent of reward-shaping scale. Belief has9 sectors.
  Carry-risk, belief and leaf target/loss coverage remains incomplete and must not be described as training-ready.
- Shop option0 is the opaque guarded complete teacher executor; its per-item descriptors are unknown zero sentinels.
  The staged F patch removes the duplicate teacher preview rather than constructing it before admission.
- `nnh::leaf` consumes an admission token and meters from its start. `context_position` reports the cached snapshot
  anchor. First-admitted-call snapshot semantics persist through the turn; later candidate features use live state.
- NFS1 and NFT1 output runs after play_turn from leftover fuel. Credit/shadow builds do not claim exact neutrality.
  The recorded evaluation amendment preserves the strict teacher_exact requirement and adds neutral_real controls.
- `install_models --model <export-dir>` is accepted for development/training only, without mutating the registry.
  `teacher_record` and `training_objective` profiles now exist. Actual engine concurrency is capped4.

The original contracts below retain their design rationale; these explicit lead amendments resolve the listed
interface changes. No training, submission or release acceptance is authorized by them.

## 0. Hard rules (all agents)

- NO training: never run anything that updates model parameters on match data, no long self-play, no fine-tuning.
  Synthetic shape/gradient/parity/round-trip tests are allowed; label synthetic data `synthetic` everywhere.
- NO submission/upload/activation (`cambc submit`, platform APIs). No login. No browser/desktop control.
- Never modify anything outside ROOT. Read-only inputs: `C:\projects\cambridge battlecode\work\neural-gameplay\**`
  (previous experiments, evidence), the historical archives, the CLI/SDK/maps. Never overwrite `references/**`.
- Only edit files you own (section 2). Integration changes to lead-owned files are delivered as patches/instructions
  in `agents/<you>/` and applied by the lead.
- Official engine only, at default fuel, `--release` for any gameplay evaluation. Never pass `--fuel`.
- Credentials never appear in source, logs, prompts, datasets or artifacts.
- Report honestly: untrained heads are untrained; synthetic tests are not match evidence; reused maps are reused.
- Tools/paths: `config/paths.json`. Python: `C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe`
  (torch 2.11+cu128, numpy 2.5; **no pytest** - use `unittest`; do not pip-install into that venv). Run Python with
  `PYTHONPATH=ROOT/python`. Native C++ tests: `C:/msys64/ucrt64/bin/g++.exe` (g++ 16.2, `-std=c++20`).
- Shared engine helpers: `python/nfs/engine.py` (official build, run_match, summary parsing, replay stdout reader,
  wasm section hashing). Use them; propose changes to the lead instead of forking them.

## 1. Verified facts (lead, 2026-10-23; agents re-verify what they depend on)

- `cambc 3.0.5`; match summaries report `engineVersion 1.0.3`. WASI clang 22.1.0. Workspace has `cambc.toml`,
  `cmake/CMakeLists.txt` and `sdk/cpp` copied from the official arena so `cambc build` works here.
- Official build = CMake `file(GLOB_RECURSE "${BOT_DIR}/src/*.cpp")`, `-O3 -DNDEBUG -std=c++20 -msimd128
  -mbulk-memory -mbulk-memory-opt -fwasm-exceptions`, include dir = SDK. **Keep all sources flat in `bot/src/`**
  (the old private helper only compiled top-level `src/*.cpp`; flat files compile identically under both).
- Official builds are byte-reproducible: the original rebuilt in two directories gave the same SHA-256
  (`references/builds/manifest.json`).
- Fuel: ~100,000 per turn (99,989 at turn start), first champion turn ~2x (182k), first draft turn 10x.
  The original typically ends turns with 20k-80k left and sometimes exhausts.
- Matches are deterministic for fixed (wasm A, wasm B, map): the engine seed is per map.
- `debug_block` (CAMBC_DEBUG builds, run without `--release`) pauses fuel, BUT a debug build of the unchanged original
  diverged from its release build on 2 of 4 maps (`evaluation/evidence/debug-build-fuel-probe.json`). A debug build
  must therefore not be assumed fuel-equivalent; any training-log path must be costed and its effect measured.
- Team shared memory is tiny (the original uses 8 bytes: claim slots + one sighting); draft memory freezes after the
  draft. Read `bc::constants::shared_memory_bytes` / `draft_memory_bytes`; do not assume more.
- The original's `A2_LAB=1` is NOT inert: `A2_KNOBS` (baked-in tuned values) flow through `lab::knobs` into gameplay.
  Lab *host controls/logging* (exports, `lab::ctl` interventions, `cn_log`, `pol_log`, `macro_feat`, `cn_force`,
  `builds`) are separable from the knobs. Stripping anything changes fuel and must be tested against the original.

## 2. File ownership

| Owner | Files |
|---|---|
| Lead | all original sources in `bot/src/` (bot.cpp, bot.h, common.h, main.cpp, draft.cpp, tsearch.*, world.*, ...), `bot/src/nn_config.h` (generated, profile switch), `bot/src/nn_access.h`, `schemas/heads.json`, `CONTRACTS.md`, top-level docs, `python/nfs/engine.py`, `config/` |
| A (audit/teacher) | `bot/src/nn_teacher.h`, `bot/src/nn_teacher.cpp`, `agents/A/**`, `tests/fixtures/teacher/**`, `tools/audit_*.py` |
| B (runtime/export) | `bot/src/nn_rt.h`, `bot/src/nn_model.h`, `bot/src/nn_budget.h`, `bot/src/nn_registry.h` (generated), `bot/src/nn_weights_*.h` (generated), `bot/src/nn_head.h`, `bot/src/nn_head.cpp`, `bot/src/nn_log.h`, `python/nfs/models/**`, `python/nfs/export.py`, `python/nfs/registry.py`, `tools/install_models.py`, `tools/gen_config.py`, `models/**`, `tests/cpp/rt_*`, `tests/python/test_rt_*.py`, `agents/B/**` |
| C (observations) | `schemas/observation.json`, `tools/gen_schema.py`, `bot/src/nn_schema.h` (generated), `bot/src/nn_obs.h`, `bot/src/nn_obs.cpp`, `bot/src/nn_obs_glue.cpp`, `python/nfs/obs.py`, `python/nfs/schema_gen.py` (generated), `python/nfs/transforms.py`, `tests/cpp/obs_*`, `tests/python/test_obs_*.py`, `agents/C/**` |
| D (strategy) | `bot/src/nn_strategy.h`, `bot/src/nn_strategy.cpp`, `schemas/heads/{draft_pick,strategy,objective,role,value}.json`, `python/nfs/heads/strategy.py`, `tests/**/test_strategy_*`, `agents/D/**` |
| E (tactics) | `bot/src/nn_tactics.h`, `bot/src/nn_tactics.cpp`, `schemas/heads/{move,combat,engage,ward,ts_leaf}.json`, `python/nfs/heads/tactics.py`, `tests/**/test_tactics_*`, `agents/E/**` |
| F (economy) | `bot/src/nn_economy.h`, `bot/src/nn_economy.cpp`, `schemas/heads/{bank,shop}.json`, `python/nfs/heads/economy.py`, `tests/**/test_economy_*`, `agents/F/**` |
| G (data/training) | `python/nfs/data/**`, `python/nfs/train/**`, `python/nfs/cli.py`, `tools/nfs.py`, `data/manifests/**`, `configs/train/**`, `tests/python/test_data_*.py`, `tests/python/test_train_*.py`, `agents/G/**` |
| H (evaluation) | `evaluation/**` (protocol, schedules, results), `python/nfs/evaluate/**`, `tools/eval_*.py`, `tools/verify_release.py`, `tools/package_release.py`, `tests/python/test_eval_*.py`, `agents/H/**` |

## 3. Runtime architecture contract (C++)

All new C++ lives in flat `bot/src/nn_*.{h,cpp}`. Rules:
1. No dynamic initialisation in nn translation units (no global objects with constructors, no `std::vector` globals):
   `constexpr`/`constinit` data and plain static arrays only. Unreferenced nn code must be removable by the linker.
2. No heap allocation per decision; bounded static buffers sized by `schemas/heads.json` (`max_candidates`=16,
   `max_candidate_features`=24) and `schemas/observation.json`.
3. Pure kernels and encoders (`nn_rt.h`, `nn_obs.h/.cpp` encode part, `nn_head.h` math) must not include `cambc.h`, so
   they compile natively with g++ for parity tests. SDK access lives in `*_glue.cpp`/hook files only.
4. Hooks in lead-owned code are compile-time gated:
   `if constexpr (nncfg::mode(nncfg::H::objective) != nncfg::Mode::off) { ... }`.
   With every head `off`, the original translation units must generate **identical code** (target: identical Wasm code
   section to the original, or a measured, explained difference).
5. Teacher fuel queries: every original `bc::fuel_remaining()` used for a decision is routed through
   `nnb::teacher_left()` (inline; identical to `bc::fuel_remaining()` unless `nncfg::kFuelCredit`).

### 3.1 `nn_config.h` (generated by `tools/gen_config.py --profile <name>`, owned by B, run by lead)
```cpp
namespace nncfg {
enum class Mode : int { off = 0, shadow = 1, active = 2 };
enum class H : int { draft_pick, strategy, objective, role, bank, shop, move, combat, engage, ward, belief, value, ts_leaf, count };
inline constexpr Mode kMode[int(H::count)] = { ... };
constexpr Mode mode(H h) { return kMode[int(h)]; }
inline constexpr bool kAnyHead;      // any head != off
inline constexpr bool kTraining;     // behaviour sampling + NFS records to stdout
inline constexpr bool kTelemetry;    // per-head fuel/fallback summary lines to stdout (dev only)
inline constexpr bool kFuelCredit;   // neutral-proof only: teacher fuel queries see neural spend credited back
inline constexpr bool kSelfTest;     // run inference fixtures on the first turn and print them
inline constexpr bool kStripLab;     // remove inherited lab host controls/logs (knobs kept)
inline constexpr unsigned kSeed;
inline constexpr const char* kProfile;
}
```
Profiles (`configs/profiles/*.json`, owned by B): `release` (default checked-in; all heads off unless a model is
installed with status `validated` and the manifest selects it), `teacher_exact` (all off, lab as original),
`neutral_credit` (all heads shadow, zero residual, kFuelCredit), `neutral_real` (shadow, no credit),
`dev_untrained` (all heads active with seeded untrained weights - plumbing only, never a playable release),
`training` (active, sampling + logging), `selftest`.

Mode semantics: `off` = compiled out. `shadow` = run head, record, **always execute the teacher choice**.
`active` = execute the head's choice (argmax in deployment, sampled when kTraining).

### 3.2 Decisions (`nn_head.h`, B)
Every learned decision is a masked candidate choice or a bounded value:
```cpp
namespace nnh {
inline constexpr int kMaxK = 16, kMaxF = 24;
struct Decision {
  nncfg::H head; int K = 0; int F = 0;   // F = this head's candidate feature width (from its schema)
  float feat[kMaxK * kMaxF];            // row-major K x F, already normalised/clipped by the candidate builder
  std::uint8_t legal[kMaxK];            // deterministic legality mask (1 legal)
  float prior[kMaxK];                   // teacher prior logit per candidate (see below)
  std::uint32_t id[kMaxK];              // stable identifiers (group index, tile code, handle, enum)
  std::uint8_t context = 0;             // call-site context code (e.g. move: travel/combat/retreat/position)
};
struct Result { int choice; bool neural; float logp; std::uint8_t reason; }; // reason: see nn_head.h enum
Result decide(const Bot& bot, Decision& d);   // budget gate, shared context, scorer, mode, fallback, logging
float value(const Bot& bot, nncfg::H head, int output); // value-kind heads (belief/value/ts_leaf); NaN-safe, 0 on fallback
}
```
`nn_config.h` also defines preprocessor macros for code that must vanish at preprocessing level (exports, includes):
`#define NN_ANY_HEAD 0|1`, `#define NN_STRIP_LAB 0|1`, `#define NN_TRAINING 0|1`, `#define NN_TELEMETRY 0|1`.
Bot access: `bot.h` declares `friend struct nn_teacher_access; nn_obs_access; nn_strategy_access; nn_tactics_access;
nn_economy_access;` (already applied; verified to produce a byte-identical Wasm). Each owner defines its own struct in
its own `.cpp` with static functions taking `const Bot&` / `Bot&`.
Conventions (all heads): candidate 0 is ALWAYS the teacher's choice and is always legal. Ties break to the lowest
index, so ties go to the teacher. Logit_k = prior_k + R * tanh(r_k / R) for legal k, -inf otherwise; r_k = residual
MLP over [shared context h, candidate features]. prior_0 >= prior_k (teacher margin). With a zero residual the choice is
exactly the teacher's. Empty/invalid sets (K==0, candidate 0 illegal, NaN/Inf anywhere, schema/model mismatch, budget
refusal, encoder skipped) return choice 0 with `neural=false` and a reason code. Hooks must keep the teacher choice
computed and valid before calling `decide`, so fallback is free.

### 3.3 Shared context (B math, C features)
`nnobs::RawTurn` (POD, C) is filled once per turn by glue, lazily on the first head call that is admitted, then encoded
(pure function) and run through the shared encoder to `h[kCtx]` (default 32). Cached per (champion, round); invalidated
at turn start. Heads with `uses_shared_context` read it. If the encoder is not admitted, all context heads fall back
for this turn.
C-provided interface (B codes against it; until C lands, B tests with a stub `nn_schema.h` of the same shape):
```cpp
// nn_schema.h (generated from schemas/observation.json)
namespace nnobs {
inline constexpr std::uint32_t kObsSchemaHash;
inline constexpr int kSelfGlobalDim;               // flat self + global block
inline constexpr int kAllyRows, kAllyDim;          // ally entity rows (padded) and width
inline constexpr int kEnemyRows, kEnemyDim;        // enemy entity rows (visible + remembered), width
inline constexpr int kObsDim = kSelfGlobalDim + kAllyRows*kAllyDim + kAllyRows + kEnemyRows*kEnemyDim + kEnemyRows;
} // layout: [self_global | ally rows | ally mask(0/1) | enemy rows | enemy mask(0/1)]
// nn_obs.h (pure)                       // nn_obs_glue.cpp (SDK)
struct RawTurn;                           bool capture(const Bot& bot, RawTurn& out);  // false = unavailable
void encode(const RawTurn& raw, float* x /* kObsDim */);
```
Padded entity rows must be all-zero with mask 0; encoders must be padding- and row-permutation-invariant
(masked mean + max pooling).

### 3.4 Budget (`nn_budget.h`, B)
`nnb::begin_turn()` at the top of `play_turn`; `nnb::admit(head, worst_case_fuel)` gates BEFORE any feature work;
`nnb::Meter` scopes record actual spend (telemetry only); defaults: per-turn neural allowance and tail reserve are
measured by B and recorded in `models/budget.json`; admission requires `fuel_remaining >= worst_case + tail_reserve +
teacher_reserve(head)`. Fallback cost after a refusal must be O(1).

### 3.5 Training records (stdout, only when kTraining; B writes, G parses)
One line per record: `NFS1 <base64>`; little-endian payload:
`u32 magic=0x3153464E, u16 version=1, u16 kind (0 turn-context, 1 decision, 2 episode-marker), u32 schema_hash,
i32 round, u32 champion_handle, ...kind-specific...`. Decision: `u16 head, u16 K, u16 F, i16 teacher(=0), i16 chosen,
u8 mode, u8 reason, u8 context, u8 sampled, f32 logp_behaviour, f32 prior[K], u8 legal[K], u32 id[K], f32 feat[K*F]`.
Turn-context: raw `RawTurn` bytes (schema-hashed). B documents the exact layout in `agents/B/RECORD_FORMAT.md` and
provides a Python decoder in `python/nfs/records.py` (B-owned). Bounded count per turn; the logging cost is measured.

## 4. Python contract
Package `python/nfs`: `engine.py` (lead), `models/` (B: SharedEncoder, CandidateHead, ValueHead, configs from
`schemas`), `export.py` + `registry.py` (B), `records.py` (B), `obs.py`/`transforms.py` (C), `heads/*.py` (D/E/F:
head-specific candidate feature specs and teacher-label helpers), `data/` + `train/` + `cli.py` (G), `evaluate/` (H).
Tests: `tests/python/test_*.py` (unittest), `tests/cpp/*.cpp` + `tools/run_cpp_tests.py` (B creates the runner).

Model API (B implements in `python/nfs/models/__init__.py`; G/D/E/F use only this):
```python
class PolicyNet(torch.nn.Module):            # shared encoder + every head; dims from configs/model/<name>.json
    def __init__(self, cfg: dict): ...
    def encode(self, obs):                    # [B, kObsDim] float32 -> h [B, ctx]
    def head_logits(self, head: str, h, feat, legal, prior):   # feat [B,K,F], legal [B,K] bool, prior [B,K] -> [B,K], illegal = -inf
    def values(self, h) -> dict:              # {'win_logit','margin','carry_risk'}: [B] each
    def belief(self, h):                      # [B, n_sectors] logits
def build_model(cfg: dict) -> PolicyNet
def activation(x)                             # the exact activation approximation used in C++ (parity)
```
`schemas/heads/<name>.json` (head owners): `{name, id, F, K_max, features:[{name, scale, clip, description}],
contexts:[...], residual_bound R, teacher_margin, label_sources:[...]}`.

## 5. Model lifecycle and manifests
`models/registry.json` lists installed models; each has `models/<name>/manifest.json`:
`name, head, arch_version, architecture{...dims}, obs_schema_hash, action_schema_hash, n_params, checksum
(fnv1a64 over little-endian float32 params), export_precision ("f32"), engine_version "1.0.3", provenance{...},
status in {untrained, teacher_initialized, trained, validated}, validation{...}`. `draft_net_original` is registered as
the inherited original draft network (status `trained`, provenance "inherited from original source", used by the
teacher). `tools/install_models.py` regenerates `nn_registry.h`/`nn_weights_*.h`/`nn_config.h` from the registry and a
profile; in `release`, only `validated` models may be active. That command is the single switch for installing models.
