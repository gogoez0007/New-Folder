Set shell = CreateObject("WScript.Shell")
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""d:\New folder\scripts\check_auth_notify.ps1"""
exitCode = shell.Run(cmd, 0, True)
WScript.Quit exitCode

