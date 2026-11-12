param(
    [switch]$ForceNotify,
    [switch]$NoDialog,
    [switch]$LogOnly
)

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ProjectRoot = "d:\New folder"
$AuthBat = Join-Path $ProjectRoot "scripts\auth_youtube.bat"
$RootAuthBat = Join-Path $ProjectRoot "auth_youtube.bat"
$AuthStateFile = Join-Path $ProjectRoot "credentials\auth_state.json"
$DesktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "Login Auth YouTube.lnk"
$LogDir = Join-Path $ProjectRoot "workspace\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir "auth_watchdog.log"

$PythonExe = "C:\Users\IT\AppData\Local\Programs\Python\Python314\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = (Get-Command python -ErrorAction Stop).Source
}

$MainPy = Join-Path $ProjectRoot "main.py"
$RawOut = & $PythonExe -u $MainPy --check-auth --json 2>&1
$CheckExit = $LASTEXITCODE
$JsonLine = ($RawOut | Where-Object { $_ -is [string] -and $_.Trim().StartsWith("{") } | Select-Object -Last 1)

$Status = $null
if ($JsonLine) {
    try {
        $Status = $JsonLine | ConvertFrom-Json
    } catch {
        $Status = $null
    }
}

$NeedsAuth = ($CheckExit -ne 0)
if ($null -ne $Status -and $null -ne $Status.needs_auth) {
    $NeedsAuth = [bool]$Status.needs_auth
}

$Reason = if ($null -ne $Status -and $Status.reason) { [string]$Status.reason } else { "expired_or_missing" }
$Message = if ($null -ne $Status -and $Status.message) { [string]$Status.message } else { "Token YouTube OAuth tidak aktif. Jalankan auth_youtube.bat untuk login ulang." }

if (-not $NeedsAuth -and -not $ForceNotify) {
    exit 0
}

if ($ForceNotify -and -not $NeedsAuth) {
    $Reason = "test_reminder"
    $Message = "Simulasi Notif: Saat token YouTube OAuth benar-benar expired/dicabut, notif ini muncul terus tiap 15 menit sampai auth_youtube.bat dijalankan."
}

$Stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -LiteralPath $LogFile -Value "[$Stamp] NOTIFY needs_auth=$NeedsAuth reason=$Reason msg=$Message" -Encoding utf8

if ($LogOnly) {
    exit 2
}

$Title = if ($Reason -eq "test_reminder") {
    "Tes Notif Watchdog Auth YouTube"
} else {
    "Token YouTube Auth Expired! Wajib Login Ulang"
}

$FileTargetDisplay = if (Test-Path $RootAuthBat) { $RootAuthBat } else { $AuthBat }
$ToastBody1 = $Message
$ToastBody2 = "File: $FileTargetDisplay (atau shortcut Desktop: Login Auth YouTube)"

# 1. Native Windows 10/11 Reminder Toast (stays pinned until dismissed/acted on + reminder sound)
try {
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

    $EscTitle = [System.Security.SecurityElement]::Escape($Title)
    $EscB1 = [System.Security.SecurityElement]::Escape($ToastBody1)
    $EscB2 = [System.Security.SecurityElement]::Escape($ToastBody2)
    $ScriptsUri = "file:///d:/New%20folder/scripts"
    $RootUri = "file:///d:/New%20folder"

    $ToastXmlStr = @"
<toast scenario="reminder">
  <visual>
    <binding template="ToastGeneric">
      <text>$EscTitle</text>
      <text>$EscB1</text>
      <text>$EscB2</text>
    </binding>
  </visual>
  <audio src="ms-winsoundevent:Notification.Reminder"/>
  <actions>
    <action content="Buka Folder File Auth" activationType="protocol" arguments="$RootUri"/>
    <action content="Buka Folder scripts" activationType="protocol" arguments="$ScriptsUri"/>
  </actions>
</toast>
"@
    $XmlDoc = New-Object Windows.Data.Xml.Dom.XmlDocument
    $XmlDoc.LoadXml($ToastXmlStr)
    $Toast = New-Object Windows.UI.Notifications.ToastNotification $XmlDoc
    $AppId = "{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe"
    $Notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($AppId)
    $Notifier.Show($Toast)
} catch {
    Add-Content -LiteralPath $LogFile -Value "[$Stamp] ToastWarning: $_" -Encoding utf8
}

if ($NoDialog) {
    exit 2
}

# 2. Persistent non-focus-stealing GUI Alert Card (single-instance via Mutex)
$CreatedNew = $false
$Mutex = New-Object System.Threading.Mutex($false, "Local\ShortsClonerAuthReminderPopup", [ref]$CreatedNew)
if (-not $CreatedNew) {
    $Mutex.Dispose()
    exit 2
}

try {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    [System.Windows.Forms.Application]::EnableVisualStyles()

    if (-not ("ShortsClonerAlertForm" -as [type])) {
        Add-Type -ReferencedAssemblies @("System.Windows.Forms.dll", "System.Drawing.dll") -TypeDefinition @"
using System;
using System.Windows.Forms;

public class ShortsClonerAlertForm : Form {
    protected override bool ShowWithoutActivation {
        get { return true; }
    }
    protected override CreateParams CreateParams {
        get {
            CreateParams cp = base.CreateParams;
            cp.ExStyle |= 0x08000000; // WS_EX_NOACTIVATE (never steals keyboard focus)
            cp.ExStyle |= 0x00000008; // WS_EX_TOPMOST
            return cp;
        }
    }
}
"@
    }

    $PopupStartUtc = (Get-Date).ToUniversalTime()

    $Form = New-Object ShortsClonerAlertForm
    $Form.Text = "Shorts Cloner - Pengingat Auth YouTube"
    $Form.Size = New-Object System.Drawing.Size(480, 290)
    $Form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
    $Form.MaximizeBox = $false
    $Form.MinimizeBox = $false
    $Form.TopMost = $true
    $Form.BackColor = [System.Drawing.Color]::FromArgb(24, 24, 28)
    $Form.ForeColor = [System.Drawing.Color]::White
    $Form.StartPosition = [System.Windows.Forms.FormStartPosition]::Manual

    $WorkArea = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
    $Form.Location = New-Object System.Drawing.Point(($WorkArea.Right - $Form.Width - 18), ($WorkArea.Bottom - $Form.Height - 18))

    $LblHeader = New-Object System.Windows.Forms.Label
    $LblHeader.Text = $Title
    $LblHeader.Font = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
    $LblHeader.ForeColor = [System.Drawing.Color]::FromArgb(255, 193, 7)
    $LblHeader.Location = New-Object System.Drawing.Point(18, 16)
    $LblHeader.Size = New-Object System.Drawing.Size(436, 28)
    $Form.Controls.Add($LblHeader)

    $LblBody = New-Object System.Windows.Forms.Label
    $LblBody.Text = "$Message`r`n`r`nNotif ini akan muncul terus setiap 15 menit sampai auth berhasil dijalankan."
    $LblBody.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)
    $LblBody.ForeColor = [System.Drawing.Color]::FromArgb(230, 230, 235)
    $LblBody.Location = New-Object System.Drawing.Point(18, 50)
    $LblBody.Size = New-Object System.Drawing.Size(436, 68)
    $Form.Controls.Add($LblBody)

    $LblFile = New-Object System.Windows.Forms.Label
    $LblFile.Text = "File Auth:"
    $LblFile.Font = New-Object System.Drawing.Font("Segoe UI", 8.5, [System.Drawing.FontStyle]::Bold)
    $LblFile.ForeColor = [System.Drawing.Color]::FromArgb(160, 175, 195)
    $LblFile.Location = New-Object System.Drawing.Point(18, 122)
    $LblFile.Size = New-Object System.Drawing.Size(70, 20)
    $Form.Controls.Add($LblFile)

    $TxtPath = New-Object System.Windows.Forms.TextBox
    $TxtPath.Text = $AuthBat
    $TxtPath.ReadOnly = $true
    $TxtPath.BackColor = [System.Drawing.Color]::FromArgb(36, 36, 42)
    $TxtPath.ForeColor = [System.Drawing.Color]::FromArgb(120, 220, 160)
    $TxtPath.BorderStyle = [System.Windows.Forms.BorderStyle]::FixedSingle
    $TxtPath.Font = New-Object System.Drawing.Font("Consolas", 9)
    $TxtPath.Location = New-Object System.Drawing.Point(90, 120)
    $TxtPath.Size = New-Object System.Drawing.Size(362, 22)
    $Form.Controls.Add($TxtPath)

    $LblDesktop = New-Object System.Windows.Forms.Label
    $LblDesktop.Text = if (Test-Path $DesktopShortcut) { "Shortcut Desktop: Login Auth YouTube" } else { "Shortcut Root: $RootAuthBat" }
    $LblDesktop.Font = New-Object System.Drawing.Font("Segoe UI", 8.5)
    $LblDesktop.ForeColor = [System.Drawing.Color]::FromArgb(150, 155, 165)
    $LblDesktop.Location = New-Object System.Drawing.Point(18, 148)
    $LblDesktop.Size = New-Object System.Drawing.Size(436, 20)
    $Form.Controls.Add($LblDesktop)

    $BtnRun = New-Object System.Windows.Forms.Button
    $BtnRun.Text = "Jalankan auth_youtube.bat Sekarang"
    $BtnRun.Font = New-Object System.Drawing.Font("Segoe UI", 9.5, [System.Drawing.FontStyle]::Bold)
    $BtnRun.BackColor = [System.Drawing.Color]::FromArgb(34, 139, 84)
    $BtnRun.ForeColor = [System.Drawing.Color]::White
    $BtnRun.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
    $BtnRun.Location = New-Object System.Drawing.Point(18, 180)
    $BtnRun.Size = New-Object System.Drawing.Size(272, 36)
    $BtnRun.Add_Click({
        Start-Process -FilePath $AuthBat -WorkingDirectory $ProjectRoot
        $Form.Close()
    })
    $Form.Controls.Add($BtnRun)

    $BtnFolder = New-Object System.Windows.Forms.Button
    $BtnFolder.Text = "Buka Folder File"
    $BtnFolder.Font = New-Object System.Drawing.Font("Segoe UI", 9)
    $BtnFolder.BackColor = [System.Drawing.Color]::FromArgb(55, 58, 68)
    $BtnFolder.ForeColor = [System.Drawing.Color]::White
    $BtnFolder.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
    $BtnFolder.Location = New-Object System.Drawing.Point(298, 180)
    $BtnFolder.Size = New-Object System.Drawing.Size(154, 36)
    $BtnFolder.Add_Click({
        Start-Process -FilePath "explorer.exe" -ArgumentList "/select,`"$AuthBat`""
    })
    $Form.Controls.Add($BtnFolder)

    $BtnLater = New-Object System.Windows.Forms.Button
    $BtnLater.Text = "Tutup (Ingatkan 15 Menit Lagi)"
    $BtnLater.Font = New-Object System.Drawing.Font("Segoe UI", 8.5)
    $BtnLater.BackColor = [System.Drawing.Color]::FromArgb(40, 40, 46)
    $BtnLater.ForeColor = [System.Drawing.Color]::FromArgb(200, 200, 205)
    $BtnLater.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
    $BtnLater.Location = New-Object System.Drawing.Point(18, 222)
    $BtnLater.Size = New-Object System.Drawing.Size(434, 28)
    $BtnLater.Add_Click({ $Form.Close() })
    $Form.Controls.Add($BtnLater)

    # Auto-dismiss cleanly if user renews auth manually while popup is open
    $Timer = New-Object System.Windows.Forms.Timer
    $Timer.Interval = 5000
    $Timer.Add_Tick({
        if (Test-Path $AuthStateFile) {
            try {
                $mt = (Get-Item -LiteralPath $AuthStateFile).LastWriteTimeUtc
                if ($mt -gt $PopupStartUtc) {
                    $Timer.Stop()
                    $Form.Close()
                }
            } catch {}
        }
    })
    $Timer.Start()
    $Form.Add_FormClosed({
        try {
            $Timer.Stop()
            $Timer.Dispose()
        } catch {}
    })

    [System.Windows.Forms.Application]::Run($Form)
} finally {
    try { $Mutex.ReleaseMutex() } catch {}
    $Mutex.Dispose()
}
exit 2
