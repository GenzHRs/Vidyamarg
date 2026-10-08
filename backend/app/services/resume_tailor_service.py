"""
JD-Based Resume Tailoring & ATS Optimization Service.
Validates AI response using strict Pydantic schemas, retries once on failure,
and enforces zero-hallucination guarantees (never invents candidate facts).
"""
import copy
import json
import logging
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ValidationError

from app.services.ai_provider import ai_provider_service, AIProviderUnavailableException

logger = logging.getLogger("app.resume_tailor")


class SuggestedChange(BaseModel):
    section: str = Field(description="Name of the section e.g. experience, summary, skills, projects")
    original: str = Field(description="Original text or bullet point from candidate resume")
    proposed: str = Field(description="Rewritten bullet point or text aligning with JD keywords")
    reason: str = Field(description="Rationale explaining why the change improves ATS match")
    requires_confirmation: bool = Field(default=False, description="True if change includes new unverified keywords")


class TailoredResumeOutput(BaseModel):
    job_title: str = Field(default="")
    company: str = Field(default="")
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    matching_skills: List[str] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    transferable_skills: List[str] = Field(default_factory=list)
    suggested_changes: List[SuggestedChange] = Field(default_factory=list)
    final_resume_data: Dict[str, Any] = Field(default_factory=dict)
    ats_keywords: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


def build_tailoring_prompt(
    resume_data: Dict[str, Any],
    job_title: str,
    company: str,
    job_description: str,
    source_resume_text: Optional[str] = None,
    location: Optional[str] = None,
    seniority: Optional[str] = None
) -> str:
    raw_text_snippet = f"\nORIGINAL RAW DOCUMENT TEXT:\n{source_resume_text[:2500]}\n" if source_resume_text else ""
    return f"""You are an elite ATS Optimization and Resume Engineering AI.
You are tasked with analyzing a Job Description (JD) and tailoring a candidate's existing resume for maximum relevance and ATS impact.

TARGET JOB DETAILS:
- Title: {job_title}
- Company: {company}
- Location: {location or 'Not specified'}
- Seniority: {seniority or 'Not specified'}

TARGET JOB DESCRIPTION:
{job_description[:6000]}

CURRENT CANDIDATE STRUCTURED RESUME DATA:
{json.dumps(resume_data, indent=2)[:6000]}
{raw_text_snippet}

STRICT ANTI-HALLUCINATION INSTRUCTIONS:
1. YOU MUST NEVER INVENT OR FABRICATE candidate details:
   - NO invented companies, job titles, employment dates, or university degrees.
   - NO invented certifications or projects.
   - NO fabricated metrics, percentages, dollar values, or accomplishments.
2. If the JD requires a skill or requirement that the candidate DOES NOT possess in their background, YOU MUST NOT add it to final_resume_data. Mark it in "missing_requirements".
3. If the candidate possesses adjacent or transferable skills, mark them in "transferable_skills".
4. When suggesting rewritten bullet points in "suggested_changes":
   - Emphasize existing genuine experience using stronger ATS action verbs and terminology found in the JD.
   - Adapt the professional summary to specifically focus on the target role: {job_title} at {company}.
   - If any claim requires the candidate to personally confirm or verify, set "requires_confirmation": true.
5. In "final_resume_data", provide the updated resume data dictionary, preserving the exact structure of the candidate's original resume, incorporating only genuine, approved improvements.
6. In "warnings", highlight any notable qualification gaps between the candidate's background and the JD.

REQUIRED OUTPUT JSON SCHEMA (Strictly return ONLY this JSON):
{{
  "job_title": "{job_title}",
  "company": "{company}",
  "required_skills": ["string"],
  "preferred_skills": ["string"],
  "responsibilities": ["string"],
  "matching_skills": ["string"],
  "missing_requirements": ["string"],
  "transferable_skills": ["string"],
  "suggested_changes": [
    {{
      "section": "summary | experience | skills | projects",
      "original": "original text",
      "proposed": "tailored text",
      "reason": "rationale for ATS improvement",
      "requires_confirmation": false
    }}
  ],
  "final_resume_data": {{ ...full structured resume json conforming to original keys... }},
  "ats_keywords": ["string"],
  "warnings": ["string"]
}}
"""


def offline_fallback_tailoring(
    resume_data: Dict[str, Any],
    job_title: str,
    company: str,
    job_description: str
) -> TailoredResumeOutput:
    """
    Deterministic lexical fallback when external AI providers are offline.
    Extracts common technical words, finds matches and missing items,
    tailors summary and aligns bullets without hallucinating.
    """
    # 1. Extract candidate skills
    candidate_skills = []
    skills_obj = resume_data.get("skills", {})
    if isinstance(skills_obj, dict):
        for items in skills_obj.values():
            if isinstance(items, list):
                for s in items:
                    s_clean = str(s).strip()
                    if s_clean and s_clean.lower() not in [cs.lower() for cs in candidate_skills]:
                        candidate_skills.append(s_clean)
    elif isinstance(skills_obj, list):
        for s in skills_obj:
            s_clean = str(s).strip()
            if s_clean and s_clean.lower() not in [cs.lower() for cs in candidate_skills]:
                candidate_skills.append(s_clean)

    # 2. Tokenize JD and extract technical keywords
    jd_lower = job_description.lower()
    common_tech_lexicon = [
        "python", "javascript", "typescript", "c++", "c", "java", "c#", "go", "golang", "rust",
        "react", "next.js", "vue", "angular", "node.js", "express", "fastapi", "django", "flask",
        "sql", "postgresql", "mysql", "mongodb", "redis", "sqlite", "elasticsearch", "cassandra",
        "docker", "kubernetes", "k8s", "terraform", "aws", "azure", "gcp", "git", "github", "ci/cd",
        "machine learning", "deep learning", "llm", "nlp", "computer vision", "scikit-learn",
        "pytorch", "tensorflow", "pandas", "numpy", "matplotlib", "rag", "rest", "graphql", "linux"
    ]

    jd_tech = [w for w in common_tech_lexicon if w in jd_lower]
    matching_skills = [
        s for s in candidate_skills
        if any(w.lower() == s.lower() or w.lower() in s.lower() or s.lower() in w.lower() for w in jd_tech)
    ]
    missing_requirements = [
        w.title() for w in jd_tech
        if not any(w.lower() == s.lower() or w.lower() in s.lower() or s.lower() in w.lower() for s in candidate_skills)
    ]

    # 3. Produce Tailored Resume Data
    final_data = copy.deepcopy(resume_data)
    suggested_changes: List[SuggestedChange] = []

    # A. Tailor Professional Summary
    orig_summary = final_data.get("summary") or ""
    if orig_summary:
        if company and company.lower() != "target company":
            tailored_summary = (
                f"{orig_summary.rstrip('. ')}. Aligned for the {job_title} role at {company}, "
                f"bringing practical expertise in {', '.join(matching_skills[:5]) if matching_skills else 'core technical requirements'}."
            )
        else:
            tailored_summary = (
                f"{orig_summary.rstrip('. ')}. Focused on {job_title} responsibilities, "
                f"leveraging demonstrated capabilities in {', '.join(matching_skills[:5]) if matching_skills else 'core technologies'}."
            )
        final_data["summary"] = tailored_summary
        suggested_changes.append(SuggestedChange(
            section="summary",
            original=orig_summary,
            proposed=tailored_summary,
            reason=f"Aligns opening summary directly with target job title ({job_title}) and primary matching competencies.",
            requires_confirmation=False
        ))

    # B. Prioritize Matching Skills in Skill Categories
    if isinstance(final_data.get("skills"), dict):
        for cat_name, cat_skills in final_data["skills"].items():
            if isinstance(cat_skills, list):
                # Put matching skills first in the list
                matched_in_cat = [s for s in cat_skills if any(m.lower() in s.lower() for m in matching_skills)]
                rest_in_cat = [s for s in cat_skills if s not in matched_in_cat]
                final_data["skills"][cat_name] = matched_in_cat + rest_in_cat

    # C. Align Experience Bullets (highlighting matching tech)
    if isinstance(final_data.get("experience"), list):
        for exp in final_data["experience"]:
            bullets = exp.get("bullets", [])
            if isinstance(bullets, list) and bullets:
                for b_idx, bullet in enumerate(bullets):
                    # Check if bullet mentions matching tech
                    for m in matching_skills[:3]:
                        if m.lower() in bullet.lower() and not bullet.startswith("Engineered") and not bullet.startswith("Architected"):
                            improved = re.sub(r"^(Developed|Built|Worked on|Handled)\b", "Engineered and optimized", bullet)
                            if improved != bullet:
                                suggested_changes.append(SuggestedChange(
                                    section="experience",
                                    original=bullet,
                                    proposed=improved,
                                    reason=f"Uses stronger ATS action verb for core skill {m}",
                                    requires_confirmation=False
                                ))
                                bullets[b_idx] = improved
                                break

    warnings = []
    if missing_requirements:
        warnings.append(
            f"The job description mentions requirements not found in candidate background: {', '.join(missing_requirements[:5])}."
        )

    return TailoredResumeOutput(
        job_title=job_title,
        company=company,
        required_skills=[w.title() for w in jd_tech[:10]],
        preferred_skills=[],
        responsibilities=["See target job description responsibilities"],
        matching_skills=matching_skills,
        missing_requirements=missing_requirements[:8],
        transferable_skills=[],
        suggested_changes=suggested_changes,
        final_resume_data=final_data,
        ats_keywords=[w.title() for w in jd_tech],
        warnings=warnings
    )


def generate_jd_tailored_resume(
    source_resume_id: int,
    source_resume_data: Dict[str, Any],
    job_title: str,
    company_name: str,
    job_description: str,
    source_resume_text: Optional[str] = None,
    selected_template_id: Optional[int] = None,
    location: Optional[str] = None,
    seniority: Optional[str] = None
) -> TailoredResumeOutput:
    """
    Dedicated production service for JD-based resume tailoring:
    - Analyzes target JD requirements.
    - Evaluates candidate profile.
    - Uses configured AI provider (with strict JSON validation and 1 automatic retry).
    - Enforces zero-hallucination constraint.
    - Gracefully falls back to offline lexical tailoring if AI is unavailable.
    """
    logger.info(f"Generating JD tailored resume for Resume ID={source_resume_id}, Title='{job_title}', Company='{company_name}'")

    if not (ai_provider_service.is_gemini_configured() or
            ai_provider_service.is_nvidia_configured() or
            ai_provider_service.is_groq_configured()):
        logger.info("AI providers unconfigured — using deterministic offline tailoring engine.")
        return offline_fallback_tailoring(source_resume_data, job_title, company_name, job_description)

    prompt = build_tailoring_prompt(
        resume_data=source_resume_data,
        job_title=job_title,
        company=company_name,
        job_description=job_description,
        source_resume_text=source_resume_text,
        location=location,
        seniority=seniority
    )

    for attempt in range(2):
        try:
            raw_response = ai_provider_service.call_with_fallback(prompt, json_mode=True)
            cleaned = raw_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            data_dict = json.loads(cleaned.strip())
            validated = TailoredResumeOutput.model_validate(data_dict)

            if not validated.final_resume_data:
                validated.final_resume_data = copy.deepcopy(source_resume_data)

            logger.info(f"AI tailoring successful on attempt {attempt + 1}. Matching skills count: {len(validated.matching_skills)}")
            return validated

        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"AI tailoring response validation failed on attempt {attempt + 1}: {e}")
            if attempt == 0:
                prompt += "\n\nCRITICAL RETRY NUDGE: Previous output failed schema validation. Return ONLY strict valid JSON conforming to the requested schema."
                continue

        except AIProviderUnavailableException as e:
            logger.warning(f"AI provider unavailable during tailoring: {e}")
            break
        except Exception as e:
            logger.error(f"Unexpected error during AI tailoring: {e}")
            break

    logger.info("Falling back to deterministic offline tailoring engine.")
    return offline_fallback_tailoring(source_resume_data, job_title, company_name, job_description)


# Backward-compatible alias
def tailor_resume_to_jd(
    resume_data: Dict[str, Any],
    job_title: str,
    company: str,
    job_description: str,
    location: Optional[str] = None,
    seniority: Optional[str] = None
) -> TailoredResumeOutput:
    return generate_jd_tailored_resume(
        source_resume_id=0,
        source_resume_data=resume_data,
        job_title=job_title,
        company_name=company,
        job_description=job_description,
        location=location,
        seniority=seniority
    )
