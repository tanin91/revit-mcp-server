# -*- coding: utf-8 -*-
"""
Honda Sakura MCP QC server — ROUTE FREE.
Reads JSON snapshots exported by HondaSakura pyRevit core.
It never connects to pyRevit Routes and never modifies Revit.
"""
import os
import sys
import json
import anyio
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP(
    "Honda Sakura Revit QC",
    host="127.0.0.1",
    port=8000,
    stateless_http=True,
    json_response=True,
)

SNAPSHOT = os.path.join(
    os.environ.get("APPDATA", ""),
    "pyRevit", "Extensions", "HondaSakura.extension", "data", "mcp_qc_snapshot.json"
)
SOURCE_CACHE = os.path.join(
    os.environ.get("APPDATA", ""),
    "pyRevit", "Extensions", "HondaSakura.extension", "data", "equipment_source_cache.json"
)

def _load(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        raw=f.read()
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return json.loads(raw.decode("cp932","ignore"))

def _norm(s):
    if s is None:return ""
    return "".join(c.lower() for c in str(s) if c.isalnum() or ("぀" <= c <= "鿿"))

def _num(s):
    if s is None:return None
    t=str(s).replace(",","")
    out=[];started=False
    for c in t:
        if c.isdigit() or c in ".-+":
            out.append(c);started=True
        elif started:break
    try:return float("".join(out)) if out else None
    except:return None

def _require_snapshot():
    d=_load(SNAPSHOT)
    if not d:
        return None, {
            "status":"error",
            "error":"QC snapshot not found",
            "action":"Open Revit and run Honda Sakura > QC > 99 MCP QC Snapshot",
            "snapshot_path":SNAPSHOT,
        }
    return d,None

@mcp.tool()
async def honda_qc_summary(ctx: Context=None) -> str:
    """Read latest Honda Sakura QC snapshot. Route-free and read-only."""
    d,e=_require_snapshot()
    if e:return json.dumps(e,ensure_ascii=False,indent=2)
    out={
      "status":"success","mode":"SNAPSHOT_READ_ONLY","project":d.get("project"),
      "generated_at":d.get("generated_at"),"counts":d.get("counts",{}),
      "network":{
        "pipe_elements_with_open_connectors":len(d.get("network",{}).get("pipe_issues",[])),
        "duct_elements_with_open_connectors":len(d.get("network",{}).get("duct_issues",[])),
      },
      "family_priority":{k:v.get("count",0) for k,v in d.get("family_priority",{}).items()}
    }
    return json.dumps(out,ensure_ascii=False,indent=2)

@mcp.tool()
async def honda_qc_network(domain: str="all", limit: int=300, ctx: Context=None) -> str:
    """Return exact ElementIds with open connectors from latest snapshot."""
    d,e=_require_snapshot()
    if e:return json.dumps(e,ensure_ascii=False,indent=2)
    n=d.get("network",{})
    out={"status":"success","mode":"SNAPSHOT_READ_ONLY","project":d.get("project")}
    if domain in ("all","pipe"):out["pipe_issues"]=n.get("pipe_issues",[])[:limit]
    if domain in ("all","duct"):out["duct_issues"]=n.get("duct_issues",[])[:limit]
    return json.dumps(out,ensure_ascii=False,indent=2)

@mcp.tool()
async def honda_qc_equipment(limit: int=500, ctx: Context=None) -> str:
    """QC missing/duplicate equipment information from latest snapshot."""
    d,e=_require_snapshot()
    if e:return json.dumps(e,ensure_ascii=False,indent=2)
    rows=d.get("equipment",[])
    fields=["code","install_date","model","power_supply","power","flow"]
    missing={k:[] for k in fields};bycode={}
    for r in rows:
        for k in fields:
            if not str(r.get(k,"")).strip():missing[k].append(r.get("element_id"))
        nc=_norm(r.get("code",""))
        if nc:bycode.setdefault(nc,[]).append(r.get("element_id"))
    dups=[{"code":k,"element_ids":v} for k,v in bycode.items() if len(v)>1]
    out={"status":"success","project":d.get("project"),"equipment_count":len(rows),
         "missing_counts":{k:len(v) for k,v in missing.items()},
         "missing_element_ids":{k:v[:limit] for k,v in missing.items()},
         "duplicate_code_groups":dups[:limit]}
    return json.dumps(out,ensure_ascii=False,indent=2)

@mcp.tool()
async def honda_qc_family_priority(ctx: Context=None) -> str:
    """Audit family priority from latest snapshot."""
    d,e=_require_snapshot()
    if e:return json.dumps(e,ensure_ascii=False,indent=2)
    return json.dumps({"status":"success","priority":["LINEUP","TTE","RUG","TEMP"],
                       "family_priority":d.get("family_priority",{})},ensure_ascii=False,indent=2)

@mcp.tool()
async def honda_qc_source_compare(limit: int=500, ctx: Context=None) -> str:
    """Compare equipment source cache with Revit QC snapshot and return ElementIds."""
    d,e=_require_snapshot()
    if e:return json.dumps(e,ensure_ascii=False,indent=2)
    cache=_load(SOURCE_CACHE)
    if not cache:
        return json.dumps({"status":"error","error":"equipment source cache not found",
                           "action":"Run Honda Sakura 05D Equipment Auto Fill first",
                           "source_cache_path":SOURCE_CACHE},ensure_ascii=False,indent=2)
    src=cache.get("records",[]); rev=d.get("equipment",[])
    bycode={};bymodel={}
    for r in src:
        if _norm(r.get("code")):bycode.setdefault(_norm(r.get("code")),[]).append(r)
        if _norm(r.get("model")):bymodel.setdefault(_norm(r.get("model")),[]).append(r)
    issues=[];used=set();matched=0
    for el in rev:
        rec=None;why=""
        nc=_norm(el.get("code"));nm=_norm(el.get("model"))
        if nc and len(bycode.get(nc,[]))==1:rec=bycode[nc][0];why="EXACT_CODE"
        elif nm and len(bymodel.get(nm,[]))==1:rec=bymodel[nm][0];why="UNIQUE_MODEL"
        if rec is None:
            issues.append({"kind":"REVIT_NO_SOURCE_MATCH","element_id":el.get("element_id"),
                           "code":el.get("code"),"model":el.get("model")})
            if len(issues)>=limit:break
            continue
        matched+=1;used.add("{}:{}".format(rec.get("source",""),rec.get("source_id","")))
        diffs=[]
        if rec.get("model") and el.get("model") and _norm(rec.get("model"))!=_norm(el.get("model")):
            diffs.append({"field":"型式","source":rec.get("model"),"revit":el.get("model")})
        if rec.get("power_supply") and el.get("power_supply") and _norm(rec.get("power_supply"))!=_norm(el.get("power_supply")):
            diffs.append({"field":"電源","source":rec.get("power_supply"),"revit":el.get("power_supply")})
        sp=rec.get("power_kw");rp=_num(el.get("power"))
        if sp is not None and rp is not None and abs(float(sp)-rp)>max(0.01,0.03*float(sp)):
            diffs.append({"field":"消費電力","source":sp,"revit":rp})
        sf=rec.get("flow_m3h");rf=_num(el.get("flow"))
        if sf is not None and rf is not None and abs(float(sf)-rf)>max(5.0,0.03*float(sf)):
            diffs.append({"field":"風量","source":sf,"revit":rf})
        if diffs:
            issues.append({"kind":"FIELD_MISMATCH","element_id":el.get("element_id"),
                           "match_rule":why,"differences":diffs})
            if len(issues)>=limit:break
    unmatched=[]
    for r in src:
        sid="{}:{}".format(r.get("source",""),r.get("source_id",""))
        if sid not in used:
            unmatched.append({"source":r.get("source"),"source_id":r.get("source_id"),
                              "code":r.get("code"),"model":r.get("model")})
            if len(unmatched)>=limit:break
    return json.dumps({"status":"success","mode":"SNAPSHOT_READ_ONLY","project":d.get("project"),
                       "source_path":cache.get("source_path",""),"matched_count":matched,
                       "issue_count":len(issues),"issues":issues,
                       "source_unmatched":unmatched},ensure_ascii=False,indent=2)

async def run_combined_async():
    import uvicorn
    http_app=mcp.streamable_http_app()
    sse_app=mcp.sse_app()
    for route in sse_app.routes:http_app.routes.append(route)
    config=uvicorn.Config(http_app,host=mcp.settings.host,port=mcp.settings.port,log_level=mcp.settings.log_level.lower())
    server=uvicorn.Server(config);await server.serve()

if __name__=="__main__":
    if "--combined" in sys.argv:
        anyio.run(run_combined_async)
    elif "--streamable-http" in sys.argv or "--http" in sys.argv:
        mcp.run(transport="streamable-http")
    elif "--sse" in sys.argv:
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")
