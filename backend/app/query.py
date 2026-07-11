from typing import Any
from .storage import get_records, graph_from_records

def mask_phone(phone: str) -> str:
    if phone.startswith("+91") and len(phone) > 8:
        return phone[:6] + "••••••" + phone[-3:]
    return phone

def search_records(query: str, role="investigator") -> dict[str, Any]:
    q = query.lower()
    records = get_records()
    if not records:
        return {"answer": "No live records are loaded yet. Upload CSV/JSON data first.", "evidence": [], "graph": {"nodes": [], "edges": []}}
    matches = []
    for r in records:
        hay = " ".join(str(v).lower() for v in r.values())
        if any(token in hay for token in q.replace("?", "").split() if len(token) > 2):
            matches.append(r)
    if not matches:
        matches = sorted(records, key=lambda x: x.get("severity", 0), reverse=True)[:8]
    else:
        matches = matches[:12]
    ev = []
    for r in matches:
        rr = dict(r)
        if role == "investigator": rr["phoneLabel"] = mask_phone(rr["phoneLabel"])
        ev.append(rr)
    top = ev[0]
    answer = f"Found {len(ev)} evidence record(s). Highest priority: {top['id']} involving {top['suspectName']} for {top['crime']} near {top['locationLabel']} with severity {top['severity']}."
    return {"answer": answer, "evidence": ev, "graph": graph_from_records(matches)}
