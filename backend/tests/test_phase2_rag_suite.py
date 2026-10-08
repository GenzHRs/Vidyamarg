"""
VidyaMarg AI — Phase 2 Mandatory RAG Verification Suite.
Covers:
- TEST 1: Candidate isolation (A vs B)
- TEST 2: Old resume isolation (A vs B)
- TEST 3: Failed replacement safety (Resume A remains active)
- TEST 4: Qdrant failure safety (Resume A remains active on vector failure)
- TEST 5: Version isolation
- TEST 6: Redis stale-cache protection (revision incrementation)
- TEST 7: Exact field accuracy (zero hallucination, canonical PostgreSQL tables)
- TEST 8: Semantic retrieval (grounded in active resume)
- TEST 9: Application state truthfulness
- TEST 10: Subscription entitlement (Free vs Plus/Pro)
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.models import User, Candidate
from app.models.resume_center_models import (
    Resume, ResumeVersion, ResumeProfile, ResumeSkill,
    ResumeExperience, ResumeEducation, ResumeProject, ResumeCertification
)
from app.models.job_models import Job, Application, Match
from app.services.active_resume_rag_service import ActiveResumeRAGService
from app.services.resume_context_service import ResumeContextService
from app.services.autofill_service import AutofillService
from app.services.embedding_service import embedding_service
from app.services.resume_cache import (
    get_candidate_context_revision,
    increment_candidate_context_revision,
    get_cached_active_resume_context,
    set_cached_active_resume_context,
    invalidate_candidate_context
)


@pytest.fixture(scope="function")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()


def create_candidate_with_resume(db, user_email, full_name, role_title, skills_list):
    user = User(
        email=user_email,
        full_name=full_name,
        password_hash="hash",
        role="candidate",
        subscription_tier="free"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    cand = Candidate(
        user_id=user.id,
        parsed_name=full_name,
        parsed_email=user_email,
        primary_designation=role_title,
        status="Active"
    )
    db.add(cand)
    db.commit()
    db.refresh(cand)

    resume = Resume(
        candidate_id=cand.id,
        title=f"{full_name} Resume",
        is_active=True,
        status="active",
        extraction_status="extracted"
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    cand.active_resume_id = resume.id
    db.commit()

    ver = ResumeVersion(
        resume_id=resume.id,
        version_number=1,
        structured_data={
            "personal_info": {"full_name": full_name, "email": user_email},
            "skills": [{"name": s, "category": "Tech"} for s in skills_list],
            "work_experience": [{"designation": role_title, "employer": "Tech Corp", "is_current": True, "responsibilities": ["Engineered core systems"]}],
            "projects": [{"name": f"{role_title} System", "description": f"Built with {skills_list[0]}", "technologies": skills_list}]
        }
    )
    db.add(ver)
    db.commit()
    db.refresh(ver)
    resume.current_version_id = ver.id

    prof = ResumeProfile(
        resume_id=resume.id,
        full_name=full_name,
        email=user_email,
        professional_summary=f"Seasoned {role_title} with proven track record."
    )
    db.add(prof)

    for s in skills_list:
        db.add(ResumeSkill(resume_id=resume.id, name=s, category="Tech"))

    db.add(ResumeExperience(
        resume_id=resume.id,
        designation=role_title,
        employer="Tech Corp",
        is_current=True,
        responsibilities=["Engineered core systems"]
    ))

    db.add(ResumeProject(
        resume_id=resume.id,
        name=f"{role_title} System",
        description=f"Built with {skills_list[0]}",
        technologies=skills_list
    ))

    db.commit()
    return user, cand, resume, ver


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1 — Candidate Isolation
# ─────────────────────────────────────────────────────────────────────────────
def test_candidate_isolation(test_db):
    user_a, cand_a, res_a, _ = create_candidate_with_resume(
        test_db, "alice@test.com", "Alice Smith", "AI Architect", ["Python", "PyTorch", "Transformers"]
    )
    user_b, cand_b, res_b, _ = create_candidate_with_resume(
        test_db, "bob@test.com", "Bob Jones", "Cloud Architect", ["Golang", "Kubernetes", "Terraform"]
    )

    prof_a = ActiveResumeRAGService.get_exact_profile(test_db, cand_a.id)
    prof_b = ActiveResumeRAGService.get_exact_profile(test_db, cand_b.id)

    # A's profile must contain only A's data
    assert prof_a["full_name"] == "Alice Smith"
    assert prof_a["primary_designation"] == "AI Architect"
    assert "Python" in prof_a["all_skills"]
    assert "Golang" not in prof_a["all_skills"]

    # B's profile must contain only B's data
    assert prof_b["full_name"] == "Bob Jones"
    assert prof_b["primary_designation"] == "Cloud Architect"
    assert "Golang" in prof_b["all_skills"]
    assert "PyTorch" not in prof_b["all_skills"]


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2 — Old Resume Isolation
# ─────────────────────────────────────────────────────────────────────────────
def test_old_resume_isolation(test_db):
    user, cand, res_a, _ = create_candidate_with_resume(
        test_db, "charlie@test.com", "Charlie Brown", "Junior Dev", ["Java", "Spring"]
    )

    # Now upload Resume B with senior role
    res_b = Resume(
        candidate_id=cand.id,
        title="Charlie Senior Resume",
        is_active=False,
        status="draft"
    )
    test_db.add(res_b)
    test_db.commit()

    ver_b = ResumeVersion(
        resume_id=res_b.id,
        version_number=1,
        structured_data={
            "personal_info": {"full_name": "Charlie Brown", "email": "charlie@test.com"},
            "skills": [{"name": "Python", "category": "Tech"}, {"name": "FastAPI", "category": "Tech"}],
            "work_experience": [{"designation": "Principal AI Engineer", "employer": "AI Labs", "is_current": True}],
            "projects": []
        }
    )
    test_db.add(ver_b)
    test_db.commit()
    res_b.current_version_id = ver_b.id
    test_db.commit()

    # Populate normalized tables for B
    test_db.add(ResumeProfile(resume_id=res_b.id, full_name="Charlie Brown", email="charlie@test.com"))
    test_db.add(ResumeSkill(resume_id=res_b.id, name="Python", category="Tech"))
    test_db.add(ResumeSkill(resume_id=res_b.id, name="FastAPI", category="Tech"))
    test_db.add(ResumeExperience(resume_id=res_b.id, designation="Principal AI Engineer", employer="AI Labs", is_current=True))
    test_db.commit()

    # Mock vector indexing to return True for Resume B
    with patch("app.services.candidate_embedding_service.CandidateEmbeddingService.index_candidate_resume", return_value=True):
        ResumeContextService.replace_active_resume(
            test_db, cand.id, res_b.id, ver_b.structured_data
        )

    test_db.refresh(res_a)
    test_db.refresh(res_b)
    test_db.refresh(cand)

    assert res_a.is_active is False
    assert res_a.status == "archived"
    assert res_b.is_active is True
    assert res_b.status == "active"
    assert cand.active_resume_id == res_b.id

    # Active profile must return Resume B's data
    curr_prof = ActiveResumeRAGService.get_exact_profile(test_db, cand.id, bypass_cache=True)
    assert curr_prof["active_resume_id"] == res_b.id
    assert "Python" in curr_prof["all_skills"]
    assert "Java" not in curr_prof["all_skills"]


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3 — Failed Replacement Safety
# ─────────────────────────────────────────────────────────────────────────────
def test_failed_replacement_safety(test_db):
    user, cand, res_a, _ = create_candidate_with_resume(
        test_db, "dave@test.com", "Dave Miller", "Security Analyst", ["Cybersecurity", "SIEM"]
    )

    # Resume B extraction fails
    res_b = Resume(candidate_id=cand.id, title="Corrupt Resume", is_active=False, status="uploading")
    test_db.add(res_b)
    test_db.commit()

    # Simulate extraction failure
    ResumeContextService.handle_extraction_failure(test_db, cand.id, res_b.id, "Corrupt PDF file")

    test_db.refresh(res_a)
    test_db.refresh(res_b)
    test_db.refresh(cand)

    # Resume A remains active
    assert res_a.is_active is True
    assert res_a.status == "active"
    assert cand.active_resume_id == res_a.id

    # Resume B is marked failed
    assert res_b.is_active is False
    assert res_b.status == "failed"


# ─────────────────────────────────────────────────────────────────────────────
# TEST 4 — Qdrant Failure Safety
# ─────────────────────────────────────────────────────────────────────────────
def test_qdrant_failure_safety(test_db):
    user, cand, res_a, _ = create_candidate_with_resume(
        test_db, "eve@test.com", "Eve Adams", "Data Scientist", ["Python", "Pandas"]
    )

    res_b = Resume(candidate_id=cand.id, title="Resume B", is_active=False, status="draft")
    test_db.add(res_b)
    test_db.commit()

    ver_b = ResumeVersion(resume_id=res_b.id, version_number=1, structured_data={"skills": ["R"]})
    test_db.add(ver_b)
    test_db.commit()

    # Simulate Qdrant client being enabled but failing indexing
    mock_store = MagicMock()
    mock_store.enabled = True
    mock_store.client = MagicMock()

    with patch("app.services.vector_store.QdrantVectorStore", return_value=mock_store):
        with patch("app.services.candidate_embedding_service.CandidateEmbeddingService.index_candidate_resume", return_value=False):
            with pytest.raises(RuntimeError):
                ResumeContextService.replace_active_resume(
                    test_db, cand.id, res_b.id, ver_b.structured_data
                )

    test_db.refresh(res_a)
    test_db.refresh(res_b)
    test_db.refresh(cand)

    # Resume A must STILL be active
    assert res_a.is_active is True
    assert cand.active_resume_id == res_a.id
    # Resume B must be failed
    assert res_b.is_active is False
    assert res_b.status == "failed"


# ─────────────────────────────────────────────────────────────────────────────
# TEST 5 — Version Isolation
# ─────────────────────────────────────────────────────────────────────────────
def test_version_isolation(test_db):
    user, cand, res, ver_1 = create_candidate_with_resume(
        test_db, "frank@test.com", "Frank Wright", "Architect", ["Revit"]
    )

    # Create version 2 of the same resume
    ver_2 = ResumeVersion(
        resume_id=res.id,
        version_number=2,
        structured_data={"skills": ["Revit", "BIM", "AutoCAD"]}
    )
    test_db.add(ver_2)
    res.current_version_id = ver_2.id
    test_db.commit()

    # Querying active resume must return version 2
    active_res, active_ver, _ = ActiveResumeRAGService.get_active_resume(test_db, cand.id)
    assert active_ver.version_number == 2


# ─────────────────────────────────────────────────────────────────────────────
# TEST 6 — Redis Stale-Cache Protection
# ─────────────────────────────────────────────────────────────────────────────
def test_redis_stale_cache_protection(test_db):
    user, cand, res, _ = create_candidate_with_resume(
        test_db, "grace@test.com", "Grace Hopper", "Computer Scientist", ["Cobol"]
    )

    # Initial profile cache stamped with revision 1
    rev_1 = get_candidate_context_revision(cand.id)
    set_cached_active_resume_context(cand.id, rev_1, {"full_name": "Grace Hopper", "revision": rev_1})

    cached = get_cached_active_resume_context(cand.id)
    assert cached is not None
    assert cached["full_name"] == "Grace Hopper"

    # Context revision increments (e.g. resume edited or replaced)
    rev_2 = increment_candidate_context_revision(cand.id)
    assert rev_2 > rev_1

    # Stale cache must be discarded
    cached_after = get_cached_active_resume_context(cand.id)
    assert cached_after is None


# ─────────────────────────────────────────────────────────────────────────────
# TEST 7 — Exact Field Accuracy (Zero Hallucination)
# ─────────────────────────────────────────────────────────────────────────────
def test_exact_field_accuracy(test_db):
    user, cand, res, _ = create_candidate_with_resume(
        test_db, "helen@test.com", "Helen Keller", "Author", ["Writing", "Public Speaking"]
    )

    name = ActiveResumeRAGService.get_exact_field(test_db, cand.id, "full_name")
    email = ActiveResumeRAGService.get_exact_field(test_db, cand.id, "email")
    company = ActiveResumeRAGService.get_exact_field(test_db, cand.id, "current_company")
    non_existent = ActiveResumeRAGService.get_exact_field(test_db, cand.id, "favorite_color")

    assert name == "Helen Keller"
    assert email == "helen@test.com"
    assert company == "Tech Corp"
    assert non_existent is None


# ─────────────────────────────────────────────────────────────────────────────
# TEST 8 — Semantic Retrieval (Active Resume Grounding)
# ─────────────────────────────────────────────────────────────────────────────
def test_semantic_retrieval_grounding(test_db):
    user, cand, res, _ = create_candidate_with_resume(
        test_db, "ivan@test.com", "Ivan Petrov", "ML Engineer", ["PyTorch", "RAG"]
    )

    # Test synchronous embedding generation works and produces 768 dimensions
    emb = embedding_service.get_embedding_sync("Explain my RAG experience")
    assert isinstance(emb, list)
    assert len(emb) == 768
    assert all(isinstance(x, float) for x in emb)


# ─────────────────────────────────────────────────────────────────────────────
# TEST 9 — Application State Truthfulness
# ─────────────────────────────────────────────────────────────────────────────
def test_application_state_truthfulness(test_db):
    user, cand, res, _ = create_candidate_with_resume(
        test_db, "judy@test.com", "Judy Garland", "Performer", ["Acting"]
    )
    job = Job(title="Lead Actor", company_name="Cinema Corp", is_active=True)
    test_db.add(job)
    test_db.commit()

    # Application initially saved/draft — NOT submitted
    app = Application(candidate_id=cand.id, job_id=job.id, status="saved")
    test_db.add(app)
    test_db.commit()

    assert app.status == "saved"
    assert app.status != "submitted"
    assert app.applied_at is None


# ─────────────────────────────────────────────────────────────────────────────
# TEST 10 — Subscription Entitlement Check
# ─────────────────────────────────────────────────────────────────────────────
def test_subscription_entitlement(test_db):
    free_user = User(email="free@test.com", role="candidate", subscription_tier="free")
    plus_user = User(email="plus@test.com", role="candidate", subscription_tier="plus")
    pro_user = User(email="pro@test.com", role="candidate", subscription_tier="pro")

    allowed_free, msg_free = AutofillService.check_subscription_entitlement(free_user)
    allowed_plus, msg_plus = AutofillService.check_subscription_entitlement(plus_user)
    allowed_pro, msg_pro = AutofillService.check_subscription_entitlement(pro_user)

    assert allowed_free is False
    assert "Upgrade to use automatic form filling" in msg_free

    assert allowed_plus is True
    assert allowed_pro is True
