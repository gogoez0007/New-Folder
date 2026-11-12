@echo off
cd /d "d:\New folder"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
echo ============================================================
echo   YouTube OAuth 2.0 One-Time Login ^(tofikgogo@gmail.com^)
echo ============================================================
echo.
echo Browser akan terbuka ke halaman login Google OAuth.
echo Jika terbuka di profil Chrome yang salah, copy URL `OAUTH_AUTH_URL:`
echo di bawah ini lalu buka di Chrome profil tofikgogo@gmail.com.
echo.
"C:\Users\IT\AppData\Local\Programs\Python\Python314\python.exe" -u main.py --auth-only
if errorlevel 1 (
    echo.
    echo [X] OAuth gagal atau dibatalkan. Silakan coba ulang.
    pause
    exit /b 1
)
echo.
echo [+] Token OAuth tersimpan! Menjadwalkan klip yang sudah ada ke jam Prime Time AS...
"C:\Users\IT\AppData\Local\Programs\Python\Python314\python.exe" -u main.py --upload-only --privacy scheduled
echo.
echo [+] SELESAI! Otomasi harian ShortsCloner_US_AutoGenUpload ^(15:00 WIB^) siap autopilot!
pause
