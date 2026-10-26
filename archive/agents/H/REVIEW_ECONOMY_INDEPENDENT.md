# Independent economy review

Reviewer: E/tactics worker, configured Codex runtime; E did not author F's economy implementation. Reviewed current
F modules, schemas/Python twin, staged `archive/agents/F/HOOKS.diff`, original call sites, SDK and tests. No implementation
edits, games, training or submission. Exact inherited model identifier was not exposed.

Overall: **FAIL for one admission-order issue; official integration verification PENDING.** The candidate/executor
contracts otherwise pass source review and synthetic parity.

## Actionable finding

**FAIL — P1: shop preview executes before admission, including on refused/repeated calls.**

`bot/src/bot.cpp:539-563` performs a neural-only teacher preview before the staged economy hook: `can_buy` for an
altar lock, `item_count`, and a scan of `build_for(type)`. F's staged hook is inserted *after* this block. Actual
admission and the once-per-round stamp happen later in `bot/src/nn_economy.cpp:135-136`. Therefore both a low-fuel
refusal and a repeated opportunity still incur SDK queries and inventory/plan preprocessing. The `CreditScope` in
`nn_teacher.h:300-303` covers the final `cap_shop` POD copy, not the preceding preview queries and loop. This fails
the requirement to gate before neural feature work and makes refused-call overhead nonconstant in build length.

Fix before integrated acceptance: move preview construction under successful shop admission and reuse that admission
token for the decision; or remove this duplicated preview and represent candidate0 using a cheap complete-teacher-plan
feature row. Candidate0 already means running the full unchanged teacher executor, so preserving that option does
not require a speculative extra inventory/plan pass. Recheck teacher_exact byte identity after the original-source
change. Measure the resulting refused and admitted costs in the official engine.

## Checks

| Result | Check and evidence |
|---|---|
| PASS | Teacher0 semantics. `build_bank` at `nn_economy.cpp:55-70` stores the exact incoming teacher verdict/route first. `build_shop:73-93` retains the complete original plan as index0 and always legal. Priors0 versus-0.25 retain teacher on zero residual/ties. Schemas and Python twin declare the same option interpretation. |
| PASS | Bank hard priorities. `build_bank:62-66` omits continue when force, wins or late. Runtime original `tribute_if_needed` computes these flags, checks gems and route reachability before the hook (`bot.cpp:4068-4150`). The resulting contract assumes the teacher's invariant that force/wins/late imply `go=true`; actual source satisfies it. |
| PASS | Reachable route alternatives. Bank glue reads raw altar distance only after admission and rejects `kUnreach` (`nn_economy.cpp:103-107,123-132`). Safe field comes from the existing original bounded decision and is offered only after reachability. The staged patch updates `use_safe`/`dist` consumed by the original existing-field executor. No fabricated per-altar fields or extra pathfinding. |
| PASS | Deposit/route legality retained. Original stuck/off-window checks, enemy altar-lock handling, `submit_gems` and `follow_field` remain after the staged hook (`bot.cpp:4152-4215`). Learned choices select timing/route intent, never API legality. Arbitrary per-altar destination choice is intentionally outside this version. |
| PASS | Shop exact affordability and availability. Alternatives use SDK metadata costs, self `item_count`, and `can_buy` (`nn_economy.cpp:146-169`). SDK `cambc.h:3670-3693` checks shop permission, purchasability, gold, valid enum/count and consumable carry limit. Builder masks additionally enforce current cached gold. |
| PASS | Supported purchases. Fixed bounded set includes12 shards across all seven SDK families and the only two consumables, tp_crystal and altar_lock. No invented ward purchase, upgrade slot or inventory mechanic. K<=16 (`nn_economy.cpp:73-93,146-169`; SDK item types around `cambc.h:1477`, consumables around1764). |
| PASS | Guarded execution/logp contract. A nonteacher purchase is explicitly a guarded purchase option. Immediate `can_buy` failure or caught SDK failure saves at that opportunity and returns true, preventing silent teacher substitution (`nn_economy.cpp:181-195`). This matches the schema's option semantics. NFS1 labels the selected intent; it does **not** prove a purchase occurred. Future analysis must retain that distinction or add execution-outcome records. |
| PASS | Complete teacher executor preserved. Returning false on choice0 runs the original complete lock-plus-build purchase loop. Returning true on save/guarded alternative ends this opportunity. A partial failed alternative never resumes the teacher purchase plan. |
| PASS | Bounded static buffers and no namespace collision with tactics. F uses `nne::State/BankTerms/BankChoice/Buy`; E uses `nne::Option/Tile/CastPick`. Headers have no duplicate types/constants/functions. Candidate buffers are bounded and SDK `enum_map` inventory queries are fixed arrays. No per-decision heap or dynamic global initializer was found. |
| PASS | Synthetic C++/Python parity. Independent rerun of `python -m unittest tests.python.test_economy_parity -v`:4/4 pass, including400 varied bank/shop fixtures with bit-exact features/masks/IDs/priors, hard-priority and route cases, teacher-plan semantics, deduplication and K bound. TMP/TEMP set to workspace `artifacts/tmp`. |
| PASS | Staged patch applicability. Independent `git apply --check archive/agents/F/HOOKS.diff` exits0. It remains staged; this review did not apply it to original gameplay files. |
| PENDING | Official all-profile build and teacher_exact full-byte identity after integration. Native syntax and parity cannot establish this. Installed WASI compiler execution was blocked in the lead's environment. |
| PENDING | Feature bounds, candidate-generation/capture overhead, downstream search reserves and tail fuel. `kBankFeatureFuel=1800` and `kShopFeatureFuel=6500` in `nn_economy.h:7` are provisional; especially shop performs many SDK legality/gold queries. No engine measurement supports a worst-case bound yet. |
| PENDING | Real NFS1 action-intent/logit/logp roundtrip and engine invalid-action checks. Synthetic builder tests do not exercise the SDK glue, executor refusal branches, live inventory changes or real context capture. Both profiles/sides against original, v47 and first-hour remain required. |

## Commands actually run

```
PYTHONPATH=ROOT/python; TMP=TEMP=ROOT/artifacts/tmp; PATH=native compiler directory + PATH
python -m unittest tests.python.test_economy_parity -v
git apply --check archive/agents/F/HOOKS.diff
```

Output:4 tests OK; patch check exit0. These are synthetic/source checks only. No strength or readiness-to-train
claim is supported until the failed admission ordering is fixed and pending official checks pass.

## Follow-up review: opaque teacher-plan fix

**PASS — the original P1 admission-order finding is fixed in the staged integration.** This section supplements,
and does not erase, the historical failure above.

Re-read the updated `archive/agents/F/HOOKS.diff`: it now removes the entire `nnt::kShop` first-purchase preview block and
replaces it with the per-head-gated call to `nne::shop`. No additional inventory query, `build_for` scan/vector or
`cap_shop` call remains before admission. `nne::shop` calls once/admit first and uses an opaque `BuyKind::plan`
teacher option. `build_shop` ignores its compatibility-preview argument and zeros candidate0's item/count/cost/
owned/projected-gold descriptors; `teacher_plan` explicitly marks their sentinel interpretation. The unchanged
teacher executor is still selected by returning false on choice0 or admission refusal.

Updated schema `shop.json` is version2 and explicitly documents the opaque plan, zero sentinels and guarded
alternative semantics. The Python twin matches the C++ change. Independent rerun:

```
python -m unittest tests.python.test_economy_parity -v
git apply --check archive/agents/F/HOOKS.diff
```

Result: **5/5 tests OK**, including400 bit-exact synthetic fixtures plus the new opacity regression proving that
arbitrary preview contents cannot change candidate0; patch applicability exits0. TMP/TEMP remain inside the workspace.

**PENDING:** this remains a source/staged-patch pass. Official integrated Wasm identity, all profiles, real fuel,
NFS1 roundtrip and smoke checks remain pending. No original gameplay file was edited by this reviewer.

### Separate lifecycle finding discovered during the follow-up

**FAIL — P2: schema version/feature-meaning changes do not invalidate the action hash.**

`python/nfs/models/config.py:54-61` hashes name/id/F/K/contexts/bounds/outputs/sectors and feature name/scale/clip,
but excludes `version`, `semantics` and feature descriptions. The shop fix changes candidate0's feature meaning
while keeping those hashed fields identical. A model trained against the old preview features can therefore carry
the same action hash as the new opaque-plan schema; changing shop version1 to2 alone does not protect compatibility.

Synthetic reproduction `artifacts/tmp/E2/review_action_hash.py` changes version/semantics/descriptions only:

```
current_v2 0x4248a7f6
synthetic_v1_semantics 0x4248a7f6
collision True
```

Lead fix: include the explicit action-schema version in the hashed fields, and require a version bump whenever raw
feature construction/option interpretation changes. An explicit semantic feature-version field can provide stronger
protection without making editorial description changes invalidate exports. Regenerate models/registry after this
hash-contract change and add a compatibility test proving v1/v2 rejection. This is runtime/export ownership, not a
new F candidate-builder defect. All heads are still untrained, so no trained model migration is being claimed.
