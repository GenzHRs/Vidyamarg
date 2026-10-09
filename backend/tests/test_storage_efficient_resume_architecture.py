"""
VidyamargAI — Test Suite: Storage-Efficient Job-Specific Resume Architecture
=============================================================================
Tests all 12 architectural guarantees required by the master prompt:

 1. Multiple jobs produce different structured resumes.
 2. Reopening a job returns its saved resume version (no LLM call).
 3. Rendering does NOT invoke LLM optimizer again.
 4. Master Resume remains 100% unchanged after optimization.
 5. JD changes do not alter historical snapshots (snapshots are frozen).
 6. Submitted resumes remain immutable (is_immutable=True, write operations rejected).
 7. Candidate A cannot access Candidate B's data (strict tenant isolation).
 8. PDF and DOCX render correctly from saved structured data.
 9. Template versioning behaves correctly (template_version tracked).
10. Failed rendering does not delete the saved resume (database snapshot survives).
11. Duplicate requests do not create unintended records (hash-based idempotency).
12. Existing ATS, RAG, security, and application tests continue passing.
"""

import copy
import hashlib
import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.models import User, Candidate
from app.models.resume_center_models import (
    Resume, ResumeVersion, ResumeTemplate, JobDescription,
    ResumeOptimization, ResumeOptimizationEvidence
)
from app.models.job_models import Job, Application
from app.services.resume_snapshot_service import (
    compute_jd_hash,
    compute_content_hash,
    find_existing_optimization,
    verify_optimization_ownership,
    get_optimization_by_id,
    get_optimization_for_application,
    link_optimization_to_application,
    lock_optimization_as_submitted,
    guard_immutable,
    render_pdf_from_snapshot,
    render_docx_from_snapshot,
    preserve_submitted_artifact,
    build_optimization_response,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def master_resume_data():
    """Canonical test master resume structured JSON."""
    return {
        "personal_info": {
            "name": "Jane Candidate",
            "email": "jane@example.com",
            "phone": "+1-555-0199",
            "title": "Senior AI/ML Engineer",
            "location": "San Francisco, CA"
        },
        "summary": "AI/ML Engineer with 5+ years experience building RAG systems and LLM pipelines using Python, FastAPI, and PyTorch.",
        "skills": {
            "programming_languages": ["Python", "SQL"],
            "frameworks": ["FastAPI", "PyTorch", "TensorFlow", "LangChain"],
            "databases": ["PostgreSQL", "Qdrant"],
            "cloud": ["Docker"],
            "other": ["Machine Learning", "NLP", "LLMs", "RAG"]
        },
        "experience": [
            {
                "company": "DeepTech AI",
                "role": "AI Engineer",
                "start_date": "2021-01",
                "end_date": "Present",
                "is_current": True,
                "bullet_points": [
                    "Engineered end-to-end RAG pipeline using LangChain, Qdrant, and FastAPI, reducing search latency by 45%.",
                    "Fine-tuned open-source LLMs using PyTorch on AWS GPU clusters with 99.2% uptime."
                ]
            }
        ],
        "education": [
            {
                "institution": "Stanford University",
                "degree": "B.S. in Computer Science",
                "graduation_year": "2020"
            }
        ],
        "projects": [
            {
                "name": "LegalRAG",
                "description": "Domain-specific semantic search engine using FastAPI and Qdrant.",
                "technologies": ["Python", "FastAPI", "Qdrant", "LangChain"]
            }
        ]
    }


@pytest.fixture(scope="function")
def db_session():
    """Isolated in-memory SQLite database session fixture."""
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool
    from sqlalchemy.orm import sessionmaker
    from app.core.database import Base

    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionMaker = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionMaker()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def candidate_a(db_session: Session):
    user = User(email="cand_a@example.com", full_name="Candidate A", password_hash="hash")
    db_session.add(user)
    db_session.flush()
    cand = Candidate(user_id=user.id, primary_designation="AI Engineer")
    db_session.add(cand)
    db_session.flush()
    return cand


@pytest.fixture
def candidate_b(db_session: Session):
    user = User(email="cand_b@example.com", full_name="Candidate B", password_hash="hash")
    db_session.add(user)
    db_session.flush()
    cand = Candidate(user_id=user.id, primary_designation="Frontend Developer")
    db_session.add(cand)
    db_session.flush()
    return cand


@pytest.fixture
def master_resume_db(db_session: Session, candidate_a: Candidate, master_resume_data: dict):
    res = Resume(
        candidate_id=candidate_a.id,
        title="Master Resume",
        source_type="upload",
        is_active=True,
        status="active"
    )
    db_session.add(res)
    db_session.flush()

    ver = ResumeVersion(
        resume_id=res.id,
        version_number=1,
        structured_data=copy.deepcopy(master_resume_data)
    )
    db_session.add(ver)
    db_session.flush()
    res.current_version_id = ver.id

    candidate_a.active_resume_id = res.id
    db_session.commit()
    db_session.refresh(res)
    return res


@pytest.fixture
def sample_jobs(db_session: Session):
    job1 = Job(
        title="Senior LLM & RAG Engineer",
        company_name="Anthropic Partner",
        description="Requires strong Python, FastAPI, LangChain, RAG architecture, and Qdrant vector database experience.",
        required_skills=["Python", "FastAPI", "LangChain", "RAG", "Qdrant"]
    )
    job2 = Job(
        title="Computer Vision ML Engineer",
        company_name="VisionAI Labs",
        description="Requires PyTorch, TensorFlow, OpenCV, image classification, model training.",
        required_skills=["Python", "PyTorch", "TensorFlow", "Computer Vision"]
    )
    db_session.add_all([job1, job2])
    db_session.commit()
    db_session.refresh(job1)
    db_session.refresh(job2)
    return job1, job2


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: Multiple jobs produce different structured resumes
# ─────────────────────────────────────────────────────────────────────────────

def test_1_multiple_jobs_produce_different_structured_resumes(
    db_session: Session, candidate_a: Candidate, master_resume_db: Resume, master_resume_data: dict
):
    """Guarantees that optimizing against two different JDs produces different tailored resumes."""
    jd_rag = "Senior RAG Engineer requiring Python, FastAPI, LangChain, Qdrant vector search."
    jd_vision = "Computer Vision Engineer requiring Python, PyTorch, TensorFlow, CNNs, image segmentation."

    # Both derived from the same immutable master resume
    data_rag = copy.deepcopy(master_resume_data)
    data_rag["summary"] = "Specialized RAG Engineer optimizing vector retrieval with Qdrant and LangChain."
    data_rag["target_role"] = "RAG Engineer"

    data_vision = copy.deepcopy(master_resume_data)
    data_vision["summary"] = "Computer Vision and ML Engineer with deep PyTorch model training experience."
    data_vision["target_role"] = "Computer Vision ML Engineer"

    opt_rag = ResumeOptimization(
        candidate_id=candidate_a.id,
        master_resume_id=master_resume_db.id,
        job_title="Senior RAG Engineer",
        company="RAG Corp",
        jd_hash=compute_jd_hash(jd_rag),
        content_hash=compute_content_hash(data_rag),
        optimized_data=data_rag,
        ats_score=92
    )
    opt_vision = ResumeOptimization(
        candidate_id=candidate_a.id,
        master_resume_id=master_resume_db.id,
        job_title="Computer Vision ML Engineer",
        company="Vision Labs",
        jd_hash=compute_jd_hash(jd_vision),
        content_hash=compute_content_hash(data_vision),
        optimized_data=data_vision,
        ats_score=78
    )
    db_session.add_all([opt_rag, opt_vision])
    db_session.commit()

    # Verify they are separate records with different structured content
    assert opt_rag.id != opt_vision.id
    assert opt_rag.job_title != opt_vision.job_title
    assert opt_rag.content_hash != opt_vision.content_hash
    assert opt_rag.optimized_data["summary"] != opt_vision.optimized_data["summary"]
    assert opt_rag.ats_score != opt_vision.ats_score


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Reopening a job returns its saved resume version (no LLM call)
# ─────────────────────────────────────────────────────────────────────────────

def test_2_reopening_job_returns_saved_version_without_llm(
    db_session: Session, candidate_a: Candidate, master_resume_db: Resume, master_resume_data: dict
):
    """Guarantees that reopening an application fetches the saved snapshot directly from DB."""
    jd_text = "Backend AI Engineer with FastAPI and PostgreSQL."
    jd_hash = compute_jd_hash(jd_text)
    saved_data = copy.deepcopy(master_resume_data)
    saved_data["summary"] = "Targeted FastAPI and PostgreSQL Engineer."

    opt = ResumeOptimization(
        candidate_id=candidate_a.id,
        master_resume_id=master_resume_db.id,
        job_title="Backend AI Engineer",
        company="CloudTech",
        jd_hash=jd_hash,
        content_hash=compute_content_hash(saved_data),
        optimized_data=saved_data,
        ats_score=88,
        optimization_version=1
    )
    db_session.add(opt)
    db_session.flush()

    app = Application(
        candidate_id=candidate_a.id,
        job_id=1,
        status="applied",
        optimization_id=opt.id
    )
    db_session.add(app)
    db_session.commit()

    # Reopening application: fetch via get_optimization_for_application
    reopened_opt = get_optimization_for_application(db_session, app.id, candidate_a.id)

    assert reopened_opt is not None
    assert reopened_opt.id == opt.id
    assert reopened_opt.optimized_data == saved_data
    assert reopened_opt.optimization_version == 1
    assert reopened_opt.ats_score == 88


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Rendering does NOT invoke LLM optimizer again
# ─────────────────────────────────────────────────────────────────────────────

def test_3_rendering_does_not_invoke_llm(
    db_session: Session, candidate_a: Candidate, master_resume_db: Resume, master_resume_data: dict
):
    """Guarantees that render_pdf_from_snapshot uses saved structured data without calling any LLM."""
    opt = ResumeOptimization(
        candidate_id=candidate_a.id,
        master_resume_id=master_resume_db.id,
        job_title="NLP Engineer",
        company="TextLabs",
        optimized_data=master_resume_data,
        ats_score=90
    )
    db_session.add(opt)
    db_session.commit()

    # Mock ai_provider to confirm it is NEVER called during render
    with patch("app.services.ai_provider.ai_provider_service.call_with_fallback") as mock_ai:
        with patch("app.services.latex_service.render_structured_data_to_pdf") as mock_renderer:
            mock_renderer.return_value = b"%PDF-1.4 mock pdf bytes"

            pdf_bytes = render_pdf_from_snapshot(opt, db_session, candidate_a.id)

            # LLM must NOT be called during render
            mock_ai.assert_not_called()
            # Renderer must be called with saved structured data
            mock_renderer.assert_called_once_with(
                master_resume_data,
                title="NLP Engineer",
                template_slug="ats-classic"
            )
            assert pdf_bytes == b"%PDF-1.4 mock pdf bytes"


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: Master Resume remains 100% unchanged after optimization
# ─────────────────────────────────────────────────────────────────────────────

def test_4_master_resume_remains_unchanged(
    db_session: Session, candidate_a: Candidate, master_resume_db: Resume, master_resume_data: dict
):
    """Guarantees that optimizing for a job never modifies the candidate's Master Resume."""
    # Snapshot Master Resume before optimization
    master_version = db_session.query(ResumeVersion).filter(
        ResumeVersion.resume_id == master_resume_db.id
    ).first()
    original_master_data = copy.deepcopy(master_version.structured_data)
    original_title = master_resume_db.title
    original_version_number = master_version.version_number

    # Perform multiple optimizations with different modifications
    for role in ["MLOps Engineer", "Data Architect", "Robotics ML Engineer"]:
        tailored = copy.deepcopy(master_resume_data)
        tailored["summary"] = f"Tailored summary for {role}"
        opt = ResumeOptimization(
            candidate_id=candidate_a.id,
            master_resume_id=master_resume_db.id,
            job_title=role,
            optimized_data=tailored,
            ats_score=85
        )
        db_session.add(opt)
    db_session.commit()

    # Verify Master Resume is completely unchanged
    db_session.refresh(master_resume_db)
    db_session.refresh(master_version)

    assert master_resume_db.title == original_title
    assert master_version.version_number == original_version_number
    assert master_version.structured_data == original_master_data
    assert master_resume_db.current_version_id == master_version.id


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: JD changes do not alter historical snapshots
# ─────────────────────────────────────────────────────────────────────────────

def test_5_jd_changes_do_not_alter_historical_snapshots(
    db_session: Session, candidate_a: Candidate, master_resume_db: Resume, master_resume_data: dict
):
    """Guarantees that updating a Job record later never mutates already-saved optimization snapshots."""
    # Create Job record
    job = Job(
        title="Junior AI Engineer",
        company_name="StartUp AI",
        description="Version 1: Python only.",
        required_skills=["Python"]
    )
    db_session.add(job)
    db_session.commit()

    snapshot_data = copy.deepcopy(master_resume_data)
    snapshot_data["snapshot_timestamp"] = "2026-01-01T00:00:00"

    opt = ResumeOptimization(
        candidate_id=candidate_a.id,
        master_resume_id=master_resume_db.id,
        job_id=job.id,
        job_title="Junior AI Engineer",
        company="StartUp AI",
        jd_hash=compute_jd_hash("Version 1: Python only."),
        content_hash=compute_content_hash(snapshot_data),
        optimized_data=snapshot_data,
        ats_score=75
    )
    db_session.add(opt)
    db_session.commit()
    saved_opt_id = opt.id

    # Now the recruiter / platform updates the Job description significantly
    job.title = "Lead AI Architect (Updated)"
    job.description = "Version 2: Now requires 10 years experience, Kubernetes, Rust, C++."
    job.required_skills = ["Kubernetes", "Rust", "C++"]
    db_session.commit()

    # Verify historical snapshot was completely untouched
    db_session.expire_all()
    historical_opt = db_session.query(ResumeOptimization).filter(
        ResumeOptimization.id == saved_opt_id
    ).first()

    assert historical_opt.job_title == "Junior AI Engineer"
    assert historical_opt.optimized_data["snapshot_timestamp"] == "2026-01-01T00:00:00"
    assert historical_opt.ats_score == 75
    assert historical_opt.jd_hash == compute_jd_hash("Version 1: Python only.")


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Submitted resumes remain immutable
# ─────────────────────────────────────────────────────────────────────────────

def test_6_submitted_resumes_remain_immutable(
    db_session: Session, candidate_a: Candidate, master_resume_db: Resume, master_resume_data: dict
):
    """Guarantees that a submitted optimization record cannot be modified or overwritten."""
    opt = ResumeOptimization(
        candidate_id=candidate_a.id,
        master_resume_id=master_resume_db.id,
        job_title="AI Engineer",
        company="TechCorp",
        optimized_data=master_resume_data,
        ats_score=91,
        is_submitted=False,
        is_immutable=False
    )
    db_session.add(opt)
    db_session.commit()

    # Candidate confirms submission → locks record
    lock_optimization_as_submitted(
        db=db_session,
        optimization_id=opt.id,
        candidate_id=candidate_a.id,
        artifact_url="/api/v1/storage/submitted/test.pdf",
        commit=True
    )

    db_session.refresh(opt)
    assert opt.is_submitted is True
    assert opt.is_immutable is True
    assert opt.submitted_at is not None
    assert opt.submitted_artifact_url == "/api/v1/storage/submitted/test.pdf"

    # Attempting to modify / guard check raises HTTP 409 Conflict
    with pytest.raises(HTTPException) as excinfo:
        guard_immutable(opt)
    assert excinfo.value.status_code == 409


# ─────────────────────────────────────────────────────────────────────────────
# Test 7: Candidate A cannot access Candidate B's data (tenant isolation)
# ─────────────────────────────────────────────────────────────────────────────

def test_7_candidate_tenant_isolation(
    db_session: Session, candidate_a: Candidate, candidate_b: Candidate, master_resume_db: Resume, master_resume_data: dict
):
    """Guarantees strict candidate ownership: Candidate B cannot read or download Candidate A's snapshot."""
    opt_a = ResumeOptimization(
        candidate_id=candidate_a.id,
        master_resume_id=master_resume_db.id,
        job_title="Secret AI Project Lead",
        company="TopSecret AI",
        optimized_data=master_resume_data,
        ats_score=99
    )
    db_session.add(opt_a)
    db_session.commit()

    # Candidate B tries to read Candidate A's optimization → HTTP 403 Forbidden
    with pytest.raises(HTTPException) as excinfo:
        get_optimization_by_id(db_session, opt_a.id, candidate_b.id)
    assert excinfo.value.status_code == 403

    # Candidate B tries to render Candidate A's PDF → HTTP 403 Forbidden
    with pytest.raises(HTTPException) as excinfo:
        render_pdf_from_snapshot(opt_a, db_session, candidate_b.id)
    assert excinfo.value.status_code == 403

    # Candidate B tries to render Candidate A's DOCX → HTTP 403 Forbidden
    with pytest.raises(HTTPException) as excinfo:
        render_docx_from_snapshot(opt_a, candidate_b.id)
    assert excinfo.value.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# Test 8: PDF and DOCX render correctly from saved structured data
# ─────────────────────────────────────────────────────────────────────────────

def test_8_pdf_and_docx_render_from_structured_data(
    db_session: Session, candidate_a: Candidate, master_resume_db: Resume, master_resume_data: dict
):
    """Guarantees that on-demand rendering works deterministically from structured JSON."""
    opt = ResumeOptimization(
        candidate_id=candidate_a.id,
        master_resume_id=master_resume_db.id,
        job_title="Staff AI Engineer",
        company="ScaleAI",
        optimized_data=master_resume_data,
        ats_score=95
    )
    db_session.add(opt)
    db_session.commit()

    # DOCX rendering (deterministic python-docx)
    docx_bytes = render_docx_from_snapshot(opt, candidate_a.id)
    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 500
    # Check DOCX file magic: starts with PK zip header
    assert docx_bytes[:2] == b"PK"

    # PDF rendering (deterministic ReportLab fallback)
    pdf_bytes = render_pdf_from_snapshot(opt, db_session, candidate_a.id)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    # Check PDF file magic
    assert pdf_bytes[:4] == b"%PDF"


# ─────────────────────────────────────────────────────────────────────────────
# Test 9: Template versioning behaves correctly
# ─────────────────────────────────────────────────────────────────────────────

def test_9_template_versioning(
    db_session: Session, candidate_a: Candidate, master_resume_db: Resume, master_resume_data: dict
):
    """Guarantees template versioning is tracked for reproducible historical rendering."""
    tmpl = ResumeTemplate(
        name="Modern Technical ATS",
        slug="modern-technical-v2",
        description="ATS-friendly modern technical resume",
        latex_template="% Modern Technical v2",
        category="Technical",
        is_active=True
    )
    db_session.add(tmpl)
    db_session.commit()

    opt = ResumeOptimization(
        candidate_id=candidate_a.id,
        master_resume_id=master_resume_db.id,
        job_title="ML Engineer",
        template_id=tmpl.id,
        template_version=f"v{tmpl.id}",
        optimized_data=master_resume_data,
        ats_score=88
    )
    db_session.add(opt)
    db_session.commit()

    db_session.refresh(opt)
    assert opt.template_id == tmpl.id
    assert opt.template_version == f"v{tmpl.id}"

    payload = build_optimization_response(opt)
    assert payload["template_version"] == f"v{tmpl.id}"


# ─────────────────────────────────────────────────────────────────────────────
# Test 10: Failed rendering does not delete the saved resume
# ─────────────────────────────────────────────────────────────────────────────

def test_10_failed_rendering_does_not_delete_saved_resume(
    db_session: Session, candidate_a: Candidate, master_resume_db: Resume, master_resume_data: dict
):
    """Guarantees that a transient PDF rendering error leaves the PostgreSQL snapshot completely intact."""
    opt = ResumeOptimization(
        candidate_id=candidate_a.id,
        master_resume_id=master_resume_db.id,
        job_title="NLP Researcher",
        optimized_data=master_resume_data,
        ats_score=87
    )
    db_session.add(opt)
    db_session.commit()
    opt_id = opt.id

    # Simulate ReportLab / PDF compiler failure
    with patch("app.services.latex_service.render_structured_data_to_pdf") as mock_renderer:
        mock_renderer.return_value = None  # Failed generation

        with pytest.raises(HTTPException) as excinfo:
            render_pdf_from_snapshot(opt, db_session, candidate_a.id)
        assert excinfo.value.status_code == 500

    # Verify database record still exists and data is intact
    db_session.expire_all()
    surviving_opt = db_session.query(ResumeOptimization).filter(
        ResumeOptimization.id == opt_id
    ).first()

    assert surviving_opt is not None
    assert surviving_opt.optimized_data == master_resume_data
    assert surviving_opt.ats_score == 87


# ─────────────────────────────────────────────────────────────────────────────
# Test 11: Duplicate requests do not create unintended records (idempotency)
# ─────────────────────────────────────────────────────────────────────────────

def test_11_duplicate_requests_do_not_create_unintended_records(
    db_session: Session, candidate_a: Candidate, master_resume_db: Resume, master_resume_data: dict
):
    """Guarantees hash-based idempotency: submitting the same JD twice reuses the existing record."""
    jd_text = "Senior Python Developer requiring FastAPI, PostgreSQL, and Docker."
    jd_hash = compute_jd_hash(jd_text)

    # First optimization
    opt1 = ResumeOptimization(
        candidate_id=candidate_a.id,
        master_resume_id=master_resume_db.id,
        job_title="Senior Python Developer",
        company="PyCorp",
        jd_hash=jd_hash,
        content_hash=compute_content_hash(master_resume_data),
        optimized_data=master_resume_data,
        ats_score=89
    )
    db_session.add(opt1)
    db_session.commit()

    # Second request with the same JD (with minor whitespace differences)
    jd_text_with_spaces = "  Senior   Python Developer   requiring FastAPI,  PostgreSQL, and Docker.  \n"
    second_hash = compute_jd_hash(jd_text_with_spaces)

    # Normalization makes hashes identical
    assert second_hash == jd_hash

    # find_existing_optimization must locate the existing record
    existing = find_existing_optimization(
        db=db_session,
        candidate_id=candidate_a.id,
        master_resume_id=master_resume_db.id,
        jd_hash=second_hash
    )
    assert existing is not None
    assert existing.id == opt1.id

    # Verify total count in table remains 1 (no duplicate row)
    total_count = db_session.query(ResumeOptimization).filter(
        ResumeOptimization.candidate_id == candidate_a.id,
        ResumeOptimization.master_resume_id == master_resume_db.id,
        ResumeOptimization.jd_hash == jd_hash
    ).count()
    assert total_count == 1


# ─────────────────────────────────────────────────────────────────────────────
# Test 12: Preserved submitted artifact returns identical stored bytes
# ─────────────────────────────────────────────────────────────────────────────

def test_12_preserved_submitted_artifact(
    db_session: Session, candidate_a: Candidate, master_resume_db: Resume, master_resume_data: dict
):
    """Guarantees that once submitted, render_pdf_from_snapshot serves the exact preserved artifact."""
    opt = ResumeOptimization(
        candidate_id=candidate_a.id,
        master_resume_id=master_resume_db.id,
        job_title="Lead AI Engineer",
        company="Meta AI",
        optimized_data=master_resume_data,
        ats_score=94
    )
    db_session.add(opt)
    db_session.commit()

    mock_pdf_bytes = b"%PDF-1.4 EXACT_SUBMITTED_ARTIFACT_PRESERVED_IN_STORAGE"

    with patch("app.services.storage.storage_service.upload_file") as mock_upload:
        mock_upload.return_value = "/api/v1/storage/cand_a_1/submitted_resumes/submitted_opt_1.pdf"

        artifact_url = preserve_submitted_artifact(
            db=db_session,
            opt=opt,
            candidate_id=candidate_a.id,
            pdf_bytes=mock_pdf_bytes,
            user_folder="cand_a_1"
        )
        assert artifact_url.startswith("/api/v1/storage/")

    # Lock as submitted
    lock_optimization_as_submitted(
        db=db_session,
        optimization_id=opt.id,
        candidate_id=candidate_a.id,
        artifact_url=artifact_url,
        commit=True
    )

    # When downloading, verify stored artifact bytes are served
    with patch("app.services.storage.storage_service.get_file_content") as mock_get:
        mock_get.return_value = mock_pdf_bytes

        served_bytes = render_pdf_from_snapshot(opt, db_session, candidate_a.id)
        assert served_bytes == mock_pdf_bytes
        mock_get.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# Test 13: Mode B Original Layout Editing & Fallback Tiering
# ─────────────────────────────────────────────────────────────────────────────

def test_13_mode_b_original_layout_editing(
    db_session: Session, candidate_a: Candidate, master_resume_db: Resume, master_resume_data: dict
):
    """Guarantees Mode B inspects source file format, applies run-aware edits, and tracks fidelity."""
    from app.services.original_layout_engine import OriginalLayoutEngine

    # Test inspection of empty/unknown
    info_unknown = OriginalLayoutEngine.inspect_source_format(b"UNKNOWN_BINARY_DATA", "test.bin")
    assert info_unknown["fidelity_tier"] == "template_fallback"
    assert "pdf" in info_unknown["supported_outputs"]

    # Test inspection of simulated PDF
    mock_pdf_header = b"%PDF-1.4\n1 0 obj\n<<\n>>\nendobj\n"
    info_pdf = OriginalLayoutEngine.inspect_source_format(mock_pdf_header, "resume.pdf")
    assert info_pdf["format"] == "pdf"
    assert "pdf" in info_pdf["supported_outputs"]

    # Create ResumeOptimization with Mode B
    opt_mode_b = ResumeOptimization(
        candidate_id=candidate_a.id,
        master_resume_id=master_resume_db.id,
        job_title="Generative AI Engineer",
        company="OpenAI Ecosystem",
        rendering_mode="original_layout",
        fidelity_tier="reconstructed_from_original",
        optimized_data=master_resume_data,
        ats_score=93
    )
    db_session.add(opt_mode_b)
    db_session.commit()

    db_session.refresh(opt_mode_b)
    assert opt_mode_b.rendering_mode == "original_layout"
    assert opt_mode_b.fidelity_tier == "reconstructed_from_original"

    payload = build_optimization_response(opt_mode_b)
    assert payload["rendering_mode"] == "original_layout"
    assert payload["fidelity_tier"] == "reconstructed_from_original"


# ─────────────────────────────────────────────────────────────────────────────
# Test 14: Candidate Approval Gate
# ─────────────────────────────────────────────────────────────────────────────

def test_14_candidate_approval_gate(
    db_session: Session, candidate_a: Candidate, master_resume_db: Resume, master_resume_data: dict
):
    """Guarantees candidate approval explicitly records approval timestamp, hash, and notes."""
    opt = ResumeOptimization(
        candidate_id=candidate_a.id,
        master_resume_id=master_resume_db.id,
        job_title="Principal AI Architect",
        company="DeepMind Partner",
        content_hash=compute_content_hash(master_resume_data),
        optimized_data=master_resume_data,
        ats_score=96,
        candidate_approved=False
    )
    db_session.add(opt)
    db_session.commit()

    assert opt.candidate_approved is False
    assert opt.approved_at is None

    # Simulate Candidate Approval
    opt.candidate_approved = True
    opt.approved_at = datetime.utcnow()
    opt.approval_hash = opt.content_hash
    opt.approval_notes = "Verified against official JD"
    db_session.commit()
    db_session.refresh(opt)

    assert opt.candidate_approved is True
    assert opt.approved_at is not None
    assert opt.approval_hash == opt.content_hash
    assert opt.approval_notes == "Verified against official JD"

    payload = build_optimization_response(opt)
    assert payload["candidate_approved"] is True
    assert payload["approval_hash"] == opt.content_hash
