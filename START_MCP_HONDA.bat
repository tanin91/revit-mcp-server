@echo off
setlocal EnableExtensions
title Honda Sakura Revit MCP

set "SERVER=%LOCALAPPDATA%\HondaSakuraRevitMCP"
set "LEGACY=%APPDATA%\pyRevit\Extensions\mcp-server-for-revit-python.extension"

rem Prefer the new split install location.
if exist "%SERVER%\main.py" goto :run_new

rem Backward compatibility with old installer.
if exist "%LEGACY%\main.py" goto :run_legacy

echo MCP server files are not installed yet.
echo.
echo I will run INSTALL_MCP_HONDA.bat now.
echo Please CLOSE ALL Revit windows before continuing.
echo.
if exist "%~dp0INSTALL_MCP_HONDA.bat" (
    call "%~dp0INSTALL_MCP_HONDA.bat"
) else (
    echo ERROR: INSTALL_MCP_HONDA.bat not found in this folder.
    echo Re-download the latest repo ZIP.
    pause
    exit /b 1
)

if exist "%SERVER%\main.py" goto :run_new
if exist "%LEGACY%\main.py" goto :run_legacy

echo.
echo INSTALL did not create the MCP server.
echo Please send a screenshot of the INSTALL_MCP_HONDA.bat window.
pause
exit /b 2

:run_new
cd /d "%SERVER%"
set REVIT_HOST=localhost
where uv >nul 2>&1
if errorlevel 1 (
    echo ERROR: uv not found. Re-run INSTALL_MCP_HONDA.bat.
    pause
    exit /b 3
)
echo Starting Honda Sakura Revit MCP from:
echo %SERVER%
echo.
uv run main.py --combined
pause
exit /b 0

:run_legacy
cd /d "%LEGACY%"
set REVIT_HOST=localhost
where uv >nul 2>&1
if errorlevel 1 (
    echo ERROR: uv not found. Re-run INSTALL_MCP_HONDA.bat.
    pause
    exit /b 3
)
echo Starting legacy Honda Sakura Revit MCP from:
echo %LEGACY%
echo.
uv run main.py --combined
pause
