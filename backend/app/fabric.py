import requests
from .config import settings

def fabric_payload(audit_entry: dict) -> dict:
    return {
        "network": "Hyperledger Fabric",
        "channel": settings.fabric_channel,
        "chaincode": settings.fabric_chaincode,
        "function": settings.fabric_function,
        "mspId": settings.fabric_msp_id,
        "args": [{
            "auditId": str(audit_entry["id"]),
            "action": audit_entry["action"],
            "user": audit_entry["user"],
            "role": audit_entry["role"],
            "timestamp": audit_entry["at"],
            "payloadHash": audit_entry["hash"],
            "previousHash": audit_entry["prev"],
            "currentHash": audit_entry["hash"],
            "payload": audit_entry.get("payload", {}),
        }]
    }

def submit_to_fabric(audit_entry: dict) -> dict:
    payload = fabric_payload(audit_entry)
    if not settings.fabric_gateway_url:
        return {"mode": "prepared", "submitted": False, "payload": payload, "message": "FABRIC_GATEWAY_URL not configured"}
    try:
        r = requests.post(settings.fabric_gateway_url.rstrip("/") + "/transactions", json=payload, timeout=15)
        return {"mode": "submitted", "submitted": r.ok, "status_code": r.status_code, "response": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text, "payload": payload}
    except Exception as exc:
        return {"mode": "error", "submitted": False, "error": str(exc), "payload": payload}
