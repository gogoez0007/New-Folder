param(
    [string]$TaskName = "ShortsCloner_Auth_Watchdog",
    [int]$IntervalMinutes = 15
)

$ErrorActionPreference = "Stop"
$VbsPath = "d:\New folder\scripts\launch_auth_watchdog.vbs"

$Action = New-ScheduledTaskAction `
    -Execute "wscript.exe" `
    -Argument "//B //Nologo `"$VbsPath`"" `
    -WorkingDirectory "d:\New folder"

$TriggerLogon = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
# Start 1 minute from now and repeat indefinitely every N minutes
$TriggerRepeat = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -Hidden `
    -ExecutionTimeLimit (New-TimeSpan -Hours 12)

$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger @($TriggerLogon, $TriggerRepeat) `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Checks YouTube OAuth health every $IntervalMinutes minutes & at logon; persistently reminds until auth_youtube.bat is executed." `
    -Force | Out-Null

$Task = Get-ScheduledTask -TaskName $TaskName
$Info = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Host ("TaskName: " + $Task.TaskName + " | State: " + $Task.State + " | NextRunTime: " + $Info.NextRunTime)

