# Deep analysis: Session 1 checkpoint

Updated 28 October 2026. **Session 1 started; setup is blocked, not complete.**

## Phase

Session 1, section 2.1: establish the current live source and activation interval.
The next phase is authenticated provenance, followed by current-game ingestion,
wave 1 (up to 14 mirrored groups), and detector implementation/validation.

## Repository

- Repository: `Infosuii/neural-networkk-battlecode` only.
- Analysis branch: `analysis/deep-2026-10-28`.
- Parent branch: `claude/compare-fix-replay-decoder`, explicitly named in
  `research/v67/HANDOFF.md` and the historical `docs/handoff.md` section 10.
- Parent commit: `294500b8c4da4af19a81f2cdb262305ea54d27f9`.
- Parent tree: `978b2b6bc8f35c6a4b6d125c948b51de65195289`.
- GitHub connector supplies pinned files and branch publication. Direct Git
  authentication is unavailable here. Local files are a partial materialization;
  remote commits must preserve the complete parent tree.
- Main is older in development content: it has versions through v58, whereas the
  named branch has v59-v67 research. Do not restart analysis from main's README.

## Completed preflight

- Installed the official `cambc==4.0.0` Linux wheel using the package command
  advertised on the official CLI page.
- `cambc --version` reports `cambc 4.0.0` (measured, n=1 binary).
- Extracted official visualiser assets with `cambc mapeditor --no-browser` and
  stopped its local server afterward. All three engine-2 checksum pins match
  `tools/replay/engine.mjs`; loader instantiates (measured, n=3 assets).
- Hashed all five attached source archives and compared every source entry
  against each bot source tree in the pinned branch.
- Captured a public ladder page with 100 teams and the latest public listing of
  25 DOOMSDAY groups; expanded the newest group (5 match metadata rows).
- Created the analysis branch. No bot source or account setting changed.

## Blocking evidence

- CLI ladder read: `Sign in first with cambc login`.
- Two CLI login starts failed immediately with `error: io: Connection refused`,
  including one explicit official event origin. No credentials were entered.
- The available website session shows `Not signed in`.
- One official replay-bundle read returned HTTP 401. Stop private downloads until
  the user restores authentication; do not extract browser cookies or tokens.
- No `artifacts/local-only/live-src/bot.zip` was provided. `apex_c9.zip` has 17
  files, not the 33-file bundle described by the master prompt. It is not an exact
  match for any pinned bot tree. See INPUT_PROVENANCE.json.
- The earlier conversation observed platform v69 with note `v75 ladder duel
  candidate`. That is historical UI evidence only; current live identity,
  activation time and source hash remain unverified.

## Budget and groups

`SCRIMMAGES.json`: 0 groups queued by this study / total cap 24.
Wave 1 cap 14; wave 2 cap 10. No quota consumed by preflight.
Do not queue until the current source, activation interval and map selection are
recorded. Reserve wave 2 for written hypotheses after FAST_FINDINGS.md.

## Files produced

- `P0_SETUP.md`: reproducible environment, blockers and decoder issue.
- `P1_DATA.md`: actual counts and attribution exclusions.
- `INPUT_PROVENANCE.json`: exact archive/file hashes and all bot comparisons.
- `PUBLIC_SNAPSHOT.json`: current ranks/ratings and provisional cohort candidates.
- `ACCESS_CHECKS.json`: sanitized preflight receipt.
- `SCRIMMAGES.json`: empty ledger and preserved budget.
- `tools/replay/deep_preflight.py`: repeatable input hashing/public snapshot tool.

## Next action

1. Restore sign-in in the task's website browser, or supply a user-authenticated
   CLI session on the executing device. Browser-only continuation is allowed by
   the master prompt, but never transfer its session secrets into shell tools.
2. Recheck Submissions; record live/selected/active IDs, uploaded time and actual
   activation evidence. Download our live source and hash its exact bytes. If
   activation time is unknown, bound it explicitly and quarantine ambiguous games.
3. Compare the downloaded tree against every `bots/*/src`; preserve an unchanged
   `bots/live-<platform version>` only if absent, as authorized in section 2.1.
4. Collect current-game metadata, finalize Learn/Climb/Control cohorts, and select
   wave-1 maps from verified current-version losses/coverage. Queue mirrored sides
   with a ledger reservation before each request; confirm response IDs.
5. Fix/use an engine-2-compatible decoder. The standalone decode_replays.mjs is
   still hardcoded to engine 1.0.3 despite the shared loader supporting engine 2.
   Validate 5 native-summary/replay pairs before bulk processing.
6. Download both wins and losses plus >=30 top-versus-top games, reconcile every
   accepted game, freeze the stratified 70/30 split (seed 20261028), then implement
   D1-D11 and validate event semantics. Do not report detector rates from n=0.

Historical findings are context, not measured facts about today's live bot.
Never submit, activate, request ranked matches or edit frozen bot sources.
