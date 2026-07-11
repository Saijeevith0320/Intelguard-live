# IntelGuard Live Working Model

This folder turns the visual IntelGuard prototype into a live-ready working model.

## What is included

- `frontend/` — the world-class IntelGuard UI with a Live API connector.
- `backend/` — FastAPI backend for real data upload, query, reports, audit receipts, and Fabric-ready payloads.
- `fabric/chaincode/auditcc/` — Hyperledger Fabric chaincode for audit receipts.
- `docker-compose.yml` — local live demo: frontend + backend.
- `.env.example` — production environment variables.

## Run locally

```bash
cd intelguard-live
docker compose up --build
```

Open:

```text
http://localhost:8000
```

Click **Live API** and connect to:

```text
http://localhost:8080
```

Then upload CSV/JSON data, import it, and query the platform. The frontend will send imported records and queries to the backend.

## Demo login users

If `AUTH_DISABLED=false`, use:

```text
investigator / investigator123
soc / soc123
admin / admin123
```

For production, replace this with SSO/Auth0/Keycloak/Azure AD.
