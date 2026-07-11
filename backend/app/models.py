from pydantic import BaseModel, Field
from typing import Any, Optional

class LoginRequest(BaseModel):
    username: str
    password: str

class QueryRequest(BaseModel):
    query: str
    user_id: str = "IG-KA-2048"
    role: str = "investigator"
    language: str = "en"

class CrimeRecord(BaseModel):
    fir_id: str = Field(alias="id")
    suspect_name: str
    crime_type: str = "Unspecified Offence"
    phone: str = "+91 00000 00000"
    vehicle: str = "UNKNOWN-VEHICLE"
    location: str = "Unknown Location"
    police_station: str = "Unknown Police Station"
    severity: int = 60
    date: Optional[str] = None

class IngestRequest(BaseModel):
    records: list[dict[str, Any]]
    source: str = "frontend-upload"
    user_id: str = "IG-KA-2048"
    role: str = "investigator"

class AuditCreate(BaseModel):
    action: str
    payload: dict[str, Any]
    user_id: str = "IG-KA-2048"
    role: str = "investigator"

class ReportRequest(BaseModel):
    title: str = "IntelGuard Intelligence Report"
    query: str | None = None
    evidence: list[dict[str, Any]] = []
    user_id: str = "IG-KA-2048"
    role: str = "investigator"
