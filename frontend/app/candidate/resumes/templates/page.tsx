"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { 
  Layers, ArrowLeft, ArrowRight, CheckCircle2, ShieldCheck, 
  Sparkles, Eye, Download, Code, Award, Check, ExternalLink, 
  RefreshCw, Search, Copy, CheckCheck, FileText, SlidersHorizontal
} from "lucide-react";
import { 
  resumeCenterApi, 
  ResumeTemplateItem, 
  ResumeItem 
} from "@/services/resumeCenterApi";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { Alert } from "@/components/ui/Alert";

// Helper map for layout architecture badges and target roles
const TEMPLATE_META: Record<string, { layout: string; roles: string }> = {
  "classic-ats": {
    layout: "Single Column ATS",
    roles: "Finance, Enterprise, Corporate, Banking",
  },
  "modern-corporate": {
    layout: "Modern Corporate Single",
    roles: "Managers, Consultants, Analysts",
  },
  "executive-resume": {
    layout: "Executive Header & Achievements",
    roles: "Directors, VPs, CTOs, Tech Leads",
  },
  "modern-two-column": {
    layout: "Two-Column Split (Deedy Style)",
    roles: "Software Engineers, System Architects",
  },
  "color-sidebar": {
    layout: "Left Sidebar & Right Stream",
    roles: "Designers, Product, Full-Stack",
  },
  "minimalist-elegant": {
    layout: "Minimalist High-Whitespace",
    roles: "Consultants, Strategists, Creatives",
  },
  "bold-creative": {
    layout: "Bold Typography & Accents",
    roles: "Designers, Creative Directors, Media",
  },
  "software-engineer": {
    layout: "Jake's LaTeX / Standard SE",
    roles: "Backend, Frontend, Full Stack, DevOps",
  },
  "ai-ml-engineer": {
    layout: "AI/ML Models & Research Stack",
    roles: "ML Engineers, AI Researchers, Data Science",
  },
  "data-scientist": {
    layout: "Data & Quantitative Metrics",
    roles: "Data Analysts, Quant, Data Engineers",
  },
  "developer-portfolio": {
    layout: "Project & Repository Showcase",
    roles: "Open Source Developers, Full Stack",
  },
  "graduate-fresher": {
    layout: "Education & Projects First",
    roles: "College Students, New Grads, Interns",
  },
  "academic-cv": {
    layout: "Academic & Publications (Oxford/Harvard)",
    roles: "Postdocs, PhDs, Professors, Researchers",
  },
  "timeline-resume": {
    layout: "Chronological Timeline Layout",
    roles: "Experienced Engineers, Specialists",
  },
  "infographic-resume": {
    layout: "Visual Infographic & Skill Metrics",
    roles: "UX/UI, Digital Marketers, Designers",
  },
};

export default function ResumeTemplateGalleryPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<ResumeTemplateItem[]>([]);
  const [userResumes, setUserResumes] = useState<ResumeItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Search & Filter & Sort state
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [sortBy, setSortBy] = useState<"ats" | "name" | "category">("ats");

  // Modals state
  const [activeTemplate, setActiveTemplate] = useState<ResumeTemplateItem | null>(null);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [applyModalOpen, setApplyModalOpen] = useState(false);
  const [templateToApply, setTemplateToApply] = useState<ResumeTemplateItem | null>(null);
  const [applyingResumeId, setApplyingResumeId] = useState<number | null>(null);

  // Copy LaTeX code feedback
  const [copiedTex, setCopiedTex] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      resumeCenterApi.getTemplates(),
      resumeCenterApi.getResumes().catch(() => []),
    ])
      .then(([tplData, resumesData]) => {
        setTemplates(tplData);
        setUserResumes(resumesData);
      })
      .catch((err) => console.error("Error loading templates:", err))
      .finally(() => setLoading(false));
  }, []);

  const categories = useMemo(() => {
    const cats = Array.from(new Set(templates.map((t) => t.category)));
    return ["all", ...cats];
  }, [templates]);

  const filteredTemplates = useMemo(() => {
    return templates
      .filter((t) => {
        const matchesCategory =
          selectedCategory === "all" ||
          t.category.toLowerCase() === selectedCategory.toLowerCase();

        const meta = TEMPLATE_META[t.slug] || { layout: "", roles: "" };
        const q = searchQuery.toLowerCase().trim();
        const matchesSearch =
          !q ||
          t.name.toLowerCase().includes(q) ||
          t.description.toLowerCase().includes(q) ||
          t.category.toLowerCase().includes(q) ||
          meta.layout.toLowerCase().includes(q) ||
          meta.roles.toLowerCase().includes(q);

        return matchesCategory && matchesSearch;
      })
      .sort((a, b) => {
        if (sortBy === "ats") return b.ats_score - a.ats_score;
        if (sortBy === "name") return a.name.localeCompare(b.name);
        return a.category.localeCompare(b.category);
      });
  }, [templates, selectedCategory, searchQuery, sortBy]);

  // Open Preview Modal with full LaTeX code fetched if needed
  const openPreview = async (tpl: ResumeTemplateItem) => {
    setActiveTemplate(tpl);
    setPreviewModalOpen(true);
    setCopiedTex(false);

    // If template does not have full latex_template loaded, fetch full item
    if (!tpl.latex_template) {
      try {
        const full = await resumeCenterApi.getTemplate(tpl.id);
        setActiveTemplate(full);
      } catch (e) {
        // Fallback to existing
      }
    }
  };

  const handleUseTemplate = (templateId: number) => {
    router.push(`/candidate/resumes/new?templateId=${templateId}`);
  };

  const openApplyModal = (tpl: ResumeTemplateItem) => {
    setTemplateToApply(tpl);
    setApplyModalOpen(true);
  };

  const handleApplyToResume = async (resumeId: number) => {
    if (!templateToApply) return;
    try {
      setApplyingResumeId(resumeId);
      await resumeCenterApi.updateResume(resumeId, {
        template_id: templateToApply.id,
      });
      setToastMessage(`Switched resume template to ${templateToApply.name}!`);
      setTimeout(() => {
        router.push(`/candidate/resumes/edit/${resumeId}`);
      }, 700);
    } catch (err: any) {
      console.error("Failed to switch template:", err);
      setToastMessage(err.message || "Failed to switch template");
    } finally {
      setApplyingResumeId(null);
      setApplyModalOpen(false);
    }
  };

  const handleCopyLatex = () => {
    if (!activeTemplate?.latex_template) return;
    navigator.clipboard.writeText(activeTemplate.latex_template);
    setCopiedTex(true);
    setTimeout(() => setCopiedTex(false), 2500);
  };

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-8 font-sans">
      {/* Toast Alert */}
      {toastMessage && (
        <Alert variant="info" className="animate-in fade-in slide-in-from-top-2">
          {toastMessage}
        </Alert>
      )}

      {/* Header & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Link 
            href="/candidate/resumes" 
            className="inline-flex items-center gap-2 text-xs font-semibold text-app-text-muted hover:text-app-text transition-colors mb-2"
          >
            <ArrowLeft size={14} /> Back to Resume Center
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl md:text-3xl font-extrabold text-app-text tracking-tight flex items-center gap-2.5">
              <Layers className="text-blue-600 dark:text-blue-400" size={28} />
              Overleaf LaTeX Template Gallery
            </h1>
            <Badge className="bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 border border-blue-200 dark:border-blue-800 text-xs font-bold">
              15 Verified Templates
            </Badge>
          </div>
          <p className="text-xs md:text-sm text-app-text-muted mt-1 leading-relaxed max-w-3xl">
            15 genuinely distinct, Overleaf-inspired LaTeX architectures covering Classic ATS, Modern Corporate, Deedy Two-Column, Color Sidebar, Minimalist, Jake's Resume, AI/ML, Data Science, Academic CV, and Timelines.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <Link href="/candidate/resumes/new">
            <Button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs py-2.5 shadow-sm">
              Start Blank Resume
              <ArrowRight size={14} className="ml-1.5" />
            </Button>
          </Link>
        </div>
      </div>

      {/* Search & Sort Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-app-card p-4 rounded-2xl border border-app-border">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-app-text-muted" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search templates by role, layout (e.g. 'Software', 'Two-column', 'Academic', 'ATS')..."
            className="w-full pl-10 pr-4 py-2 rounded-xl text-xs border border-app-border bg-app-surface text-app-text placeholder:text-app-text-muted focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium"
          />
        </div>

        {/* Sort Selector */}
        <div className="flex items-center gap-2 shrink-0">
          <SlidersHorizontal size={14} className="text-app-text-muted" />
          <span className="text-xs font-semibold text-app-text-muted">Sort:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-1.5 text-xs rounded-xl border border-app-border bg-app-surface text-app-text font-semibold focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ats">Highest ATS Score</option>
            <option value="name">Template Name (A - Z)</option>
            <option value="category">Category</option>
          </select>
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex flex-wrap items-center gap-2 border-b border-app-border pb-4">
        {categories.map((cat) => {
          const count = cat === "all" 
            ? templates.length 
            : templates.filter((t) => t.category.toLowerCase() === cat.toLowerCase()).length;
          const isActive = selectedCategory.toLowerCase() === cat.toLowerCase();

          return (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all capitalize flex items-center gap-1.5 ${
                isActive
                  ? "bg-blue-600 text-white shadow-sm"
                  : "bg-app-card border border-app-border text-app-text-muted hover:text-app-text hover:bg-app-surface"
              }`}
            >
              <span>{cat === "all" ? "All Designs" : cat}</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                isActive ? "bg-white/20 text-white" : "bg-app-surface text-app-text-muted border border-app-border"
              }`}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Templates Grid */}
      {loading ? (
        <div className="p-16 text-center text-app-text-muted space-y-3">
          <RefreshCw size={28} className="animate-spin mx-auto text-blue-600" />
          <p className="text-xs font-semibold">Loading Overleaf LaTeX templates...</p>
        </div>
      ) : filteredTemplates.length === 0 ? (
        <div className="p-16 text-center text-app-text-muted space-y-3 bg-app-card rounded-2xl border border-app-border">
          <Search size={32} className="mx-auto text-app-text-muted opacity-40" />
          <p className="text-sm font-semibold text-app-text">No templates matching your query</p>
          <p className="text-xs text-app-text-muted">Try a different search keyword or category filter.</p>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => { setSearchQuery(""); setSelectedCategory("all"); }}
            className="text-xs mt-2"
          >
            Reset Filters
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTemplates.map((template) => {
            const meta = TEMPLATE_META[template.slug] || {
              layout: template.category,
              roles: "Professionals & Developers",
            };

            const atsScore = template.ats_score;
            const atsBadgeColor = atsScore >= 98 
              ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800" 
              : atsScore >= 95 
              ? "bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 border-blue-200 dark:border-blue-800"
              : "bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800";

            return (
              <Card
                key={template.id}
                className="flex flex-col justify-between p-5 bg-app-card border-app-border hover:border-blue-500/50 hover:shadow-xl transition-all duration-200 group"
              >
                <div className="space-y-3.5">
                  {/* Real Resume Preview Graphic */}
                  <div className="h-64 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-app-border flex items-center justify-center relative overflow-hidden group-hover:border-blue-500/60 group-hover:shadow-md transition-all p-1 cursor-pointer"
                    onClick={() => openPreview(template)}
                  >
                    {template.preview_image ? (
                      <img 
                        src={template.preview_image} 
                        alt={template.name}
                        className="w-full h-full object-cover object-top rounded-lg shadow-sm border border-slate-200/60 dark:border-slate-800 transition-transform duration-300 group-hover:scale-[1.02]" 
                      />
                    ) : (
                      <div className="space-y-2 opacity-75 p-4 w-full">
                        <div className="h-3.5 bg-blue-600/30 rounded w-1/2 mx-auto" />
                        <div className="h-2 bg-slate-400/30 rounded w-3/4 mx-auto" />
                      </div>
                    )}

                    {/* Quick View Overlay on hover */}
                    <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center backdrop-blur-[2px]">
                      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white text-slate-900 text-xs font-bold shadow-lg">
                        <Eye size={13} /> Quick Preview
                      </span>
                    </div>

                    {/* Floating Layout & ATS badges */}
                    <div className="absolute bottom-2 left-2 right-2 bg-slate-900/85 backdrop-blur-md px-2.5 py-1 rounded-lg flex items-center justify-between text-[10px] font-mono font-semibold text-slate-200 border border-slate-700/60 shadow">
                      <span className="truncate max-w-[170px]">{meta.layout}</span>
                      <span className="text-emerald-400 font-bold shrink-0">{template.ats_score}% ATS</span>
                    </div>
                  </div>

                  {/* Template Meta Info */}
                  <div className="space-y-1.5">
                    <div className="flex items-start justify-between gap-2">
                      <h3 
                        onClick={() => openPreview(template)}
                        className="text-base font-bold text-app-text group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors cursor-pointer"
                      >
                        {template.name}
                      </h3>
                      <Badge className={`text-[10px] shrink-0 font-bold border ${atsBadgeColor}`}>
                        {template.ats_score}% ATS
                      </Badge>
                    </div>

                    <div className="flex items-center gap-2">
                      <Badge className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[10px] font-medium">
                        {template.category}
                      </Badge>
                      <span className="text-[10px] text-app-text-muted font-medium truncate">
                        Target: {meta.roles}
                      </span>
                    </div>

                    <p className="text-xs text-app-text-muted leading-relaxed line-clamp-2 pt-0.5">
                      {template.description}
                    </p>
                  </div>
                </div>

                {/* Card Footer Actions */}
                <div className="pt-4 mt-3 border-t border-app-border flex items-center justify-between gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openPreview(template)}
                    className="text-xs flex-1"
                  >
                    <Eye size={13} className="mr-1.5" />
                    Preview
                  </Button>

                  {userResumes.length > 0 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openApplyModal(template)}
                      className="text-xs px-2.5"
                      title="Apply this template to an existing resume"
                    >
                      Apply
                    </Button>
                  )}

                  <Button
                    size="sm"
                    onClick={() => handleUseTemplate(template.id)}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs flex-1"
                  >
                    Use Template
                    <ArrowRight size={13} className="ml-1.5" />
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Preview Modal with full LaTeX code and details */}
      <Modal
        isOpen={previewModalOpen}
        onClose={() => setPreviewModalOpen(false)}
        title={activeTemplate?.name || "Template Preview"}
        className="max-w-4xl"
      >
        {activeTemplate && (
          <div className="space-y-5 pt-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 border border-blue-200 dark:border-blue-800 text-xs">
                Category: {activeTemplate.category}
              </Badge>
              <Badge className="bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 text-xs">
                ATS Score: {activeTemplate.ats_score}%
              </Badge>
              <Badge className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs">
                License: {activeTemplate.license_name}
              </Badge>
              <Badge className="bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300 border border-purple-200 dark:border-purple-800 text-xs">
                Layout: {TEMPLATE_META[activeTemplate.slug]?.layout || "Distinct LaTeX"}
              </Badge>
            </div>

            <p className="text-xs text-app-text-secondary leading-relaxed">
              {activeTemplate.description}
            </p>

            {/* High-res Graphic Preview */}
            {activeTemplate.preview_image && (
              <div className="flex justify-center p-4 bg-slate-100 dark:bg-slate-900/90 rounded-2xl border border-app-border overflow-hidden">
                <img 
                  src={activeTemplate.preview_image} 
                  alt={activeTemplate.name}
                  className="max-h-[520px] w-auto object-contain rounded-lg shadow-xl border border-slate-200 dark:border-slate-800"
                />
              </div>
            )}

            {/* LaTeX Structure Preview Box with Copy action */}
            {activeTemplate.latex_template && (
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-app-text-muted flex items-center gap-1.5">
                    <Code size={12} /> Overleaf / LaTeX Source Template
                  </span>
                  <button
                    onClick={handleCopyLatex}
                    className="inline-flex items-center gap-1 text-[11px] font-medium text-blue-600 hover:text-blue-500 transition-colors"
                  >
                    {copiedTex ? (
                      <>
                        <CheckCheck size={12} className="text-emerald-500" />
                        <span className="text-emerald-600 font-semibold">Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy size={12} />
                        <span>Copy LaTeX Code</span>
                      </>
                    )}
                  </button>
                </div>
                <div className="max-h-48 overflow-y-auto rounded-xl bg-slate-900 text-slate-200 p-4 font-mono text-[11px] leading-relaxed border border-slate-800">
                  <pre>{activeTemplate.latex_template.substring(0, 1200)}...</pre>
                </div>
              </div>
            )}

            {/* Modal Footer Controls */}
            <div className="flex flex-wrap items-center justify-end gap-3 pt-3 border-t border-app-border">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPreviewModalOpen(false)}
                className="text-xs"
              >
                Close
              </Button>

              {userResumes.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setPreviewModalOpen(false);
                    openApplyModal(activeTemplate);
                  }}
                  className="text-xs"
                >
                  Apply to Existing Resume
                </Button>
              )}

              <Button
                size="sm"
                onClick={() => {
                  setPreviewModalOpen(false);
                  handleUseTemplate(activeTemplate.id);
                }}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs"
              >
                Create Resume with this Template
                <ArrowRight size={14} className="ml-1.5" />
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Modal: Apply Template to Existing Resume */}
      <Modal
        isOpen={applyModalOpen}
        onClose={() => setApplyModalOpen(false)}
        title={`Apply "${templateToApply?.name}" to an Existing Resume`}
        className="max-w-xl"
      >
        <div className="space-y-4 pt-2">
          <p className="text-xs text-app-text-muted leading-relaxed">
            Select one of your existing resumes below. Its layout will immediately switch to <span className="font-semibold text-app-text">{templateToApply?.name}</span> while preserving all of your work experience, education, skills, and projects.
          </p>

          <div className="max-h-64 overflow-y-auto space-y-2.5 pr-1">
            {userResumes.map((res) => (
              <div
                key={res.id}
                className="p-3 rounded-xl border border-app-border bg-app-surface hover:border-blue-500/60 hover:bg-app-card transition-all flex items-center justify-between gap-3"
              >
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-app-text truncate">{res.title}</span>
                    <span className="text-[10px] font-mono bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 px-1.5 py-0.2 rounded border border-blue-200 dark:border-blue-800">
                      v{res.version_number}
                    </span>
                  </div>
                  <p className="text-[11px] text-app-text-muted truncate">
                    Current Template: {res.template_name || "ATS Classic"}
                  </p>
                </div>

                <Button
                  size="sm"
                  disabled={applyingResumeId === res.id}
                  onClick={() => handleApplyToResume(res.id)}
                  className="bg-blue-600 hover:bg-blue-700 text-white text-xs shrink-0 font-medium py-1.5"
                >
                  {applyingResumeId === res.id ? (
                    <RefreshCw size={12} className="animate-spin" />
                  ) : (
                    "Switch & Open"
                  )}
                </Button>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-app-border">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setApplyModalOpen(false)}
              className="text-xs"
            >
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
