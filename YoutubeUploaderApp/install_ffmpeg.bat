@echo off
echo ========================================
echo Instalacja FFmpeg przez Chocolatey
echo ========================================
echo.

echo Krok 1: Sprawdzam czy Chocolatey jest zainstalowany...
choco --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Chocolatey jest juz zainstalowany
    goto install_ffmpeg
)

echo [INFO] Chocolatey nie jest zainstalowany. Instaluje...
echo.
echo UWAGA: Wymagane uprawnienia Administratora!
pause

powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"

echo.
echo [INFO] Chocolatey zainstalowany. Odswiezam srodowisko...
call refreshenv

:install_ffmpeg
echo.
echo Krok 2: Instalacja FFmpeg...
choco install ffmpeg -y

echo.
echo ========================================
echo Instalacja zakonczona!
echo ========================================
echo.
echo Sprawdzam wersje FFmpeg...
ffmpeg -version

echo.
echo Nacisnij dowolny klawisz aby zamknac...
pause >nul
