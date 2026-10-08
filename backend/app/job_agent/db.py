"""
VidyaMarg AI — Job Agent Database Layer (SQLAlchemy Unified Infrastructure).
Replaces legacy raw psycopg2 connection calls with SQLAlchemy SessionLocal engine.
Guarantees full compatibility across PostgreSQL and SQLite database drivers.
"""
import logging
import hashlib
import json as _json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.models.job_models import Job, Company, JobSource
from app.job_agent.url_utils import canonicalize_url

logger = logging.getLogger("app.job_agent.db")

def get_db_session() -> Session:
    """Returns a thread-safe SQLAlchemy SessionLocal instance."""
    return SessionLocal()

def init_db():
    """Initializes schema tables and ensures default JobSource records exist."""
    try:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as session:
            tg_source = session.query(JobSource).filter_by(name="telegram_agent").first()
            if not tg_source:
                tg_source = JobSource(
                    name="telegram_agent",
                    display_name="Telegram Job Agent",
                    source_type="scraper",
                    is_active=True,
                    priority=3
                )
                session.add(tg_source)
                session.commit()
    except Exception as e:
        logger.error(f"Failed to initialize Job Agent DB: {e}")

def get_or_create_telegram_source(session: Session) -> JobSource:
    source = session.query(JobSource).filter_by(name="telegram_agent").first()
    if not source:
        source = JobSource(
            name="telegram_agent",
            display_name="Telegram Job Agent",
            source_type="scraper",
            is_active=True,
            priority=3
        )
        session.add(source)
        session.commit()
        session.refresh(source)
    return source

def is_url_already_processed(url: str) -> bool:
    """Checks if a job URL has already been processed into the DB."""
    if not url:
        return False
    canon_url = canonicalize_url(url)
    with SessionLocal() as session:
        job = session.query(Job).filter(
            (Job.apply_url == url) | (Job.apply_url == canon_url)
        ).first()
        return job is not None

def get_existing_job_by_url(url: str) -> Optional[Dict[str, Any]]:
    """Fetches an existing job record matching the given URL."""
    if not url:
        return None
    canon_url = canonicalize_url(url)
    with SessionLocal() as session:
        job = session.query(Job).filter(
            (Job.apply_url == url) | (Job.apply_url == canon_url)
        ).first()
        if job:
            return {
                "id": job.id,
                "title": job.title,
                "company": job.company_name,
                "location": job.location,
                "salary": job.salary_raw,
                "apply_link": job.apply_url,
            }
    return None

def upsert_job(job_dict: Dict[str, Any], job_hash: str) -> bool:
    """
    Upserts a single job record using SQLAlchemy ORM.
    Returns True if inserted as a new record, False if existing record updated.
    """
    batch_res = upsert_jobs_batch([job_dict])
    return batch_res.get("inserted", 0) > 0

def upsert_jobs_batch(job_records: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Transactional upsert of job records into the SQLAlchemy 'jobs' table.
    Updates existing records if (source_id, external_id) or job_hash matches.
    Preserves all foreign keys, candidate applications, and saved jobs.
    Returns metrics dict: {'inserted': int, 'updated': int, 'failed': int}.
    """
    if not job_records:
        return {"inserted": 0, "updated": 0, "failed": 0}

    now = datetime.now(timezone.utc)
    inserted_count = 0
    updated_count = 0
    failed_count = 0

    with SessionLocal() as session:
        source = get_or_create_telegram_source(session)
        
        for job_dict in job_records:
            try:
                apply_url = job_dict.get("original_link") or job_dict.get("apply_link") or ""
                if apply_url in ("unresolved", "N/A", ""):
                    apply_url = job_dict.get("apply_link") or job_dict.get("email") or "no_link"
                
                canon_url = canonicalize_url(apply_url)
                
                title = (job_dict.get("title") or "Position Opening").strip()[:499]
                company_name = (job_dict.get("company") or "Technology Employer").strip()[:254]
                location_raw = (job_dict.get("location") or "").strip()[:499]
                description = (job_dict.get("raw_text") or job_dict.get("description") or "").strip()
                salary_raw = (job_dict.get("salary") or "").strip()[:254]
                
                skills_raw = job_dict.get("skills") or ""
                if isinstance(skills_raw, list):
                    required_skills = [str(s).strip() for s in skills_raw if str(s).strip()]
                elif isinstance(skills_raw, str):
                    required_skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
                else:
                    required_skills = []

                # Build stable external_id and job_hash
                ext_raw = f"{source.name}:{job_dict.get('channel', 'ch')}:{job_dict.get('message_id', '0')}:{canon_url}"
                external_id = hashlib.sha256(ext_raw.encode("utf-8")).hexdigest()
                
                job_hash_raw = f"{canon_url}:{title.lower()}:{company_name.lower()}"
                job_hash = hashlib.sha256(job_hash_raw.encode("utf-8")).hexdigest()

                is_remote = any(w in location_raw.lower() for w in ["remote", "wfh", "work from home"])
                work_mode = "remote" if is_remote else "onsite"

                posted_at = None
                date_str = job_dict.get("date")
                if date_str:
                    try:
                        posted_at = datetime.fromisoformat(str(date_str))
                    except Exception:
                        posted_at = now

                meta = {
                    "telegram_channel": job_dict.get("channel"),
                    "telegram_message_id": job_dict.get("message_id"),
                    "message_link": job_dict.get("message_link"),
                    "original_link": job_dict.get("original_link"),
                    "email": job_dict.get("email"),
                    "experience": job_dict.get("experience"),
                    "source": source.name,
                }

                # Check if job already exists
                existing_job = session.query(Job).filter(
                    (Job.external_id == external_id) | (Job.job_hash == job_hash) | (Job.apply_url == canon_url)
                ).first()

                if existing_job:
                    # Perform transactional update for changed fields
                    existing_job.title = title
                    existing_job.company_name = company_name
                    if description:
                        existing_job.description = description[:5000]
                    existing_job.apply_url = canon_url[:999]
                    existing_job.location = location_raw
                    existing_job.is_remote = is_remote
                    existing_job.work_mode = work_mode
                    if required_skills:
                        existing_job.required_skills = required_skills
                    if salary_raw:
                        existing_job.salary_raw = salary_raw
                    existing_job.is_active = True
                    existing_job.updated_at = now
                    session.commit()
                    updated_count += 1
                else:
                    # Create new Job record
                    new_job = Job(
                        external_id=external_id,
                        job_hash=job_hash,
                        source_id=source.id,
                        title=title,
                        title_normalized=title.lower(),
                        company_name=company_name,
                        description=description[:5000],
                        apply_url=canon_url[:999],
                        job_url=job_dict.get("message_link") or "",
                        location=location_raw,
                        is_remote=is_remote,
                        work_mode=work_mode,
                        required_skills=required_skills,
                        preferred_skills=[],
                        salary_raw=salary_raw,
                        lifecycle_status="persisted",
                        is_active=True,
                        is_verified=False,
                        trust_score=0.7,
                        quality_score=0.6,
                        freshness_score=1.0,
                        spam_score=0.05,
                        posted_at=posted_at or now,
                        discovered_at=now,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(new_job)
                    session.commit()
                    inserted_count += 1
            except Exception as e:
                logger.error(f"Failed to upsert job record '{job_dict.get('title')}': {e}")
                session.rollback()
                failed_count += 1

    return {"inserted": inserted_count, "updated": updated_count, "failed": failed_count}

def expire_old_telegram_jobs(days: int = 7) -> int:
    """
    Marks Telegram jobs older than `days` days as stale/inactive (is_active = False)
    without deleting database records or disrupting user application history.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    expired_count = 0

    with SessionLocal() as session:
        source = session.query(JobSource).filter_by(name="telegram_agent").first()
        if not source:
            return 0
        
        stale_jobs = session.query(Job).filter(
            Job.source_id == source.id,
            Job.is_active == True,
            Job.posted_at < cutoff
        ).all()

        for j in stale_jobs:
            j.is_active = False
            j.lifecycle_status = "stale"
            j.updated_at = now
            expired_count += 1
        
        session.commit()
    
    return expired_count
