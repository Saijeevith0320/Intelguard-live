from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import csv, io, json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .config import settings
from .auth import DEMO_USERS, create_token, verify_auth
from .models import LoginRequest, QueryRequest, IngestRequest, AuditCreate, ReportRequest
from .storage import upsert_records, get_records, get_audit, add_audit, graph_from_records, clear_records
from .query import search_records
from .fabric import submit_to_fabric, fabric_payload

app = FastAPI(title=settings.app_name)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list + ["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"ok": True, "app": settings.app_name, "environment": settings.environment, "records": len(get_records()), "audit": len(get_audit())}

@app.post("/auth/login")
def login(req: LoginRequest):
    user = DEMO_USERS.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_token(req.username, user["role"], user["user_id"]), "token_type": "bearer", "role": user["role"], "user_id": user["user_id"]}

@app.post("/api/ingest/json")
def ingest_json(req: IngestRequest, auth=Depends(verify_auth)):
    imported = upsert_records(req.records, source=req.source)
    audit = add_audit("REAL_DATA_IMPORT", {"rows": len(imported), "source": req.source}, req.user_id, req.role)
    fabric = submit_to_fabric(audit) if settings.fabric_gateway_url else {"prepared": fabric_payload(audit)}
    return {"imported": len(imported), "records": imported, "audit": audit, "fabric": fabric, "total_records": len(get_records())}

@app.post("/api/ingest/file")
async def ingest_file(file: UploadFile = File(...), auth=Depends(verify_auth)):
    content = (await file.read()).decode("utf-8-sig")
    if file.filename.lower().endswith(".json"):
        data = json.loads(content)
        if isinstance(data, dict): data = data.get("records") or data.get("data") or []
    else:
        data = list(csv.DictReader(io.StringIO(content)))
    imported = upsert_records(data, source=file.filename)
    audit = add_audit("REAL_DATA_FILE_IMPORT", {"rows": len(imported), "filename": file.filename}, auth.get("user_id", "api"), auth.get("role", "user"))
    return {"imported": len(imported), "audit": audit, "fabric": submit_to_fabric(audit), "total_records": len(get_records())}

@app.delete("/api/records")
def delete_records(auth=Depends(verify_auth)):
    clear_records()
    audit = add_audit("CLEAR_RECORDS", {}, auth.get("user_id", "api"), auth.get("role", "admin"))
    return {"ok": True, "audit": audit}

@app.post("/api/query")
def query(req: QueryRequest, auth=Depends(verify_auth)):
    result = search_records(req.query, req.role)
    audit = add_audit("QUERY_ANALYSIS", {"query": req.query, "evidence": [x["id"] for x in result["evidence"][:10]]}, req.user_id, req.role)
    return {**result, "audit": audit, "fabric": submit_to_fabric(audit)}

@app.get("/api/graph")
def graph(auth=Depends(verify_auth)):
    return graph_from_records(get_records())

@app.get("/api/audit")
def audit_log(auth=Depends(verify_auth)):
    return {"audit": get_audit()}

@app.post("/api/audit")
def create_audit(req: AuditCreate, auth=Depends(verify_auth)):
    audit = add_audit(req.action, req.payload, req.user_id, req.role)
    return {"audit": audit, "fabric": submit_to_fabric(audit)}

@app.post("/api/fabric/submit-latest")
def submit_latest(auth=Depends(verify_auth)):
    chain = get_audit()
    if not chain: raise HTTPException(status_code=404, detail="No audit entries yet")
    return submit_to_fabric(chain[0])

@app.get("/api/fabric/latest-payload")
def latest_fabric_payload(auth=Depends(verify_auth)):
    chain = get_audit()
    if not chain: raise HTTPException(status_code=404, detail="No audit entries yet")
    return fabric_payload(chain[0])

@app.post("/api/report")
def report(req: ReportRequest, auth=Depends(verify_auth)):
    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    y = h - 50
    pdf.setFont("Helvetica-Bold", 16); pdf.drawString(50, y, req.title); y -= 28
    pdf.setFont("Helvetica", 10); pdf.drawString(50, y, f"User: {req.user_id} | Role: {req.role}"); y -= 24
    if req.query: pdf.drawString(50, y, f"Query: {req.query[:110]}"); y -= 24
    pdf.setFont("Helvetica-Bold", 12); pdf.drawString(50, y, "Evidence"); y -= 18
    pdf.setFont("Helvetica", 9)
    for item in req.evidence[:25]:
        line = f"{item.get('id','')} | {item.get('suspectName','')} | {item.get('crime','')} | {item.get('locationLabel','')} | risk {item.get('severity','')}"
        pdf.drawString(50, y, line[:130]); y -= 14
        if y < 60: pdf.showPage(); y = h - 50; pdf.setFont("Helvetica", 9)
    audit = add_audit("REPORT_EXPORT", {"title": req.title, "evidence_count": len(req.evidence)}, req.user_id, req.role)
    pdf.showPage(); pdf.save(); buf.seek(0)
    return Response(buf.read(), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=intelguard-report.pdf", "X-Audit-Hash": audit["hash"]})
