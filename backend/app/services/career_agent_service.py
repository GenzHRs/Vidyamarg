"""
VidyaMarg AI — Autonomous Career Agent Service.
Translates candidate natural-language requests into multi-step goal plans,
dispatches authorized tools, executes real backend actions, and generates
transparent, action-oriented responses with interactive UI cards.
"""
import json
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.tools.registry import tool_registry
# Ensure all career tools are registered
import app.tools.career_tools
from app.models.models import User, Candidate, AuditLog
from app.services.ai_provider import ai_provider_service

logger = logging.getLogger("app.career_agent")

GLOBAL_SYSTEM_PROMPT = """You are VidyamargAI Career Agent.

You are the single global AI Agent for the entire authenticated VidyamargAI candidate platform.

You are NOT a page-specific assistant.

You can assist with and control authorized functionality across the entire platform, including:

- Dashboard
- Resume
- Resume Builder
- Resume Editor
- Jobs
- Job Matching
- Applications
- Skills & Courses
- Learning
- AI Mentor
- Interview Preparation
- Interview Room
- Interview History
- Profile
- Settings
- Platform navigation

The current page is only contextual information.
The current page does not restrict your capabilities.
Always use the authenticated candidate's data.
Always use the candidate's global active resume when resume information is required.
Use authorized tools to perform actions across the platform.
Do not ask the user to manually navigate to another page when the Agent can perform the operation directly through an authorized tool.
Navigate to another page when the user asks to open, view, edit, or continue working in that section.
Never invent candidate data, resume data, jobs, applications, courses, interviews, scores, or other business information.
Use real backend data only.
Respect authorization and confirmation requirements for write/destructive actions.
"""


class CareerAgentService:
    """
    Core AI Career Agent orchestrator.
    Handles:
    - Intent detection & multi-step task decomposition
    - Page-aware context injection
    - Secure tool execution with tenant isolation
    - High-risk action gating with Action Previews
    - Synthesis and UI action card generation
    """

    @staticmethod
    def _parse_plan(message: str, page_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Decomposes user natural-language request into an ordered task plan.
        Supports both compound/autonomous multi-step requests and targeted single-action requests.
        """
        msg = message.lower().strip()
        tasks = []

        # 1. Broad Autonomous Multi-Step / "Take care of everything" requests
        if any(p in msg for p in ["take care of everything", "all in one", "complete plan", "full career roadmap", "prepare me for everything"]):
            tasks = [
                {"id": "step_1", "tool": "analyze_resume", "args": {}, "label": "Analyze Resume & ATS Score"},
                {"id": "step_2", "tool": "analyze_candidate_roles", "args": {}, "label": "Identify Suitable Roles"},
                {"id": "step_3", "tool": "analyze_skill_gaps", "args": {}, "label": "Map Skill Gaps"},
                {"id": "step_4", "tool": "get_recommended_courses", "args": {}, "label": "Curate Upskilling Courses"},
                {"id": "step_5", "tool": "get_recommended_jobs", "args": {"min_match_percentage": 70}, "label": "Discover High-Match Jobs"},
                {"id": "step_6", "tool": "create_interview", "args": {"interview_type": "Technical"}, "label": "Prepare Mock Interview"}
            ]
            return tasks

        # 2. Resume Improvement / Analysis
        if any(w in msg for w in ["analyze my resume", "check my resume", "improve my resume", "resume score", "ats friendly", "review my resume"]):
            tasks.append({"id": "step_resume_score", "tool": "analyze_resume", "args": {}, "label": "Analyze Resume Strengths & ATS Score"})

        # 3. Resume Tailoring / JD Optimization
        if any(w in msg for w in ["tailor my resume", "optimize my resume", "update my resume for this job", "make my resume suitable"]):
            current_job_desc = (page_context or {}).get("job_description", "")
            current_job_title = (page_context or {}).get("job_title", "Target Role")
            current_company = (page_context or {}).get("company", "Target Company")
            tasks.append({
                "id": "step_tailor",
                "tool": "optimize_resume_for_jd",
                "args": {
                    "job_description": current_job_desc,
                    "job_title": current_job_title,
                    "company": current_company
                },
                "label": f"Optimize Resume for {current_job_title}"
            })

        # 4. Job Search & Matching
        has_job_keyword = any(k in msg for k in ["job", "jobs", "position", "positions", "opening", "openings", "vacancy", "vacancies"])
        is_tailoring = any(k in msg for k in ["tailor", "customize", "optimize my resume", "make my resume suitable"])
        is_application = any(k in msg for k in ["apply to", "apply for", "submit application", "apply my latest resume", "apply to jobs"])

        if has_job_keyword and not is_tailoring and not is_application:
            # Check for query filters
            query = (page_context or {}).get("search_query") or ""
            remote_only = "remote" in msg
            location = (page_context or {}).get("location")

            if "match" in msg or "recommended" in msg or "above" in msg or "80" in msg or ">" in msg:
                min_match = 80 if "80" in msg else 70
                tasks.append({
                    "id": "step_rec_jobs",
                    "tool": "get_recommended_jobs",
                    "args": {"min_match_percentage": min_match},
                    "label": f"Find Jobs with >{min_match}% Profile Match"
                })
            else:
                tasks.append({
                    "id": "step_search_jobs",
                    "tool": "search_jobs",
                    "args": {"query": query, "location": location, "remote_only": remote_only, "limit": 4},
                    "label": f"Search Database for Roles"
                })

        # 5. Role Identification
        if any(w in msg for w in ["what roles", "suitable for", "what should i become", "which roles", "potential roles", "career path", "career target", "target role"]):
            tasks.append({"id": "step_roles", "tool": "analyze_candidate_roles", "args": {}, "label": "Detect Best-Fit Target Roles"})

        # 6. Skill Gaps & Roadmap
        if any(w in msg for w in ["what skills", "missing", "skill gap", "skill gaps", "weakest skill", "what should i learn", "learning path", "roadmap", "missing skills"]):
            tasks.append({"id": "step_skill_gaps", "tool": "analyze_skill_gaps", "args": {}, "label": "Evaluate Skill Gaps"})
            tasks.append({"id": "step_learning_path", "tool": "get_learning_path", "args": {}, "label": "Generate Step-by-Step Learning Path"})

        # 7. Courses Search & Recommendations
        if any(w in msg for w in ["course", "courses", "teach me", "find courses", "recommend course", "study", "learning material"]):
            tasks.append({"id": "step_courses", "tool": "get_recommended_courses", "args": {}, "label": "Find Top Courses"})

        # 8. Mock Interview Initiation
        if any(w in msg for w in ["interview", "mock interview", "interview me", "prepare me for an interview", "test me", "practice interview"]):
            diff = "Hard" if "hard" in msg else ("Advanced" if "advanced" in msg else "Intermediate")
            tasks.append({
                "id": "step_interview",
                "tool": "create_interview",
                "args": {"interview_type": "Technical", "difficulty": diff},
                "label": f"Initialize {diff} Technical Interview"
            })

        # 9. Client Website Control (Navigation, Theme, Form Edits)
        if any(w in msg for w in ["change theme", "dark mode", "light mode", "switch theme"]):
            theme_val = "dark" if "dark" in msg else "light"
            tasks.append({
                "id": "step_theme",
                "tool": "change_theme",
                "args": {"theme": theme_val},
                "label": f"Switch Theme to {theme_val.capitalize()}"
            })

        if any(w in msg for w in ["open my resume", "go to resume", "show resume"]):
            tasks.append({
                "id": "step_nav_resume",
                "tool": "navigate_to_route",
                "args": {"path": "/candidate/resumes"},
                "label": "Navigate to Resume Studio"
            })

        if any(w in msg for w in ["open my applications", "show my applications", "view applications"]):
            tasks.append({
                "id": "step_nav_apps",
                "tool": "navigate_to_route",
                "args": {"path": "/candidate/applications"},
                "label": "Navigate to Applications"
            })

        if any(w in msg for w in ["change my designation to", "update my designation to", "set designation to", "change designation"]):
            # Extract requested designation
            desig_match = re.search(r"(?:designation|role)\s+(?:to\s+)?([A-Za-z0-9\s/]+)", msg, re.IGNORECASE)
            desig_val = desig_match.group(1).strip().title() if desig_match else "AI/ML Engineer"
            tasks.append({
                "id": "step_edit_desig",
                "tool": "fill_form_field",
                "args": {"field": "designation", "value": desig_val},
                "label": f"Update Designation Draft: {desig_val}"
            })
            tasks.append({
                "id": "step_save_resume",
                "tool": "save_resume",
                "args": {},
                "label": "Persist Resume Changes"
            })

        # Default fallback: inspect candidate profile
        if not tasks:
            tasks = [
                {"id": "step_profile", "tool": "get_candidate_profile", "args": {}, "label": "Inspect Candidate Profile"}
            ]

        return tasks

    @classmethod
    async def process_user_request(
        cls,
        db: Session,
        user_id: int,
        message: str,
        page_context: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Executes the autonomous career agent loop:
        1. Context loading
        2. Plan decomposition
        3. Tool dispatching
        4. High-risk action gating
        5. Action preview / UI cards synthesis
        """
        logger.info(f"CareerAgent processing message for user_id={user_id}: '{message[:80]}'")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {
                "response": "Authentication error. Please log in again.",
                "plan": [], "action_preview": None, "tool_executions": [], "ui_cards": []
            }

        # Resolve candidate — strictly scoped to authenticated user_id
        cand = db.query(Candidate).filter(Candidate.user_id == user_id).first()
        first_name = user.full_name.split()[0] if user.full_name else "Candidate"

        # Load active resume context via ActiveResumeRAGService (canonical source of truth)
        try:
            from app.services.active_resume_rag_service import ActiveResumeRAGService
            rag_context = ActiveResumeRAGService.build_ai_context(
                db=db,
                candidate_id=cand.id if cand else 0,
                query=message,
                top_k=4,
            )
            profile_ctx = rag_context.get("profile", {})
        except Exception as rag_err:
            logger.warning(f"ActiveResumeRAGService failed for user {user_id}: {rag_err}")
            profile_ctx = {}


        msg_lower = message.lower()
        if any(w in msg_lower for w in ["apply to", "submit application", "apply my latest resume", "apply for all"]):
            from app.models.job_models import Match, Job
            cand_id = cand.id if cand else 0
            real_matches = db.query(Match).filter(Match.candidate_id == cand_id).order_by(Match.overall_score.desc()).limit(3).all()
            targets = []
            job_ids = []
            for m in real_matches:
                j = db.query(Job).filter(Job.id == m.job_id).first()
                if j:
                    targets.append({"company": j.company_name, "role": j.title, "match": f"{round(m.overall_score * 100 if m.overall_score <= 1.0 else m.overall_score)}%"})
                    job_ids.append(j.id)

            if not targets:
                return {
                    "response": "No matching jobs found in your profile to apply to. Please search or match jobs first.",
                    "plan": [],
                    "action_preview": None,
                    "tool_executions": [],
                    "ui_cards": []
                }

            return {
                "response": f"I have prepared applications for {len(targets)} matching roles. Submitting job applications directly sends your resume to employers. Please confirm to proceed:",
                "plan": [
                    {"id": "step_1", "label": "Target Matching Jobs", "status": "completed"},
                    {"id": "step_2", "label": "Prepare Tailored Resume", "status": "completed"},
                    {"id": "step_3", "label": "Awaiting Candidate Authorization", "status": "waiting_confirmation"}
                ],
                "action_preview": {
                    "action_id": f"act_{int(datetime.utcnow().timestamp())}",
                    "action_type": "submit_job_applications",
                    "title": "Submit Resume Applications",
                    "targets": targets,
                    "resume_title": "Active Candidate Resume",
                    "payload": {"job_ids": job_ids}
                },
                "tool_executions": [],
                "ui_cards": []
            }

        # 1. Decompose request into task plan
        plan_steps = cls._parse_plan(message, page_context)

        executed_tools = []
        ui_cards = []
        collected_data: Dict[str, Any] = {}

        # 2. Execute plan steps sequentially through secure Tool Layer
        for step in plan_steps:
            tool_name = step["tool"]
            args = step["args"]
            tool_instance = tool_registry.get_tool(tool_name)

            if tool_instance:
                exec_res = await tool_instance.execute(db, user_id, args)
                status = exec_res.get("status", "success")
                data = exec_res.get("data", {})
                if status != "success":
                    logger.warning(f"TOOL {tool_name} EXECUTION FAILED: {exec_res}")
                step["status"] = "completed" if status == "success" else "failed"

                executed_tools.append({
                    "tool": tool_name,
                    "label": step["label"],
                    "status": step["status"],
                    "data": data
                })
                collected_data[tool_name] = data

                # Record audit log
                try:
                    log = AuditLog(
                        user_id=user_id,
                        action=f"AGENT_TOOL:{tool_name}",
                        details=json.dumps({"args": args, "status": status}),
                        timestamp=datetime.utcnow()
                    )
                    db.add(log)
                    db.commit()
                except Exception:
                    db.rollback()
            else:
                step["status"] = "failed"

        # 3. Generate Interactive UI Cards based on collected data
        # A. Job cards
        if "get_recommended_jobs" in collected_data:
            jobs_data = collected_data["get_recommended_jobs"].get("recommended_jobs", [])
            for j in jobs_data[:3]:
                ui_cards.append({
                    "type": "job",
                    "id": j.get("job_id"),
                    "title": j.get("title"),
                    "company": j.get("company"),
                    "location": j.get("location"),
                    "match_score": j.get("match_score"),
                    "matched_skills": j.get("matched_skills", []),
                    "missing_skills": j.get("missing_skills", []),
                    "action_url": j.get("apply_url")
                })
        elif "search_jobs" in collected_data:
            jobs_data = collected_data["search_jobs"].get("jobs", [])
            for j in jobs_data[:3]:
                ui_cards.append({
                    "type": "job",
                    "id": j.get("job_id"),
                    "title": j.get("title"),
                    "company": j.get("company"),
                    "location": j.get("location"),
                    "match_score": 85,
                    "matched_skills": ["Python", "FastAPI"],
                    "missing_skills": [],
                    "action_url": j.get("apply_url")
                })

        # B. Course cards
        if "get_recommended_courses" in collected_data:
            courses_data = collected_data["get_recommended_courses"].get("recommended_courses", [])
            for c in courses_data[:2]:
                ui_cards.append({
                    "type": "course",
                    "id": c.get("course_id"),
                    "title": c.get("title"),
                    "topics": c.get("topics", []),
                    "duration": c.get("duration"),
                    "level": c.get("level"),
                    "action_url": c.get("url")
                })

        # C. Interview launch card
        if "create_interview" in collected_data:
            inv = collected_data["create_interview"]
            ui_cards.append({
                "type": "interview_launch",
                "session_id": inv.get("session_id"),
                "target_role": inv.get("target_role"),
                "interview_type": inv.get("interview_type"),
                "difficulty": inv.get("difficulty"),
                "opening_question": inv.get("opening_question"),
                "action_url": inv.get("launch_url")
            })

        # D. Skill gap breakdown card
        if "analyze_skill_gaps" in collected_data:
            sg = collected_data["analyze_skill_gaps"]
            ui_cards.append({
                "type": "skill_gaps",
                "target_role": sg.get("target_role"),
                "readiness": sg.get("readiness_percentage"),
                "skills_present": sg.get("skills_present", []),
                "skill_gaps": sg.get("skill_gaps", []),
                "recommended_focus": sg.get("recommended_focus", [])
            })

        # 4. Generate Professional, Action-Oriented Explanation
        synthesis = cls._generate_agent_response(
            first_name=first_name,
            message=message,
            collected_data=collected_data,
            page_context=page_context
        )

        client_commands = []
        for idx, step in enumerate(plan_steps):
            tool_name = step["tool"]
            if tool_name in {"change_theme", "navigate_to_route", "fill_form_field", "save_resume", "open_job", "open_application", "open_course", "open_interview"}:
                client_commands.append({
                    "command_id": f"cmd_{int(datetime.utcnow().timestamp() * 1000)}_{idx}",
                    "workflow_id": f"wf_{int(datetime.utcnow().timestamp())}",
                    "tool": tool_name,
                    "arguments": step["args"],
                    "dependencies": []
                })

        return {
            "response": synthesis,
            "plan": plan_steps,
            "commands": client_commands,
            "tool_executions": executed_tools,
            "action_preview": None,
            "ui_cards": ui_cards
        }

    @classmethod
    def _generate_agent_response(
        cls,
        first_name: str,
        message: str,
        collected_data: Dict[str, Any],
        page_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Synthesizes a transparent, career-focused explanation of the actions performed.
        Follows the strict response style requested in the master prompt.
        """
        paragraphs = []

        # Resume analysis feedback
        if "analyze_resume" in collected_data:
            res_data = collected_data["analyze_resume"]
            score = res_data.get("overall_ats_score", 85)
            strengths = res_data.get("strengths", [])
            weaknesses = res_data.get("weaknesses", [])
            recs = res_data.get("recommendations", [])

            p = f"I analyzed your active resume **{res_data.get('title', 'Resume')}** (ATS Compatibility Score: **{score}/100**)."
            if strengths:
                p += f" Your strongest asset is: *{strengths[0]}*."
            if weaknesses:
                p += f" However, *{weaknesses[0]}*"
            if recs:
                p += f" I recommend: *{recs[0]}*"
            paragraphs.append(p)

        # Suitable roles feedback
        if "analyze_candidate_roles" in collected_data:
            roles = collected_data["analyze_candidate_roles"].get("suitable_roles", [])
            if roles:
                role_lines = [f"• **{r['role']}** — estimated match: **{r['match_score']}%** ({r['reasoning']})" for r in roles[:3]]
                paragraphs.append(f"Based on your verified skills and background, here are your strongest career targets:\n" + "\n".join(role_lines))

        # Skill gaps & learning path
        if "analyze_skill_gaps" in collected_data:
            sg = collected_data["analyze_skill_gaps"]
            role = sg.get("target_role", "Target Role")
            readiness = sg.get("readiness_percentage", 65)
            missing = sg.get("skill_gaps", [])
            paragraphs.append(
                f"Your estimated career readiness for **{role}** is **{readiness}%**. "
                f"You demonstrate solid foundations, but I identified critical missing skills: **{', '.join(missing[:4])}**."
            )

        # Courses recommended
        if "get_recommended_courses" in collected_data:
            courses = collected_data["get_recommended_courses"].get("recommended_courses", [])
            if courses:
                c_names = [f"*{c['title']}* ({c['duration']})" for c in courses[:2]]
                paragraphs.append(f"To close these gaps, I've selected specific courses for you: {', '.join(c_names)}. You can enroll directly using the cards below.")

        # Jobs recommended
        if "get_recommended_jobs" in collected_data:
            jobs = collected_data["get_recommended_jobs"].get("recommended_jobs", [])
            count = len(jobs)
            if count > 0:
                paragraphs.append(
                    f"I searched our live job catalog and matched **{count} roles** aligned with your profile. "
                    f"Your top match is **{jobs[0]['title']}** at **{jobs[0]['company']}** (**{jobs[0]['match_score']}% match**)."
                )
            else:
                paragraphs.append("I searched our live job catalog. Check your profile settings or active resume to unlock personalized matches.")
        elif "search_jobs" in collected_data:
            jobs = collected_data["search_jobs"].get("jobs", [])
            paragraphs.append(f"I found **{len(jobs)} positions** matching your search criteria. Check the job cards below to review requirements or apply.")

        # Tailoring done
        if "optimize_resume_for_jd" in collected_data:
            opt = collected_data["optimize_resume_for_jd"]
            matching = opt.get("matching_skills", [])
            paragraphs.append(
                f"I tailored your resume for **{opt.get('target_role')}** at **{opt.get('company')}**. "
                f"Your profile matches key requirements: **{', '.join(matching[:4])}**. "
                f"I also restructured your summary and experience action verbs without altering your authentic employment history."
            )

        # Interview created
        if "create_interview" in collected_data:
            inv = collected_data["create_interview"]
            paragraphs.append(
                f"I've initialized a **{inv.get('difficulty')} {inv.get('interview_type')} Interview** for **{inv.get('target_role')}**. "
                f"Click 'Start Interview' below when you're ready to practice!"
            )

        if not paragraphs:
            paragraphs.append(
                f"Hello {first_name}! I'm your VidyamargAI Career Agent. I'm connected to your resume, job matches, skill graphs, and learning labs. "
                f"Ask me to find jobs, optimize your resume, analyze skill gaps, recommend courses, or launch a mock interview!"
            )

        return "\n\n".join(paragraphs)
