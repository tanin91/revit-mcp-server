@echo off
setlocal EnableExtensions
title Honda Sakura Revit MCP Installer

set "SRC=%~dp0"
set "EXTROOT=%APPDATA%\pyRevit\Extensions"
set "DST=%EXTROOT%\mcp-server-for-revit-python.extension"

echo ==========================================
echo   HONDA SAKURA - REVIT MCP INSTALLER
echo ==========================================
echo.
echo Python/pyRevit remains the production core.
echo MCP is installed as READ-ONLY QC.
echo.

where uv >nul 2>&1
if errorlevel 1 (
    echo [1/4] uv not found. Installing uv...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.cargo\bin;%PATH%"
)

where uv >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: uv installation failed.
    echo Install manually from: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

echo [2/4] Copying pyRevit MCP extension...
if not exist "%EXTROOT%" mkdir "%EXTROOT%"
if not exist "%DST%" mkdir "%DST%"
robocopy "%SRC%" "%DST%" /E /NFL /NDL /NJH /NJS /NP /XD ".git" ".venv" "__pycache__" >nul
if errorlevel 8 (
    echo ERROR: copy failed.
    pause
    exit /b 1
)

echo [3/4] Installing MCP Python dependencies...
pushd "%DST%"
uv sync
if errorlevel 1 (
    popd
    echo ERROR: uv sync failed.
    pause
    exit /b 1
)
popd

echo [4/4] Creating desktop launcher...
set "LAUNCH=%USERPROFILE%\Desktop\START_HONDA_REVIT_MCP.bat"
(
echo @echo off
echo title Honda Sakura Revit MCP
echo cd /d "%DST%"
echo set REVIT_HOST=localhost
echo uv run main.py --combined
echo pause
) > "%LAUNCH%"

echo.
echo ==========================================
echo INSTALL COMPLETE
echo ==========================================
echo.
echo NEXT:
echo 1. Close ALL Revit windows.
echo 2. Open Revit.
echo 3. pyRevit ^> Settings ^> Routes ^> Enable Routes Server.
echo 4. Open your project.
echo 5. Double-click START_HONDA_REVIT_MCP.bat on Desktop.
echo.
echo Verify Revit Routes:
echo   http://localhost:48884/revit_mcp/status/
echo MCP HTTP endpoint:
echo   http://localhost:8000/mcp
echo.
pause
