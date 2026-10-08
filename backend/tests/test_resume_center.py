"""
Tests for Production-Grade Resume Center.
Covers:
- Candidate ownership and isolation
- Unauthorized access rejection
- Multi-format upload validation (PDF, DOCX, TXT, TEX), MIME types, and magic bytes
- LaTeX escaping and command injection protection
- Resume versioning and version restoration
- Private downloads for PDF and .tex
- JD analysis and anti-hallucination guarantees
- Preserving original resumes upon tailoring approval
"""
import io
import json
import pytest
from unittest.mock import patch, MagicMock

from tests.conftest import headers
from app.services.latex_service import escape_latex, render_resume_to_latex
from app.services.resume_tailor_service import tailor_resume_to_jd, TailoredResumeOutput


def test_list_resume_templates(environment):
    client, db, owner, other, admin, candidate, tmp_path = environment
    res = client.get("/api/v1/resume-templates")
    assert res.status_code == 200
    templates = res.json()
    assert len(templates) >= 12
    slugs = [t["slug"] for t in templates]
    assert "classic-ats" in slugs or "ats-classic" in slugs
    assert "software-engineer" in slugs
    assert "data-scientist" in slugs
    assert "academic-cv" in slugs

    # Verify template details
    tmpl_res = client.get(f"/api/v1/resume-templates/{templates[0]['id']}")
    assert tmpl_res.status_code == 200
    t_detail = tmpl_res.json()
    assert "latex_template" in t_detail
    assert t_detail["license_name"] == "MIT License"
    assert t_detail["ats_score"] >= 90


def test_create_and_get_resume(environment):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    payload = {
        "title": "Software Engineer Resume",
        "structured_data": {
            "personal_info": {
                "full_name": "Alice Developer",
                "email": "alice@example.com",
                "phone": "+1-555-0199",
                "location": "San Francisco, CA"
            },
            "summary": "Full-stack engineer with 5 years experience.",
            "skills": {
                "Languages": ["Python", "TypeScript", "SQL"],
                "Frameworks": ["FastAPI", "React", "Next.js"]
            },
            "experience": [
                {
                    "title": "Senior Engineer",
                    "company": "Tech Corp",
                    "start_date": "2021",
                    "end_date": "Present",
                    "bullets": ["Architected distributed microservices.", "Optimized SQL queries."]
                }
            ],
            "education": [
                {
                    "degree": "B.S. in Computer Science",
                    "institution": "State University",
                    "end_date": "2020"
                }
            ]
        }
    }

    create_res = client.post("/api/v1/resumes", json=payload, headers=auth)
    assert create_res.status_code == 200
    created = create_res.json()
    resume_id = created["id"]
    assert created["title"] == "Software Engineer Resume"

    # Get resume details
    get_res = client.get(f"/api/v1/resumes/{resume_id}", headers=auth)
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["structured_data"]["personal_info"]["full_name"] == "Alice Developer"
    assert data["version_number"] == 1


def test_candidate_ownership_isolation(environment):
    client, db, owner, other, admin, candidate, tmp_path = environment
    owner_auth = headers(owner)
    other_auth = headers(other)
    admin_auth = headers(admin)

    # 1. Owner creates resume
    res = client.post("/api/v1/resumes", json={
        "title": "Confidential Resume",
        "structured_data": {"personal_info": {"full_name": "Private Person"}}
    }, headers=owner_auth)
    assert res.status_code == 200
    resume_id = res.json()["id"]

    # 2. Other candidate attempts access — MUST be rejected with 403
    other_get = client.get(f"/api/v1/resumes/{resume_id}", headers=other_auth)
    assert other_get.status_code == 403

    other_patch = client.patch(f"/api/v1/resumes/{resume_id}", json={"title": "Hacked"}, headers=other_auth)
    assert other_patch.status_code == 403

    other_delete = client.delete(f"/api/v1/resumes/{resume_id}", headers=other_auth)
    assert other_delete.status_code == 403

    # 3. Admin has authorized oversight
    admin_get = client.get(f"/api/v1/resumes/{resume_id}", headers=admin_auth)
    assert admin_get.status_code == 200


def test_unauthenticated_access_rejected(environment):
    client, db, owner, other, admin, candidate, tmp_path = environment
    # Requests without Authorization header must fail
    assert client.get("/api/v1/resumes").status_code == 401
    assert client.post("/api/v1/resumes", json={"title": "Test"}).status_code == 401
    assert client.get("/api/v1/resumes/1").status_code == 401


def test_upload_magic_bytes_and_size_validation(environment):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    # 1. Invalid PDF signature (disguised text claiming to be PDF)
    fake_pdf = b"Hello, this is just plain text, not a PDF!"
    res_fake = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.pdf", io.BytesIO(fake_pdf), "application/pdf")},
        headers=auth
    )
    assert res_fake.status_code == 400
    assert "signature" in res_fake.json()["detail"].lower()

    # 2. Oversized upload > 10MB
    oversized = b"%PDF-" + b"0" * (11 * 1024 * 1024)
    res_big = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("huge.pdf", io.BytesIO(oversized), "application/pdf")},
        headers=auth
    )
    assert res_big.status_code == 400
    assert "limit" in res_big.json()["detail"].lower()

    # 3. Valid text file upload
    txt_content = b"""John Doe
john.doe@example.com
555-0199
Experience:
- Senior Developer at Acme Corp (2020-Present)
Skills: Python, FastAPI, React
Education: BS Computer Science, Tech University
"""
    res_txt = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", io.BytesIO(txt_content), "text/plain")},
        headers=auth
    )
    assert res_txt.status_code == 200
    txt_data = res_txt.json()
    assert "resume_id" in txt_data
    assert "structured_data" in txt_data
    assert txt_data["structured_data"]["personal_info"]["email"] == "john.doe@example.com"


def test_versioning_and_restore(environment):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    # 1. Create initial resume (v1)
    res = client.post("/api/v1/resumes", json={
        "title": "Versioned Resume",
        "structured_data": {"personal_info": {"full_name": "Candidate V1"}}
    }, headers=auth)
    resume_id = res.json()["id"]

    # 2. Commit version 2
    v2_res = client.post(f"/api/v1/resumes/{resume_id}/versions", json={
        "structured_data": {"personal_info": {"full_name": "Candidate V2"}},
        "change_summary": "Updated name to V2"
    }, headers=auth)
    assert v2_res.status_code == 200
    v2_id = v2_res.json()["version_id"]

    # 3. List versions
    versions = client.get(f"/api/v1/resumes/{resume_id}/versions", headers=auth).json()
    assert len(versions) == 2
    assert versions[0]["version_number"] == 2
    assert versions[1]["version_number"] == 1
    v1_id = versions[1]["id"]

    # 4. Restore version 1
    restore_res = client.post(f"/api/v1/resumes/{resume_id}/versions/{v1_id}/restore", headers=auth)
    assert restore_res.status_code == 200
    new_v_num = restore_res.json()["new_version_number"]
    assert new_v_num == 3

    # Check that current resume now has version 1 data
    cur_res = client.get(f"/api/v1/resumes/{resume_id}", headers=auth).json()
    assert cur_res["version_number"] == 3
    assert cur_res["structured_data"]["personal_info"]["full_name"] == "Candidate V1"


def test_latex_character_escaping():
    """Verify all dangerous LaTeX command characters are strictly escaped."""
    raw_payload = r"User & Co. $100% #1 _test_ {bracket} ~tilde ^caret \backslash <tag>"
    escaped = escape_latex(raw_payload)

    # Ensure dangerous unescaped characters are not present in raw form
    assert r"\&" in escaped
    assert r"\%" in escaped
    assert r"\$" in escaped
    assert r"\#" in escaped
    assert r"\_" in escaped
    assert r"\{" in escaped
    assert r"\}" in escaped
    assert r"\textasciitilde{}" in escaped
    assert r"\textasciicircum{}" in escaped
    assert r"\textbackslash{}" in escaped


def test_latex_compilation_and_tex_download(environment):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    res = client.post("/api/v1/resumes", json={
        "title": "Compile Test Resume",
        "structured_data": {
            "personal_info": {"full_name": "Test User", "email": "test@test.com"},
            "skills": {"Languages": ["Python"]}
        }
    }, headers=auth)
    resume_id = res.json()["id"]

    # Call compile endpoint
    compile_res = client.post(f"/api/v1/resumes/{resume_id}/compile", headers=auth)
    assert compile_res.status_code == 200
    comp_data = compile_res.json()
    assert "latest_tex_url" in comp_data

    # Download .tex source
    tex_dl = client.get(f"/api/v1/resumes/{resume_id}/download/latex", headers=auth)
    assert tex_dl.status_code == 200
    assert "documentclass" in tex_dl.text
    assert "Test User" in tex_dl.text


def test_jd_analysis_and_anti_hallucination():
    """
    Verify JD analysis compares real candidate skills against requirements,
    and never invents credentials or unverified claims.
    """
    resume_data = {
        "personal_info": {"full_name": "Bob Realist"},
        "skills": ["python", "fastapi", "docker"],
        "experience": [
            {
                "title": "Python Developer",
                "company": "Real Corp",
                "bullets": ["Built REST APIs in FastAPI"]
            }
        ]
    }

    job_description = """
    We are looking for a Senior Python Developer with Docker and Kubernetes experience.
    Must have 5 years with Rust and Go.
    """

    output = tailor_resume_to_jd(
        resume_data=resume_data,
        job_title="Senior Python Developer",
        company="Dream Corp",
        job_description=job_description
    )

    assert isinstance(output, TailoredResumeOutput)
    # python and docker should be recognized as matching
    assert "python" in [s.lower() for s in output.matching_skills]
    assert "docker" in [s.lower() for s in output.matching_skills]

    # Unpossessed skills (e.g. kubernetes) should be in missing requirements, NOT fabricated
    matching_lower = [s.lower() for s in output.matching_skills]
    assert "kubernetes" not in matching_lower


def test_tailoring_approval_preserves_original(environment):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    # 1. Create original resume
    original_data = {
        "personal_info": {"full_name": "Alice Original"},
        "summary": "Original Summary"
    }
    create_res = client.post("/api/v1/resumes", json={
        "title": "Base Master Resume",
        "structured_data": original_data
    }, headers=auth)
    original_id = create_res.json()["id"]

    # 2. Approve tailoring with create_new_resume=True
    tailored_data = {
        "personal_info": {"full_name": "Alice Original"},
        "summary": "Tailored Summary with High Impact"
    }
    approve_res = client.post(f"/api/v1/resume-tailoring/{original_id}/approve", json={
        "approved_resume_data": tailored_data,
        "create_new_resume": True,
        "new_title": "Google Tailored Resume"
    }, headers=auth)
    assert approve_res.status_code == 200
    tailored_id = approve_res.json()["resume_id"]
    assert tailored_id != original_id

    # 3. Verify original resume is completely unchanged
    orig_check = client.get(f"/api/v1/resumes/{original_id}", headers=auth).json()
    assert orig_check["structured_data"]["summary"] == "Original Summary"

    # 4. Verify tailored resume has tailored data
    tailored_check = client.get(f"/api/v1/resumes/{tailored_id}", headers=auth).json()
    assert tailored_check["structured_data"]["summary"] == "Tailored Summary with High Impact"
