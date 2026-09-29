# Cài Honda Sakura Revit MCP

## Kiến trúc

```
TFAS IFC / PDF / DXF
        |
        v
HondaSakura Python / pyRevit Core
        |
        v
Native Revit Model
        |
        v
Revit MCP READ-ONLY QC
```

**Python vẫn là core sản xuất. MCP không tự ý sửa model Honda Sakura.**

## Cài một lần

1. Cài pyRevit và kiểm tra tab pyRevit xuất hiện trong Revit.
2. Tải ZIP repo này và giải nén.
3. Double-click `INSTALL_MCP_HONDA.bat`.
4. Đóng toàn bộ Revit.
5. Mở Revit > pyRevit > Settings > Routes > bật **Routes Server**.
6. Mở project cần QC.
7. Double-click shortcut `START_HONDA_REVIT_MCP.bat` trên Desktop.
8. Chạy `TEST_MCP_HONDA.bat`.

## Kiểm tra thủ công

Mở trình duyệt:

- Revit Routes: `http://localhost:48884/revit_mcp/status/`
- MCP HTTP: `http://localhost:8000/mcp`

## Tool Honda QC

- `honda_qc_summary` — tổng quan Pipe/Duct/Terminal/Equipment.
- `honda_qc_network(domain="pipe")` — open connector Pipe + ElementId.
- `honda_qc_network(domain="duct")` — open connector Duct + ElementId.
- `honda_qc_equipment` — thiếu/trùng thông tin thiết bị.
- `honda_qc_family_priority` — LINEUP → TTE → RUG → 仮スペース.
- `honda_qc_source_compare` — so source IFC/PDF/DXF/CSV cache với Revit và trả ElementId lỗi.

## Luồng QC source

1. Trong HondaSakura, chạy `05D Equipment Auto Fill` với IFC/PDF/DXF/CSV.
2. 05D lưu source cache.
3. Gọi MCP `honda_qc_source_compare`.
4. MCP trả:
   - Revit ElementId không match source.
   - ElementId có mismatch 型式 / 電源 / 消費電力 / 風量.
   - source record chưa có trong Revit.
5. Sửa bằng Python/pyRevit core, không sửa tự động qua MCP.

## Client MCP

### ChatGPT/Client hỗ trợ HTTP MCP
Kết nối tới:

`http://localhost:8000/mcp`

### Client dùng stdio
Command:

`uv run main.py`

Working directory:

`%APPDATA%\pyRevit\Extensions\mcp-server-for-revit-python.extension`

## Nếu không kết nối

- Revit phải đang mở project.
- pyRevit Routes phải bật.
- Port Revit Routes: 48884.
- Port MCP: 8000.
- Sau khi update `startup.py` hoặc `revit_mcp/`, phải restart Revit.
