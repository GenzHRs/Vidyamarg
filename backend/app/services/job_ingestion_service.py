"""
VidyaMarg AI — Unified Job Ingestion & Extraction Service.
Handles structured job payload parsing, SSRF URL security, field validation,
provenance tracking, database ORM persistence, and metrics reporting.
"""
import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.job_models import Job, JobSource, Match
from app.job_agent.url_utils import is_safe_public_url, canonicalize_url
from app.job_agent.db import upsert_jobs_batch, expire_old_telegram_jobs

logger = logging.getLogger("app.services.job_ingestion")

class ExtractedJobSchema(BaseModel):
    title: str = Field(..., min_length=2, max_length=500)
    company: str = Field(..., min_length=1, max_length=255)
    location: Optional[str] = Field(None, max_length=500)
    is_remote: bool = False
    salary_raw: Optional[str] = Field(None, max_length=255)
    experience_raw: Optional[str] = Field(None, max_length=255)
    required_skills: List[str] = Field(default_factory=list)
    description: Optional[str] = Field(None, max_length=10000)
    apply_url: Optional[str] = Field(None, max_length=1000)
    source_url: Optional[str] = Field(None, max_length=1000)
    external_id: Optional[str] = Field(None, max_length=255)
    posted_at: Optional[datetime] = None

class JobIngestionMetrics(BaseModel):
    fetched: int = 0
    extracted: int = 0
    inserted: int = 0
    updated: int = 0
    rejected: int = 0
    failed: int = 0

class JobIngestionService:
    """
    Core orchestrator for Job Discovery Ingestion.
    Extracts, validates, deduplicates, and persists job records with full provenance.
    """

    @staticmethod
    def validate_and_parse_job(raw_job: Dict[str, Any]) -> Tuple[Optional[ExtractedJobSchema], Optional[str]]:
        """
        Validates raw extracted job data against ExtractedJobSchema.
        Validates apply_url for SSRF safety.
        Returns (parsed_schema, rejection_reason).
        """
        title = (raw_job.get("title") or "").strip()
        company = (raw_job.get("company") or raw_job.get("company_name") or "").strip()
        
        if not title or len(title) < 2:
            return None, "Missing or invalid job title"
        if not company or len(company) < 1:
            return None, "Missing company name"

        apply_url = (raw_job.get("apply_link") or raw_job.get("original_link") or raw_job.get("apply_url") or "").strip()
        if apply_url and not is_safe_public_url(apply_url):
            logger.warning(f"Rejecting unsafe/SSRF apply_url: '{apply_url}'")
            return None, "SSRF validation failed: apply_url is internal or untrusted"

        canon_apply_url = canonicalize_url(apply_url) if apply_url else None

        raw_skills = raw_job.get("skills") or raw_job.get("required_skills") or []
        if isinstance(raw_skills, str):
            skills_list = [s.strip() for s in raw_skills.split(",") if s.strip()]
        elif isinstance(raw_skills, list):
            skills_list = [str(s).strip() for s in raw_skills if str(s).strip()]
        else:
            skills_list = []

        location = raw_job.get("location") or None
        is_remote = bool(raw_job.get("is_remote")) or (location and any(w in location.lower() for w in ["remote", "wfh"]))

        ext_id = raw_job.get("external_id") or raw_job.get("message_id")
        if not ext_id:
            ext_id = hashlib.sha256((canon_apply_url or f"{title}:{company}").encode()).hexdigest()[:32]

        try:
            parsed = ExtractedJobSchema(
                title=title,
                company=company,
                location=location,
                is_remote=is_remote,
                salary_raw=raw_job.get("salary") or raw_job.get("salary_raw"),
                experience_raw=raw_job.get("experience") or raw_job.get("experience_raw"),
                required_skills=skills_list,
                description=raw_job.get("raw_text") or raw_job.get("description"),
                apply_url=canon_apply_url,
                source_url=raw_job.get("message_link") or raw_job.get("source_url"),
                external_id=str(ext_id),
                posted_at=datetime.now(timezone.utc)
            )
            return parsed, None
        except Exception as err:
            return None, f"Schema validation error: {err}"

    @classmethod
    def ingest_payload(cls, jobs_payload: List[Dict[str, Any]], source_name: str = "telegram_agent") -> JobIngestionMetrics:
        """
        Executes a complete structured job ingestion run.
        Returns JobIngestionMetrics tracking fetched, extracted, inserted, updated, rejected, and failed items.
        """
        metrics = JobIngestionMetrics(fetched=len(jobs_payload))
        valid_records = []

        for item in jobs_payload:
            parsed, error = cls.validate_and_parse_job(item)
            if parsed:
                metrics.extracted += 1
                record_dict = {
                    "title": parsed.title,
                    "company": parsed.company,
                    "location": parsed.location,
                    "is_remote": parsed.is_remote,
                    "salary": parsed.salary_raw,
                    "experience": parsed.experience_raw,
                    "skills": parsed.required_skills,
                    "raw_text": parsed.description,
                    "apply_link": parsed.apply_url,
                    "original_link": parsed.apply_url,
                    "message_link": parsed.source_url,
                    "external_id": parsed.external_id,
                    "channel": item.get("channel") or source_name,
                    "message_id": item.get("message_id") or parsed.external_id,
                    "date": parsed.posted_at.isoformat() if parsed.posted_at else None,
                }
                valid_records.append(record_dict)
            else:
                metrics.rejected += 1
                logger.info(f"Ingestion rejected record: {error}")

        if valid_records:
            res = upsert_jobs_batch(valid_records)
            metrics.inserted = res.get("inserted", 0)
            metrics.updated = res.get("updated", 0)
            metrics.failed = res.get("failed", 0)

        return metrics
