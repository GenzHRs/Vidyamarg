# VidyamargAI — Security & Tenant Isolation Audit

**Audit Date**: October 9, 2026  
**Auditor**: Lead Security Auditor  
**Mode**: Read-Only Security Architecture & Code Inspection  

---

## 1. Authentication Architecture

### JWT Implementation (`backend/app/core/security.py`)
- **Algorithm**: HS256 with cryptographically generated secret.
- **Payload Validation**:
  - `sub` field extracted and validated as registered email.
  - Expiration timestamp `exp` strictly checked against UTC time; expired tokens trigger `401 Unauthorized`.
- **Database Identity Verification**:
  - Every authenticated request calls `get_current_user`, querying the `users` table to verify user existence and active status.
  - Prevents revoked or deleted users with valid tokens from making requests.

### CSRF Mitigation
- **Pattern**: Double Submit Cookie pattern.
- **Enforcement**: State-modifying requests (`POST`, `PUT`, `DELETE`, `PATCH`) that rely on browser cookies must provide a matching `x-csrf-token` header.
- **Comparison**: Verified via `secrets.compare_digest` to prevent timing attacks.

---

## 2. Tenant Isolation & IDOR Protection

### Candidate Context Scoping
In multi-tenant SaaS, cross-tenant data leakage is a critical risk. We audited candidate-scoped routers:

1. **Resume Center (`backend/app/api/routers/resume_center.py`)**:
   - `_get_or_create_candidate(current_user)` resolves the candidate exclusively from `current_user.id`.
   - Every read, update, generation, or download endpoint requires ownership validation:
     ```python
     def _verify_resume_ownership(db: Session, resume_id: str, candidate_id: str) -> Resume:
         resume = db.query(Resume).filter(Resume.id == resume_id, Resume.candidate_id == candidate_id).first()
         if not resume:
             raise HTTPException(status_code=403, detail="Resume does not belong to candidate")
         return resume
     ```
   - **Status**: **[VERIFIED]** (Tested in `test_candidate_ownership_isolation` which confirms 403 Forbidden on foreign candidate access).

2. **Jobs & Recommendations (`backend/app/api/routers/jobs.py`)**:
   - Recommendations query candidate's active resume and verified skills using `candidate.id`.
   - Candidate A cannot query or influence recommendations for Candidate B.
   - **Status**: **[VERIFIED]**

3. **Autofill Service (`backend/app/api/routers/autofill.py`)**:
   - Requires `current_user`.
   - Checks subscription entitlement (`Plus` or `Pro`) and scopes extracted candidate profile data strictly to `candidate.id`.
   - **Status**: **[VERIFIED]**

---

## 3. Administrative Gates & Role-Based Access Control (RBAC)

### Admin Router Protection (`backend/app/api/routers/admin.py`)
- Protected by `Depends(get_current_admin)`.
- Enforces `current_user.role in ["admin", "super_admin"]`.
- Regular candidates or recruiters attempting access to `/api/admin/*` are rejected with `403 Forbidden: Insufficient permissions`.
- **Status**: **[VERIFIED]**

---

## 4. Secret Management & PII Safety

- **Environment Config**: Secrets (`JWT_SECRET`, database passwords, API keys) are loaded through `pydantic-settings` from environment variables, never hardcoded in source.
- **Credential Masking**: Loggers and error handlers sanitize token and credential values.
- **Candidate PII in Prompts**: AI prompt construction isolates candidate facts without leaking cross-candidate context.

---

## 5. Security Audit Verdict
The security posture of the application is **VERIFIED**. Authentication, CSRF mitigation, role-based authorization, and candidate tenant isolation are properly implemented and covered by unit/integration tests.
