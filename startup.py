# -*- coding: UTF-8 -*-
"""
Honda Sakura Revit MCP startup.
SAFE MODE: register READ-ONLY QC routes only.
Python/pyRevit HondaSakura remains the production core.
"""

from pyrevit import routes
import logging
import traceback

logger = logging.getLogger(__name__)
api = routes.API("revit_mcp")


def register_routes():
    errors = []

    try:
        from revit_mcp.status import register_status_routes
        register_status_routes(api)
        logger.info("Honda MCP status route registered")
    except Exception as ex:
        errors.append("status: {}".format(str(ex)))
        logger.error("Honda MCP status route failed: {}".format(traceback.format_exc()))

    try:
        from revit_mcp.honda_qc import register_honda_qc_routes
        register_honda_qc_routes(api)
        logger.info("Honda Sakura QC routes registered")
    except Exception as ex:
        errors.append("honda_qc: {}".format(str(ex)))
        logger.error("Honda Sakura QC routes failed: {}".format(traceback.format_exc()))

    # Never raise during Revit startup. A failed optional route must not crash Revit.
    if errors:
        logger.error("Honda MCP started with route errors: {}".format(" | ".join(errors)))
    else:
        logger.info("Honda MCP SAFE MODE started successfully")


register_routes()
