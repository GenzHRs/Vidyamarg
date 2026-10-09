"""
Production-grade Resume Center Database Models.
Supports multiple resumes per candidate, full A-to-Z extraction storage,
normalized profile components, version history, template management, and job description tailoring.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Index, Float, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ResumeTemplate(Base):
    """Stores Overleaf-compatible LaTeX resume templates with licensing metadata."""
    __tablename__ = "resume_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    preview_image = Column(String(500), nullable=True)
    latex_template = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="Classic")  # Classic, Modern, Technical, Academic, Minimal
    license_name = Column(String(100), nullable=False, default="MIT")
    license_url = Column(String(500), nullable=True)
    ats_score = Column(Integer, default=95)  # Estimated ATS compatibility score (0-100)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    resumes = relationship("Resume", back_populates="template")


class ResumeVersion(Base):
    """Immutable or semi-immutable snapshots of resume data, LaTeX source, and compiled PDFs."""
    __tablename__ = "resume_document_versions"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    structured_data = Column(JSON, nullable=False)  # JSON structure matching candidate resume fields
    latex_source = Column(Text, nullable=True)
    pdf_file_url = Column(String(500), nullable=True)
    change_summary = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    resume = relationship("Resume", back_populates="versions")

    __table_args__ = (
        Index("idx_resume_version_unique", "resume_id", "version_number", unique=True),
    )


class Resume(Base):
    """Root resume entity owned by a candidate. Tracks current version, file assets, and extraction."""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False, default="Untitled Resume")
    source_type = Column(String(50), nullable=False, default="builder")  # upload, builder, tailored
    template_id = Column(Integer, ForeignKey("resume_templates.id", ondelete="SET NULL"), nullable=True)
    current_version_id = Column(Integer, nullable=True)

    # File Assets & Security Metadata
    original_file_url = Column(String(500), nullable=True)
    latest_pdf_url = Column(String(500), nullable=True)
    latest_tex_url = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_type = Column(String(50), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)  # SHA-256 for duplicate detection
    page_count = Column(Integer, nullable=True)

    # Extraction & Lifecycle Status
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(String(50), nullable=False, default="active")  # active, draft, archived
    extraction_status = Column(String(50), nullable=False, default="pending")  # pending, processing, extracted, reviewed, verified, failed
    extraction_confidence = Column(Float, nullable=True, default=1.0)
    parser_version = Column(String(50), nullable=True, default="v2.0-hybrid")
    is_verified = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    candidate = relationship("Candidate", foreign_keys=[candidate_id])
    template = relationship("ResumeTemplate", back_populates="resumes")
    versions = relationship(
        ResumeVersion,
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by=lambda: ResumeVersion.version_number.desc()
    )

    # Comprehensive Normalized Relationships
    extraction = relationship("ResumeExtraction", uselist=False, back_populates="resume", cascade="all, delete-orphan")
    profile = relationship("ResumeProfile", uselist=False, back_populates="resume", cascade="all, delete-orphan")
    skills = relationship("ResumeSkill", back_populates="resume", cascade="all, delete-orphan")
    experiences = relationship("ResumeExperience", back_populates="resume", cascade="all, delete-orphan")
    educations = relationship("ResumeEducation", back_populates="resume", cascade="all, delete-orphan")
    projects = relationship("ResumeProject", back_populates="resume", cascade="all, delete-orphan")
    certifications = relationship("ResumeCertification", back_populates="resume", cascade="all, delete-orphan")
    sections = relationship("ResumeSection", back_populates="resume", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_resumes_candidate_deleted", "candidate_id", "deleted_at"),
    )


class ResumeExtraction(Base):
    """Preserves raw extracted text, layout metadata, structured JSON, warnings, and parser diagnostics."""
    __tablename__ = "resume_extractions"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    raw_text = Column(Text, nullable=False)
    layout_info = Column(JSON, nullable=True)  # Blocks, columns, tables, hyperlinks, OCR flags
    structured_data = Column(JSON, nullable=False)  # Full parsed dictionary
    confidence_score = Column(Float, default=1.0)
    missing_fields = Column(JSON, default=list)
    warnings = Column(JSON, default=list)
    parser_pipeline = Column(String(100), default="PyMuPDF + OCR + AI Structured")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    resume = relationship("Resume", back_populates="extraction")


class ResumeProfile(Base):
    """Normalized candidate profile information extracted from resume."""
    __tablename__ = "resume_profiles"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Personal Information
    full_name = Column(String(255), nullable=True)
    first_name = Column(String(100), nullable=True)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    professional_title = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    additional_emails = Column(JSON, default=list)
    phone = Column(String(100), nullable=True)
    additional_phones = Column(JSON, default=list)
    location = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)

    # Professional Links
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    custom_links = Column(JSON, default=list)  # [{"label": "Twitter", "url": "..."}]

    # Professional Summary & Objectives
    professional_summary = Column(Text, nullable=True)
    career_objective = Column(Text, nullable=True)
    years_of_experience = Column(Float, nullable=True)
    areas_of_specialization = Column(JSON, default=list)
    career_interests = Column(JSON, default=list)

    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    resume = relationship("Resume", back_populates="profile")


class ResumeSkill(Base):
    """Normalized skill entries with categorization and source tracking."""
    __tablename__ = "resume_skills"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    category = Column(String(100), nullable=False, default="other")  # programming_languages, frameworks, databases, cloud, tools, ai_ml, soft_skills, domain, other
    source_text = Column(String(255), nullable=True)  # Exact wording as written in resume
    proficiency = Column(String(50), nullable=True)  # Beginner, Intermediate, Expert, or null
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    resume = relationship("Resume", back_populates="skills")


class ResumeExperience(Base):
    """Normalized work experience entry."""
    __tablename__ = "resume_experiences"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    employer = Column(String(255), nullable=False)
    designation = Column(String(255), nullable=False)
    employment_location = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)
    employment_type = Column(String(50), nullable=True)  # Full-time, Internship, Freelance, Contract
    responsibilities = Column(JSON, default=list)  # list of bullet strings
    achievements = Column(JSON, default=list)
    technologies = Column(JSON, default=list)
    metrics = Column(JSON, default=list)
    original_text = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    resume = relationship("Resume", back_populates="experiences")


class ResumeEducation(Base):
    """Normalized education entry."""
    __tablename__ = "resume_educations"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    degree = Column(String(255), nullable=False)
    field_of_study = Column(String(255), nullable=True)
    institution = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    graduation_year = Column(String(50), nullable=True)
    grade = Column(String(50), nullable=True)  # GPA, CGPA, or percentage
    relevant_coursework = Column(JSON, default=list)
    achievements = Column(JSON, default=list)
    thesis = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    resume = relationship("Resume", back_populates="educations")


class ResumeProject(Base):
    """Normalized project entry."""
    __tablename__ = "resume_projects"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    problem = Column(Text, nullable=True)
    solution = Column(Text, nullable=True)
    technologies = Column(JSON, default=list)
    responsibilities = Column(JSON, default=list)
    features = Column(JSON, default=list)
    results_metrics = Column(JSON, default=list)
    duration = Column(String(100), nullable=True)
    link = Column(String(500), nullable=True)
    project_type = Column(String(50), nullable=True)  # Individual, Team
    sort_order = Column(Integer, default=0, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    resume = relationship("Resume", back_populates="projects")


class ResumeCertification(Base):
    """Normalized certification and training entry."""
    __tablename__ = "resume_certifications"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    issuing_organization = Column(String(255), nullable=True)
    issue_date = Column(String(50), nullable=True)
    expiration_date = Column(String(50), nullable=True)
    credential_id = Column(String(255), nullable=True)
    credential_url = Column(String(500), nullable=True)
    training_type = Column(String(50), nullable=True)  # Certification, Workshop, Bootcamp, Course
    sort_order = Column(Integer, default=0, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    resume = relationship("Resume", back_populates="certifications")


class ResumeSection(Base):
    """Stores additional, custom, or uncategorized sections extracted from resume."""
    __tablename__ = "resume_sections"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    section_title = Column(String(255), nullable=False)
    original_content = Column(Text, nullable=False)
    structured_content = Column(JSON, nullable=True)
    section_order = Column(Integer, default=0, nullable=False)
    source_page = Column(Integer, nullable=True)
    section_category = Column(String(100), nullable=True)  # awards, publications, languages, volunteer, custom, etc.
    is_verified = Column(Boolean, default=False, nullable=False)

    resume = relationship("Resume", back_populates="sections")


class JobDescription(Base):
    """Stores JD uploaded or pasted by candidates for ATS tailoring analysis."""
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    raw_text = Column(Text, nullable=False)
    extracted_requirements = Column(JSON, nullable=True)  # Required skills, preferred, responsibilities
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    candidate = relationship("Candidate")


class ResumeOptimization(Base):
    """
    Stores derived JD-optimized resume analyses, ATS breakdown scores,
    and truthfulness verification results. Never overwrites the master resume.

    Storage Policy:
    - optimized_data is the authoritative structured JSON snapshot.
    - PDF/DOCX are generated on-demand from optimized_data (never stored by default).
    - submitted_artifact_url is set ONLY after the candidate confirms submission;
      it preserves the exact submitted document in private storage.
    - is_immutable=True prevents any further modifications after submission.
    - jd_hash enables idempotency: the same (candidate, master_resume, jd_text)
      triple will reuse the existing record rather than creating a duplicate.
    - content_hash enables deterministic render cache keying.
    """
    __tablename__ = "resume_optimizations"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    master_resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True, index=True)

    # Job entity link (nullable — optimization may be JD-only without a job record)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)

    # Application entity link (set when candidate prepares to apply)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True)

    template_id = Column(Integer, ForeignKey("resume_templates.id", ondelete="SET NULL"), nullable=True)
    template_version = Column(String(50), nullable=True)  # e.g. "v1.2" for reproducible rendering

    optimization_version = Column(Integer, nullable=False, default=1)

    # Idempotency & integrity hashes
    jd_hash = Column(String(64), nullable=True, index=True)       # SHA-256 of normalized JD text
    content_hash = Column(String(64), nullable=True, index=True)  # SHA-256 of canonical optimized_data JSON

    # ATS and verification scores (0-100)
    ats_score = Column(Integer, nullable=False, default=0)
    keyword_score = Column(Integer, nullable=False, default=0)
    experience_score = Column(Integer, nullable=False, default=0)
    technical_score = Column(Integer, nullable=False, default=0)
    responsibility_score = Column(Integer, nullable=False, default=0)
    alignment_score = Column(Integer, nullable=False, default=0)
    quality_score = Column(Integer, nullable=False, default=0)
    truthfulness_score = Column(Integer, nullable=False, default=100)

    # Generated metadata
    job_title = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    optimized_data = Column(JSON, nullable=False)
    matched_skills = Column(JSON, nullable=True)
    partial_matches = Column(JSON, nullable=True)
    missing_skills = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    ats_report = Column(JSON, nullable=True)

    # Mode & Lineage Tracking
    # rendering_mode: "template" (Mode A - choose template) | "original_layout" (Mode B - edit uploaded resume)
    rendering_mode = Column(String(50), nullable=False, default="template")
    # fidelity_tier: "original_layout_preserved" | "reconstructed_from_original" | "template_fallback"
    fidelity_tier = Column(String(50), nullable=True, default="template_fallback")
    parent_optimization_id = Column(Integer, ForeignKey("resume_optimizations.id", ondelete="SET NULL"), nullable=True)

    # State Machine Fields
    generation_state = Column(String(50), nullable=False, default="SUCCEEDED")  # QUEUED, RUNNING, SUCCEEDED, FAILED
    layout_validation_status = Column(String(50), nullable=False, default="PASSED")  # PENDING, PASSED, WARNING, BLOCKED
    layout_warnings = Column(JSON, default=list)

    # Approval Tracking (explicit candidate review & signoff)
    candidate_approved = Column(Boolean, nullable=False, default=False)
    approved_at = Column(DateTime, nullable=True)
    approval_hash = Column(String(64), nullable=True)  # hash of content reviewed & approved
    approval_notes = Column(Text, nullable=True)

    # Submission tracking (immutable once submitted)
    is_submitted = Column(Boolean, nullable=False, default=False)
    submitted_at = Column(DateTime, nullable=True)
    submitted_artifact_url = Column(String(500), nullable=True)  # private storage path of submitted document
    is_immutable = Column(Boolean, nullable=False, default=False)  # True after submission — prevents overwrite

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    candidate = relationship("Candidate")
    master_resume = relationship("Resume", foreign_keys=[master_resume_id])
    job_description = relationship("JobDescription")
    evidence_items = relationship("ResumeOptimizationEvidence", back_populates="optimization", cascade="all, delete-orphan")

    __table_args__ = (
        # Idempotency: same candidate + master resume + JD text hash = reuse existing record
        UniqueConstraint("candidate_id", "master_resume_id", "jd_hash", name="uq_optimization_candidate_resume_jd"),
        Index("idx_opt_candidate_job", "candidate_id", "job_id"),
        Index("idx_opt_candidate_application", "candidate_id", "application_id"),
        Index("idx_opt_candidate_created", "candidate_id", "created_at"),
        Index("idx_opt_jd_hash", "jd_hash"),
        Index("idx_opt_content_hash", "content_hash"),
    )


class ResumeOptimizationEvidence(Base):
    """
    Stores individual requirement-to-evidence mappings proving that
    every optimization claim originated from the candidate's master profile.
    """
    __tablename__ = "resume_optimization_evidence"

    id = Column(Integer, primary_key=True, index=True)
    optimization_id = Column(Integer, ForeignKey("resume_optimizations.id", ondelete="CASCADE"), nullable=False, index=True)
    jd_requirement = Column(String(255), nullable=False)
    candidate_evidence = Column(Text, nullable=True)
    match_type = Column(String(50), nullable=False)  # STRONG_MATCH, PARTIAL_MATCH, WEAK_MATCH, NO_MATCH
    confidence = Column(Float, nullable=False, default=1.0)
    category = Column(String(50), nullable=True)  # technical, experience, responsibility, education

    optimization = relationship("ResumeOptimization", back_populates="evidence_items")

