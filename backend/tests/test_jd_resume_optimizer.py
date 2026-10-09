"""
VidyaMarg AI — JD-Driven ATS Resume Optimization Engine Acceptance Test Suite.
Exhaustively validates:
1. Candidate Master Resume Immutability (never modified).
2. All 5 Required Job Descriptions:
   - AI/ML Engineer
   - Generative AI Engineer
   - Data Scientist
   - Machine Learning Engineer
   - NLP Engineer
3. JD Parsing, Classification, and Keyword Normalization.
4. Candidate Evidence Mapping (Strong, Partial, Missing).
5. Weighted ATS Scoring Breakdown (Keyword, Experience, Technical, Responsibility, Alignment, Quality).
6. Evidence-First Bullet Generation (Avataa experience bullets with strong action verbs).
7. Pass-2 Truthfulness & Grounding Verification (Truthfulness = 100%, zero hallucinations).
8. PDF Rendering (ReportLab).
9. DOCX Rendering (python-docx).
10. Database Persistence & Separation (resume_optimizations & resume_optimization_evidence).
11. End-to-End API Endpoints & Centralized Agent Tool.
"""
import copy
import json
import re
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.models.models import Candidate, User
from app.models.resume_center_models import (
    Resume, ResumeVersion, ResumeOptimization, ResumeOptimizationEvidence
)
from app.services.ats_optimizer import (
    run_full_jd_optimization,
    generate_optimized_docx,
    normalize_skill,
    are_skills_equivalent,
    parse_job_description,
    extract_master_evidence,
    match_candidate_evidence,
    calculate_ats_scores,
    validate_truthfulness
)
from app.services.latex_service import render_structured_data_to_pdf
from app.tools.career_tools import OptimizeResumeForJdTool, OptimizeResumeForJdArgs
import main


# 5 Required Job Descriptions
JD_AIML_ENGINEER = """
Job Title: AI/ML Engineer
Company: Avataa Enterprise
Location: Remote

Responsibilities:
- Build scalable REST APIs and microservices using Python and FastAPI for intelligent document processing.
- Develop RAG pipelines and semantic search workflows using LLMs (OpenAI, Gemini).
- Implement document preprocessing, OCR, and NER pipelines for automated compliance verification.
- Deploy machine learning models and optimize throughput for sub-second retrieval latency.

Requirements:
- 2+ years of experience with Python, FastAPI, and machine learning.
- Hands-on experience with RAG, LLMs, and prompt engineering.
- Solid background in OCR, NER, and NLP text processing.
- Experience with Docker, Git, and REST APIs.
- Preferred: Experience with Kubernetes, AWS, and MLflow.
"""

JD_GENAI_ENGINEER = """
Job Title: Generative AI Engineer
Company: DeepGen Tech
Location: Hybrid

Responsibilities:
- Architect enterprise Generative AI and RAG architectures for document intelligence.
- Integrate foundation models including OpenAI and Gemini into production pipelines.
- Implement semantic retrieval, vector search, and contextual document grounding.
- Optimize prompt engineering, context window management, and inference efficiency.

Requirements:
- Strong programming background in Python and FastAPI.
- Proven expertise in RAG, LLMs, and semantic search retrieval.
- Practical experience in document processing, embeddings, and prompt engineering.
- Familiarity with Docker and containerized deployment.
- Preferred: Experience with LangChain, Kubernetes, AWS Bedrock, and Pinecone.
"""

JD_DATA_SCIENTIST = """
Job Title: Data Scientist
Company: Analytics Core
Location: New York, NY

Responsibilities:
- Develop predictive machine learning models and NLP pipelines for automated document classification.
- Perform feature engineering, data cleaning, and preprocessing on unstructured text and scanned files.
- Integrate LLM-assisted summarization and information extraction models.
- Build REST API endpoints with FastAPI to serve real-time model inferences.

Requirements:
- Proficiency in Python, Pandas, NumPy, and Scikit-learn.
- Experience with NLP, OCR, and document intelligence workflows.
- Hands-on familiarity with LLMs, RAG, and prompt engineering.
- Strong understanding of supervised and unsupervised learning algorithms.
- Preferred: Knowledge of Spark, Hadoop, AWS SageMaker, and Tableau.
"""

JD_ML_ENGINEER = """
Job Title: Machine Learning Engineer
Company: Visionary AI Labs
Location: San Francisco, CA

Responsibilities:
- Design and deploy machine learning and deep learning pipelines in production.
- Build high-performance REST APIs with FastAPI to serve ML inference endpoints.
- Develop OCR and Named Entity Recognition (NER) models for automated text extraction.
- Implement monitoring, automated regression testing, and data validation.

Requirements:
- 2+ years of production experience in Python and FastAPI.
- Solid understanding of ML frameworks (Scikit-learn, PyTorch, TensorFlow).
- Hands-on experience with NLP, OCR, and document preprocessing.
- Proficiency with Docker, Git, and Linux environments.
- Preferred: Experience with Kubernetes, Kubeflow, AWS, and CI/CD pipelines.
"""

JD_NLP_ENGINEER = """
Job Title: NLP Engineer
Company: Lingua AI
Location: Remote

Responsibilities:
- Build advanced NLP systems for text summarization, entity extraction, and compliance checking.
- Implement Named Entity Recognition (NER), tokenization, and TF-IDF pipelines.
- Integrate modern LLMs (OpenAI, Gemini) with retrieval-augmented generation (RAG).
- Develop REST APIs using Python and FastAPI for document OCR ingestion and processing.

Requirements:
- Strong Python programming with experience in NLP libraries and Transformers.
- Proven experience with NER, OCR, and enterprise document intelligence.
- Practical expertise with RAG systems, semantic embeddings, and LLM prompting.
- Preferred: Experience with Spacy, Hugging Face, C++, and AWS.
"""

ALL_TEST_JDS = [
    ("AI/ML Engineer", JD_AIML_ENGINEER),
    ("Generative AI Engineer", JD_GENAI_ENGINEER),
    ("Data Scientist", JD_DATA_SCIENTIST),
    ("Machine Learning Engineer", JD_ML_ENGINEER),
    ("NLP Engineer", JD_NLP_ENGINEER),
]


SAMPLE_MASTER_STRUCTURED_DATA = {
    "personal_info": {
        "full_name": "JAYAVARAPU SIVA TEJACHARY",
        "email": "candidate@vidyamarg.ai",
        "phone": "+91-9866862016",
        "location": "Hyderabad, India",
        "linkedin": "https://www.linkedin.com/in/jayavarapu-siva-tejachary",
        "github": "https://github.com/sivatejachary"
    },
    "summary": "AI/ML Engineer with 2+ years of experience building AI-powered document intelligence and automation solutions using Python, FastAPI, NLP, LLMs, and RAG.",
    "skills": {
        "Programming Languages": ["Python"],
        "Frameworks & Libraries": ["FastAPI", "Scikit-learn", "TensorFlow", "PyTorch", "Pandas", "NumPy"],
        "Databases": ["MySQL", "PostgreSQL"],
        "Cloud & DevOps": ["Git", "GitHub", "Docker", "Azure"],
        "Developer Tools": ["REST APIs", "Jupyter Notebook"],
        "AI & Machine Learning": ["LLMs", "OpenAI", "Gemini", "RAG", "Prompt Engineering", "LangChain", "Hugging Face Transformers", "NER", "OCR", "TF-IDF", "Embeddings"],
        "Technologies & Tools": ["Supervised Learning", "Unsupervised Learning"]
    },
    "experience": [
        {
            "company": "Avataa Solutions Pvt. Ltd.",
            "title": "AI/ML Engineer",
            "start_date": "June 2024",
            "end_date": "Present",
            "location": "Hyderabad, India",
            "bullets": [
                "Engineered AI/ML applications using Python, FastAPI, NLP, LLMs, and RAG for intelligent document processing.",
                "Developed REST APIs and backend microservices supporting AI-driven document analysis and automated processing workflows.",
                "Implemented OCR, Named Entity Recognition (NER), data preprocessing, and machine learning pipelines for enterprise document analysis.",
                "Integrated OpenAI and Gemini LLMs for document understanding, contextual summarization, and automated workflows.",
                "Developed RAG-based document intelligence solutions using semantic retrieval and LLMs to provide context-grounded responses from enterprise documents."
            ]
        }
    ],
    "projects": [
        {
            "name": "Enterprise Document AI & Compliance Automation",
            "technologies": ["Python", "FastAPI", "RAG", "OpenAI", "Gemini", "OCR", "NER"],
            "bullets": [
                "Architected an end-to-end RAG system for contextual enterprise document intelligence.",
                "Deployed high-throughput FastAPI REST endpoints for real-time document extraction."
            ]
        },
        {
            "name": "AI Resume Screening System",
            "technologies": ["Python", "NLP", "Scikit-learn", "TF-IDF"],
            "bullets": [
                "Developed automated semantic screening pipeline for candidate profiles against job postings."
            ]
        }
    ],
    "education": [
        {
            "institution": "JNTU",
            "degree": "Bachelor of Technology in Computer Science",
            "graduation_year": "2024"
        }
    ],
    "certifications": [
        "Machine Learning Specialization — DeepLearning.AI"
    ]
}


@pytest.fixture(scope="function")
def test_db():
    """Isolated in-memory SQLite database fixture."""
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    db = Session()

    # Seed User & Candidate
    user = User(
        id=1,
        email="candidate@vidyamarg.ai",
        full_name="JAYAVARAPU SIVA TEJACHARY",
        role="candidate",
        password_hash="test-pw-hash"
    )
    db.add(user)
    db.flush()

    cand = Candidate(
        id=1,
        user_id=user.id,
        parsed_name="JAYAVARAPU SIVA TEJACHARY",
        parsed_email="candidate@vidyamarg.ai",
        primary_designation="AI/ML Engineer",
        target_roles=json.dumps(["AI/ML Engineer", "Generative AI Engineer"]),
        status="Active"
    )
    db.add(cand)
    db.flush()

    resume = Resume(
        id=99904,
        candidate_id=cand.id,
        title="AIML- JAYAVARAPU SIVA TEJACHARY",
        source_type="upload",
        is_active=True,
        status="active",
        extraction_status="verified",
        is_verified=True
    )
    db.add(resume)
    db.flush()

    cand.active_resume_id = resume.id

    ver = ResumeVersion(
        id=1,
        resume_id=resume.id,
        version_number=1,
        structured_data=copy.deepcopy(SAMPLE_MASTER_STRUCTURED_DATA),
        change_summary="Initial master resume import"
    )
    db.add(ver)
    db.commit()

    resume.current_version_id = ver.id
    db.commit()

    try:
        yield db, user, cand, resume, ver
    finally:
        db.close()
        engine.dispose()


def test_keyword_normalization():
    """Rule 4: Validates equivalent terminology and strict distinction boundaries."""
    assert are_skills_equivalent("large language models", "LLM")
    assert are_skills_equivalent("generative ai", "LLM")
    assert are_skills_equivalent("natural language processing", "NLP")
    assert are_skills_equivalent("retrieval augmented generation", "RAG")
    assert are_skills_equivalent("restful api", "REST API")
    assert are_skills_equivalent("k8s", "Kubernetes")

    # Strict distinctions must NEVER be equivalent
    assert not are_skills_equivalent("Python", "Java")
    assert not are_skills_equivalent("TensorFlow", "PyTorch")
    assert not are_skills_equivalent("AWS", "Azure")
    assert not are_skills_equivalent("FastAPI", "Flask")


def test_master_resume_immutability(test_db):
    """Rule 1: Guarantees Master Resume is NEVER modified during or after optimization."""
    db, user, cand, master_resume, ver = test_db
    orig_data_copy = copy.deepcopy(SAMPLE_MASTER_STRUCTURED_DATA)
    orig_title = master_resume.title

    # Run optimization across all 5 JDs
    for jd_name, jd_text in ALL_TEST_JDS:
        res = run_full_jd_optimization(SAMPLE_MASTER_STRUCTURED_DATA, jd_text)
        assert res is not None

    # Verify original master data dict is strictly identical
    assert SAMPLE_MASTER_STRUCTURED_DATA == orig_data_copy, "In-memory master data must remain strictly immutable"

    # Query DB to verify master resume row was not altered
    r_after = db.query(Resume).filter(Resume.id == master_resume.id).first()
    v_after = db.query(ResumeVersion).filter(ResumeVersion.resume_id == master_resume.id).first()
    assert r_after.title == orig_title
    assert v_after.structured_data == orig_data_copy


@pytest.mark.parametrize("jd_name,jd_text", ALL_TEST_JDS)
def test_jd_optimization_pipeline_five_roles(jd_name, jd_text):
    """
    Rule 28: Acceptance test for all 5 distinct JDs.
    Verifies parsing, evidence mapping, ATS scores, 100% truthfulness, PDF, and DOCX.
    """
    master_data = copy.deepcopy(SAMPLE_MASTER_STRUCTURED_DATA)

    # 1. Run optimization engine
    result = run_full_jd_optimization(master_data, jd_text)

    # 2. Verify dynamic title selection matches target role
    assert result.dynamic_title == jd_name, f"Expected dynamic title '{jd_name}', got '{result.dynamic_title}'"
    assert result.optimized_resume["personal_info"]["professional_title"] == jd_name
    assert result.optimized_resume["summary"].startswith(jd_name)

    # 3. Verify project ranking alignment
    if jd_name == "NLP Engineer":
        assert "Screening" in result.optimized_resume["projects"][0]["name"]
    elif jd_name == "Generative AI Engineer":
        assert "Document AI" in result.optimized_resume["projects"][0]["name"]

    # 4. Verify JD parsing and requirement classification
    assert result.parsed_jd.job_title != ""
    assert len(result.parsed_jd.requirements) > 0
    categories = {r.category for r in result.parsed_jd.requirements}
    assert "REQUIRED" in categories
    assert "RESPONSIBILITY" in categories

    # 5. Verify evidence matching
    assert len(result.evidence_matches) > 0
    strong_matches = [m for m in result.evidence_matches if m.match_type == "STRONG_MATCH"]
    assert len(strong_matches) >= 3, "Candidate must strongly match core skills (Python, FastAPI, RAG, etc.)"

    # 6. Verify ATS scores breakdown
    scores = result.ats_scores
    assert 60 <= scores.overall_ats_score <= 100
    assert 70 <= scores.keyword_match <= 100
    assert 70 <= scores.experience_match <= 100
    assert 70 <= scores.technical_match <= 100
    assert 70 <= scores.responsibility_match <= 100
    assert 80 <= scores.alignment_score <= 100
    assert scores.quality_score >= 85

    # 7. Verify missing skills identified (e.g. Kubernetes, AWS, etc.)
    assert len(scores.missing_skills) > 0, "JD mentions technologies candidate does not have (e.g. Kubernetes, AWS)"
    for missing_skill in scores.missing_skills:
        # Missing skills must NEVER appear as whole technology words in optimized experience bullets
        pattern = r"(?<!\w)" + re.escape(missing_skill.lower()) + r"(?!\w)"
        for exp in result.optimized_resume.get("experience", []):
            for bullet in exp.get("bullets", []):
                assert not re.search(pattern, bullet.lower()), f"Hallucination: Missing skill '{missing_skill}' found in bullet: {bullet}"

    # 8. Verify 100% Truthfulness
    assert result.truthfulness_score == 100
    assert len(result.truthfulness_violations) == 0

    # 9. Verify Avataa Experience generation (Rule 7, 8, 9, 10)
    avataa_exp = next((e for e in result.optimized_resume.get("experience", []) if "avataa" in e.get("company", "").lower()), None)
    assert avataa_exp is not None
    assert 4 <= len(avataa_exp.get("bullets", [])) <= 6, "Must generate 4-6 bullets for Avataa experience"

    # Verify action verbs in bullets
    valid_verbs = ("engineered", "developed", "designed", "implemented", "integrated", "optimized", "automated", "built", "contributed")
    for bullet in avataa_exp["bullets"]:
        first_word = bullet.split()[0].lower()
        assert first_word in valid_verbs, f"Bullet must start with strong action verb, got: {first_word}"

    # 10. Verify PDF Rendering (ReportLab)
    pdf_bytes = render_structured_data_to_pdf(result.optimized_resume)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000, "PDF must render successfully with valid length"

    # 11. Verify DOCX Rendering (python-docx)
    docx_bytes = generate_optimized_docx(result.optimized_resume)
    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 5000, "DOCX must render successfully with valid length"


def test_dynamic_title_downgrades_and_buzzwords():
    """Validates truthful seniority downgrading and buzzword stripping."""
    from app.services.ats_optimizer import determine_truthful_professional_title

    # 1. Seniority downgrade: candidate with 1-2 years experience cannot claim 'Senior' or 'Lead'
    title1 = determine_truthful_professional_title(
        raw_jd_title="Senior Generative AI Engineer",
        jd_text="Looking for an engineer with LLM, RAG, Python, and FastAPI skills."
    )
    assert title1 == "Generative AI Engineer", f"Expected 'Generative AI Engineer', got '{title1}'"

    title2 = determine_truthful_professional_title(
        raw_jd_title="Lead Machine Learning Engineer",
        jd_text="Build PyTorch and TensorFlow ML pipelines."
    )
    assert title2 == "Machine Learning Engineer", f"Expected 'Machine Learning Engineer', got '{title2}'"

    # 2. Buzzword stripping: rockstars and gurus are mapped to truthful titles
    title3 = determine_truthful_professional_title(
        raw_jd_title="AI Rockstar",
        jd_text="Build scalable artificial intelligence applications."
    )
    assert title3 == "AI/ML Engineer", f"Expected 'AI/ML Engineer', got '{title3}'"

    title4 = determine_truthful_professional_title(
        raw_jd_title="Prompt Guru",
        jd_text="Work with OpenAI, Gemini, RAG architectures and LLM prompts."
    )
    assert title4 == "Generative AI Engineer", f"Expected 'Generative AI Engineer', got '{title4}'"

    # 3. Unsupported role fallback: candidate does not have iOS/React evidence
    title5 = determine_truthful_professional_title(
        raw_jd_title="Senior iOS Developer",
        jd_text="Develop Swift, Objective-C, and UIKit iOS mobile apps."
    )
    assert title5 == "AI/ML Engineer", f"Expected truthful fallback 'AI/ML Engineer', got '{title5}'"


def test_master_resume_header_sanitization():
    """Validates that dirty multi-specialty headlines in master resume are cleansed."""
    from app.services.ats_optimizer import sanitize_master_resume_header

    dirty_master = copy.deepcopy(SAMPLE_MASTER_STRUCTURED_DATA)
    dirty_master["personal_info"]["professional_title"] = "AI/ML Engineer | Generative AI | RAG | NLP | Document AI"

    clean = sanitize_master_resume_header(dirty_master)
    assert clean["personal_info"]["professional_title"] == "AI/ML Engineer"
    assert "|" not in clean["personal_info"]["professional_title"]


def test_api_optimize_and_download_flow(test_db):
    """Rules 21, 24: Validates the REST API endpoints and PDF/DOCX downloads."""
    db, user, cand, master_resume, ver = test_db

    # Override get_db dependency
    def override_get_db():
        yield db

    main.app.dependency_overrides[get_db] = override_get_db

    try:
        token = create_access_token("candidate@vidyamarg.ai", role="candidate")
        client = TestClient(main.app)

        # 1. POST /api/v1/resume/optimize
        req_body = {
            "resume_id": master_resume.id,
            "job_description": JD_AIML_ENGINEER,
            "job_title": "AI/ML Engineer",
            "company": "Avataa Enterprise",
            "template_id": 1
        }
        res = client.post("/api/v1/resume/optimize", json=req_body, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200, f"Optimize endpoint failed: {res.text}"
        data = res.json()
        opt_id = data["optimization_id"]
        assert opt_id > 0
        assert data["ats_score"] >= 80
        assert data["truthfulness_score"] == 100
        assert len(data["matched_skills"]) > 0
        assert len(data["missing_skills"]) > 0
        assert len(data["evidence_items"]) > 0

        # 2. GET /api/v1/resume/optimize/{id}
        res_get = client.get(f"/api/v1/resume/optimize/{opt_id}", headers={"Authorization": f"Bearer {token}"})
        assert res_get.status_code == 200
        assert res_get.json()["optimization_id"] == opt_id

        # 3. GET /api/v1/resume/optimize/{id}/download/pdf
        res_pdf = client.get(f"/api/v1/resume/optimize/{opt_id}/download/pdf", headers={"Authorization": f"Bearer {token}"})
        assert res_pdf.status_code == 200
        assert res_pdf.headers["content-type"] == "application/pdf"
        assert len(res_pdf.content) > 1000

        # 4. GET /api/v1/resume/optimize/{id}/download/docx
        res_docx = client.get(f"/api/v1/resume/optimize/{opt_id}/download/docx", headers={"Authorization": f"Bearer {token}"})
        assert res_docx.status_code == 200
        assert "wordprocessingml" in res_docx.headers["content-type"]
        assert len(res_docx.content) > 5000

        # 5. POST /api/v1/resume/optimize/{id}/save-as-resume (Derives new resume without touching master)
        res_save = client.post(
            f"/api/v1/resume/optimize/{opt_id}/save-as-resume",
            json={"custom_title": "Avataa AI/ML Tailored V1", "set_as_active": False},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res_save.status_code == 200
        save_data = res_save.json()
        new_resume_id = save_data["resume_id"]
        assert new_resume_id != master_resume.id, "Must save as a NEW resume, never overwriting master"
    finally:
        main.app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_career_agent_tool_optimize_resume(test_db):
    """Rule 25: Validates centralized optimize_resume_for_jd agent tool."""
    db, user, cand, master_resume, ver = test_db

    tool = OptimizeResumeForJdTool()
    args = OptimizeResumeForJdArgs(
        job_description=JD_GENAI_ENGINEER,
        job_title="Generative AI Engineer",
        company="DeepGen Tech",
        resume_id=master_resume.id
    )

    tool_result = await tool._run(db, user.id, args)
    assert "error" not in tool_result
    assert "optimization_id" in tool_result
    assert tool_result["ats_score"] >= 80
    assert tool_result["resume_match_score"] == tool_result["ats_score"]
    assert tool_result["truthfulness_score"] == 100
    assert len(tool_result["evidence_map"]) > 0
    assert len(tool_result["matched_skills"]) > 0
    assert len(tool_result["missing_skills"]) > 0
    assert "score_breakdown" in tool_result
    assert "score_explanation" in tool_result
    assert "skill_gaps" in tool_result
    assert "application_readiness" in tool_result
    assert "prepared_application" in tool_result


def test_score_explanation_and_gaps_classification():
    """Validates 6-part weighted breakdown, score explanation, and critical/important/optional gap separation."""
    result = run_full_jd_optimization(
        master_resume_data=SAMPLE_MASTER_STRUCTURED_DATA,
        job_description_text=JD_AIML_ENGINEER
    )

    # 1. Resume Match Score Equivalence
    assert result.resume_match_score == result.ats_scores.overall_ats_score
    assert result.resume_match_score >= 80

    # 2. 6-part Breakdown
    bd = result.score_breakdown
    assert "keyword_match" in bd
    assert "experience_match" in bd
    assert "technical_match" in bd
    assert "responsibility_match" in bd
    assert "alignment_score" in bd
    assert "quality_score" in bd

    # 3. Score Explanation
    exp = result.score_explanation
    assert len(exp.positive_factors) >= 2
    assert any("+" in f for f in exp.positive_factors)
    assert any("-" in f for f in exp.negative_factors)
    assert "Calculated from job-description" in exp.disclaimer

    # 4. Skill Gaps Classification
    gaps = result.skill_gaps
    assert isinstance(gaps.critical_gaps, list)
    assert isinstance(gaps.important_gaps, list)
    assert isinstance(gaps.optional_gaps, list)


def test_application_readiness_and_preparation():
    """Validates application readiness calculation and safe draft preparation."""
    from app.services.ats_optimizer import calculate_application_readiness, prepare_application_draft

    result = run_full_jd_optimization(
        master_resume_data=SAMPLE_MASTER_STRUCTURED_DATA,
        job_description_text=JD_GENAI_ENGINEER
    )

    # 1. Readiness Evaluation
    readiness = result.application_readiness
    assert readiness.readiness_level in ("HIGH", "MEDIUM", "LOW")
    assert readiness.score >= 80
    assert len(readiness.reasoning) >= 1
    assert len(readiness.recommendation) > 10

    # 2. Safe Draft Preparation
    prep = result.prepared_application
    assert prep.status == "PREPARED"
    assert prep.requires_user_confirmation is True
    assert prep.submission_allowed is False
    assert len(prep.exact_fields) >= 8
    assert len(prep.semantic_fields) >= 2
    assert len(prep.missing_fields) >= 2

    # Verify exact fields have 1.0 confidence
    full_name_field = next(f for f in prep.exact_fields if f.field_key == "full_name")
    assert full_name_field.value == "JAYAVARAPU SIVA TEJACHARY"
    assert full_name_field.confidence == 1.0
    assert full_name_field.user_confirmed is False

    # Verify semantic answers are grounded in candidate facts
    why_interested = next(f for f in prep.semantic_fields if f.field_key == "why_interested")
    assert "Avataa Solutions" in why_interested.value
    assert why_interested.confidence >= 0.90


def test_api_application_prepare_and_confirm_endpoints(test_db):
    """Validates the prepare-application and confirm-application endpoints with safety gate."""
    db, user, cand, master_resume, ver = test_db

    def override_get_db():
        yield db

    main.app.dependency_overrides[get_db] = override_get_db

    try:
        token = create_access_token("candidate@vidyamarg.ai", role="candidate")
        client = TestClient(main.app)

        # 1. Optimize resume
        req_body = {
            "resume_id": master_resume.id,
            "job_description": JD_AIML_ENGINEER,
            "job_title": "AI/ML Engineer",
            "company": "Avataa Enterprise",
            "template_id": 1
        }
        res_opt = client.post("/api/v1/resume/optimize", json=req_body, headers={"Authorization": f"Bearer {token}"})
        assert res_opt.status_code == 200
        opt_data = res_opt.json()
        opt_id = opt_data["optimization_id"]

        assert "resume_match_score" in opt_data
        assert "score_breakdown" in opt_data
        assert "score_explanation" in opt_data
        assert "skill_gaps" in opt_data
        assert "application_readiness" in opt_data
        assert "prepared_application" in opt_data

        # 2. POST /prepare-application
        res_prep = client.post(f"/api/v1/resume/optimize/{opt_id}/prepare-application", headers={"Authorization": f"Bearer {token}"})
        assert res_prep.status_code == 200
        prep_data = res_prep.json()
        assert prep_data["status"] == "PREPARED"
        assert prep_data["requires_user_confirmation"] is True
        assert prep_data["submission_allowed"] is False

        # 3. POST /confirm-application without acknowledgement must fail with 400
        res_fail = client.post(
            f"/api/v1/resume/optimize/{opt_id}/confirm-application",
            json={"user_acknowledged": False},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res_fail.status_code == 400

        # 4. POST /confirm-application with explicit acknowledgement
        res_confirm = client.post(
            f"/api/v1/resume/optimize/{opt_id}/confirm-application",
            json={"user_acknowledged": True},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res_confirm.status_code == 200
        conf_data = res_confirm.json()
        assert conf_data["status"] == "CONFIRMED"
        assert conf_data["prepared_application"]["status"] == "CONFIRMED"
        assert conf_data["prepared_application"]["submission_allowed"] is False
    finally:
        main.app.dependency_overrides.clear()


def test_zero_dead_code_references_in_codebase():
    """Validates that zero active production or test files reference deprecated ai_os or core_lib modules."""
    import os
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    banned_tokens = ["from ai_os", "import ai_os", "AIOSKernel", "from packages.core_lib", "import core_lib"]

    for root, dirs, files in os.walk(os.path.join(backend_dir, "app")):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                    for token in banned_tokens:
                        assert token not in content, f"Found banned dead reference '{token}' in {path}"

