# Farm-speed knob search (E68): knob_ctx.js with ES_SCORE=farm, p63b against the idle bot on farm_train maps.
param([int]$Gens = 15, [int]$Workers = 5)
Set-Location (Join-Path $PSScriptRoot "..\..")
$env:ENGWASM = "tools\viz\v2_0_0.wasm"; $env:BOTS_DIR = "v4\bots"; $env:LAB_BOT = "p63b"; $env:ES_OPPS = "idle=idle4"
$env:CTX_F = "1"; $env:ES_SCORE = "farm"; $env:LAB_DRAFT_FUEL = "10000000"; $env:ES_SEED = "868"
$env:ES_MAPLIST = "agent2/lab/clusters/farm_train.txt"
$env:KNOB_INIT = (Get-Content agent2\lab\knobs_m62_init.txt -Raw).Trim()
powershell -File agent2\lab\run_guarded.ps1 -Script agent2\lab\knob_ctx.js -Log "agent2\lab\farm_s1.log" -Args2 "agent2/lab/farm_s1.tsv $Gens 12 25 0.25 0.10 $Workers"
