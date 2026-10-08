# VidyamargAI — Production Resume Center Test Suite & Verification

## Test Strategy Overview

The Resume Center test suite implements defense-in-depth verification across unit, integration, security, and end-to-end layers:

1. **Backend Integration & Security Tests (`backend/tests/test_resume_center.py`)**:
   - Database operations (CRUD, Alembic migrations, foreign keys).
   - Candidate ownership isolation (prevent cross-user data access).
   - File validation (magic bytes, MIME types, 10MB limit).
   - Sandboxed LaTeX compilation, escaping regexes, and PDF/TeX downloads.
   - Zero-hallucination JD alignment and non-destructive approvals.
2. **Frontend Integration Tests (`frontend/tests/resume-center.test.cjs`)**:
   - Bearer token authorization and CSRF token transmission.
   - Query string serialization for search and status filters.
   - Typed payload delivery for CRUD, compile, and approval workflows.
3. **Static Analysis & Build Verification**:
   - TypeScript 5 strict type checking (`npx tsc --noEmit`).
   - ESLint validation (`npm run lint -- --quiet`).
   - Next.js Turbopack production compilation (`npm run build`).

---

## Backend Test Breakdown (`test_resume_center.py`)

| Test Case | Scope & Objective |
|---|---|
| `test_templates_endpoint_returns_12_templates` | Verifies all 12 Overleaf templates are seeded, active, and include valid ATS scores (93%–99%). |
| `test_create_and_get_resume` | Tests creation of structured resume document, database persistence, and retrieval. |
| `test_candidate_ownership_isolation` | Verifies candidate A cannot view, edit, or delete candidate B's resume (returns `404 Not Found`). |
| `test_unauthenticated_request_rejected` | Verifies all endpoints reject requests lacking valid JWT authorization (`401 Unauthorized`). |
| `test_upload_magic_bytes_and_size_validation` | Uploads valid and invalid files; verifies magic bytes enforcement (`%PDF-`) and 10MB limit rejection (`400 Bad Request`). |
| `test_versioning_and_restore` | Verifies version snapshot creation and rollback mechanism. Restoring a prior version creates a new version with past data. |
| `test_latex_escaping_prevents_injection` | Passes malicious LaTeX tokens (`\`, `{`, `}`, `%`, `$`, `&`, `_`, `#`, `~`, `^`) and verifies single-pass escaping neutralization. |
| `test_latex_compilation_and_tex_download` | Validates LaTeX code rendering, sandboxed compilation invocation, and `.tex` source text streaming. |
| `test_jd_analysis_anti_hallucination` | Tests JD keyword extraction. Confirms unverified skills are placed in `missing_requirements` rather than added to profile. |
| `test_tailoring_approval_preserves_original` | Tests non-destructive approval. Confirms original resume remains completely untouched when saving as a new resume. |

---

## Frontend Test Breakdown (`resume-center.test.cjs`)

| Test Case | Scope & Objective |
|---|---|
| `resumeCenterApi includes auth token and csrf header in requests` | Confirms every HTTP request attaches `Bearer <token>` and `X-CSRF-Token` headers. |
| `resumeCenterApi.getResumes sends search and status query parameters correctly` | Tests query parameter construction for `search` and `status_filter`. |
| `resumeCenterApi.createResume posts structured resume payload with JSON Content-Type` | Verifies JSON payload serialization and `Content-Type: application/json`. |
| `resumeCenterApi.compileResume triggers compilation endpoint and returns status` | Tests compilation trigger and response parsing (`status: COMPILED`). |
| `resumeCenterApi.approveTailoring sends approved data non-destructively` | Verifies non-destructive approval payload transmission (`create_new_resume: true`). |

---

## How to Run Tests

### 1. Run Backend Pytest Suite
```bash
# From repository root:
pytest backend/tests

# Run Resume Center tests specifically:
pytest backend/tests/test_resume_center.py -v
```
**Expected Result**: `65 passed, 1 skipped` (100% pass rate).

### 2. Run Frontend Test Suite
```bash
# Run Resume Center frontend tests:
node --test frontend/tests/resume-center.test.cjs

# Run all frontend integration tests:
node --test frontend/tests/api.test.cjs frontend/tests/e2e.test.cjs frontend/tests/resume-center.test.cjs
```
**Expected Result**: `16 passed` (100% pass rate).

### 3. Run Static Type Checking & Linter
```bash
cd frontend

# TypeScript check (0 errors):
cmd /c npx tsc --noEmit

# ESLint check (0 errors):
cmd /c npx eslint --quiet

# Next.js Production Build:
cmd /c npm run build
```
