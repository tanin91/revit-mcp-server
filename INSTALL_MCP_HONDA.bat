@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Honda Sakura Revit MCP Installer

set "SRC=%~dp0"
set "EXTROOT=%APPDATA%\pyRevit\Extensions"
set "EXTDST=%EXTROOT%\mcp-server-for-revit-python.extension"
set "SERVER=%LOCALAPPDATA%\HondaSakuraRevitMCP"
set "LOG=%TEMP%\honda_mcp_install.log"

echo ==========================================
echo   HONDA SAKURA - REVIT MCP INSTALLER
echo ==========================================
echo.
echo Python/pyRevit = production core
echo MCP = READ-ONLY QC
echo.

tasklist /FI "IMAGENAME eq Revit.exe" | find /I "Revit.exe" >nul
if not errorlevel 1 (
    echo ERROR: Revit is running.
    echo Please CLOSE ALL Revit windows first, then run this installer again.
    echo.
    pause
    exit /b 2
)

where uv >nul 2>&1
if errorlevel 1 (
    echo [1/5] uv not found. Installing uv...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.cargo\bin;%PATH%"
) else (
    echo [1/5] uv OK
)

where uv >nul 2>&1
if errorlevel 1 (
    echo ERROR: uv installation failed.
    echo Install manually: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 3
)

echo [2/5] Installing pyRevit route extension...
if not exist "%EXTROOT%" mkdir "%EXTROOT%"
if not exist "%EXTDST%" mkdir "%EXTDST%"

copy /Y "%SRC%startup.py" "%EXTDST%\startup.py" >nul
if errorlevel 1 goto :copyfail

copy /Y "%SRC%extension.json" "%EXTDST%\extension.json" >nul
if errorlevel 1 goto :copyfail

if exist "%EXTDST%\revit_mcp" rmdir /S /Q "%EXTDST%\revit_mcp"
xcopy "%SRC%revit_mcp" "%EXTDST%\revit_mcp\" /E /I /Y >nul
if errorlevel 1 goto :copyfail

echo [3/5] Installing local MCP server...
if not exist "%SERVER%" mkdir "%SERVER%"
copy /Y "%SRC%main_honda_qc.py" "%SERVER%\main_honda_qc.py" >nul
copy /Y "%SRC%pyproject.toml" "%SERVER%\pyproject.toml" >nul
copy /Y "%SRC%uv.lock" "%SERVER%\uv.lock" >nul 2>nul
copy /Y "%SRC%requirements.txt" "%SERVER%\requirements.txt" >nul 2>nul
if exist "%SERVER%\tools" rmdir /S /Q "%SERVER%\tools"
xcopy "%SRC%tools" "%SERVER%\tools\" /E /I /Y >nul
if errorlevel 1 goto :copyfail

echo [4/5] Installing Python dependencies...
pushd "%SERVER%"
uv sync
if errorlevel 1 (
    popd
    echo ERROR: uv sync failed.
    pause
    exit /b 4
)
popd

echo [5/5] Creating launchers...
set "LAUNCH=%USERPROFILE%\Desktop\START_HONDA_REVIT_MCP.bat"
(
echo @echo off
echo title Honda Sakura Revit MCP
echo cd /d "%SERVER%"
echo set REVIT_HOST=localhost
echo uv run main_honda_qc.py --combined
echo pause
) > "%LAUNCH%"

set "TESTER=%USERPROFILE%\Desktop\TEST_HONDA_REVIT_MCP.bat"
(
echo @echo off
echo title Honda Sakura MCP Test
echo echo Testing Revit Routes...
echo powershell -NoProfile -Command "try { $r=Invoke-RestMethod -Uri 'http://localhost:48884/revit_mcp/status/' -TimeoutSec 5; $r ^| ConvertTo-Json -Depth 4 } catch { Write-Host 'FAIL: Revit Routes not reachable' -ForegroundColor Red }"
echo echo.
echo echo Testing Honda QC...
echo powershell -NoProfile -Command "try { $r=Invoke-RestMethod -Uri 'http://localhost:48884/revit_mcp/honda_qc_summary/' -TimeoutSec 15; $r ^| ConvertTo-Json -Depth 6 } catch { Write-Host 'FAIL: Honda QC route not reachable' -ForegroundColor Red }"
echo pause
) > "%TESTER%"

echo.
echo ==========================================
echo INSTALL COMPLETE
echo ==========================================
echo.
echo 1. Open Revit.
echo 2. pyRevit ^> Settings ^> Routes ^> Enable Routes Server.
echo 3. Open project.
echo 4. Run START_HONDA_REVIT_MCP.bat on Desktop.
echo 5. Run TEST_HONDA_REVIT_MCP.bat.
echo.
echo Revit Routes: http://localhost:48884/revit_mcp/status/
echo MCP HTTP:     http://localhost:8000/mcp
echo.
pause
exit /b 0

:copyfail
echo.
echo ERROR: copy failed.
echo Source: "%SRC%"
echo Extension: "%EXTDST%"
echo Server: "%SERVER%"
echo.
echo Common cause: Revit/pyRevit still open or antivirus blocks AppData copy.
echo Close Revit and retry.
echo.
pause
exit /b 5
