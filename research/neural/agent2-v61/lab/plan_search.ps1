# Specialist-plan searches (E61): one 48-knob black-box search per map cluster (clusters/c<k>_train.txt), run one
# after another through the RAM watchdog. Lab bot m62_c1, opponents v61_c2 + b5_c2 (seed 3 kept for tests),
# start = v61 knobs. Output: plan_c<k>.tsv / .log.
# usage: powershell -File agent2\lab\plan_search.ps1 [-Clusters "0,1,2,3"] [-Gens 15] [-Workers 5]
# -Resume: start each cluster from the last generation of plan_c<k>a.tsv (an earlier stopped run) when it exists.
param([string]$Clusters = "0,1,2,3", [int]$Gens = 15, [int]$Workers = 5, [switch]$Resume)
Set-Location (Join-Path $PSScriptRoot "..\..")
$env:ENGWASM = "tools\viz\v2_0_0.wasm"
$env:BOTS_DIR = "v4\bots"
$env:LAB_BOT = "m62_c1"
$env:ES_OPPS = "v61=v61_c2,b5=b5_c2"
$env:CTX_F = "1"
$env:KNOB_INIT = (Get-Content agent2\lab\knobs_m62_init.txt -Raw).Trim()
foreach ($k in $Clusters -split ",") {
    $env:ES_MAPLIST = "agent2/lab/clusters/c${k}_train.txt"
    $env:ES_SEED = "$(610 + [int]$k)"
    $env:KNOB_INIT = (Get-Content agent2\lab\knobs_m62_init.txt -Raw).Trim()
    $g = $Gens
    if ($Resume -and (Test-Path "agent2\lab\plan_c${k}a.tsv")) {
        $rows = @(Get-Content "agent2\lab\plan_c${k}a.tsv" | Select-Object -Skip 1)
        if ($rows.Count -gt 0) {
            $env:KNOB_INIT = ($rows[-1] -split "`t" | Select-Object -Skip 5) -join ","
            $env:ES_SEED = "$(710 + [int]$k)"
            $g = [Math]::Max(1, $Gens - $rows.Count)
        }
    }
    $out = powershell -File agent2\lab\run_guarded.ps1 -Script agent2\lab\knob_ctx.js -Log "agent2\lab\plan_c$k.log" -Args2 "agent2/lab/plan_c$k.tsv $g 12 25 0.25 0.10 $Workers" 2>&1 | Out-String
    Write-Output "cluster ${k}: $out"
    # A watchdog kill stops the chain (the next cluster would hit the same memory limit).
    if ($out -match "KILLED") { Write-Output "STOPPED at cluster $k (RAM watchdog)"; break }
}
