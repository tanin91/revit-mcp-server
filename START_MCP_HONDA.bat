@echo off
setlocal
title Honda Sakura Revit MCP
set "DIR=%APPDATA%\pyRevit\Extensions\mcp-server-for-revit-python.extension"
if not exist "%DIR%\main.py" (
  echo MCP is not installed.
  echo Run INSTALL_MCP_HONDA.bat first.
  pause
  exit /b 1
)
cd /d "%DIR%"
set REVIT_HOST=localhost
uv run main.py --combined
pause
