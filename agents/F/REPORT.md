# Agent F: economy and banking, Wave 2

Runtime: spawned Codex worker `economy` in the resumed session. It inherited the session model. The tools did not
expose an exact model identifier or offer Opus 5.5; this report does not claim an Opus run. No training, games,
submission, upload, browser or desktop use occurred in this worker.

Delivered:

- `bot/src/nn_economy.{h,cpp}`: pure POD candidate builders, bounded static runtime buffers, and SDK glue calling
  `nnh::admit` before state/features/SDK alternative queries, then `nnh::decide`. Both heads run at most once per
  champion/round; repeat opportunities execute their newly computed teacher choice. New code is preprocessed out
  when all heads are off.
- `schemas/heads/{bank,shop}.json`: versioned F=20 schemas, IDs, clipping, labels, legality and option semantics.
- `python/nfs/heads/economy.py`: float32 feature/candidate twin and teacher-label validation.
- `tests/cpp/test_economy_parity.cpp`, `tests/python/test_economy_parity.py`: 400 varied synthetic candidate fixtures
  compared bit-exactly, plus hard bank priorities, existing route alternatives, masks, bounded K, de-duplication,
  teacher plan semantics and schema checks.
- `agents/F/HOOKS.diff` and `make_hook_patch.py`: exact proposed integration replaces the entire Wave1 shop-preview
  capture pre-pass with the admitted shop hook, and adds the bank hook at its capture. The script only creates the
  patch. The lead applies the patch to original gameplay files.

## Meaningful decisions and deterministic boundaries

Bank candidate zero is the already-computed `go` and route. Other candidates continue farming, bank along the
already-built safe route, or bank along the already-built static nearest-altar route. Force, winning-bag and
deadline-critical bank priorities cannot be vetoed. The raw route is offered only when its existing field proves
reachability; no new fields, per-altar sorting or exhaustive route enumeration are added. Destination selection is
between safe-nearest and static-nearest altar routes, which can reach different altars. It is not arbitrary
individual-altar selection. The original deterministic walk, stale/stuck guards, enemy-lock attacks and submit API
executor remain responsible for legal action execution.

Shop candidate zero executes the **complete original plan**, including its lock purchase and potentially several
shard purchases. It is an **opaque guarded executor**: item, count, cost, owned and projected-gold-after descriptors
are zero sentinels, with the teacher-plan flag identifying this option. No first-purchase preview is reconstructed.
The Wave1 duplicate pre-pass is removed by the proposed patch; it had repeated SDK queries and called `build_for`,
which allocates a vector, before admission. The original guarded purchase executor remains unchanged. This is a
single guarded option, not a label pretending that the teacher buys only one shard or that its plan is free.
Alternative actions save or attempt one affordable SDK-legal shard/consumable purchase. Fixed deterministic narrowing
includes 12 shard variants across all seven families plus teleport crystal and altar lock, for K<=16 including
teacher/save. `can_buy` is rechecked immediately before execution. If the check changes or the purchase throws,
the selected guarded-purchase option saves for this opportunity; it does not send an illegal action. The policy
semantics are explicitly guarded purchase options. There is no multi-turn forced commitment to merge.

SDK verified facts: `sdk/cpp/cambc.h` item_type (starting line 1477) documents shard/emblem families and shard costs;
consumable_type (starting line 1764) has only `tp_crystal` and `altar_lock`. Wards are champion placement abilities,
not purchasable consumables. Runtime alternative prices come from metadata. `can_buy` (lines 3670 and 3684) enforces
shop availability, cost and consumable carry limits. Both `buy` overloads are preserved behind their exact guards.
Observations use current self inventory/gold/health/bag, public scores and already computed visible-threat flags;
no hidden or future fields are read.

## Commands and results

With `PYTHONPATH=ROOT/python`, the native toolchain on PATH and TMP/TEMP inside `ROOT/artifacts/tmp`:

```
python -m unittest tests.python.test_economy_parity -v
```

Result after removing the preview: **5/5 tests pass**, including 400 synthetic bit-exact C++/Python cases and an
explicit opacity regression proving arbitrary preview data cannot affect candidate0's features. No parameters are
updated.

```
python agents/F/make_hook_patch.py
git apply --check agents/F/HOOKS.diff
```

Both pass. Original gameplay files were not edited by this worker.

The actual SDK glue body also passed native `g++ -std=c++20 -fsyntax-only -I sdk/cpp` in
`artifacts/tmp/F2/sdk-syntax`, using a source copy with NN_ANY_HEAD=1. That validates its SDK names/types, not Wasm
code generation or engine execution. The official WASI compiler currently fails with execution permission denied
in the lead's environment. **Wasm identity, active official build, actual fuel and engine smoke remain lead checks.**

## Integration notes and limits

- Apply `HOOKS.diff`, regenerate models (new F20 schemas), then officially rebuild teacher_exact and compare full
  Wasm bytes before running enabled profiles. No all-off byte-identity claim is made from native syntax checking.
- Admission feature allowances bank=1800 and shop=6500 are conservative provisional constants in the module header,
  not measured fuel claims. Replace/raise them using the lead's engine probe; measure full SDK legality queries.
- Shop/bank do not invalidate the shared encoder cache themselves. The lead must keep its documented snapshot
  semantics or add action-effect invalidation for later heads after a purchase/move.
- Logs encode candidate0 as teacher option, not its internal buy list. Low-level individual-purchase imitation
  would need a finer logging schema; current future training optimizes options with the declared semantics.
- These heads are untrained and must stay off in the release profile.

## Follow-up fix from independent tactical review

The lead requested the opaque-plan change described above after independent E review found the duplicate shop
capture pre-pass. `shop.json` is now version 2 because candidate0's feature semantics changed. Its width remains
F20. The C++ builder ignores the retained compatibility-preview argument, as does the Python twin. The runtime
does not read `nn_teacher_access::shop` or call `build_for`; its metadata and legality queries for alternatives
occur after `nnh::admit`. This follow-up edits only F's module/schema/twin/tests/docs and proposed hook patch;
original gameplay files remain lead-owned and untouched by this worker. Bank behavior is unchanged.
