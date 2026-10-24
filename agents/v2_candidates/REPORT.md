# Direct v2 candidate worker report

Actual worker: previously assigned strategy (D), reused for direct-policy v2 candidate ownership.
Inherited configured Codex runtime; exact model identifier is not exposed to this worker. No
Opus5.5 run is claimed. This is a new task on the same real worker, not an invented specialist run.

Implemented:

- `nn_policy_candidates.{h,cpp}`: SDK-independent Candidate/Decision types, checked normalization,
  ascending stable-ID ordering, strict errors, separate optional teacher annotation and checked
  movement/combat composite-ID helpers. All eight gameplay heads, F12/K16/context4.
- `schemas/policy_v2.json`: interpretation/schema2; explicit96 feature semantics and raw units,
  eight option/ID definitions, legal independent narrowing/diversity contracts and semantic hashes.
- `python/nfs/policy/candidates.py`: float32 builder twin, canonical order/masks, exceptions/status
  API, label lookup, checked composite IDs and independently recomputed semantic hashes.
- Generator and [INTERFACE.md](INTERFACE.md) give exact root/model/log integration contracts.

Verification actually run (synthetic only):

```powershell
$env:PYTHONPATH="$PWD/python"
$env:PATH="C:/msys64/ucrt64/bin;"+$env:PATH
$env:TEMP="$PWD/artifacts/tmp"; $env:TMP=$env:TEMP
& 'C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe' agents/v2_candidates/generate_schema.py
& 'C:/projects/cambridge battlecode/work/neural-gameplay/.venv/Scripts/python.exe' -m unittest tests.python.test_policy_candidates_parity -v
```

**5/5 tests pass**, including1440 diverse candidate sets (180 per head) with bit-exact native/Python
features, IDs and masks, all contexts and candidate sizes1..16. Tests cover invalid heads/contexts,
empty/all-illegal/over-capacity, duplicate IDs, mask errors, NaN/Inf in legal and masked rows,
teacher absence/out-of-set/illegal labels, teacher annotation noninterference, candidate permutation,
stable tie behavior with illegal index0, C++/Python semantic constants, semantic-change hash sensitivity,
and composite-ID injectivity/overflow. Tests compile and run a native binary under artifacts/tmp;
that does not establish Wasm fuel or engine legality. No match data was used as synthetic evidence.

The generator's full-semantic hashing includes interpretation2, feature descriptions/scales/clips,
candidate IDs/options and narrowing rules. There is no teacher score/prior/is_teacher feature, no
forced legal index0 and no constructor/global dynamic initialization in new C++.

Remaining integration work belongs to the lead: generate legal World candidates according to the
schema's independent narrowing contracts, gate complete cost before feature work, map chosen stable
IDs back to exact execution, handle failures explicitly, collect optional labels separately, rebuild
teacher_exact and test byte identity after C++ changes, then official-engine budgets/records/smokes.
This worker did not run new official builds/games and makes no control-coverage or strength claim.

No training, submission, upload, browser/desktop use, changes to references, shared legacy model/runtime
edits or commits occurred. All scratch writes are under artifacts/tmp/v2_candidates.

## Compact-observation test follow-up

The same worker was separately assigned tests only for the root-owned compact observation. Added
`tests/cpp/test_policy_observation.cpp` and `tests/python/test_policy_observation.py`; did not edit
the observation generator, header, schema or Python implementation. Scratch remains inside
`artifacts/tmp/v2_observation`.

Ran `python -m unittest tests.python.test_policy_observation -v` with the workspace Python/PATH and
TMP/TEMP settings above. **6/6 synthetic tests pass** after root fixes described below:

- 1013 native/Python cases:1000 valid varied/masked/clipped/signed-zero/extreme finite cases and13
  invalid live NaN/Inf/mask cases; accepted observations match all173 float32 values bit-exactly.
- Masked raw rows containing NaN/Inf are excluded and encode as zero, including their masks.
- Normalized payload roundtrip; rejection of incorrect length, invalid masks, nonzero masked
  padding, nonfinite values and values outside[-4,4].
- Fixed raw shapes: self40, ally5x10/mask5, enemy6x12/mask6. Too few/many rows, columns and masks,
  and flattened/extra dimensions are rejected.
- Independent semantic hash recomputation, native dimensions/hash agreement, and altered stored
  schema hash rejected on module import. Schema hash is recomputed from current semantics rather
  than hardcoded in the tests; obs dimension173.
- Generator copied into an isolated workspace subtree, run twice, then compared byte-for-byte
  against checked-in schema/header. Both repeated outputs are identical and match current files.

Review found Python initially accepted some incorrect raw shapes and trusted a changed stored
schema hash. Regression tests exposed these gaps; the lead fixed strict shapes and import hash
validation in root-owned `observation.py`, then this worker reran the suite successfully. Raw C++
encode failure can leave a partially filled output; callers must discard it when encode returns
false. No SDK capture or real match fixture was created, and these tests make no visibility or
fuel claim about the eventual engine capture path.

The lead subsequently froze compact row ordering and capture semantics in the schema, changing
its identity to0x1346E3BA without changing dimensions. The same six tests were rerun against the
new header/schema/generator and pass; isolated regeneration still matches byte-for-byte.
