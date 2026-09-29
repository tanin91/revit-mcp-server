@echo off
setlocal EnableExtensions
title Honda Sakura MCP QC Installer

set "SRC=%~dp0"
set "SERVER=%LOCALAPPDATA%\HondaSakuraRevitMCP"

echo ==========================================
echo   HONDA SAKURA - MCP QC INSTALLER
echo ==========================================
echo.
echo pyRevit/Python = CORE build 3D
echo MCP = READ-ONLY QC from JSON snapshot
echo NO pyRevit Routes required.
echo NO Revit startup extension installed.
echo.

where uv >nul 2>&1
if errorlevel 1 (
    echo [1/4] uv not found. Installing uv...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.cargo\bin;%PATH%"
) else (
    echo [1/4] uv OK
)

where uv >nul 2>&1
if errorlevel 1 (
    echo ERROR: uv installation failed.
    pause
    exit /b 1
)

echo [2/4] Installing standalone MCP QC server...
if not exist "%SERVER%" mkdir "%SERVER%"
copy /Y "%SRC%main_honda_qc.py" "%SERVER%\main_honda_qc.py" >nul
copy /Y "%SRC%pyproject.toml" "%SERVER%\pyproject.toml" >nul
if exist "%SRC%uv.lock" copy /Y "%SRC%uv.lock" "%SERVER%\uv.lock" >nul

echo [3/4] Installing dependencies...
pushd "%SERVER%"
uv sync
if errorlevel 1 (
    popd
    echo ERROR: uv sync failed.
    pause
    exit /b 2
)
popd

echo [4/4] Creating desktop launchers...
set "LAUNCH=%USERPROFILE%\Desktop\START_HONDA_MCP_QC.bat"
(
echo @echo off
echo title Honda Sakura MCP QC
echo cd /d "%SERVER%"
echo uv run main_honda_qc.py --combined
echo pause
) > "%LAUNCH%"

set "TESTER=%USERPROFILE%\Desktop\TEST_HONDA_MCP_QC.bat"
(
echo @echo off
echo title Honda Sakura MCP QC Test
echo set "SNAP=%%APPDATA%%\pyRevit\Extensions\HondaSakura.extension\data\mcp_qc_snapshot.json"
echo if not exist "%%SNAP%%" ^(
echo   echo FAIL: snapshot not found.
echo   echo Open Revit and run: Honda Sakura ^> QC ^> 99 MCP QC Snapshot
echo   pause
echo   exit /b 1
echo ^)
echo echo Snapshot found:
echo echo %%SNAP%%
echo echo.
echo echo Starting HTTP test requires START_HONDA_MCP_QC.bat to be running.
echo powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8000/mcp' -Method Get -TimeoutSec 5 ^| Out-Null; Write-Host 'MCP port 8000 reachable' -ForegroundColor Green } catch { Write-Host 'If START_HONDA_MCP_QC is running, this client may require POST/streamable HTTP. Server install itself is OK if snapshot exists.' -ForegroundColor Yellow }"
echo pause
) > "%TESTER%"

echo.
echo INSTALL COMPLETE
echo.
echo IMPORTANT:
echo 1. In pyRevit Settings, Routes can stay OFF.
echo 2. Open Revit normally.
echo 3. Run Honda Sakura ^> QC ^> 99 MCP QC Snapshot.
echo 4. Start Desktop: START_HONDA_MCP_QC.bat
echo.
echo MCP endpoint: http://localhost:8000/mcp
echo.
pause
