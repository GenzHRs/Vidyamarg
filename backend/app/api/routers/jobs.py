"""
VidyaMarg AI — Jobs & Strict Recommendations API Router
======================================================
Endpoints for strict candidate-specific job recommendations based on
the candidate's current active resume, target roles, and verified skills.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import Candidate, User
from app.services.job_recommendation_engine import JobRecommendationEngine

router = APIRouter(tags=["Jobs & Recommendations"])
logger = logging.getLogger("app.api.jobs")


def _get_candidate(user: User, db: Session) -> Candidate:
    cand = db.query(Candidate).filter(Candidate.user_id == user.id).first()
    if not cand:
        cand = Candidate(user_id=user.id, full_name=user.full_name)
        db.add(cand)
        db.commit()
        db.refresh(cand)
    return cand


@router.get("/recommended")
def get_recommended_jobs(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    STRICT TARGET-ROLE & SKILL-BASED JOB RECOMMENDATION
    Returns ONLY jobs that pass the 5-dimension weighted match score (>= 65),
    with hard rejection filtering against the candidate's active resume.
    """
    candidate = _get_candidate(current_user, db)
    return JobRecommendationEngine.get_recommended_jobs(db, candidate.id, limit=limit)
