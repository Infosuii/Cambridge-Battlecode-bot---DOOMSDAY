$ErrorActionPreference = 'Stop'
$plan = Get-Content -LiteralPath 'research/codex-ishan/discovery4/DISCOVERY_SAMPLE.json' -Raw | ConvertFrom-Json
$count = 0
foreach ($match in $plan.matches) {
    $id = ([guid]$match.matchId).ToString()
    if ($match.partition -notin @('discovery', 'confirm')) { throw 'Unexpected partition' }
    $directory = Join-Path 'artifacts/codex-p0/discovery4' $match.partition
    New-Item -ItemType Directory -Force -Path "$directory/summaries", "$directory/replays" | Out-Null
    $summary = "$directory/summaries/$id.json"
    $replay = "$directory/replays/$id.zip"
    if (!(Test-Path -LiteralPath $summary)) {
        & .\tools\vendor\cambc.exe matches summary --json -o $summary $id
        if ($LASTEXITCODE -ne 0) { throw "Summary failed: $id; respect any server retry interval before resuming" }
    }
    if (!(Test-Path -LiteralPath $replay)) {
        & .\tools\vendor\cambc.exe matches download $id -o $replay
        if ($LASTEXITCODE -ne 0) { throw "Replay failed: $id; respect any server retry interval before resuming" }
    }
    $count += 1
    Write-Output "Captured $count/$($plan.matches.Count)"
}
