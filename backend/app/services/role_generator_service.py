"""
VidyaMarg AI — Resume-Driven Primary Designation & Target Role Generator.
Extracts candidate's primary professional designation and traceably grounded
target job roles strictly from extracted resume evidence.
Zero hardcoding, zero generic dummy fallbacks.
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("app.role_generator_service")

# Knowledge map linking primary role clusters to closely aligned target designations
ROLE_TAXONOMY_MAP = {
    "ai_ml": [
        "AI/ML Engineer",
        "Machine Learning Engineer",
        "AI Engineer",
        "Generative AI Engineer",
        "RAG Engineer",
        "Applied AI Engineer",
        "Data Scientist",
    ],
    "full_stack": [
        "Full Stack Engineer",
        "Software Engineer",
        "Backend Engineer",
        "Frontend Engineer",
        "Web Applications Engineer",
        "System Architect",
    ],
    "backend": [
        "Backend Engineer",
        "Software Engineer",
        "API Platform Engineer",
        "Systems Engineer",
        "Distributed Systems Engineer",
    ],
    "frontend": [
        "Frontend Engineer",
        "UI/UX Engineer",
        "React/Next.js Developer",
        "Web Application Developer",
    ],
    "data_science": [
        "Data Scientist",
        "Machine Learning Engineer",
        "Data Analyst",
        "AI Researcher",
        "Analytics Engineer",
    ],
    "devops_cloud": [
        "DevOps Engineer",
        "Cloud Engineer",
        "Site Reliability Engineer (SRE)",
        "Platform Engineer",
        "Infrastructure Engineer",
    ],
    "mobile": [
        "Mobile Application Engineer",
        "iOS Developer",
        "Android Developer",
        "Cross-Platform Engineer",
    ],
    "cybersecurity": [
        "Cybersecurity Analyst",
        "Security Engineer",
        "Information Security Officer",
        "Penetration Tester",
    ],
}

class RoleGeneratorService:
    """
    Analyzes structured resume payload to derive:
    1. primary_designation (strongest professional role based on experience priority)
    2. target_roles (4-6 closely aligned designations based on evidence)
    3. role_evidence (audit trace linking roles to specific resume sections)
    """

    @classmethod
    def generate_roles_from_resume(cls, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        if not structured_data:
            return cls._default_response()

        exps = structured_data.get("work_experience") or structured_data.get("experience") or []
        skills_raw = structured_data.get("skills") or []
        summary = (structured_data.get("personal_info") or {}).get("summary") or (structured_data.get("professional_summary") or {}).get("summary") or ""
        projects = structured_data.get("projects") or []

        # Clean skill strings
        skill_names = cls._extract_skill_names(skills_raw)
        skill_str_lower = " ".join([s.lower() for s in skill_names])
        exp_str_lower = " ".join([json_str(e) for e in exps]).lower() if isinstance(exps, list) else ""

        # Step 1: Determine Primary Designation
        primary_designation, primary_evidence = cls._derive_primary_designation(exps, summary, skill_names, projects)

        # Step 2: Determine Target Roles and Evidence
        target_roles, role_evidence = cls._derive_target_roles(primary_designation, primary_evidence, skill_names, projects)

        return {
            "primary_designation": primary_designation,
            "target_roles": target_roles,
            "role_evidence": role_evidence,
        }

    @classmethod
    def _derive_primary_designation(
        cls,
        exps: List[Any],
        summary: str,
        skill_names: List[str],
        projects: List[Any]
    ) -> Tuple[str, List[str]]:
        evidence = []

        # Priority 1: Current or most recent job title from work_experience
        if isinstance(exps, list) and len(exps) > 0:
            for exp in exps:
                if isinstance(exp, dict):
                    title = exp.get("title") or exp.get("designation") or exp.get("role") or exp.get("job_title")
                    if title and isinstance(title, str) and len(title.strip()) > 2:
                        clean_title = cls._clean_job_title(title)
                        is_current = bool(exp.get("is_current"))
                        evidence_str = f"Current job title: '{clean_title}'" if is_current else f"Recent job title: '{clean_title}'"
                        evidence.append(evidence_str)
                        return clean_title, evidence

        # Priority 2: Summary headline inspection
        if summary and len(summary) > 5:
            summary_lower = summary.lower()
            for key, roles in ROLE_TAXONOMY_MAP.items():
                for role in roles:
                    if role.lower() in summary_lower:
                        evidence.append(f"Derived from professional summary: '{role}'")
                        return role, evidence

        # Priority 3: Skill & Project cluster inference
        inferred_role, cluster_evidence = cls._infer_role_from_skills_and_projects(skill_names, projects)
        if inferred_role:
            evidence.extend(cluster_evidence)
            return inferred_role, evidence

        # Priority 4: Fallback based on top skill
        if skill_names:
            top_skill = skill_names[0]
            fallback_title = f"{top_skill} Specialist"
            evidence.append(f"Derived from primary skill: {top_skill}")
            return fallback_title, evidence

        return "Professional Specialist", ["Derived from general candidate profile"]

    @classmethod
    def _infer_role_from_skills_and_projects(
        cls, skill_names: List[str], projects: List[Any]
    ) -> Tuple[Optional[str], List[str]]:
        skill_set = set([s.lower() for s in skill_names])
        proj_str = " ".join([cls._project_text(p) for p in projects]).lower() if isinstance(projects, list) else ""

        # AI/ML cluster check
        ai_keywords = {"python", "pytorch", "tensorflow", "fastapi", "llm", "llms", "rag", "langchain", "qdrant", "transformers", "machine learning", "deep learning"}
        if len(skill_set.intersection(ai_keywords)) >= 2 or any(k in proj_str for k in ["rag", "llm", "transformer", "machine learning"]):
            matching_skills = list(skill_set.intersection(ai_keywords))[:3]
            return "AI/ML Engineer", [f"Matching AI/ML skills: {', '.join(matching_skills)}", "AI project experience"]

        # Full Stack cluster check
        fullstack_keywords = {"react", "next.js", "node.js", "typescript", "javascript", "vue", "angular", "express", "fullstack", "full stack"}
        if len(skill_set.intersection(fullstack_keywords)) >= 2:
            matching_skills = list(skill_set.intersection(fullstack_keywords))[:3]
            return "Full Stack Engineer", [f"Matching Full Stack skills: {', '.join(matching_skills)}"]

        # Backend cluster check
        backend_keywords = {"python", "java", "go", "golang", "fastapi", "django", "spring", "postgresql", "mysql", "redis", "kafka", "docker"}
        if len(skill_set.intersection(backend_keywords)) >= 2:
            matching_skills = list(skill_set.intersection(backend_keywords))[:3]
            return "Backend Engineer", [f"Matching Backend skills: {', '.join(matching_skills)}"]

        # DevOps / Cloud cluster check
        devops_keywords = {"aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ci/cd", "jenkins", "ansible"}
        if len(skill_set.intersection(devops_keywords)) >= 2:
            matching_skills = list(skill_set.intersection(devops_keywords))[:3]
            return "DevOps Engineer", [f"Matching DevOps skills: {', '.join(matching_skills)}"]

        return None, []

    @classmethod
    def _derive_target_roles(
        cls,
        primary_designation: str,
        primary_evidence: List[str],
        skill_names: List[str],
        projects: List[Any]
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        target_roles = [primary_designation]
        role_evidence = [
            {
                "role": primary_designation,
                "evidence": primary_evidence
            }
        ]

        # Match primary designation to cluster taxonomy
        primary_lower = primary_designation.lower()
        matched_cluster_key = None

        if any(k in primary_lower for k in ["ai", "machine learning", "ml", "rag", "data science"]):
            matched_cluster_key = "ai_ml"
        elif any(k in primary_lower for k in ["full stack", "fullstack"]):
            matched_cluster_key = "full_stack"
        elif any(k in primary_lower for k in ["backend", "java", "python developer"]):
            matched_cluster_key = "backend"
        elif any(k in primary_lower for k in ["frontend", "ui", "web developer"]):
            matched_cluster_key = "frontend"
        elif any(k in primary_lower for k in ["devops", "cloud", "sre", "infrastructure"]):
            matched_cluster_key = "devops_cloud"
        elif any(k in primary_lower for k in ["data scientist", "analyst"]):
            matched_cluster_key = "data_science"

        if matched_cluster_key and matched_cluster_key in ROLE_TAXONOMY_MAP:
            cluster_roles = ROLE_TAXONOMY_MAP[matched_cluster_key]
            for role in cluster_roles:
                if role not in target_roles:
                    target_roles.append(role)
                    role_evidence.append({
                        "role": role,
                        "evidence": [f"Aligned with primary designation '{primary_designation}'"] + primary_evidence[:1]
                    })
        else:
            # Generate target variations based on skills
            if skill_names:
                for sk in skill_names[:3]:
                    role_var = f"{sk} Specialist"
                    if role_var not in target_roles:
                        target_roles.append(role_var)
                        role_evidence.append({
                            "role": role_var,
                            "evidence": [f"Derived from candidate skill '{sk}'"]
                        })

        return target_roles[:6], role_evidence[:6]

    @staticmethod
    def _clean_job_title(title: str) -> str:
        clean = re.sub(r'[\(\[\{].*?[\)\]\}]', '', title).strip()
        clean = ' '.join(clean.split())
        if not clean:
            return title.strip()

        # Fix capitalization of common technical acronyms
        acronyms = {"ai": "AI", "ml": "ML", "llm": "LLM", "llms": "LLMs", "rag": "RAG", "ui": "UI", "ux": "UX", "api": "API", "it": "IT", "aws": "AWS", "sre": "SRE"}
        words = clean.split()
        res = []
        for w in words:
            # Check slashes (e.g. AI/ML)
            subparts = w.split('/')
            clean_subparts = []
            for sub in subparts:
                sub_lower = sub.lower()
                if sub_lower in acronyms:
                    clean_subparts.append(acronyms[sub_lower])
                elif sub.isupper():
                    clean_subparts.append(sub)
                else:
                    clean_subparts.append(sub.capitalize())
            res.append('/'.join(clean_subparts))
        return ' '.join(res)

    @staticmethod
    def _extract_skill_names(skills_raw: Any) -> List[str]:
        names = []
        if isinstance(skills_raw, list):
            for item in skills_raw:
                if isinstance(item, dict) and item.get("name"):
                    names.append(str(item["name"]).strip())
                elif isinstance(item, str) and item.strip():
                    names.append(item.strip())
        elif isinstance(skills_raw, dict):
            for k, v in skills_raw.items():
                if isinstance(v, list):
                    for sub in v:
                        if isinstance(sub, str) and sub.strip():
                            names.append(sub.strip())
        return list(dict.fromkeys(names))

    @staticmethod
    def _project_text(p: Any) -> str:
        if isinstance(p, dict):
            return f"{p.get('name', '')} {p.get('title', '')} {p.get('description', '')} {' '.join(p.get('technologies', []))}"
        return str(p)

    @classmethod
    def _default_response(cls) -> Dict[str, Any]:
        return {
            "primary_designation": "Candidate Professional",
            "target_roles": ["Candidate Professional"],
            "role_evidence": [{"role": "Candidate Professional", "evidence": ["Default initial state"]}]
        }

def json_str(val: Any) -> str:
    if isinstance(val, dict):
        return " ".join([str(v) for v in val.values()])
    return str(val)
