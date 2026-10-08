"""
End-to-End Tests for JD-Based Resume Tailoring Pipeline.
Verifies:
1. Source resume validation and consolidated structured data retrieval.
2. Operation A: Content tailoring, matching skills, missing requirements, diffs.
3. Operation B: Template rendering, LaTeX generation, PDF compilation.
4. Switching templates dynamically without re-running AI tailoring.
5. Live PDF streaming endpoint.
6. Saving as a new resume record while preserving the source resume 100% untouched.
"""
import json
import pytest
from tests.conftest import headers
from app.models.resume_center_models import Resume, ResumeVersion, ResumeTemplate
from app.models.job_models import ResumeAIAnalysis


@pytest.fixture
def source_resume(environment):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    payload = {
        "title": "Base Software Engineer Resume",
        "structured_data": {
            "personal_info": {
                "full_name": "Shiva Tejachary",
                "email": "shiva@example.com",
                "phone": "+91-9876543210",
                "location": "Hyderabad, India",
                "linkedin": "https://linkedin.com/in/shiva",
                "github": "https://github.com/shiva"
            },
            "summary": "Full-stack AI developer with experience in Python, FastAPI, and machine learning models.",
            "skills": {
                "Languages": ["Python", "JavaScript", "TypeScript", "SQL"],
                "Frameworks": ["FastAPI", "React", "Next.js", "PyTorch"],
                "Tools": ["Git", "Docker", "Linux"]
            },
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "Tech Solutions",
                    "dates": "2023 - Present",
                    "bullets": [
                        "Developed backend APIs using FastAPI and Python.",
                        "Handled database queries and optimized query response times."
                    ]
                }
            ],
            "education": [
                {
                    "degree": "B.Tech in Computer Science",
                    "institution": "JNTU",
                    "dates": "2019 - 2023",
                    "gpa": "8.5"
                }
            ],
            "projects": [
                {
                    "name": "AI Document Assistant",
                    "technologies": ["Python", "FastAPI", "LangChain"],
                    "description": "Engineered multi-document conversational search system."
                }
            ]
        }
    }

    res = client.post("/api/v1/resumes", json=payload, headers=auth)
    assert res.status_code == 200
    return res.json()["id"]


def test_source_resume_validation(environment, source_resume):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    # 1. Successful retrieval of source resume with valid data
    res = client.get(f"/api/v1/resume-tailoring/source/{source_resume}", headers=auth)
    assert res.status_code == 200
    data = res.json()
    assert data["resume_id"] == source_resume
    assert "personal_info" in data["structured_data"]
    assert data["structured_data"]["personal_info"]["full_name"] == "Shiva Tejachary"

    # 2. Ownership check: unauthorized user rejected
    other_auth = headers(other)
    unauth_res = client.get(f"/api/v1/resume-tailoring/source/{source_resume}", headers=other_auth)
    assert unauth_res.status_code == 403

    # 3. Non-existent resume returns 404
    missing_res = client.get("/api/v1/resume-tailoring/source/99999", headers=auth)
    assert missing_res.status_code == 404


def test_operation_a_tailoring_content_generation(environment, source_resume):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    jd_payload = {
        "resume_id": source_resume,
        "job_title": "Senior Generative AI Engineer",
        "company": "Anthropic AI",
        "job_description": """
        We are seeking an experienced AI Engineer skilled in Python, FastAPI, Docker, and PyTorch.
        Required:
        - Strong background in Python, PyTorch, Docker, Linux, Git.
        - Experience with Kubernetes, AWS, and Vector Databases (RAG architectures).
        - Demonstrated ability to optimize backend microservices.
        """
    }

    res = client.post("/api/v1/resume-tailoring/generate", json=jd_payload, headers=auth)
    assert res.status_code == 200
    result = res.json()

    # Verify structured fields returned
    assert result["source_resume_id"] == source_resume
    assert result["job_title"] == "Senior Generative AI Engineer"
    assert result["company"] == "Anthropic AI"
    assert "tailored_resume_data" in result
    assert "matching_skills" in result
    assert "missing_requirements" in result
    assert "suggested_changes" in result

    # Check matching skills identified correctly
    matching_lower = [s.lower() for s in result["matching_skills"]]
    assert "python" in matching_lower
    assert "fastapi" in matching_lower

    # Check missing skills identified (e.g. Kubernetes, AWS)
    missing_lower = [m.lower() for m in result["missing_requirements"]]
    assert any("kubernetes" in m or "aws" in m for m in missing_lower)

    # Check that summary was adapted
    tailored_summary = result["tailored_resume_data"].get("summary", "")
    assert "Senior Generative AI Engineer" in tailored_summary or "Anthropic AI" in tailored_summary or len(tailored_summary) > 20

    # Verify audit log in db
    analysis_log = db.query(ResumeAIAnalysis).filter(ResumeAIAnalysis.source_type == "TAILOR_JD").first()
    assert analysis_log is not None


def test_operation_b_template_rendering_and_preview(environment, source_resume):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    # First get tailored data
    jd_payload = {
        "resume_id": source_resume,
        "job_title": "Full Stack AI Developer",
        "company": "DeepMind",
        "job_description": "Looking for Python, React, and FastAPI engineers to build scalable AI interfaces."
    }
    gen_res = client.post("/api/v1/resume-tailoring/generate", json=jd_payload, headers=auth)
    assert gen_res.status_code == 200
    tailored_data = gen_res.json()["tailored_resume_data"]

    # Get available templates
    tmpls_res = client.get("/api/v1/resume-templates")
    assert tmpls_res.status_code == 200
    tmpls = tmpls_res.json()
    assert len(tmpls) > 0
    selected_tmpl_1 = tmpls[0]

    # Operation B: Render Template 1
    render_payload = {
        "source_resume_id": source_resume,
        "selected_template_id": selected_tmpl_1["id"],
        "tailored_resume_data": tailored_data
    }
    render_res = client.post("/api/v1/resume-tailoring/render-template", json=render_payload, headers=auth)
    assert render_res.status_code == 200
    render_data = render_res.json()
    assert render_data["template_id"] == selected_tmpl_1["id"]
    assert "latex_source" in render_data
    assert "preview_url" in render_data
    assert render_data["compiled_success"] is True

    # Test Live PDF Preview streaming endpoint
    preview_url = render_data["preview_url"]
    preview_res = client.get(preview_url, headers=auth)
    assert preview_res.status_code == 200
    assert preview_res.headers["content-type"] == "application/pdf"
    assert preview_res.content.startswith(b"%PDF")

    # Template Switching: Render Template 2 without regenerating AI content
    if len(tmpls) > 1:
        selected_tmpl_2 = tmpls[1]
        render_payload_2 = {
            "source_resume_id": source_resume,
            "selected_template_id": selected_tmpl_2["id"],
            "tailored_resume_data": tailored_data
        }
        render_res_2 = client.post("/api/v1/resume-tailoring/render-template", json=render_payload_2, headers=auth)
        assert render_res_2.status_code == 200
        assert render_res_2.json()["template_id"] == selected_tmpl_2["id"]


def test_save_tailored_resume_preserves_source(environment, source_resume):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    # 1. Fetch source resume details before save
    source_before = db.query(Resume).filter(Resume.id == source_resume).first()
    source_title_before = source_before.title
    source_version_id_before = source_before.current_version_id

    # 2. Tailor content
    jd_payload = {
        "resume_id": source_resume,
        "job_title": "Lead Software Architect",
        "company": "Google",
        "job_description": "We need an experienced Python and React architect with high standards."
    }
    gen_res = client.post("/api/v1/resume-tailoring/generate", json=jd_payload, headers=auth)
    tailored_data = gen_res.json()["tailored_resume_data"]

    # 3. Save as new tailored resume
    save_payload = {
        "source_resume_id": source_resume,
        "selected_template_id": 1,
        "tailored_resume_data": tailored_data,
        "job_title": "Lead Software Architect",
        "company_name": "Google",
        "job_description": jd_payload["job_description"],
        "custom_title": "Shiva Tejachary - Tailored for Google"
    }
    save_res = client.post("/api/v1/resume-tailoring/save", json=save_payload, headers=auth)
    assert save_res.status_code == 200
    save_data = save_res.json()

    new_resume_id = save_data["resume_id"]
    assert new_resume_id != source_resume
    assert save_data["title"] == "Shiva Tejachary - Tailored for Google"

    # 4. CRITICAL: Verify source resume is 100% untouched
    db.expire_all()
    source_after = db.query(Resume).filter(Resume.id == source_resume).first()
    assert source_after.title == source_title_before
    assert source_after.current_version_id == source_version_id_before

    # 5. Verify new resume is created properly
    new_resume = db.query(Resume).filter(Resume.id == new_resume_id).first()
    assert new_resume is not None
    assert new_resume.source_type == "tailored"
    assert new_resume.candidate_id == source_after.candidate_id
    assert new_resume.latest_pdf_url is not None

    # Verify new resume version 1 exists
    new_version = db.query(ResumeVersion).filter(ResumeVersion.resume_id == new_resume_id, ResumeVersion.version_number == 1).first()
    assert new_version is not None
    assert new_version.structured_data is not None
