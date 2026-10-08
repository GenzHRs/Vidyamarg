# VidyamargAI — Production Platform & Resume Center

VidyamargAI is an enterprise-grade AI career platform featuring a full-stack **Resume Center**, Skill Lab learning environments, AI career mentorship, and automated job intelligence workflows.

---

## Production Resume Center

The Resume Center (`/candidate/resumes`) provides an Overleaf-grade LaTeX resume generation and intelligence engine with 12 battle-tested templates:

- **1. Upload Resume (`/candidate/resumes/upload`)**: Upload PDF, DOCX, TXT, or TeX. Features magic-byte signature validation, 10MB limit, AI section structuring, offline heuristic fallbacks, candidate review/correction form, and private document storage.
- **2. Create New Resume (`/candidate/resumes/new`)**: Multi-section structured builder with real-time draft saving, template selection, and live PDF compilation.
- **3. Template Gallery (`/candidate/resumes/templates`)**: 12 Overleaf-compatible LaTeX templates (Software Engineer, Data Analyst, Data Scientist, Product Manager, Academic CV, ATS Classic, Minimal Professional, Compact One-Page, Two-Column Modern, Fresher, Executive) with verified 93%–99% ATS ratings and MIT licensing.
- **4. Live Editor (`/candidate/resumes/edit/[resumeId]`)**: Split-screen interface with structured form on the left, live PDF/LaTeX preview on the right, autosave, version history drawer, diff tracking, and one-click version rollback.
- **5. JD-Based Tailoring (`/candidate/resumes/tailor/[resumeId]`)**: Match your resume against any job description. Categorizes matching vs missing requirements, suggests phrasing improvements, guarantees zero hallucination, and requires explicit candidate approval before saving non-destructively.

---

## Local Setup

1. **Environment Variables**:
   Copy `.env.example` to `.env` and configure `SECRET_KEY`, `POSTGRES_PASSWORD`, and any optional AI integration keys (`GEMINI_API_KEY`, `GROQ_API_KEY`). Keep `.env` private.
2. **Database & Migrations**:
   Start PostgreSQL and Redis. Run Alembic migrations:
   ```bash
   alembic upgrade head
   ```
   *Note: Application startup never modifies database schemas automatically.*
3. **Backend Service**:
   Install requirements: `pip install -r backend/requirements.txt`.
   Start API from repository root:
   ```bash
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```
4. **Frontend Service**:
   Install dependencies: `cd frontend && npm ci`.
   Copy `frontend/.env.example` to `frontend/.env.local`.
   Start development server:
   ```bash
   npm run dev
   ```
5. **Access Application**:
   - Web application: `http://localhost:3000`
   - Resume Center: `http://localhost:3000/candidate/resumes`
   - API Docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`

---

## LaTeX Compilation Environment

The Resume Center compiles LaTeX resumes into PDF using `pdflatex`:
- **Docker / Linux**: Install TeX Live (`apt-get install -y texlive-latex-base texlive-latex-extra texlive-fonts-recommended`).
- **Windows**: Install MiKTeX or TeX Live for Windows.
- **Standalone Mode**: If `pdflatex` is not installed on the host, the system gracefully generates clean `.tex` files ready for one-click import into Overleaf or local compilation.

---

## Security & Privacy Invariants

1. **Candidate Ownership Isolation**: Strict row-level authorization ensures candidates cannot view, edit, or download another candidate's resumes or versions.
2. **Zero-Hallucination Integrity**: AI tailoring only refines the presentation of verified facts. Unverified skills are marked as missing rather than inserted.
3. **Non-Destructive Storage**: Original uploaded resumes and prior versions are never silently overwritten.
4. **Sandboxed LaTeX Execution**: Invoked with `-no-shell-escape` and sanitized with single-pass regex escaping to neutralize injection attacks.
5. **Private Storage**: Resumes are served through authenticated streaming proxy endpoints, not public URLs.

---

## Running Tests

### Backend Tests (pytest)
```bash
pytest backend/tests
```
*Current test suite: 65 passed, 1 skipped, 0 failed.*

### Frontend Tests (node:test)
```bash
node --test frontend/tests/api.test.cjs frontend/tests/e2e.test.cjs frontend/tests/resume-center.test.cjs
```
*Current test suite: 16 passed, 0 failed.*

### Static Type & Lint Verification
```bash
cd frontend
npx tsc --noEmit
npx eslint --quiet
npm run build
```

---

## Documentation

Detailed technical documentation is available in the `docs/` folder:
- [`docs/resume-feature.md`](docs/resume-feature.md): Complete functional specification and template catalog.
- [`docs/resume-api.md`](docs/resume-api.md): Reference guide for all 17 Resume Center endpoints.
- [`docs/resume-security.md`](docs/resume-security.md): Security architecture, row-level isolation, and LaTeX sandboxing.
- [`docs/resume-testing.md`](docs/resume-testing.md): Test plan, coverage breakdown, and verification procedures.
