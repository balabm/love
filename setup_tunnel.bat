@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo =========================================
echo  LOVE Cloudflare Named Tunnel Setup
echo =========================================
echo.

set "CF=C:\Program Files (x86)\cloudflared\cloudflared.exe"
if not exist "%CF%" (
    set "CF=C:\Program Files\Cloudflare\cloudflared.exe"
)
if not exist "%CF%" (
    echo [ERROR] cloudflared not found.
    echo Install: winget install Cloudflare.cloudflared
    exit /b 1
)

echo [CHECK] Verifying Cloudflare login...
"%CF%" tunnel list >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] You are NOT logged in to Cloudflare.
    echo.
    echo Step 1: Run this in PowerShell AS ADMIN:
    echo   ^& "%CF%" tunnel login
    echo.
    echo Step 2: Click through the browser auth
    echo Step 3: Run this script again
    exit /b 1
)

echo [OK] Logged in.
echo.

echo [1/4] Checking for existing tunnel 'love-bridge'...
set "TUNNEL_ID="
for /f "tokens=*" %%a in ('"%CF%" tunnel list --output json 2^>nul') do (
    echo %%a | findstr /C:"love-bridge" >nul && (
        for /f "tokens=2 delims=:" %%b in ("%%a") do (
            echo %%b | findstr /C:"id" >nul && (
                for /f "tokens=2 delims=\"" %%c in ("%%b") do set TUNNEL_ID=%%c
            )
        )
    )
)

if not defined TUNNEL_ID (
    echo [2/4] Creating new tunnel 'love-bridge'...
    for /f "tokens=*" %%a in ('"%CF%" tunnel create love-bridge 2^>^&1') do (
        echo %%a
        echo %%a | findstr /C:"Created tunnel" >nul && (
            for /f "tokens=4 delims= " %%b in ("%%a") do set TUNNEL_ID=%%b
        )
    )
) else (
    echo [2/4] Found existing tunnel: %TUNNEL_ID%
)

if not defined TUNNEL_ID (
    echo.
    echo [ERROR] Could not create or find tunnel.
    echo Run manually: "%CF%" tunnel create love-bridge
    exit /b 1
)

echo.
echo [3/4] Tunnel ID: %TUNNEL_ID%
set "CREDS=%USERPROFILE%\.cloudflared\%TUNNEL_ID%.json"
if not exist "%CREDS%" (
    echo [WARN] Credentials file not at expected path. cloudflared may use default location.
)

echo [4/4] Updating LOVE .env...
set "ENVFILE=%~dp0.env"
set "PERM_URL=https://%TUNNEL_ID%.cfargotunnel.com"

if exist "%ENVFILE%" (
    powershell -Command "$envPath='%ENVFILE%'; $lines=Get-Content $envPath; $found=$false; for($i=0;$i -lt $lines.Count;$i++){if($lines[$i] -match '^CLOUDFLARE_TUNNEL_NAME='){$lines[$i]='CLOUDFLARE_TUNNEL_NAME=love-bridge';$found=$true} if($lines[$i] -match '^CLOUDFLARE_TUNNEL_URL='){$lines[$i]='CLOUDFLARE_TUNNEL_URL=%PERM_URL%'}} if(-not $found){$lines+='CLOUDFLARE_TUNNEL_NAME=love-bridge'; $lines+='CLOUDFLARE_TUNNEL_URL=%PERM_URL%'} Set-Content $envPath ($lines -join \"`n\") -NoNewline"
) else (
    (
        echo CLOUDFLARE_TUNNEL_NAME=love-bridge
        echo CLOUDFLARE_TUNNEL_URL=%PERM_URL%
    ) > "%ENVFILE%"
)

echo.
echo =========================================
echo  SETUP COMPLETE
echo =========================================
echo.
echo Permanent URL: %PERM_URL%
echo Webhook:       %PERM_URL%/device/webhook
echo.
echo Next steps:
echo   1. Restart LOVE (Ctrl+C, then python api/main.py)
echo   2. Update Tasker Server:Port to: %TUNNEL_ID%.cfargotunnel.com
echo   3. Path: /device/webhook
echo   4. Done — this URL NEVER changes, even if LOVE restarts
echo.
pause
