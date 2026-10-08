"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { 
  ArrowLeft, Sparkles, CheckCircle2, AlertTriangle, 
  ShieldCheck, ArrowRight, RefreshCw, FileText, 
  Check, X, Eye, Layers, Download, Code,
  Sliders, Briefcase, ExternalLink, ChevronRight
} from "lucide-react";
import { 
  resumeCenterApi, 
  ResumeItem, 
  ResumeTemplateItem,
  TailoredResumeOutput, 
  SuggestedChange,
  StructuredResumeData,
  SourceResumeForTailoring,
  RenderTailoredTemplateResponse
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

      const result = await resumeCenterApi.generateTailoredResume({
        resume_id: resumeId,
        job_title: jobTitle,
        company: company || "Target Company",
        job_description: jobDescription,
        template_id: selectedTemplateId
      });

      // Normalize result into state
      const tailoredState = {
        analysis: result.analysis,
        source_resume_id: resumeId,
        job_title: jobTitle,
        company: company || "Target Company",
        original_resume: result.original_resume,
        tailored_resume_data: (result as any).tailored_resume_data || result.proposed_resume,
        matching_skills: (result as any).matching_skills || result.analysis.matching_skills || [],
        missing_requirements: (result as any).missing_requirements || result.analysis.missing_requirements || [],
        transferable_skills: (result as any).transferable_skills || result.analysis.transferable_skills || [],
        suggested_changes: result.suggested_changes || [],
        ats_keywords: (result as any).ats_keywords || result.analysis.ats_keywords || [],
        warnings: result.warnings || []
      };

      setTailorResult(tailoredState);
      setCustomNewTitle(`${sourceResume?.title || "Resume"} - ${jobTitle} (${company || "Target Company"})`);
      setCurrentStep("diffs");
      setSuccessMessage("Content tailored! Review matching skills and proposed diffs, then select your template.");

      // Automatically pre-render selected template (Operation B)
      await handleRenderTemplate(selectedTemplateId, tailoredState.tailored_resume_data);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to generate tailored resume analysis");
    } finally {
      setAnalyzing(false);
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

            {/* Missing Requirements */}
            <Card className="p-5 bg-app-card border-app-border space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle size={14} />
                  Missing JD Requirements ({tailorResult.missing_requirements.length})
                </h3>
                <span className="text-[10px] text-app-text-muted font-semibold">Not found in profile</span>
              </div>
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
    </div>
  );
}
