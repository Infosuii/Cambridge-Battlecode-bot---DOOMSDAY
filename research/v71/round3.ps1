# Round 3 of per-map knob profiles: ten second-generation profiles on the 33 maps without a v72 profile.
# Selection seeds 1/2/5/6 on a plan of those maps only; the new entries are merged with v72's table into bots/v73, which
# is validated against bots/v72 on fresh seeds 19/20 over the whole pool. Output: research/v71/round3.txt
$ErrorActionPreference = 'Stop'
Set-Location "C:\projects\cambridge battlecode\work\neural-full-stack"
$py = '..\neural-gameplay\.venv\Scripts\python.exe'
$out = 'research/v71/round3.txt'
"round 3 started $(Get-Date -Format o)" | Set-Content $out
$names = 'hunt2','ranged2','search2','huntranged','bankhunt','softcaut','softaggr','decisive','patient','teamfight'
& $py tools/v67/c_profiles.py --base bots/v72 --out-prefix artifacts/tmp/v67/v73p --only @names 2>&1 | Add-Content $out
# Plans with the maps v72's table leaves alone.
& $py -c @"
import json
tab = set(json.load(open('research/v71/knob_table_r2.json'))['table'])
maps = sorted(p for p in json.load(open('artifacts/tmp/v67/map_keys_full.json')) if p not in tab)
teams = list(dict.fromkeys(g['opponent'] for g in json.load(open('research/v59/duel_top1.json'))['groups']))
slots = [(m, s) for m in maps for s in 'ab']
json.dump({'note': 'maps without a v72 profile', 'groups': [{'opponent': 'pool', 'maps': [m for m, _ in slots[i:i+10]], 'sides': [s for _, s in slots[i:i+10]]} for i in range(0, len(slots), 10)]}, open('research/v71/r3_plan.json', 'w'), indent=1)
json.dump({'note': 'maps without a v72 profile, each group vs a top team', 'groups': [{'opponent': teams[k % len(teams)], 'maps': [m for m, _ in slots[i:i+5]], 'sides': [s for _, s in slots[i:i+5]]} for k, i in enumerate(range(0, len(slots), 5))]}, open('research/v71/r3_plan_teams.json', 'w'), indent=1)
print(len(maps), 'maps in the round-3 plans')
"@ 2>&1 | Add-Content $out
$jobs = @('base=bots/v72') + @($names | ForEach-Object { "$_=artifacts/tmp/v67/v73p-$_" })
foreach ($o in 'v65','v61','v58') {
    & $py tools/v67/c_batch.py --seeds 1 2 5 6 --workers 2 --opponent $o --plan research/v71/r3_plan.json @($jobs | ForEach-Object { "S-$o-$_" }) 2>&1 | Add-Content $out
}
& $py tools/v67/c_batch.py --seeds 1 2 5 6 --workers 2 --opponent proxy --per-team --plan research/v71/r3_plan_teams.json @($jobs | ForEach-Object { "S-proxy-$_" }) 2>&1 | Add-Content $out
$a = @()
foreach ($o in 'v65','v61','v58','proxy') { $a += '--base', "$($o)=S-$o-base" }
foreach ($n in $names) { foreach ($o in 'v65','v61','v58','proxy') { $a += '--option', "$($n):$($o)=S-$o-$n" } }
& $py tools/v67/c_draft_league.py @a --keys artifacts/tmp/v67/map_keys_full.json --out research/v71/knob_table_r3.json --min-gain 100 --max-loss 250 2>&1 | Add-Content $out
& $py -c @"
import json
r2 = json.load(open('research/v71/knob_table_r2.json'))
r3 = json.load(open('research/v71/knob_table_r3.json'))['table']
merged = dict(r2['table']); merged.update({m: t for m, t in r3.items() if m not in merged})
json.dump({'note': 'v72 table plus round-3 entries for maps it left alone', 'table': merged}, open('research/v71/knob_table_v73.json', 'w'), indent=1)
print('v73 table', len(merged), 'maps (', len(r3), 'new )')
"@ 2>&1 | Add-Content $out
if (-not (Test-Path bots/v73)) {
    New-Item -ItemType Directory bots/v73 | Out-Null
    Copy-Item -Recurse bots/v70/src bots/v73/src
    & $py tools/v67/c_v71_knobs.py bots/v73 research/v71/knob_table_v73.json 2>&1 | Add-Content $out
}
foreach ($o in 'v65','v61','v58') {
    & $py tools/v67/c_batch.py --seeds 19 20 --workers 9 --opponent $o "T-$o-v72=bots/v72" "T-$o-v73=bots/v73" 2>&1 | Add-Content $out
}
& $py tools/v67/c_batch.py --seeds 19 20 --workers 9 --opponent proxy --per-team --plan research/v70/pool_plan_teams.json "T-proxy-v72=bots/v72" "T-proxy-v73=bots/v73" 2>&1 | Add-Content $out
foreach ($o in 'v65','v61','v58','proxy') { & $py tools/v67/c_paired.py "T-$o-v73" "T-$o-v72" 2>&1 | Add-Content $out }
"round 3 finished $(Get-Date -Format o)" | Add-Content $out
