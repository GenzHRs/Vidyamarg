"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, ArrowRight, Save, Terminal, Plus, Trash2, 
  Layers, User, Briefcase, GraduationCap, Code, Folder, 
  Award, FileText, CheckCircle2, ShieldCheck, Sparkles 
} from "lucide-react";
import { 
  resumeCenterApi, 
  StructuredResumeData, 
  WorkExperience, 
  Education, 
  Project, 
  ResumeTemplateItem 
} from "@/services/resumeCenterApi";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";

function ResumeBuilderContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const templateIdParam = searchParams.get("templateId");

  const [templates, setTemplates] = useState<ResumeTemplateItem[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | undefined>(
    templateIdParam ? Number(templateIdParam) : undefined
  );
  const [resumeTitle, setResumeTitle] = useState("Software Engineer Resume");
  const [activeTab, setActiveTab] = useState<"personal" | "summary" | "experience" | "education" | "skills" | "projects" | "certifications">("personal");

  const [saving, setSaving] = useState(false);
  const [importing, setImporting] = useState(false);
  const [savedProfileAvailable, setSavedProfileAvailable] = useState(false);
  const [infoMessage, setInfoMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    resumeCenterApi.getCandidateProfileData()
      .then((res) => {
        if (res && res.has_profile) {
          setSavedProfileAvailable(true);
          handleImportSavedProfile();
        }
      })
      .catch(() => {});
  }, []);

  const handleImportSavedProfile = async () => {
    try {
      setImporting(true);
      setErrorMessage("");
      const res = await resumeCenterApi.getCandidateProfileData();
      if (!res.has_profile || !res.template_compatible_data) {
        setErrorMessage("No saved profile data found. Please upload a resume first.");
        return;
      }
      const data = res.template_compatible_data;
      if (res.resume_title) setResumeTitle(res.resume_title);
      if (data.personal_info) {
        setPersonalInfo({
          full_name: data.personal_info.full_name || "",
          email: data.personal_info.email || "",
          phone: data.personal_info.phone || "",
          location: data.personal_info.location || "",
          linkedin: data.personal_info.linkedin || "",
          github: data.personal_info.github || "",
          portfolio: data.personal_info.portfolio || "",
        });
      }
      if (data.summary) setSummary(data.summary);
      if (Array.isArray(data.experience) && data.experience.length > 0) setExperience(data.experience);
      if (Array.isArray(data.education) && data.education.length > 0) setEducation(data.education);
      if (Array.isArray(data.projects) && data.projects.length > 0) setProjects(data.projects);
      if (data.skills) {
        if (typeof data.skills === "object" && !Array.isArray(data.skills)) {
          setSkillsText(
            Object.entries(data.skills)
              .map(([cat, items]) => `${cat}: ${Array.isArray(items) ? items.join(", ") : items}`)
              .join("\n")
          );
        } else if (Array.isArray(data.skills)) {
          setSkillsText(data.skills.join(", "));
        }
      }
      if (Array.isArray(data.certifications) && data.certifications.length > 0) {
        setCertificationsText(data.certifications.map((c) => (typeof c === "string" ? c : (c as any).name || "")).join("\n"));
      }
      setInfoMessage(`Imported saved profile from "${res.resume_title || 'Previous Resume'}"!`);
      setTimeout(() => setInfoMessage(""), 4000);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to import saved profile.");
    } finally {
      setImporting(false);
    }
  };

  // Structured Form States
  const [personalInfo, setPersonalInfo] = useState({
    full_name: "",
    email: "",
    phone: "",
    location: "",
    linkedin: "",
    github: "",
    portfolio: "",
  });

  const [summary, setSummary] = useState("");

  const [experience, setExperience] = useState<WorkExperience[]>([]);
  const [education, setEducation] = useState<Education[]>([]);
  const [skillsText, setSkillsText] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [certificationsText, setCertificationsText] = useState("");

  useEffect(() => {
    resumeCenterApi.getTemplates()
      .then((data) => {
        setTemplates(data);
        if (templateIdParam) {
          const match = data.find((t) => t.id === Number(templateIdParam));
          if (match) {
            setSelectedTemplateId(match.id);
            return;
          }
        }
        if (data.length > 0 && !selectedTemplateId) {
          setSelectedTemplateId(data[0].id);
        }
      })
      .catch((err) => console.error("Error loading templates:", err));
  }, [templateIdParam]);

  // Helpers for Experience
  const addExperience = () => {
    setExperience([
      ...experience,
      {
        title: "",
        company: "",
        location: "",
        start_date: "",
        end_date: "",
        bullets: [""],
      },
    ]);
  };

  const updateExperience = (index: number, field: keyof WorkExperience, val: any) => {
    const updated = [...experience];
    updated[index] = { ...updated[index], [field]: val };
    setExperience(updated);
  };

  const removeExperience = (index: number) => {
    setExperience(experience.filter((_, i) => i !== index));
  };

  const addExperienceBullet = (expIdx: number) => {
    const updated = [...experience];
    const bullets = updated[expIdx].bullets || [];
    updated[expIdx].bullets = [...bullets, ""];
    setExperience(updated);
  };

  const updateExperienceBullet = (expIdx: number, bIdx: number, val: string) => {
    const updated = [...experience];
    const bullets = [...(updated[expIdx].bullets || [])];
    bullets[bIdx] = val;
    updated[expIdx].bullets = bullets;
    setExperience(updated);
  };

  const removeExperienceBullet = (expIdx: number, bIdx: number) => {
    const updated = [...experience];
    const bullets = (updated[expIdx].bullets || []).filter((_, i) => i !== bIdx);
    updated[expIdx].bullets = bullets;
    setExperience(updated);
  };

  // Helpers for Projects
  const addProject = () => {
    setProjects([
      ...projects,
      { name: "", tech_stack: "", bullets: [""] },
    ]);
  };

  const updateProject = (index: number, field: keyof Project, val: any) => {
    const updated = [...projects];
    updated[index] = { ...updated[index], [field]: val };
    setProjects(updated);
  };

  const removeProject = (index: number) => {
    setProjects(projects.filter((_, i) => i !== index));
  };

  const addProjectBullet = (pIdx: number) => {
    const updated = [...projects];
    const bullets = updated[pIdx].bullets || [];
    updated[pIdx].bullets = [...bullets, ""];
    setProjects(updated);
  };

  const updateProjectBullet = (pIdx: number, bIdx: number, val: string) => {
    const updated = [...projects];
    const bullets = [...(updated[pIdx].bullets || [])];
    bullets[bIdx] = val;
    updated[pIdx].bullets = bullets;
    setProjects(updated);
  };

  const removeProjectBullet = (pIdx: number, bIdx: number) => {
    const updated = [...projects];
    const bullets = (updated[pIdx].bullets || []).filter((_, i) => i !== bIdx);
    updated[pIdx].bullets = bullets;
    setProjects(updated);
  };

  // Build Payload
  const assembleData = (): StructuredResumeData => {
    // Parse skills
    const skillsLines = skillsText.split("\n").filter((l) => l.trim().length > 0);
    const parsedSkills: Record<string, string[]> = {};
    const uncatSkills: string[] = [];

    skillsLines.forEach((line) => {
      if (line.includes(":")) {
        const [cat, items] = line.split(":");
        parsedSkills[cat.trim()] = items
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);
      } else {
        line.split(",").forEach((s) => uncatSkills.push(s.trim()));
      }
    });

    const certs = certificationsText
      .split("\n")
      .map((c) => c.trim())
      .filter(Boolean);

    return {
      personal_info: personalInfo,
      summary,
      experience,
      education,
      skills: Object.keys(parsedSkills).length > 0 ? parsedSkills : uncatSkills,
      projects,
      certifications: certs,
    };
  };

  const handleSave = async (autoCompile = false) => {
    try {
      setSaving(true);
      setErrorMessage("");

      const structured_data = assembleData();
      const newResume = await resumeCenterApi.createResume({
        title: resumeTitle || "Untitled Resume",
        template_id: selectedTemplateId,
        structured_data,
      });

      if (autoCompile) {
        await resumeCenterApi.compileResume(newResume.id).catch(() => {});
      }

      router.push(`/candidate/resumes/edit/${newResume.id}`);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to create resume");
      setSaving(false);
    }
  };

  const tabs = [
    { id: "personal", name: "Personal", icon: User },
    { id: "summary", name: "Summary", icon: FileText },
    { id: "experience", name: "Experience", icon: Briefcase },
    { id: "education", name: "Education", icon: GraduationCap },
    { id: "skills", name: "Skills", icon: Code },
    { id: "projects", name: "Projects", icon: Folder },
    { id: "certifications", name: "Certifications", icon: Award },
  ] as const;

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-6 font-sans">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Link 
            href="/candidate/resumes" 
            className="inline-flex items-center gap-2 text-xs font-semibold text-app-text-muted hover:text-app-text transition-colors mb-2"
          >
            <ArrowLeft size={14} /> Back to Resume Center
          </Link>
          <h1 className="text-2xl md:text-3xl font-extrabold text-app-text tracking-tight flex items-center gap-2.5">
            <Sparkles className="text-blue-600 dark:text-blue-400" size={28} />
            Create New LaTeX Resume
          </h1>
          <p className="text-xs md:text-sm text-app-text-muted mt-1 leading-relaxed">
            Fill in your details across sections. You can edit, compile to PDF, and inspect LaTeX source immediately.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {savedProfileAvailable && (
            <Button
              variant="outline"
              disabled={importing || saving}
              onClick={handleImportSavedProfile}
              className="text-xs bg-indigo-50/50 hover:bg-indigo-50 border-indigo-200 text-indigo-700 dark:bg-indigo-950/30 dark:border-indigo-800 dark:text-indigo-300 font-semibold"
              title="Pre-fill form using your uploaded resume data"
            >
              <FileText size={13} className="mr-1.5" />
              {importing ? "Importing..." : "Import Saved Profile"}
            </Button>
          )}
          <Button
            variant="outline"
            disabled={saving}
            onClick={() => handleSave(false)}
            className="text-xs"
          >
            <Save size={14} className="mr-1.5" />
            Save Draft
          </Button>
          <Button
            disabled={saving}
            onClick={() => handleSave(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-5 shadow-sm"
          >
            <Terminal size={14} className="mr-1.5" />
            Save & Compile PDF
          </Button>
        </div>
      </div>

      {infoMessage && <Alert variant="success">{infoMessage}</Alert>}
      {errorMessage && <Alert variant="error">{errorMessage}</Alert>}

      {/* Meta Bar: Title & Template Selection */}
      <Card className="p-4 bg-app-card border-app-border space-y-3">
        <div className="flex flex-col md:flex-row items-center gap-4">
          <div className="flex-1 w-full">
            <label className="block text-[11px] font-bold uppercase tracking-wider text-app-text-muted mb-1">
              Resume Title
            </label>
            <input
              type="text"
              value={resumeTitle}
              onChange={(e) => setResumeTitle(e.target.value)}
              className="w-full text-xs px-3.5 py-2 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500 font-semibold"
              placeholder="e.g. Senior Backend Engineer - 2026"
            />
          </div>

          <div className="w-full md:w-80">
            <div className="flex items-center justify-between mb-1">
              <label className="block text-[11px] font-bold uppercase tracking-wider text-app-text-muted">
                LaTeX Template
              </label>
              <Link 
                href="/candidate/resumes/templates" 
                className="text-[10px] text-blue-600 hover:text-blue-500 font-medium inline-flex items-center gap-1"
              >
                Browse Gallery <ArrowRight size={10} />
              </Link>
            </div>
            <select
              value={selectedTemplateId || ""}
              onChange={(e) => setSelectedTemplateId(Number(e.target.value))}
              className="w-full text-xs px-3.5 py-2 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500 font-semibold"
            >
              {templates.map((tpl) => (
                <option key={tpl.id} value={tpl.id}>
                  {tpl.name} ({tpl.ats_score}% ATS) - {tpl.category}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Selected Template Visual Banner */}
        {(() => {
          const currentTpl = templates.find((t) => t.id === selectedTemplateId);
          if (!currentTpl) return null;
          return (
            <div className="pt-2 border-t border-app-border/60 flex items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-3">
                {currentTpl.preview_image && (
                  <img
                    src={currentTpl.preview_image}
                    alt={currentTpl.name}
                    className="w-10 h-12 object-cover object-top rounded border border-app-border shadow-xs"
                  />
                )}
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-app-text">{currentTpl.name}</span>
                    <Badge className="bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 text-[10px] font-bold">
                      {currentTpl.ats_score}% ATS
                    </Badge>
                  </div>
                  <p className="text-[11px] text-app-text-muted line-clamp-1">{currentTpl.description}</p>
                </div>
              </div>
              <Link
                href="/candidate/resumes/templates"
                className="text-[11px] font-semibold text-blue-600 hover:text-blue-500 shrink-0"
              >
                Change in Gallery
              </Link>
            </div>
          );
        })()}
      </Card>

      {/* Navigation Tabs */}
      <div className="flex overflow-x-auto gap-2 border-b border-app-border pb-2">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                isActive
                  ? "bg-blue-600 text-white shadow-sm"
                  : "bg-app-card border border-app-border text-app-text-muted hover:text-app-text hover:bg-app-surface"
              }`}
            >
              <Icon size={14} />
              <span>{tab.name}</span>
            </button>
          );
        })}
      </div>

      {/* TAB CONTENT */}
      <Card className="p-6 md:p-8 bg-app-card border-app-border space-y-6">
        {/* Personal Info Tab */}
        {activeTab === "personal" && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-app-text uppercase tracking-wider border-b border-app-border pb-2">
              Personal & Contact Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-app-text mb-1">Full Name</label>
                <input
                  type="text"
                  value={personalInfo.full_name}
                  onChange={(e) => setPersonalInfo({ ...personalInfo, full_name: e.target.value })}
                  placeholder="e.g. John Doe"
                  className="w-full text-xs px-3 py-2 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-app-text mb-1">Email</label>
                <input
                  type="email"
                  value={personalInfo.email}
                  onChange={(e) => setPersonalInfo({ ...personalInfo, email: e.target.value })}
                  placeholder="e.g. john@example.com"
                  className="w-full text-xs px-3 py-2 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-app-text mb-1">Phone</label>
                <input
                  type="text"
                  value={personalInfo.phone}
                  onChange={(e) => setPersonalInfo({ ...personalInfo, phone: e.target.value })}
                  placeholder="e.g. +1 555 123 4567"
                  className="w-full text-xs px-3 py-2 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-app-text mb-1">Location</label>
                <input
                  type="text"
                  value={personalInfo.location}
                  onChange={(e) => setPersonalInfo({ ...personalInfo, location: e.target.value })}
                  placeholder="e.g. San Francisco, CA / Remote"
                  className="w-full text-xs px-3 py-2 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-app-text mb-1">LinkedIn Profile</label>
                <input
                  type="text"
                  value={personalInfo.linkedin}
                  onChange={(e) => setPersonalInfo({ ...personalInfo, linkedin: e.target.value })}
                  placeholder="e.g. linkedin.com/in/johndoe"
                  className="w-full text-xs px-3 py-2 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-app-text mb-1">GitHub Profile</label>
                <input
                  type="text"
                  value={personalInfo.github}
                  onChange={(e) => setPersonalInfo({ ...personalInfo, github: e.target.value })}
                  placeholder="e.g. github.com/johndoe"
                  className="w-full text-xs px-3 py-2 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        )}

        {/* Summary Tab */}
        {activeTab === "summary" && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-app-text uppercase tracking-wider border-b border-app-border pb-2">
              Professional Summary
            </h3>
            <textarea
              rows={5}
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              placeholder="Concise 2-3 sentence overview highlighting your background, core technical strengths, and measurable impact..."
              className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500 leading-relaxed"
            />
          </div>
        )}

        {/* Experience Tab */}
        {activeTab === "experience" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-app-border pb-2">
              <h3 className="text-sm font-bold text-app-text uppercase tracking-wider">
                Work Experience ({experience.length})
              </h3>
              <Button size="sm" onClick={addExperience} className="text-xs bg-blue-600 text-white">
                <Plus size={13} className="mr-1" /> Add Position
              </Button>
            </div>

            {experience.map((exp, expIdx) => (
              <div key={expIdx} className="p-4 rounded-xl border border-app-border bg-app-surface/50 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-app-text">Position #{expIdx + 1}</span>
                  <button
                    onClick={() => removeExperience(expIdx)}
                    className="text-red-500 hover:text-red-600 text-xs p-1"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                  <div>
                    <label className="block text-[11px] font-medium text-app-text mb-1">Job Title</label>
                    <input
                      type="text"
                      value={exp.title || ""}
                      onChange={(e) => updateExperience(expIdx, "title", e.target.value)}
                      placeholder="e.g. Senior Software Engineer"
                      className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-surface text-app-text"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-app-text mb-1">Company</label>
                    <input
                      type="text"
                      value={exp.company || ""}
                      onChange={(e) => updateExperience(expIdx, "company", e.target.value)}
                      placeholder="e.g. Google"
                      className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-surface text-app-text"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-app-text mb-1">Start Date</label>
                    <input
                      type="text"
                      value={exp.start_date || ""}
                      onChange={(e) => updateExperience(expIdx, "start_date", e.target.value)}
                      placeholder="e.g. Jan 2022"
                      className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-surface text-app-text"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-app-text mb-1">End Date</label>
                    <input
                      type="text"
                      value={exp.end_date || ""}
                      onChange={(e) => updateExperience(expIdx, "end_date", e.target.value)}
                      placeholder="e.g. Present"
                      className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-surface text-app-text"
                    />
                  </div>
                </div>

                {/* Bullets */}
                <div className="space-y-2 pt-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-app-text-muted">Achievement Bullets</span>
                    <button
                      onClick={() => addExperienceBullet(expIdx)}
                      className="text-xs text-blue-600 font-semibold hover:underline"
                    >
                      + Add Bullet
                    </button>
                  </div>
                  {(exp.bullets || []).map((bullet, bIdx) => (
                    <div key={bIdx} className="flex items-center gap-2">
                      <input
                        type="text"
                        value={bullet}
                        onChange={(e) => updateExperienceBullet(expIdx, bIdx, e.target.value)}
                        placeholder="Action verb + context + measurable result (e.g. Reduced latency by 35%)..."
                        className="flex-1 text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-surface text-app-text"
                      />
                      <button
                        onClick={() => removeExperienceBullet(expIdx, bIdx)}
                        className="text-app-text-muted hover:text-red-500 p-1"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Education Tab */}
        {activeTab === "education" && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-app-text uppercase tracking-wider border-b border-app-border pb-2">
              Education
            </h3>
            {education.map((edu, idx) => (
              <div key={idx} className="p-4 rounded-xl border border-app-border bg-app-surface/50 space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[11px] font-medium text-app-text mb-1">Degree</label>
                    <input
                      type="text"
                      value={edu.degree || ""}
                      onChange={(e) => {
                        const updated = [...education];
                        updated[idx].degree = e.target.value;
                        setEducation(updated);
                      }}
                      className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-surface text-app-text"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-app-text mb-1">Institution</label>
                    <input
                      type="text"
                      value={edu.institution || ""}
                      onChange={(e) => {
                        const updated = [...education];
                        updated[idx].institution = e.target.value;
                        setEducation(updated);
                      }}
                      className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-surface text-app-text"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-app-text mb-1">Graduation Year / GPA</label>
                    <input
                      type="text"
                      value={edu.graduation_year || ""}
                      onChange={(e) => {
                        const updated = [...education];
                        updated[idx].graduation_year = e.target.value;
                        setEducation(updated);
                      }}
                      className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-surface text-app-text"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Skills Tab */}
        {activeTab === "skills" && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-app-text uppercase tracking-wider border-b border-app-border pb-2">
              Technical & Professional Skills
            </h3>
            <p className="text-xs text-app-text-muted">
              Organize your skills by categories (e.g. &quot;Languages: Python, Go&quot;) or enter comma-separated skills.
            </p>
            <textarea
              rows={6}
              value={skillsText}
              onChange={(e) => setSkillsText(e.target.value)}
              className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
            />
          </div>
        )}

        {/* Projects Tab */}
        {activeTab === "projects" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-app-border pb-2">
              <h3 className="text-sm font-bold text-app-text uppercase tracking-wider">
                Projects ({projects.length})
              </h3>
              <Button size="sm" onClick={addProject} className="text-xs bg-blue-600 text-white">
                <Plus size={13} className="mr-1" /> Add Project
              </Button>
            </div>

            {projects.map((proj, pIdx) => (
              <div key={pIdx} className="p-4 rounded-xl border border-app-border bg-app-surface/50 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-app-text">Project #{pIdx + 1}</span>
                  <button onClick={() => removeProject(pIdx)} className="text-red-500 p-1">
                    <Trash2 size={14} />
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-medium text-app-text mb-1">Project Name</label>
                    <input
                      type="text"
                      value={proj.name || ""}
                      onChange={(e) => updateProject(pIdx, "name", e.target.value)}
                      placeholder="e.g. Distributed Task Queue"
                      className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-surface text-app-text"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-app-text mb-1">Tech Stack</label>
                    <input
                      type="text"
                      value={proj.tech_stack || proj.technologies || ""}
                      onChange={(e) => updateProject(pIdx, "tech_stack", e.target.value)}
                      placeholder="e.g. Go, Redis, Docker, gRPC"
                      className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-surface text-app-text"
                    />
                  </div>
                </div>

                {/* Bullets */}
                <div className="space-y-2 pt-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-app-text-muted">Key Bullets</span>
                    <button onClick={() => addProjectBullet(pIdx)} className="text-xs text-blue-600 font-semibold hover:underline">
                      + Add Bullet
                    </button>
                  </div>
                  {(proj.bullets || []).map((bullet, bIdx) => (
                    <div key={bIdx} className="flex items-center gap-2">
                      <input
                        type="text"
                        value={bullet}
                        onChange={(e) => updateProjectBullet(pIdx, bIdx, e.target.value)}
                        placeholder="Built X using Y, resulting in Z..."
                        className="flex-1 text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-surface text-app-text"
                      />
                      <button onClick={() => removeProjectBullet(pIdx, bIdx)} className="text-app-text-muted hover:text-red-500 p-1">
                        <Trash2 size={13} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Certifications Tab */}
        {activeTab === "certifications" && (
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-app-text uppercase tracking-wider border-b border-app-border pb-2">
              Certifications & Honors
            </h3>
            <textarea
              rows={5}
              value={certificationsText}
              onChange={(e) => setCertificationsText(e.target.value)}
              placeholder="One certification per line..."
              className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}
      </Card>
    </div>
  );
}

export default function ResumeBuilderPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center text-xs">Loading resume builder...</div>}>
      <ResumeBuilderContent />
    </Suspense>
  );
}
