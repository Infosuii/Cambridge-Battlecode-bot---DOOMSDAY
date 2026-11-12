# Runs a long engine-lab job with a RAM watchdog: if free physical memory falls under 2 GB, the job's node process is
# killed (the PC crashed twice when training ran out of memory).
# usage: powershell -File run_guarded.ps1 -Script agent2\lab\es_host.js -Log out.log -Args2 "a b c"
param([string]$Script = "agent2\lab\es_host.js", [string]$Log = "guarded.log", [string]$Args2 = "")
$ArgList = @($Args2 -split " " | Where-Object { $_ })
Set-Location (Join-Path $PSScriptRoot "..\..")
$p = Start-Process node -ArgumentList (@($Script) + $ArgList) -NoNewWindow -PassThru -RedirectStandardOutput $Log -RedirectStandardError "$Log.err"
$minFree = 99
while (-not $p.HasExited) {
    Start-Sleep -Seconds 3
    $free = (Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB
    if ($free -lt $minFree) { $minFree = $free }
    if ($free -lt 2) {
        Stop-Process -Id $p.Id -Force
        Add-Content $Log "KILLED by watchdog: free RAM $([math]::Round($free, 2)) GB"
        Write-Output "KILLED: free RAM under 2 GB"
        break
    }
}
Write-Output ("done; lowest free RAM {0:N1} GB" -f $minFree)
