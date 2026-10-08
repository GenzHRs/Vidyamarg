"""
VidyaMarg AI — AI Application Autofill Service.
Provides canonical form field mapping for external job application sites.
Strictly enforces Plus/Pro subscription entitlement on backend.
Uses PostgreSQL as canonical source of truth and Qdrant for semantic questions.
Zero hallucination guarantee: Returns 'Information not available in your profile' if missing.
"""
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.models import User, Candidate
from app.models.resume_center_models import ResumeExperience, ResumeProject, ResumeSkill
from app.services.resume_context_service import ResumeContextService
from app.services.vector_store import QdrantVectorStore

logger = logging.getLogger("app.autofill_service")

class AutofillService:
    """
    Orchestrates subscription-entitled application form autofilling.
    """

    @classmethod
    def check_subscription_entitlement(cls, user: User) -> Tuple[bool, str]:
        """
        Backend entitlement check:
        Free plan: Blocked with 'AI Application Autofill is available on Plus and Pro. Upgrade to use automatic form filling.'
        Plus / Pro / Admin: Allowed.
        """
        user_tier = (getattr(user, "subscription_tier", "free") or "free").lower()
        user_role = (getattr(user, "role", "candidate") or "candidate").lower()

        if user_role in ("admin", "super_admin"):
            return True, "Authorized (Admin access)"

        if user_tier in ("plus", "pro"):
            return True, f"Authorized ({user_tier.capitalize()} Subscription)"

        return False, "AI Application Autofill is available on Plus and Pro. Upgrade to use automatic form filling."

    @classmethod
    def map_application_form(
        cls,
        db: Session,
        user: User,
        target_url: Optional[str] = None,
        form_fields: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        # 1. Enforce Entitlement
        allowed, msg = cls.check_subscription_entitlement(user)
        if not allowed:
            return {
                "status": "subscription_required",
                "message": msg,
                "can_autofill": False,
                "upgrade_required": True,
                "mapped_fields": {}
            }

        # 2. Get active resume and canonical candidate data from PostgreSQL
        candidate = ResumeContextService.get_candidate_for_user(db, user.id)
        active_res, _, s_data = ResumeContextService.get_active_resume(db, candidate.id)

        if not active_res or not s_data:
            return {
                "status": "no_active_resume",
                "message": "No active resume found. Please upload a resume to enable AI Application Autofill.",
                "can_autofill": False,
                "mapped_fields": {}
            }

        # 3. Canonical Field Mapping from PostgreSQL
        pi = s_data.get("personal_info") or {}
        full_name = candidate.parsed_name or pi.get("full_name") or user.full_name or "Candidate"
        name_parts = full_name.strip().split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        current_exp = db.query(ResumeExperience).filter(
            ResumeExperience.resume_id == active_res.id,
            ResumeExperience.is_current == True
        ).first()
        if not current_exp:
            current_exp = db.query(ResumeExperience).filter(
                ResumeExperience.resume_id == active_res.id
            ).order_by(ResumeExperience.sort_order.asc()).first()

        current_company = current_exp.employer if current_exp else ""
        current_title = current_exp.designation if current_exp else (candidate.primary_designation or "")

        from app.services.active_resume_rag_service import ActiveResumeRAGService
        exact_prof = ActiveResumeRAGService.get_exact_profile(db, candidate.id)
        links = exact_prof.get("links", {}) or {}
        all_skills = ", ".join(exact_prof.get("all_skills", [])) or candidate.skills or cls._not_available()

        canonical_map = {
            "first_name": first_name,
            "last_name": last_name,
            "full_name": exact_prof.get("full_name") or full_name,
            "email": exact_prof.get("email") or candidate.parsed_email or user.email,
            "phone": exact_prof.get("phone") or candidate.phone or pi.get("phone") or cls._not_available(),
            "location": exact_prof.get("location") or candidate.address or pi.get("location") or cls._not_available(),
            "current_company": current_company or cls._not_available(),
            "current_title": current_title or exact_prof.get("primary_designation") or cls._not_available(),
            "primary_designation": exact_prof.get("primary_designation") or current_title or cls._not_available(),
            "skills": all_skills,
            "linkedin": links.get("linkedin") or candidate.linkedin or pi.get("linkedin") or cls._not_available(),
            "github": links.get("github") or candidate.github or pi.get("github") or cls._not_available(),
            "portfolio": links.get("portfolio") or candidate.portfolio or pi.get("portfolio") or cls._not_available(),
        }

        mapped_fields = {}
        if form_fields:
            for field in form_fields:
                field_label = (field.get("label") or field.get("name") or "").lower()
                field_key = cls._match_field_key(field_label)
                if field_key in canonical_map:
                    val = canonical_map[field_key]
                else:
                    val = cls._not_available()
                mapped_fields[field.get("id") or field.get("name") or field_label] = {
                    "label": field.get("label") or field_label,
                    "value": val,
                    "is_available": val != cls._not_available()
                }
        else:
            mapped_fields = {k: {"label": k.replace("_", " ").title(), "value": v, "is_available": v != cls._not_available()} for k, v in canonical_map.items()}

        return {
            "status": "success",
            "message": "Application form mapped successfully using canonical PostgreSQL candidate profile.",
            "can_autofill": True,
            "user_subscription": getattr(user, "subscription_tier", "free"),
            "active_resume_title": active_res.title,
            "mapped_fields": mapped_fields,
            "review_prompt": "Application form is ready. Review and submit?"
        }

    @classmethod
    def answer_semantic_question(cls, db: Session, user: User, question: str) -> Dict[str, Any]:
        allowed, msg = cls.check_subscription_entitlement(user)
        if not allowed:
            return {"status": "subscription_required", "message": msg, "answer": None}

        candidate = ResumeContextService.get_candidate_for_user(db, user.id)
        from app.services.active_resume_rag_service import ActiveResumeRAGService

        # 1. First, search Qdrant via ActiveResumeRAGService for semantically relevant active-resume passages
        semantic_passages = ActiveResumeRAGService.query_semantic_context(
            db=db,
            candidate_id=candidate.id,
            query_text=question,
            top_k=3
        )

        evidence_pieces = []
        if semantic_passages:
            for p in semantic_passages:
                txt = p.get("text", "").strip()
                if txt and len(txt) > 10:
                    evidence_pieces.append(txt)

        # 2. If Qdrant returned no passages (e.g. Qdrant unconfigured), check canonical PostgreSQL tables
        if not evidence_pieces:
            active_res, _, _ = ResumeContextService.get_active_resume(db, candidate.id)
            if active_res:
                projects = db.query(ResumeProject).filter(ResumeProject.resume_id == active_res.id).all()
                exps = db.query(ResumeExperience).filter(ResumeExperience.resume_id == active_res.id).all()
                for p in projects:
                    if p.description:
                        evidence_pieces.append(f"Project '{p.name}': {p.description}")
                for e in exps:
                    if e.responsibilities:
                        evidence_pieces.append(f"Role '{e.designation}' at {e.employer}: {', '.join(e.responsibilities)}")

        if not evidence_pieces:
            return {
                "status": "insufficient_data",
                "answer": cls._not_available(),
                "message": "Information not available in your profile to answer this application question."
            }

        answer_text = f"Based on candidate verified experience: {'; '.join(evidence_pieces[:2])}."
        return {
            "status": "success",
            "question": question,
            "answer": answer_text,
            "evidence_count": len(evidence_pieces)
        }

    @staticmethod
    def _match_field_key(label: str) -> str:
        lbl = label.lower()
        if "first name" in lbl or "given name" in lbl:
            return "first_name"
        if "last name" in lbl or "surname" in lbl:
            return "last_name"
        if "full name" in lbl or "your name" in lbl or "name" in lbl:
            return "full_name"
        if "email" in lbl:
            return "email"
        if "phone" in lbl or "mobile" in lbl or "contact number" in lbl:
            return "phone"
        if "company" in lbl or "employer" in lbl:
            return "current_company"
        if "title" in lbl or "designation" in lbl or "role" in lbl:
            return "primary_designation"
        if "skill" in lbl:
            return "skills"
        if "linkedin" in lbl:
            return "linkedin"
        if "github" in lbl:
            return "github"
        if "portfolio" in lbl or "website" in lbl:
            return "portfolio"
        if "location" in lbl or "city" in lbl or "address" in lbl:
            return "location"
        return label

    @staticmethod
    def _not_available() -> str:
        return "Information not available in your profile."
