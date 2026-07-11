from datetime import datetime, timedelta, timezone
from fastapi import Header, HTTPException, Depends
import jwt
from .config import settings

DEMO_USERS = {
    "investigator": {"password": "investigator123", "role": "investigator", "user_id": "IG-KA-2048"},
    "soc": {"password": "soc123", "role": "soc", "user_id": "IG-SOC-1001"},
    "admin": {"password": "admin123", "role": "admin", "user_id": "IG-ADMIN-0001"},
}

def create_token(username: str, role: str, user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "role": role,
        "user_id": user_id,
        "iss": settings.jwt_issuer,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=8)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def verify_auth(authorization: str | None = Header(default=None)) -> dict:
    if settings.auth_disabled:
        return {"sub": "demo", "role": "admin", "user_id": "IG-DEMO"}
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"], issuer=settings.jwt_issuer)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")
