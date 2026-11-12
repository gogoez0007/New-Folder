$ErrorActionPreference = "Continue"

$ProjectRoot = "d:\New folder"
Set-Location $ProjectRoot

# Force UTF-8 encoding so headless/Task Scheduler stdout never fails on emoji titles
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$LogDir = Join-Path $ProjectRoot "workspace\logs"
$RefDir = Join-Path $ProjectRoot "workspace\references"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

# Prune logs and old downloaded reference videos older than 14 days cleanly
Get-ChildItem -Path $LogDir -Filter "auto_*.log" -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-14) } |
    Remove-Item -Force -ErrorAction SilentlyContinue
if (Test-Path $RefDir) {
    Get-ChildItem -Path $RefDir -Filter "*.mp4" -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-14) } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogDir "auto_$Timestamp.log"
$ErrFile = Join-Path $LogDir "auto_$Timestamp.err.log"

$PythonExe = "C:\Users\IT\AppData\Local\Programs\Python\Python314\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = (Get-Command python -ErrorAction Stop).Source
}

"=== ShortsCloner Auto-Generate & US Upload Start: $(Get-Date -Format o) (PID=$PID, User=$env:USERNAME) ===" | Out-File -FilePath $LogFile -Encoding utf8

# Launch Python unbuffered with direct file redirection so logs stream immediately without PS 5.1 pipeline deadlock/buffering
$MainPy = Join-Path $ProjectRoot "main.py"
$Proc = Start-Process -FilePath $PythonExe `
    -ArgumentList "`"-u`" `"$MainPy`" --auto-scout --count 2 --language en --auto-upload --privacy scheduled --non-interactive --cleanup-workspace" `
    -WorkingDirectory $ProjectRoot `
    -NoNewWindow `
    -Wait `
    -PassThru `
    -RedirectStandardOutput $LogFile `
    -RedirectStandardError $ErrFile

$ExitCode = $Proc.ExitCode
if (Test-Path $ErrFile) {
    $ErrText = Get-Content -LiteralPath $ErrFile -Raw -ErrorAction SilentlyContinue
    if ($ErrText) {
        Add-Content -LiteralPath $LogFile -Value "`n--- STDERR ---`n$ErrText" -Encoding utf8
    }
    Remove-Item -LiteralPath $ErrFile -Force -ErrorAction SilentlyContinue
}
Add-Content -LiteralPath $LogFile -Value "`n=== Completed (exit=$ExitCode) at $(Get-Date -Format o) ===" -Encoding utf8

# Immediately trigger persistent auth reminder if pipeline failed due to expired/missing OAuth
if ($ExitCode -ne 0) {
    $AuthNotifyScript = Join-Path $ProjectRoot "scripts\check_auth_notify.ps1"
    if (Test-Path $AuthNotifyScript) {
        & $AuthNotifyScript | Out-Null
    }
} elseif (Test-Path "D:\Tools & Doc\Automate Video Gen") {
    # Keep mirror archive updated with permanently saved clips and history
    $SavedSrc = Join-Path $ProjectRoot "output\saved_clips"
    $SavedDst = "D:\Tools & Doc\Automate Video Gen\output\saved_clips"
    if (Test-Path $SavedSrc) {
        robocopy $SavedSrc $SavedDst /E /XO /NFL /NDL /NP | Out-Null
    }
    robocopy (Join-Path $ProjectRoot "output") "D:\Tools & Doc\Automate Video Gen\output" history_log.json youtube_upload_pack.md /NFL /NDL /NP | Out-Null
    robocopy (Join-Path $ProjectRoot "workspace") "D:\Tools & Doc\Automate Video Gen\workspace" history_log.json /NFL /NDL /NP | Out-Null
}
exit $ExitCode
