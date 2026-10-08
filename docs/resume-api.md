# VidyamargAI — Production Resume Center API Reference

## Base URL
`/api/v1`

## Authentication
All endpoints require authentication via Bearer token:
```http
Authorization: Bearer <jwt_access_token>
```
Mutating operations (`POST`, `PATCH`, `DELETE`) also validate the `X-CSRF-Token` header when browser cookies are present.

---

## 1. Resume Template Endpoints

### `GET /resume-templates`
Retrieve all available LaTeX resume templates.

- **Auth**: Candidate / Admin
- **Response**: `200 OK`
```json
[
  {
    "id": 1,
    "name": "ATS Classic",
    "slug": "ats-classic",
    "description": "Clean, traditional single-column format optimized for highest ATS readability.",
    "category": "Engineering",
    "ats_score": 99,
    "license_name": "MIT",
    "is_active": true
  }
]
```

### `GET /resume-templates/{template_id}`
Retrieve a specific template by ID, including its raw LaTeX skeleton.

- **Auth**: Candidate / Admin
- **Response**: `200 OK`
```json
{
  "id": 1,
  "name": "ATS Classic",
  "slug": "ats-classic",
  "description": "Clean, traditional single-column format...",
  "category": "Engineering",
  "ats_score": 99,
  "license_name": "MIT",
  "is_active": true,
  "latex_template": "\\documentclass[10pt,letterpaper]{article}..."
}
```

---

## 2. Resumes CRUD Endpoints

### `GET /resumes`
List all resumes owned by the authenticated candidate.

- **Query Parameters**:
  - `search` *(string, optional)*: Filter by title, template name, or source.
  - `status_filter` *(string, optional)*: Filter by status (`draft`, `compiled`, `parsed`, `tailored`).
- **Response**: `200 OK`
```json
[
  {
    "id": 10,
    "title": "Senior Backend Engineer",
    "source_type": "uploaded",
    "template_id": 1,
    "template_name": "ATS Classic",
    "template_slug": "ats-classic",
    "version_number": 2,
    "original_file_url": "/api/v1/storage/resumes/orig_12345.pdf",
    "latest_pdf_url": "/api/v1/storage/resumes/compiled_10.pdf",
    "latest_tex_url": "/api/v1/storage/resumes/compiled_10.tex",
    "status": "COMPILED",
    "created_at": "2026-10-04T12:00:00Z",
    "updated_at": "2026-10-04T12:30:00Z",
    "change_summary": "Added distributed tracing project"
  }
]
```

### `POST /resumes`
Create a new structured resume document.

- **Request Body**:
```json
{
  "title": "Full Stack Developer",
  "template_id": 1,
  "structured_data": {
    "personal_info": {
      "full_name": "Alex Mercer",
      "email": "alex@example.com",
      "phone": "+1 555 019 2831",
      "location": "Austin, TX",
      "linkedin": "linkedin.com/in/alexmercer",
      "github": "github.com/alexmercer"
    },
    "summary": "Full Stack Engineer with 5+ years building distributed web applications.",
    "experience": [
      {
        "title": "Software Engineer",
        "company": "Tech Corp",
        "start_date": "2022",
        "end_date": "Present",
        "bullets": [
          "Developed high-throughput REST APIs using FastAPI.",
          "Implemented frontend dashboards with Next.js and Tailwind CSS."
        ]
      }
    ],
    "education": [
      {
        "degree": "B.S. in Computer Science",
        "institution": "University of Texas",
        "graduation_year": "2022"
      }
    ],
    "skills": {
      "Languages": ["Python", "TypeScript", "SQL"],
      "Frameworks": ["FastAPI", "React", "Next.js"]
    }
  }
}
```
- **Response**: `201 Created` (Returns created resume object)

### `GET /resumes/{resume_id}`
Get details and current structured data for a resume. Candidate ownership is strictly enforced.

- **Response**: `200 OK`

### `PATCH /resumes/{resume_id}`
Update resume title, template, or structured data. Optionally creates a new version record.

- **Request Body**:
```json
{
  "title": "Senior Full Stack Developer",
  "template_id": 2,
  "structured_data": { ... },
  "change_summary": "Updated summary and skills",
  "create_new_version": true
}
```
- **Response**: `200 OK`

### `DELETE /resumes/{resume_id}`
Delete a resume and all its version history.

- **Response**: `200 OK`
```json
{
  "message": "Resume deleted successfully",
  "id": 10
}
```

---

## 3. Resume Upload Endpoint

### `POST /resumes/upload`
Upload an existing document (PDF, DOCX, TXT, TEX). Magic bytes are validated. The original file is preserved in private storage.

- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: Binary file (PDF, DOCX, TXT, TEX)
  - `title` *(optional)*: Custom title
  - `template_id` *(optional)*: Preferred LaTeX template ID
- **Response**: `201 Created`
```json
{
  "message": "Resume uploaded and parsed successfully",
  "resume_id": 12,
  "version_id": 15,
  "title": "Resume - Alex Mercer",
  "original_file_url": "/api/v1/storage/resumes/orig_1728045600_resume.pdf",
  "structured_data": { ... },
  "extracted_text_preview": "Alex Mercer\nSoftware Engineer..."
}
```

---

## 4. Version Management Endpoints

### `GET /resumes/{resume_id}/versions`
Retrieve all historical versions for a resume.

- **Response**: `200 OK`
```json
[
  {
    "id": 16,
    "version_number": 2,
    "change_summary": "Added distributed tracing project",
    "created_at": "2026-10-04T12:30:00Z",
    "is_current": true,
    "structured_data": { ... }
  },
  {
    "id": 15,
    "version_number": 1,
    "change_summary": "Initial upload",
    "created_at": "2026-10-04T12:00:00Z",
    "is_current": false,
    "structured_data": { ... }
  }
]
```

### `POST /resumes/{resume_id}/versions`
Explicitly snapshot a new version.

- **Request Body**:
```json
{
  "structured_data": { ... },
  "change_summary": "Pre-interview revision"
}
```
- **Response**: `201 Created`

### `POST /resumes/{resume_id}/versions/{version_id}/restore`
Roll back the resume's active structured data to match a prior version snapshot. Creates a new version reflecting the rollback.

- **Response**: `200 OK`
```json
{
  "message": "Restored version 1 as version 3",
  "new_version_id": 17,
  "new_version_number": 3
}
```

---

## 5. LaTeX Compilation & Downloads

### `POST /resumes/{resume_id}/compile`
Render structured data into Overleaf-compatible LaTeX and compile to PDF using sandboxed `pdflatex`.

- **Response**: `200 OK`
```json
{
  "status": "COMPILED",
  "latex_available": true,
  "message": "Resume successfully compiled to PDF",
  "latest_pdf_url": "/api/v1/storage/resumes/compiled_12.pdf",
  "latest_tex_url": "/api/v1/storage/resumes/compiled_12.tex"
}
```

### `GET /resumes/{resume_id}/download/pdf`
Stream the compiled PDF directly as binary (`application/pdf`). Requires successful compilation first.

- **Response**: `200 OK` with `Content-Type: application/pdf`

### `GET /resumes/{resume_id}/download/latex`
Stream the generated LaTeX source as text (`text/x-tex`).

- **Response**: `200 OK` with `Content-Type: text/x-tex`

---

## 6. JD-Based Tailoring Endpoints

### `POST /resume-tailoring/analyze-jd`
Analyze job description requirements without modifying the resume.

- **Request Body**:
```json
{
  "job_title": "Staff Platform Engineer",
  "company": "Stripe",
  "job_description": "We are seeking a Staff Platform Engineer with extensive Go, Kubernetes, and distributed consensus expertise...",
  "resume_id": 12
}
```
- **Response**: `200 OK` (Pydantic `TailoredResumeOutput`)

### `POST /resume-tailoring/generate`
Generate tailored resume phrasing and side-by-side diffs. Enforces zero hallucination.

- **Request Body**:
```json
{
  "resume_id": 12,
  "job_title": "Staff Platform Engineer",
  "company": "Stripe",
  "job_description": "..."
}
```
- **Response**: `200 OK`
```json
{
  "analysis": {
    "matching_skills": ["Go", "Kubernetes", "PostgreSQL"],
    "missing_requirements": ["Distributed Consensus (Raft/Paxos)"],
    "suggested_changes": [
      {
        "section": "summary",
        "original": "Full Stack Engineer with 5+ years...",
        "proposed": "Platform Engineer with 5+ years designing distributed systems...",
        "reason": "Aligns with Platform focus of the JD",
        "requires_confirmation": false
      }
    ]
  },
  "original_resume": { ... },
  "proposed_resume": { ... },
  "warnings": []
}
```

### `POST /resume-tailoring/{resume_id}/approve`
Explicitly apply tailored resume changes.

- **Request Body**:
```json
{
  "approved_resume_data": { ... },
  "create_new_resume": true,
  "new_title": "Alex Mercer - Stripe Platform Tailored",
  "change_summary": "Tailored for Stripe Staff Platform Engineer"
}
```
- **Response**: `200 OK`
```json
{
  "message": "Tailored resume created successfully",
  "resume_id": 13,
  "version_id": 18,
  "title": "Alex Mercer - Stripe Platform Tailored"
}
```
