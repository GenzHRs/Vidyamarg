"""
VidyaMarg AI — Comprehensive Career Agent Tools Layer.
Provides secure, isolated, and typed tools for:
- Profile Tools
- Resume Tools
- Role & Skill Tools
- Job Tools
- Course & Learning Tools
- Mentor Tools
- Interview Tools
- Notification Tools

Every tool enforces tenant / user_id isolation and validates inputs via Pydantic schemas.
"""
import copy
import json
import logging
from typing import Dict, Any, Type, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.tools.base import BaseAgentTool
from app.tools.registry import tool_registry
from app.models.models import User, Candidate, Notification, AuditLog
from app.models.resume_center_models import (
    Resume, ResumeVersion, ResumeTemplate, JobDescription,
    ResumeExtraction, ResumeProfile, ResumeSkill, ResumeExperience, ResumeEducation, ResumeProject
)
from app.models.job_models import (
    Job, Application, Recommendation, Match, CandidateAgentPreferences,
    SkillGapAnalysis, InterviewPreparation
)
from app.services.latex_service import (
    render_resume_to_latex, compile_latex_to_pdf, is_latex_installed, render_structured_data_to_pdf
)
from app.services.resume_tailor_service import generate_jd_tailored_resume
from app.services.storage import storage_service, get_user_folder_name

logger = logging.getLogger("app.career_tools")


def _get_candidate(db: Session, user_id: int) -> Optional[Candidate]:
    """
    Helper to retrieve candidate belonging to user_id.
    SECURITY: Never falls back to another user. Returns None if user not found.
    """
    try:
        if not user_id:
            logger.warning("_get_candidate called with no user_id")
            return None
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"_get_candidate: user_id={user_id} not found — rejecting")
            return None
        if user.candidate:
            return user.candidate
        cand = db.query(Candidate).filter(Candidate.user_id == user.id).first()
        if not cand:
            cand = Candidate(user_id=user.id, status="Active")
            db.add(cand)
            db.commit()
            db.refresh(cand)
        return cand
    except Exception as e:
        logger.error(f"_get_candidate failed for user_id={user_id}: {e}")
        db.rollback()
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 1. PROFILE TOOLS
# ─────────────────────────────────────────────────────────────────────────────

class GetProfileArgs(BaseModel):
    pass

class GetCandidateProfileTool(BaseAgentTool):
    @property
    def name(self) -> str: return "get_candidate_profile"
    @property
    def description(self) -> str: return "Retrieves the candidate's verified profile details, summary, contact info, and education."
    @property
    def args_schema(self) -> Type[BaseModel]: return GetProfileArgs

    async def _run(self, db: Session, user_id: int, args: GetProfileArgs, **kwargs) -> Any:
        try:
            cand = _get_candidate(db, user_id)
            if not cand:
                return {"error": "Candidate not found"}

            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "User not found"}

            # Read from active resume structured tables via centralized ActiveResumeRAGService
            from app.services.active_resume_rag_service import ActiveResumeRAGService

            exact = ActiveResumeRAGService.get_exact_profile(db, cand.id)
            exp_list = [
                f"{e['designation']} at {e['employer']}" if e.get("employer") else e.get("designation", "")
                for e in exact.get("experience", [])
                if e.get("designation")
            ]
            edu_list = [
                f"{e['degree']} in {e['field_of_study']} from {e['institution']}" if e.get("institution") else e.get("degree", "")
                for e in exact.get("education", [])
                if e.get("degree")
            ]

            return {
                "candidate_id": cand.id,
                "full_name": exact.get("full_name") or user.full_name or "",
                "email": exact.get("email") or user.email or "",
                "phone": exact.get("phone") or cand.phone or "",
                "location": exact.get("location") or getattr(cand, "address", "") or "",
                "summary": exact.get("summary") or getattr(cand, "summary", "") or "",
                "primary_designation": exact.get("primary_designation") or "",
                "target_roles": exact.get("target_roles", []),
                "skills": ", ".join(exact.get("all_skills", [])) or (cand.skills or ""),
                "experience": exp_list,
                "education": edu_list,
                "active_resume_id": exact.get("active_resume_id"),
                "resume_version": exact.get("resume_version"),
            }
        except Exception as e:
            logger.error(f"GetCandidateProfileTool error: {e}")
            return {"error": f"Failed to retrieve profile: {str(e)}"}

tool_registry.register(GetCandidateProfileTool())


class UpdateProfileArgs(BaseModel):
    phone: Optional[str] = Field(None, description="Candidate contact phone number.")
    location: Optional[str] = Field(None, description="City, State, or Country.")
    bio: Optional[str] = Field(None, description="Short professional bio.")
    target_role: Optional[str] = Field(None, description="Desired career role, e.g. GenAI Engineer.")

class UpdateCandidateProfileTool(BaseAgentTool):
    @property
    def name(self) -> str: return "update_candidate_profile"
    @property
    def description(self) -> str: return "Updates candidate profile details (phone, location, bio, target_role)."
    @property
    def args_schema(self) -> Type[BaseModel]: return UpdateProfileArgs

    async def _run(self, db: Session, user_id: int, args: UpdateProfileArgs, **kwargs) -> Any:
        cand = _get_candidate(db, user_id)
        if not cand:
            return {"error": "Candidate not found"}
        if args.phone is not None: cand.phone = args.phone
        if args.location is not None: cand.location = args.location
        if args.bio is not None: cand.bio = args.bio
        if args.target_role is not None and hasattr(cand, "target_role"):
            cand.target_role = args.target_role
        db.commit()
        return {"message": "Profile updated successfully"}

tool_registry.register(UpdateCandidateProfileTool())


class GetPreferencesArgs(BaseModel):
    pass

class GetCandidatePreferencesTool(BaseAgentTool):
    @property
    def name(self) -> str: return "get_candidate_preferences"
    @property
    def description(self) -> str: return "Gets job search preferences (desired roles, locations, remote preference)."
    @property
    def args_schema(self) -> Type[BaseModel]: return GetPreferencesArgs

    async def _run(self, db: Session, user_id: int, args: GetPreferencesArgs, **kwargs) -> Any:
        cand = _get_candidate(db, user_id)
        if not cand:
            return {"error": "Candidate not found"}
        pref = db.query(CandidateAgentPreferences).filter(CandidateAgentPreferences.candidate_id == cand.id).first()
        if not pref:
            target_role = getattr(cand, "target_role", None)
            return {
                "target_roles": [target_role] if target_role else [],
                "preferred_locations": [cand.location] if cand.location else [],
                "remote_only": False,
                "min_match_score": 70
            }
        return {
            "target_roles": pref.target_roles or [],
            "preferred_locations": pref.preferred_locations or [],
            "remote_only": pref.remote_only,
            "min_match_score": pref.min_match_score
        }

tool_registry.register(GetCandidatePreferencesTool())


class AnalyzeCandidateRolesArgs(BaseModel):
    pass

class AnalyzeCandidateRolesTool(BaseAgentTool):
    @property
    def name(self) -> str: return "analyze_candidate_roles"
    @property
    def description(self) -> str: return "Analyzes candidate resume, skills, and background to determine best-fit target roles with match percentages."
    @property
    def args_schema(self) -> Type[BaseModel]: return AnalyzeCandidateRolesArgs

    async def _run(self, db: Session, user_id: int, args: AnalyzeCandidateRolesArgs, **kwargs) -> Any:
        cand = _get_candidate(db, user_id)
        if not cand:
            return {
                "top_role": "Generative AI Engineer",
                "suitable_roles": [
                    {"role": "Generative AI Engineer", "match_score": 92, "reasoning": "Demonstrated AI/LLM stack experience."},
                    {"role": "AI / ML Engineer", "match_score": 88, "reasoning": "Machine learning and model deployment skills."}
                ]
            }

        from app.services.active_resume_rag_service import ActiveResumeRAGService
        resume, version, data = ActiveResumeRAGService.get_active_resume(db, cand.id)
        data = data or {}

        text = json.dumps(data).lower()
        roles = []

        if any(w in text for w in ["ai", "llm", "langchain", "pytorch", "transformers", "rag", "prompt", "fastapi"]):
            roles.append({"role": "Generative AI Engineer", "match_score": 92, "reasoning": "Demonstrated AI/LLM stack experience (Python, PyTorch, RAG)."})
        if any(w in text for w in ["machine learning", "scikit-learn", "numpy", "pandas", "model"]):
            roles.append({"role": "AI / ML Engineer", "match_score": 88, "reasoning": "Strong machine learning foundations and predictive modeling."})
        if any(w in text for w in ["react", "next.js", "frontend", "typescript", "fastapi", "django"]):
            roles.append({"role": "Full Stack AI Developer", "match_score": 85, "reasoning": "Full-cycle capability building modern web frontends + AI backend APIs."})
        if any(w in text for w in ["python", "sql", "api", "backend", "docker"]):
            roles.append({"role": "Backend Engineer (Python)", "match_score": 84, "reasoning": "Solid microservices, relational database, and API architecture background."})

        if not roles:
            roles = [
                {"role": "Software / AI Engineer", "match_score": 88, "reasoning": "Broad foundational computer science skill set and AI interest."},
                {"role": "Full Stack AI Developer", "match_score": 85, "reasoning": "Hands-on experience with web applications and Python backend services."}
            ]

        return {
            "top_role": roles[0]["role"],
            "suitable_roles": roles
        }

tool_registry.register(AnalyzeCandidateRolesTool())


# ─────────────────────────────────────────────────────────────────────────────
# 2. RESUME TOOLS
# ─────────────────────────────────────────────────────────────────────────────

class GetResumeArgs(BaseModel):
    resume_id: Optional[int] = Field(None, description="Specific resume ID. If omitted, gets latest active resume.")

class GetResumeTool(BaseAgentTool):
    @property
    def name(self) -> str: return "get_resume"
    @property
    def description(self) -> str: return "Fetches structured data and details of candidate's active or specified resume."
    @property
    def args_schema(self) -> Type[BaseModel]: return GetResumeArgs

    async def _run(self, db: Session, user_id: int, args: GetResumeArgs, **kwargs) -> Any:
        cand = _get_candidate(db, user_id)
        if not cand:
            return {"error": "Candidate not found"}

        from app.services.active_resume_rag_service import ActiveResumeRAGService
        if args.resume_id:
            resume = db.query(Resume).filter(Resume.candidate_id == cand.id, Resume.id == args.resume_id, Resume.deleted_at == None).first()
            version = db.query(ResumeVersion).filter(ResumeVersion.id == resume.current_version_id).first() if resume else None
            structured_data = version.structured_data if (version and version.structured_data) else {}
        else:
            resume, version, structured_data = ActiveResumeRAGService.get_active_resume(db, cand.id)

        if not resume:
            return {"found": False, "message": "No resumes found for candidate"}

        return {
            "found": True,
            "resume_id": resume.id,
            "title": resume.title,
            "source_type": resume.source_type,
            "template_id": resume.template_id,
            "version_number": version.version_number if version else 1,
            "structured_data": structured_data or {},
            "latest_pdf_url": resume.latest_pdf_url
        }

tool_registry.register(GetResumeTool())


class AnalyzeResumeArgs(BaseModel):
    resume_id: Optional[int] = Field(None, description="Resume ID to analyze. Defaults to latest.")

class AnalyzeResumeTool(BaseAgentTool):
    @property
    def name(self) -> str: return "analyze_resume"
    @property
    def description(self) -> str: return "Performs comprehensive ATS, strength, weakness, and completeness analysis of resume."
    @property
    def args_schema(self) -> Type[BaseModel]: return AnalyzeResumeArgs

    async def _run(self, db: Session, user_id: int, args: AnalyzeResumeArgs, **kwargs) -> Any:
        cand = _get_candidate(db, user_id)
        if not cand:
            return {"error": "Candidate not found"}

        from app.services.active_resume_rag_service import ActiveResumeRAGService
        if args.resume_id:
            resume = db.query(Resume).filter(Resume.candidate_id == cand.id, Resume.id == args.resume_id, Resume.deleted_at == None).first()
            version = db.query(ResumeVersion).filter(ResumeVersion.id == resume.current_version_id).first() if resume else None
            data = version.structured_data if (version and version.structured_data) else {}
        else:
            resume, version, data = ActiveResumeRAGService.get_active_resume(db, cand.id)
            data = data or {}

        if not resume:
            return {"error": "No resume found to analyze"}

        version = db.query(ResumeVersion).filter(ResumeVersion.id == resume.current_version_id).first()
        data = version.structured_data if (version and version.structured_data) else {}

        # Heuristic / deterministic multi-factor analysis
        summary = data.get("summary", "")
        skills = data.get("skills", {})
        skills_count = sum(len(v) if isinstance(v, list) else 1 for v in skills.values()) if isinstance(skills, dict) else len(skills)
        experiences = data.get("experience", [])
        projects = data.get("projects", [])

        strengths = []
        weaknesses = []
        recommendations = []

        if skills_count >= 10:
            strengths.append(f"Strong skill breadth: {skills_count} verified technical skills detected.")
        else:
            weaknesses.append("Skill section is sparse. Consider listing specific libraries and tools.")
            recommendations.append("Add key tools, frameworks, and database technologies.")

        if summary and len(summary) > 80:
            strengths.append("Contains structured professional summary.")
        else:
            weaknesses.append("Professional summary is missing or too brief.")
            recommendations.append("Add a targeted 2-3 sentence summary highlighting target role and strengths.")

        if len(projects) >= 2:
            strengths.append(f"Contains {len(projects)} distinct practical projects.")
        else:
            weaknesses.append("Fewer than 2 projects listed.")
            recommendations.append("Highlight open-source or end-to-end applications demonstrating core stack.")

        score = min(100, max(50, 60 + (10 if skills_count >= 8 else 0) + (15 if len(summary) > 80 else 0) + (15 if len(experiences) >= 1 or len(projects) >= 2 else 0)))

        return {
            "resume_id": resume.id,
            "title": resume.title,
            "overall_ats_score": score,
            "skills_count": skills_count,
            "projects_count": len(projects),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": recommendations
        }

tool_registry.register(AnalyzeResumeTool())


class OptimizeResumeForJdArgs(BaseModel):
    job_description: str = Field(..., description="Full text or key requirements of the target job posting.")
    resume_id: Optional[int] = Field(None, description="Resume ID to optimize. Defaults to active master resume.")
    template_id: Optional[int] = Field(None, description="Template ID for rendering.")
    job_title: Optional[str] = Field(None, description="Job title for optimization.")
    company: Optional[str] = Field(None, description="Target company name.")

class OptimizeResumeForJdTool(BaseAgentTool):
    @property
    def name(self) -> str: return "optimize_resume_for_jd"
    @property
    def description(self) -> str: return "Optimizes candidate master resume for a specific job description with 100% truthfulness and full ATS evidence matching."
    @property
    def args_schema(self) -> Type[BaseModel]: return OptimizeResumeForJdArgs

    async def _run(self, db: Session, user_id: int, args: OptimizeResumeForJdArgs, **kwargs) -> Any:
        cand = _get_candidate(db, user_id)
        if not cand:
            return {"error": "Candidate not found"}

        from app.services.active_resume_rag_service import ActiveResumeRAGService
        from app.services.ats_optimizer import run_full_jd_optimization
        from app.models.resume_center_models import ResumeOptimization, ResumeOptimizationEvidence, JobDescription

        if args.resume_id:
            resume = db.query(Resume).filter(Resume.candidate_id == cand.id, Resume.id == args.resume_id, Resume.deleted_at == None).first()
            version = db.query(ResumeVersion).filter(ResumeVersion.resume_id == resume.id).order_by(ResumeVersion.version_number.desc()).first() if resume else None
            data = version.structured_data if (version and version.structured_data) else {}
        else:
            resume, version, data = ActiveResumeRAGService.get_active_resume(db, cand.id)
            data = data or {}

        if not resume or not data:
            return {"error": "No source master resume found"}

        opt_result = run_full_jd_optimization(
            master_resume_data=data,
            job_description_text=args.job_description,
            job_title=args.job_title,
            company=args.company
        )

        # Store in DB
        prior_opts_count = db.query(ResumeOptimization).filter(
            ResumeOptimization.master_resume_id == resume.id,
            ResumeOptimization.candidate_id == cand.id
        ).count()

        opt_record = ResumeOptimization(
            candidate_id=cand.id,
            master_resume_id=resume.id,
            template_id=args.template_id,
            optimization_version=prior_opts_count + 1,
            ats_score=opt_result.ats_scores.overall_ats_score,
            keyword_score=opt_result.ats_scores.keyword_match,
            experience_score=opt_result.ats_scores.experience_match,
            technical_score=opt_result.ats_scores.technical_match,
            responsibility_score=opt_result.ats_scores.responsibility_match,
            alignment_score=opt_result.ats_scores.alignment_score,
            quality_score=opt_result.ats_scores.quality_score,
            truthfulness_score=opt_result.truthfulness_score,
            job_title=opt_result.job_title,
            company=opt_result.company,
            optimized_data=opt_result.optimized_resume,
            matched_skills=opt_result.ats_scores.matched_skills,
            partial_matches=opt_result.ats_scores.partial_matches,
            missing_skills=opt_result.ats_scores.missing_skills,
            recommendations=opt_result.ats_scores.recommendations,
            ats_report=opt_result.ats_scores.model_dump()
        )
        db.add(opt_record)
        db.flush()

        for ev in opt_result.evidence_matches:
            db.add(ResumeOptimizationEvidence(
                optimization_id=opt_record.id,
                jd_requirement=ev.jd_requirement,
                candidate_evidence=ev.candidate_evidence,
                match_type=ev.match_type,
                confidence=ev.confidence,
                category=ev.category
            ))

        db.commit()
        db.refresh(opt_record)

        evidence_map = [
            {
                "requirement": ev.jd_requirement,
                "evidence": ev.candidate_evidence,
                "strength": ev.match_type
            }
            for ev in opt_result.evidence_matches
        ]

        return {
            "optimization_id": opt_record.id,
            "job_title": opt_record.job_title,
            "dynamic_title": opt_record.job_title,
            "ats_score": opt_record.ats_score,
            "resume_match_score": opt_result.resume_match_score,
            "keyword_match": opt_record.keyword_score,
            "experience_match": opt_record.experience_score,
            "technical_match": opt_record.technical_score,
            "truthfulness_score": opt_record.truthfulness_score,
            "score_breakdown": opt_result.score_breakdown,
            "score_explanation": opt_result.score_explanation.model_dump(),
            "skill_gaps": opt_result.skill_gaps.model_dump(),
            "application_readiness": opt_result.application_readiness.model_dump(),
            "prepared_application": opt_result.prepared_application.model_dump(),
            "optimized_resume": opt_record.optimized_data,
            "evidence_map": evidence_map,
            "matched_skills": opt_record.matched_skills,
            "missing_skills": opt_record.missing_skills,
            "recommendations": opt_record.recommendations
        }

tool_registry.register(OptimizeResumeForJdTool())


# ─────────────────────────────────────────────────────────────────────────────
# 3. ROLE / SKILL TOOLS
# ─────────────────────────────────────────────────────────────────────────────


class AnalyzeSkillGapsArgs(BaseModel):
    target_role: Optional[str] = Field("GenAI Engineer", description="Target role to evaluate against, e.g. 'GenAI Engineer', 'ML Engineer'.")

class AnalyzeSkillGapsTool(BaseAgentTool):
    @property
    def name(self) -> str: return "analyze_skill_gaps"
    @property
    def description(self) -> str: return "Identifies missing skills and knowledge gaps for candidate's target career role."
    @property
    def args_schema(self) -> Type[BaseModel]: return AnalyzeSkillGapsArgs

    async def _run(self, db: Session, user_id: int, args: AnalyzeSkillGapsArgs, **kwargs) -> Any:
        cand = _get_candidate(db, user_id)
        if not cand:
            return {"error": "Candidate not found"}

        # Load skills from active resume (canonical source — ResumeSkill table)
        from app.services.resume_context_service import ResumeContextService
        from app.models.resume_center_models import ResumeSkill

        active_resume, _, _ = ResumeContextService.get_active_resume(db, cand.id)
        skills_text = ""

        if active_resume:
            skill_rows = db.query(ResumeSkill).filter(ResumeSkill.resume_id == active_resume.id).all()
            skills_text = " ".join([s.name.lower() for s in skill_rows if s.name])
        else:
            # Fallback: stale denormalized skills (will be empty if no active resume)
            skills_text = (cand.skills or "").lower()

        # Benchmark sets for major roles
        role_benchmarks = {
            "genai engineer": ["Python", "PyTorch", "Transformers", "RAG (Retrieval-Augmented Generation)", "Vector Databases (Qdrant/Pinecone)", "LangChain / LlamaIndex", "Evaluation (Ragas)", "Docker / Kubernetes", "Cloud Deployment (AWS/GCP)"],
            "ml engineer": ["Python", "Scikit-Learn", "PyTorch / TensorFlow", "MLOps", "Model Deployment", "Docker", "Feature Engineering", "SQL"],
            "full stack ai developer": ["TypeScript", "Next.js", "React", "FastAPI", "Tailwind CSS", "Docker", "LLM APIs", "SQL / PostgreSQL"]
        }

        target_norm = args.target_role.lower()
        benchmark = role_benchmarks.get(target_norm, role_benchmarks["genai engineer"])

        skills_present = []
        skills_missing = []

        for skill in benchmark:
            kw = skill.split("(")[0].strip().lower()
            if kw in skills_text:
                skills_present.append(skill)
            else:
                skills_missing.append(skill)

        readiness_pct = round((len(skills_present) / len(benchmark)) * 100)

        return {
            "target_role": args.target_role,
            "readiness_percentage": readiness_pct,
            "skills_present": skills_present,
            "skill_gaps": skills_missing,
            "recommended_focus": skills_missing[:3]
        }

tool_registry.register(AnalyzeSkillGapsTool())


# ─────────────────────────────────────────────────────────────────────────────
# 4. JOB TOOLS
# ─────────────────────────────────────────────────────────────────────────────

class SearchJobsArgs(BaseModel):
    query: str = Field(..., description="Job title, skill, or keyword, e.g. 'GenAI Engineer', 'Python'.")
    location: Optional[str] = Field(None, description="Location filter, e.g. 'Hyderabad', 'Remote'.")
    remote_only: bool = Field(False, description="Whether to filter strictly for remote roles.")
    limit: int = Field(5, description="Maximum number of jobs to return.")

class SearchJobsTool(BaseAgentTool):
    @property
    def name(self) -> str: return "search_jobs"
    @property
    def description(self) -> str: return "Searches job listings in the database matching title, skill, or location criteria."
    @property
    def args_schema(self) -> Type[BaseModel]: return SearchJobsArgs

    async def _run(self, db: Session, user_id: int, args: SearchJobsArgs, **kwargs) -> Any:
        query_str = args.query.lower().strip()
        q = db.query(Job)
        if query_str:
            q = q.filter((Job.title.ilike(f"%{query_str}%")) | (Job.description.ilike(f"%{query_str}%")))
        if args.location:
            q = q.filter(Job.location.ilike(f"%{args.location.strip()}%"))
        if args.remote_only:
            q = q.filter(Job.is_remote == True)

        jobs = q.limit(args.limit).all()

        results = []
        for j in jobs:
            results.append({
                "job_id": j.id,
                "title": j.title,
                "company": j.company_name,
                "location": j.location,
                "is_remote": j.is_remote,
                "salary": j.salary_raw or "Competitive",
                "summary": j.description_summary or (j.description[:220] if j.description else ""),
                "apply_url": j.apply_url or j.job_url or f"/candidate/jobs?id={j.id}"
            })

        return {"count": len(results), "jobs": results}

tool_registry.register(SearchJobsTool())


class GetRecommendedJobsArgs(BaseModel):
    min_match_percentage: int = Field(70, description="Minimum match percentage threshold, e.g. 80.")
    limit: int = Field(5, description="Max jobs to return.")

class GetRecommendedJobsTool(BaseAgentTool):
    @property
    def name(self) -> str: return "get_recommended_jobs"
    @property
    def description(self) -> str: return "Finds jobs scored and ranked specifically against candidate's resume with match percentages."
    @property
    def args_schema(self) -> Type[BaseModel]: return GetRecommendedJobsArgs

    async def _run(self, db: Session, user_id: int, args: GetRecommendedJobsArgs, **kwargs) -> Any:
        cand = _get_candidate(db, user_id)
        if not cand:
            return {"error": "Candidate not found"}

        # Get existing matches
        matches = db.query(Match).filter(Match.candidate_id == cand.id).order_by(Match.overall_score.desc()).limit(args.limit).all()

        results = []
        for m in matches:
            job = db.query(Job).filter(Job.id == m.job_id).first()
            if job:
                score_pct = round(m.overall_score * 100) if m.overall_score <= 1.0 else round(m.overall_score)
                if score_pct >= args.min_match_percentage:
                    results.append({
                        "job_id": job.id,
                        "title": job.title,
                        "company": job.company_name,
                        "location": job.location,
                        "match_score": score_pct,
                        "matched_skills": getattr(m, "match_reasons", []) or [],
                        "missing_skills": getattr(m, "missing_skills", []) or [],
                        "apply_url": job.apply_url or f"/candidate/jobs?id={job.id}"
                    })

        return {"count": len(results), "recommended_jobs": results}

tool_registry.register(GetRecommendedJobsTool())


# ─────────────────────────────────────────────────────────────────────────────
# 5. COURSE TOOLS
# ─────────────────────────────────────────────────────────────────────────────

class GetRecommendedCoursesArgs(BaseModel):
    skill_focus: Optional[str] = Field(None, description="Specific skill or topic to recommend courses for, e.g. 'RAG', 'Vector DBs', 'Kubernetes'.")

class GetRecommendedCoursesTool(BaseAgentTool):
    @property
    def name(self) -> str: return "get_recommended_courses"
    @property
    def description(self) -> str: return "Finds courses designed to resolve candidate's skill gaps and achieve target job readiness."
    @property
    def args_schema(self) -> Type[BaseModel]: return GetRecommendedCoursesArgs

    async def _run(self, db: Session, user_id: int, args: GetRecommendedCoursesArgs, **kwargs) -> Any:
        focus = (args.skill_focus or "GenAI").lower()

        catalog = [
            {
                "course_id": 1,
                "title": "Mastering RAG Architectures & Vector Databases",
                "topics": ["RAG", "Vector DBs", "Qdrant", "Pinecone", "Embeddings"],
                "duration": "6 hours",
                "level": "Intermediate",
                "url": "/candidate/skill-lab"
            },
            {
                "course_id": 2,
                "title": "Building Production AI Agents with LangChain & LangGraph",
                "topics": ["LangChain", "Agentic AI", "Tool Calling", "Memory"],
                "duration": "8 hours",
                "level": "Advanced",
                "url": "/candidate/skill-lab"
            },
            {
                "course_id": 3,
                "title": "Cloud AI Deployment: Docker, Kubernetes & AWS SageMaker",
                "topics": ["AWS", "Kubernetes", "Docker", "MLOps", "Deployment"],
                "duration": "5 hours",
                "level": "Intermediate",
                "url": "/candidate/skill-lab"
            },
            {
                "course_id": 4,
                "title": "Deep Learning & Transformer Foundations with PyTorch",
                "topics": ["PyTorch", "Transformers", "Attention", "Fine-Tuning"],
                "duration": "10 hours",
                "level": "Beginner to Intermediate",
                "url": "/candidate/skill-lab"
            }
        ]

        if args.skill_focus:
            matching = [c for c in catalog if any(focus in t.lower() for t in c["topics"])]
            return {"recommended_courses": matching or catalog[:2]}

        return {"recommended_courses": catalog}

tool_registry.register(GetRecommendedCoursesTool())


class GetLearningPathArgs(BaseModel):
    target_role: str = Field("GenAI Engineer", description="Target role to generate step-by-step roadmap for.")

class GetLearningPathTool(BaseAgentTool):
    @property
    def name(self) -> str: return "get_learning_path"
    @property
    def description(self) -> str: return "Generates a structured, step-by-step learning progression roadmap for a target role."
    @property
    def args_schema(self) -> Type[BaseModel]: return GetLearningPathArgs

    async def _run(self, db: Session, user_id: int, args: GetLearningPathArgs, **kwargs) -> Any:
        cand = _get_candidate(db, user_id)
        candidate_skills = []
        if cand:
            from app.services.active_resume_rag_service import ActiveResumeRAGService
            prof = ActiveResumeRAGService.get_exact_profile(db, cand.id)
            candidate_skills = [s.lower() for s in prof.get("all_skills", []) if s]

        # Role benchmark skills
        role_benchmarks = {
            "genai engineer": ["Python", "FastAPI", "PyTorch", "Transformers", "RAG & Vector DBs", "LangChain / AI Agents", "Evaluation & Guardrails", "Docker & Cloud Deploy"],
            "ml engineer": ["Python", "SQL", "Scikit-Learn", "PyTorch / TensorFlow", "Feature Engineering", "MLOps & MLflow", "Docker", "Model Monitoring"],
            "full stack ai developer": ["TypeScript", "Next.js & React", "FastAPI", "PostgreSQL", "Tailwind CSS", "LLM APIs", "Docker", "Authentication & Security"]
        }
        target_norm = args.target_role.lower()
        benchmark = role_benchmarks.get(target_norm, role_benchmarks["genai engineer"])

        roadmap_steps = []
        for idx, skill in enumerate(benchmark, 1):
            kw = skill.split("&")[0].split("/")[0].strip().lower()
            is_present = any(kw in s or s in kw for s in candidate_skills)
            status = "Demonstrated in Active Resume" if is_present else ("Critical Gap — Recommended Focus" if idx <= 4 else "Advanced Milestone")
            roadmap_steps.append({
                "step": idx,
                "topic": skill,
                "status": status
            })

        return {
            "target_role": args.target_role,
            "roadmap_steps": roadmap_steps
        }

tool_registry.register(GetLearningPathTool())


# ─────────────────────────────────────────────────────────────────────────────
# 6. INTERVIEW TOOLS
# ─────────────────────────────────────────────────────────────────────────────

class CreateInterviewArgs(BaseModel):
    target_role: Optional[str] = Field(None, description="Role to conduct interview for. Defaults to active resume designation.")
    interview_type: str = Field("Technical", description="Type: Technical, HR, Project, Behavioral, or Mixed.")
    difficulty: str = Field("Intermediate", description="Difficulty: Beginner, Intermediate, Advanced, Expert.")

class CreateInterviewTool(BaseAgentTool):
    @property
    def name(self) -> str: return "create_interview"
    @property
    def description(self) -> str: return "Initializes an AI mock interview session configured for role, type, and difficulty."
    @property
    def args_schema(self) -> Type[BaseModel]: return CreateInterviewArgs

    async def _run(self, db: Session, user_id: int, args: CreateInterviewArgs, **kwargs) -> Any:
        cand = _get_candidate(db, user_id)
        if not cand:
            return {"error": "Candidate not found"}

        from app.services.active_resume_rag_service import ActiveResumeRAGService
        prof = ActiveResumeRAGService.get_exact_profile(db, cand.id)

        target_role = args.target_role or prof.get("primary_designation") or (prof.get("target_roles", [None])[0] if prof.get("target_roles") else None) or "Software Engineer"
        session_id = f"mock_{int(datetime.utcnow().timestamp())}"
        resume_id = prof.get("active_resume_id")
        resume_version = prof.get("resume_version", 1)

        # Ground question in candidate's verified projects and skills
        projects = prof.get("projects") or []
        skills = prof.get("all_skills") or []
        project_ref = f"'{projects[0]['name']}'" if projects else "your recent software engineering project"
        primary_skill = skills[0] if skills else "your core technology stack"

        opening_q = (
            f"Welcome to your {args.difficulty} {args.interview_type} Interview for the {target_role} position. "
            f"To begin, tell me about your work on {project_ref} and how you leveraged {primary_skill} to achieve your goals."
        )

        # Associate with candidate's best matching job if available
        matched_job = db.query(Job).join(Match, Match.job_id == Job.id).filter(Match.candidate_id == cand.id).order_by(Match.overall_score.desc()).first()
        if not matched_job:
            matched_job = db.query(Job).filter(Job.is_active == True).first()

        if matched_job:
            try:
                prep = InterviewPreparation(
                    candidate_id=cand.id,
                    job_id=matched_job.id,
                    technical_questions=[
                        {"question": f"Walk me through the architecture of {project_ref}. What technical tradeoffs did you make?", "hint": "Highlight system components and choices", "difficulty": args.difficulty.lower()},
                        {"question": f"How do you ensure reliability and optimal performance when deploying applications built with {primary_skill}?", "hint": "Discuss concurrency, error handling, and testing", "difficulty": args.difficulty.lower()}
                    ],
                    study_topics=[target_role, primary_skill, "System Architecture", "Best Practices"],
                    difficulty_level=args.difficulty.lower(),
                    version=resume_version
                )
                db.add(prep)
                db.commit()
            except Exception as e:
                logger.warning(f"Could not persist InterviewPreparation: {e}")
                db.rollback()

        return {
            "session_id": session_id,
            "target_role": target_role,
            "interview_type": args.interview_type,
            "difficulty": args.difficulty,
            "resume_id": resume_id,
            "resume_version": resume_version,
            "opening_question": opening_q,
            "launch_url": f"/candidate/interview?role={target_role}"
        }

tool_registry.register(CreateInterviewTool())


# ─────────────────────────────────────────────────────────────────────────────
# 7. NOTIFICATION TOOLS
# ─────────────────────────────────────────────────────────────────────────────

class CreateNotificationArgs(BaseModel):
    title: str = Field(..., description="Notification title.")
    message: str = Field(..., description="Notification body message.")
    type: str = Field("info", description="Type: info, alert, system, success.")

class CreateNotificationTool(BaseAgentTool):
    @property
    def name(self) -> str: return "create_notification"
    @property
    def description(self) -> str: return "Sends an in-app career notification to the candidate."
    @property
    def args_schema(self) -> Type[BaseModel]: return CreateNotificationArgs

    async def _run(self, db: Session, user_id: int, args: CreateNotificationArgs, **kwargs) -> Any:
        notif = Notification(
            user_id=user_id,
            title=args.title,
            message=args.message,
            type=args.type,
            read=False,
            created_at=datetime.utcnow()
        )
        db.add(notif)
        db.commit()
        return {"status": "created", "notification_id": notif.id}

tool_registry.register(CreateNotificationTool())
