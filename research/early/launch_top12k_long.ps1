# Detached 150-minute BC run on the top-team dataset plus its independent supervisor (survives the chat session).
$repo = 'C:\projects\cambridge battlecode\work\neural-full-stack'
$py = 'C:\projects\cambridge battlecode\work\neural-gameplay\.venv\Scripts\python.exe'
$env:PYTHONPATH = "$repo\python"; $env:TMP = "$repo\artifacts\tmp"; $env:TEMP = "$repo\artifacts\tmp"
$env:PYTHONDONTWRITEBYTECODE = '1'; $env:PATH = "C:\msys64\ucrt64\bin;$env:PATH"
$run = "$repo\artifacts\runs\bc-top12k-long"
$logs = "$repo\research\early\logs"
$data = 0..5 | ForEach-Object { "`"$repo\artifacts\local-only\bc-top12k\batch$_`"" }
$train = @("`"$repo\tools\policy_bc.py`"", '--data') + $data + @('--out', "`"$run`"", '--minutes', '150', '--epochs', '5000',
  '--fp16-storage', '--cosine', '--export-every-minutes', '25', '--patience', '60', '--move-distance-offset', '40',
  '--device', 'cuda', '--i-authorize-training')
$t = Start-Process -FilePath $py -ArgumentList $train -WorkingDirectory $repo -WindowStyle Hidden -PassThru `
  -RedirectStandardOutput "$logs\top12k_long_train.out" -RedirectStandardError "$logs\top12k_long_train.err"
Start-Sleep -Seconds 5
$sup = @("`"$repo\tools\train_supervisor.py`"", '--run', "`"$run`"", '--minutes', '150', '--previous', "`"$repo\artifacts\runs\bc-v6\export`"")
$s = Start-Process -FilePath $py -ArgumentList $sup -WorkingDirectory $repo -WindowStyle Hidden -PassThru `
  -RedirectStandardOutput "$logs\top12k_long_supervisor.out" -RedirectStandardError "$logs\top12k_long_supervisor.err"
"train_pid=$($t.Id) supervisor_pid=$($s.Id) started=$(Get-Date -Format s)" | Tee-Object -FilePath "$logs\top12k_long_pids.txt"
