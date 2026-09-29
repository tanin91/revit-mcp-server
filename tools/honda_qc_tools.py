# -*- coding: utf-8 -*-
"""Honda Sakura QC MCP tools (read-only)."""

from mcp.server.fastmcp import Context
from .utils import format_response


def register_honda_qc_tools(mcp, revit_get, revit_post, revit_image=None):
    _ = revit_image

    @mcp.tool()
    async def honda_qc_summary(ctx: Context = None) -> str:
        """Run a read-only Honda Sakura QC summary on the active Revit model.

        Returns Pipe/Duct/Terminal/Equipment counts, open connectors,
        missing equipment metadata, duplicate machine numbers, family-priority
        availability, and source-cache availability.
        """
        response = await revit_get("/honda_qc_summary/", ctx)
        return format_response(response)

    @mcp.tool()
    async def honda_qc_network(
        domain: str = "all",
        limit: int = 300,
        ctx: Context = None,
    ) -> str:
        """Read-only QC for Pipe/Duct open connectors.

        Args:
            domain: all, pipe, or duct
            limit: maximum issue rows returned
        """
        response = await revit_post(
            "/honda_qc_network/",
            {"domain": domain, "limit": limit},
            ctx,
        )
        return format_response(response)

    @mcp.tool()
    async def honda_qc_equipment(
        limit: int = 200,
        ctx: Context = None,
    ) -> str:
        """Read-only QC for Takasago/Honda Sakura equipment metadata.

        Checks:
        機器番号 / 設置年月日 / 型式 / 電源 / 消費電力 / 風量,
        duplicate equipment codes, and the latest HondaSakura source cache.
        """
        response = await revit_post(
            "/honda_qc_equipment/",
            {"limit": limit},
            ctx,
        )
        return format_response(response)

    @mcp.tool()
    async def honda_qc_family_priority(ctx: Context = None) -> str:
        """Audit loaded Revit families using Honda Sakura priority:
        LINEUP -> TTE -> RUG -> TEMP.
        This tool is read-only.
        """
        response = await revit_get("/honda_qc_family_priority/", ctx)
        return format_response(response)


    @mcp.tool()
    async def honda_qc_source_compare(
        limit: int = 500,
        ctx: Context = None,
    ) -> str:
        """Compare the latest HondaSakura IFC/PDF/DXF/CSV equipment source cache
        against the active Revit model and return exact Revit ElementIds for issues.

        Matching priority:
        1) exact 機器番号
        2) unique 型式

        Reports:
        - Revit equipment with no source match
        - field mismatches for 機器番号 / 型式 / 電源 / 消費電力 / 風量
        - source records not represented in Revit

        Read-only. Run HondaSakura 05D first to refresh the source cache.
        """
        response = await revit_post(
            "/honda_qc_source_compare/",
            {"limit": limit},
            ctx,
        )
        return format_response(response)
