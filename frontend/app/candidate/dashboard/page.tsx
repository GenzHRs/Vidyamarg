"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuthStore } from "@/store/authStore";
import { apiService } from "@/services/api";
import {
  FileText,
  Briefcase,
  BookOpen,
  Mic2,
  Target,
  TrendingUp,
  Zap,
  ArrowRight,
  CheckCircle,
  AlertCircle,
  Upload,
  ChevronRight,
  Star,
  Award,
  BarChart3,
  RefreshCw,
  User,
  Brain,
} from "lucide-react";

// ──────── Types ────────
interface CareerData {
  profile: any;
  roles: any;
  skillGaps: any;
  readiness: any;
  resumes: any[];
}

// ──────── Sub-components ────────
function StatCard({
  label,
  value,
  icon: Icon,
  color,
  sub,
}: {
  label: string;
  value: string | number;
  icon: any;
  color: string;
  sub?: string;
}) {
  return (
    <div className="bg-app-surface border border-app-border rounded-2xl p-5 flex items-center gap-4">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${color}`}>
        <Icon size={20} />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-app-text-muted font-medium truncate">{label}</p>
        <p className="text-xl font-bold text-app-text leading-tight">{value}</p>
        {sub && <p className="text-[11px] text-app-text-muted mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

function SkillBadge({ name, type }: { name: string; type: "have" | "gap" | "recommended" }) {
  const styles = {
    have: "bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400 border-emerald-200/60 dark:border-emerald-800/40",
    gap: "bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-400 border-red-200/60 dark:border-red-800/40",
    recommended: "bg-blue-50 dark:bg-blue-950/30 text-blue-700 dark:text-blue-400 border-blue-200/60 dark:border-blue-800/40",
  };
  const icons = { have: "✓", gap: "✗", recommended: "+" };
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold border ${styles[type]}`}>
      <span className="text-[10px]">{icons[type]}</span>
      {name}
    </span>
  );
}

function CareerJourneyBar({ readiness }: { readiness: number }) {
  const steps = [
    { label: "Resume", done: readiness > 0 },
    { label: "Skills", done: readiness >= 20 },
    { label: "Learning", done: readiness >= 40 },
    { label: "Jobs", done: readiness >= 60 },
    { label: "Interview", done: readiness >= 80 },
  ];
  return (
    <div className="flex items-center gap-1 sm:gap-2">
      {steps.map((step, i) => (
        <div key={step.label} className="flex items-center gap-1 sm:gap-2">
          <div className={`flex flex-col items-center gap-1`}>
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-all ${
                step.done
                  ? "bg-blue-600 border-blue-600 text-white"
                  : "bg-app-surface border-app-border text-app-text-muted"
              }`}
            >
              {step.done ? <CheckCircle size={14} /> : i + 1}
            </div>
            <span className="text-[9px] sm:text-[10px] font-semibold text-app-text-muted whitespace-nowrap">
              {step.label}
            </span>
          </div>
          {i < steps.length - 1 && (
            <div
              className={`h-0.5 w-6 sm:w-10 rounded mb-4 transition-all ${
                steps[i + 1].done ? "bg-blue-600" : "bg-app-border"
              }`}
            />
          )}
        </div>
      ))}
    </div>
  );
}

// ──────── Main Dashboard ────────
export default function DashboardPage() {
  const router = useRouter();
  const { fullName } = useAuthStore();
  const [data, setData] = useState<CareerData>({
    profile: null,
    roles: null,
    skillGaps: null,
    readiness: null,
    resumes: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const firstName = fullName ? fullName.split(" ")[0] : "there";
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [profile, roles, skillGaps, readiness, resumes] = await Promise.allSettled([
        apiService.getProfile(),
        apiService.getResumeRoles(),
        apiService.getResumeSkillGaps(),
        apiService.getCareerReadiness(),
        apiService.getResumes(),
      ]);

      setData({
        profile: profile.status === "fulfilled" ? profile.value : null,
        roles: roles.status === "fulfilled" ? roles.value : null,
        skillGaps: skillGaps.status === "fulfilled" ? skillGaps.value : null,
        readiness: readiness.status === "fulfilled" ? readiness.value : null,
        resumes: resumes.status === "fulfilled" ? (Array.isArray(resumes.value) ? resumes.value : []) : [],
      });
    } catch (e) {
      setError("Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const hasResume = data.resumes.length > 0 || Boolean(data.profile?.personal_info?.name) || Boolean(data.profile?.skills) || Boolean(data.readiness?.resume_score);
  const readinessScore = data.readiness?.career_readiness_score ?? 0;
  const topSkills: string[] = data.skillGaps?.skills_present?.slice(0, 6) ?? [];
  const missingSkills: string[] = data.skillGaps?.skill_gaps?.slice(0, 5) ?? [];
  const recommendedRoles: string[] = data.roles?.roles?.slice(0, 4) ?? [];
  const targetRole = data.roles?.target_role ?? data.roles?.roles?.[0] ?? null;
  const resumeScore = data.readiness?.resume_score ?? null;
  const profileCompletion = data.readiness?.profile_completion ?? null;
  const coursesCompleted = data.readiness?.courses_completed ?? 0;
  const learningStreak = data.readiness?.learning_streak ?? 0;

  if (loading) {
    return (
      <div className="min-h-screen bg-app-bg flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 rounded-full border-4 border-t-blue-500 border-app-border animate-spin" />
          <p className="text-sm text-app-text-muted">Loading your career dashboard…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-app-bg text-app-text font-sans">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6">

        {/* ── Top: Greeting + Quick Actions ── */}
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <p className="text-sm text-app-text-muted font-medium">{greeting} 👋</p>
            <h1 className="text-2xl sm:text-3xl font-bold text-app-text mt-0.5">
              Welcome back, {firstName}
            </h1>
            {targetRole && (
              <p className="text-sm text-app-text-muted mt-1">
                Target Role: <span className="font-semibold text-blue-600 dark:text-blue-400">{targetRole}</span>
              </p>
            )}
          </div>
          <button
            onClick={fetchDashboardData}
            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-app-border text-sm font-medium text-app-text-muted hover:text-app-text hover:bg-app-surface transition-colors self-start"
          >
            <RefreshCw size={14} />
            Refresh
          </button>
        </div>

        {/* ── No Resume Banner ── */}
        {!hasResume && (
          <div className="bg-gradient-to-r from-blue-600/10 to-indigo-600/10 border border-blue-200/60 dark:border-blue-800/40 rounded-2xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-600/20 flex items-center justify-center text-blue-600 dark:text-blue-400">
                <FileText size={20} />
              </div>
              <div>
                <p className="font-semibold text-app-text">Get started by adding your resume</p>
                <p className="text-xs text-app-text-muted mt-0.5">
                  Upload your resume or create one to unlock personalized AI insights.
                </p>
              </div>
            </div>
            <div className="flex gap-2 shrink-0">
              <Link
                href="/candidate/resumes/upload"
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition-colors"
              >
                <Upload size={14} />
                Upload Resume
              </Link>
              <Link
                href="/candidate/resumes/new"
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-app-border text-sm font-semibold hover:bg-app-surface transition-colors"
              >
                Create New
              </Link>
            </div>
          </div>
        )}

        {/* ── Career Profile Cards ── */}
        <div className="grid cq-grid-stat gap-3 sm:gap-4">
          <StatCard
            label="Resume Score"
            value={resumeScore !== null ? `${resumeScore}/100` : "—"}
            icon={FileText}
            color="bg-blue-100 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400"
            sub={resumeScore !== null ? (resumeScore >= 70 ? "Strong" : "Needs work") : "Upload resume"}
          />
          <StatCard
            label="Profile Completion"
            value={profileCompletion !== null ? `${Math.round(profileCompletion)}%` : "—"}
            icon={User}
            color="bg-indigo-100 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-400"
            sub="Keep it updated"
          />
          <StatCard
            label="Courses Done"
            value={coursesCompleted}
            icon={BookOpen}
            color="bg-emerald-100 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400"
            sub="Keep learning"
          />
          <StatCard
            label="Learning Streak"
            value={`${learningStreak}d`}
            icon={Zap}
            color="bg-amber-100 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400"
            sub={learningStreak > 0 ? "On a roll!" : "Start today"}
          />
        </div>

        {/* ── Career Journey Progress ── */}
        <div className="bg-app-surface border border-app-border rounded-2xl p-5 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-bold text-app-text text-base">AI Career Progress</h2>
              <p className="text-xs text-app-text-muted mt-0.5">Your journey to job-readiness</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-app-text-muted">Readiness</span>
              <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
                {Math.round(readinessScore)}%
              </span>
            </div>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-app-border rounded-full h-2 mb-5">
            <div
              className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-500"
              style={{ width: `${Math.min(100, readinessScore)}%` }}
            />
          </div>

          <CareerJourneyBar readiness={readinessScore} />
        </div>

        {/* ── Main Content Grid ── */}
        <div className="grid cq-dashboard-main gap-4 sm:gap-6">

          {/* Left col (2/3) */}
          <div className="lg:col-span-2 space-y-4 sm:space-y-6">

            {/* Top Skills */}
            {topSkills.length > 0 && (
              <div className="bg-app-surface border border-app-border rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Brain size={16} className="text-emerald-500" />
                  <h3 className="font-bold text-app-text text-sm">Your Top Skills</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {topSkills.map((s) => (
                    <SkillBadge key={s} name={s} type="have" />
                  ))}
                </div>
              </div>
            )}

            {/* Skill Gaps */}
            {missingSkills.length > 0 && (
              <div className="bg-app-surface border border-app-border rounded-2xl p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <AlertCircle size={16} className="text-red-500" />
                    <h3 className="font-bold text-app-text text-sm">Skill Gaps</h3>
                  </div>
                  <Link
                    href="/candidate/skill-lab"
                    className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                  >
                    Start learning <ArrowRight size={12} />
                  </Link>
                </div>
                <div className="flex flex-wrap gap-2">
                  {missingSkills.map((s) => (
                    <SkillBadge key={s} name={s} type="gap" />
                  ))}
                </div>
              </div>
            )}

            {/* Recommended Jobs Quick Links */}
            <div className="bg-app-surface border border-app-border rounded-2xl p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Briefcase size={16} className="text-blue-500" />
                  <h3 className="font-bold text-app-text text-sm">Recommended Jobs</h3>
                </div>
                <Link
                  href="/candidate/jobs"
                  className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                >
                  View all <ArrowRight size={12} />
                </Link>
              </div>
              {hasResume ? (
                <div className="space-y-2">
                  {recommendedRoles.length > 0 ? (
                    recommendedRoles.map((role) => (
                      <Link
                        key={role}
                        href={`/candidate/jobs?role=${encodeURIComponent(role)}`}
                        className="flex items-center justify-between p-3 rounded-xl border border-app-border hover:border-blue-200 dark:hover:border-blue-800/60 hover:bg-blue-50/30 dark:hover:bg-blue-950/20 transition-all group"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-950/40 flex items-center justify-center">
                            <Briefcase size={14} className="text-blue-600 dark:text-blue-400" />
                          </div>
                          <span className="text-sm font-semibold text-app-text">{role}</span>
                        </div>
                        <ChevronRight size={15} className="text-app-text-muted group-hover:text-blue-500 transition-colors" />
                      </Link>
                    ))
                  ) : (
                    <p className="text-sm text-app-text-muted py-2">
                      AI is analyzing your resume to suggest roles…
                    </p>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-6 gap-2 text-center">
                  <FileText size={28} className="text-app-text-muted/40" />
                  <p className="text-sm text-app-text-muted">Upload your resume to get personalized job recommendations</p>
                </div>
              )}
            </div>

            {/* Interview Practice CTA */}
            <div className="bg-gradient-to-br from-indigo-600/10 via-violet-600/10 to-blue-600/10 border border-indigo-200/60 dark:border-indigo-800/40 rounded-2xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-xl bg-indigo-100 dark:bg-indigo-950/50 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                  <Mic2 size={20} />
                </div>
                <div>
                  <p className="font-bold text-app-text text-sm">Practice Your Interview</p>
                  <p className="text-xs text-app-text-muted mt-0.5">
                    AI-powered realistic interview based on your resume
                  </p>
                </div>
              </div>
              <Link
                href="/candidate/interview"
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 transition-colors shrink-0"
              >
                Start Interview <ArrowRight size={14} />
              </Link>
            </div>
          </div>

          {/* Right col (1/3) */}
          <div className="space-y-4">

            {/* Suitable Roles */}
            {recommendedRoles.length > 0 && (
              <div className="bg-app-surface border border-app-border rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Target size={15} className="text-violet-500" />
                  <h3 className="font-bold text-app-text text-sm">AI-Detected Roles</h3>
                </div>
                <div className="space-y-2">
                  {recommendedRoles.map((role, i) => (
                    <div key={role} className="flex items-center gap-2.5 py-1.5">
                      <div className="w-5 h-5 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-[9px] font-bold text-app-text-muted">
                        {i + 1}
                      </div>
                      <span className="text-sm font-medium text-app-text">{role}</span>
                      {i === 0 && (
                        <span className="ml-auto text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-blue-100 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400">
                          Best match
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Quick Actions */}
            <div className="bg-app-surface border border-app-border rounded-2xl p-5">
              <h3 className="font-bold text-app-text text-sm mb-3">Quick Actions</h3>
              <div className="space-y-1.5">
                {[
                  { label: "View My Resumes", href: "/candidate/resumes", icon: FileText, color: "text-blue-500" },
                  { label: "Browse Jobs", href: "/candidate/jobs", icon: Briefcase, color: "text-emerald-500" },
                  { label: "Start Learning", href: "/candidate/skill-lab", icon: BookOpen, color: "text-amber-500" },
                  { label: "Ask AI Mentor", href: "/candidate/mentor", icon: Brain, color: "text-violet-500" },
                  { label: "Practice Interview", href: "/candidate/interview", icon: Mic2, color: "text-indigo-500" },
                ].map((action) => {
                  const Icon = action.icon;
                  return (
                    <Link
                      key={action.label}
                      href={action.href}
                      className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors group"
                    >
                      <Icon size={16} className={action.color} />
                      <span className="text-sm font-medium text-app-text-muted group-hover:text-app-text transition-colors">
                        {action.label}
                      </span>
                      <ChevronRight size={13} className="ml-auto text-app-border group-hover:text-app-text-muted transition-colors" />
                    </Link>
                  );
                })}
              </div>
            </div>

            {/* Resume Stats */}
            {data.resumes.length > 0 && (
              <div className="bg-app-surface border border-app-border rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Award size={15} className="text-amber-500" />
                  <h3 className="font-bold text-app-text text-sm">My Resumes</h3>
                </div>
                <div className="space-y-2">
                  {data.resumes.slice(0, 3).map((r: any) => (
                    <Link
                      key={r.id}
                      href={`/candidate/resumes`}
                      className="flex items-center gap-2.5 p-2.5 rounded-xl border border-app-border hover:border-blue-200 dark:hover:border-blue-800/60 transition-all"
                    >
                      <FileText size={14} className="text-blue-500 shrink-0" />
                      <span className="text-xs font-medium text-app-text truncate">
                        {r.title || r.original_filename || `Resume #${r.id}`}
                      </span>
                      <CheckCircle size={12} className="ml-auto text-emerald-500 shrink-0" />
                    </Link>
                  ))}
                  {data.resumes.length > 3 && (
                    <Link
                      href="/candidate/resumes"
                      className="text-xs text-blue-600 dark:text-blue-400 font-semibold hover:underline block text-center pt-1"
                    >
                      +{data.resumes.length - 3} more resumes
                    </Link>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── Career Loop Visualization ── */}
        <div className="bg-app-surface border border-app-border rounded-2xl p-5 sm:p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={16} className="text-blue-500" />
            <h2 className="font-bold text-app-text text-base">The VidyamargAI Career Loop</h2>
          </div>
          <div className="flex flex-wrap gap-2 items-center justify-start">
            {[
              "Resume",
              "AI Analysis",
              "Roles",
              "Job Matching",
              "Skill Gaps",
              "Courses",
              "AI Mentor",
              "Interview Prep",
              "Interview",
              "Evaluation",
              "Improvement",
            ].map((step, i, arr) => (
              <div key={step} className="flex items-center gap-2">
                <span className="px-3 py-1.5 rounded-full text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-app-text border border-app-border">
                  {step}
                </span>
                {i < arr.length - 1 && (
                  <ArrowRight size={12} className="text-app-text-muted shrink-0" />
                )}
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
