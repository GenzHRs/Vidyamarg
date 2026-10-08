"""
VidyaMarg AI — AI Application Autofill API Router.
Exposes endpoints for mapping job application form fields and answering semantic questions.
Backend strictly enforces Plus/Pro subscription entitlements.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import User
from app.services.autofill_service import AutofillService

logger = logging.getLogger("app.api.autofill")

router = APIRouter(tags=["AI Application Autofill"])

class FormFieldSchema(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    label: Optional[str] = None
    field_type: Optional[str] = None

class AutofillRequest(BaseModel):
    target_url: Optional[str] = None
    form_fields: Optional[List[FormFieldSchema]] = None

class SemanticQuestionRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)

@router.get("/status")
def check_autofill_entitlement(
    current_user: User = Depends(get_current_user)
):
    """
    Checks user's subscription entitlement for AI Application Autofill.
    """
    allowed, message = AutofillService.check_subscription_entitlement(current_user)
    return {
        "can_autofill": allowed,
        "subscription_tier": getattr(current_user, "subscription_tier", "free"),
        "message": message
    }

@router.post("/map")
def map_application_form(
    request: AutofillRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Maps form fields from canonical PostgreSQL candidate data.
    Enforces Plus/Pro subscription entitlement.
    """
    fields_list = [f.dict() for f in request.form_fields] if request.form_fields else None
    result = AutofillService.map_application_form(
        db, current_user, target_url=request.target_url, form_fields=fields_list
    )
    if not result.get("can_autofill") and result.get("status") == "subscription_required":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.get("message")
        )
    return result

@router.post("/semantic-question")
def answer_semantic_question(
    request: SemanticQuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Answers an open-ended application question using Qdrant semantic search over candidate evidence.
    Enforces Plus/Pro subscription entitlement.
    """
    result = AutofillService.answer_semantic_question(db, current_user, request.question)
    if result.get("status") == "subscription_required":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.get("message")
        )
    return result
