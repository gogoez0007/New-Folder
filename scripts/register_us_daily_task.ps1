param(
    [string]$TaskName = "ShortsCloner_US_AutoGenUpload",
    [string[]]$RunTimesLocalWIB = @("10:00", "15:00")
)

$ErrorActionPreference = "Stop"
$VbsPath = "d:\New folder\scripts\launch_hidden.vbs"

$Action = New-ScheduledTaskAction `
    -Execute "wscript.exe" `
    -Argument "//B //Nologo `"$VbsPath`"" `
    -WorkingDirectory "d:\New folder"

# 2 daily sessions x 2 Shorts = 4 Shorts/day filling all 4 US Prime Time windows (08:00, 12:30, 16:30, 20:00 ET)
$Triggers = @()
foreach ($t in $RunTimesLocalWIB) {
    $Triggers += New-ScheduledTaskTrigger -Daily -At $t
}

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -WakeToRun `
    -Hidden `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 10) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Triggers `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Autonomous background 4-videos/day US high-RPM YouTube Shorts pipeline (2 runs x 2 Shorts -> 08:00, 12:30, 16:30, 20:00 ET)." `
    -Force | Out-Null

$Task = Get-ScheduledTask -TaskName $TaskName
$Info = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Host ("TaskName: " + $Task.TaskName + " | State: " + $Task.State + " | NextRunTime: " + $Info.NextRunTime)
foreach ($tr in $Task.Triggers) {
    Write-Host ("Trigger Daily At: " + $tr.StartBoundary)
}
