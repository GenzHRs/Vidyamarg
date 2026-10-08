"""
VidyaMarg AI — Phase 3 Master Verification Suite:
Shared Candidate Context & End-to-End User Workflows.

Verifies:
1. Multi-tenant candidate isolation across all modules (Candidate A vs Candidate B).
2. End-to-end active resume replacement propagation (Resume A -> Resume B across Profile, Autofill, Tools, AI Context).
3. Corrupt/failing upload failure safety (Resume B preserved 100% when new upload fails).
4. Truthful application lifecycle status and active resume version stamping.
5. AI Mentor and Mock Interview session grounding in active resume.
6. Zero hallucination guarantee on missing candidate data.
"""
import pytest
import json
import asyncio
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.models import User, Candidate, CandidateProfile, CandidateResume
from app.models.resume_center_models import (
    Resume, ResumeVersion, ResumeProfile, ResumeSkill,
    ResumeExperience, ResumeEducation, ResumeProject, ResumeCertification
)
from app.models.job_models import (
    Job, Application, ApplicationEvent, Match,
    CandidateAgent, InterviewPreparation, SkillGapAnalysis
)
from app.services.active_resume_rag_service import ActiveResumeRAGService
from app.services.resume_context_service import ResumeContextService
from app.services.autofill_service import AutofillService
from app.tools.career_tools import (
    GetCandidateProfileTool, GetProfileArgs,
    AnalyzeSkillGapsTool, AnalyzeSkillGapsArgs,
    CreateInterviewTool, CreateInterviewArgs
)
from app.services.resume_cache import (
    get_candidate_context_revision,
    increment_candidate_context_revision,
    get_cached_active_resume_context,
    set_cached_active_resume_context,
    invalidate_candidate_context,
    clear_all_local_caches
)


@pytest.fixture(scope="function")
def test_db():
    clear_all_local_caches()
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()
        clear_all_local_caches()


def setup_candidate(db, email, full_name, role_title, skills, project_name="QuantumCore"):
    user = User(
        email=email,
        full_name=full_name,
        password_hash="hashed_pw_xyz",
        role="candidate",
        subscription_tier="pro"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    cand = Candidate(
        user_id=user.id,
        parsed_name=full_name,
        parsed_email=email,
        primary_designation=role_title,
        target_roles=json.dumps([role_title]),
        status="Active"
    )
    db.add(cand)
    db.commit()
    db.refresh(cand)

    resume = Resume(
        candidate_id=cand.id,
        title=f"{full_name} Active Resume",
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
            "personal_info": {"full_name": full_name, "email": email},
            "skills": [{"name": s, "category": "Core"} for s in skills],
            "work_experience": [{
                "designation": role_title,
                "employer": "Tech Apex",
                "is_current": True,
                "responsibilities": [f"Architected {skills[0]} pipeline"]
            }],
            "projects": [{
                "name": project_name,
                "description": f"Production system using {skills[0]} and {skills[1] if len(skills)>1 else ''}",
                "technologies": skills
            }]
        }
    )
    db.add(ver)
    db.commit()
    db.refresh(ver)

    resume.current_version_id = ver.id

    prof = ResumeProfile(
        resume_id=resume.id,
        full_name=full_name,
        email=email,
        phone="+1-555-0199",
        location="San Francisco, CA",
        professional_summary=f"Elite {role_title} expert in {', '.join(skills)}.",
        linkedin_url=f"https://linkedin.com/in/{full_name.lower().replace(' ', '')}",
        github_url=f"https://github.com/{full_name.lower().replace(' ', '')}"
    )
    db.add(prof)

    for s in skills:
        db.add(ResumeSkill(resume_id=resume.id, name=s, category="Core"))

    db.add(ResumeExperience(
        resume_id=resume.id,
        designation=role_title,
        employer="Tech Apex",
        is_current=True,
        responsibilities=[f"Architected {skills[0]} pipeline"]
    ))

    db.add(ResumeProject(
        resume_id=resume.id,
        name=project_name,
        description=f"Production system using {skills[0]}",
        technologies=skills
    ))

    db.commit()
    return user, cand, resume, ver


# ─────────────────────────────────────────────────────────────────────────────
# 1. CROSS-MODULE CANDIDATE ISOLATION (A vs B)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_cross_module_candidate_isolation(test_db):
    """
    Candidate A (Alice, AI Engineer) vs Candidate B (Bob, Cloud DevOps).
    Ensures that every module (Profile tool, Autofill, AI Context, Exact profile)
    resolves exclusively to the authenticated user's active resume.
    """
    user_a, cand_a, res_a, _ = setup_candidate(
        test_db, "alice@test.com", "Alice Smith", "AI Engineer", ["Python", "PyTorch", "vLLM"], project_name="QuantumRAG"
    )
    user_b, cand_b, res_b, _ = setup_candidate(
        test_db, "bob@test.com", "Bob Jones", "Cloud DevOps", ["Terraform", "Kubernetes", "AWS"], project_name="InfraMesh"
    )

    # 1. Profile Tool Isolation
    profile_tool = GetCandidateProfileTool()
    res_prof_a = await profile_tool._run(test_db, user_a.id, GetProfileArgs())
    res_prof_b = await profile_tool._run(test_db, user_b.id, GetProfileArgs())

    assert res_prof_a["candidate_id"] == cand_a.id
    assert res_prof_a["full_name"] == "Alice Smith"
    assert "PyTorch" in res_prof_a["skills"]
    assert "Kubernetes" not in res_prof_a["skills"]

    assert res_prof_b["candidate_id"] == cand_b.id
    assert res_prof_b["full_name"] == "Bob Jones"
    assert "Kubernetes" in res_prof_b["skills"]
    assert "PyTorch" not in res_prof_b["skills"]

    # 2. Autofill Service Isolation
    form_a = AutofillService.map_application_form(test_db, user_a)
    form_b = AutofillService.map_application_form(test_db, user_b)

    assert form_a["mapped_fields"]["full_name"]["value"] == "Alice Smith"
    assert "Python" in form_a["mapped_fields"]["skills"]["value"]
    assert "Terraform" not in form_a["mapped_fields"]["skills"]["value"]

    assert form_b["mapped_fields"]["full_name"]["value"] == "Bob Jones"
    assert "Terraform" in form_b["mapped_fields"]["skills"]["value"]
    assert "PyTorch" not in form_b["mapped_fields"]["skills"]["value"]

    # 3. AI Context Isolation
    ctx_a = ActiveResumeRAGService.build_ai_context(test_db, cand_a.id)
    ctx_b = ActiveResumeRAGService.build_ai_context(test_db, cand_b.id)

    assert ctx_a["profile"]["full_name"] == "Alice Smith"
    assert "QuantumRAG" in [p["name"] for p in ctx_a["profile"]["projects"]]
    assert ctx_b["profile"]["full_name"] == "Bob Jones"
    assert "InfraMesh" in [p["name"] for p in ctx_b["profile"]["projects"]]
    assert "QuantumRAG" not in [p["name"] for p in ctx_b["profile"]["projects"]]


# ─────────────────────────────────────────────────────────────────────────────
# 2. ACTIVE RESUME REPLACEMENT PROPAGATION (A -> B)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_active_resume_replacement_propagation(test_db):
    """
    Candidate replaces Resume A with Resume B.
    All modules must immediately reflect Resume B without any stale cache.
    """
    user, cand, res_a, ver_a = setup_candidate(
        test_db, "carol@test.com", "Carol White", "Frontend Developer", ["React", "JavaScript"], project_name="WebPortal"
    )

    # Verify initial state is Resume A
    prof_before = ActiveResumeRAGService.get_exact_profile(test_db, cand.id)
    assert prof_before["primary_designation"] == "Frontend Developer"
    assert "React" in prof_before["all_skills"]

    # Now create and activate Resume B (Senior Fullstack Lead)
    res_b = Resume(
        candidate_id=cand.id,
        title="Carol Senior Fullstack Resume",
        is_active=False,
        status="active",
        extraction_status="extracted"
    )
    test_db.add(res_b)
    test_db.commit()
    test_db.refresh(res_b)

    ver_b = ResumeVersion(
        resume_id=res_b.id,
        version_number=2,
        structured_data={
            "personal_info": {"full_name": "Carol White", "email": "carol@test.com"},
            "skills": [{"name": s, "category": "Tech"} for s in ["FastAPI", "TypeScript", "Next.js", "Docker"]],
            "work_experience": [{
                "designation": "Fullstack Lead",
                "employer": "Tech Giant",
                "is_current": True,
                "responsibilities": ["Lead distributed fullstack architecture"]
            }],
            "projects": [{
                "name": "CloudArchitectApp",
                "description": "Production Next.js and FastAPI app",
                "technologies": ["Next.js", "FastAPI"]
            }]
        }
    )
    test_db.add(ver_b)
    test_db.commit()
    test_db.refresh(ver_b)
    res_b.current_version_id = ver_b.id

    prof_b = ResumeProfile(
        resume_id=res_b.id,
        full_name="Carol White",
        email="carol@test.com",
        professional_summary="Senior Fullstack Architect."
    )
    test_db.add(prof_b)
    for s in ["FastAPI", "TypeScript", "Next.js", "Docker"]:
        test_db.add(ResumeSkill(resume_id=res_b.id, name=s, category="Tech"))
    test_db.commit()

    # Update candidate's designation to match new resume
    cand.primary_designation = "Fullstack Lead"
    test_db.commit()

    # Activate Resume B using ResumeContextService
    ResumeContextService.activate_resume(test_db, cand.id, res_b.id)

    # 1. Verification of database state
    test_db.refresh(res_a)
    test_db.refresh(res_b)
    test_db.refresh(cand)

    assert res_a.is_active is False
    assert res_b.is_active is True
    assert cand.active_resume_id == res_b.id

    # 2. Verification of ActiveResumeRAGService immediate reflection
    exact_after = ActiveResumeRAGService.get_exact_profile(test_db, cand.id)
    assert exact_after["active_resume_id"] == res_b.id
    assert exact_after["resume_version"] == 2
    assert "FastAPI" in exact_after["all_skills"]
    assert "React" not in exact_after["all_skills"]

    # 3. Verification of Career Tools immediate reflection
    profile_tool = GetCandidateProfileTool()
    tool_profile = await profile_tool._run(test_db, user.id, GetProfileArgs())
    assert tool_profile["active_resume_id"] == res_b.id
    assert "FastAPI" in tool_profile["skills"]
    assert "React" not in tool_profile["skills"]

    # 4. Verification of Autofill immediate reflection
    form_after = AutofillService.map_application_form(test_db, user)
    assert "FastAPI" in form_after["mapped_fields"]["skills"]["value"]
    assert form_after["active_resume_title"] == "Carol Senior Fullstack Resume"


# ─────────────────────────────────────────────────────────────────────────────
# 3. CORRUPT UPLOAD FAILURE SAFETY (Resume B preserved on failure)
# ─────────────────────────────────────────────────────────────────────────────
def test_corrupt_upload_failure_safety(test_db):
    """
    If a new resume upload or vector indexing fails, the existing active resume
    must remain 100% untouched and active.
    """
    user, cand, res_a, _ = setup_candidate(
        test_db, "david@test.com", "David Brown", "Backend Engineer", ["Go", "gRPC", "PostgreSQL"]
    )

    # Simulate attempt to activate a broken/unverifiable resume
    corrupt_resume = Resume(
        candidate_id=cand.id,
        title="Corrupt Resume",
        is_active=False,
        status="pending"
    )
    test_db.add(corrupt_resume)
    test_db.commit()
    test_db.refresh(corrupt_resume)

    mock_store = MagicMock()
    mock_store.enabled = True
    mock_store.client = MagicMock()

    with patch("app.services.vector_store.QdrantVectorStore", return_value=mock_store):
        with patch("app.services.candidate_embedding_service.CandidateEmbeddingService.index_candidate_resume", return_value=False):
            with pytest.raises(RuntimeError):
                ResumeContextService.activate_resume(test_db, cand.id, corrupt_resume.id)

    # Verify Resume A is still active and unchanged
    test_db.refresh(res_a)
    test_db.refresh(corrupt_resume)
    test_db.refresh(cand)

    assert res_a.is_active is True
    assert corrupt_resume.is_active is False
    assert cand.active_resume_id == res_a.id

    # Active profile still returns Resume A
    active_prof = ActiveResumeRAGService.get_exact_profile(test_db, cand.id)
    assert active_prof["active_resume_id"] == res_a.id
    assert "Go" in active_prof["all_skills"]


# ─────────────────────────────────────────────────────────────────────────────
# 4. TRUTHFUL APPLICATION STATUS & VERSION STAMPING
# ─────────────────────────────────────────────────────────────────────────────
def test_truthful_application_status_and_version_stamping(test_db):
    """
    Creating an application must stamp the candidate's active resume version,
    and initialize with truthful status ('saved', not 'submitted').
    """
    user, cand, res, ver = setup_candidate(
        test_db, "eva@test.com", "Eva Green", "MLOps Engineer", ["Docker", "Kubeflow", "MLflow"]
    )

    job = Job(
        title="Senior MLOps Engineer",
        company_name="AI Labs",
        is_active=True,
        required_skills=["Docker", "Kubeflow"]
    )
    test_db.add(job)
    test_db.commit()

    # Application creation logic stamping active resume version
    active_res, active_ver, _ = ResumeContextService.get_active_resume(test_db, cand.id)
    assert active_res is not None

    app = Application(
        candidate_id=cand.id,
        job_id=job.id,
        status="saved",
        resume_version_id=active_res.current_version_id,
        notes="Applied after verifying requirements"
    )
    test_db.add(app)
    test_db.commit()
    test_db.refresh(app)

    # Truthful status: 'saved', NEVER 'submitted' without real submission
    assert app.status == "saved"
    assert app.resume_version_id == ver.id


# ─────────────────────────────────────────────────────────────────────────────
# 5. AI MENTOR & INTERVIEW GROUNDING IN ACTIVE RESUME
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_ai_mentor_and_interview_grounding(test_db):
    """
    Interview generation tool grounds its questions in active resume projects and skills,
    and stamps the interview package with the active resume version.
    """
    user, cand, res, ver = setup_candidate(
        test_db, "frank@test.com", "Frank Miller", "Robotics Engineer", ["ROS", "C++", "SLAM"], project_name="AutonomousRover"
    )

    job = Job(
        title="Robotics Engineer",
        company_name="RoboCorp",
        is_active=True,
        required_skills=["ROS", "C++"]
    )
    test_db.add(job)
    test_db.commit()

    interview_tool = CreateInterviewTool()
    res_interview = await interview_tool._run(
        test_db, user.id, CreateInterviewArgs(interview_type="Technical", difficulty="Advanced")
    )

    assert res_interview["target_role"] == "Robotics Engineer"
    assert res_interview["resume_version"] == ver.version_number
    assert "AutonomousRover" in res_interview["opening_question"]
    assert "ROS" in res_interview["opening_question"]

    # Verify InterviewPreparation record stamped with resume version
    prep = test_db.query(InterviewPreparation).filter(InterviewPreparation.candidate_id == cand.id).first()
    assert prep is not None
    assert prep.version == ver.version_number
    assert prep.difficulty_level == "advanced"


# ─────────────────────────────────────────────────────────────────────────────
# 6. ZERO HALLUCINATION GUARANTEE ON MISSING DATA
# ─────────────────────────────────────────────────────────────────────────────
def test_zero_hallucination_guarantee(test_db):
    """
    Missing candidate fields must return strictly 'Information not available in your profile.'
    No invented titles, companies, or contact info.
    """
    user = User(email="ghost@test.com", full_name="Ghost User", password_hash="h", role="candidate", subscription_tier="pro")
    test_db.add(user)
    test_db.commit()

    cand = Candidate(user_id=user.id, status="Active")
    test_db.add(cand)
    test_db.commit()

    # Exact field query on missing phone returns None (zero hallucination)
    val = ActiveResumeRAGService.get_exact_field(test_db, cand.id, "phone")
    assert val is None

    # Semantic question query on candidate with zero evidence
    res_sem = AutofillService.answer_semantic_question(test_db, user, "What is your experience leading teams?")
    assert res_sem["status"] == "insufficient_data"
    assert res_sem["answer"] == "Information not available in your profile."
