"""Compatibility endpoints backed by the authoritative legacy candidate models."""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import Candidate, CandidateProfile

router = APIRouter(prefix="/candidates", tags=["candidates"])

@router.post("")
def create_candidate_account(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    # Signup creates the user and candidate atomically; never accept arbitrary identity input.
    candidate = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not candidate:
        raise HTTPException(409, "No candidate profile. Register using /api/v1/auth/signup.")
    return {"id": str(candidate.id), "name": current_user.full_name, "email": current_user.email, "created_at": candidate.created_at}

@router.get("/profile/{candidate_id}")
def get_candidate_profile(candidate_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(Candidate).filter(Candidate.id == candidate_id)
    if current_user.role not in {"admin", "super_admin"}:
        query = query.filter(Candidate.user_id == current_user.id)
    candidate = query.first()
    if not candidate:
        raise HTTPException(404, "Candidate not found")
    profile = db.query(CandidateProfile).filter(CandidateProfile.candidate_id == candidate.id).order_by(CandidateProfile.created_at.desc()).first()
    if not profile:
        raise HTTPException(404, "Candidate profile record not found")
    def decoded(value, default):
        try:
            return json.loads(value) if value else default
        except (ValueError, TypeError):
            return default
    return {"id": str(profile.id), "candidate_id": str(candidate.id), "summary": candidate.summary,
            "skills_graph": decoded(profile.skills_graph, {}), "experience_graph": decoded(candidate.experience, []),
            "education_graph": decoded(candidate.education, []), "created_at": profile.created_at}
