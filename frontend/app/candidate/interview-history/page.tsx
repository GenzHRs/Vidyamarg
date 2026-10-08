"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  History,
  Mic2,
  Calendar,
  Award,
  BarChart3,
  RefreshCw,
  Play,
  ChevronRight,
  Loader2,
  TrendingUp,
} from "lucide-react";

interface InterviewRecord {
  id: string | number;
  role: string;
  type: string;
  difficulty: string;
  score: number;
  date: string;
  duration?: string;
}

export default function InterviewHistoryPage() {
  const [records, setRecords] = useState<InterviewRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load from localStorage (interviews started in this session)
    // In production this would come from a backend endpoint
    const stored = localStorage.getItem("vidyamarg_interview_history");
    if (stored) {
      try {
        setRecords(JSON.parse(stored));
      } catch {
        setRecords([]);
      }
    }
    setLoading(false);
  }, []);

  const avgScore = records.length > 0
    ? Math.round(records.reduce((s, r) => s + r.score, 0) / records.length)
    : 0;

  const bestScore = records.length > 0
    ? Math.max(...records.map((r) => r.score))
    : 0;

  const scoreColor = (s: number) =>
    s >= 80 ? "text-emerald-600 dark:text-emerald-400"
    : s >= 60 ? "text-amber-600 dark:text-amber-400"
    : "text-red-600 dark:text-red-400";

  return (
    <div className="min-h-screen bg-app-bg text-app-text font-sans">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-6">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-app-text">Interview History</h1>
            <p className="text-sm text-app-text-muted mt-0.5">Track your practice sessions and improvement</p>
          </div>
          <Link
            href="/candidate/interview"
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-bold hover:bg-indigo-700 transition-colors"
          >
            <Play size={14} /> New Interview
          </Link>
        </div>

        {/* Stats */}
        {records.length > 0 && (
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-app-surface border border-app-border rounded-2xl p-4 text-center">
              <p className="text-2xl font-bold text-app-text">{records.length}</p>
              <p className="text-xs text-app-text-muted font-medium mt-0.5">Sessions</p>
            </div>
            <div className="bg-app-surface border border-app-border rounded-2xl p-4 text-center">
              <p className={`text-2xl font-bold ${scoreColor(avgScore)}`}>{avgScore}</p>
              <p className="text-xs text-app-text-muted font-medium mt-0.5">Avg Score</p>
            </div>
            <div className="bg-app-surface border border-app-border rounded-2xl p-4 text-center">
              <p className={`text-2xl font-bold ${scoreColor(bestScore)}`}>{bestScore}</p>
              <p className="text-xs text-app-text-muted font-medium mt-0.5">Best Score</p>
            </div>
          </div>
        )}

        {/* Records */}
        {loading ? (
          <div className="flex items-center justify-center py-16 gap-2">
            <Loader2 size={20} className="animate-spin text-blue-500" />
            <span className="text-sm text-app-text-muted">Loading history…</span>
          </div>
        ) : records.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
            <div className="w-16 h-16 rounded-2xl bg-indigo-50 dark:bg-indigo-950/30 flex items-center justify-center">
              <History size={28} className="text-indigo-400" />
            </div>
            <div>
              <p className="font-semibold text-app-text">No interviews yet</p>
              <p className="text-sm text-app-text-muted mt-1 max-w-xs">
                Complete your first AI interview to see your performance history here.
              </p>
            </div>
            <Link
              href="/candidate/interview"
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 text-white text-sm font-bold hover:bg-indigo-700 transition-colors"
            >
              <Mic2 size={15} /> Start First Interview
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {records.map((r) => (
              <div key={r.id} className="bg-app-surface border border-app-border rounded-2xl p-5">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-950/30 flex items-center justify-center">
                      <Mic2 size={17} className="text-indigo-500" />
                    </div>
                    <div>
                      <p className="font-bold text-sm text-app-text">{r.role}</p>
                      <div className="flex gap-2 mt-0.5">
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                          {r.type}
                        </span>
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                          {r.difficulty}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-xl font-bold ${scoreColor(r.score)}`}>{r.score}</p>
                    <p className="text-[10px] text-app-text-muted">/ 100</p>
                  </div>
                </div>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-[11px] text-app-text-muted flex items-center gap-1">
                    <Calendar size={10} /> {new Date(r.date).toLocaleDateString()}
                  </span>
                  <Link
                    href={`/candidate/interview?role=${encodeURIComponent(r.role)}&type=${r.type}`}
                    className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
                  >
                    Practice again <ChevronRight size={11} />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Improvement tip */}
        {records.length > 0 && avgScore < 75 && (
          <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200/60 dark:border-blue-800/40 rounded-2xl p-4 flex items-start gap-3">
            <TrendingUp size={18} className="text-blue-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-blue-700 dark:text-blue-400">Keep practicing to improve!</p>
              <p className="text-xs text-blue-600/80 dark:text-blue-500 mt-0.5">
                Your average score is {avgScore}/100. Practice more interviews and take our recommended courses to boost your performance.
              </p>
              <Link href="/candidate/skill-lab" className="text-xs font-bold text-blue-600 dark:text-blue-400 underline mt-1 block">
                Browse Recommended Courses →
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
