# -*- coding: UTF-8 -*-
"""
Honda Sakura QC routes.
Read-only QC layer for models produced by the Python/pyRevit TFAS engine.
No model modification is performed here.
"""
from pyrevit import routes, DB
import os
import json
import math
import logging
import traceback

logger = logging.getLogger(__name__)
MM = 304.8

CODE_KEYS = [u"機器番号", u"機器記号", u"記号", u"機番", u"Mark", u"Equipment Number", u"Equipment No"]
DATE_KEYS = [u"設置年月日", u"設置日", u"Install Date", u"Installation Date"]
MODEL_KEYS = [u"型式", u"形式", u"モデル", u"Model", u"Model Number", u"品番"]
FLOW_KEYS = [u"風量", u"給気量", u"排気量", u"処理風量", u"Air Flow", u"Airflow", u"Flow"]
POWER_SUPPLY_KEYS = [u"電源", u"電源仕様", u"Power Supply", u"Voltage"]
POWER_KEYS = [u"消費電力", u"入力", u"定格消費電力", u"Power Consumption", u"Input Power"]


def _eid(el):
    try:
        return el.Id.Value
    except Exception:
        try:
            return el.Id.IntegerValue
        except Exception:
            return None


def _name(el):
    if el is None:
        return u""
    try:
        return el.Name or u""
    except Exception:
        try:
            return DB.Element.Name.GetValue(el) or u""
        except Exception:
            return u""


def _param_text(el, names):
    if el is None:
        return u""
    for n in names:
        try:
            p = el.LookupParameter(n)
            if p:
                return p.AsString() or p.AsValueString() or u""
        except Exception:
            pass
    return u""


def _param_instance_then_type(doc, el, names):
    v = _param_text(el, names)
    if v:
        return v
    try:
        typ = doc.GetElement(el.GetTypeId())
        return _param_text(typ, names)
    except Exception:
        return u""


def _norm(s):
    if s is None:
        return u""
    keep = []
    for c in u"{}".format(s).lower():
        if c.isalnum() or (u"ぁ" <= c <= u"龯"):
            keep.append(c)
    return u"".join(keep)


def _connectors(el):
    try:
        return list(el.ConnectorManager.Connectors)
    except Exception:
        try:
            if el.MEPModel and el.MEPModel.ConnectorManager:
                return list(el.MEPModel.ConnectorManager.Connectors)
        except Exception:
            pass
    return []


def _open_end_count(el):
    n = 0
    for c in _connectors(el):
        try:
            if c.ConnectorType == DB.ConnectorType.End and not c.IsConnected:
                n += 1
        except Exception:
            pass
    return n


def _collect(doc, bic):
    try:
        return list(
            DB.FilteredElementCollector(doc)
            .OfCategory(bic)
            .WhereElementIsNotElementType()
            .ToElements()
        )
    except Exception:
        return []


def _equipment(doc):
    return _collect(doc, DB.BuiltInCategory.OST_MechanicalEquipment)


def _pipes(doc):
    return _collect(doc, DB.BuiltInCategory.OST_PipeCurves)


def _ducts(doc):
    return _collect(doc, DB.BuiltInCategory.OST_DuctCurves)


def _pipe_fittings(doc):
    return _collect(doc, DB.BuiltInCategory.OST_PipeFitting)


def _duct_fittings(doc):
    return _collect(doc, DB.BuiltInCategory.OST_DuctFitting)


def _duct_terminals(doc):
    return _collect(doc, DB.BuiltInCategory.OST_DuctTerminal)


def _family_priority(doc):
    result = {"LINEUP": [], "TTE": [], "RUG": [], "TEMP": [], "OTHER": []}
    for fam in DB.FilteredElementCollector(doc).OfClass(DB.Family):
        n = _name(fam)
        up = n.upper()
        if "LINEUP" in up or "ラインアップ" in n:
            result["LINEUP"].append(n)
        elif up.startswith("TTE") or "TTE_" in up:
            result["TTE"].append(n)
        elif "RUG" in up:
            result["RUG"].append(n)
        elif u"仮スペース" in n or u"サービススペース" in n or u"検討用" in n:
            result["TEMP"].append(n)
        else:
            result["OTHER"].append(n)
    return result


def _equipment_qc(doc, limit=200):
    eqs = _equipment(doc)
    missing = {"code": [], "install_date": [], "model": [], "power_supply": [], "power": [], "flow": []}
    by_code = {}
    rows = []

    for el in eqs:
        code = _param_instance_then_type(doc, el, CODE_KEYS)
        date = _param_instance_then_type(doc, el, DATE_KEYS)
        model = _param_instance_then_type(doc, el, MODEL_KEYS)
        ps = _param_instance_then_type(doc, el, POWER_SUPPLY_KEYS)
        power = _param_instance_then_type(doc, el, POWER_KEYS)
        flow = _param_instance_then_type(doc, el, FLOW_KEYS)

        if not code:
            missing["code"].append(_eid(el))
        else:
            by_code.setdefault(_norm(code), []).append(_eid(el))
        if not date:
            missing["install_date"].append(_eid(el))
        if not model:
            missing["model"].append(_eid(el))
        if not ps:
            missing["power_supply"].append(_eid(el))
        if not power:
            missing["power"].append(_eid(el))
        if not flow:
            missing["flow"].append(_eid(el))

        if len(rows) < limit:
            rows.append({
                "element_id": _eid(el),
                "family": _name(doc.GetElement(el.GetTypeId()).Family) if hasattr(doc.GetElement(el.GetTypeId()), "Family") else "",
                "type": _name(doc.GetElement(el.GetTypeId())),
                "code": code,
                "install_date": date,
                "model": model,
                "power_supply": ps,
                "power": power,
                "flow": flow,
            })

    duplicates = [{"code": k, "element_ids": v} for k, v in by_code.items() if k and len(v) > 1]
    return {
        "equipment_count": len(eqs),
        "missing_counts": {k: len(v) for k, v in missing.items()},
        "missing_element_ids": missing,
        "duplicate_code_groups": duplicates,
        "rows": rows,
    }


def _network_qc(doc, domain="all", limit=300):
    domains = []
    if domain in ("all", "pipe"):
        domains.append(("pipe", _pipes(doc)))
    if domain in ("all", "duct"):
        domains.append(("duct", _ducts(doc)))

    out = {}
    for key, els in domains:
        issues = []
        open_total = 0
        for el in els:
            c = _open_end_count(el)
            open_total += c
            if c and len(issues) < limit:
                issues.append({
                    "element_id": _eid(el),
                    "type": _name(doc.GetElement(el.GetTypeId())),
                    "open_connectors": c,
                })
        out[key] = {
            "segment_count": len(els),
            "open_connector_count": open_total,
            "elements_with_open_connectors": len([1 for x in els if _open_end_count(x) > 0]),
            "issues": issues,
        }
    return out


def _source_cache():
    try:
        appdata = os.environ.get("APPDATA", "")
        p = os.path.join(appdata, "pyRevit", "Extensions", "HondaSakura.extension", "data", "equipment_source_cache.json")
        if not os.path.exists(p):
            return {"available": False, "path": p, "record_count": 0}
        raw = open(p, "rb").read()
        try:
            data = json.loads(raw.decode("utf-8"))
        except Exception:
            data = json.loads(raw.decode("cp932", "ignore"))
        return {
            "available": True,
            "path": p,
            "source_path": data.get("source_path", ""),
            "record_count": len(data.get("records", [])),
        }
    except Exception as ex:
        return {"available": False, "error": str(ex), "record_count": 0}


def register_honda_qc_routes(api):
    @api.route("/honda_qc_summary/", methods=["GET"])
    def honda_qc_summary(doc, request):
        try:
            if not doc:
                return routes.make_response(data={"error": "No active Revit document"}, status=503)
            eq = _equipment_qc(doc, 30)
            net = _network_qc(doc, "all", 30)
            fam = _family_priority(doc)
            data = {
                "status": "success",
                "project": doc.Title,
                "mode": "READ_ONLY_QC",
                "python_core": "HondaSakura TFAS/pyRevit",
                "counts": {
                    "pipes": len(_pipes(doc)),
                    "pipe_fittings": len(_pipe_fittings(doc)),
                    "ducts": len(_ducts(doc)),
                    "duct_fittings": len(_duct_fittings(doc)),
                    "duct_terminals": len(_duct_terminals(doc)),
                    "equipment": eq["equipment_count"],
                },
                "network": {
                    "pipe_open_connectors": net.get("pipe", {}).get("open_connector_count", 0),
                    "duct_open_connectors": net.get("duct", {}).get("open_connector_count", 0),
                },
                "equipment_missing": eq["missing_counts"],
                "equipment_duplicate_code_groups": len(eq["duplicate_code_groups"]),
                "family_priority": {k: len(v) for k, v in fam.items()},
                "equipment_source_cache": _source_cache(),
            }
            return routes.make_response(data=data)
        except Exception as ex:
            return routes.make_response(data={"error": str(ex), "traceback": traceback.format_exc()}, status=500)

    @api.route("/honda_qc_network/", methods=["POST"])
    def honda_qc_network(doc, request):
        try:
            if not doc:
                return routes.make_response(data={"error": "No active Revit document"}, status=503)
            data = json.loads(request.data) if isinstance(request.data, str) else (request.data or {})
            domain = data.get("domain", "all")
            limit = int(data.get("limit", 300))
            if domain not in ("all", "pipe", "duct"):
                return routes.make_response(data={"error": "domain must be all, pipe, or duct"}, status=400)
            return routes.make_response(data={"status": "success", "mode": "READ_ONLY_QC", "result": _network_qc(doc, domain, limit)})
        except Exception as ex:
            return routes.make_response(data={"error": str(ex), "traceback": traceback.format_exc()}, status=500)

    @api.route("/honda_qc_equipment/", methods=["POST"])
    def honda_qc_equipment(doc, request):
        try:
            if not doc:
                return routes.make_response(data={"error": "No active Revit document"}, status=503)
            data = json.loads(request.data) if isinstance(request.data, str) else (request.data or {})
            limit = int(data.get("limit", 200))
            out = _equipment_qc(doc, limit)
            out["source_cache"] = _source_cache()
            return routes.make_response(data={"status": "success", "mode": "READ_ONLY_QC", "result": out})
        except Exception as ex:
            return routes.make_response(data={"error": str(ex), "traceback": traceback.format_exc()}, status=500)

    @api.route("/honda_qc_family_priority/", methods=["GET"])
    def honda_qc_family_priority(doc, request):
        try:
            if not doc:
                return routes.make_response(data={"error": "No active Revit document"}, status=503)
            fam = _family_priority(doc)
            return routes.make_response(data={
                "status": "success",
                "mode": "READ_ONLY_QC",
                "priority": ["LINEUP", "TTE", "RUG", "TEMP"],
                "counts": {k: len(v) for k, v in fam.items()},
                "families": {k: v[:100] for k, v in fam.items()},
            })
        except Exception as ex:
            return routes.make_response(data={"error": str(ex), "traceback": traceback.format_exc()}, status=500)

    logger.info("Honda Sakura QC routes registered successfully")
