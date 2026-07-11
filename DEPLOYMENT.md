# IntelGuard Production Deployment Guide

## Recommended production stack

- Frontend: Cloudflare Pages / Vercel / Netlify
- Backend: Google Cloud Run / AWS ECS / Azure Container Apps
- Graph DB: Neo4j AuraDB
- Operational DB: PostgreSQL, if required
- Ledger: Hyperledger Fabric network
- Storage: GCS/S3 for reports and evidence exports
- Auth: Keycloak, Auth0, Azure AD, or NIC/department SSO

## 1. Deploy backend to Google Cloud Run

```bash
cd backend
gcloud builds submit --tag gcr.io/PROJECT_ID/intelguard-api
gcloud run deploy intelguard-api \
  --image gcr.io/PROJECT_ID/intelguard-api \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production,AUTH_DISABLED=false,CORS_ORIGINS=https://app.yourdomain.com
```

Set secrets using Secret Manager:

```text
JWT_SECRET
NEO4J_URI
NEO4J_USERNAME
NEO4J_PASSWORD
GEMINI_API_KEY
FABRIC_GATEWAY_URL
```

## 2. Deploy frontend

Upload `frontend/` to Cloudflare Pages, Vercel, Netlify, or Firebase Hosting.

After deployment, open the app, click **Live API**, and set:

```text
https://api.yourdomain.com
```

## 3. Hyperledger Fabric integration

Do **not** connect Fabric directly from browser JavaScript. The frontend prepares payloads, but the backend must submit to Fabric because certificates/private keys must remain server-side.

Production flow:

```text
Frontend -> Backend API -> Fabric Gateway SDK -> endorsing peers -> orderer -> committed block -> txId returned
```

Chaincode path:

```text
fabric/chaincode/auditcc
```

Suggested channel and chaincode:

```text
Channel: intelguard-channel
Chaincode: auditcc
Function: CreateAuditReceipt
```

## 4. Real data security checklist

- HTTPS only
- SSO + MFA
- RBAC enforced in backend, not only frontend
- Encrypt secrets in Secret Manager/Vault
- Keep Fabric keys in HSM or secure backend volume
- Mask PII based on role
- Maintain immutable audit receipts
- Enable WAF and rate limiting
- Log all imports, queries, exports, failed logins
- Run penetration test before using real police data
