"""
End-to-End Tests for VidyaMarg AI — AI Career Agent System.
Verifies:
1. Tool catalog retrieval and schema validation.
2. Context retrieval.
3. Natural language job search and matching tool execution.
4. Natural language resume analysis tool execution.
5. Skill gap analysis and course recommendation tool execution.
6. Mock interview session setup tool execution.
7. High-risk action gating with Action Preview cards and confirmation execution.
8. Multi-step autonomous plan decomposition and execution ("Take care of everything").
"""
import json
import pytest
from tests.conftest import headers
from app.models.models import Candidate, User
from app.models.resume_center_models import Resume
from app.models.job_models import Application


@pytest.fixture
def candidate_with_resume(environment):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    payload = {
        "title": "Jayavarapu Siva Tejachary - Resume",
        "structured_data": {
            "personal_info": {
                "full_name": "Jayavarapu Siva Tejachary",
                "email": "j.shivachary@gmail.com",
                "phone": "+91-9876543210",
                "location": "Hyderabad, Telangana"
            },
            "summary": "Full Stack AI Engineer with expertise in Python, FastAPI, PyTorch, and machine learning architectures.",
            "skills": {
                "Languages": ["Python", "TypeScript", "SQL"],
                "Frameworks": ["FastAPI", "React", "Next.js", "PyTorch"],
                "Tools": ["Docker", "Git", "Linux"]
            },
            "experience": [
                {
                    "title": "AI Engineer",
                    "company": "DeepTech Systems",
                    "dates": "2023 - Present",
                    "bullets": ["Engineered high-performance FastAPI backends for generative AI pipelines."]
                }
            ],
            "projects": [
                {
                    "name": "Enterprise Document QA",
                    "technologies": ["Python", "FastAPI", "LangChain"],
                    "description": "Multi-agent document processing framework."
                }
            ]
        }
    }
    res = client.post("/api/v1/resumes", json=payload, headers=auth)
    assert res.status_code == 200

    # Seed a real job and match for candidate testing
    from app.models.job_models import Job, Match
    job = Job(
        title="GenAI Engineer",
        company_name="DeepTech AI Labs",
        location="Hyderabad",
        is_remote=True,
        required_skills=["Python", "FastAPI", "PyTorch"],
        description="Build state of the art generative AI platforms.",
        is_active=True
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    owner_cand = db.query(Candidate).filter(Candidate.user_id == owner.id).first()
    match = Match(
        candidate_id=owner_cand.id if owner_cand else candidate.id,
        job_id=job.id,
        overall_score=0.88,
        status="new"
    )
    db.add(match)
    db.commit()

    return res.json()["id"]


def test_list_agent_tools(environment):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    res = client.get("/api/v1/agent/tools", headers=auth)
    assert res.status_code == 200
    tools = res.json()
    assert len(tools) >= 8

    names = [t["name"] for t in tools]
    assert "get_candidate_profile" in names
    assert "search_jobs" in names
    assert "analyze_resume" in names
    assert "analyze_skill_gaps" in names
    assert "get_recommended_courses" in names
    assert "create_interview" in names


def test_get_agent_context(environment, candidate_with_resume):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    res = client.get("/api/v1/agent/context", headers=auth)
    assert res.status_code == 200
    ctx = res.json()
    assert ctx["has_resume"] is True
    assert ctx["active_resume_id"] == candidate_with_resume
    assert "Jayavarapu" in ctx["active_resume_title"]


def test_agent_job_search_instruction(environment, candidate_with_resume):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    payload = {
        "message": "Find me GenAI jobs above 80% match in Hyderabad",
        "page_context": {"pathname": "/candidate/jobs"}
    }
    res = client.post("/api/v1/agent/chat", json=payload, headers=auth)
    assert res.status_code == 200
    data = res.json()
    assert "response" in data
    assert len(data["plan"]) > 0
    assert any(step["status"] == "completed" for step in data["plan"])

    # Verify UI cards generated
    ui_cards = data.get("ui_cards", [])
    assert any(c["type"] == "job" for c in ui_cards)


def test_agent_resume_analysis_instruction(environment, candidate_with_resume):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    payload = {
        "message": "Analyze my resume and tell me what I should improve",
        "page_context": {"pathname": "/candidate/resumes"}
    }
    res = client.post("/api/v1/agent/chat", json=payload, headers=auth)
    assert res.status_code == 200
    data = res.json()

    assert "response" in data
    # Check that ATS or compatibility score was mentioned
    assert "ATS" in data["response"] or "Score" in data["response"] or "score" in data["response"]
    assert any(t["tool"] == "analyze_resume" for t in data.get("tool_executions", []))


def test_agent_skill_gaps_and_courses_instruction(environment, candidate_with_resume):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    payload = {
        "message": "What skills am I missing for GenAI roles? Find courses to learn RAG.",
        "page_context": {"pathname": "/candidate/skill-lab"}
    }
    res = client.post("/api/v1/agent/chat", json=payload, headers=auth)
    assert res.status_code == 200
    data = res.json()

    assert "response" in data
    # Check course cards were returned
    ui_cards = data.get("ui_cards", [])
    assert any(c["type"] in ["course", "skill_gaps"] for c in ui_cards)


def test_agent_interview_creation_instruction(environment, candidate_with_resume):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    payload = {
        "message": "Interview me for a GenAI Engineer position",
        "page_context": {"pathname": "/candidate/interview"}
    }
    res = client.post("/api/v1/agent/chat", json=payload, headers=auth)
    assert res.status_code == 200
    data = res.json()

    ui_cards = data.get("ui_cards", [])
    assert any(c["type"] == "interview_launch" for c in ui_cards)
    assert "Interview" in data["response"] or "interview" in data["response"]


def test_agent_high_risk_action_gating_and_confirmation(environment, candidate_with_resume):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    # 1. User asks agent to apply to jobs -> must trigger confirmation preview!
    payload = {
        "message": "Apply my latest resume to the jobs I selected",
        "page_context": {"pathname": "/candidate/jobs"}
    }
    res = client.post("/api/v1/agent/chat", json=payload, headers=auth)
    assert res.status_code == 200
    data = res.json()

    assert data.get("action_preview") is not None
    action_preview = data["action_preview"]
    assert action_preview["action_type"] == "submit_job_applications"
    assert len(action_preview["targets"]) >= 1

    # 2. Confirm action
    confirm_payload = {
        "action_id": action_preview["action_id"],
        "action_type": action_preview["action_type"],
        "payload": action_preview["payload"],
        "confirmed": True
    }
    conf_res = client.post("/api/v1/agent/confirm-action", json=confirm_payload, headers=auth)
    assert conf_res.status_code == 200
    conf_data = conf_res.json()
    assert conf_data["status"] == "executed"
    assert conf_data["applications_count"] >= 1

    # Verify applications created in database
    apps = db.query(Application).filter(Application.candidate_id == candidate.id).all()
    assert len(apps) >= 1


def test_agent_autonomous_multistep_plan(environment, candidate_with_resume):
    client, db, owner, other, admin, candidate, tmp_path = environment
    auth = headers(owner)

    # Compound high-level goal instruction
    payload = {
        "message": "I want a GenAI Engineer job. Take care of everything.",
        "page_context": {"pathname": "/candidate/dashboard"}
    }
    res = client.post("/api/v1/agent/chat", json=payload, headers=auth)
    assert res.status_code == 200
    data = res.json()

    plan = data.get("plan", [])
    assert len(plan) == 6
    completed_steps = [s for s in plan if s["status"] == "completed"]
    assert len(completed_steps) == 6

    # Response explains comprehensive findings
    resp = data["response"]
    assert len(resp) > 100
    assert "Jayavarapu" in resp or "Candidate" in resp or "resume" in resp.lower()
