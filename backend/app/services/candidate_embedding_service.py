"""
VidyaMarg AI — Candidate Embedding Service.
Generates semantic embeddings for candidate resume sections and indexes them in Qdrant
with payload metadata (candidate_id, resume_id, document_type, version, timestamp).
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.services.vector_store import QdrantVectorStore
from app.services.embedding_service import embedding_service

logger = logging.getLogger("app.candidate_embedding_service")

class CandidateEmbeddingService:
    """
    Indexes candidate profile sections into Qdrant for semantic search and Q&A.
    PostgreSQL remains the canonical source of truth for exact data.
    """

    @classmethod
    def index_candidate_resume(
        cls, db: Session, candidate_id: int, resume_id: int, structured_data: Dict[str, Any]
    ) -> bool:
        try:
            vector_store = QdrantVectorStore()
            if not vector_store.enabled:
                logger.info(f"Qdrant disabled or unconfigured; bypassing vector indexing for candidate {candidate_id}")
                return False

            # Ensure collections exist
            vector_store.init_collections()

            # Resolve resume version number for payload metadata
            resume_version = 1
            try:
                from app.models.resume_center_models import ResumeVersion
                latest_ver = (
                    db.query(ResumeVersion)
                    .filter(ResumeVersion.resume_id == resume_id)
                    .order_by(ResumeVersion.version_number.desc())
                    .first()
                )
                if latest_ver:
                    resume_version = latest_ver.version_number
            except Exception as ver_err:
                logger.warning(f"Could not resolve resume version for resume {resume_id}: {ver_err}")

            sections = cls._extract_indexable_sections(structured_data)
            now_iso = datetime.now(timezone.utc).isoformat()

            points = []
            for idx, sec in enumerate(sections):
                doc_type = sec["document_type"]
                sec_name = sec.get("section", doc_type)
                text_content = sec["text"]
                if not text_content or len(text_content.strip()) < 5:
                    continue

                # Use synchronous embedding generation to avoid passing coroutine objects
                emb = embedding_service.get_embedding_sync(text_content)
                if not emb or len(emb) != 768:
                    continue

                point_id = int(f"{candidate_id}{resume_id}{idx}")
                payload = {
                    "candidate_id": candidate_id,
                    "resume_id": resume_id,
                    "resume_version": resume_version,
                    "document_type": doc_type,
                    "section": sec_name,
                    "text": text_content,
                    "is_active": True,
                    "created_at": now_iso,
                    "updated_at": now_iso
                }
                points.append({
                    "id": point_id,
                    "vector": emb,
                    "payload": payload
                })

            if points and vector_store.client:
                # Upsert into candidate_embeddings collection
                try:
                    from qdrant_client.http.models import PointStruct
                    q_points = [PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"]) for p in points]
                    vector_store.client.upsert(collection_name="candidate_embeddings", points=q_points)
                    logger.info(f"Successfully indexed {len(q_points)} sections in Qdrant for candidate {candidate_id} resume {resume_id} v{resume_version}")
                    
                    # Verify points were persisted
                    is_verified = cls.verify_candidate_vectors(candidate_id, resume_id, resume_version)
                    return is_verified
                except Exception as e:
                    logger.warning(f"Failed to upsert points in Qdrant: {e}")
                    return False

            return False
        except Exception as err:
            logger.warning(f"Candidate embedding indexing failed: {err}")
            return False

    @classmethod
    def verify_candidate_vectors(
        cls, candidate_id: int, resume_id: int, resume_version: Optional[int] = None
    ) -> bool:
        """
        Confirms that candidate vectors for this active resume version exist and are searchable in Qdrant.
        """
        try:
            vector_store = QdrantVectorStore()
            if not vector_store.enabled or not vector_store.client:
                return True  # If Qdrant is unconfigured, return True to avoid blocking DB-only mode

            from qdrant_client.http.models import Filter, FieldCondition, MatchValue
            must_conds = [
                FieldCondition(key="candidate_id", match=MatchValue(value=candidate_id)),
                FieldCondition(key="resume_id", match=MatchValue(value=resume_id)),
                FieldCondition(key="is_active", match=MatchValue(value=True)),
            ]
            if resume_version is not None:
                must_conds.append(FieldCondition(key="resume_version", match=MatchValue(value=resume_version)))

            query_filter = Filter(must=must_conds)
            count_res = vector_store.client.count(
                collection_name="candidate_embeddings",
                count_filter=query_filter,
                exact=True
            )
            count = getattr(count_res, "count", 0)
            logger.info(f"Verified {count} active vectors in Qdrant for candidate {candidate_id} resume {resume_id}")
            return count > 0
        except Exception as err:
            logger.warning(f"Failed to verify candidate vectors in Qdrant: {err}")
            return False

    @classmethod
    def _extract_indexable_sections(cls, data: Dict[str, Any]) -> List[Dict[str, str]]:
        sections = []
        
        # 1. Summary
        pi = data.get("personal_info") or data.get("profile") or {}
        summary = pi.get("summary") or (data.get("professional_summary") or {}).get("summary")
        if summary:
            sections.append({
                "document_type": "resume_summary",
                "section": "summary",
                "text": str(summary)
            })

        # 2. Skills
        skills = data.get("skills") or []
        if skills:
            if isinstance(skills, list):
                skill_str = ", ".join([s.get("name", "") if isinstance(s, dict) else str(s) for s in skills if s])
            elif isinstance(skills, dict):
                skill_names = []
                for cat, sk_list in skills.items():
                    if isinstance(sk_list, list):
                        skill_names.extend([str(x) for x in sk_list])
                    else:
                        skill_names.append(str(sk_list))
                skill_str = ", ".join(skill_names)
            else:
                skill_str = str(skills)
            if skill_str.strip():
                sections.append({
                    "document_type": "skills",
                    "section": "skills",
                    "text": f"Candidate Technical & Professional Skills: {skill_str}"
                })

        # 3. Work Experience (all items preserved)
        exps = data.get("work_experience") or data.get("experience") or []
        if isinstance(exps, list) and exps:
            for exp in exps:
                if isinstance(exp, dict):
                    title = exp.get("title") or exp.get("designation") or ""
                    emp = exp.get("employer") or exp.get("company") or ""
                    loc = exp.get("employment_location") or exp.get("location") or ""
                    dates = f"{exp.get('start_date', '')} - {exp.get('end_date', '')}".strip(" -")
                    resp_list = exp.get("responsibilities") or exp.get("bullets") or []
                    bullets = " ".join([str(b) for b in resp_list if b])
                    tech = ", ".join(exp.get("technologies", []) or [])
                    
                    parts = []
                    if title or emp:
                        parts.append(f"Role: {title} at {emp}".strip())
                    if loc:
                        parts.append(f"Location: {loc}")
                    if dates:
                        parts.append(f"Dates: {dates}")
                    if bullets:
                        parts.append(f"Responsibilities & Achievements: {bullets}")
                    if tech:
                        parts.append(f"Technologies: {tech}")
                        
                    exp_text = " | ".join(parts)
                    if len(exp_text.strip()) > 5:
                        sections.append({
                            "document_type": "experience",
                            "section": "work_experience",
                            "text": exp_text
                        })

        # 4. Projects (all items preserved)
        projs = data.get("projects") or []
        if isinstance(projs, list) and projs:
            for p in projs:
                if isinstance(p, dict):
                    name = p.get("name") or p.get("title") or ""
                    desc = p.get("description") or ""
                    tech = ", ".join(p.get("technologies", []) or [])
                    feat = " ".join(p.get("features", []) or [])
                    metrics = p.get("results_metrics") or ""
                    link = p.get("link") or p.get("project_url") or ""
                    
                    parts = [f"Project: {name}"]
                    if desc: parts.append(f"Description: {desc}")
                    if tech: parts.append(f"Built with: {tech}")
                    if feat: parts.append(f"Features: {feat}")
                    if metrics: parts.append(f"Results: {metrics}")
                    if link: parts.append(f"Link: {link}")
                    
                    proj_text = " | ".join(parts)
                    if len(proj_text.strip()) > 5:
                        sections.append({
                            "document_type": "projects",
                            "section": "projects",
                            "text": proj_text
                        })

        # 5. Education
        edus = data.get("education") or []
        if isinstance(edus, list) and edus:
            for ed in edus:
                if isinstance(ed, dict):
                    degree = ed.get("degree") or ""
                    field = ed.get("field_of_study") or ""
                    inst = ed.get("institution") or ""
                    year = ed.get("graduation_year") or ed.get("end_date") or ""
                    grade = ed.get("grade") or ed.get("gpa") or ""
                    
                    parts = []
                    if degree or field:
                        parts.append(f"Degree: {degree} in {field}".strip(" in"))
                    if inst:
                        parts.append(f"Institution: {inst}")
                    if year:
                        parts.append(f"Graduation: {year}")
                    if grade:
                        parts.append(f"Grade: {grade}")
                        
                    edu_text = " | ".join(parts)
                    if len(edu_text.strip()) > 5:
                        sections.append({
                            "document_type": "education",
                            "section": "education",
                            "text": edu_text
                        })

        # 6. Certifications
        certs = data.get("certifications") or []
        if isinstance(certs, list) and certs:
            for c in certs:
                if isinstance(c, dict):
                    cname = c.get("name") or ""
                    issuer = c.get("issuer") or ""
                    cyear = c.get("year") or ""
                    cert_text = f"Certification: {cname} issued by {issuer} ({cyear})".strip()
                    if len(cert_text) > 5:
                        sections.append({
                            "document_type": "certifications",
                            "section": "certifications",
                            "text": cert_text
                        })

        # 7. Target Roles & Designation
        target_role = data.get("primary_designation") or data.get("target_role")
        target_roles = data.get("target_roles") or []
        if target_role or target_roles:
            role_parts = []
            if target_role:
                role_parts.append(f"Primary Target Role: {target_role}")
            if target_roles:
                role_parts.append(f"Suitable Target Roles: {', '.join(target_roles)}")
            sections.append({
                "document_type": "target_roles",
                "section": "career_goals",
                "text": " | ".join(role_parts)
            })

        return sections
