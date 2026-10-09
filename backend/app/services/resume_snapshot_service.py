"""
VidyamargAI — Resume Snapshot Service
======================================
Storage-efficient, idempotent service layer for job-specific resume optimization records.

Responsibilities:
  1. Compute deterministic JD hash for idempotency.
  2. get_or_create_optimization — reuse existing record if JD+master already matched.
  3. lock_optimization_as_submitted — freeze record after candidate confirms submission.
  4. get_optimization_for_application — instant fetch via application_id FK.
  5. render_pdf_from_snapshot — deterministic rendering without calling LLM.
  6. render_docx_from_snapshot — deterministic rendering without calling LLM.
  7. preserve_submitted_artifact — store exact PDF in private storage after submission.

Security invariants:
  - Every read/write verifies candidate_id ownership.
  - Submitted records (is_immutable=True) are read-only.
  - No LLM call ever happens in this service.
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.resume_center_models import ResumeOptimization
from app.models.job_models import Application

logger = logging.getLogger("app.resume_snapshot_service")


# ─────────────────────────────────────────────────────────────────────────────
# Hash Utilities
# ─────────────────────────────────────────────────────────────────────────────

def compute_jd_hash(jd_text: str) -> str:
    """
    SHA-256 of normalized JD text.
    Normalizes whitespace to make minor formatting differences irrelevant.
    """
    normalized = " ".join(jd_text.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def compute_content_hash(optimized_data: Dict[str, Any]) -> str:
    """
    SHA-256 of the canonical optimized resume JSON.
    Uses sort_keys=True for determinism regardless of dict key order.
    """
    canonical = json.dumps(optimized_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Idempotent Fetch-or-Check
# ─────────────────────────────────────────────────────────────────────────────

def find_existing_optimization(
    db: Session,
    candidate_id: int,
    master_resume_id: int,
    jd_hash: str,
) -> Optional[ResumeOptimization]:
    """
    Returns an existing optimization record if one exists for the same
    (candidate, master_resume, jd_hash) triple.
    Returns None if no record exists yet.
    """
    return db.query(ResumeOptimization).filter(
        ResumeOptimization.candidate_id == candidate_id,
        ResumeOptimization.master_resume_id == master_resume_id,
        ResumeOptimization.jd_hash == jd_hash
    ).first()


# ─────────────────────────────────────────────────────────────────────────────
# Ownership Verification
# ─────────────────────────────────────────────────────────────────────────────

def verify_optimization_ownership(
    opt: ResumeOptimization,
    candidate_id: int
) -> None:
    """
    Raises HTTP 403 if the optimization record does not belong to the candidate.
    Tenant isolation guard — called before every read or write.
    """
    if opt.candidate_id != candidate_id:
        raise HTTPException(
            status_code=403,
            detail="Access denied: this optimization record belongs to a different candidate."
        )


def get_optimization_by_id(
    db: Session,
    optimization_id: int,
    candidate_id: int
) -> ResumeOptimization:
    """
    Fetch an optimization record and enforce ownership.
    Raises HTTP 404 if not found, HTTP 403 if wrong candidate.
    """
    opt = db.query(ResumeOptimization).filter(
        ResumeOptimization.id == optimization_id
    ).first()
    if not opt:
        raise HTTPException(status_code=404, detail="Optimization record not found.")
    verify_optimization_ownership(opt, candidate_id)
    return opt


# ─────────────────────────────────────────────────────────────────────────────
# Fetch Optimization for a Specific Application
# ─────────────────────────────────────────────────────────────────────────────

def get_optimization_for_application(
    db: Session,
    application_id: int,
    candidate_id: int
) -> Optional[ResumeOptimization]:
    """
    Fetches the saved resume optimization linked to an application.
    Does NOT re-run the optimizer. Returns None if not linked yet.
    Tenant-isolated: verifies candidate_id ownership on both application and optimization.
    """
    app = db.query(Application).filter(
        Application.id == application_id,
        Application.candidate_id == candidate_id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    if not app.optimization_id:
        return None

    opt = db.query(ResumeOptimization).filter(
        ResumeOptimization.id == app.optimization_id
    ).first()
    if not opt:
        return None

    verify_optimization_ownership(opt, candidate_id)
    return opt


# ─────────────────────────────────────────────────────────────────────────────
# Link Optimization to Application
# ─────────────────────────────────────────────────────────────────────────────

def link_optimization_to_application(
    db: Session,
    optimization_id: int,
    application_id: int,
    candidate_id: int,
    commit: bool = False
) -> None:
    """
    Sets applications.optimization_id and resume_optimizations.application_id
    to create a bidirectional link. Safe to call multiple times (idempotent).
    """
    opt = get_optimization_by_id(db, optimization_id, candidate_id)

    app = db.query(Application).filter(
        Application.id == application_id,
        Application.candidate_id == candidate_id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found.")

    # Update both sides
    if app.optimization_id != optimization_id:
        app.optimization_id = optimization_id

    if opt.application_id != application_id:
        opt.application_id = application_id

    if commit:
        db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Submission Locking (Immutability)
# ─────────────────────────────────────────────────────────────────────────────

def lock_optimization_as_submitted(
    db: Session,
    optimization_id: int,
    candidate_id: int,
    artifact_url: Optional[str] = None,
    commit: bool = True
) -> ResumeOptimization:
    """
    Marks an optimization as submitted and immutable.
    - Sets is_submitted=True, is_immutable=True, submitted_at=now.
    - Optionally records the submitted_artifact_url (private storage path of PDF).
    - After calling this, the optimized_data cannot be overwritten.

    Raises HTTP 409 if record is already submitted.
    """
    opt = get_optimization_by_id(db, optimization_id, candidate_id)

    if opt.is_submitted:
        logger.info(f"Optimization {optimization_id} already submitted — no-op.")
        return opt  # Idempotent

    opt.is_submitted = True
    opt.is_immutable = True
    opt.submitted_at = datetime.utcnow()
    if artifact_url:
        opt.submitted_artifact_url = artifact_url

    if commit:
        db.commit()
        db.refresh(opt)

    logger.info(f"Optimization {optimization_id} locked as submitted (is_immutable=True).")
    return opt


def guard_immutable(opt: ResumeOptimization) -> None:
    """
    Raises HTTP 409 if an optimization record is immutable (already submitted).
    Call this before any write operation on a record.
    """
    if opt.is_immutable:
        raise HTTPException(
            status_code=409,
            detail=(
                "This optimization record is locked because the application has already been submitted. "
                "To create a new optimization, please start a new optimization request."
            )
        )


# ─────────────────────────────────────────────────────────────────────────────
# Deterministic PDF Rendering from Saved Snapshot
# ─────────────────────────────────────────────────────────────────────────────

def render_pdf_from_snapshot(
    opt: ResumeOptimization,
    db: Session,
    candidate_id: int,
) -> bytes:
    """
    Renders a PDF from the saved structured snapshot WITHOUT calling any LLM.
    - If opt.submitted_artifact_url is set, retrieves the stored artifact.
    - Otherwise, renders on-demand from opt.optimized_data using the deterministic renderer.
    Returns raw PDF bytes.
    """
    verify_optimization_ownership(opt, candidate_id)

    # Prefer preserved submitted artifact
    if opt.submitted_artifact_url:
        try:
            from app.services.storage import storage_service
            # Parse folder/filename from stored URL path  /api/v1/storage/<folder>/<filename>
            url_path = opt.submitted_artifact_url
            if "/api/v1/storage/" in url_path:
                rel = url_path.split("/api/v1/storage/", 1)[1]
                parts = rel.split("/", 1)
                if len(parts) == 2:
                    folder, filename = parts
                    artifact_bytes = storage_service.get_file_content(folder, filename)
                    if artifact_bytes:
                        logger.info(f"Serving submitted artifact for optimization {opt.id}")
                        return artifact_bytes
        except Exception as e:
            logger.warning(f"Could not retrieve submitted artifact: {e}. Falling back to dynamic render.")

    # Dynamic on-demand rendering from structured data (no LLM)
    from app.services.latex_service import render_structured_data_to_pdf
    from app.models.resume_center_models import ResumeTemplate

    template_slug = "ats-classic"
    if opt.template_id:
        tmpl = db.query(ResumeTemplate).filter(ResumeTemplate.id == opt.template_id).first()
        if tmpl:
            template_slug = tmpl.slug or "ats-classic"

    pdf_bytes = render_structured_data_to_pdf(
        opt.optimized_data,
        title=opt.job_title or "Optimized Resume",
        template_slug=template_slug
    )
    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="PDF rendering failed from saved resume snapshot.")
    return pdf_bytes


def render_docx_from_snapshot(
    opt: ResumeOptimization,
    candidate_id: int,
) -> bytes:
    """
    Renders a DOCX from the saved structured snapshot WITHOUT calling any LLM.
    Returns raw DOCX bytes.
    """
    verify_optimization_ownership(opt, candidate_id)

    from app.services.ats_optimizer import generate_optimized_docx
    docx_bytes = generate_optimized_docx(opt.optimized_data)
    if not docx_bytes:
        raise HTTPException(status_code=500, detail="DOCX rendering failed from saved resume snapshot.")
    return docx_bytes


# ─────────────────────────────────────────────────────────────────────────────
# Preserve Submitted Artifact
# ─────────────────────────────────────────────────────────────────────────────

def preserve_submitted_artifact(
    db: Session,
    opt: ResumeOptimization,
    candidate_id: int,
    pdf_bytes: bytes,
    user_folder: str,
) -> str:
    """
    Saves the exact submitted PDF to private storage and records its URL in the DB.
    Returns the storage URL.
    This should be called ONCE when the candidate confirms submission.
    """
    verify_optimization_ownership(opt, candidate_id)

    from app.services.storage import storage_service
    import re

    safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', opt.job_title or 'Submitted_Resume')
    filename = f"submitted_opt_{opt.id}_{safe_title}.pdf"

    url = storage_service.upload_file(
        folder=f"{user_folder}/submitted_resumes",
        filename=filename,
        content=pdf_bytes,
        mime_type="application/pdf"
    )
    logger.info(f"Preserved submitted artifact for optimization {opt.id} at {url}")
    return url


# ─────────────────────────────────────────────────────────────────────────────
# Build Snapshot Response Payload
# ─────────────────────────────────────────────────────────────────────────────

def build_optimization_response(opt: ResumeOptimization) -> Dict[str, Any]:
    """
    Builds the standard JSON response payload from a ResumeOptimization record.
    Used across get_optimization, reopen_application, etc.
    Never invokes LLM; reads only from saved DB fields.
    """
    report = opt.ats_report or {}
    resume_match_score = report.get("resume_match_score", opt.ats_score)
    score_breakdown = report.get("score_breakdown", {
        "keyword_match": opt.keyword_score,
        "experience_match": opt.experience_score,
        "technical_match": opt.technical_score,
        "responsibility_match": opt.responsibility_score,
        "alignment_score": opt.alignment_score,
        "quality_score": opt.quality_score
    })

    return {
        "optimization_id": opt.id,
        "master_resume_id": opt.master_resume_id,
        "job_id": opt.job_id,
        "application_id": opt.application_id,
        "ats_score": opt.ats_score,
        "resume_match_score": resume_match_score,
        "keyword_match": opt.keyword_score,
        "experience_match": opt.experience_score,
        "technical_match": opt.technical_score,
        "responsibility_match": opt.responsibility_score,
        "alignment_score": opt.alignment_score,
        "quality_score": opt.quality_score,
        "truthfulness_score": opt.truthfulness_score,
        "score_breakdown": score_breakdown,
        "score_explanation": report.get("score_explanation", {}),
        "skill_gaps": report.get("skill_gaps", {}),
        "application_readiness": report.get("application_readiness", {}),
        "prepared_application": report.get("prepared_application", {}),
        "optimized_resume": opt.optimized_data,
        "matched_skills": opt.matched_skills or [],
        "partial_matches": opt.partial_matches or [],
        "missing_skills": opt.missing_skills or [],
        "recommendations": opt.recommendations or [],
        "ats_report": opt.ats_report or {},
        "job_title": opt.job_title,
        "dynamic_title": opt.job_title,
        "generated_title": opt.job_title,
        "company": opt.company,
        "is_submitted": opt.is_submitted,
        "is_immutable": opt.is_immutable,
        "submitted_at": opt.submitted_at.isoformat() if opt.submitted_at else None,
        "submitted_artifact_url": opt.submitted_artifact_url,
        "jd_hash": opt.jd_hash,
        "content_hash": opt.content_hash,
        "optimization_version": opt.optimization_version,
        "template_version": opt.template_version,
        "rendering_mode": getattr(opt, "rendering_mode", "template") or "template",
        "fidelity_tier": getattr(opt, "fidelity_tier", "template_fallback") or "template_fallback",
        "candidate_approved": getattr(opt, "candidate_approved", False) or False,
        "approved_at": opt.approved_at.isoformat() if getattr(opt, "approved_at", None) else None,
        "approval_hash": getattr(opt, "approval_hash", None),
        "approval_notes": getattr(opt, "approval_notes", None),
        "layout_validation_status": getattr(opt, "layout_validation_status", "PASSED") or "PASSED",
        "layout_warnings": getattr(opt, "layout_warnings", []) or [],
        "created_at": opt.created_at.isoformat() if opt.created_at else None,
        "updated_at": opt.updated_at.isoformat() if opt.updated_at else None,
        "evidence_items": [
            {
                "requirement": e.jd_requirement,
                "evidence": e.candidate_evidence,
                "match_type": e.match_type,
                "confidence": e.confidence,
                "category": e.category
            } for e in (opt.evidence_items or [])
        ]
    }
