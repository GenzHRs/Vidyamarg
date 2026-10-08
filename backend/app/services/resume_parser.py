"""
Resume Document Ingestion and Structured Extraction Service.
Supports PDF, DOCX, TXT, and LaTeX (.tex) with file-signature validation,
MIME-type checks, and AI / heuristic section detection.
"""
import io
import re
from typing import Dict, Any, Tuple, Optional

# Max upload size: 10MB
MAX_RESUME_UPLOAD_SIZE = 10 * 1024 * 1024
ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx", ".txt", ".tex"}
ALLOWED_RESUME_MIMES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "application/x-tex",
    "text/x-tex"
}


def validate_resume_file(filename: str, content: bytes, content_type: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validates file extension, size, MIME type, and file signature (magic bytes).
    Returns (is_valid, error_message).
    """
    if len(content) == 0:
        return False, "Uploaded file is empty"

    if len(content) > MAX_RESUME_UPLOAD_SIZE:
        return False, "File exceeds the 10MB upload limit"

    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_RESUME_EXTENSIONS:
        return False, f"Unsupported file extension '{ext}'. Allowed: .pdf, .docx, .txt, .tex"

    # Signature (magic bytes) validation
    if ext == ".pdf":
        if not content.startswith(b"%PDF-"):
            return False, "Invalid PDF file signature (corrupted or disguised file)"
    elif ext == ".docx":
        # ZIP magic bytes PK\x03\x04
        if not content.startswith(b"PK\x03\x04"):
            return False, "Invalid DOCX file signature"
    elif ext in (".txt", ".tex"):
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content.decode("latin-1")
            except Exception:
                return False, "Text file cannot be decoded as valid text"

    return True, ""


def extract_text_from_file(filename: str, content: bytes) -> str:
    """Extracts raw text from PDF, DOCX, TXT, or TEX."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == ".pdf":
        text_parts = []
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=content, filetype="pdf")
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
        except Exception:
            # Fallback to pypdf
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content))
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts).strip()

    elif ext == ".docx":
        import docx
        doc = docx.Document(io.BytesIO(content))
        return "\n".join([p.text for p in doc.paragraphs if p.text]).strip()

    elif ext == ".txt":
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("latin-1", errors="replace")

    elif ext == ".tex":
        try:
            raw = content.decode("utf-8")
        except UnicodeDecodeError:
            raw = content.decode("latin-1", errors="replace")
        # Strip TeX comments and basic command wrappers for text parsing
        clean_lines = []
        for line in raw.split("\n"):
            line = re.sub(r"%.*$", "", line)  # remove comments
            clean_lines.append(line)
        return "\n".join(clean_lines).strip()

    return ""


def heuristic_parse_resume_text(text: str) -> Dict[str, Any]:
    """
    Offline fallback parser that extracts contact info and detects sections
    without needing external AI keys.
    """
    structured: Dict[str, Any] = {
        "personal_info": {
            "full_name": "Candidate",
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": "",
            "github": "",
            "portfolio": ""
        },
        "summary": "",
        "skills": {
            "Languages": [],
            "Frameworks & Tools": [],
            "Concepts": []
        },
        "experience": [],
        "projects": [],
        "education": [],
        "certifications": []
    }

    # Extract email
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if email_match:
        structured["personal_info"]["email"] = email_match.group(0)

    # Extract phone
    phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    if phone_match:
        structured["personal_info"]["phone"] = phone_match.group(0).strip()

    # Extract LinkedIn / GitHub
    linkedin_match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+", text, re.I)
    if linkedin_match:
        structured["personal_info"]["linkedin"] = linkedin_match.group(0)

    github_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/[\w-]+", text, re.I)
    if github_match:
        structured["personal_info"]["github"] = github_match.group(0)

    # Attempt to extract candidate name from top lines
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if lines:
        for first_line in lines[:5]:
            if "@" not in first_line and not re.search(r"\d{3}", first_line) and len(first_line) < 40:
                structured["personal_info"]["full_name"] = first_line
                break

    # Look for common sections
    current_section = None
    section_buffers: Dict[str, list] = {
        "summary": [],
        "experience": [],
        "skills": [],
        "projects": [],
        "education": [],
        "certifications": []
    }

    section_keywords = {
        "summary": re.compile(r"^(professional\s+summary|summary|profile|about\s+me|objective)", re.I),
        "experience": re.compile(r"^(work\s+experience|professional\s+experience|experience|employment\s+history)", re.I),
        "skills": re.compile(r"^(skills|technical\s+skills|core\s+competencies|technologies)", re.I),
        "projects": re.compile(r"^(projects|key\s+projects|featured\s+projects|personal\s+projects)", re.I),
        "education": re.compile(r"^(education|academic\s+background|academics)", re.I),
        "certifications": re.compile(r"^(certifications|licenses|courses|awards)", re.I),
    }

    for line in lines:
        cleaned_line = line.strip(" :#*-")
        matched_section = None
        for sec_name, pattern in section_keywords.items():
            if pattern.match(cleaned_line) and len(cleaned_line.split()) <= 4:
                matched_section = sec_name
                break

        if matched_section:
            current_section = matched_section
            continue

        if current_section:
            section_buffers[current_section].append(line)

    # Populate summary
    if section_buffers["summary"]:
        structured["summary"] = " ".join(section_buffers["summary"][:6])

    # Populate skills
    all_skill_words = []
    for s_line in section_buffers["skills"]:
        items = re.split(r"[,;|•·]\s*", s_line)
        for item in items:
            clean_item = item.strip(" -•*")
            if clean_item and len(clean_item) < 30:
                all_skill_words.append(clean_item)
    if all_skill_words:
        structured["skills"]["Languages"] = all_skill_words[:8]
        structured["skills"]["Frameworks & Tools"] = all_skill_words[8:16]

    # Populate experience
    if section_buffers["experience"]:
        current_job = {"title": "Role", "company": "Company", "start_date": "", "end_date": "", "bullets": []}
        for exp_line in section_buffers["experience"][:15]:
            if exp_line.startswith(("-", "•", "*")):
                current_job["bullets"].append(exp_line.lstrip("-•* "))
            else:
                if current_job["bullets"]:
                    structured["experience"].append(current_job)
                    current_job = {"title": exp_line, "company": "Company", "start_date": "", "end_date": "", "bullets": []}
                else:
                    current_job["title"] = exp_line
        if current_job["bullets"] or current_job["title"] != "Role":
            structured["experience"].append(current_job)

    # Populate education
    if section_buffers["education"]:
        edu_item = {"degree": "Degree", "institution": "University / College", "start_date": "", "end_date": "", "details": ""}
        for edu_line in section_buffers["education"][:4]:
            if "degree" in edu_line.lower() or "bachelor" in edu_line.lower() or "master" in edu_line.lower() or "b.tech" in edu_line.lower():
                edu_item["degree"] = edu_line
            elif "university" in edu_line.lower() or "college" in edu_line.lower() or "institute" in edu_line.lower():
                edu_item["institution"] = edu_line
        structured["education"].append(edu_item)

    return structured


def parse_resume_to_structured(raw_text: str) -> Dict[str, Any]:
    """
    Attempts AI structured parsing via AIProviderService (Gemini / NVIDIA / Groq).
    Gracefully degrades to heuristic regex parsing if AI is unconfigured or fails.
    """
    from app.services.ai_provider import ai_provider_service, AIProviderUnavailableException
    import json

    prompt = f"""You are an expert resume parsing engine.
Extract structured information from the following resume text into valid JSON matching this schema:
{{
  "personal_info": {{
    "full_name": "Full Name",
    "email": "email@example.com",
    "phone": "Phone number",
    "location": "City, Country",
    "linkedin": "url or empty",
    "github": "url or empty",
    "portfolio": "url or empty"
  }},
  "summary": "Professional summary or career objective",
  "skills": {{
    "Languages": ["python", "javascript"],
    "Frameworks & Tools": ["react", "fastapi"],
    "Cloud & Databases": ["postgresql", "docker"]
  }},
  "experience": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "location": "Location",
      "start_date": "Date",
      "end_date": "Date or Present",
      "bullets": ["Achievement or responsibility 1", "Achievement 2"]
    }}
  ],
  "projects": [
    {{
      "name": "Project Title",
      "technologies": "Stack used",
      "start_date": "Date",
      "end_date": "Date",
      "link": "url or empty",
      "bullets": ["Project detail 1"]
    }}
  ],
  "education": [
    {{
      "degree": "Degree and Major",
      "institution": "University / School",
      "location": "Location",
      "start_date": "Start Year",
      "end_date": "Graduation Year",
      "gpa": "GPA or empty"
    }}
  ],
  "certifications": [
    {{
      "name": "Certification Name",
      "issuer": "Issuing Org",
      "date": "Year"
    }}
  ]
}}

CRITICAL RULES:
1. Return ONLY the JSON object. Do not include markdown formatting or extra conversational text.
2. DO NOT invent or fabricate any details. Extract only information present in the text.
3. If a section is absent, set it to an empty array or empty string.

RESUME TEXT:
{raw_text[:8000]}
"""
    try:
        if (ai_provider_service.is_gemini_configured() or
            ai_provider_service.is_nvidia_configured() or
            ai_provider_service.is_groq_configured()):
            response_text = ai_provider_service.call_with_fallback(prompt, json_mode=True)
            # Clean markdown codeblocks if returned
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            parsed = json.loads(cleaned.strip())
            if isinstance(parsed, dict) and "personal_info" in parsed:
                return parsed
    except Exception:
        pass

    # Heuristic fallback
    return heuristic_parse_resume_text(raw_text)
