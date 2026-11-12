# Round 4: revisit the per-map draft on top of v73's knob profiles. Each forced lineup is played on every pool map with
# v73's knob table (draft table off), selection seeds 1/2/5/6 against the league; a map changes lineup only if the
# combination beats v73 there. bots/v74 = v69 + updated draft table + v73 knob table, validated against v73 on fresh
# seeds 21/22. Output: research/v71/round4.txt
$ErrorActionPreference = 'Stop'
Set-Location "C:\projects\cambridge battlecode\work\neural-full-stack"
$py = '..\neural-gameplay\.venv\Scripts\python.exe'
$out = 'research/v71/round4.txt'
"round 4 started $(Get-Date -Format o)" | Set-Content $out
$lineups = 26, 21, 22, 6, 24, 27, 28
foreach ($l in $lineups) {
    if (-not (Test-Path "artifacts/tmp/v67/v74l-$l")) {
        & $py tools/v67/c_variant.py --base bots/v73 --out "artifacts/tmp/v67/v74l-$l" --set A2_MLDRAFT=0 --set "NOVA_ALL_LINEUP=$l" --set V70_DRAFT_TABLE=0 2>&1 | Add-Content $out
    }
}
$jobs = @('base=bots/v73') + @($lineups | ForEach-Object { "l$_=artifacts/tmp/v67/v74l-$_" })
foreach ($o in 'v65','v61','v58') {
    & $py tools/v67/c_batch.py --seeds 1 2 5 6 --workers 2 --opponent $o @($jobs | ForEach-Object { "U-$o-$_" }) 2>&1 | Add-Content $out
}
& $py tools/v67/c_batch.py --seeds 1 2 5 6 --workers 2 --opponent proxy --per-team --plan research/v70/pool_plan_teams.json @($jobs | ForEach-Object { "U-proxy-$_" }) 2>&1 | Add-Content $out
$a = @()
foreach ($o in 'v65','v61','v58','proxy') { $a += '--base', "$($o)=U-$o-base" }
foreach ($l in $lineups) { foreach ($o in 'v65','v61','v58','proxy') { $a += '--option', "$($l):$($o)=U-$o-l$l" } }
& $py tools/v67/c_draft_league.py @a --keys artifacts/tmp/v67/map_keys_full.json --out research/v71/draft_table_r4.json --min-gain 100 --max-loss 250 2>&1 | Add-Content $out
& $py -c @"
import json
old = json.load(open('research/v70/draft_table_v70.json'))['table']
new = json.load(open('research/v71/draft_table_r4.json'))['table']
merged = dict(old)
merged.update(new)
json.dump({'note': 'v70 draft table updated by round 4 (lineups re-chosen on top of v73 knob profiles)', 'table': merged}, open('research/v71/draft_table_v74.json', 'w'), indent=1)
print('v74 draft table', len(merged), 'maps;', len(new), 'entries from round 4')
"@ 2>&1 | Add-Content $out
if (-not (Test-Path bots/v74)) {
    New-Item -ItemType Directory bots/v74 | Out-Null
    Copy-Item -Recurse bots/v69/src bots/v74/src
    & $py tools/v67/c_v70_draft.py bots/v74 research/v71/draft_table_v74.json 2>&1 | Add-Content $out
    & $py tools/v67/c_v71_knobs.py bots/v74 research/v71/knob_table_v73.json 2>&1 | Add-Content $out
}
foreach ($o in 'v65','v61','v58') {
    & $py tools/v67/c_batch.py --seeds 21 22 --workers 9 --opponent $o "X-$o-v73=bots/v73" "X-$o-v74=bots/v74" 2>&1 | Add-Content $out
}
& $py tools/v67/c_batch.py --seeds 21 22 --workers 9 --opponent proxy --per-team --plan research/v70/pool_plan_teams.json "X-proxy-v73=bots/v73" "X-proxy-v74=bots/v74" 2>&1 | Add-Content $out
foreach ($o in 'v65','v61','v58','proxy') { & $py tools/v67/c_paired.py "X-$o-v74" "X-$o-v73" 2>&1 | Add-Content $out }
"round 4 finished $(Get-Date -Format o)" | Add-Content $out
