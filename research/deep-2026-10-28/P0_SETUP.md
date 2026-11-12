# Session 1 setup and provenance

Updated 2026-10-28T16:04:21.416097+00:00. Source freeze, metadata setup and replay intake complete.
555 official replay/native pairs pass, including five calibration games validated before bulk decoding.
The original CLI/source observations below remain historical; current download evidence is in REPLAY_RETRIEVAL.md.

| Check (measured) | Result | Sample |
|---|---|---:|
| CLI | official cambc 4.0.0 Linux x86_64 |1 binary|
| Binary SHA256 |552056aab1b99a6626597b6aaf0ae38f967709626f90f2d6926c4510ca929eb4|1 binary|
| Engine |2.0.0, all shared-loader pins match; instantiates|3 assets|
| User archive |bot.zip,284031 bytes,33 files|1 archive|
| Match against v58 |29/33 source files byte-identical|33 files|
| Remote frozen copy |33/33 Git blob hashes match ZIP|33 files|
| Native internal checks |draft/roster/gem/gold identities pass|555 summaries,5,356 champion bodies|
| Replay/native reconciliation |all final-state, draft and roster checks pass|555 games|
| Website account |Ishanp signed in; live platform 69 Active/Verified|1 submission|
| CLI session |not authenticated; login initiation refused before credentials|2 prior attempts|

Archive SHA256:0433755c1cbc5f120247c132a6c875912f14c3ac5f36abaa7edbfe20845b325c.
Canonical tree SHA256:5b07f2bfb84f8168a2d24e8fa67a2d431cc836999137576a238f666d2fb08eb2.
Definition and per-file hashes: LIVE_SOURCE.json. Frozen copy: bots/live-69/src.
Remote source-copy staging tree:b31cff2ee61823585117100158bd08ba286318bc.
The user supplied this archive as live 69. The blocked server archive was not
independently hashed. Submission:f91de3f0-0453-409e-b712-b86067eecbca,
note“v75 ladder duel candidate”, uploaded by Om. Absolute activation time unknown.

The correct attachment supersedes the five earlier 16/17-file input archives.
Their original hashes and comparisons remain in INPUT_PROVENANCE.json.

## Decoder migration and its limit

decode_replays.mjs now imports engine/defaultAssets/verifyAssets/PINNED/VERSION
from engine.mjs, eliminating its duplicate 1.0.3-only loader. Its summary comparison
checks the selected version. Engine 2 remains explicit: NFS_REPLAY_ENGINE=2.0.0.
Default asset search supports Linux and Windows; NFS_REPLAY_ASSETS overrides it.
Syntax, official asset pins, engine instantiation and all 555 replay/native comparisons pass.
Five calibration pairs passed before bulk processing. Own-perspective and detector semantics still require separate validation. The older cached 0.0.3 replays fail the engine 2 load and
are excluded rather than coerced through another engine.

Native rosters are dynamic: a draft may have fewer than ten picks/champions;
Cassi & Issac share one draftPick while having separate champion IDs. The native
auditor checks each recorded roster entry against its actual pick and does not
assume a ten-champion roster (measured, n=555 summaries / 5,356 physical champion bodies).

## Repository and boundaries

Parent working branch:claude/compare-fix-replay-decoder, pinned commit
294500b8c4da4af19a81f2cdb262305ea54d27f9. Main lacks the newer v59–v67 reports.
The resumed Windows checkout is a full clone; the earlier connector checkout was partial.
Preserve every unrelated entry. Publish only analysis/deep-2026-10-28, without force. Frozen bot bytes remain
unchanged. No account settings, submissions, activations or ranked requests.
