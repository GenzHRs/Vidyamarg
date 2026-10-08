"""
VidyaMarg AI — Resume Diff Engine.
Compares normalized text, skills, work experience, projects, and designations
between candidate's previous active resume and new resume.
Classifies changes into: NO_CHANGE, MINOR_CHANGE, or MEANINGFUL_CHANGE.
"""
import re
import logging
from typing import Dict, Any, List, Set, Tuple, Optional

logger = logging.getLogger("app.resume_diff_engine")

class ResumeDiffEngine:
    """
    Analyzes structural and semantic differences between two resume JSON payloads.
    Guarantees text normalization before comparison.
    """

    @classmethod
    def compare_resumes(cls, old_data: Optional[Dict[str, Any]], new_data: Dict[str, Any]) -> Dict[str, Any]:
        if not old_data or not isinstance(old_data, dict) or not any(old_data.values()):
            return {
                "change_level": "MEANINGFUL_CHANGE",
                "added_skills": cls._extract_skills(new_data),
                "removed_skills": [],
                "added_projects": cls._extract_project_names(new_data),
                "removed_projects": [],
                "added_experience": cls._extract_experience_titles(new_data),
                "removed_experience": [],
                "designation_changed": True,
                "details": ["Initial active resume upload"]
            }

        details = []

        # 1. Normalize and compare skills
        old_skills = cls._extract_skills(old_data)
        new_skills = cls._extract_skills(new_data)
        old_skill_set = set([cls.normalize_text(s) for s in old_skills if s])
        new_skill_set = set([cls.normalize_text(s) for s in new_skills if s])

        added_skills = [s for s in new_skills if cls.normalize_text(s) not in old_skill_set]
        removed_skills = [s for s in old_skills if cls.normalize_text(s) not in new_skill_set]

        # 2. Compare work experience and job titles
        old_exp_titles = cls._extract_experience_titles(old_data)
        new_exp_titles = cls._extract_experience_titles(new_data)
        old_exp_set = set([cls.normalize_text(t) for t in old_exp_titles])
        new_exp_set = set([cls.normalize_text(t) for t in new_exp_titles])

        added_experience = [t for t in new_exp_titles if cls.normalize_text(t) not in old_exp_set]
        removed_experience = [t for t in old_exp_titles if cls.normalize_text(t) not in new_exp_set]

        old_current_title = cls._extract_current_title(old_data)
        new_current_title = cls._extract_current_title(new_data)
        designation_changed = cls.normalize_text(old_current_title) != cls.normalize_text(new_current_title)

        # 3. Compare projects
        old_projects = cls._extract_project_names(old_data)
        new_projects = cls._extract_project_names(new_data)
        old_proj_set = set([cls.normalize_text(p) for p in old_projects])
        new_proj_set = set([cls.normalize_text(p) for p in new_projects])

        added_projects = [p for p in new_projects if cls.normalize_text(p) not in old_proj_set]
        removed_projects = [p for p in old_projects if cls.normalize_text(p) not in new_proj_set]

        # Determine Change Level
        has_meaningful_change = False

        if designation_changed and (old_current_title or new_current_title):
            has_meaningful_change = True
            details.append(f"Designation changed from '{old_current_title}' to '{new_current_title}'")

        if len(added_skills) >= 2 or len(removed_skills) >= 2:
            has_meaningful_change = True
            details.append(f"Skills updated: +{len(added_skills)} added, -{len(removed_skills)} removed")
        elif len(added_skills) == 1 or len(removed_skills) == 1:
            details.append(f"Single skill tweak: +{added_skills}, -{removed_skills}")

        if len(added_experience) > 0 or len(removed_experience) > 0:
            has_meaningful_change = True
            details.append(f"Work experience history changed: +{len(added_experience)} entries")

        if len(added_projects) > 0 or len(removed_projects) > 0:
            has_meaningful_change = True
            details.append(f"Projects updated: +{len(added_projects)} added")

        # Classify change level
        if has_meaningful_change:
            change_level = "MEANINGFUL_CHANGE"
        elif added_skills or removed_skills or details:
            change_level = "MINOR_CHANGE"
        else:
            change_level = "NO_CHANGE"

        if change_level == "NO_CHANGE":
            details.append("No structural or skill changes detected between active and new resume")

        return {
            "change_level": change_level,
            "added_skills": added_skills,
            "removed_skills": removed_skills,
            "added_projects": added_projects,
            "removed_projects": removed_projects,
            "added_experience": added_experience,
            "removed_experience": removed_experience,
            "designation_changed": designation_changed,
            "details": details
        }

    @staticmethod
    def normalize_text(text: Optional[str]) -> str:
        if not text:
            return ""
        clean = re.sub(r"[^\w\s]", "", str(text)).strip().lower()
        return " ".join(clean.split())

    @staticmethod
    def _extract_skills(data: Dict[str, Any]) -> List[str]:
        skills_raw = data.get("skills") or []
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
    def _extract_experience_titles(data: Dict[str, Any]) -> List[str]:
        exps = data.get("work_experience") or data.get("experience") or []
        titles = []
        if isinstance(exps, list):
            for e in exps:
                if isinstance(e, dict):
                    t = e.get("title") or e.get("designation") or e.get("role") or e.get("job_title")
                    if t and isinstance(t, str):
                        titles.append(t.strip())
        return titles

    @staticmethod
    def _extract_current_title(data: Dict[str, Any]) -> str:
        exps = data.get("work_experience") or data.get("experience") or []
        if isinstance(exps, list) and len(exps) > 0:
            for e in exps:
                if isinstance(e, dict):
                    if e.get("is_current"):
                        t = e.get("title") or e.get("designation") or e.get("role") or e.get("job_title")
                        if t and isinstance(t, str):
                            return t.strip()
            # Fallback to first title
            first = exps[0]
            if isinstance(first, dict):
                t = first.get("title") or first.get("designation") or first.get("role")
                if t and isinstance(t, str):
                    return t.strip()
        return ""

    @staticmethod
    def _extract_project_names(data: Dict[str, Any]) -> List[str]:
        projs = data.get("projects") or []
        names = []
        if isinstance(projs, list):
            for p in projs:
                if isinstance(p, dict):
                    name = p.get("name") or p.get("title")
                    if name and isinstance(name, str):
                        names.append(name.strip())
        return names
