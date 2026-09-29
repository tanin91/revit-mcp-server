# Honda Sakura — kiến trúc chốt

## Nguyên tắc

**pyRevit/Python = CORE sản xuất 3D nặng.**

Dùng HondaSakura extension hiện tại để:
- parse CADWe'll Tfas IFC
- dựng Pipe
- dựng Duct
- dựng Terminal / Box
- dựng Equipment
- valve/fitting
- map Family/Type/System
- ghi parameter
- Base Point alignment

**MCP = QC ONLY.**

MCP tuyệt đối không tạo Pipe/Duct/Family và không sửa model trong luồng Honda Sakura.

## Luồng chuẩn

```
TFAS IFC / PDF / DXF
        |
        v
HondaSakura pyRevit Python CORE
        |
        |  dựng model 3D thật
        v
      REVIT
        |
        |  chỉ đọc
        v
Honda Sakura MCP QC
        |
        +-- honda_qc_summary
        +-- honda_qc_network
        +-- honda_qc_equipment
        +-- honda_qc_family_priority
        +-- honda_qc_source_compare
```

## Quy tắc sửa lỗi

MCP phát hiện lỗi -> trả ElementId + nguyên nhân -> người dùng review ->
quay lại HondaSakura Python core để sửa/apply.

Không có đường MCP -> modify/create model trong Honda workflow.
