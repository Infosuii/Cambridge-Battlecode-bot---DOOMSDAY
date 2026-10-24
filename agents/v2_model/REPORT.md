# V2 direct policy model and exporter

Worker: `economy`, assigned v2_model ownership by the lead. Model/runtime: inherited configured Codex model. The
agent tool does not expose this worker's exact model identifier and offers no Opus 5.5 choice; no Opus execution is
claimed. No training, games, parameter selection, submission, upload, browser or desktop actions were performed.

## Delivered and verified

- `bot/src/nn_policy_model.h`: pure SDK-free `nnpm::PolicyDesc` wrapper, direct raw scoring, structural version/schema
  validation, exact canonical offsets, full finite/checksum verification and a checked forward function. Numeric
  kernel architecture remains **1**, reused without modification; policy interpretation is **2**. These are
  separate fields, not a silent reinterpretation of v1 residual artifacts.
- `python/nfs/policy/{__init__,model,export}.py`: `DirectPolicyNet` is a fully implemented torch module reusing the
  existing shared encoder and raw candidate MLP operations. Its `head_logits` accepts **no prior**. No output
  bound around the teacher is applied. New exporters/loaders reject v1 or unversioned models even when dimensions
  match. Parameters use the unchanged canonical f32 numeric-kernel layout, with only eight active heads and none
  in the other five C++ descriptor slots.
- `configs/model/policy_v2.json`: initial G8/E4/ctx8 encoder, hidden8 per head, F12 and four contexts on every
  gameplay head. It now requires the compact own `nn_policy_observation.h` schema (S40, ally5x10, enemy6x12,
  D173); it never falls back to the legacy RawTurn/563-input schema. Active legacy IDs are strategy1, objective2,
  role3, bank4, shop5, move6, combat7 and engage8.
- Automatic candidate schema resolution independently recomputes each head and combined FNV1a32 semantic hash from
  `schemas/policy_v2.json` and rejects stale stored hashes. Explicit hashes remain available for labelled synthetic
  fixtures and later versioned schema construction. Observation dimensions/hash come from the dedicated compact
  `nn_policy_observation.h`; there is no provisional or legacy observation fallback.
- `tests/cpp/test_policy_model.cpp`, `tests/python/test_policy_model.py`: **10/10 tests PASS**, including 24 native
  descriptor/failure checks; 128 varied forward cells across all eight heads, all four contexts and K1/3/8/16;
  C++/Torch output tolerance <2e-6 with argmax agreement on every tested cell; export/import exact parameter round
  trip; deterministic artifact bytes; NaN/Inf, checksum, segment and header corruption; v1 rejection; schema
  validation; padding invariance; masks; canonical ties and candidate permutations.
- An explicit test sets direct bank logits to37, proving the old teacher-centred residual bound is absent. A
  distinct seeded zero-logit control has all legal logits zero and chooses the lowest legal canonical ID. It is
  **not** a teacher-neutral control and is never described as one.
- `agents/v2_model/build_untrained.py`: reproducible synthetic artifact generator with workspace/references bounds.
  It creates untrained weights only, with training_games=0 and parameter_updates=0 provenance. No installation,
  registry mutation or release activation occurs.

## Frozen integration API

```
namespace nnpm {
struct PolicyDesc { uint32_t interpretation_version; const nnm::ModelDesc* kernel; };
constexpr bool desc_ok(const PolicyDesc&, uint32_t expected_obs=0,
                      uint32_t expected_action=0, const uint32_t* expected_head_hashes=nullptr);
bool verify(const PolicyDesc&); // full finite+whole/segment checksum, call once at warmup/install
bool logits(const PolicyDesc&, int head, int context, const float* h,
            const float* feat, int K, const uint8_t* legal, float* out);
void direct_logits(const PolicyDesc&, int head, int context, const float* h,
                   const float* feat, int K, const uint8_t* legal, float* out);
}
```

`desc_ok` validates metadata/offsets, not float contents. `verify` validates the blob. A fuel-bounded runtime may use
the existing `nnm::verify_step` segment machinery after `desc_ok`, rather than running full verification per turn.
`direct_logits` is the fast already-validated kernel; `logits` additionally checks sizes/context/masks/finite input
and output. It returns false for invalid/empty/all-illegal sets. The caller must explicitly select whole-bot fallback;
index0 is never implicitly the teacher. Illegal output rows are negative infinity. Valid model inputs need the
caller to validate its observation and encoder output as well.

Python:

```
from nfs.policy.model import load_config, DirectPolicyNet, build_model, init_untrained
from nfs.policy.export import export_model, load_model, load_blob

cfg = load_config('policy_v2')  # current versioned candidate schema + compact own observation header
model = init_untrained(DirectPolicyNet(cfg), seed=20261024, zero_logits=False)
h = model.encode(obs)                            # [B,D] -> [B,8]
z = model.head_logits('move', h, feat, legal, context=None)  # [B,K,12] -> [B,K], no teacher prior
manifest = export_model(model, name, out_dir, status='untrained', provenance={'synthetic': True})
```

The generated `nn_policy_weights_<name>.h` uses namespace `nnpw_<name>`, exposes `kBlob`, `kKernel` (`nnm::ModelDesc`)
and `kDesc` (`nnpm::PolicyDesc`). The manifest explicitly lists interpretation_version2, direct policy kind,
kernel_arch_version1, engine1.0.3, f32 precision, observation/combined/per-head hashes, dimensions, offsets by config,
whole and segment checksums, lifecycle status and provenance. Loaders can require expected current schema hashes
and reconstruct/check the exact generated header. Export does not register or install anything.

## Actual commands

With PYTHONPATH=ROOT/python, native g++ on PATH, and TMP/TEMP inside ROOT/artifacts/tmp:

```
python -m unittest tests.python.test_policy_model -v
```

Result: 10 tests, OK. All data and exported fixtures are labelled synthetic and stay in
`artifacts/tmp/v2_model`. No match data is used; no parameter updates occur.

After the compact own observation header landed, the same tests were rerun successfully against D173 and schema
hash `0x831AC800`. `build_untrained.py --out artifacts/tmp/v2_model/actual_schema --name policy_v2_untrained` then
generated **2296 f32 parameters**, checksum `0xc446256bb95743bd`, with the actual compact observation and direct
candidate schema identities. This replaces the earlier scratch artifact that used legacy observation dimensions;
it is still synthetic and untrained. `artifacts/tmp/v2_model/model.exe checks` reports **24 checks, 0 failures**.

## Limits / remaining lead checks

Official Wasm build, model installation into development profiles, whole-bot all-off byte identity, real observation
and record parity, full feature/observation/logging/inference fuel, and engine smoke are not proved by native model
tests. They remain lead integration checks. Initial capacity is a small engineering starting point, not a measured
fuel guarantee or evidence of strength. No release/default configuration was edited; direct heads stay off.

The v2 model has no learned draft/value/belief/leaf head. Inherited drafting remains separate; the first direct
milestone deliberately defers the auxiliary heads per POLICY_FIRST_PLAN.md. Training losses and NFS2 records are
owned by the records worker, and legality/canonical candidate construction by the candidate worker.
