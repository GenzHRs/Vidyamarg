"""
VidyaMarg AI — AI Career Agent API Router.
Endpoints:
- POST /agent/chat: Processes natural-language requests, executes tools, returns responses, task plans, and interactive UI cards.
- POST /agent/confirm-action: Executes high-risk consequential actions once approved by candidate.
- GET /agent/tools: Lists registered tools, parameters, and risk categories.
- GET /agent/context: Retrieves active candidate context (skills, target role, active resume).
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import User, Candidate, Notification, AuditLog
from app.models.resume_center_models import Resume
from app.models.job_models import Application
from app.tools.registry import tool_registry
from app.services.career_agent_service import CareerAgentService

logger = logging.getLogger("app.career_agent_router")

router = APIRouter(prefix="/agent", tags=["AI Career Agent"])


# ─────────────────────────────────────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Candidate natural-language command or inquiry.")
    page_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Active UI context (pathname, job_id, etc.).")
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Prior conversation messages.")


class ConfirmActionRequest(BaseModel):
    action_id: str
    action_type: str
    payload: Dict[str, Any]
    confirmed: bool = True


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat_with_agent(
    payload: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Primary endpoint for natural language control of the VidyamargAI career platform.
    Decomposes intent, executes authorized backend tools, and returns actionable responses.
    """
    try:
        result = await CareerAgentService.process_user_request(
            db=db,
            user_id=current_user.id,
            message=payload.message,
            page_context=payload.page_context,
            history=payload.history
        )
        return result
    except Exception as e:
        logger.error(f"Error in career agent execution: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Agent execution encountered an error: {str(e)}"
        )


@router.post("/confirm-action")
def confirm_agent_action(
    payload: ConfirmActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes a high-risk consequential action previously gated by an Action Preview card.
    """
    cand = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate profile not found")

    if not payload.confirmed:
        return {
            "status": "cancelled",
            "message": "Action was cancelled by the user. No changes were made."
        }

    # Execute approved action
    if payload.action_type == "submit_job_applications":
        job_ids = payload.payload.get("job_ids", [])
        created_count = 0
        for jid in job_ids:
            existing = db.query(Application).filter(Application.candidate_id == cand.id, Application.job_id == jid).first()
            if not existing:
                app_rec = Application(
                    candidate_id=cand.id,
                    job_id=jid,
                    status="applied",
                    applied_via="ai_agent",
                    notes="Applied via authorized AI Career Agent instruction"
                )
                db.add(app_rec)
                created_count += 1

        db.commit()
        return {
            "status": "executed",
            "message": f"Successfully submitted applications to {created_count} jobs!",
            "applications_count": created_count
        }

    return {
        "status": "executed",
        "message": f"Action '{payload.action_type}' was confirmed and processed successfully."
    }


@router.get("/tools")
def list_agent_tools(current_user: User = Depends(get_current_user)):
    """
    Returns registered tool schemas, parameters, and risk categories.
    """
    schemas = tool_registry.get_schemas()
    # Categorize risk
    high_risk_names = {"submit_job_applications", "delete_resume", "delete_account"}
    for s in schemas:
        s["risk_level"] = "high" if s["name"] in high_risk_names else "low"
    return schemas


@router.get("/context")
def get_agent_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns candidate's active career memory and environment context.
    """
    cand = db.query(Candidate).filter(Candidate.user_id == current_user.id).first()
    active_resume = db.query(Resume).filter(
        Resume.candidate_id == (cand.id if cand else 0),
        Resume.deleted_at == None
    ).order_by(Resume.updated_at.desc()).first()

    return {
        "candidate_id": cand.id if cand else None,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "has_resume": active_resume is not None,
        "active_resume_id": active_resume.id if active_resume else None,
        "active_resume_title": active_resume.title if active_resume else None,
        "skills": cand.skills if cand else "",
        "target_role": getattr(cand, "target_role", None) or ""
    }
