import json, os, hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .config import settings

DATA_DIR = Path(settings.data_dir)
STORE_PATH = DATA_DIR / "records.json"
AUDIT_PATH = DATA_DIR / "audit.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _read(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default

def _write(path: Path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def normalize_record(r: dict[str, Any]) -> dict[str, Any]:
    def g(*keys, default=""):
        for k in keys:
            if k in r and str(r[k]).strip(): return str(r[k]).strip()
        return default
    fir_id = g("fir_id", "id", "fir", "case_id", default=f"LIVE-FIR-{int(datetime.now().timestamp())}")
    return {
        "id": fir_id,
        "suspectName": g("suspect_name", "suspectName", "suspect", default="Unknown Suspect"),
        "crime": g("crime_type", "crime", "offence", default="Unspecified Offence"),
        "phoneLabel": g("phone", "phoneLabel", "mobile", default="+91 00000 00000"),
        "vehicleLabel": g("vehicle", "vehicleLabel", "vehicle_no", default="UNKNOWN-VEHICLE"),
        "locationLabel": g("location", "locationLabel", "place", default="Unknown Location"),
        "stationLabel": g("police_station", "stationLabel", "station", default="Unknown Police Station"),
        "severity": max(1, min(100, int(float(g("severity", "risk", default="60") or 60)))),
        "date": g("date", "fir_date", default=datetime.now(timezone.utc).date().isoformat()),
        "source": g("source", default="api"),
    }

def get_records() -> list[dict[str, Any]]:
    return _read(STORE_PATH, [])

def upsert_records(records: list[dict[str, Any]], source="api") -> list[dict[str, Any]]:
    existing = {r["id"]: r for r in get_records() if "id" in r}
    normalized = []
    for r in records:
        nr = normalize_record({**r, "source": source})
        existing[nr["id"]] = nr
        normalized.append(nr)
    all_records = list(existing.values())
    _write(STORE_PATH, all_records)
    return normalized

def clear_records():
    _write(STORE_PATH, [])

def get_audit() -> list[dict[str, Any]]:
    return _read(AUDIT_PATH, [])

def add_audit(action: str, payload: dict[str, Any], user_id="IG-KA-2048", role="investigator") -> dict[str, Any]:
    chain = get_audit()
    prev = chain[0]["hash"] if chain else "GENESIS"
    entry = {
        "id": len(chain) + 1,
        "at": datetime.now(timezone.utc).isoformat(),
        "user": user_id,
        "role": role,
        "action": action,
        "payload": payload,
        "prev": prev,
    }
    entry["hash"] = hashlib.sha256(json.dumps(entry, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    chain.insert(0, entry)
    _write(AUDIT_PATH, chain[:5000])
    return entry

def graph_from_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    nodes, edges = {}, []
    def node(id, label, type, **extra):
        if id not in nodes: nodes[id] = {"id": id, "label": label, "type": type, **extra}
        return nodes[id]
    for r in records:
        sid = "SUS-" + hashlib.sha1(r["suspectName"].lower().encode()).hexdigest()[:8]
        fid = r["id"]
        phid = "PH-" + hashlib.sha1(r["phoneLabel"].encode()).hexdigest()[:8]
        vid = "VEH-" + hashlib.sha1(r["vehicleLabel"].encode()).hexdigest()[:8]
        lid = "LOC-" + hashlib.sha1(r["locationLabel"].lower().encode()).hexdigest()[:8]
        stid = "ST-" + hashlib.sha1(r["stationLabel"].lower().encode()).hexdigest()[:8]
        node(sid, r["suspectName"], "suspect", risk=r["severity"])
        node(fid, fid, "fir", risk=r["severity"], crime=r["crime"])
        node(phid, r["phoneLabel"], "phone")
        node(vid, r["vehicleLabel"], "vehicle")
        node(lid, r["locationLabel"], "location")
        node(stid, r["stationLabel"], "station")
        edges += [
            {"from": sid, "to": fid, "label": "NAMED_IN"},
            {"from": fid, "to": phid, "label": "USED_PHONE"},
            {"from": fid, "to": vid, "label": "USED_VEHICLE"},
            {"from": fid, "to": lid, "label": "OCCURRED_AT"},
            {"from": fid, "to": stid, "label": "REGISTERED_AT"},
        ]
    return {"nodes": list(nodes.values()), "edges": edges}
