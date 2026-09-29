# -*- coding: utf-8 -*-
"""
Honda Sakura MCP QC server.
QC ONLY. It never creates or modifies Revit elements.
Heavy 3D production remains in HondaSakura pyRevit/Python core.
"""
import os
import sys
import base64
import httpx
import anyio
from typing import Optional, Dict, Any, Union
from mcp.server.fastmcp import FastMCP, Image, Context

mcp = FastMCP(
    "Honda Sakura Revit QC",
    host="127.0.0.1",
    port=8000,
    stateless_http=True,
    json_response=True,
)

REVIT_HOST = os.environ.get("REVIT_HOST", "localhost")
REVIT_PORT = int(os.environ.get("REVIT_PORT", "48884"))
BASE_URL = "http://{}:{}/revit_mcp".format(REVIT_HOST, REVIT_PORT)
_http_client: Optional[httpx.AsyncClient] = None

def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            base_url=BASE_URL,
            limits=httpx.Limits(max_keepalive_connections=4, max_connections=8),
        )
    return _http_client

async def _revit_call(method: str, endpoint: str, data: Dict = None, ctx: Context = None,
                      timeout: float = 30.0, params: Dict = None) -> Union[Dict, str]:
    try:
        client = _get_client()
        if method == "GET":
            response = await client.get(endpoint, params=params, timeout=timeout)
        else:
            response = await client.post(endpoint, json=data or {}, timeout=timeout)
        if response.status_code == 200:
            return response.json()
        return "Error: {} - {}".format(response.status_code, response.text)
    except Exception as ex:
        return "Error: {}".format(ex)

async def revit_get(endpoint: str, ctx: Context = None, **kwargs):
    return await _revit_call("GET", endpoint, ctx=ctx, **kwargs)

async def revit_post(endpoint: str, data: Dict[str, Any], ctx: Context = None, **kwargs):
    return await _revit_call("POST", endpoint, data=data, ctx=ctx, **kwargs)

# Register ONLY Honda QC tools.
from tools.honda_qc_tools import register_honda_qc_tools
register_honda_qc_tools(mcp, revit_get, revit_post, None)

async def run_combined_async():
    import uvicorn
    http_app = mcp.streamable_http_app()
    sse_app = mcp.sse_app()
    for route in sse_app.routes:
        http_app.routes.append(route)
    config = uvicorn.Config(
        http_app,
        host=mcp.settings.host,
        port=mcp.settings.port,
        log_level=mcp.settings.log_level.lower(),
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    transport = "stdio"
    if "--sse" in sys.argv:
        transport = "sse"
    elif "--http" in sys.argv or "--streamable-http" in sys.argv:
        transport = "streamable-http"
    elif "--combined" in sys.argv:
        anyio.run(run_combined_async)
        sys.exit(0)
    mcp.run(transport=transport)
