"""
VidyaMarg AI — Job Deduplication Utilities.
Computes deterministic job digests and performs database duplicate checking.
"""
import hashlib
from app.job_agent.url_utils import canonicalize_url
from app.core.database import SessionLocal
from app.models.job_models import Job

def generate_job_hash(title: str, company: str, location: str, apply_link: str) -> str:
    canon_url = canonicalize_url(apply_link) if apply_link else ""
    norm_title = (title or "").strip().lower()
    norm_company = (company or "").strip().lower()
    raw_key = f"{canon_url}:{norm_title}:{norm_company}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

def is_duplicate_job(job_hash: str) -> bool:
    if not job_hash:
        return False
    with SessionLocal() as session:
        job = session.query(Job).filter(Job.job_hash == job_hash).first()
        return job is not None
