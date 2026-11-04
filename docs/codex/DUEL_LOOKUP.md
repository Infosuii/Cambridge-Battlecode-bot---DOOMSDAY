# Plan C group lookup regression

**MEASURED:** In the 4 November read-only capture, the twentieth unranked page (100 games per page) ended at 3 November 17:43:24 UTC, later than archived Plan C baseline arm's 16:24:12 UTC search start. The old report searched at most 20 pages. Its historical log `pipeline_c3.log` contained only 10 paired cells. Direct `cambc match-groups show <id> --json` still returned five finished matches for each of all 48 recorded groups.

The [recount](PLAN_C_AUDIT_RECOUNT.json) verifies opponent team ID, map name, side, position, engine version and the 120 match ID pairs. It reproduces v80/v92 at 57/120; v103/v92audit is 47/120, b/c=13/23, z=-1.6667. The recorded pin setting is in the archived plan; the read API does not expose the actual opponent submission or pin lineage. Never use this result as pin verification.

**Fix:** use group-ID reads and cache completed groups across polling sweeps; the report no longer depends on the age or volume of unrelated matches. The new path reran the full archived baseline and audit report against the live CLI's captured group responses. It returned 57/120 and 47/120 with 120 pairs; a second poll of a completed group did not query it again. No replayed arm or gate decision changed.

Reproduction: export `research/x3/duel/duel_20261103c.json` from handover commit `33c16873` to `artifacts/codex-p0/archived-plan-c-readonly.json`; capture the 48 recorded group IDs under `artifacts/codex-p0/duel-group-cache/<id>.json` with the official read command; run `py docs/codex/audit_archived_duel.py artifacts/codex-p0/archived-plan-c-readonly.json v92 v92audit --out <new-output.json>`. On this machine, a directly launched CLI can read the account, but Python subprocesses receive "Sign in first"; the recount uses direct CLI captures. Do not run the mutation pipeline until its own subprocess authentication and restoration have been verified.

## Required pin sources

A second local regression fixture gave the run action an empty baseline arm and replaced activation with an exception. The previous code reached activation; it would have omitted `--source-group` for missing slots. The new code exits before that call. Tests also rejected null, duplicate, short and empty ID lists for a candidate or recheck. A first baseline is allowed to establish the pin groups; a complete candidate arm gets exactly its ordered baseline IDs. This check is about preparation and was exercised without any authenticated CLI or platform mutation.

## Quota and restoration on early exit

The previous run path printed completion after a partial arm and returned success; the parent also ignored a failed child and restored only after the main loop. It could advance to another arm after incomplete work, or leave the candidate active after an exception. The new child fails on partial completion; the parent checks child exits and attempts to verify the fallback in its `finally` path whenever an arm or upload was attempted. A compile still queued, pending, building or compiling at the end of the wait now aborts. Before any create call, the child reads the rolling quota and waits if the shared count has reached 45.

Offline mocks verified that a child failure results in exactly one fallback restore and no next arm, a missing pin reaches neither upload nor restore, a persistently compiling queue causes no mutation, and quota readings 45/46/44 cause two waits. The unchanged archived baseline replay from captured groups still gives 57/120 against v92audit's 47/120. There were no live pipeline invocations.

## Unique candidate upload receipt

An offline pipeline fixture delivered the requested candidate as v102 and a concurrent unrelated upload as v103, both with the same archive filename. The old selector accepted every new row and chose v103. It also started an arm with no attributable upload or with duplicate matching receipts. The revised pipeline attaches a unique note, selects one new exact match, and uses the existing fallback path on ambiguity, absent receipt or compile timeout. It does not submit a second time when the first outcome is uncertain.

Reproduce with `py docs/codex/test_duel_upload.py`. All four scenarios pass against the fake CLI. The 48 cached Plan C groups reproduced the archived recount byte for byte (v92 57/120, v92audit 47/120, b/c=13/23, z=-1.667). This verifies attribution and preserves the historical recount. No real submission or ladder match was created.

## Verify the active selection is pinned

An offline activation test returned v80 as both active and selected while the pinned flag was false. The old early return skipped pinning. It also returned early for active v80 and selected v81. Activation and fallback now require a single read to show the requested version both active and selected, with pinned true. The regression fixture verifies both failures and the already-pinned no-op. The archived Plan C paired recount reproduced byte for byte again. No live activation was performed.
