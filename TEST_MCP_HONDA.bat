@echo off
setlocal EnableExtensions
title Honda Sakura MCP QC Test

set "SNAP=%APPDATA%\pyRevit\Extensions\HondaSakura.extension\data\mcp_qc_snapshot.json"

echo ==========================================
echo   HONDA SAKURA - MCP QC TEST
echo ==========================================
echo.
echo NOTE: pyRevit Routes are NOT used in this version.
echo.

if not exist "%SNAP%" (
  echo FAIL: QC snapshot not found.
  echo.
  echo Open Revit and run:
  echo   Honda Sakura ^> QC ^> 99 MCP QC Snapshot
  echo.
  echo Expected file:
  echo   %SNAP%
  echo.
  pause
  exit /b 1
)

echo [OK] Snapshot found:
echo %SNAP%
echo.

powershell -NoProfile -Command "try { $p='%SNAP%'; $j=Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json; Write-Host ('[OK] Project: ' + $j.project) -ForegroundColor Green; Write-Host ('[OK] Pipes: ' + $j.counts.pipes); Write-Host ('[OK] Ducts: ' + $j.counts.ducts); Write-Host ('[OK] Equipment: ' + $j.counts.equipment) } catch { Write-Host ('FAIL: Snapshot JSON invalid: ' + $_.Exception.Message) -ForegroundColor Red; exit 2 }"
if errorlevel 1 (
  pause
  exit /b 2
)

echo.
echo Snapshot QC is ready.
echo Next: run START_MCP_HONDA.bat
echo MCP endpoint: http://localhost:8000/mcp
echo.
pause
