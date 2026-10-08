# VidyamargAI — Production Resume Center Security & Integrity

## 1. Candidate Ownership Isolation (Row-Level Authorization)

The Resume Center strictly enforces row-level multi-tenant isolation across all endpoints:

```python
resume = db.query(Resume).filter(
    Resume.id == resume_id,
    Resume.candidate_id == current_candidate.id
).first()
if not resume:
    raise HTTPException(status_code=404, detail="Resume not found")
```

- **Candidate Scoping**: Every resume, version snapshot, compile request, and download is validated against the authenticated candidate's ID extracted from the verified JWT.
- **Enumeration Prevention**: Requesting a resume that belongs to another candidate returns `404 Not Found` rather than `403 Forbidden`, preventing attackers from enumerating valid resume IDs.
- **Admin Isolation**: Admin users cannot silently tamper with candidate resumes; they access candidate profiles through read-only audit endpoints.

---

## 2. File Ingestion & Magic-Byte Validation

To prevent malicious polyglot file uploads, web shells, and executable payloads:

1. **Size Enforced Limit**: Incoming files must not exceed **10MB**. Payloads exceeding this limit are rejected immediately before reading into memory.
2. **Magic-Byte Signature Verification**:
   - **PDF**: Verified against signature `b"%PDF-"`.
   - **DOCX**: Verified as a valid Zip container (`b"PK\x03\x04"`) with document XML structures.
   - **TEX & TXT**: Verified as decodable UTF-8 text free of binary null-byte bombs.
3. **MIME Whitelist**: `storage.py` whitelists only trusted MIME types (`application/pdf`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `text/plain`, `application/x-tex`, `text/x-tex`).

---

## 3. Sandboxed LaTeX Compilation Security

LaTeX is a Turing-complete macro language. VidyamargAI implements defense-in-depth measures to sandbox compilation:

### A. Shell Escape Disabled
Compilation commands are invoked with `-no-shell-escape`:
```python
cmd = [
    "pdflatex",
    "-interaction=nonstopmode",
    "-halt-on-error",
    "-no-shell-escape",
    tex_filename,
]
```
This flag prevents LaTeX packages and macros from executing shell commands (`\write18`).

### B. Single-Pass Character Sanitization
All candidate text inputs (names, summaries, bullet points, skills) are escaped through a single-pass regex escaper before template interpolation:
```python
_LATEX_ESCAPES = {
    "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
    "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}", "\\": r"\textbackslash{}",
}
```
Single-pass execution prevents cascading escape loops (e.g., escaping backslashes from already-escaped characters).

### C. Isolated Ephemeral Workspaces
Compilation takes place in an isolated `tempfile.TemporaryDirectory()`. The directory and all auxiliary artifacts (`.aux`, `.log`, `.out`) are guaranteed to be cleaned up in a `finally:` block.

### D. Path Masking in Logs & Error Messages
Raw server paths (e.g., `/var/task`, `C:\Users\...`) are filtered and sanitized before any compilation errors are returned in API responses:
```python
clean_log = re.sub(r"[A-Za-z]:\\[\w\\]+", "[internal_path]", raw_log)
```

---

## 4. Anti-Hallucination & AI Workflow Guarantees

AI tailoring must never compromise candidate credibility or invent fraudulent qualifications:

1. **System Prompt Directives**: The tailoring engine explicitly instructs the LLM:
   > *"CRITICAL ZERO-HALLUCINATION REQUIREMENT: Never invent candidate work experience, credentials, degrees, employers, or skills not explicitly present in the original resume. If the job description requires skills the candidate lacks, mark them in missing_requirements. DO NOT claim the candidate possesses them."*
2. **Pydantic Schema Validation**: LLM outputs are validated against the strict `TailoredResumeOutput` schema. If schema parsing fails, a second corrective pass is executed.
3. **Offline Lexical Fallback**: When LLM APIs are unreachable, a deterministic keyword overlap algorithm runs offline, ensuring zero downtime and 100% truthful data.
4. **Non-Destructive Approvals**: The original resume is never silently modified. The candidate must explicitly approve proposed phrasing in a side-by-side diff review before saving as a new version or new resume.

---

## 5. Private Storage & Transport

- **No Public Buckets**: Resumes are stored under private paths in local filesystem storage or S3/MinIO buckets with private ACLs.
- **Authenticated Proxy Downloads**: All downloads pass through authenticated backend proxy routes (`/resumes/{id}/download/pdf` and `/resumes/{id}/download/latex`) rather than exposed static links.
- **CSRF Tokens**: Mutating requests validate `X-CSRF-Token` headers to protect browser sessions from cross-site request forgery.
