"""
ActiveResumeRAGService — Centralized Active-Resume RAG Context Gateway for VidyamargAI.

All AI features (Career Agent, AI Mentor, Interview Room, Job Matching, Application Autofill, Email)
must retrieve candidate context through this single authoritative gateway.

Architecture & Security rules:
- PostgreSQL is the ONLY source of truth for exact identity and career fields.
- Qdrant is ONLY used for semantic retrieval, strictly filtered by:
    candidate_id == authenticated_candidate_id
    AND resume_id == current_active_resume_id
    AND resume_version == current_active_version
    AND is_active == True
- Redis is CACHE ONLY, stamped with a monotonic candidate context_revision. Stale cache is NEVER returned.
- Zero hallucination guarantee: If evidence is missing, returns "Information not available in your profile."
- Multi-tenant isolation: No query may access unauthenticated or cross-candidate data.
"""
import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session

from app.models.models import Candidate, User
from app.models.resume_center_models import (
    Resume, ResumeVersion, ResumeProfile, ResumeSkill,
    ResumeExperience, ResumeEducation, ResumeProject, ResumeCertification
)
from app.services.resume_context_service import ResumeContextService
from app.services.embedding_service import embedding_service
from app.services.resume_cache import (
    get_candidate_context_revision,
    increment_candidate_context_revision,
    get_cached_active_resume_context,
    set_cached_active_resume_context,
    invalidate_candidate_context
)

logger = logging.getLogger("app.active_resume_rag_service")


class ActiveResumeRAGService:
    """
    Single authoritative candidate-context gateway for the entire VidyaMarg AI platform.
    """

    # ─────────────────────────────────────────────────────────────────────
    # 1. ACTIVE RESUME RESOLUTION
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_active_resume(
        db: Session, candidate_id: int
    ) -> Tuple[Optional[Resume], Optional[ResumeVersion], Optional[Dict[str, Any]]]:
        """Resolves the candidate's single authoritative active resume and latest version."""
        return ResumeContextService.get_active_resume(db, candidate_id)

    # ─────────────────────────────────────────────────────────────────────
    # 2. EXACT PROFILE FIELDS (PostgreSQL → Canonical Source of Truth)
    # ─────────────────────────────────────────────────────────────────────

    @classmethod
    def get_exact_profile(cls, db: Session, candidate_id: int, bypass_cache: bool = False) -> Dict[str, Any]:
        """
        Returns a complete structured profile dictionary driven strictly by the active resume's
        PostgreSQL tables. Never invents data. Uses revision-stamped Redis cache if valid.
        """
        if not bypass_cache:
            cached_data = get_cached_active_resume_context(candidate_id)
            if cached_data:
                return cached_data

        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return {"error": f"Candidate {candidate_id} not found"}

        user = db.query(User).filter(User.id == candidate.user_id).first()
        active_resume, latest_version, structured_data = ResumeContextService.get_active_resume(db, candidate_id)

        current_rev = get_candidate_context_revision(candidate_id)

        if not active_resume:
            result = {
                "candidate_id": candidate_id,
                "context_revision": current_rev,
                "active_resume_id": None,
                "resume_version": None,
                "full_name": user.full_name if user else None,
                "email": user.email if user else None,
                "phone": candidate.phone,
                "location": getattr(candidate, "address", None),
                "primary_designation": candidate.primary_designation,
                "target_roles": _safe_json_list(candidate.target_roles),
                "skills": [],
                "skills_by_category": {},
                "all_skills": [],
                "experience": [],
                "education": [],
                "projects": [],
                "certifications": [],
                "summary": None,
                "links": {},
                "note": "No active resume found.",
            }
            set_cached_active_resume_context(candidate_id, current_rev, result)
            return result

        rid = active_resume.id
        version_num = latest_version.version_number if latest_version else 1

        # Personal info from ResumeProfile
        prof = db.query(ResumeProfile).filter(ResumeProfile.resume_id == rid).first()

        # Skills from ResumeSkill
        skill_rows = db.query(ResumeSkill).filter(ResumeSkill.resume_id == rid).all()
        skills_by_category: Dict[str, List[str]] = {}
        all_skill_names: List[str] = []
        for s in skill_rows:
            cat = s.category or "Other"
            skills_by_category.setdefault(cat, []).append(s.name)
            all_skill_names.append(s.name)

        # Work Experience
        exp_rows = db.query(ResumeExperience).filter(ResumeExperience.resume_id == rid).order_by(ResumeExperience.sort_order.asc()).all()
        experience = [
            {
                "designation": e.designation,
                "employer": e.employer,
                "location": e.employment_location,
                "start_date": e.start_date,
                "end_date": e.end_date,
                "is_current": e.is_current,
                "responsibilities": e.responsibilities or [],
                "technologies": e.technologies or [],
            }
            for e in exp_rows
        ]

        # Education
        edu_rows = db.query(ResumeEducation).filter(ResumeEducation.resume_id == rid).order_by(ResumeEducation.sort_order.asc()).all()
        education = [
            {
                "degree": e.degree,
                "field_of_study": e.field_of_study,
                "institution": e.institution,
                "graduation_year": e.graduation_year or e.end_date,
                "grade": e.grade,
            }
            for e in edu_rows
        ]

        # Projects
        proj_rows = db.query(ResumeProject).filter(ResumeProject.resume_id == rid).order_by(ResumeProject.sort_order.asc()).all()
        projects = [
            {
                "name": p.name,
                "description": p.description,
                "technologies": p.technologies or [],
                "duration": p.duration,
                "results_metrics": p.results_metrics,
                "features": p.features,
                "link": p.link,
            }
            for p in proj_rows
        ]

        # Certifications
        cert_rows = db.query(ResumeCertification).filter(ResumeCertification.resume_id == rid).all()
        certifications = [
            {
                "name": c.name,
                "issuer": c.issuer,
                "year": c.year,
            }
            for c in cert_rows
        ]

        # Links
        links: Dict[str, Optional[str]] = {}
        if prof:
            links = {
                "linkedin": getattr(prof, "linkedin_url", None),
                "github": getattr(prof, "github_url", None),
                "portfolio": getattr(prof, "portfolio_url", None),
            }

        result = {
            "candidate_id": candidate_id,
            "context_revision": current_rev,
            "active_resume_id": rid,
            "resume_version": version_num,
            "full_name": (prof.full_name if prof and prof.full_name else None) or (user.full_name if user else None),
            "email": (prof.email if prof and prof.email else None) or (user.email if user else None),
            "phone": (prof.phone if prof and prof.phone else None) or candidate.phone,
            "location": (prof.location if prof and prof.location else None) or getattr(candidate, "address", None),
            "summary": prof.professional_summary if prof else None,
            "links": links,
            "primary_designation": candidate.primary_designation,
            "target_roles": _safe_json_list(candidate.target_roles),
            "role_evidence": _safe_json_list(candidate.role_evidence),
            "skills_by_category": skills_by_category,
            "all_skills": all_skill_names,
            "experience": experience,
            "education": education,
            "projects": projects,
            "certifications": certifications,
        }

        # Cache with current revision
        set_cached_active_resume_context(candidate_id, current_rev, result)
        return result

    @classmethod
    def get_exact_field(cls, db: Session, candidate_id: int, field_name: str) -> Any:
        """
        Retrieves a single exact field directly from canonical structured profile.
        Never guesses or hallucinates. Returns None if field is missing.
        """
        profile = cls.get_exact_profile(db, candidate_id)
        if field_name in profile:
            return profile[field_name]

        # Lookups for nested convenience fields
        if field_name == "first_name":
            full = profile.get("full_name") or ""
            return full.split()[0] if full else None
        if field_name == "last_name":
            parts = (profile.get("full_name") or "").split(None, 1)
            return parts[1] if len(parts) > 1 else None
        if field_name == "current_company":
            exps = profile.get("experience") or []
            curr = next((e for e in exps if e.get("is_current")), None) or (exps[0] if exps else None)
            return curr.get("employer") if curr else None
        if field_name == "current_title":
            exps = profile.get("experience") or []
            curr = next((e for e in exps if e.get("is_current")), None) or (exps[0] if exps else None)
            return curr.get("designation") if curr else profile.get("primary_designation")

        return None

    # ─────────────────────────────────────────────────────────────────────
    # 3. SEMANTIC SEARCH (Qdrant — Strictly Scoped to Active Resume)
    # ─────────────────────────────────────────────────────────────────────

    @classmethod
    def query_semantic_context(
        cls,
        db: Session,
        candidate_id: int,
        query_text: str,
        top_k: int = 5,
        document_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves semantically relevant sections strictly from the candidate's ACTIVE resume
        in Qdrant. Enforces candidate_id, active resume_id, resume_version, and is_active=True.
        Never returns vectors for another candidate or inactive resume versions.
        """
        try:
            from app.services.vector_store import QdrantVectorStore
            vector_store = QdrantVectorStore()
            if not vector_store.enabled or not vector_store.client:
                logger.info(f"Qdrant vector store disabled — bypassing semantic query for candidate {candidate_id}")
                return []

            active_resume, latest_version, _ = ResumeContextService.get_active_resume(db, candidate_id)
            if not active_resume:
                logger.info(f"No active resume found for candidate {candidate_id} — returning empty semantic context")
                return []

            resume_id = active_resume.id
            resume_version = latest_version.version_number if latest_version else 1

            # Use synchronous embedding to prevent passing coroutine objects
            query_vec = embedding_service.get_embedding_sync(query_text)
            if not query_vec or len(query_vec) != 768:
                logger.warning(f"Failed to generate 768-dim embedding for query: '{query_text[:50]}'")
                return []

            # Enforce multi-tenant and active-resume must filters
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue
            must_conditions = [
                FieldCondition(key="candidate_id", match=MatchValue(value=candidate_id)),
                FieldCondition(key="resume_id", match=MatchValue(value=resume_id)),
                FieldCondition(key="resume_version", match=MatchValue(value=resume_version)),
                FieldCondition(key="is_active", match=MatchValue(value=True)),
            ]
            if document_types and len(document_types) == 1:
                must_conditions.append(
                    FieldCondition(key="document_type", match=MatchValue(value=document_types[0]))
                )

            search_filter = Filter(must=must_conditions)

            results = vector_store.client.search(
                collection_name="candidate_embeddings",
                query_vector=query_vec,
                query_filter=search_filter,
                limit=top_k,
                with_payload=True,
            )

            return [
                {
                    "text": r.payload.get("text", ""),
                    "document_type": r.payload.get("document_type", ""),
                    "section": r.payload.get("section", ""),
                    "score": round(r.score, 4),
                }
                for r in results
            ]

        except Exception as err:
            logger.warning(f"Semantic search failed for candidate {candidate_id}: {err}")
            return []

    # ─────────────────────────────────────────────────────────────────────
    # 4. COMBINED CONTEXT FOR AI PROMPTS
    # ─────────────────────────────────────────────────────────────────────

    @classmethod
    def build_ai_context(
        cls,
        db: Session,
        candidate_id: int,
        query: Optional[str] = None,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        """
        Builds a combined context dictionary for AI feature prompts:
        - Exact structured profile from PostgreSQL.
        - Verified semantic passages from Qdrant (active resume only).
        - Monotonic context_revision stamp.
        """
        profile = cls.get_exact_profile(db, candidate_id)

        semantic_passages: List[Dict] = []
        if query and profile.get("active_resume_id"):
            semantic_passages = cls.query_semantic_context(
                db=db,
                candidate_id=candidate_id,
                query_text=query,
                top_k=top_k,
            )

        return {
            "profile": profile,
            "semantic_passages": semantic_passages,
            "context_revision": profile.get("context_revision", 1),
        }

    # ─────────────────────────────────────────────────────────────────────
    # 5. REVISION & CACHE MANAGEMENT
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_context_revision(candidate_id: int) -> int:
        """Returns the current monotonic context revision for a candidate."""
        return get_candidate_context_revision(candidate_id)

    @staticmethod
    def increment_context_revision(candidate_id: int) -> int:
        """Increments candidate context revision and purges stale Redis cache."""
        return increment_candidate_context_revision(candidate_id)

    @staticmethod
    def clear_candidate_cache(candidate_id: int):
        """Invalidates all cached candidate context across Redis and memory."""
        invalidate_candidate_context(candidate_id)

    # ─────────────────────────────────────────────────────────────────────
    # 6. VECTOR VERIFICATION & INVALIDATION
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def verify_active_resume_index(candidate_id: int, resume_id: int, resume_version: Optional[int] = None) -> bool:
        """Verifies that active resume vectors exist and are retrievable in Qdrant."""
        from app.services.candidate_embedding_service import CandidateEmbeddingService
        return CandidateEmbeddingService.verify_candidate_vectors(candidate_id, resume_id, resume_version)

    @staticmethod
    def invalidate_inactive_vectors(candidate_id: int, old_resume_id: int) -> bool:
        """Marks all Qdrant points for the old resume as is_active=False."""
        try:
            from app.services.vector_store import QdrantVectorStore
            from qdrant_client.http.models import Filter, FieldCondition, MatchValue

            vector_store = QdrantVectorStore()
            if not vector_store.enabled or not vector_store.client:
                return False

            target_filter = Filter(must=[
                FieldCondition(key="candidate_id", match=MatchValue(value=candidate_id)),
                FieldCondition(key="resume_id", match=MatchValue(value=old_resume_id)),
            ])

            vector_store.client.set_payload(
                collection_name="candidate_embeddings",
                payload={"is_active": False},
                points_selector=target_filter,
            )
            logger.info(f"Invalidated Qdrant vectors for candidate {candidate_id} resume {old_resume_id}")
            return True

        except Exception as err:
            logger.warning(f"Failed to invalidate Qdrant vectors for candidate {candidate_id}: {err}")
            return False

    # ─────────────────────────────────────────────────────────────────────
    # 7. COVER LETTER / EMAIL GROUNDED CONTEXT
    # ─────────────────────────────────────────────────────────────────────

    @classmethod
    def generate_cover_letter_context(
        cls,
        db: Session,
        candidate_id: int,
        target_role: str,
        company_name: str,
        job_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates zero-hallucination factual context for recruiter emails and cover letters.
        Extracts verified skills, authentic employment history, and semantic alignment.
        """
        profile = cls.get_exact_profile(db, candidate_id)
        if not profile.get("active_resume_id"):
            return {
                "error": "No active resume found.",
                "available": False
            }

        # Search for semantically relevant experiences matching role/JD
        query = f"{target_role} {job_description or ''}".strip()
        semantic_matches = cls.query_semantic_context(db, candidate_id, query, top_k=3)

        return {
            "available": True,
            "candidate_name": profile.get("full_name") or "Candidate",
            "email": profile.get("email"),
            "phone": profile.get("phone"),
            "target_role": target_role,
            "company_name": company_name,
            "primary_designation": profile.get("primary_designation"),
            "verified_skills": profile.get("all_skills") or [],
            "recent_experience": profile.get("experience")[:2] if profile.get("experience") else [],
            "top_projects": profile.get("projects")[:2] if profile.get("projects") else [],
            "semantic_highlights": [m.get("text") for m in semantic_matches if m.get("text")],
            "instruction": (
                "Ground all statements strictly in the verified skills and real employment history above. "
                "Never fabricate unlisted companies, metrics, or years of experience."
            )
        }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _safe_json_list(value: Optional[str]) -> List[Any]:
    """Safely parses a JSON string to a list. Returns [] on failure."""
    if not value:
        return []
    try:
        result = json.loads(value)
        return result if isinstance(result, list) else [result]
    except Exception:
        return []
