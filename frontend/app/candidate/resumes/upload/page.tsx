"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { 
  Upload, FileText, CheckCircle2, AlertCircle, ArrowLeft, 
  ArrowRight, Loader2, Sparkles, User, Briefcase, GraduationCap, 
  Code, ShieldCheck, Eye, Layers, Plus, Trash2, Globe, Award, 
  Terminal, Check, ExternalLink, AlertTriangle, HelpCircle,
  FileCheck, BookOpen, Tag, RefreshCw
} from "lucide-react";
import { 
  resumeCenterApi, 
  ComprehensiveExtractedProfile, 
  ResumeTemplateItem 
} from "@/services/resumeCenterApi";
import { useResumeStore } from "@/store/resumeStore";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";

function normalizeExtractedData(data: any): ComprehensiveExtractedProfile {
  if (!data || typeof data !== "object") return {};
  const pi = data.personal_info || {};
  const ps = data.professional_summary || {};

  const normalizedPi = {
    ...pi,
    full_name: pi.full_name || pi.name || "",
    professional_title: pi.professional_title || pi.title || data.primary_designation || "",
    email: pi.email || "",
    phone: pi.phone || "",
    location: pi.location || "",
    linkedin_url: pi.linkedin_url || pi.linkedin || "",
    github_url: pi.github_url || pi.github || "",
    portfolio_url: pi.portfolio_url || pi.portfolio || "",
  };

  const normalizedPs = {
    summary: typeof ps === "string" ? ps : (ps.summary || data.summary || ""),
    career_objective: typeof ps === "object" ? (ps.career_objective || "") : "",
    years_of_experience: typeof ps === "object" ? ps.years_of_experience : null,
    areas_of_specialization: typeof ps === "object" ? (ps.areas_of_specialization || []) : [],
  };

  const rawSkills = data.skills || data.raw_skills || {};
  const normalizedSkills: Record<string, string[]> = {};
  if (typeof rawSkills === "object" && !Array.isArray(rawSkills)) {
    const keyMap: Record<string, string> = {
      "programming languages": "programming_languages",
      "programming_languages": "programming_languages",
      "frameworks & libraries": "frameworks_libraries",
      "frameworks and libraries": "frameworks_libraries",
      "frameworks_libraries": "frameworks_libraries",
      "databases": "databases",
      "databases & storage": "databases",
      "cloud platforms & devops": "cloud_platforms",
      "cloud & devops": "cloud_platforms",
      "cloud platforms": "cloud_platforms",
      "cloud_platforms": "cloud_platforms",
      "developer tools": "developer_tools",
      "developer_tools": "developer_tools",
      "ai & machine learning": "ai_ml_technologies",
      "ai and machine learning": "ai_ml_technologies",
      "ai_ml_technologies": "ai_ml_technologies",
      "soft skills & leadership": "soft_skills",
      "soft skills": "soft_skills",
      "core competencies": "soft_skills",
      "soft_skills": "soft_skills",
      "domain knowledge": "domain_knowledge",
      "domain_knowledge": "domain_knowledge",
      "other skills": "other_skills",
      "other technologies": "other_skills",
      "technical skills": "other_skills",
      "other_skills": "other_skills",
    };
    for (const [k, v] of Object.entries(rawSkills)) {
      if (Array.isArray(v)) {
        normalizedSkills[k] = v;
        const lowerK = k.toLowerCase().trim();
        const mappedKey = keyMap[lowerK];
        if (mappedKey) {
          normalizedSkills[mappedKey] = v;
        }
      }
    }
  }

  let workExp = data.work_experience || data.experience || [];
  if (Array.isArray(workExp)) {
    workExp = workExp.map((e: any) => ({
      ...e,
      employer: e.employer || e.company || "",
      company: e.company || e.employer || "",
      designation: e.designation || e.title || e.role || "",
      title: e.title || e.designation || e.role || "",
      employment_location: e.employment_location || e.location || "",
      location: e.location || e.employment_location || "",
      responsibilities: Array.isArray(e.responsibilities) ? e.responsibilities : (e.bullets || []),
      bullets: Array.isArray(e.bullets) ? e.bullets : (e.responsibilities || []),
    }));
  }

  let projs = data.projects || [];
  if (Array.isArray(projs)) {
    projs = projs.map((p: any) => {
      let techs = p.technologies;
      if (!techs && p.tech_stack) {
        techs = typeof p.tech_stack === "string" ? p.tech_stack.split(",").map((s: string) => s.trim()) : p.tech_stack;
      }
      return {
        ...p,
        technologies: Array.isArray(techs) ? techs : [],
        responsibilities: Array.isArray(p.responsibilities) ? p.responsibilities : (p.bullets || (p.description ? [p.description] : [])),
      };
    });
  }

  let edus = data.education || [];
  if (Array.isArray(edus)) {
    edus = edus.map((ed: any) => ({
      ...ed,
      institution: ed.institution || ed.university || "",
      degree: ed.degree || "",
      graduation_year: ed.graduation_year || ed.end_date || "",
      grade: ed.grade || ed.gpa || "",
    }));
  }

  let certs = data.certifications || [];
  if (Array.isArray(certs)) {
    certs = certs.map((c: any) => {
      if (typeof c === "string") {
        return { name: c, issuing_organization: "", issue_date: "" };
      }
      return {
        ...c,
        name: c.name || "Certification",
        issuing_organization: c.issuing_organization || c.issuer || "",
        issue_date: c.issue_date || "",
      };
    });
  }

  return {
    ...data,
    personal_info: normalizedPi,
    professional_summary: normalizedPs,
    skills: normalizedSkills as any,
    work_experience: workExp,
    projects: projs,
    education: edus,
    certifications: certs,
  };
}

function ResumeUploadContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const resumeIdParam = searchParams.get("resumeId");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [customTitle, setCustomTitle] = useState("");
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | undefined>(undefined);
  const [templates, setTemplates] = useState<ResumeTemplateItem[]>([]);

  // Workflow states
  const [step, setStep] = useState<"upload" | "parsing" | "review">("upload");
  const [progressStage, setProgressStage] = useState(0);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  // Extracted data state
  const [createdResumeId, setCreatedResumeId] = useState<number | null>(
    resumeIdParam ? Number(resumeIdParam) : null
  );
  const [extractedData, setExtractedData] = useState<ComprehensiveExtractedProfile>({});
  const [rawText, setRawText] = useState<string>("");
  const [confidenceScore, setConfidenceScore] = useState<number>(1.0);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [fileMeta, setFileMeta] = useState<{ name?: string; size?: number; pages?: number }>({});
  const [isVerified, setIsVerified] = useState<boolean>(false);

  // Active Review Tab
  const [activeReviewTab, setActiveReviewTab] = useState<
    "personal" | "summary" | "skills" | "experience" | "education" | "projects" | "certifications" | "achievements" | "custom" | "raw"
  >("personal");

  useEffect(() => {
    resumeCenterApi.getTemplates()
      .then((res) => {
        setTemplates(res);
        if (res.length > 0 && !selectedTemplateId) setSelectedTemplateId(res[0].id);
      })
      .catch((err) => console.error("Could not load templates:", err));

    // If navigated with existing resumeId to review
    if (resumeIdParam) {
      resumeCenterApi.getExtraction(Number(resumeIdParam))
        .then((data) => {
          setCreatedResumeId(data.resume_id);
          setExtractedData(normalizeExtractedData(data.structured_data || {}));
          setRawText(data.raw_text || "");
          setConfidenceScore(data.confidence_score || 1.0);
          setWarnings(data.warnings || []);
          setMissingFields(data.missing_fields || []);
          setIsVerified(data.is_verified || false);
          setFileMeta({ name: data.file_name, size: data.file_size, pages: data.page_count });
          setStep("review");
        })
        .catch((err) => console.error("Could not load existing extraction:", err));
    }
  }, [resumeIdParam]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const validateAndSetFile = (selectedFile: File) => {
    setErrorMessage("");
    const validExtensions = [".pdf", ".docx", ".txt", ".tex"];
    const ext = "." + selectedFile.name.split(".").pop()?.toLowerCase();
    
    if (!validExtensions.includes(ext)) {
      setErrorMessage("Unsupported file type. Please upload a PDF, DOCX, TXT, or TeX document.");
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setErrorMessage("File exceeds 10MB limit. Please upload a smaller file.");
      return;
    }

    setFile(selectedFile);
    if (!customTitle) {
      const baseName = selectedFile.name.substring(0, selectedFile.name.lastIndexOf('.')) || selectedFile.name;
      setCustomTitle(baseName);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const startUploadAndParse = async (e?: React.SyntheticEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (!file || isUploading) return;

    setIsUploading(true);
    setStep("parsing");
    setErrorMessage("");
    setProgressStage(1); // File Validation & SHA-256 Hash

    try {
      setTimeout(() => setProgressStage(2), 500); // Private User Storage
      setTimeout(() => setProgressStage(3), 1100); // Multi-Column Text & OCR Detection
      setTimeout(() => setProgressStage(4), 1800); // AI-Based Semantic Structuring
      setTimeout(() => setProgressStage(5), 2600); // Completeness & Consistency Audit

      const res = await resumeCenterApi.uploadResume(
        file,
        customTitle || file.name,
        selectedTemplateId
      );

      // Auto-refresh the global Zustand store so activeResume is immediately updated everywhere
      await useResumeStore.getState().fetchActiveResume();

      setCreatedResumeId(res.resume_id);
      setExtractedData(normalizeExtractedData(res.structured_data || {}));
      setRawText(res.raw_text_preview || "");
      setConfidenceScore(res.confidence_score || 1.0);
      setWarnings(res.warnings || []);
      setMissingFields(res.missing_fields || []);
      setFileMeta({ name: res.file_name, size: res.file_size, pages: res.page_count });
      setIsVerified(false);

      setStep("review");
      setSuccessMessage(
        res.is_duplicate 
          ? "Resume parsed! (Note: Duplicate file previously uploaded; details refreshed)."
          : "Extraction complete! Review all extracted sections, add any missing items, and verify below."
      );
    } catch (err: any) {
      setStep("upload");
      setErrorMessage(err.message || "Resume upload failed. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  // State Mutators for Personal Info
  const updatePersonalInfo = (field: string, val: any) => {
    setExtractedData((prev) => ({
      ...prev,
      personal_info: {
        ...(prev.personal_info || {}),
        [field]: val,
      },
    }));
  };

  // State Mutators for Summary
  const updateSummary = (field: string, val: any) => {
    setExtractedData((prev) => ({
      ...prev,
      professional_summary: {
        ...(prev.professional_summary || {}),
        [field]: val,
      },
    }));
  };

  // State Mutators for Categorized Skills
  const addSkillToCategory = (catKey: string, newSkill: string) => {
    if (!newSkill.trim()) return;
    setExtractedData((prev) => {
      const skillsObj = { ...(prev.skills || {}) };
      const currentList = Array.isArray((skillsObj as any)[catKey]) ? (skillsObj as any)[catKey] : [];
      (skillsObj as any)[catKey] = [...currentList, newSkill.trim()];
      return { ...prev, skills: skillsObj };
    });
  };

  const removeSkillFromCategory = (catKey: string, indexToRemove: number) => {
    setExtractedData((prev) => {
      const skillsObj = { ...(prev.skills || {}) };
      const currentList = Array.isArray((skillsObj as any)[catKey]) ? (skillsObj as any)[catKey] : [];
      (skillsObj as any)[catKey] = currentList.filter((_: any, idx: number) => idx !== indexToRemove);
      return { ...prev, skills: skillsObj };
    });
  };

  // State Mutators for Experience
  const addExperienceItem = () => {
    setExtractedData((prev) => ({
      ...prev,
      work_experience: [
        ...(prev.work_experience || []),
        {
          employer: "New Company",
          designation: "Role / Title",
          employment_location: "",
          start_date: "",
          end_date: "",
          is_current: false,
          responsibilities: [""],
          technologies: [],
        },
      ],
    }));
  };

  const updateExperienceItem = (index: number, field: string, val: any) => {
    setExtractedData((prev) => {
      const exps = [...(prev.work_experience || [])];
      exps[index] = { ...exps[index], [field]: val };
      return { ...prev, work_experience: exps };
    });
  };

  const removeExperienceItem = (index: number) => {
    setExtractedData((prev) => ({
      ...prev,
      work_experience: (prev.work_experience || []).filter((_, i) => i !== index),
    }));
  };

  // State Mutators for Education
  const addEducationItem = () => {
    setExtractedData((prev) => ({
      ...prev,
      education: [
        ...(prev.education || []),
        {
          degree: "Bachelor of Science",
          institution: "University Name",
          location: "",
          graduation_year: "",
          grade: "",
          relevant_coursework: [],
        },
      ],
    }));
  };

  const updateEducationItem = (index: number, field: string, val: any) => {
    setExtractedData((prev) => {
      const edus = [...(prev.education || [])];
      edus[index] = { ...edus[index], [field]: val };
      return { ...prev, education: edus };
    });
  };

  const removeEducationItem = (index: number) => {
    setExtractedData((prev) => ({
      ...prev,
      education: (prev.education || []).filter((_, i) => i !== index),
    }));
  };

  // State Mutators for Projects
  const addProjectItem = () => {
    setExtractedData((prev) => ({
      ...prev,
      projects: [
        ...(prev.projects || []),
        {
          name: "New Project",
          description: "",
          technologies: [],
          responsibilities: [""],
          link: "",
        },
      ],
    }));
  };

  const updateProjectItem = (index: number, field: string, val: any) => {
    setExtractedData((prev) => {
      const projs = [...(prev.projects || [])];
      projs[index] = { ...projs[index], [field]: val };
      return { ...prev, projects: projs };
    });
  };

  const removeProjectItem = (index: number) => {
    setExtractedData((prev) => ({
      ...prev,
      projects: (prev.projects || []).filter((_, i) => i !== index),
    }));
  };

  // State Mutators for Certifications
  const addCertItem = () => {
    setExtractedData((prev) => ({
      ...prev,
      certifications: [
        ...(prev.certifications || []),
        { name: "New Certification", issuing_organization: "", issue_date: "" },
      ],
    }));
  };

  const removeCertItem = (index: number) => {
    setExtractedData((prev) => ({
      ...prev,
      certifications: (prev.certifications || []).filter((_, i) => i !== index),
    }));
  };

  // Handle Save & Mark Verified
  const handleSaveAndVerify = async (openEditor = true) => {
    if (!createdResumeId) return;

    try {
      setIsSaving(true);
      setErrorMessage("");

      await resumeCenterApi.verifyExtraction(createdResumeId, {
        structured_data: extractedData,
        raw_text: rawText,
      });

      setIsVerified(true);
      setSuccessMessage("Extraction verified and saved to database successfully!");

      if (openEditor) {
        setTimeout(() => {
          router.push(`/candidate/resumes/edit/${createdResumeId}`);
        }, 600);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to verify extraction.");
    } finally {
      setIsSaving(false);
    }
  };

  const countSkills = (data: ComprehensiveExtractedProfile) => {
    if (!data.skills) return 0;
    const skillsObj = data.skills as Record<string, any>;
    let total = 0;
    for (const key in skillsObj) {
      if (key !== "all_raw_skills" && Array.isArray(skillsObj[key])) {
        total += skillsObj[key].length;
      }
    }
    return total || (skillsObj.all_raw_skills?.length || 0);
  };

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-6 font-sans">
      {/* Breadcrumb / Navigation */}
      <div className="flex items-center justify-between">
        <Link 
          href="/candidate/resumes" 
          className="inline-flex items-center gap-2 text-xs font-semibold text-app-text-muted hover:text-app-text transition-colors"
        >
          <ArrowLeft size={14} /> Back to Resume Center
        </Link>
        <span className="text-xs font-semibold text-app-text-muted">
          {step === "upload" ? "Step 1 of 2: Upload Document" : "Step 2 of 2: Data Review & Verification"}
        </span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-app-text tracking-tight flex items-center gap-2.5">
          <Upload className="text-blue-600 dark:text-blue-400" size={28} />
          A-to-Z Resume Extraction & Storage Engine
        </h1>
        <p className="text-xs md:text-sm text-app-text-muted mt-1 leading-relaxed">
          Upload PDF or DOCX resumes. Our hybrid engine parses multi-column layouts, runs OCR when necessary, extracts comprehensive structured data without hallucination, and preserves your original file.
        </p>
      </div>

      {errorMessage && <Alert variant="error">{errorMessage}</Alert>}
      {successMessage && <Alert variant="success">{successMessage}</Alert>}

      {/* ── STEP 1: Upload Zone ──────────────────────────────────────────────── */}
      {step === "upload" && (
        <Card className="p-6 md:p-8 bg-app-card border-app-border space-y-6 shadow-sm">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-8 md:p-12 text-center cursor-pointer transition-all duration-200 flex flex-col items-center justify-center gap-3 ${
              dragOver
                ? "border-blue-500 bg-blue-50/50 dark:bg-blue-950/20 scale-[0.99]"
                : "border-app-border hover:border-blue-400/80 bg-app-surface/40 hover:bg-app-surface"
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf,.docx,.txt,.tex"
              className="hidden"
            />
            <div className="w-16 h-16 rounded-2xl bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 flex items-center justify-center border border-blue-200/60 dark:border-blue-800/40 shadow-sm">
              <Upload size={28} />
            </div>
            <div>
              <p className="text-sm font-bold text-app-text">
                {file ? file.name : "Click to select or drag and drop your resume"}
              </p>
              <p className="text-xs text-app-text-muted mt-1">
                Supports PDF (selectable or scanned), Word (DOCX), TXT, or TeX • Max 10MB
              </p>
            </div>
            {file && (
              <Badge className="bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 text-xs py-1 px-3 mt-1">
                <CheckCircle2 size={13} className="mr-1.5" />
                {(file.size / 1024).toFixed(1)} KB ready for extraction
              </Badge>
            )}
          </div>

          {/* Configuration Controls */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-bold text-app-text mb-1.5">
                Resume Title (Optional)
              </label>
              <input
                type="text"
                value={customTitle}
                onChange={(e) => setCustomTitle(e.target.value)}
                placeholder="e.g. Senior Software Engineer - Extracted"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-app-text mb-1.5">
                Initial Overleaf LaTeX Template
              </label>
              <select
                value={selectedTemplateId || ""}
                onChange={(e) => setSelectedTemplateId(Number(e.target.value))}
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
              >
                {templates.map((tpl) => (
                  <option key={tpl.id} value={tpl.id}>
                    {tpl.name} ({tpl.ats_score}% ATS • {tpl.category})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Pipeline Features Note */}
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-app-border text-xs text-app-text-muted space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-app-text block">Extraction Guarantees:</span>
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800 text-[10px] font-extrabold">
                <Sparkles size={11} className="text-amber-500 animate-pulse" />
                <span>AI-Powered Extraction Engine Active</span>
              </span>
            </div>
            <ul className="list-disc pl-5 space-y-0.5 text-[11px]">
              <li>Zero hallucination: only facts present in your document are extracted.</li>
              <li>Multi-column reading order and hyperlink anchors are recovered.</li>
              <li>Scanned pages are processed with OCR.</li>
              <li>Original document is stored separately and never modified.</li>
            </ul>
          </div>

          <div className="flex items-center justify-between pt-4 border-t border-app-border">
            <span className="text-xs text-app-text-muted">
              {file ? `File selected (${(file.size / 1024).toFixed(1)} KB)` : "No file chosen"}
            </span>
            <Button
              type="button"
              disabled={!file || isUploading}
              onClick={(e) => startUploadAndParse(e)}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-6 py-2.5 shadow-sm disabled:opacity-50"
            >
              {isUploading ? (
                <>
                  <Loader2 size={14} className="mr-1.5 animate-spin" />
                  Extracting Resume...
                </>
              ) : (
                <>
                  Start Full Extraction
                  <ArrowRight size={14} className="ml-1.5" />
                </>
              )}
            </Button>
          </div>
        </Card>
      )}

      {/* ── STEP 2: Processing Progress ─────────────────────────────────────── */}
      {step === "parsing" && (
        <Card className="p-10 bg-app-card border-app-border text-center space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 flex items-center justify-center mx-auto border border-blue-200 dark:border-blue-800 animate-pulse">
            <Loader2 size={30} className="animate-spin" />
          </div>

          <div className="space-y-2">
            <h2 className="text-lg font-extrabold text-app-text">
              Extracting Complete Resume Data...
            </h2>
            <p className="text-xs text-app-text-muted max-w-md mx-auto">
              Please wait while our engine validates file signatures, preserves your original file, reads layout reading order, and extracts all resume sections.
            </p>
          </div>

          <div className="max-w-md mx-auto space-y-2.5 text-left text-xs">
            <div className={`p-2.5 rounded-xl border flex items-center gap-2.5 ${progressStage >= 1 ? "bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300" : "bg-app-surface border-app-border text-app-text-muted"}`}>
              <CheckCircle2 size={16} className={progressStage >= 1 ? "text-emerald-600" : "opacity-40"} />
              <span>1. File integrity validation & SHA-256 duplicate detection</span>
            </div>
            <div className={`p-2.5 rounded-xl border flex items-center gap-2.5 ${progressStage >= 2 ? "bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300" : "bg-app-surface border-app-border text-app-text-muted"}`}>
              <CheckCircle2 size={16} className={progressStage >= 2 ? "text-emerald-600" : "opacity-40"} />
              <span>2. Secure private user file storage</span>
            </div>
            <div className={`p-2.5 rounded-xl border flex items-center gap-2.5 ${progressStage >= 3 ? "bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300" : "bg-app-surface border-app-border text-app-text-muted"}`}>
              <CheckCircle2 size={16} className={progressStage >= 3 ? "text-emerald-600" : "opacity-40"} />
              <span>3. Multi-column reading-order & OCR detection</span>
            </div>
            <div className={`p-2.5 rounded-xl border flex items-center gap-2.5 ${progressStage >= 4 ? "bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300" : "bg-app-surface border-app-border text-app-text-muted"}`}>
              <CheckCircle2 size={16} className={progressStage >= 4 ? "text-emerald-600" : "opacity-40"} />
              <span>4. AI-based semantic structured extraction</span>
            </div>
            <div className={`p-2.5 rounded-xl border flex items-center gap-2.5 ${progressStage >= 5 ? "bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300" : "bg-app-surface border-app-border text-app-text-muted"}`}>
              <CheckCircle2 size={16} className={progressStage >= 5 ? "text-emerald-600" : "opacity-40"} />
              <span>5. Completeness & date anomaly audit</span>
            </div>
          </div>
        </Card>
      )}

      {/* ── STEP 3: Comprehensive Extraction Review & Correction ────────────── */}
      {step === "review" && (
        <div className="space-y-6">
          {/* Active Global Resume Success Summary Banner */}
          <div className="p-5 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 space-y-3 shadow-sm">
            <div className="flex items-center gap-2.5 text-emerald-900 dark:text-emerald-200 font-extrabold text-sm">
              <CheckCircle2 size={20} className="text-emerald-600 shrink-0" />
              <span>✓ Resume extracted successfully! Your resume is now active across VidyamargAI.</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 pt-1 text-xs">
              <div className="bg-white/90 dark:bg-slate-900/80 p-3 rounded-xl border border-emerald-200/60 dark:border-emerald-800/40 text-center">
                <span className="block text-xl font-extrabold text-emerald-700 dark:text-emerald-400">
                  {countSkills(extractedData)}
                </span>
                <span className="text-[11px] font-semibold text-emerald-800/80 dark:text-emerald-300">Skills</span>
              </div>
              <div className="bg-white/90 dark:bg-slate-900/80 p-3 rounded-xl border border-emerald-200/60 dark:border-emerald-800/40 text-center">
                <span className="block text-xl font-extrabold text-emerald-700 dark:text-emerald-400">
                  {(extractedData.work_experience || []).length}
                </span>
                <span className="text-[11px] font-semibold text-emerald-800/80 dark:text-emerald-300 font-semibold">Positions</span>
              </div>
              <div className="bg-white/90 dark:bg-slate-900/80 p-3 rounded-xl border border-emerald-200/60 dark:border-emerald-800/40 text-center">
                <span className="block text-xl font-extrabold text-emerald-700 dark:text-emerald-400">
                  {(extractedData.projects || []).length}
                </span>
                <span className="text-[11px] font-semibold text-emerald-800/80 dark:text-emerald-300">Projects</span>
              </div>
              <div className="bg-white/90 dark:bg-slate-900/80 p-3 rounded-xl border border-emerald-200/60 dark:border-emerald-800/40 text-center">
                <span className="block text-xl font-extrabold text-emerald-700 dark:text-emerald-400">
                  {(extractedData.education || []).length}
                </span>
                <span className="text-[11px] font-semibold text-emerald-800/80 dark:text-emerald-300">Education</span>
              </div>
              <div className="bg-white/90 dark:bg-slate-900/80 p-3 rounded-xl border border-emerald-200/60 dark:border-emerald-800/40 text-center">
                <span className="block text-xl font-extrabold text-emerald-700 dark:text-emerald-400">
                  {(extractedData.certifications || []).length}
                </span>
                <span className="text-[11px] font-semibold text-emerald-800/80 dark:text-emerald-300">Certifications</span>
              </div>
            </div>
          </div>

          {/* Diagnostic Summary Bar */}
          <Card className="p-4 bg-app-card border-app-border flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 flex items-center justify-center border border-blue-200 dark:border-blue-800">
                <FileCheck size={20} />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-app-text">
                    {customTitle || fileMeta.name || "Parsed Resume"}
                  </h3>
                  <Badge className={`text-[10px] font-bold border ${isVerified ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-amber-50 text-amber-700 border-amber-200"}`}>
                    {isVerified ? "Verified" : "Review Needed"}
                  </Badge>
                </div>
                <p className="text-[11px] text-app-text-muted mt-0.5">
                  {fileMeta.name} • {fileMeta.pages ? `${fileMeta.pages} pages • ` : ""}
                  Confidence: <span className="font-bold text-app-text">{(confidenceScore * 100).toFixed(0)}%</span>
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2.5 shrink-0">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setStep("upload")}
                className="text-xs"
              >
                Re-upload File
              </Button>
              <Button
                size="sm"
                disabled={isSaving}
                onClick={() => handleSaveAndVerify(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-sm"
              >
                <Check size={14} className="mr-1.5" />
                {isSaving ? "Saving..." : "Verify & Open in Editor"}
              </Button>
            </div>
          </Card>

          {/* Warnings & Attention Alerts */}
          {warnings.length > 0 && (
            <div className="p-4 rounded-2xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 space-y-1.5 text-xs">
              <div className="flex items-center gap-2 font-bold text-amber-800 dark:text-amber-300">
                <AlertTriangle size={15} /> Attention Items Detected:
              </div>
              <ul className="list-disc pl-5 space-y-0.5 text-amber-900/80 dark:text-amber-200/80 text-[11px]">
                {warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Section Navigation Tabs */}
          <div className="flex overflow-x-auto gap-2 border-b border-app-border pb-2">
            {[
              { id: "personal", label: "Personal Info", icon: User },
              { id: "summary", label: "Summary", icon: FileText },
              { id: "skills", label: "Skills", icon: Code },
              { id: "experience", label: "Experience", icon: Briefcase },
              { id: "education", label: "Education", icon: GraduationCap },
              { id: "projects", label: "Projects", icon: BookOpen },
              { id: "certifications", label: "Certifications", icon: Award },
              { id: "achievements", label: "Languages & Awards", icon: Globe },
              { id: "custom", label: "Custom Sections", icon: Layers },
              { id: "raw", label: "Raw Extracted Text", icon: Terminal },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeReviewTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveReviewTab(tab.id as any)}
                  className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                    isActive
                      ? "bg-blue-600 text-white shadow-sm"
                      : "bg-app-card border border-app-border text-app-text-muted hover:text-app-text hover:bg-app-surface"
                  }`}
                >
                  <Icon size={13} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* ── TAB CONTENT ────────────────────────────────────────────────── */}
          <Card className="p-6 md:p-8 bg-app-card border-app-border space-y-6">
            {/* 1. PERSONAL INFO TAB */}
            {activeReviewTab === "personal" && (
              <div className="space-y-4">
                <div className="border-b border-app-border pb-2 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-app-text uppercase tracking-wider">
                    Candidate Identity & Contact Information
                  </h3>
                  <span className="text-[11px] text-app-text-muted">Edit to correct any typos</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-app-text mb-1">Full Name</label>
                    <input
                      type="text"
                      value={extractedData.personal_info?.full_name || ""}
                      onChange={(e) => updatePersonalInfo("full_name", e.target.value)}
                      placeholder="e.g. John Doe"
                      className="w-full text-xs px-3.5 py-2 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500 font-semibold"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-app-text mb-1">Professional Title</label>
                    <input
                      type="text"
                      value={extractedData.personal_info?.professional_title || ""}
                      onChange={(e) => updatePersonalInfo("professional_title", e.target.value)}
                      placeholder="e.g. Senior Software Engineer"
                      className="w-full text-xs px-3.5 py-2 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-app-text mb-1">Primary Email</label>
                    <input
                      type="email"
                      value={extractedData.personal_info?.email || ""}
                      onChange={(e) => updatePersonalInfo("email", e.target.value)}
                      placeholder="e.g. john@example.com"
                      className="w-full text-xs px-3.5 py-2 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-app-text mb-1">Phone Number</label>
                    <input
                      type="text"
                      value={extractedData.personal_info?.phone || ""}
                      onChange={(e) => updatePersonalInfo("phone", e.target.value)}
                      placeholder="e.g. +1 555-0199"
                      className="w-full text-xs px-3.5 py-2 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-app-text mb-1">Location / City</label>
                    <input
                      type="text"
                      value={extractedData.personal_info?.location || ""}
                      onChange={(e) => updatePersonalInfo("location", e.target.value)}
                      placeholder="e.g. San Francisco, CA"
                      className="w-full text-xs px-3.5 py-2 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-app-text mb-1">LinkedIn Profile URL</label>
                    <input
                      type="text"
                      value={extractedData.personal_info?.linkedin_url || ""}
                      onChange={(e) => updatePersonalInfo("linkedin_url", e.target.value)}
                      placeholder="https://linkedin.com/in/username"
                      className="w-full text-xs px-3.5 py-2 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-app-text mb-1">GitHub Profile URL</label>
                    <input
                      type="text"
                      value={extractedData.personal_info?.github_url || ""}
                      onChange={(e) => updatePersonalInfo("github_url", e.target.value)}
                      placeholder="https://github.com/username"
                      className="w-full text-xs px-3.5 py-2 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-app-text mb-1">Portfolio / Website</label>
                    <input
                      type="text"
                      value={extractedData.personal_info?.portfolio_url || ""}
                      onChange={(e) => updatePersonalInfo("portfolio_url", e.target.value)}
                      placeholder="https://myportfolio.dev"
                      className="w-full text-xs px-3.5 py-2 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* 2. SUMMARY TAB */}
            {activeReviewTab === "summary" && (
              <div className="space-y-4">
                <div className="border-b border-app-border pb-2 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-app-text uppercase tracking-wider">
                    Professional Summary & Objectives
                  </h3>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-app-text mb-1">
                    Professional Summary
                  </label>
                  <textarea
                    rows={4}
                    value={extractedData.professional_summary?.summary || ""}
                    onChange={(e) => updateSummary("summary", e.target.value)}
                    placeholder="Brief overview of background, core strengths, and career highlights..."
                    className="w-full text-xs p-3 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500 leading-relaxed"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-app-text mb-1">
                    Career Objective (Optional)
                  </label>
                  <textarea
                    rows={2}
                    value={extractedData.professional_summary?.career_objective || ""}
                    onChange={(e) => updateSummary("career_objective", e.target.value)}
                    placeholder="Target role or trajectory goals..."
                    className="w-full text-xs p-3 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500 leading-relaxed"
                  />
                </div>
              </div>
            )}

            {/* 3. SKILLS TAB */}
            {activeReviewTab === "skills" && (
              <div className="space-y-5">
                <div className="border-b border-app-border pb-2 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-app-text uppercase tracking-wider">
                    Categorized Skills Architecture
                  </h3>
                  <span className="text-[11px] text-app-text-muted">Extracted and grouped from source</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { key: "programming_languages", title: "Programming Languages" },
                    { key: "frameworks_libraries", title: "Frameworks & Libraries" },
                    { key: "databases", title: "Databases & Storage" },
                    { key: "cloud_platforms", title: "Cloud Platforms & DevOps" },
                    { key: "developer_tools", title: "Developer Tools" },
                    { key: "ai_ml_technologies", title: "AI & Machine Learning" },
                    { key: "soft_skills", title: "Soft Skills & Leadership" },
                    { key: "domain_knowledge", title: "Domain Knowledge" },
                    { key: "other_skills", title: "Other Technologies" },
                  ].map((cat) => {
                    const list = (extractedData.skills as any)?.[cat.key] || [];
                    return (
                      <div key={cat.key} className="p-4 rounded-xl border border-app-border bg-app-surface space-y-2.5">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-app-text">{cat.title}</span>
                          <span className="text-[10px] text-app-text-muted">{list.length} skills</span>
                        </div>
                        <div className="flex flex-wrap gap-1.5 min-h-[32px]">
                          {list.map((item: string, idx: number) => (
                            <span
                              key={idx}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs bg-app-card border border-app-border text-app-text font-medium"
                            >
                              <span>{item}</span>
                              <button
                                type="button"
                                onClick={() => removeSkillFromCategory(cat.key, idx)}
                                className="text-app-text-muted hover:text-rose-500"
                              >
                                &times;
                              </button>
                            </span>
                          ))}
                        </div>
                        <div className="flex items-center gap-2 pt-1">
                          <input
                            type="text"
                            placeholder={`Add to ${cat.title}...`}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                e.preventDefault();
                                addSkillToCategory(cat.key, (e.target as HTMLInputElement).value);
                                (e.target as HTMLInputElement).value = "";
                              }
                            }}
                            className="flex-1 text-[11px] px-2.5 py-1.5 rounded-lg border border-app-border bg-app-card text-app-text focus:outline-none focus:ring-1 focus:ring-blue-500"
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* 4. WORK EXPERIENCE TAB */}
            {activeReviewTab === "experience" && (
              <div className="space-y-4">
                <div className="border-b border-app-border pb-2 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-app-text uppercase tracking-wider">
                    Work Experience & Roles ({(extractedData.work_experience || []).length})
                  </h3>
                  <Button size="sm" variant="outline" onClick={addExperienceItem} className="text-xs">
                    <Plus size={13} className="mr-1" /> Add Experience
                  </Button>
                </div>

                <div className="space-y-4">
                  {(extractedData.work_experience || []).map((exp, idx) => (
                    <div key={idx} className="p-4 rounded-xl border border-app-border bg-app-surface space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-blue-600">Entry #{idx + 1}</span>
                        <button
                          type="button"
                          onClick={() => removeExperienceItem(idx)}
                          className="text-app-text-muted hover:text-rose-500 text-xs flex items-center gap-1"
                        >
                          <Trash2 size={12} /> Remove
                        </button>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                          <label className="block text-[11px] font-semibold text-app-text-muted mb-1">Company / Employer</label>
                          <input
                            type="text"
                            value={exp.employer || exp.company || ""}
                            onChange={(e) => {
                              const val = e.target.value;
                              updateExperienceItem(idx, "employer", val);
                              updateExperienceItem(idx, "company", val);
                            }}
                            className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-card text-app-text font-semibold"
                          />
                        </div>
                        <div>
                          <label className="block text-[11px] font-semibold text-app-text-muted mb-1">Job Designation</label>
                          <input
                            type="text"
                            value={exp.designation || exp.title || exp.role || ""}
                            onChange={(e) => {
                              const val = e.target.value;
                              updateExperienceItem(idx, "designation", val);
                              updateExperienceItem(idx, "role", val);
                              updateExperienceItem(idx, "title", val);
                            }}
                            className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-card text-app-text font-semibold"
                          />
                        </div>
                        <div>
                          <label className="block text-[11px] font-semibold text-app-text-muted mb-1">Start Date</label>
                          <input
                            type="text"
                            value={exp.start_date || ""}
                            onChange={(e) => updateExperienceItem(idx, "start_date", e.target.value)}
                            placeholder="e.g. Jan 2022"
                            className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-card text-app-text"
                          />
                        </div>
                        <div>
                          <label className="block text-[11px] font-semibold text-app-text-muted mb-1">End Date</label>
                          <input
                            type="text"
                            value={exp.end_date || ""}
                            onChange={(e) => updateExperienceItem(idx, "end_date", e.target.value)}
                            placeholder="e.g. Present"
                            className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-card text-app-text"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-[11px] font-semibold text-app-text-muted mb-1">
                          Responsibilities & Achievements (One per line)
                        </label>
                        <textarea
                          rows={3}
                          value={(exp.responsibilities || []).join("\n")}
                          onChange={(e) =>
                            updateExperienceItem(
                              idx,
                              "responsibilities",
                              e.target.value.split("\n").filter(Boolean)
                            )
                          }
                          className="w-full text-xs p-2.5 rounded-lg border border-app-border bg-app-card text-app-text leading-relaxed"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 5. EDUCATION TAB */}
            {activeReviewTab === "education" && (
              <div className="space-y-4">
                <div className="border-b border-app-border pb-2 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-app-text uppercase tracking-wider">
                    Education & Degrees ({(extractedData.education || []).length})
                  </h3>
                  <Button size="sm" variant="outline" onClick={addEducationItem} className="text-xs">
                    <Plus size={13} className="mr-1" /> Add Education
                  </Button>
                </div>

                <div className="space-y-4">
                  {(extractedData.education || []).map((edu, idx) => (
                    <div key={idx} className="p-4 rounded-xl border border-app-border bg-app-surface space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-blue-600">Education #{idx + 1}</span>
                        <button
                          type="button"
                          onClick={() => removeEducationItem(idx)}
                          className="text-app-text-muted hover:text-rose-500 text-xs flex items-center gap-1"
                        >
                          <Trash2 size={12} /> Remove
                        </button>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                          <label className="block text-[11px] font-semibold text-app-text-muted mb-1">Degree / Qualification</label>
                          <input
                            type="text"
                            value={edu.degree || ""}
                            onChange={(e) => updateEducationItem(idx, "degree", e.target.value)}
                            className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-card text-app-text font-semibold"
                          />
                        </div>
                        <div>
                          <label className="block text-[11px] font-semibold text-app-text-muted mb-1">Institution / University</label>
                          <input
                            type="text"
                            value={edu.institution || ""}
                            onChange={(e) => updateEducationItem(idx, "institution", e.target.value)}
                            className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-card text-app-text font-semibold"
                          />
                        </div>
                        <div>
                          <label className="block text-[11px] font-semibold text-app-text-muted mb-1">Graduation Year / Dates</label>
                          <input
                            type="text"
                            value={edu.graduation_year || edu.end_date || ""}
                            onChange={(e) => updateEducationItem(idx, "graduation_year", e.target.value)}
                            placeholder="e.g. 2024"
                            className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-card text-app-text"
                          />
                        </div>
                        <div>
                          <label className="block text-[11px] font-semibold text-app-text-muted mb-1">GPA / Grade / Percentage</label>
                          <input
                            type="text"
                            value={edu.grade || ""}
                            onChange={(e) => updateEducationItem(idx, "grade", e.target.value)}
                            placeholder="e.g. 3.9 / 4.0 or 88%"
                            className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-card text-app-text"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 6. PROJECTS TAB */}
            {activeReviewTab === "projects" && (
              <div className="space-y-4">
                <div className="border-b border-app-border pb-2 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-app-text uppercase tracking-wider">
                    Key Projects ({(extractedData.projects || []).length})
                  </h3>
                  <Button size="sm" variant="outline" onClick={addProjectItem} className="text-xs">
                    <Plus size={13} className="mr-1" /> Add Project
                  </Button>
                </div>

                <div className="space-y-4">
                  {(extractedData.projects || []).map((proj, idx) => (
                    <div key={idx} className="p-4 rounded-xl border border-app-border bg-app-surface space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-blue-600">Project #{idx + 1}</span>
                        <button
                          type="button"
                          onClick={() => removeProjectItem(idx)}
                          className="text-app-text-muted hover:text-rose-500 text-xs flex items-center gap-1"
                        >
                          <Trash2 size={12} /> Remove
                        </button>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                          <label className="block text-[11px] font-semibold text-app-text-muted mb-1">Project Name</label>
                          <input
                            type="text"
                            value={proj.name || ""}
                            onChange={(e) => updateProjectItem(idx, "name", e.target.value)}
                            className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-card text-app-text font-semibold"
                          />
                        </div>
                        <div>
                          <label className="block text-[11px] font-semibold text-app-text-muted mb-1">Tech Stack</label>
                          <input
                            type="text"
                            value={Array.isArray(proj.technologies) ? proj.technologies.join(", ") : (proj.technologies || "")}
                            onChange={(e) => updateProjectItem(idx, "technologies", e.target.value.split(",").map((s) => s.trim()))}
                            placeholder="e.g. Next.js, Python, PostgreSQL"
                            className="w-full text-xs px-3 py-1.5 rounded-lg border border-app-border bg-app-card text-app-text"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="block text-[11px] font-semibold text-app-text-muted mb-1">
                          Bullets & Highlights (One per line)
                        </label>
                        <textarea
                          rows={2}
                          value={(proj.responsibilities || []).join("\n")}
                          onChange={(e) =>
                            updateProjectItem(idx, "responsibilities", e.target.value.split("\n").filter(Boolean))
                          }
                          className="w-full text-xs p-2.5 rounded-lg border border-app-border bg-app-card text-app-text leading-relaxed"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 7. CERTIFICATIONS TAB */}
            {activeReviewTab === "certifications" && (
              <div className="space-y-4">
                <div className="border-b border-app-border pb-2 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-app-text uppercase tracking-wider">
                    Certifications & Professional Courses ({(extractedData.certifications || []).length})
                  </h3>
                  <Button size="sm" variant="outline" onClick={addCertItem} className="text-xs">
                    <Plus size={13} className="mr-1" /> Add Certification
                  </Button>
                </div>

                <div className="space-y-2.5">
                  {(extractedData.certifications || []).map((cert, idx) => (
                    <div key={idx} className="p-3 rounded-xl border border-app-border bg-app-surface flex items-center justify-between gap-3">
                      <div className="flex-1">
                        <span className="text-xs font-semibold text-app-text">
                          {typeof cert === "string" ? cert : cert.name || "Certification"}
                        </span>
                        {typeof cert === "object" && cert.issuing_organization && (
                          <span className="text-[11px] text-app-text-muted block">
                            Issuer: {cert.issuing_organization} {cert.issue_date ? `• ${cert.issue_date}` : ""}
                          </span>
                        )}
                      </div>
                      <button
                        type="button"
                        onClick={() => removeCertItem(idx)}
                        className="text-app-text-muted hover:text-rose-500 text-xs"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 8. ACHIEVEMENTS & LANGUAGES TAB */}
            {activeReviewTab === "achievements" && (
              <div className="space-y-4">
                <div className="border-b border-app-border pb-2">
                  <h3 className="text-sm font-bold text-app-text uppercase tracking-wider">
                    Honors, Languages & Additional Extracted Details
                  </h3>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-app-text mb-1.5">
                    Awards, Honors & Hackathons
                  </label>
                  <textarea
                    rows={3}
                    value={(extractedData.achievements || []).join("\n")}
                    onChange={(e) =>
                      setExtractedData((prev) => ({
                        ...prev,
                        achievements: e.target.value.split("\n").filter(Boolean),
                      }))
                    }
                    placeholder="One award per line..."
                    className="w-full text-xs p-3 rounded-xl border border-app-border bg-app-surface text-app-text"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-app-text mb-1.5">
                    Languages Spoken
                  </label>
                  <input
                    type="text"
                    value={(extractedData.languages || []).map((l) => (typeof l === "string" ? l : `${l.language} (${l.proficiency || "Fluent"})`)).join(", ")}
                    onChange={(e) => {
                      const tokens = e.target.value.split(",").map((s) => s.trim()).filter(Boolean);
                      setExtractedData((prev) => ({
                        ...prev,
                        languages: tokens.map((t) => ({ language: t, proficiency: "Fluent" })),
                      }));
                    }}
                    placeholder="e.g. English (Native), Spanish (Fluent), German"
                    className="w-full text-xs px-3.5 py-2 rounded-xl border border-app-border bg-app-surface text-app-text"
                  />
                </div>
              </div>
            )}

            {/* 9. CUSTOM SECTIONS TAB */}
            {activeReviewTab === "custom" && (
              <div className="space-y-4">
                <div className="border-b border-app-border pb-2">
                  <h3 className="text-sm font-bold text-app-text uppercase tracking-wider">
                    Custom & Uncategorized Sections ({(extractedData.custom_sections || []).length})
                  </h3>
                  <p className="text-[11px] text-app-text-muted">
                    Sections from your resume that did not fit standard headings are preserved here and will never be discarded.
                  </p>
                </div>

                {(extractedData.custom_sections || []).length === 0 ? (
                  <p className="text-xs text-app-text-muted italic">No custom sections found.</p>
                ) : (
                  <div className="space-y-3">
                    {(extractedData.custom_sections || []).map((sec, idx) => (
                      <div key={idx} className="p-4 rounded-xl border border-app-border bg-app-surface space-y-2">
                        <span className="text-xs font-bold text-app-text">{sec.section_title}</span>
                        <pre className="text-[11px] text-app-text-muted whitespace-pre-wrap font-sans bg-app-card p-3 rounded-lg border border-app-border">
                          {sec.original_content}
                        </pre>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* 10. RAW TEXT TAB */}
            {activeReviewTab === "raw" && (
              <div className="space-y-3">
                <div className="border-b border-app-border pb-2 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-app-text uppercase tracking-wider flex items-center gap-2">
                    <Terminal size={14} /> Full Raw Extracted Document Text
                  </h3>
                  <span className="text-[11px] text-app-text-muted">Preserved for auditability</span>
                </div>
                <div className="max-h-96 overflow-y-auto rounded-xl bg-slate-900 text-slate-200 p-4 font-mono text-[11px] leading-relaxed border border-slate-800">
                  <pre>{rawText || "No raw text available"}</pre>
                </div>
              </div>
            )}
          </Card>

          {/* Sticky Bottom Actions */}
          <div className="flex items-center justify-between p-4 bg-app-card rounded-2xl border border-app-border shadow-sm">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleSaveAndVerify(false)}
              disabled={isSaving}
              className="text-xs"
            >
              Save Corrections Only
            </Button>

            <div className="flex items-center gap-3">
              <Button
                size="sm"
                disabled={isSaving}
                onClick={() => handleSaveAndVerify(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-6 py-2 shadow-sm"
              >
                <Check size={14} className="mr-1.5" />
                {isSaving ? "Saving..." : "Mark Verified & Open in Overleaf Editor"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ResumeUploadPage() {
  return (
    <Suspense fallback={<div className="p-10 text-center text-xs">Loading Resume Extraction Engine...</div>}>
      <ResumeUploadContent />
    </Suspense>
  );
}
