# Reproduce the descriptive replay study

Requirements: Node 20+, Python 3.12, the vendored official CLI, and the pinned
official visualiser assets described in [docs/setup.md](../../../docs/setup.md).
No GPU, model fitting or new matches are needed. Raw files must stay local.
The commands use this checkout's `.venv-dev/Scripts/python.exe`; substitute your
Python 3.12 interpreter if needed. These three study tools use Python's standard
library and Node's built-in modules only.

From the repository root in PowerShell:

```powershell
$study = 'artifacts/local-only/top-team-study-2026-10-25'
New-Item -ItemType Directory -Force -Path $study | Out-Null
Copy-Item -LiteralPath 'research/v52/top-teams-2026-10-25/selection.json' -Destination "$study/selection.json"
Copy-Item -LiteralPath 'research/v52/top-teams-2026-10-25/ladder_snapshot.json' -Destination "$study/ladder.json"
```

The user completes `tools/vendor/cambc.exe login` if this device has no existing
session. The acquisition tool does not read or print credentials. Then:

```powershell
.venv-dev/Scripts/python.exe tools/replay/scout_public.py download --work $study --cli tools/vendor/cambc.exe
node --no-warnings tools/replay/decode_replays.mjs --workers 2 --out "$study/decoded.jsonl" "$study/replays"
node --no-warnings tools/replay/scout_states.mjs --out "$study/states" "$study/replays"
```

`ladder_snapshot.json` retains only original rank/name/team/rating labels and the
snapshot revision/freshness, omitting profiles and other irrelevant fields. Its
public source was
`https://2026a.battlecode.co.uk/api/v1/ladder?page=1&pageSize=100&category=all`.
Fetching that endpoint later gives a **new** snapshot; keep it separate.
Replay checksums in `matches.json` allow independent confirmation of the files.

With the original local metadata available:

```powershell
.venv-dev/Scripts/python.exe tools/replay/scout_report.py --work $study --out research/v52/top-teams-2026-10-25
```

For a **new** study, first run `scout_public.py catalog --work <fresh local
directory>`. It fetches a new ladder snapshot and bounded recent public group
pages. Keep its selection separate from this study's frozen selection.

The existing decoder produces a local raw action sequence. The new census uses
the same pinned engine and official snapshot decoder; it samples full states at
round boundaries, reads exact submitted-score deltas from every timeline step,
and retains final physical-body KDA. It has a progress guard, a 1.5-million-step
cap, an incomplete-game rejection, and a bank-total reconciliation check.

`scout_report.py` refuses a replay whose standard decode, census, public
score/outcome/round/draft metadata, checksums or action/fuel counts disagree.
`decoder_validation.json` separately records comparison with an existing local
official summary and the decoder's slower reference path.

Do not add raw bundles, decoded JSONL, state dumps or training arrays to Git.
The report directory contains only the narrative, fixed selection and compact
derived evidence. No benchmark, training or submission is implied by these commands.
