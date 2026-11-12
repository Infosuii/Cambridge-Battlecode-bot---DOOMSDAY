param([Parameter(Mandatory)][ValidateSet('discovery','confirm')][string]$Partition)
$ErrorActionPreference = 'Stop'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = "$PWD/artifacts/codex-p0/py-deps"
$env:NFS_REPLAY_ENGINE = '2.0.0'
$assets = Get-ChildItem -LiteralPath "$env:LOCALAPPDATA/cambc/assets" -Directory |
  ForEach-Object { Join-Path $_.FullName 'visualiser/assets' } |
  Where-Object { Test-Path -LiteralPath (Join-Path $_ 'v2_0_0-hWOQ1R8f.wasm') } |
  Select-Object -First 1
if (!$assets) { throw 'Official engine 2.0.0 replay assets missing' }
$env:NFS_REPLAY_ASSETS = [string]$assets
py research/codex-ishan/discovery3/run_profiles.py $Partition prepare
if ($LASTEXITCODE -ne 0) { throw 'Failed to prepare inputs' }
$part = "artifacts/codex-p0/discovery3/$Partition"
$reps = @(Get-ChildItem "$part/replays/rep" -Filter '*.repl26a' | ForEach-Object FullName)
node tools/replay/winner_profile.mjs "$part/analysis/winner_profile.json" @reps
if ($LASTEXITCODE -ne 0) { throw 'Winner profile failed' }
node tools/replay/death_context.mjs 600 "$part/analysis/death_context.json" @reps
if ($LASTEXITCODE -ne 0) { throw 'Death context failed' }
node tools/replay/camp_clear.mjs "$part/analysis/camp_clear.json" @reps
if ($LASTEXITCODE -ne 0) { throw 'Camp clear attribution failed' }
py research/codex-ishan/discovery3/run_profiles.py $Partition finish
if ($LASTEXITCODE -ne 0) { throw 'Failed to combine analyses' }
py research/codex-ishan/discovery3/metrics.py $Partition
if ($LASTEXITCODE -ne 0) { throw 'Failed to summarize replay metrics' }
