# Round 2 of per-map knob profiles: wait for the seed 5/6 league runs, reselect from seeds 1/2/5/6, build bots/v72 and
# validate it against bots/v71 on fresh seeds 17/18 against v65, v61, v58 and the proxy. Output: research/v71/round2.txt
$ErrorActionPreference = 'Stop'
Set-Location "C:\projects\cambridge battlecode\work\neural-full-stack"
$py = '..\neural-gameplay\.venv\Scripts\python.exe'
$out = 'research/v71/round2.txt'
$names = 'aggr','caut','bank','hoard','hunt','group','gems','gold','mid','nomid','search','ranged'
$opps = 'v65','v61','v58','proxy'
$need = @($opps | ForEach-Object { $o = $_; @('base') + $names | ForEach-Object { "artifacts/evaluations/v67/Q-$o-$_/games.json" } })
while (@($need | Where-Object { -not (Test-Path $_) }).Count -gt 0) { Start-Sleep -Seconds 30 }
"round 2 started $(Get-Date -Format o)" | Set-Content $out
$a = @()
foreach ($o in $opps) { $a += '--base', "$($o)=I-$o-v70,Q-$o-base" }
foreach ($n in $names) { foreach ($o in $opps) { $a += '--option', "$($n):$($o)=P-$o-$n,Q-$o-$n" } }
& $py tools/v67/c_draft_league.py @a --keys artifacts/tmp/v67/map_keys_full.json --out research/v71/knob_table_r2.json --min-gain 100 --max-loss 250 2>&1 | Add-Content $out
if (-not (Test-Path bots/v72)) {
    New-Item -ItemType Directory bots/v72 | Out-Null
    Copy-Item -Recurse bots/v70/src bots/v72/src
    & $py tools/v67/c_v71_knobs.py bots/v72 research/v71/knob_table_r2.json 2>&1 | Add-Content $out
}
foreach ($o in 'v65','v61','v58') {
    & $py tools/v67/c_batch.py --seeds 17 18 --workers 9 --opponent $o "R-$o-v71=bots/v71" "R-$o-v72=bots/v72" 2>&1 | Add-Content $out
}
& $py tools/v67/c_batch.py --seeds 17 18 --workers 9 --opponent proxy --per-team --plan research/v70/pool_plan_teams.json "R-proxy-v71=bots/v71" "R-proxy-v72=bots/v72" 2>&1 | Add-Content $out
foreach ($o in $opps) { & $py tools/v67/c_paired.py "R-$o-v72" "R-$o-v71" 2>&1 | Add-Content $out }
"round 2 finished $(Get-Date -Format o)" | Add-Content $out
