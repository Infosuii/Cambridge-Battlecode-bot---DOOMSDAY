# Productive lifecycle and map-package repairs — 2026-11-01

This is development progress, not a competitive bot or a release recommendation.
The working map package remains enabled only with **DZ_ECONOMY_V2=1 and
DZ_LIFECYCLE=1**. Both defaults remain zero. No weights were transferred,
no online games were launched, and no release, submission or activation changed.

The user clarified the engineering standard during implementation: accept useful
gameplay risk, and diagnose/repair an underperforming package before abandoning
it. Candidate06 was initially removed too quickly. It was restored and repaired
in09/10. It remains available for further work; candidate05 is a frozen stronger
collision comparison, not a competing controller running inside the bot.

## Results and provenance

All numbers below are untraced deterministic development games. A/B means DZ's
spawn side. Opponents are the exact v76lab and v81hl sources from the intake.
Both sides still lose every listed game. These cells are not a general win rate.

| Candidate | Collision v76lab bank A/B | Collision v81hl bank A/B | Packs v76lab bank A/B |
|---|---:|---:|---:|
| Frozen advanced control, f81b101c | 0 / 0 | 0 / 0 | unmeasured here |
| First complete lifecycle02 | 88 / 103 | 88 / 103 | unmeasured |
| More permissive execution05 | 183 / 181 | 134 / 181 | 28 / 0 |
| Initial map package06 | 188 / 81 | unmeasured | 28 / 0 |
| Repaired package09 | 122 / 64 | unmeasured | 148 / 0 |
| Current package10 | 80 / 26 | 80 / 26 | 56 / 56 |

Package10 also banks56/56 on packs against v81hl. It fixes that demonstrated
zero-output side but regresses collision against05. Keep that tradeoff visible;
do not promote10 or call its map plans optimised. Candidate05 remains the better
measured collision incumbent. Its v76lab binary is
`3bf0d1e7b5260470c12e2626eeefdbe3c09620a9081ca0596d0aefafbf058318`;
the source-identical v81hl build has a different binary hash, recorded separately.

The current package10 has the SAME binary across both opponents:
`5bee79c68dc723e9e8ae767f8ccf849a614b277c1334b998d2dfcdc2175dc260`.
Each of its eight cells has zero native faults and fuel-outs. Deaths remain a
material gameplay cost: packs-B has17, despite delivering56. On collision all
three bodies demonstrate an ordered positive camp receipt → bank → purchase →
return receipt. Packs-B has **zero** bodies satisfying that complete ordered
cycle; collecting and banking56 does not establish repeated conversion there.

`scoreboard.csv` reports R100/R250 gold, spending, collection, submission,
captures, clears, full-game gold/spending, deaths, scores, outcomes and runtime
counters for every untraced candidate. Home/idle rounds are unmeasured for those
builds. Trace capsules retain cumulative task counts, but trace strength numbers
are not acceptance evidence. `SOURCE.json` pins current files and development
settings. Each run's `provenance.json` and `evidence.zip` retain frozen source,
binaries, native summaries and replay hashes; completed capsules were not edited.

## Reference evidence and actual divergence

Four downloaded existing games, all exact-map-hash matches to the local pool:

* Mite–Ad Astra, collision, `ca170a4d-50d9-4491-a7ae-f8490565cc4b`, Nov1 11:00 UTC.
* Fish–NEETCoders, expanse, `3536220a-c571-421f-91cd-4156775e019f`, Nov1 11:20 UTC.
* print dont int–Fish, split, `656686a8-4b80-4a08-814c-24e23b79ad4c`, Nov1 11:00 UTC.
* Claudus–Mite, packs, `1bf7d5f5-21a3-4f08-9241-ab9cddda593b`, Oct29 12:40 UTC.

The fresh ladder snapshot places Fish first and Mite fourth. Opponent submission
versions are not public and remain unknown. `references.json` contains group URLs,
metadata, retrieval times, engine/build identifiers, replay bundle/inner hashes,
summary hashes and concrete actions/purchases/payouts. The first250 rounds were
decoded into ordered native actions plus each actor's own legal perspective.
Raw data stay in `artifacts/local-only/dz-cycle-reference-2026-11-01`.

| Observed behaviour | DZ divergence | Implemented dependency/package | Complete-game check |
|---|---|---|---|
| Legacy collision collects, buys, banks and returns; the frozen DZ earns zero | Optional access/crew/auction work consumes the first executable job | Bounded lifecycle owns an incumbent before optional prerequisites; requested navigation survives |02 gains88/103 bank, actual purchases and repeat receipts |
| Mite packs' three bodies attack the same harmless resource patch from R10–15 | Singleton soft claims exclude helpers; ordinal discovery sends B toward group2 instead of its observed group3 opening | Harmless assistance, capture election, exact packs side opening, finite contracts |09 A improves to148; B still0, so assistance alone is insufficient |
| Leaders move and cast during the opening | DZ waits for full altar preparation before farming | Publish playable income readiness only AFTER all terrain, home and camp designs exist; finish altar boot after the action |10 packs-B first own movement is R5 rather than the old R13; B banks56 |
| Mite collision Vendetta uses attack → reset → refreshed attack, and travel casts | DZ can retain a killed target, choose an out-of-range member, and omit travel casts | Live in-range targeting, singleton reset refresh, legal travel casts through Actuator | Native06/10 replays show travel casts; all managed/siege overrides remain locked |
| Mite collision Heart buys Focus and uses its landing kit | Copied purchases were present without a farm execution for the damaging dash | Checked landing strike, collateral exclusion, healthy unfunded shield deferral, no managed/siege interference |10 exercises the repaired package; its competitive effect is still poor |
| Capture ownership is followed by real delivery | A raw gem bid can collect without creating a bank task | Actual bag creates a finite delivery task; live bank admission keeps Deferred distinct from Denied |10 collision banks80/26; packs56/56, but packs-B still lacks a full repeated cycle |

At collision R15, Mite Vendetta is at(23,17), full1000HP, with no personally visible
enemy; it attacks the camp at(24,18), resets and attacks again. At packs R10–15,
Mite Vesper, Heart and Vendetta attack the shared resource patch, rather than
three exclusive solo assignments. These are observations, not recovered intent.
Fish's expanse Prospector/Monster roles and split Capture/Focus Marcella differ
from collision; they are reference evidence, not implemented or validated plans.
No Varg behaviour or trained camp/draft scorer was imported.

The expired-respawn omission was repaired using full design HP/strength for a
new unseen generation. Candidate08 still failed packs-B. It was a real source
omission, not a sufficient explanation of that side's loss. Likewise, startup
and kit repairs improve some transitions without proving that the whole copied
policy now matches Mite. Damaging camp staffing, contested delivery, combat
interruptions and equipment/executor compatibility remain the main open work.

## One owner per transition/action

| Responsibility | Owner |
|---|---|
| Singleton selection, retention and finite failure | lifecycle_goal / existing Contract |
| Harmless helpers and capture handoff | Lifecycle soft claims; existing authoritative crew capturer wins |
| Managed damaging crew, formation and focus | Existing economy/crew_action; lifecycle refuses ownership |
| Siege strike/withdrawal | Existing siege task; no singleton reset or dash overrides it |
| Collection-to-bank transition | Lifecycle actual-bag commitment |
| Channel permission and unsafe withdrawal | Existing bank_admission / neutral recovery |
| Shopping/recovery and return | Lifecycle Home task, funded fixed/map-specific purchase plan, existing executor |
| Combat interruption | Existing engagement model; unfinished optional rollout falls back to the bounded visible-unit check |
| Every move/attack/cast/channel/purchase | Existing execute and Actuator; adapters emit no independent SDK actions |

Unknown hazards are not declared safe. Completed unsafe checks withdraw. A
budget-interrupted escape search can retain bounded live progress at healthy HP;
an observed affordable isolated pull can be finished instead of requiring a
separate geometric exit. Low HP, actual recovery, transactional funded shields,
managed crew barriers and bank admission remain authoritative.

## Coverage, reproduction and next repair

`map-strategies.json` inventories all70 maps and both sides. Fourteen registered
maps remain unopened holdouts; their hashes/strategy fields are intentionally
pending. Three maps have development measurements. The remaining53 have no new
measured strategy. Inventory coverage is **not** completion of map optimisation.
No seed121–124 or reserved trajectory was used. No map is labelled optimised.

Reproduce current source with the configured Python executable:

```
tools/dz.py smoke --name NEW_NAME --maps 00collision 00packs --opponent v76lab --set DZ_ECONOMY_V2=1 --set DZ_LIFECYCLE=1 --workers 2
```

Use `tools/dz_cycle_report.py --names RUNS --output artifacts/tmp/report.json` for
native ordered lifecycle proofs and gear purchases. `rebuild.py` regenerates this
compact evidence/registry from the named immutable capsules and downloaded raw
references. Existing24 host suites and58 Python tests passed; final default and
development configurations compile. Validation logs are in this directory.

The next repair should preserve package10 and the frozen05 comparison. Diagnose
why the actual three-body damaging-farm/gear transition stalls after packs'
resource payout, and why collision loses tempo after the new opening. Check the
live crew/kit execution against the reference before discarding its design.
Do not begin another wide map campaign or another scalar threshold sweep.
