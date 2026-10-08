"use client";

import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { apiService } from "@/services/api";
import { useResumeStore } from "@/store/resumeStore";
import {
  Briefcase,
  Search,
  Filter,
  MapPin,
  Clock,
  Star,
  Bookmark,
  BookmarkCheck,
  ExternalLink,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  Zap,
  RefreshCw,
  FileText,
  ChevronRight,
  Building2,
  SlidersHorizontal,
  X,
} from "lucide-react";

interface Job {
  id: number | string;
  title: string;
  company: string;
  location?: string;
  employment_type?: string;
  salary?: string;
  description?: string;
  required_skills?: string[];
  match_score?: number;
  match_explanation?: string;
  matched_skills?: string[];
  missing_skills?: string[];
  application_url?: string;
  posted_date?: string;
  source?: string;
}

function isValidUrl(url?: string): boolean {
  if (!url) return false;
  const trimmed = url.trim().toLowerCase();
  if (
    trimmed === "" ||
    trimmed === "#" ||
    trimmed.startsWith("javascript:") ||
    trimmed.includes("fake-job") ||
    trimmed.includes("example-job") ||
    trimmed.includes("demo-job")
  ) {
    return false;
  }
  return true;
}

function MatchBadge({ score }: { score: number }) {
  const color =
    score >= 80
      ? "bg-emerald-100 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400"
      : score >= 60
      ? "bg-amber-100 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400"
      : "bg-slate-100 dark:bg-slate-800 text-slate-500";
  return (
    <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${color}`}>
      {Math.round(score)}% match
    </span>
  );
}

function JobCard({
  job,
  saved,
  onSave,
  hasResume,
}: {
  job: Job;
  saved: boolean;
  onSave: (id: string | number) => void;
  hasResume: boolean | null;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className="bg-app-surface border border-app-border rounded-2xl p-5 hover:border-blue-200 dark:hover:border-blue-800/60 transition-all group"
      data-agent-resource="job"
      data-job-id={job.id}
    >
      <div className="flex items-start justify-between gap-3">
        {/* Company logo placeholder */}
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-950/40 dark:to-indigo-950/40 flex items-center justify-center shrink-0 border border-app-border">
          <Building2 size={17} className="text-blue-500 dark:text-blue-400" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <h3 className="text-sm font-bold text-app-text">{job.title}</h3>
            {hasResume && job.match_score !== undefined && job.match_score !== null && job.match_score > 0 && (
              <MatchBadge score={job.match_score} />
            )}
          </div>
          <p className="text-xs text-app-text-muted font-medium">{job.company}</p>

          <div className="flex flex-wrap items-center gap-3 mt-2 text-[11px] text-app-text-muted">
            {job.location && (
              <span className="flex items-center gap-1">
                <MapPin size={10} /> {job.location}
              </span>
            )}
            {job.employment_type && (
              <span className="flex items-center gap-1">
                <Clock size={10} /> {job.employment_type}
              </span>
            )}
            {job.salary && (
              <span className="flex items-center gap-1">
                <TrendingUp size={10} /> {job.salary}
              </span>
            )}
          </div>
        </div>

        <button
          onClick={() => onSave(job.id)}
          className="p-2 rounded-lg hover:bg-app-bg transition-colors shrink-0"
          title={saved ? "Unsave" : "Save job"}
        >
          {saved ? (
            <BookmarkCheck size={16} className="text-blue-500" />
          ) : (
            <Bookmark size={16} className="text-app-text-muted group-hover:text-blue-500 transition-colors" />
          )}
        </button>
      </div>

      {/* Skill match breakdown */}
      {(job.matched_skills?.length || job.missing_skills?.length) ? (
        <div className="mt-3 pt-3 border-t border-app-border space-y-2">
          {job.matched_skills && job.matched_skills.length > 0 && (
            <div className="flex flex-wrap gap-1.5 items-center">
              <CheckCircle size={11} className="text-emerald-500 shrink-0" />
              {job.matched_skills.slice(0, 4).map((s) => (
                <span
                  key={s}
                  className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400"
                >
                  {s}
                </span>
              ))}
            </div>
          )}
          {job.missing_skills && job.missing_skills.length > 0 && (
            <div className="flex flex-wrap gap-1.5 items-center">
              <AlertCircle size={11} className="text-amber-500 shrink-0" />
              {job.missing_skills.slice(0, 3).map((s) => (
                <span
                  key={s}
                  className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 dark:bg-amber-950/30 text-amber-700 dark:text-amber-400"
                >
                  {s}
                </span>
              ))}
            </div>
          )}
        </div>
      ) : null}

      {/* Match explanation */}
      {job.match_explanation && expanded && (
        <div className="mt-3 pt-3 border-t border-app-border">
          <p className="text-xs text-app-text-muted leading-relaxed">{job.match_explanation}</p>
        </div>
      )}

      {/* Actions */}
      <div className="mt-4 flex flex-wrap items-center gap-2">
        {isValidUrl(job.application_url) && (
          <a
            href={job.application_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-bold hover:bg-blue-700 transition-colors"
          >
            Apply Now <ExternalLink size={11} />
          </a>
        )}
        <Link
          href={`/candidate/resumes?optimize=true&role=${encodeURIComponent(job.title)}`}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-app-border text-xs font-semibold hover:bg-app-bg transition-colors"
        >
          <FileText size={11} /> Optimize Resume
        </Link>
        <Link
          href={`/candidate/interview?role=${encodeURIComponent(job.title)}`}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-app-border text-xs font-semibold hover:bg-app-bg transition-colors"
        >
          <Zap size={11} /> Practice Interview
        </Link>
        {job.match_explanation && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="text-xs font-semibold text-app-text-muted hover:text-app-text transition-colors ml-auto"
          >
            {expanded ? "Less" : "Why this match?"}
          </button>
        )}
      </div>
    </div>
  );
}

export default function JobsPage() {
  const searchParams = useSearchParams();
  const roleParam = searchParams.get("role") || "";
  const { activeResume, primaryDesignation, targetRoles, fetchActiveResume } = useResumeStore();

  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasResume, setHasResume] = useState<boolean | null>(null);

  const [search, setSearch] = useState(roleParam);
  const [locationFilter, setLocationFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("All");
  const [savedJobs, setSavedJobs] = useState<Set<string | number>>(new Set());
  const [activeTab, setActiveTab] = useState<"recommended" | "all" | "saved">("recommended");

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resumes = await apiService.getResumes().catch(() => []);
      setHasResume(Array.isArray(resumes) && resumes.length > 0);

      const res = await apiService.getRecommendedJobs();
      setJobs(Array.isArray(res) ? res : []);
    } catch (e: any) {
      setError("Unable to load jobs right now. Please try again.");
      setJobs([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
    fetchActiveResume();
  }, []);

  const handleSave = (id: string | number) => {
    setSavedJobs((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
    // TODO: persist to backend
  };

  const filteredJobs = jobs.filter((j) => {
    const matchesSearch =
      !search ||
      j.title.toLowerCase().includes(search.toLowerCase()) ||
      j.company.toLowerCase().includes(search.toLowerCase());
    const matchesLocation =
      !locationFilter ||
      (j.location || "").toLowerCase().includes(locationFilter.toLowerCase());
    const matchesType =
      typeFilter === "All" || j.employment_type === typeFilter;
    return matchesSearch && matchesLocation && matchesType;
  });

  const displayJobs =
    activeTab === "saved"
      ? filteredJobs.filter((j) => savedJobs.has(j.id))
      : filteredJobs;

  return (
    <div className="min-h-screen bg-app-bg text-app-text font-sans">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6">

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-app-text">Jobs</h1>
            <p className="text-sm text-app-text-muted mt-0.5">
              Personalized matches based on your active resume and generated target roles
            </p>
          </div>
          <button
            onClick={fetchJobs}
            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-app-border text-sm font-medium text-app-text-muted hover:text-app-text hover:bg-app-surface transition-colors self-start"
          >
            <RefreshCw size={14} />
            Refresh
          </button>
        </div>

        {/* Active Resume Context Indicator */}
        {activeResume ? (
          <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200/60 dark:border-blue-800/40 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3 shadow-xs">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-600/10 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
                <FileText size={16} />
              </div>
              <div>
                <p className="text-xs font-semibold text-blue-900 dark:text-blue-200">
                  Using your active resume: <span className="font-bold text-blue-600 dark:text-blue-400">{activeResume.title || activeResume.file_name}</span>
                </p>
                <p className="text-[11px] text-blue-700/80 dark:text-blue-300/70">
                  Primary Designation: <strong className="text-blue-900 dark:text-blue-200">{primaryDesignation || "Extracting..."}</strong>
                  {targetRoles && targetRoles.length > 0 && ` • Target Roles: ${targetRoles.slice(0, 3).join(", ")}`}
                </p>
              </div>
            </div>
            <span className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300">
              Single Active Context
            </span>
          </div>
        ) : hasResume === false && (
          <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-800/40 rounded-2xl p-4 flex items-center gap-3">
            <AlertCircle size={18} className="text-amber-500 shrink-0" />
            <p className="text-sm text-amber-700 dark:text-amber-400">
              Upload your resume to get personalized job matches with skill scores.{" "}
              <Link href="/candidate/resumes/upload" className="font-semibold underline">
                Upload Resume →
              </Link>
            </p>
          </div>
        )}

        {/* Search + Filters */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-app-text-muted" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by role or company…"
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-app-border bg-app-surface text-sm text-app-text placeholder:text-app-text-muted focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-all"
            />
          </div>
          <div className="relative">
            <MapPin size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-app-text-muted" />
            <input
              type="text"
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
              placeholder="Location…"
              className="w-full sm:w-40 pl-9 pr-3 py-2.5 rounded-xl border border-app-border bg-app-surface text-sm text-app-text placeholder:text-app-text-muted focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-all"
            />
          </div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-2.5 rounded-xl border border-app-border bg-app-surface text-sm text-app-text focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition-all"
          >
            {["All", "Full-time", "Part-time", "Remote", "Contract", "Internship"].map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-app-border gap-6">
          {(["recommended", "all", "saved"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-2.5 text-sm font-semibold border-b-2 transition-all capitalize ${
                activeTab === tab
                  ? "border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400"
                  : "border-transparent text-app-text-muted hover:text-app-text"
              }`}
            >
              {tab === "recommended" ? "Recommended For You" : tab === "all" ? "All Jobs" : `Saved (${savedJobs.size})`}
            </button>
          ))}
        </div>

        {/* Jobs List */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3">
            <div className="w-8 h-8 rounded-full border-4 border-t-blue-500 border-app-border animate-spin" />
            <p className="text-sm text-app-text-muted">Finding your best job matches…</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
            <AlertCircle size={32} className="text-red-400" />
            <p className="text-sm text-app-text-muted">{error}</p>
            <button
              onClick={fetchJobs}
              className="px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        ) : displayJobs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
            <Briefcase size={36} className="text-app-text-muted/30" />
            <p className="font-semibold text-app-text">
              {activeTab === "saved" ? "No saved jobs yet" : "No jobs found"}
            </p>
            <p className="text-sm text-app-text-muted max-w-sm">
              {activeTab === "saved"
                ? "Bookmark jobs to save them here."
                : hasResume
                ? "Try adjusting your search filters, or refresh to load new matches."
                : "Upload your resume to get AI-powered job recommendations."}
            </p>
            {!hasResume && (
              <Link
                href="/candidate/resumes/upload"
                className="mt-2 flex items-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition-colors"
              >
                <FileText size={14} /> Upload Resume
              </Link>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {displayJobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                saved={savedJobs.has(job.id)}
                onSave={handleSave}
                hasResume={hasResume}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
