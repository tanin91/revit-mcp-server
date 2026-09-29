@echo off
setlocal
title Honda Sakura MCP Connection Test
echo Testing pyRevit Routes...
powershell -NoProfile -Command "try { $r=Invoke-RestMethod -Uri 'http://localhost:48884/revit_mcp/status/' -TimeoutSec 5; $r | ConvertTo-Json -Depth 4 } catch { Write-Host 'FAIL: Revit Routes not reachable. Open Revit and enable pyRevit Routes.' -ForegroundColor Red }"
echo.
echo Testing Honda QC route...
powershell -NoProfile -Command "try { $r=Invoke-RestMethod -Uri 'http://localhost:48884/revit_mcp/honda_qc_summary/' -TimeoutSec 15; $r | ConvertTo-Json -Depth 6 } catch { Write-Host 'FAIL: Honda QC route not reachable. Restart Revit after installing latest repo.' -ForegroundColor Red }"
echo.
pause
