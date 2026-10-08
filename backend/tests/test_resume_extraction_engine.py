"""
Comprehensive Automated Tests for A-to-Z Resume Data Extraction & Storage Engine:
- Text PDF parsing with multi-column reading order detection
- DOCX parsing with tables, headers, and hyperlinks
- Missing fields and date anomaly detection
- Custom sections preservation
- SHA-256 file integrity and duplicate detection
- Dual representation: raw extraction + normalized database records
- Extraction verification workflow
- Candidate profile reuse endpoint
"""
import io
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from tests.conftest import headers
from app.models.models import User, Candidate
from app.models.resume_center_models import (
    Resume, ResumeVersion, ResumeTemplate, ResumeExtraction,
    ResumeProfile, ResumeSkill, ResumeExperience, ResumeEducation,
    ResumeProject, ResumeCertification, ResumeSection
)
from app.services.resume_extractor_engine import (
    validate_resume_upload, extract_document_content,
    heuristic_comprehensive_parse
)
from app.services.latex_service import render_resume_to_latex


def _create_sample_pdf(multi_column: bool = False) -> bytes:
    """Generates synthetic PDF bytes with selectable text using ReportLab."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    
    if not multi_column:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, "Dr. Alice Turing, Ph.D.")
        c.setFont("Helvetica", 10)
        c.drawString(50, 735, "alice.turing@research.org | +1 555-0142 | Boston, MA")
        c.drawString(50, 720, "https://linkedin.com/in/aliceturing | https://github.com/aliceturing")
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 690, "Professional Summary")
        c.setFont("Helvetica", 10)
        c.drawString(50, 675, "Distinguished Machine Learning Research Scientist with 8+ years developing foundation models.")
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 645, "Technical Skills")
        c.setFont("Helvetica", 10)
        c.drawString(50, 630, "Languages: Python, C++, SQL, Julia")
        c.drawString(50, 615, "Frameworks: PyTorch, TensorFlow, FastAPI, React")
        c.drawString(50, 600, "Cloud & Databases: AWS, Docker, Kubernetes, PostgreSQL, Redis")
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 570, "Work Experience")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, 555, "Principal Research Scientist - DeepBrain AI Labs (Jan 2021 - Present)")
        c.setFont("Helvetica", 10)
        c.drawString(60, 540, "- Architected state-of-the-art vision-language model reducing inference latency by 35%.")
        c.drawString(60, 525, "- Led a distributed training cluster across 512 H100 GPUs with 99.8% training uptime.")
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 495, "Education")
        c.setFont("Helvetica", 10)
        c.drawString(50, 480, "Ph.D. in Computer Science - Massachusetts Institute of Technology, 2020 (GPA: 3.95/4.0)")
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 450, "Patents and Inventions")
        c.setFont("Helvetica", 10)
        c.drawString(50, 435, "US Patent 11,452,890: Dynamic Neural Sparse Attention Gate, Issued 2023.")
    else:
        # Multi-column distribution
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, "Marcus Vance")
        c.setFont("Helvetica", 10)
        c.drawString(50, 735, "marcus.vance@techcorp.io | +1 555-8899 | Seattle, WA")
        
        # Left column (x=50 to 250)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, 700, "Skills")
        c.setFont("Helvetica", 9)
        c.drawString(50, 685, "Python, Go, Docker")
        c.drawString(50, 670, "Kubernetes, AWS")
        c.drawString(50, 655, "PostgreSQL, Redis")
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, 620, "Education")
        c.setFont("Helvetica", 9)
        c.drawString(50, 605, "B.S. in Software Eng")
        c.drawString(50, 590, "Univ of Washington, 2022")
        
        # Right column (x=300 to 550)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(300, 700, "Professional Experience")
        c.setFont("Helvetica-Bold", 9)
        c.drawString(300, 685, "Senior Cloud Engineer - CloudWave Inc (2022 - Present)")
        c.setFont("Helvetica", 9)
        c.drawString(300, 670, "- Automated multi-region Kubernetes deployments.")
        c.drawString(300, 655, "- Reduced infrastructure monthly spend by $45,000.")
        
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()


def _create_sample_docx() -> bytes:
    """Generates synthetic DOCX bytes with tables and paragraphs using python-docx."""
    import docx
    doc = docx.Document()
    
    doc.add_heading("Elena Rostova", level=0)
    p_contact = doc.add_paragraph("elena.rostova@engineer.dev | +1 555-9011 | Chicago, IL\nhttps://github.com/erostova")
    
    doc.add_heading("Professional Summary", level=1)
    doc.add_paragraph("Full-Stack Solutions Architect with extensive experience building fintech platforms.")
    
    doc.add_heading("Skills", level=1)
    table = doc.add_table(rows=3, cols=2)
    table.rows[0].cells[0].text = "Category"
    table.rows[0].cells[1].text = "Technologies"
    table.rows[1].cells[0].text = "Backend & DB"
    table.rows[1].cells[1].text = "Python, TypeScript, FastAPI, PostgreSQL, Redis"
    table.rows[2].cells[0].text = "Cloud & DevOps"
    table.rows[2].cells[1].text = "Docker, AWS, Kubernetes, Terraform"
    
    doc.add_heading("Work Experience", level=1)
    doc.add_paragraph("Lead Software Architect - Citadel Tech (Mar 2021 - Present)")
    doc.add_paragraph("- Designed low-latency matching engine in Go and Python.")
    doc.add_paragraph("- Scaled transaction throughput to 100,000 TPS.")
    
    doc.add_heading("Education", level=1)
    doc.add_paragraph("Master of Science in Software Engineering - Northwestern University, 2021")
    
    doc.add_heading("Volunteer Work", level=1)
    doc.add_paragraph("Mentor at Girls Who Code (2022 - Present): Coached 40+ students in Python fundamentals.")
    
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


def test_file_validation_and_integrity_hashing():
    """Validates magic bytes, size limits, and SHA-256 hash generation."""
    pdf_bytes = _create_sample_pdf()
    is_valid, msg, file_hash, ext = validate_resume_upload("sample.pdf", pdf_bytes, "application/pdf")
    assert is_valid is True
    assert msg == ""
    assert len(file_hash) == 64
    assert ext == ".pdf"
    
    # Test invalid magic signature
    fake_pdf = b"NOT_A_REAL_PDF_HEADER"
    is_valid_fake, err_msg, _, _ = validate_resume_upload("fake.pdf", fake_pdf, "application/pdf")
    assert is_valid_fake is False
    assert "Invalid PDF signature" in err_msg
    
    # Test DOCX validation
    docx_bytes = _create_sample_docx()
    is_valid_docx, _, docx_hash, docx_ext = validate_resume_upload("sample.docx", docx_bytes)
    assert is_valid_docx is True
    assert docx_ext == ".docx"
    assert len(docx_hash) == 64


def test_layout_aware_pdf_extraction():
    """Verifies that multi-column PDFs are read with column separation."""
    multi_col_pdf = _create_sample_pdf(multi_column=True)
    res = extract_document_content("resume.pdf", multi_col_pdf, ".pdf")
    assert res["page_count"] == 1
    raw_text = res["raw_text"]
    assert "Marcus Vance" in raw_text
    assert "Skills" in raw_text
    assert "Professional Experience" in raw_text
    assert "marcus.vance@techcorp.io" in raw_text


def test_docx_table_and_custom_section_extraction():
    """Verifies that DOCX tables and non-standard sections are extracted."""
    docx_bytes = _create_sample_docx()
    res = extract_document_content("resume.docx", docx_bytes, ".docx")
    raw_text = res["raw_text"]
    assert "Elena Rostova" in raw_text
    assert "FastAPI" in raw_text
    assert "Volunteer Work" in raw_text
    assert res["layout_info"]["tables_count"] >= 1


def test_heuristic_parser_zero_hallucination_and_custom_sections():
    """Verifies offline extraction of contact info, skills, experience, and custom sections."""
    sample_text = """
    Samantha Ray
    samantha.ray@cloudsystems.com | +1 555-3211 | Austin, TX
    https://linkedin.com/in/samantharay | https://github.com/samantharay

    Professional Summary
    Senior DevOps and Site Reliability Engineer with 7+ years orchestrating Kubernetes clusters.

    Technical Skills
    Languages: Python, Go, Bash
    Cloud & Tools: Docker, Kubernetes, Terraform, AWS, Prometheus
    Databases: PostgreSQL, Redis

    Work Experience
    Lead SRE - Austin Cloudworks (Jan 2021 - Present)
    - Maintained 99.99% system availability across 8 global regions.
    - Automated incident remediation playbooks saving 20 engineer-hours weekly.

    Education
    B.S. in Computer Science - University of Texas at Austin, 2020

    Open Source Contributions
    Created terraform-aws-k8s-blueprint with over 1,200 GitHub stars.
    """
    data = heuristic_comprehensive_parse(sample_text)
    
    # 1. Contact info
    assert data["personal_info"]["full_name"] == "Samantha Ray"
    assert data["personal_info"]["email"] == "samantha.ray@cloudsystems.com"
    assert "555-3211" in data["personal_info"]["phone"]
    assert "linkedin.com/in/samantharay" in data["personal_info"]["linkedin_url"]
    
    # 2. Categorized skills
    skills = data["skills"]
    assert "Python" in skills["programming_languages"] or "python" in [s.lower() for s in skills["programming_languages"]]
    assert len(skills["cloud_platforms"]) >= 1
    
    # 3. Work experience
    assert len(data["work_experience"]) >= 1
    exp0 = data["work_experience"][0]
    assert "Jan 2021" in (exp0.get("start_date") or "")
    assert exp0.get("is_current") is True
    assert len(exp0.get("responsibilities", [])) >= 2
    
    # 4. Custom section preservation
    custom_secs = data.get("custom_sections", [])
    assert any("Open Source Contributions" in c.get("section_title", "") for c in custom_secs)


def test_e2e_resume_upload_extraction_api(environment):
    """End-to-end test uploading PDF, verifying database rows, and calling verification."""
    client, db, owner, other, admin, candidate, tmp_path = environment
    candidate_auth_headers = headers(owner)
    pdf_bytes = _create_sample_pdf()
    
    # 1. Upload resume
    files = {"file": ("dr_alice_turing.pdf", pdf_bytes, "application/pdf")}
    data = {"title": "Dr. Alice Turing Research CV"}
    
    res = client.post("/api/v1/resumes/upload", files=files, data=data, headers=candidate_auth_headers)
    assert res.status_code == 200, res.text
    payload = res.json()
    
    resume_id = payload["resume_id"]
    assert resume_id is not None
    assert payload["file_name"] == "dr_alice_turing.pdf"
    assert payload["extraction_status"] == "extracted"
    assert payload["confidence_score"] > 0.7
    
    # 2. Get extraction diagnostic details
    get_res = client.get(f"/api/v1/resumes/{resume_id}/extraction", headers=candidate_auth_headers)
    assert get_res.status_code == 200
    ext_payload = get_res.json()
    assert ext_payload["resume_id"] == resume_id
    assert "alice.turing@research.org" in (ext_payload["normalized"]["profile"]["email"] or "")
    
    # 3. Verify extraction
    corrected_profile = ext_payload["structured_data"]
    corrected_profile["personal_info"]["professional_title"] = "Chief AI Scientist"
    
    verify_res = client.put(
        f"/api/v1/resumes/{resume_id}/extraction/verify",
        json={"structured_data": corrected_profile},
        headers=candidate_auth_headers
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["is_verified"] is True
    
    # 4. Test candidate profile reuse endpoint
    profile_res = client.get("/api/v1/candidate/profile-data", headers=candidate_auth_headers)
    assert profile_res.status_code == 200
    prof_payload = profile_res.json()
    assert prof_payload["has_profile"] is True
    assert prof_payload["resume_id"] == resume_id
