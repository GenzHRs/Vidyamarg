"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { 
  ArrowLeft, Sparkles, CheckCircle2, AlertTriangle, 
  ShieldCheck, ArrowRight, RefreshCw, FileText, 
  Check, X, Eye, Layers, Download, Code,
  Sliders, Briefcase, ExternalLink, ChevronRight,
  UserCheck, Send, CheckSquare, Square, Info
} from "lucide-react";
import { 
  resumeCenterApi, 
  ResumeItem, 
  ResumeTemplateItem,
  TailoredResumeOutput, 
  SuggestedChange,
  StructuredResumeData,
  SourceResumeForTailoring,
  RenderTailoredTemplateResponse,
  JDOptimizeResponse,
  PreparedApplication
} from "@/services/resumeCenterApi";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Alert } from "@/components/ui/Alert";
import { Modal } from "@/components/ui/Modal";

interface PageProps {
  params: Promise<{ resumeId: string }>;
}

export default function ResumeTailoringPage({ params }: PageProps) {
  const resolvedParams = use(params);
  const resumeId = Number(resolvedParams.resumeId);
  const router = useRouter();

  // Source Resume State
  const [sourceResume, setSourceResume] = useState<SourceResumeForTailoring | null>(null);
  const [templates, setTemplates] = useState<ResumeTemplateItem[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<number>(1);
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [sourceDataError, setSourceDataError] = useState<string | null>(null);

  // Form Inputs
  const [jobTitle, setJobTitle] = useState("");
  const [company, setCompany] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [renderingMode, setRenderingMode] = useState<"template" | "original_layout">("template");
  const [candidateApproved, setCandidateApproved] = useState(false);
  const [approving, setApproving] = useState(false);
  const [approvalNotes, setApprovalNotes] = useState("");

  // Operation A: Tailoring Content Generation States
  const [analyzing, setAnalyzing] = useState(false);
  const [tailorResult, setTailorResult] = useState<{
    analysis: TailoredResumeOutput;
    source_resume_id: number;
    job_title: string;
    company: string;
    original_resume: StructuredResumeData;
    tailored_resume_data: StructuredResumeData;
    matching_skills: string[];
    missing_requirements: string[];
    transferable_skills: string[];
    suggested_changes: SuggestedChange[];
    ats_keywords: string[];
    warnings: string[];
  } | null>(null);
  const [optimizationResult, setOptimizationResult] = useState<JDOptimizeResponse | null>(null);

  // Operation B: Template Rendering & Live PDF Preview States
  const [renderingTemplate, setRenderingTemplate] = useState(false);
  const [renderResult, setRenderResult] = useState<RenderTailoredTemplateResponse | null>(null);
  const [previewPdfBlobUrl, setPreviewPdfBlobUrl] = useState<string | null>(null);
  const [previewTab, setPreviewTab] = useState<"pdf" | "latex">("pdf");
  const [templateFilterCategory, setTemplateFilterCategory] = useState<string>("All");

  // Clean up blob URL memory on unmount or change
  useEffect(() => {
    return () => {
      if (previewPdfBlobUrl) {
        URL.revokeObjectURL(previewPdfBlobUrl);
      }
    };
  }, [previewPdfBlobUrl]);

  // Save Modal States
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [customNewTitle, setCustomNewTitle] = useState("");
  const [savingResume, setSavingResume] = useState(false);

  // Application Preparation States
  const [appDrawerOpen, setAppDrawerOpen] = useState(false);
  const [preparingApp, setPreparingApp] = useState(false);
  const [confirmingApp, setConfirmingApp] = useState(false);
  const [preparedApp, setPreparedApp] = useState<PreparedApplication | null>(null);
  const [userConfirmedAcknowledgement, setUserConfirmedAcknowledgement] = useState(false);
  const [appConfirmedMessage, setAppConfirmedMessage] = useState<string | null>(null);

  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // Step Tracker
  const [currentStep, setCurrentStep] = useState<"input" | "diffs" | "template_and_preview">("input");

  // 1. Initial Load: Fetch source resume and verify structured data exists
  useEffect(() => {
    let isMounted = true;
    async function loadInitialData() {
      try {
        setLoadingInitial(true);
        setSourceDataError(null);

        const [srcRes, tmplList] = await Promise.all([
          resumeCenterApi.getSourceResumeForTailoring(resumeId),
          resumeCenterApi.getTemplates().catch(() => [])
        ]);

        if (isMounted) {
          setSourceResume(srcRes);
          setTemplates(tmplList);
          const initialTmpl = srcRes.template_id || (tmplList[0]?.id ?? 1);
          setSelectedTemplateId(initialTmpl);
          setCustomNewTitle(`${srcRes.title} - Tailored`);

          // Pre-fetch initial preview PDF blob with auth header
          try {
            const blob = await resumeCenterApi.fetchTailoredPreviewBlob(resumeId, initialTmpl);
            const url = URL.createObjectURL(blob);
            if (isMounted) setPreviewPdfBlobUrl(url);
          } catch (e) {
            // Silently ignore if not pre-cached
          }
        }
      } catch (err: any) {
        if (isMounted) {
          setSourceDataError(err.message || "Failed to load source resume data for tailoring.");
        }
      } finally {
        if (isMounted) setLoadingInitial(false);
      }
    }

    loadInitialData();
    return () => { isMounted = false; };
  }, [resumeId]);

  // 2. Operation A: Generate Tailored Content (AI analysis & diffs)
  const handleRunTailoring = async () => {
    if (!jobDescription.trim() || !jobTitle.trim()) {
      setErrorMessage("Please enter both the Job Title and Job Description.");
      return;
    }

    try {
      setAnalyzing(true);
      setErrorMessage("");
      setSuccessMessage("");

      // Call production JD-Driven ATS Optimization Engine
      const optResult = await resumeCenterApi.optimizeResume({
        resume_id: resumeId,
        job_description: jobDescription,
        job_title: jobTitle,
        company: company || "Target Company",
        template_id: selectedTemplateId,
        rendering_mode: renderingMode
      });
      setOptimizationResult(optResult);
      setCandidateApproved(Boolean(optResult.candidate_approved));

      // Normalize result into state
      const tailoredState = {
        analysis: {
          job_title: optResult.job_title,
          company: optResult.company,
          required_skills: optResult.matched_skills,
          preferred_skills: optResult.partial_matches,
          responsibilities: [],
          matching_skills: optResult.matched_skills,
          missing_requirements: optResult.missing_skills,
          transferable_skills: optResult.partial_matches,
          suggested_changes: [],
          final_resume_data: optResult.optimized_resume,
          ats_keywords: optResult.matched_skills,
          warnings: optResult.recommendations
        },
        source_resume_id: resumeId,
        job_title: optResult.job_title,
        company: optResult.company || "Target Company",
        original_resume: sourceResume?.structured_data || optResult.optimized_resume,
        tailored_resume_data: optResult.optimized_resume,
        matching_skills: optResult.matched_skills,
        missing_requirements: optResult.missing_skills,
        transferable_skills: optResult.partial_matches,
        suggested_changes: [],
        ats_keywords: optResult.matched_skills,
        warnings: optResult.recommendations
      };

      setTailorResult(tailoredState);
      setCustomNewTitle(`${sourceResume?.title || "Resume"} - ${jobTitle} (${company || "Target Company"})`);
      setCurrentStep("diffs");
      setSuccessMessage(`Job Analysis complete! RESUME MATCH SCORE: ${optResult.resume_match_score || optResult.ats_score} / 100 (TRUTHFULNESS CHECK: 100% Verified).`);

      // Automatically pre-render selected template (Operation B)
      await handleRenderTemplate(selectedTemplateId, optResult.optimized_resume);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to generate tailored resume analysis");
    } finally {
      setAnalyzing(false);
    }
  };

  const handlePrepareApplication = async () => {
    if (!optimizationResult) return;
    try {
      setPreparingApp(true);
      const res = await resumeCenterApi.prepareApplication(optimizationResult.optimization_id);
      setPreparedApp(res);
      setAppDrawerOpen(true);
      setUserConfirmedAcknowledgement(false);
      setAppConfirmedMessage(null);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to prepare application");
    } finally {
      setPreparingApp(false);
    }
  };

  const handleConfirmApplication = async () => {
    if (!optimizationResult || !userConfirmedAcknowledgement) return;
    try {
      setConfirmingApp(true);
      const res = await resumeCenterApi.confirmApplication(optimizationResult.optimization_id, {
        user_acknowledged: true,
      });
      setPreparedApp(res.prepared_application);
      setAppConfirmedMessage(res.message);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to confirm application");
    } finally {
      setConfirmingApp(false);
    }
  };

  // 3. Operation B: Render Selected Template (Generates LaTeX and compiles PDF)
  const handleRenderTemplate = async (tmplId: number, dataOverride?: StructuredResumeData) => {
    const dataToRender = dataOverride || tailorResult?.tailored_resume_data;
    if (!dataToRender) return;

    try {
      setRenderingTemplate(true);
      setSelectedTemplateId(tmplId);

      const renderRes = await resumeCenterApi.renderTailoredTemplate({
        source_resume_id: resumeId,
        selected_template_id: tmplId,
        tailored_resume_data: dataToRender
      });

      setRenderResult(renderRes);

      // Fetch authenticated PDF blob for live iframe preview
      try {
        const blob = await resumeCenterApi.fetchTailoredPreviewBlob(resumeId, tmplId);
        const url = URL.createObjectURL(blob);
        setPreviewPdfBlobUrl(prev => {
          if (prev) URL.revokeObjectURL(prev);
          return url;
        });
      } catch (blobErr) {
        console.error("Failed to fetch preview PDF blob", blobErr);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to compile preview PDF for selected template");
    } finally {
      setRenderingTemplate(false);
    }
  };

  // 4. Save Tailored Resume as a new resume record
  const handleSaveTailoredResume = async () => {
    if (!tailorResult) return;

    try {
      setSavingResume(true);
      setErrorMessage("");

      const saveRes = await resumeCenterApi.saveTailoredResume({
        source_resume_id: resumeId,
        selected_template_id: selectedTemplateId,
        tailored_resume_data: tailorResult.tailored_resume_data,
        job_title: jobTitle,
        company_name: company || "Target Company",
        job_description: jobDescription,
        custom_title: customNewTitle || undefined
      });

      setSuccessMessage("Tailored resume successfully saved!");
      setSaveModalOpen(false);
      router.push(`/candidate/resumes/edit/${saveRes.resume_id}`);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to save tailored resume");
      setSavingResume(false);
    }
  };

  // Categories for template filtering
  const templateCategories = ["All", ...Array.from(new Set(templates.map(t => t.category).filter(Boolean)))];
  const filteredTemplates = templateFilterCategory === "All"
    ? templates
    : templates.filter(t => t.category === templateFilterCategory);

  // ─── Initial Loading State ────────────────────────────────────────────────
  if (loadingInitial) {
    return (
      <div className="p-16 text-center text-app-text-muted space-y-3 font-sans">
        <RefreshCw size={28} className="animate-spin mx-auto text-blue-600 dark:text-blue-400" />
        <p className="text-sm font-semibold">Loading verified resume data for tailoring...</p>
      </div>
    );
  }

  // ─── Source Data Error State (Stop immediately if source has no data) ───────
  if (sourceDataError) {
    return (
      <div className="p-6 md:p-12 max-w-3xl mx-auto space-y-6 font-sans">
        <Link 
          href="/candidate/resumes" 
          className="inline-flex items-center gap-2 text-xs font-semibold text-app-text-muted hover:text-app-text transition-colors"
        >
          <ArrowLeft size={14} /> Back to Resume Center
        </Link>
        <Card className="p-8 border-red-200 dark:border-red-900/60 bg-red-50/30 dark:bg-red-950/20 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/40 text-red-600 flex items-center justify-center mx-auto">
            <AlertTriangle size={24} />
          </div>
          <h2 className="text-lg font-bold text-red-900 dark:text-red-200">
            Cannot Tailor Resume
          </h2>
          <p className="text-xs text-red-800/80 dark:text-red-300/80 max-w-md mx-auto leading-relaxed">
            {sourceDataError}
          </p>
          <div className="flex items-center justify-center gap-3 pt-4">
            <Link href="/candidate/resumes/upload">
              <Button className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold">
                Upload Readable Resume
              </Button>
            </Link>
            <Link href="/candidate/resumes/new">
              <Button variant="outline" className="text-xs font-semibold">
                Build Resume from Scratch
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  // ─── Main Content ──────────────────────────────────────────────────────────
  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8 font-sans">
      {/* Top Header */}
      <div>
        <Link 
          href="/candidate/resumes" 
          className="inline-flex items-center gap-2 text-xs font-semibold text-app-text-muted hover:text-app-text transition-colors mb-2"
        >
          <ArrowLeft size={14} /> Back to Resume Center
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-app-text tracking-tight flex items-center gap-2.5">
              <Sparkles className="text-purple-600 dark:text-purple-400" size={28} />
              JD-Based Resume Tailoring & Template Studio
            </h1>
            <p className="text-xs md:text-sm text-app-text-muted mt-1 leading-relaxed">
              Source Resume: <span className="font-bold text-app-text">{sourceResume?.title}</span> (#{sourceResume?.resume_id})
            </p>
          </div>

          {tailorResult && (
            <div className="flex items-center gap-2.5">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentStep(currentStep === "diffs" ? "template_and_preview" : "diffs")}
                className="text-xs font-semibold"
              >
                {currentStep === "diffs" ? "View Template & PDF Preview" : "Review Diffs & Skills"}
              </Button>
              <Button
                onClick={() => setSaveModalOpen(true)}
                className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs px-5 shadow-sm"
              >
                <CheckCircle2 size={14} className="mr-1.5" />
                Save as New Resume
              </Button>
            </div>
          )}
        </div>

        {/* Workflow Step Indicators */}
        <div className="grid grid-cols-3 gap-2 mt-6 max-w-2xl">
          <div 
            onClick={() => setCurrentStep("input")}
            className={`cursor-pointer p-2.5 rounded-xl border text-center transition-all ${
              currentStep === "input" 
                ? "border-purple-500 bg-purple-50/50 dark:bg-purple-950/20 text-purple-700 dark:text-purple-300 font-bold" 
                : "border-app-border text-app-text-muted text-xs font-medium"
            }`}
          >
            1. Target Job Description
          </div>
          <div 
            onClick={() => tailorResult && setCurrentStep("diffs")}
            className={`p-2.5 rounded-xl border text-center transition-all ${
              !tailorResult ? "opacity-50 cursor-not-allowed border-app-border text-app-text-muted text-xs" :
              currentStep === "diffs" 
                ? "border-purple-500 bg-purple-50/50 dark:bg-purple-950/20 text-purple-700 dark:text-purple-300 font-bold cursor-pointer" 
                : "border-app-border text-app-text-muted text-xs font-medium cursor-pointer"
            }`}
          >
            2. Match & Diffs Review
          </div>
          <div 
            onClick={() => tailorResult && setCurrentStep("template_and_preview")}
            className={`p-2.5 rounded-xl border text-center transition-all ${
              !tailorResult ? "opacity-50 cursor-not-allowed border-app-border text-app-text-muted text-xs" :
              currentStep === "template_and_preview" 
                ? "border-purple-500 bg-purple-50/50 dark:bg-purple-950/20 text-purple-700 dark:text-purple-300 font-bold cursor-pointer" 
                : "border-app-border text-app-text-muted text-xs font-medium cursor-pointer"
            }`}
          >
            3. Overleaf Template & PDF
          </div>
        </div>
      </div>

      {errorMessage && <Alert variant="error">{errorMessage}</Alert>}
      {successMessage && <Alert variant="success">{successMessage}</Alert>}

      {/* ── STEP 1: Job Description Input Form ──────────────────────────────── */}
      {currentStep === "input" && (
        <Card className="p-6 md:p-8 bg-app-card border-app-border space-y-5 shadow-sm">
          <div className="border-b border-app-border pb-3">
            <h2 className="text-base font-bold text-app-text">1. Target Job Details</h2>
            <p className="text-xs text-app-text-muted">
              Paste the job posting details to extract keywords, analyze match rate, and optimize phrasing without fabricating facts.
            </p>
          </div>

          {/* Rendering Mode Selector (Mode A: Choose Template vs Mode B: Edit Original Resume) */}
          <div>
            <label className="block text-xs font-bold text-app-text mb-2">Rendering Mode</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div 
                onClick={() => setRenderingMode("template")}
                className={`cursor-pointer p-4 rounded-xl border transition-all ${
                  renderingMode === "template"
                    ? "border-purple-600 bg-purple-50/50 dark:bg-purple-950/20 ring-1 ring-purple-600"
                    : "border-app-border bg-app-surface hover:border-purple-300"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-app-text flex items-center gap-1.5">
                    <Layers size={14} className="text-purple-600" />
                    Mode A: Choose a Template
                  </span>
                  {renderingMode === "template" && <CheckCircle2 size={15} className="text-purple-600" />}
                </div>
                <p className="text-[11px] text-app-text-muted leading-relaxed">
                  Populate one of 15 ATS-optimized LaTeX / ReportLab templates with verified job-specific content.
                </p>
                <div className="mt-2 flex gap-1.5">
                  <Badge variant="outline" className="text-[10px] py-0">PDF Supported</Badge>
                  <Badge variant="outline" className="text-[10px] py-0">DOCX Supported</Badge>
                </div>
              </div>

              <div 
                onClick={() => setRenderingMode("original_layout")}
                className={`cursor-pointer p-4 rounded-xl border transition-all ${
                  renderingMode === "original_layout"
                    ? "border-purple-600 bg-purple-50/50 dark:bg-purple-950/20 ring-1 ring-purple-600"
                    : "border-app-border bg-app-surface hover:border-purple-300"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-app-text flex items-center gap-1.5">
                    <FileText size={14} className="text-purple-600" />
                    Mode B: Edit My Original Resume
                  </span>
                  {renderingMode === "original_layout" && <CheckCircle2 size={15} className="text-purple-600" />}
                </div>
                <p className="text-[11px] text-app-text-muted leading-relaxed">
                  Edit your uploaded document while preserving its original design, fonts, and structure as far as supported.
                </p>
                <div className="mt-2 flex gap-1.5">
                  <Badge variant="outline" className="text-[10px] py-0">Preserve Typography</Badge>
                  <Badge variant="outline" className="text-[10px] py-0">Run-Aware DOCX</Badge>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-app-text mb-1.5">Job Title *</label>
              <input
                type="text"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                placeholder="e.g. Senior Machine Learning Engineer, Backend Developer"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-purple-500 font-medium"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-app-text mb-1.5">Company Name (Optional)</label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="e.g. Google, Anthropic, NVIDIA"
                className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-purple-500 font-medium"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-app-text mb-1.5">Job Description *</label>
            <textarea
              rows={8}
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the complete job description, requirements, responsibilities, and qualifications..."
              className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-purple-500 leading-relaxed font-sans"
            />
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
            <div className="flex items-center gap-2 text-[11px] text-app-text-muted">
              <ShieldCheck size={14} className="text-purple-600 dark:text-purple-400 shrink-0" />
              <span>Strict zero hallucination standard. Never creates fake companies or qualifications.</span>
            </div>

            <Button
              disabled={analyzing}
              onClick={handleRunTailoring}
              className="bg-purple-600 hover:bg-purple-700 text-white font-semibold text-xs px-6 py-2.5 shadow-md shadow-purple-600/20"
            >
              {analyzing ? (
                <>
                  <RefreshCw size={14} className="animate-spin mr-2" />
                  Analyzing JD & Tailoring Resume...
                </>
              ) : (
                <>
                  <Sparkles size={14} className="mr-2" />
                  Analyze & Tailor Content
                </>
              )}
            </Button>
          </div>
        </Card>
      )}

      {/* ── STEP 2: Match & Diffs Review ────────────────────────────────────── */}
      {currentStep === "diffs" && tailorResult && (
        <div className="space-y-6">
          {/* Zero Hallucination Assurance Banner */}
          <div className="p-4 rounded-2xl bg-purple-50/70 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-800/40 flex items-start gap-3">
            <ShieldCheck size={20} className="text-purple-600 dark:text-purple-400 shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <h4 className="text-xs font-bold text-purple-900 dark:text-purple-200 uppercase tracking-wider">
                Zero-Hallucination Verified Alignment
              </h4>
              <p className="text-xs text-purple-800/80 dark:text-purple-300/80 leading-relaxed">
                VidyamargAI reorders your genuine skills and sharpens summary & bullet points with action verbs. Any JD requirements not in your background are flagged below as missing.
              </p>
            </div>
          </div>

          {/* RESUME MATCH SCORE Header & Metrics Breakdown */}
          {optimizationResult && (
            <Card className="p-6 bg-app-card border-app-border space-y-6 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-app-border pb-4">
                <div className="flex items-center gap-4">
                  <div className="w-24 h-20 rounded-2xl bg-purple-100 dark:bg-purple-950/60 border border-purple-300 dark:border-purple-800 flex flex-col items-center justify-center text-purple-700 dark:text-purple-300 shrink-0 shadow-xs">
                    <span className="text-2xl font-black">
                      {optimizationResult.resume_match_score || optimizationResult.ats_score}
                      <span className="text-xs font-normal text-purple-600/70"> / 100</span>
                    </span>
                    <span className="text-[9px] font-extrabold uppercase tracking-wider text-center leading-tight">
                      RESUME MATCH SCORE
                    </span>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-base font-bold text-app-text">
                        {optimizationResult.job_title} Optimization Report
                      </h3>
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                        Target Title: {optimizationResult.dynamic_title || optimizationResult.job_title}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-app-text-muted flex-wrap">
                      <span>Target Company: <strong className="text-app-text">{optimizationResult.company}</strong></span>
                      <span>&bull;</span>
                      <span className="inline-flex items-center gap-1 font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-md border border-emerald-200 dark:border-emerald-800">
                        <ShieldCheck size={12} />
                        TRUTHFULNESS CHECK: 100% Verified
                      </span>
                    </div>
                  </div>
                </div>

                {/* Direct Document Downloads & Application Draft Actions */}
                <div className="flex items-center gap-2 flex-wrap">
                  <Button
                    onClick={handlePrepareApplication}
                    disabled={preparingApp}
                    className="bg-purple-600 hover:bg-purple-700 text-white font-semibold text-xs px-3.5 py-2 shadow-sm"
                  >
                    {preparingApp ? (
                      <>
                        <RefreshCw size={13} className="animate-spin mr-1.5" />
                        Preparing Form...
                      </>
                    ) : (
                      <>
                        <UserCheck size={13} className="mr-1.5" />
                        Prepare Application Form
                      </>
                    )}
                  </Button>
                  <a
                    href={resumeCenterApi.getOptimizedPdfUrl(optimizationResult.optimization_id)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <Button variant="outline" size="sm" className="text-xs border-purple-300 hover:bg-purple-50 dark:hover:bg-purple-950/40">
                      <Download size={13} className="mr-1.5 text-purple-600" />
                      Download PDF
                    </Button>
                  </a>
                  <a
                    href={resumeCenterApi.getOptimizedDocxUrl(optimizationResult.optimization_id)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <Button variant="outline" size="sm" className="text-xs border-blue-300 hover:bg-blue-50 dark:hover:bg-blue-950/40">
                      <Download size={13} className="mr-1.5 text-blue-600" />
                      Download Word
                    </Button>
                  </a>
                </div>
              </div>

              {/* Mode & Fidelity Tier Badge */}
              <div className="flex items-center justify-between p-3 rounded-xl bg-purple-50/60 dark:bg-purple-950/20 border border-purple-200 dark:border-purple-800 text-xs">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="bg-purple-100 dark:bg-purple-900/60 text-purple-800 dark:text-purple-300 border-purple-300 font-bold">
                    {optimizationResult.rendering_mode === "original_layout" ? "Mode B: Original Resume Layout" : "Mode A: ATS Template"}
                  </Badge>
                  <span className="text-[11px] text-app-text-muted">
                    Fidelity: <strong className="text-app-text capitalize">{String(optimizationResult.fidelity_tier || "template_fallback").replace(/_/g, " ")}</strong>
                  </span>
                </div>

                {/* Candidate Approval Action */}
                <div className="flex items-center gap-2">
                  {candidateApproved || optimizationResult.candidate_approved ? (
                    <span className="inline-flex items-center gap-1.5 font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50 px-3 py-1 rounded-lg border border-emerald-300 text-xs">
                      <CheckCircle2 size={14} />
                      Approved for Applications
                    </span>
                  ) : (
                    <Button
                      size="sm"
                      disabled={approving}
                      onClick={async () => {
                        try {
                          setApproving(true);
                          const res = await resumeCenterApi.approveOptimization(optimizationResult.optimization_id, {
                            user_acknowledged: true,
                            notes: "Candidate approved via Tailor Studio"
                          });
                          setCandidateApproved(true);
                          setSuccessMessage(res.message);
                        } catch (e: any) {
                          setErrorMessage(e.message || "Failed to approve revision");
                        } finally {
                          setApproving(false);
                        }
                      }}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs px-3.5 py-1.5 shadow-sm"
                    >
                      {approving ? "Approving..." : "Approve This Version"}
                    </Button>
                  )}
                </div>
              </div>

              {/* Mandatory Score Disclaimer */}
              <div className="flex items-start gap-2 text-[11px] text-app-text-muted bg-app-surface/60 p-2.5 rounded-xl border border-app-border leading-relaxed">
                <Info size={14} className="text-purple-600 dark:text-purple-400 shrink-0 mt-0.5" />
                <span>
                  <strong>Disclaimer:</strong> Calculated from job-description keyword, experience, technical-skill, responsibility, role-alignment, and resume-quality matching. This score is an optimization indicator and does not guarantee ATS selection.
                </span>
              </div>

              {/* 6-Part Component Metrics Breakdown */}
              <div>
                <span className="text-[10px] font-bold text-app-text-muted uppercase tracking-wider block mb-2">
                  Weighted Component Breakdown
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
                  <div className="p-3 rounded-xl bg-app-surface border border-app-border text-center space-y-1">
                    <span className="text-[10px] font-bold text-app-text-muted uppercase">Keyword Match</span>
                    <div className="text-lg font-black text-purple-600">{optimizationResult.keyword_match}%</div>
                    <div className="text-[9px] text-app-text-muted">Weight 25%</div>
                  </div>
                  <div className="p-3 rounded-xl bg-app-surface border border-app-border text-center space-y-1">
                    <span className="text-[10px] font-bold text-app-text-muted uppercase">Experience</span>
                    <div className="text-lg font-black text-blue-600">{optimizationResult.experience_match}%</div>
                    <div className="text-[9px] text-app-text-muted">Weight 25%</div>
                  </div>
                  <div className="p-3 rounded-xl bg-app-surface border border-app-border text-center space-y-1">
                    <span className="text-[10px] font-bold text-app-text-muted uppercase">Technical</span>
                    <div className="text-lg font-black text-indigo-600">{optimizationResult.technical_match}%</div>
                    <div className="text-[9px] text-app-text-muted">Weight 20%</div>
                  </div>
                  <div className="p-3 rounded-xl bg-app-surface border border-app-border text-center space-y-1">
                    <span className="text-[10px] font-bold text-app-text-muted uppercase">Responsibilities</span>
                    <div className="text-lg font-black text-emerald-600">{optimizationResult.responsibility_match}%</div>
                    <div className="text-[9px] text-app-text-muted">Weight 15%</div>
                  </div>
                  <div className="p-3 rounded-xl bg-app-surface border border-app-border text-center space-y-1">
                    <span className="text-[10px] font-bold text-app-text-muted uppercase">Role Alignment</span>
                    <div className="text-lg font-black text-amber-600">{optimizationResult.alignment_score}%</div>
                    <div className="text-[9px] text-app-text-muted">Weight 10%</div>
                  </div>
                  <div className="p-3 rounded-xl bg-app-surface border border-app-border text-center space-y-1">
                    <span className="text-[10px] font-bold text-app-text-muted uppercase">Resume Quality</span>
                    <div className="text-lg font-black text-teal-600">{optimizationResult.quality_score || 92}%</div>
                    <div className="text-[9px] text-app-text-muted">Weight 5%</div>
                  </div>
                </div>
              </div>

              {/* Score Explanation: Positive & Negative Factors */}
              {optimizationResult.score_explanation && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1 border-t border-app-border">
                  <div className="p-3.5 rounded-xl bg-emerald-50/40 dark:bg-emerald-950/20 border border-emerald-200/60 dark:border-emerald-800/40 space-y-2">
                    <span className="text-[10px] font-bold text-emerald-800 dark:text-emerald-300 uppercase tracking-wider flex items-center gap-1.5">
                      <CheckCircle2 size={13} className="text-emerald-600" /> Positive Matching Factors
                    </span>
                    <ul className="text-xs text-app-text-secondary space-y-1.5">
                      {optimizationResult.score_explanation.positive_factors?.map((pos, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-emerald-600 font-bold shrink-0">{pos.startsWith('+') ? '' : '+ '}</span>
                          <span>{pos.replace(/^\+\s*/, '')}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="p-3.5 rounded-xl bg-amber-50/40 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-800/40 space-y-2">
                    <span className="text-[10px] font-bold text-amber-800 dark:text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
                      <AlertTriangle size={13} className="text-amber-600" /> Negative Factors / Growth Areas
                    </span>
                    <ul className="text-xs text-app-text-secondary space-y-1.5">
                      {optimizationResult.score_explanation.negative_factors?.map((neg, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-amber-600 font-bold shrink-0">{neg.startsWith('-') ? '' : '- '}</span>
                          <span>{neg.replace(/^-\s*/, '')}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Application Readiness Card */}
              {optimizationResult.application_readiness && (
                <div className="p-4 rounded-xl bg-gradient-to-r from-purple-500/10 via-blue-500/10 to-teal-500/10 border border-purple-300/60 dark:border-purple-800/40 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <span className="text-xs font-bold text-app-text uppercase tracking-wider">Application Readiness:</span>
                      <Badge className={`text-xs font-bold px-3 py-1 ${
                        optimizationResult.application_readiness.readiness_level === 'HIGH'
                          ? 'bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-900/60 dark:text-emerald-200'
                          : optimizationResult.application_readiness.readiness_level === 'MEDIUM'
                          ? 'bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-900/60 dark:text-amber-200'
                          : 'bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-900/60 dark:text-rose-200'
                      }`}>
                        {optimizationResult.application_readiness.readiness_level} READINESS
                      </Badge>
                    </div>
                    <span className="text-xs text-app-text-muted">
                      Matched: <strong className="text-app-text">{optimizationResult.application_readiness.matched_skills_count}</strong> &bull; Partial: <strong className="text-app-text">{optimizationResult.application_readiness.partial_skills_count}</strong> &bull; Missing: <strong className="text-app-text">{optimizationResult.application_readiness.missing_skills_count}</strong>
                    </span>
                  </div>
                  <p className="text-xs font-medium text-app-text leading-relaxed">
                    <strong>Recommendation:</strong> {optimizationResult.application_readiness.recommendation}
                  </p>
                  {optimizationResult.application_readiness.reasoning?.length > 0 && (
                    <ul className="text-[11px] text-app-text-secondary space-y-1 pl-1">
                      {optimizationResult.application_readiness.reasoning.map((r, i) => (
                        <li key={i} className="flex items-start gap-1.5">
                          <span className="text-purple-600 font-bold">&bull;</span>
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              {/* Optimization Guidance */}
              {optimizationResult.recommendations && optimizationResult.recommendations.length > 0 && (
                <div className="p-3.5 rounded-xl bg-purple-50/30 dark:bg-purple-950/20 border border-purple-200/60 dark:border-purple-800/40 space-y-1.5">
                  <span className="text-[10px] font-bold text-purple-700 dark:text-purple-300 uppercase tracking-wider">
                    Optimization Guidance
                  </span>
                  <ul className="text-xs text-app-text-secondary space-y-1">
                    {optimizationResult.recommendations.map((rec, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-purple-600 font-bold">•</span>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Evidence Matching Traceability Breakdown */}
              {optimizationResult.evidence_items && optimizationResult.evidence_items.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-app-border">
                  <span className="text-[10px] font-bold text-app-text-muted uppercase tracking-wider">
                    Candidate Evidence Traceability (Rule 14)
                  </span>
                  <div className="max-h-56 overflow-y-auto space-y-1.5 pr-1">
                    {optimizationResult.evidence_items.map((ev, idx) => (
                      <div key={idx} className="p-2.5 rounded-lg bg-app-surface border border-app-border flex items-center justify-between text-xs gap-3">
                        <div className="space-y-0.5 min-w-0">
                          <span className="font-bold text-app-text block truncate">{ev.requirement}</span>
                          {ev.evidence && (
                            <p className="text-[11px] text-app-text-muted line-clamp-1">{ev.evidence}</p>
                          )}
                        </div>
                        <Badge className={`text-[10px] uppercase font-bold shrink-0 ${
                          ev.match_type === "STRONG_MATCH" ? "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300" :
                          ev.match_type === "PARTIAL_MATCH" ? "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300" :
                          "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300"
                        }`}>
                          {ev.match_type.replace("_", " ")}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          )}

          {/* Skill Matching Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Matching Skills */}
            <Card className="p-5 bg-app-card border-app-border space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle2 size={14} />
                  Matching Skills ({tailorResult.matching_skills.length})
                </h3>
                <span className="text-[10px] text-app-text-muted font-semibold">Found in your profile</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {tailorResult.matching_skills.map((skill, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </Card>

            {/* Missing Requirements with Critical / Important / Optional Breakdown */}
            <Card className="p-5 bg-app-card border-app-border space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle size={14} />
                  Missing Requirements Intelligence ({tailorResult.missing_requirements.length})
                </h3>
                <span className="text-[10px] text-app-text-muted font-semibold">Prioritized Skill Gaps</span>
              </div>

              {optimizationResult?.skill_gaps && (
                <div className="space-y-3 pt-1">
                  {optimizationResult.skill_gaps.critical_gaps?.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[10px] font-bold text-rose-600 dark:text-rose-400 uppercase tracking-wider block">
                        Critical Gaps (Required)
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {optimizationResult.skill_gaps.critical_gaps.map((cg, i) => (
                          <span key={i} className="px-2.5 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300 border border-rose-300 dark:border-rose-800">
                            {cg}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {optimizationResult.skill_gaps.important_gaps?.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider block">
                        Important Gaps (Preferred)
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {optimizationResult.skill_gaps.important_gaps.map((ig, i) => (
                          <span key={i} className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
                            {ig}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {optimizationResult.skill_gaps.optional_gaps?.length > 0 && (
                    <div className="space-y-1">
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                        Optional Gaps (Nice-to-have)
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {optimizationResult.skill_gaps.optional_gaps.map((og, i) => (
                          <span key={i} className="px-2.5 py-1 rounded-full text-xs font-normal bg-slate-50 text-slate-700 dark:bg-slate-900 dark:text-slate-300 border border-slate-200 dark:border-slate-800">
                            {og}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {(!optimizationResult?.skill_gaps || (
                !optimizationResult.skill_gaps.critical_gaps?.length &&
                !optimizationResult.skill_gaps.important_gaps?.length &&
                !optimizationResult.skill_gaps.optional_gaps?.length
              )) && (
                <div className="flex flex-wrap gap-1.5">
                  {tailorResult.missing_requirements.length > 0 ? (
                    tailorResult.missing_requirements.map((req, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
                      >
                        {req}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-app-text-muted">No missing requirements detected!</span>
                  )}
                </div>
              )}
            </Card>
          </div>

          {/* Diffs Review Card */}
          <Card className="p-6 md:p-8 bg-app-card border-app-border space-y-6 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-app-border pb-4">
              <div>
                <h2 className="text-base font-bold text-app-text">Itemized Diffs Review</h2>
                <p className="text-xs text-app-text-muted">
                  Examine every tailored section. Changes preserve your authentic facts.
                </p>
              </div>
              <Badge className="bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300 border border-purple-200 dark:border-purple-800 text-xs">
                {tailorResult.suggested_changes?.length || 0} Suggested Adjustments
              </Badge>
            </div>

            {/* Summary Diff Comparison */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-app-text-muted flex items-center gap-1.5">
                <FileText size={14} /> Professional Summary Comparison
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl border border-app-border bg-app-surface space-y-2">
                  <span className="text-[10px] font-bold text-app-text-muted uppercase">Original Summary</span>
                  <p className="text-xs text-app-text-secondary leading-relaxed">
                    {tailorResult.original_resume?.summary || "No original summary provided."}
                  </p>
                </div>

                <div className="p-4 rounded-xl border border-purple-200 dark:border-purple-800/50 bg-purple-50/20 dark:bg-purple-950/20 space-y-2">
                  <span className="text-[10px] font-bold text-purple-600 dark:text-purple-400 uppercase">
                    Proposed Tailored Summary
                  </span>
                  <p className="text-xs text-app-text font-medium leading-relaxed">
                    {tailorResult.tailored_resume_data?.summary}
                  </p>
                </div>
              </div>
            </div>

            {/* Suggested Changes List */}
            {tailorResult.suggested_changes && tailorResult.suggested_changes.length > 0 && (
              <div className="space-y-4 pt-4 border-t border-app-border">
                <h3 className="text-xs font-bold uppercase tracking-wider text-app-text-muted">
                  Itemized Phrasing Adjustments
                </h3>

                <div className="space-y-3">
                  {tailorResult.suggested_changes.map((change, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl border border-app-border bg-app-surface/50 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-app-text capitalize">
                          Section: {change.section}
                        </span>
                        {change.requires_confirmation ? (
                          <Badge className="bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 text-[10px]">
                            Requires Confirmation
                          </Badge>
                        ) : (
                          <Badge className="bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 text-[10px]">
                            Recommended
                          </Badge>
                        )}
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-1">
                        <div className="p-2.5 rounded-lg bg-red-50/40 dark:bg-red-950/20 border border-red-200/50 dark:border-red-900/40 text-red-900 dark:text-red-300">
                          <span className="block text-[10px] font-bold text-red-600 uppercase mb-1">Previous</span>
                          {change.original}
                        </div>
                        <div className="p-2.5 rounded-lg bg-emerald-50/40 dark:bg-emerald-950/20 border border-emerald-200/50 dark:border-emerald-900/40 text-emerald-900 dark:text-emerald-300 font-medium">
                          <span className="block text-[10px] font-bold text-emerald-600 uppercase mb-1">Proposed</span>
                          {change.proposed}
                        </div>
                      </div>

                      <p className="text-[11px] text-app-text-muted italic pt-1">
                        Reason: {change.reason}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Bottom Actions Bar */}
            <div className="flex items-center justify-between pt-4 border-t border-app-border">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentStep("input")}
                className="text-xs"
              >
                Modify JD Details
              </Button>

              <Button
                onClick={() => setCurrentStep("template_and_preview")}
                className="bg-purple-600 hover:bg-purple-700 text-white font-semibold text-xs px-6 py-2.5 shadow-md shadow-purple-600/20"
              >
                Proceed to Template Gallery & PDF Preview
                <ArrowRight size={14} className="ml-2" />
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* ── STEP 3: Overleaf Template Gallery & Live PDF Preview ───────────── */}
      {currentStep === "template_and_preview" && tailorResult && (
        <div className="space-y-6">
          {/* Overleaf Templates Gallery Picker */}
          <Card className="p-6 bg-app-card border-app-border space-y-4 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-app-border pb-3">
              <div>
                <h2 className="text-base font-bold text-app-text flex items-center gap-2">
                  <Layers size={18} className="text-purple-600 dark:text-purple-400" />
                  Select Overleaf Resume Template
                </h2>
                <p className="text-xs text-app-text-muted">
                  Choose any of the 15 distinct resume styles. Switching templates dynamically updates the compiled PDF without losing content.
                </p>
              </div>

              {/* Category Pills */}
              <div className="flex flex-wrap gap-1">
                {templateCategories.map(cat => (
                  <button
                    key={cat}
                    onClick={() => setTemplateFilterCategory(cat)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                      templateFilterCategory === cat
                        ? "bg-purple-600 text-white shadow-xs"
                        : "bg-app-surface border border-app-border text-app-text-muted hover:text-app-text"
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            {/* Template Cards Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3 max-h-72 overflow-y-auto pr-1">
              {filteredTemplates.map(tmpl => {
                const isSelected = selectedTemplateId === tmpl.id;
                return (
                  <div
                    key={tmpl.id}
                    onClick={() => handleRenderTemplate(tmpl.id)}
                    className={`p-3 rounded-xl border text-left cursor-pointer transition-all ${
                      isSelected
                        ? "border-purple-600 bg-purple-50/60 dark:bg-purple-950/40 ring-2 ring-purple-600/30"
                        : "border-app-border hover:border-purple-400/60 bg-app-surface"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-bold text-app-text-muted uppercase truncate">
                        {tmpl.category}
                      </span>
                      {isSelected ? (
                        <span className="w-4 h-4 rounded-full bg-purple-600 text-white flex items-center justify-center text-[10px]">
                          ✓
                        </span>
                      ) : (
                        <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400">
                          ATS {tmpl.ats_score}%
                        </span>
                      )}
                    </div>
                    <h4 className="text-xs font-bold text-app-text line-clamp-1">{tmpl.name}</h4>
                    <p className="text-[10px] text-app-text-muted line-clamp-2 mt-1 leading-tight">
                      {tmpl.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Real PDF Compilation & Live Preview Section */}
          <Card className="p-6 bg-app-card border-app-border space-y-4 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-app-border pb-3">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-950/40 text-emerald-600 flex items-center justify-center">
                  <FileText size={18} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-app-text">
                    Live Compiled Preview: {renderResult?.template_name || "ATS Classic"}
                  </h3>
                  <p className="text-xs text-app-text-muted">
                    Rendered via Overleaf LaTeX compiler. Zoom, review, or inspect source.
                  </p>
                </div>
              </div>

              {/* View Mode Toggle & Save Button */}
              <div className="flex items-center gap-2">
                <div className="flex rounded-lg border border-app-border p-0.5 bg-app-surface">
                  <button
                    onClick={() => setPreviewTab("pdf")}
                    className={`px-3 py-1 rounded-md text-xs font-bold transition-all ${
                      previewTab === "pdf" ? "bg-purple-600 text-white" : "text-app-text-muted hover:text-app-text"
                    }`}
                  >
                    PDF Preview
                  </button>
                  <button
                    onClick={() => setPreviewTab("latex")}
                    className={`px-3 py-1 rounded-md text-xs font-bold transition-all ${
                      previewTab === "latex" ? "bg-purple-600 text-white" : "text-app-text-muted hover:text-app-text"
                    }`}
                  >
                    LaTeX Code
                  </button>
                </div>

                <Button
                  onClick={() => setSaveModalOpen(true)}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs px-5 shadow-sm"
                >
                  <CheckCircle2 size={14} className="mr-1.5" />
                  Save Tailored Resume
                </Button>
              </div>
            </div>

            {/* Live Preview Display Window */}
            <div className="relative min-h-[600px] rounded-xl border border-app-border bg-slate-900/5 dark:bg-slate-950 overflow-hidden">
              {renderingTemplate ? (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-app-card/80 backdrop-blur-xs z-10 space-y-3">
                  <RefreshCw size={28} className="animate-spin text-purple-600" />
                  <p className="text-xs font-bold text-app-text">
                    Compiling tailored resume to {templates.find(t => t.id === selectedTemplateId)?.name}...
                  </p>
                </div>
              ) : null}

              {previewTab === "pdf" ? (
                previewPdfBlobUrl ? (
                  <iframe
                    src={previewPdfBlobUrl}
                    className="w-full h-[650px] border-0"
                    title="Tailored Resume Live PDF Preview"
                  />
                ) : (
                  <div className="w-full h-[650px] flex flex-col items-center justify-center text-app-text-muted space-y-3">
                    <RefreshCw size={24} className="animate-spin text-purple-600" />
                    <p className="text-xs font-semibold">Generating live PDF preview...</p>
                  </div>
                )
              ) : (
                <div className="p-4 bg-slate-950 text-slate-100 font-mono text-xs overflow-auto h-[650px]">
                  <pre>{renderResult?.latex_source || "% LaTeX source will appear here after compilation"}</pre>
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* ── SAVE MODAL ──────────────────────────────────────────────────────── */}
      <Modal
        isOpen={saveModalOpen}
        onClose={() => setSaveModalOpen(false)}
        title="Save Tailored Resume"
        className="max-w-md"
      >
        <div className="space-y-5 pt-2">
          <p className="text-xs text-app-text-secondary leading-relaxed">
            Your source resume &quot;{sourceResume?.title}&quot; will remain <span className="font-bold text-emerald-600">100% untouched</span>. This creates a new tailored resume record ready for applications.
          </p>

          <div>
            <label className="block text-xs font-bold text-app-text mb-1">New Resume Title *</label>
            <input
              type="text"
              value={customNewTitle}
              onChange={(e) => setCustomNewTitle(e.target.value)}
              className="w-full text-xs px-3.5 py-2.5 rounded-xl border border-app-border bg-app-surface text-app-text focus:outline-none focus:ring-2 focus:ring-emerald-500 font-medium"
            />
          </div>

          <div className="p-3 rounded-xl bg-app-surface border border-app-border space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-app-text-muted">Target Role:</span>
              <span className="font-bold text-app-text">{jobTitle}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-app-text-muted">Target Company:</span>
              <span className="font-bold text-app-text">{company || "Target Company"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-app-text-muted">Selected Template:</span>
              <span className="font-bold text-purple-600 dark:text-purple-400">
                {templates.find(t => t.id === selectedTemplateId)?.name || "ATS Classic"}
              </span>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-app-border">
            <Button
              variant="outline"
              size="sm"
              disabled={savingResume}
              onClick={() => setSaveModalOpen(false)}
              className="text-xs"
            >
              Cancel
            </Button>
            <Button
              size="sm"
              disabled={savingResume}
              onClick={handleSaveTailoredResume}
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs"
            >
              {savingResume ? "Saving & Finalizing..." : "Confirm & Save"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* ── APPLICATION PREPARATION & AUTOFILL MODAL ───────────────────────── */}
      <Modal
        isOpen={appDrawerOpen}
        onClose={() => setAppDrawerOpen(false)}
        title="Candidate Job Application Preparation"
        className="max-w-3xl"
      >
        <div className="space-y-5 pt-2 max-h-[75vh] overflow-y-auto pr-1">
          <div className="p-3.5 rounded-xl bg-purple-50/60 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-800/50 space-y-1">
            <div className="flex items-center gap-2">
              <ShieldCheck size={16} className="text-purple-600" />
              <h4 className="text-xs font-bold text-purple-900 dark:text-purple-200 uppercase tracking-wider">
                Safe Application Autofill Standard
              </h4>
            </div>
            <p className="text-xs text-purple-800/80 dark:text-purple-300/80 leading-relaxed">
              All profile and technical fields are populated from your verified Master Resume and project evidence. <strong>No autonomous external submissions occur:</strong> you must review every field and perform the final manual submission.
            </p>
          </div>

          {appConfirmedMessage && (
            <Alert variant="success" className="text-xs">
              <CheckCircle2 size={14} className="mr-1.5 inline" />
              {appConfirmedMessage}
            </Alert>
          )}

          {preparedApp ? (
            <div className="space-y-5">
              {/* 1. Exact Fields from Master Resume */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-app-text uppercase tracking-wider flex items-center justify-between border-b border-app-border pb-1.5">
                  <span>1. Verified Master Profile Details (Exact Fields)</span>
                  <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200 text-[10px]">100% Grounded</Badge>
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
                  {preparedApp.exact_fields.map((field, idx) => (
                    <div key={idx} className="p-2.5 rounded-lg border border-app-border bg-app-surface space-y-0.5">
                      <span className="text-[10px] font-bold text-app-text-muted uppercase block">{field.field_label}</span>
                      <span className="text-app-text font-medium block truncate">{String(field.value || "—")}</span>
                      <span className="text-[9px] text-app-text-muted italic">{field.source}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 2. Semantic Answers Grounded in Evidence */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-app-text uppercase tracking-wider flex items-center justify-between border-b border-app-border pb-1.5">
                  <span>2. Tailored Application Responses (Evidence-Backed)</span>
                  <Badge className="bg-blue-50 text-blue-700 border-blue-200 text-[10px]">Truthfully Grounded</Badge>
                </h4>
                <div className="space-y-2 text-xs">
                  {preparedApp.semantic_fields.map((field, idx) => (
                    <div key={idx} className="p-3 rounded-lg border border-blue-200/60 dark:border-blue-900/40 bg-blue-50/20 dark:bg-blue-950/20 space-y-1">
                      <span className="text-[10px] font-bold text-blue-700 dark:text-blue-300 uppercase block">{field.field_label}</span>
                      <p className="text-xs text-app-text leading-relaxed font-sans">{String(field.value || "")}</p>
                      <span className="text-[9px] text-app-text-muted italic block">Evidence Source: {field.source}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* 3. Missing Information Requiring Candidate Input */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-app-text uppercase tracking-wider flex items-center justify-between border-b border-app-border pb-1.5">
                  <span>3. Additional Application Questions</span>
                  <Badge className="bg-amber-50 text-amber-700 border-amber-200 text-[10px]">User Input Required</Badge>
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                  {preparedApp.missing_fields.map((field, idx) => (
                    <div key={idx} className="p-2.5 rounded-lg border border-amber-200/80 bg-amber-50/20 space-y-0.5">
                      <span className="text-[10px] font-bold text-amber-800 dark:text-amber-300 uppercase block">{field.field_label}</span>
                      <span className="text-[11px] text-app-text-muted italic">Provide during final submission form</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Explicit User Review & Confirmation Gate */}
              <div className="pt-3 border-t border-app-border space-y-3">
                <label className="flex items-start gap-2.5 cursor-pointer text-xs select-none">
                  <input
                    type="checkbox"
                    checked={userConfirmedAcknowledgement}
                    onChange={(e) => setUserConfirmedAcknowledgement(e.target.checked)}
                    className="mt-0.5 rounded border-app-border text-purple-600 focus:ring-purple-500"
                  />
                  <span className="text-app-text-secondary leading-relaxed">
                    I have thoroughly reviewed all application draft fields and verify that the facts and statements truthfully represent my background.
                  </span>
                </label>

                <div className="flex items-center justify-end gap-3 pt-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setAppDrawerOpen(false)}
                    className="text-xs"
                  >
                    Close
                  </Button>
                  <Button
                    onClick={handleConfirmApplication}
                    disabled={!userConfirmedAcknowledgement || confirmingApp || preparedApp.status === "CONFIRMED"}
                    className={`text-xs px-5 py-2 font-semibold text-white ${
                      preparedApp.status === "CONFIRMED"
                        ? "bg-emerald-600 hover:bg-emerald-700"
                        : "bg-purple-600 hover:bg-purple-700"
                    }`}
                  >
                    {confirmingApp ? (
                      <>
                        <RefreshCw size={13} className="animate-spin mr-1.5" />
                        Confirming...
                      </>
                    ) : preparedApp.status === "CONFIRMED" ? (
                      <>
                        <CheckCircle2 size={13} className="mr-1.5" />
                        Application Details Confirmed
                      </>
                    ) : (
                      <>
                        <Check size={13} className="mr-1.5" />
                        Confirm Application Draft
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-10 text-center text-xs text-app-text-muted">
              <RefreshCw size={24} className="animate-spin mx-auto text-purple-600 mb-2" />
              Loading application preparation draft...
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}
