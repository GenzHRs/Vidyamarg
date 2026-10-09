"""
VidyaMarg AI — Automated Tests for Strict Job Recommendation Engine
===================================================================
Tests verifying all 10 specifications from Section 22 of the Master Prompt:
- TEST 1: AI/ML Engineer (Python, FastAPI, RAG, LLM) vs Generative AI Engineer (Python, RAG, LLM) => RECOMMENDED
- TEST 2: AI/ML Engineer vs React Frontend Developer (React, Next.js, TypeScript) => NOT RECOMMENDED (Hard Reject)
- TEST 3: AI/ML Engineer vs Java Spring Boot Developer => NOT RECOMMENDED (Hard Reject)
- TEST 4: AI/ML Engineer (Python, ML, NLP) vs NLP Engineer (Python, NLP, Transformers) => RECOMMENDED
- TEST 5: AI/ML Engineer (2 yrs exp) vs Principal AI Engineer (8+ yrs exp) => NOT RECOMMENDED (Seniority gap)
- TEST 6: AI/ML Engineer vs AI Sales Manager => NOT RECOMMENDED (Sales profession hard reject)
- TEST 7: AI/ML Engineer vs Data Scientist (Python, Scikit-learn, SQL, ML) => RECOMMENDED (score >= 65)
- TEST 8: Candidate with only Python vs Job (Python, Java, Spring, K8s, AWS) => NOT RECOMMENDED (Single generic skill trap)
- TEST 9: No matching jobs => Returns empty list without filling with unrelated jobs
- TEST 10: Candidate isolation: Candidate A and Candidate B receive distinct, strictly personalized recommendations
"""
import pytest
from app.models.job_models import Job
from app.services.job_recommendation_engine import (
    JobRecommendationEngine,
    JobMatchScorer,
    HardRejectionFilter,
    SkillNormalizer,
)


class MockJob:
    """Mock job for isolated testing without DB overhead."""
    def __init__(
        self,
        id=1,
        title="AI/ML Engineer",
        role_category="AI/ML",
        required_skills=None,
        preferred_skills=None,
        experience_min_years=1.0,
        experience_max_years=4.0,
        description="Develop ML models and pipelines",
        company_name="TechCorp",
        location="Remote",
        is_remote=True,
        employment_type="Full-time",
        is_active=True,
    ):
        self.id = id
        self.title = title
        self.title_normalized = title.lower()
        self.role_category = role_category
        self.required_skills = required_skills or []
        self.preferred_skills = preferred_skills or []
        self.experience_min_years = experience_min_years
        self.experience_max_years = experience_max_years
        self.description = description
        self.description_summary = description
        self.company_name = company_name
        self.location = location
        self.is_remote = is_remote
        self.employment_type = employment_type
        self.salary_min = 120.0
        self.salary_max = 160.0
        self.salary_raw = "$120k - $160k"
        self.apply_url = "https://example.com/apply"
        self.job_url = "https://example.com/apply"
        self.posted_at = None
        self.industry = "Technology"
        self.is_active = is_active


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1: AI/ML Engineer vs Generative AI Engineer
# ─────────────────────────────────────────────────────────────────────────────
def test_case_1_aiml_vs_generative_ai_engineer():
    candidate_context = {
        "candidate_id": 1,
        "primary_designation": "AI/ML Engineer",
        "target_roles": ["AI/ML Engineer", "Generative AI Engineer", "Machine Learning Engineer"],
        "all_skills": ["Python", "FastAPI", "RAG", "LLM"],
        "skills_norm": SkillNormalizer.normalize_set(["Python", "FastAPI", "RAG", "LLM"]),
        "years_experience": 2.0,
        "responsibilities": ["Develop RAG pipelines", "Deploy LLM models with FastAPI"],
    }
    job = MockJob(
        title="Generative AI Engineer",
        role_category="AI/ML",
        required_skills=["Python", "RAG", "LLMs"],
        experience_min_years=1.0,
        experience_max_years=3.0,
    )
    result = JobMatchScorer.score_job(candidate_context, job)
    assert result["is_recommended"] is True
    assert result["overall_score"] >= 65.0
    assert not result["is_hard_rejected"]


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2: AI/ML Engineer vs React Frontend Developer (Hard Reject)
# ─────────────────────────────────────────────────────────────────────────────
def test_case_2_aiml_vs_react_frontend_developer():
    candidate_context = {
        "candidate_id": 1,
        "primary_designation": "AI/ML Engineer",
        "target_roles": ["AI/ML Engineer", "Generative AI Engineer"],
        "all_skills": ["Python", "PyTorch", "TensorFlow", "FastAPI"],
        "skills_norm": SkillNormalizer.normalize_set(["Python", "PyTorch", "TensorFlow", "FastAPI"]),
        "years_experience": 2.0,
        "responsibilities": ["Train deep learning models"],
    }
    job = MockJob(
        title="React Frontend Developer",
        role_category="Engineering",
        required_skills=["React", "Next.js", "TypeScript"],
        experience_min_years=2.0,
    )
    result = JobMatchScorer.score_job(candidate_context, job)
    assert result["is_recommended"] is False
    assert result["is_hard_rejected"] is True
    assert "frontend" in result["rejection_reason"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3: AI/ML Engineer vs Java Spring Boot Developer (Hard Reject)
# ─────────────────────────────────────────────────────────────────────────────
def test_case_3_aiml_vs_java_spring_boot_developer():
    candidate_context = {
        "candidate_id": 1,
        "primary_designation": "AI/ML Engineer",
        "target_roles": ["AI/ML Engineer", "Data Scientist"],
        "all_skills": ["Python", "PyTorch", "Scikit-learn"],
        "skills_norm": SkillNormalizer.normalize_set(["Python", "PyTorch", "Scikit-learn"]),
        "years_experience": 2.0,
    }
    job = MockJob(
        title="Java Spring Boot Developer",
        role_category="Backend Engineering",
        required_skills=["Java", "Spring Boot", "Microservices"],
        experience_min_years=2.0,
    )
    result = JobMatchScorer.score_job(candidate_context, job)
    assert result["is_recommended"] is False
    assert result["is_hard_rejected"] is True
    assert "java" in result["rejection_reason"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 4: AI/ML Engineer vs NLP Engineer
# ─────────────────────────────────────────────────────────────────────────────
def test_case_4_aiml_vs_nlp_engineer():
    candidate_context = {
        "candidate_id": 1,
        "primary_designation": "AI/ML Engineer",
        "target_roles": ["AI/ML Engineer", "NLP Engineer", "Machine Learning Engineer"],
        "all_skills": ["Python", "ML", "NLP"],
        "skills_norm": SkillNormalizer.normalize_set(["Python", "Machine Learning", "NLP"]),
        "years_experience": 2.5,
        "responsibilities": ["Train NLP models and text classification pipelines"],
    }
    job = MockJob(
        title="NLP Engineer",
        role_category="AI/ML",
        required_skills=["Python", "NLP", "Machine Learning"],
        experience_min_years=2.0,
        experience_max_years=4.0,
    )
    result = JobMatchScorer.score_job(candidate_context, job)
    assert result["is_recommended"] is True
    assert result["overall_score"] >= 65.0
    assert not result["is_hard_rejected"]


# ─────────────────────────────────────────────────────────────────────────────
# TEST 5: Experience Mismatch: 2 yrs exp vs Principal (8+ yrs)
# ─────────────────────────────────────────────────────────────────────────────
def test_case_5_seniority_experience_gap_principal():
    candidate_context = {
        "candidate_id": 1,
        "primary_designation": "AI/ML Engineer",
        "target_roles": ["AI/ML Engineer"],
        "all_skills": ["Python", "PyTorch", "LLMs"],
        "skills_norm": SkillNormalizer.normalize_set(["Python", "PyTorch", "LLMs"]),
        "years_experience": 2.0,
    }
    job = MockJob(
        title="Principal AI Engineer",
        role_category="AI/ML",
        required_skills=["Python", "PyTorch", "LLMs"],
        experience_min_years=8.0,
        experience_max_years=12.0,
    )
    result = JobMatchScorer.score_job(candidate_context, job)
    assert result["is_recommended"] is False
    assert result["is_hard_rejected"] is True
    assert "seniority" in result["rejection_reason"].lower() or "years" in result["rejection_reason"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 6: AI/ML Engineer vs AI Sales Manager (Sales Profession Hard Reject)
# ─────────────────────────────────────────────────────────────────────────────
def test_case_6_sales_manager_rejection():
    candidate_context = {
        "candidate_id": 1,
        "primary_designation": "AI/ML Engineer",
        "target_roles": ["AI/ML Engineer", "Data Scientist"],
        "all_skills": ["Python", "PyTorch", "Machine Learning"],
        "skills_norm": SkillNormalizer.normalize_set(["Python", "PyTorch", "Machine Learning"]),
        "years_experience": 2.0,
    }
    job = MockJob(
        title="AI Product Sales Manager",
        role_category="Sales",
        required_skills=["AI", "Enterprise Sales", "CRM"],
        experience_min_years=2.0,
    )
    result = JobMatchScorer.score_job(candidate_context, job)
    assert result["is_recommended"] is False
    assert result["is_hard_rejected"] is True
    assert "profession" in result["rejection_reason"].lower() or "outside target" in result["rejection_reason"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 7: AI/ML Engineer vs Data Scientist (Scikit-learn, SQL, ML)
# ─────────────────────────────────────────────────────────────────────────────
def test_case_7_data_scientist_role_match():
    candidate_context = {
        "candidate_id": 1,
        "primary_designation": "AI/ML Engineer",
        "target_roles": ["AI/ML Engineer", "Data Scientist", "Machine Learning Engineer"],
        "all_skills": ["Python", "Scikit-learn", "SQL", "Machine Learning"],
        "skills_norm": SkillNormalizer.normalize_set(["Python", "Scikit-learn", "SQL", "Machine Learning"]),
        "years_experience": 2.0,
        "responsibilities": ["Built predictive models with scikit-learn", "Queried data using SQL"],
    }
    job = MockJob(
        title="Data Scientist",
        role_category="Data Science",
        required_skills=["Python", "Scikit-learn", "SQL", "Machine Learning"],
        experience_min_years=1.0,
        experience_max_years=3.0,
    )
    result = JobMatchScorer.score_job(candidate_context, job)
    assert result["is_recommended"] is True
    assert result["overall_score"] >= 65.0


# ─────────────────────────────────────────────────────────────────────────────
# TEST 8: Single Generic Skill Trap (Python alone vs Java+Spring+K8s+AWS)
# ─────────────────────────────────────────────────────────────────────────────
def test_case_8_single_generic_skill_trap():
    candidate_context = {
        "candidate_id": 1,
        "primary_designation": "Software Developer",
        "target_roles": ["Software Developer"],
        "all_skills": ["Python"],
        "skills_norm": SkillNormalizer.normalize_set(["Python"]),
        "years_experience": 2.0,
    }
    job = MockJob(
        title="Enterprise Cloud Backend Engineer",
        role_category="Backend Engineering",
        required_skills=["Python", "Java", "Spring", "Kubernetes", "AWS"],
        experience_min_years=3.0,
    )
    result = JobMatchScorer.score_job(candidate_context, job)
    assert result["is_recommended"] is False
    assert result["is_hard_rejected"] is True
    assert "generic skill" in result["rejection_reason"].lower() or "insufficient" in result["rejection_reason"].lower()


# ─────────────────────────────────────────────────────────────────────────────
# TEST 9: Empty State (No jobs meet threshold, no fake filler)
# ─────────────────────────────────────────────────────────────────────────────
def test_case_9_empty_state_does_not_fill_unrelated():
    candidate_context = {
        "candidate_id": 1,
        "primary_designation": "Quantum Computing Researcher",
        "target_roles": ["Quantum Computing Researcher"],
        "all_skills": ["Qiskit", "Cirq"],
        "skills_norm": SkillNormalizer.normalize_set(["Qiskit", "Cirq"]),
        "years_experience": 2.0,
    }
    # Unrelated jobs catalog
    unrelated_jobs = [
        MockJob(id=101, title="Sales Representative", role_category="Sales", required_skills=["Salesforce", "Cold Calling"]),
        MockJob(id=102, title="Graphic Designer", role_category="Design", required_skills=["Figma", "Illustrator"]),
        MockJob(id=103, title="Payroll Specialist", role_category="Human Resources", required_skills=["Excel", "ADP"]),
    ]
    recommended = []
    for j in unrelated_jobs:
        score_res = JobMatchScorer.score_job(candidate_context, j)
        if score_res["is_recommended"]:
            recommended.append(j)

    # Empty list must NOT be filled with unrelated jobs
    assert len(recommended) == 0


# ─────────────────────────────────────────────────────────────────────────────
# TEST 10: Candidate Isolation
# ─────────────────────────────────────────────────────────────────────────────
def test_case_10_candidate_isolation():
    candidate_a = {
        "candidate_id": 100,
        "primary_designation": "AI/ML Engineer",
        "target_roles": ["AI/ML Engineer", "Generative AI Engineer"],
        "all_skills": ["Python", "PyTorch", "RAG", "LLMs"],
        "skills_norm": SkillNormalizer.normalize_set(["Python", "PyTorch", "RAG", "LLMs"]),
        "years_experience": 2.0,
    }
    candidate_b = {
        "candidate_id": 200,
        "primary_designation": "Financial Analyst",
        "target_roles": ["Financial Analyst", "Investment Analyst"],
        "all_skills": ["Financial Modeling", "Excel", "DCF Valuation"],
        "skills_norm": SkillNormalizer.normalize_set(["Financial Modeling", "Excel", "DCF Valuation"]),
        "years_experience": 3.0,
    }

    ai_job = MockJob(id=1, title="Generative AI Engineer", role_category="AI/ML", required_skills=["Python", "RAG", "LLMs"])
    finance_job = MockJob(id=2, title="Senior Financial Analyst", role_category="Finance & Banking", required_skills=["Financial Modeling", "Excel"])

    a_ai_score = JobMatchScorer.score_job(candidate_a, ai_job)
    a_fin_score = JobMatchScorer.score_job(candidate_a, finance_job)

    b_ai_score = JobMatchScorer.score_job(candidate_b, ai_job)
    b_fin_score = JobMatchScorer.score_job(candidate_b, finance_job)

    # Candidate A gets AI job recommended, Finance job rejected
    assert a_ai_score["is_recommended"] is True
    assert a_fin_score["is_recommended"] is False

    # Candidate B gets Finance job recommended, AI job rejected
    assert b_ai_score["is_recommended"] is False
    assert b_fin_score["is_recommended"] is True

    # No cross contamination
    assert a_ai_score["overall_score"] >= 65.0
    assert b_fin_score["overall_score"] >= 65.0
