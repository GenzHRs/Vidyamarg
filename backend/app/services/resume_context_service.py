"""
ResumeContextService — Single source of truth for candidate active resume context across VidyamargAI.
Provides reusable methods for resolving, setting, and synchronizing the candidate's single active resume.
"""
import json
import logging
from typing import Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import Candidate, User
from app.models.resume_center_models import (
    Resume, ResumeVersion, ResumeProfile, ResumeSkill,
    ResumeExperience, ResumeEducation, ResumeProject, ResumeCertification
)
from app.models.job_models import Match
from app.services.role_generator_service import RoleGeneratorService

logger = logging.getLogger("app.resume_context_service")


class ResumeContextService:
    @staticmethod
    def get_candidate_for_user(db: Session, user_id: int) -> Candidate:
        """Resolves Candidate model for user_id, creating one if not present."""
        cand = db.query(Candidate).filter(Candidate.user_id == user_id).first()
        if not cand:
            cand = Candidate(user_id=user_id, status="Active")
            db.add(cand)
            db.commit()
            db.refresh(cand)
        return cand

    @staticmethod
    def get_active_resume(
        db: Session, candidate_id: int
    ) -> Tuple[Optional[Resume], Optional[ResumeVersion], Optional[Dict[str, Any]]]:
        """
        Returns (resume, latest_version, structured_data) for candidate's SINGLE active resume.
        If active_resume_id is not explicitly set, picks the latest non-deleted resume and marks it active.
        """
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return None, None, None

        active_resume = None

        # 1. Check candidate.active_resume_id
        active_resume_id_attr = getattr(candidate, "active_resume_id", None)
        if active_resume_id_attr:
            active_resume = (
                db.query(Resume)
                .filter(
                    Resume.id == active_resume_id_attr,
                    Resume.candidate_id == candidate_id,
                    Resume.deleted_at == None,
                )
                .first()
            )

        # 2. Fallback: query latest active resume
        if not active_resume:
            active_resume = (
                db.query(Resume)
                .filter(
                    Resume.candidate_id == candidate_id,
                    Resume.deleted_at == None,
                    Resume.is_active == True,
                )
                .order_by(Resume.updated_at.desc(), Resume.id.desc())
                .first()
            )

        # 2b. Fallback: query latest non-deleted resume
        if not active_resume:
            active_resume = (
                db.query(Resume)
                .filter(
                    Resume.candidate_id == candidate_id,
                    Resume.deleted_at == None,
                )
                .order_by(Resume.updated_at.desc(), Resume.id.desc())
                .first()
            )
            if active_resume:
                candidate.active_resume_id = active_resume.id
                active_resume.is_active = True
                active_resume.status = "active"
                db.commit()

        if not active_resume:
            return None, None, None

        # Retrieve current/latest version and structured_data
        latest_version = (
            db.query(ResumeVersion)
            .filter(ResumeVersion.resume_id == active_resume.id)
            .order_by(ResumeVersion.version_number.desc())
            .first()
        )

        structured_data = None
        if latest_version and latest_version.structured_data:
            structured_data = latest_version.structured_data
        else:
            structured_data = ResumeContextService.reconstruct_structured_data(db, active_resume.id)

        return active_resume, latest_version, structured_data

    @classmethod
    def replace_active_resume(
        cls, db: Session, candidate_id: int, new_resume_id: int, structured_data: Dict[str, Any]
    ) -> Tuple[Resume, Dict[str, Any]]:
        """
        ATOMIC RESUME REPLACEMENT PIPELINE:
        1. Validates structured extraction.
        2. Generates primary designation & target roles from extracted resume evidence.
        3. Archives all previous candidate resumes (is_active = False, status = "archived").
        4. Sets new_resume.is_active = True, status = "active", candidate.active_resume_id = new_resume_id.
        5. Syncs profile (skills, experience, education, primary_designation, target_roles).
        6. Invalidates old job matches for candidate.
        7. Triggers job match recalculation against active jobs.
        """
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        target_resume = (
            db.query(Resume)
            .filter(
                Resume.id == new_resume_id,
                Resume.candidate_id == candidate_id,
                Resume.deleted_at == None,
            )
            .first()
        )
        if not target_resume:
            raise ValueError(f"Resume {new_resume_id} not found for candidate {candidate_id}")

        # Retrieve previous active resume structured data for diff comparison
        old_resume, _, old_s_data = cls.get_active_resume(db, candidate_id)

        # Perform structured diff comparison
        from app.services.resume_diff_engine import ResumeDiffEngine
        diff_res = ResumeDiffEngine.compare_resumes(
            old_s_data if old_resume and old_resume.id != new_resume_id else None,
            structured_data
        )
        logger.info(f"Resume Diff Result candidate {candidate_id}: {diff_res['change_level']} -> {diff_res['details']}")

        # Conditionally regenerate roles ONLY if MEANINGFUL_CHANGE or initial upload
        role_res = {}
        if diff_res["change_level"] == "MEANINGFUL_CHANGE" or not candidate.primary_designation:
            role_res = RoleGeneratorService.generate_roles_from_resume(structured_data)
            candidate.primary_designation = role_res.get("primary_designation")
            candidate.target_roles = json.dumps(role_res.get("target_roles", []))
            candidate.role_evidence = json.dumps(role_res.get("role_evidence", []))
        else:
            target_roles_list = []
            if candidate.target_roles:
                try:
                    target_roles_list = json.loads(candidate.target_roles)
                except Exception:
                    target_roles_list = [candidate.primary_designation] if candidate.primary_designation else []
            
            role_evidence_list = []
            if candidate.role_evidence:
                try:
                    role_evidence_list = json.loads(candidate.role_evidence)
                except Exception:
                    role_evidence_list = []

            role_res = {
                "primary_designation": candidate.primary_designation,
                "target_roles": target_roles_list,
                "role_evidence": role_evidence_list,
                "preserved_existing_roles": True
            }

        # ── STEP 1: Index and verify Resume B vectors in Qdrant BEFORE touching Resume A ──
        # If Qdrant vector store is active, indexing must verify before Resume A is deactivated.
        from app.services.vector_store import QdrantVectorStore
        vector_store = QdrantVectorStore()
        
        if vector_store.enabled and vector_store.client:
            from app.services.candidate_embedding_service import CandidateEmbeddingService
            indexed_ok = CandidateEmbeddingService.index_candidate_resume(
                db, candidate.id, new_resume_id, structured_data
            )
            if not indexed_ok:
                logger.error(f"Vector indexing and verification failed for Resume {new_resume_id}. Aborting replacement — Resume {old_resume.id if old_resume else 'None'} remains active.")
                target_resume.is_active = False
                target_resume.status = "failed"
                target_resume.extraction_status = "failed"
                db.commit()
                raise RuntimeError(f"Qdrant indexing and verification failed for resume {new_resume_id}. Previous active resume was preserved.")
            logger.info(f"Qdrant indexing and verification succeeded for candidate {candidate_id} resume {new_resume_id}")

        # ── STEP 2: ONLY NOW deactivate previous resumes and activate Resume B ──
        db.query(Resume).filter(
            Resume.candidate_id == candidate_id,
            Resume.id != new_resume_id,
        ).update({"is_active": False, "status": "archived"}, synchronize_session=False)

        target_resume.is_active = True
        target_resume.status = "active"
        target_resume.extraction_status = "extracted"
        candidate.active_resume_id = target_resume.id

        # Sync profile fields in PostgreSQL
        cls.sync_candidate_profile(db, candidate, structured_data)

        # Invalidate old job matches for candidate
        db.query(Match).filter(Match.candidate_id == candidate_id).delete(synchronize_session=False)

        # Invalidate old resume Qdrant vectors
        if old_resume and old_resume.id != new_resume_id:
            try:
                from app.services.active_resume_rag_service import ActiveResumeRAGService
                ActiveResumeRAGService.invalidate_inactive_vectors(candidate_id, old_resume.id)
            except Exception as inv_err:
                logger.warning(f"Could not invalidate old Qdrant vectors for resume {old_resume.id}: {inv_err}")

        # Commit DB updates
        db.commit()
        db.refresh(target_resume)
        db.refresh(candidate)

        # ── STEP 3: Increment Context Revision & Clear Stale Caches ──
        try:
            from app.services.active_resume_rag_service import ActiveResumeRAGService
            ActiveResumeRAGService.increment_context_revision(candidate_id)
        except Exception as rev_err:
            logger.warning(f"Failed to increment context revision for candidate {candidate_id}: {rev_err}")

        # ── STEP 4: Recalculate dependent job matches ──
        try:
            from app.api.routers.job_agent import _auto_ensure_candidate_matches
            _auto_ensure_candidate_matches(candidate_id, db)
        except Exception as e:
            logger.warning(f"Failed auto job match recalculation after active resume update: {e}")

        return target_resume, role_res

    @classmethod
    def handle_extraction_failure(cls, db: Session, candidate_id: int, failed_resume_id: int, error_msg: str):
        """
        Failure protection rule: If new resume extraction fails, mark failed resume as failed (is_active = False).
        DO NOT touch previous active resume. Previous active resume remains active.
        """
        failed_resume = db.query(Resume).filter(Resume.id == failed_resume_id).first()
        if failed_resume:
            failed_resume.is_active = False
            failed_resume.status = "failed"
            failed_resume.extraction_status = "failed"
            db.commit()

    @staticmethod
    def set_active_resume(db: Session, candidate_id: int, resume_id: int) -> Resume:
        """Sets an existing resume as the active resume for candidate."""
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found")

        target_resume = (
            db.query(Resume)
            .filter(
                Resume.id == resume_id,
                Resume.candidate_id == candidate_id,
                Resume.deleted_at == None,
            )
            .first()
        )
        if not target_resume:
            raise ValueError(f"Resume {resume_id} not found for candidate {candidate_id}")

        # Get structured data for role generation
        _, _, s_data = ResumeContextService.get_active_resume_details(db, target_resume)
        return ResumeContextService.replace_active_resume(db, candidate_id, resume_id, s_data or {})[0]

    activate_resume = set_active_resume

    @staticmethod
    def get_active_resume_details(
        db: Session, resume: Resume
    ) -> Tuple[Resume, Optional[ResumeVersion], Optional[Dict[str, Any]]]:
        latest_version = (
            db.query(ResumeVersion)
            .filter(ResumeVersion.resume_id == resume.id)
            .order_by(ResumeVersion.version_number.desc())
            .first()
        )
        s_data = latest_version.structured_data if latest_version else None
        if not s_data:
            s_data = ResumeContextService.reconstruct_structured_data(db, resume.id)
        return resume, latest_version, s_data

    @staticmethod
    def sync_candidate_profile(db: Session, candidate: Candidate, s_data: Dict[str, Any]):
        """Synchronizes active resume skills, experience, education to candidate profile."""
        try:
            profile = s_data.get("personal_info") or s_data.get("profile") or {}
            skills = s_data.get("skills", {})
            summary_info = s_data.get("professional_summary") or {}
            experience = s_data.get("work_experience") or s_data.get("experience") or []
            education = s_data.get("education") or []

            # 1. Skills
            skill_names = []
            if isinstance(skills, list):
                skill_names = [s.get("name", "") if isinstance(s, dict) else str(s) for s in skills if s]
            elif isinstance(skills, dict):
                if skills.get("all_raw_skills"):
                    skill_names = skills.get("all_raw_skills", [])
                else:
                    for k, v in skills.items():
                        if isinstance(v, list):
                            skill_names.extend(v)
            if skill_names:
                candidate.skills = ", ".join(list(dict.fromkeys([str(s).strip() for s in skill_names if s])))

            # 2. Profile Info
            if isinstance(profile, dict):
                if profile.get("summary"):
                    candidate.summary = profile.get("summary")
                elif isinstance(summary_info, dict) and summary_info.get("summary"):
                    candidate.summary = summary_info.get("summary")

                if profile.get("phone"):
                    candidate.phone = profile.get("phone")
                if profile.get("full_name"):
                    candidate.parsed_name = profile.get("full_name")
                if profile.get("email"):
                    candidate.parsed_email = profile.get("email")

            if education and isinstance(education, (list, dict)):
                candidate.education = json.dumps(education) if isinstance(education, list) else json.dumps([education])
            if experience and isinstance(experience, (list, dict)):
                candidate.experience = json.dumps(experience) if isinstance(experience, list) else json.dumps([experience])
            projects = s_data.get("projects") or []
            if projects and isinstance(projects, (list, dict)):
                candidate.projects = json.dumps(projects) if isinstance(projects, list) else json.dumps([projects])

        except Exception as err:
            logger.warning(f"Failed to sync active resume to candidate profile: {err}")

    @staticmethod
    def reconstruct_structured_data(db: Session, resume_id: int) -> Dict[str, Any]:
        """Reconstructs structured_data dict from normalized tables if json version absent."""
        prof = db.query(ResumeProfile).filter(ResumeProfile.resume_id == resume_id).first()
        skills = db.query(ResumeSkill).filter(ResumeSkill.resume_id == resume_id).all()
        exps = db.query(ResumeExperience).filter(ResumeExperience.resume_id == resume_id).all()
        edus = db.query(ResumeEducation).filter(ResumeEducation.resume_id == resume_id).all()
        projs = db.query(ResumeProject).filter(ResumeProject.resume_id == resume_id).all()

        return {
            "personal_info": {
                "full_name": prof.full_name if prof else "",
                "email": prof.email if prof else "",
                "phone": prof.phone if prof else "",
                "location": prof.location if prof else "",
                "summary": prof.professional_summary if prof else "",
            },
            "skills": [{"name": s.name, "category": s.category} for s in skills] if skills else [],
            "work_experience": [
                {
                    "title": e.designation,
                    "designation": e.designation,
                    "role": e.designation,
                    "job_title": e.designation,
                    "company": e.employer,
                    "employer": e.employer,
                    "employment_location": e.employment_location,
                    "location": e.employment_location,
                    "start_date": e.start_date,
                    "end_date": e.end_date,
                    "is_current": e.is_current,
                    "responsibilities": e.responsibilities or [],
                    "bullets": e.responsibilities or [],
                }
                for e in exps
            ] if exps else [],
            "experience": [
                {
                    "title": e.designation,
                    "designation": e.designation,
                    "role": e.designation,
                    "job_title": e.designation,
                    "company": e.employer,
                    "employer": e.employer,
                    "employment_location": e.employment_location,
                    "location": e.employment_location,
                    "start_date": e.start_date,
                    "end_date": e.end_date,
                    "is_current": e.is_current,
                    "responsibilities": e.responsibilities or [],
                    "bullets": e.responsibilities or [],
                }
                for e in exps
            ] if exps else [],
            "education": [
                {
                    "degree": ed.degree,
                    "field_of_study": ed.field_of_study,
                    "institution": ed.institution,
                    "graduation_year": ed.graduation_year or ed.end_date,
                }
                for ed in edus
            ] if edus else [],
            "projects": [
                {
                    "name": pr.name,
                    "title": pr.name,
                    "description": pr.description,
                    "technologies": pr.technologies or [],
                    "responsibilities": pr.responsibilities or [],
                    "bullets": pr.responsibilities or [],
                }
                for pr in projs
            ] if projs else [],
        }
