"use client";

/**
 * AskVidyamargAgent — Global AI Career Agent panel.
 *
 * State is sourced entirely from GlobalAgentStore (Zustand + localStorage persistence).
 * The component does NOT manage its own message list or open/close state;
 * it reads from and writes to the shared store so that conversation history
 * survives navigation, refresh, and tab closure.
 *
 * Panel lifecycle:
 * - Always mounted at the CandidateLayout level (not per-page).
 * - Renders null when closed, keeping the React tree stable across route changes.
 * - isOpen / onClose are supplied as props from the layout.
 *
 * Context enrichment:
 * - Attaches lightweight resume metadata (title, status, has_resume) from
 *   useResumeStore (already loaded by the layout) to every request.
 * - These values are HINTS for the backend. The backend must use its own
 *   authoritative data sources for secure career operations.
 */

import { useState, useRef, useEffect, useMemo, useCallback } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Bot, Sparkles, Send, X, ChevronRight, CheckCircle2,
  AlertCircle, ArrowRight, ExternalLink, Briefcase, BookOpen,
  Mic, MicOff, FileText, Check, ShieldCheck, RefreshCw, Maximize2, Minimize2,
  Terminal, Flame, Sun, Moon, RotateCcw, ChevronDown
} from "lucide-react";
import { apiService } from "@/services/api";
import { useGlobalAgentStore } from "@/store/globalAgentStore";
import { useResumeStore } from "@/store/resumeStore";
import { useAuthStore } from "@/store/authStore";
import { APP_ROUTES } from "@/config/routes";
import { AgentActionBridge } from "@/services/agentActionBridge";

// ─── Props ────────────────────────────────────────────────────────────────────

interface AskVidyamargAgentProps {
  isOpen: boolean;
  onClose: () => void;
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function AskVidyamargAgent({ isOpen, onClose }: AskVidyamargAgentProps) {
  const pathname = usePathname();
  const router = useRouter();

  // ── Global store ──
  const messages = useGlobalAgentStore((state) => state.messages);
  const sessionId = useGlobalAgentStore((state) => state.sessionId);
  const addMessage = useGlobalAgentStore((state) => state.addMessage);
  const updateMessage = useGlobalAgentStore((state) => state.updateMessage);
  const clearMessages = useGlobalAgentStore((state) => state.clearMessages);
  const setHasUnread = useGlobalAgentStore((state) => state.setHasUnread);

  // ── Resume context (already fetched by layout) ──
  const resumeState = useResumeStore();

  // ── Auth context ──
  const { email: currentEmail } = useAuthStore();

  // ── UI local state ──
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);

  // Track in-flight request id to prevent duplicate submissions.
  const inflightRef = useRef<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<any>(null);

  // ── Derived page context (informational metadata ONLY — NEVER capability boundary) ──
  const pageContext = useMemo(() => {
    const path = pathname || "";
    let pageName = "Dashboard";

    if (path.includes("/candidate/resumes")) pageName = "Resume";
    else if (path.includes("/candidate/jobs")) pageName = "Jobs";
    else if (path.includes("/candidate/skill-lab") || path.includes("/candidate/learning")) pageName = "Skills & Courses";
    else if (path.includes("/candidate/interview")) pageName = "Interview";
    else if (path.includes("/candidate/applications")) pageName = "Applications";
    else if (path.includes("/candidate/mentor")) pageName = "AI Mentor";
    else if (path.includes("/candidate/settings")) pageName = "Settings";
    else if (path.includes("/candidate/profile")) pageName = "Profile";

    return { pageName, label: pageName, type: pageName.toLowerCase(), path };
  }, [pathname]);

  // ── Unified Global Quick Actions (identical across all routes) ──
  const quickActions = useMemo(() => [
    "Find matching jobs",
    "Analyze my resume",
    "Find my skill gaps",
    "Recommend courses",
    "Prepare me for an interview",
    "Show my applications",
  ], []);

  // ── Setup Web Speech Recognition ──
  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        setSpeechSupported(true);
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = "en-US";
        recognition.onresult = (event: any) => {
          const transcript = Array.from(event.results).map((r: any) => r[0].transcript).join("");
          setInput(transcript);
        };
        recognition.onerror = () => setIsListening(false);
        recognition.onend = () => setIsListening(false);
        recognitionRef.current = recognition;
      }
    }
  }, []);

  // ── Keyboard: Escape closes the panel ──
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // ── Scroll to bottom & focus on open/new message ──
  useEffect(() => {
    if (isOpen) {
      setHasUnread(false);
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        textareaRef.current?.focus();
      }, 50);
    }
  }, [isOpen, messages, setHasUnread]);

  // ── Voice input toggle ──
  const toggleVoiceInput = useCallback(() => {
    if (!speechSupported || !recognitionRef.current) {
      alert("Speech recognition is not supported in this browser. Please use Google Chrome or Edge.");
      return;
    }
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      setInput("");
      setIsListening(true);
      try {
        recognitionRef.current.start();
      } catch {
        setIsListening(false);
      }
    }
  }, [speechSupported, isListening]);

  // ── Client-side command handler using AgentActionBridge ──
  const handleClientSideCommand = useCallback(async (text: string) => {
    const lower = text.toLowerCase().trim();

    // Theme switching via AgentActionBridge
    if (lower.includes("light mode") || lower.includes("light theme") || lower.includes("dark mode") || lower.includes("dark theme")) {
      const targetTheme = (lower.includes("light mode") || lower.includes("light theme")) ? "light" : "dark";
      const cmdResult = await AgentActionBridge.executeCommand({
        command_id: `cmd_theme_${Date.now()}`,
        tool: "change_theme",
        arguments: { theme: targetTheme },
      });

      if (cmdResult.status === "succeeded") {
        addMessage({
          role: "agent",
          content: `Done! Switched VidyamargAI theme to **${targetTheme} mode**. Verified UI state: \`theme=${cmdResult.verification_evidence?.theme}\`.`,
          status: "success",
        });
      } else {
        addMessage({
          role: "agent",
          content: `Failed to change theme: ${cmdResult.error || "Theme update rejected."}`,
          status: "error",
        });
      }
      return true;
    }

    // Resume field update & save (e.g. "change designation to AI/ML Engineer")
    if (lower.includes("change my designation to") || lower.includes("update my designation to") || lower.includes("set designation to") || lower.includes("change designation")) {
      const desigMatch = text.match(/(?:designation|role)\s+(?:to\s+)?([A-Za-z0-9\s/]+)/i);
      const desigVal = desigMatch ? desigMatch[1].trim() : "AI/ML Engineer";

      // 1. Fill draft field
      const editResult = await AgentActionBridge.executeCommand({
        command_id: `cmd_edit_${Date.now()}`,
        tool: "fill_form_field",
        arguments: { field: "designation", value: desigVal },
      });

      // 2. Save draft
      const saveResult = await AgentActionBridge.executeCommand({
        command_id: `cmd_save_${Date.now()}`,
        tool: "save_resume",
        arguments: {},
      });

      if (editResult.status === "succeeded" && saveResult.status === "succeeded") {
        addMessage({
          role: "agent",
          content: `Updated designation draft to **"${desigVal}"** (Status: *Saved*). Verified active resume updated.`,
          status: "success",
        });
      } else if (editResult.status === "succeeded") {
        addMessage({
          role: "agent",
          content: `Updated designation to **"${desigVal}"** (*Updated in your draft*). Auto-save pending.`,
          status: "success",
        });
      }
      return true;
    }

    // Direct navigation via AgentActionBridge
    if (lower.startsWith("go to ") || lower.startsWith("open ") || lower.startsWith("take me to ") || lower.startsWith("navigate to ")) {
      let targetRoute = "";
      let targetName = "";
      if (lower.includes("job")) { targetRoute = APP_ROUTES.jobs; targetName = "Jobs"; }
      else if (lower.includes("resume")) { targetRoute = APP_ROUTES.resume; targetName = "Resume"; }
      else if (lower.includes("course") || lower.includes("skill") || lower.includes("learning")) { targetRoute = APP_ROUTES.courses; targetName = "Skills & Courses"; }
      else if (lower.includes("interview")) { targetRoute = APP_ROUTES.interview; targetName = "Interview"; }
      else if (lower.includes("application")) { targetRoute = APP_ROUTES.applications; targetName = "Applications"; }
      else if (lower.includes("dashboard")) { targetRoute = APP_ROUTES.dashboard; targetName = "Dashboard"; }
      else if (lower.includes("setting")) { targetRoute = APP_ROUTES.settings; targetName = "Settings"; }
      else if (lower.includes("profile")) { targetRoute = APP_ROUTES.profile; targetName = "Profile"; }
      else if (lower.includes("mentor")) { targetRoute = APP_ROUTES.mentor; targetName = "AI Mentor"; }

      if (targetRoute) {
        const navResult = await AgentActionBridge.executeCommand({
          command_id: `cmd_nav_${Date.now()}`,
          tool: "navigate_to_route",
          arguments: { path: targetRoute },
        });

        if (navResult.status === "succeeded") {
          addMessage({
            role: "agent",
            content: `Opened **${targetName}** (\`${navResult.output?.route}\`). Verified page destination ready.`,
            status: "success",
          });
        } else {
          addMessage({
            role: "agent",
            content: `Attempted to open **${targetName}**, but navigation verification returned an issue.`,
            status: "error",
          });
        }
        return true;
      }
    }

    return false;
  }, [addMessage]);

  // ── Build enriched page context for the backend ──
  const buildPageContext = useCallback(() => {
    const resumeHint = (() => {
      if (resumeState.isLoading) return { resume_status: "loading" as const };
      if (resumeState.error) return { resume_status: "error" as const };
      if (!resumeState.hasResume) return { resume_status: "none" as const };
      return {
        resume_status: "available" as const,
        resume_title: resumeState.activeResume?.title ?? null,
        resume_source_type: resumeState.activeResume?.source_type ?? null,
        resume_file_status: resumeState.activeResume?.status ?? null,
      };
    })();

    const uiState = AgentActionBridge.get_ui_state();

    return {
      pathname: uiState.current_route,
      page_label: pageContext.label,
      page_type: pageContext.type,
      active_resume_id: uiState.active_resume_id,
      theme: uiState.theme,
      is_dirty: uiState.is_dirty,
      ...resumeHint,
    };
  }, [pageContext, resumeState]);

  // ── Main message dispatcher ──
  const handleSendMessage = useCallback(async (textToSend?: string) => {
    const text = (textToSend ?? input).trim();
    if (!text || loading) return;
    if (inflightRef.current) return;

    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }

    addMessage({ role: "user", content: text, status: "success" });
    setInput("");

    // Execute client-side website control commands first
    const handledLocally = await handleClientSideCommand(text);
    if (handledLocally) return;

    setLoading(true);

    const pendingId = addMessage({
      role: "agent",
      content: "",
      status: "pending",
    });
    inflightRef.current = pendingId;

    try {
      const historyPayload = messages
        .filter((m) => !m.id.startsWith("welcome_") && m.id !== pendingId && m.status !== "pending")
        .slice(-8)
        .map((m) => ({ role: m.role === "agent" ? "assistant" : "user", content: m.content }));

      const result = await apiService.chatWithCareerAgent({
        message: text,
        page_context: buildPageContext(),
        history: historyPayload,
        ...(sessionId ? { session_id: sessionId } : {}),
      } as any);

      // Execute returned client commands via AgentActionBridge
      if (result.commands && Array.isArray(result.commands) && result.commands.length > 0) {
        for (const cmd of result.commands) {
          const cmdRes = await AgentActionBridge.executeCommand(cmd);
          if (cmdRes.status === "failed") {
            console.warn(`[AgentActionBridge] Command ${cmd.tool} failed:`, cmdRes.error);
          }
        }
      }

      updateMessage(pendingId, {
        content: result.response,
        status: "success",
        plan: result.plan || [],
        actionPreview: result.action_preview || null,
        uiCards: result.ui_cards || [],
      });

      if (!isOpen) setHasUnread(true);

      if (result.session_id && result.session_id !== sessionId) {
        useGlobalAgentStore.setState({ sessionId: result.session_id });
      }
    } catch (err: any) {
      updateMessage(pendingId, {
        content: `I couldn't complete the action: ${err.message || "Please check your network and try again."}`,
        status: "error",
      });
    } finally {
      setLoading(false);
      inflightRef.current = null;
    }
  }, [input, loading, isListening, messages, sessionId, isOpen, addMessage, updateMessage, setHasUnread, handleClientSideCommand, buildPageContext]);

  // ── Confirm / cancel an action preview ──
  const handleConfirmAction = useCallback(async (
    msgId: string,
    preview: NonNullable<typeof messages[0]["actionPreview"]>,
    confirmed: boolean
  ) => {
    try {
      const res = await apiService.confirmCareerAgentAction({
        action_id: preview.action_id,
        action_type: preview.action_type,
        payload: preview.payload,
        confirmed,
      });
      updateMessage(msgId, {
        actionPreview: null,
        content: messages.find((m) => m.id === msgId)?.content +
          `\n\n**Action Status:** ${res.message}`,
      });
    } catch (e: any) {
      alert("Failed to confirm action: " + e.message);
    }
  }, [messages, updateMessage]);

  // ── Render null when closed (panel always stays mounted in the tree) ──
  if (!isOpen) return null;

  return (
    <>
      {/* Mobile/Tablet backdrop overlay */}
      <div
        className="lg:hidden fixed inset-0 bg-black/50 backdrop-blur-xs z-40 animate-in fade-in duration-200"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Agent Panel — strictly fixed 390px width */}
      <aside
        role="dialog"
        aria-label="VidyamargAI Career Agent"
        className="fixed inset-y-0 right-0 z-50 lg:static lg:z-10 h-full flex flex-col bg-app-surface border-l border-app-border font-sans shrink-0 overflow-hidden shadow-2xl lg:shadow-none w-full sm:w-[390px] lg:w-[390px] min-w-[390px] max-w-[390px]"
      >
        {/* ── Header bar ── */}
        <div className="p-3.5 border-b border-app-border bg-gradient-to-r from-purple-950/20 via-indigo-950/15 to-blue-950/20 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-purple-600 via-indigo-600 to-blue-600 flex items-center justify-center text-white shadow-md shrink-0">
              <Bot size={17} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-app-text">AI Agent</h3>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={clearMessages}
              className="p-1.5 rounded-lg text-app-text-muted hover:text-app-text hover:bg-app-bg transition-colors"
              title="New Conversation"
              aria-label="New Conversation"
            >
              <RotateCcw size={13} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-app-text-muted hover:text-app-text hover:bg-app-bg transition-colors"
              title="Close Agent Panel"
              aria-label="Close Agent Panel"
            >
              <X size={15} />
            </button>
          </div>
        </div>

        {/* ── Messages Scroll Area ── */}
        <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-2.5 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
            >
              {/* Avatar */}
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs font-bold mt-1 shadow-xs ${
                  msg.role === "user"
                    ? "bg-purple-600 text-white"
                    : "bg-gradient-to-br from-purple-600 to-indigo-600 text-white"
                }`}
              >
                {msg.role === "user" ? "You" : <Bot size={14} />}
              </div>

              <div className={`flex flex-col gap-2 max-w-[85%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
                {/* Plan steps */}
                {msg.plan && msg.plan.length > 0 && (
                  <div className="p-3 rounded-xl border border-purple-200 dark:border-purple-800/40 bg-purple-50/50 dark:bg-purple-950/20 w-full space-y-1.5 text-xs">
                    <span className="text-[10px] font-bold text-purple-700 dark:text-purple-300 uppercase tracking-wider block">
                      Action Progress:
                    </span>
                    {msg.plan.map((step) => (
                      <div key={step.id} className="flex items-center gap-2 text-[11px]">
                        {step.status === "completed" && <CheckCircle2 size={12} className="text-emerald-500 shrink-0" />}
                        {step.status === "running" && <RefreshCw size={12} className="animate-spin text-purple-600 shrink-0" />}
                        {step.status === "failed" && <AlertCircle size={12} className="text-red-500 shrink-0" />}
                        {step.status === "waiting_confirmation" && <Flame size={12} className="text-amber-500 shrink-0" />}
                        <span className={step.status === "completed" ? "text-app-text font-medium" : "text-app-text-muted"}>
                          {step.label}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Message bubble */}
                <div
                  className={`p-3.5 rounded-2xl text-xs leading-relaxed ${
                    msg.role === "user"
                      ? "bg-purple-600 text-white rounded-tr-xs"
                      : msg.status === "pending"
                      ? "bg-app-bg border border-app-border text-app-text-muted rounded-tl-xs animate-pulse"
                      : msg.status === "error"
                      ? "bg-red-50/50 dark:bg-red-950/20 border border-red-200 dark:border-red-800/40 text-app-text rounded-tl-xs"
                      : "bg-app-bg border border-app-border text-app-text rounded-tl-xs"
                  }`}
                >
                  {msg.status === "pending" ? (
                    <div className="flex items-center gap-2">
                      <RefreshCw size={12} className="animate-spin text-purple-600 shrink-0" />
                      <span>Career Agent is executing authorized tools…</span>
                    </div>
                  ) : (
                    <div className="space-y-2 whitespace-pre-wrap font-sans break-words [overflow-wrap:anywhere]">{msg.content}</div>
                  )}
                </div>

                {/* Action preview card */}
                {msg.actionPreview && (
                  <div className="w-full p-3.5 rounded-xl border border-amber-300 dark:border-amber-800/60 bg-amber-50/50 dark:bg-amber-950/20 space-y-2.5 text-xs">
                    <div className="flex items-center gap-2 text-amber-800 dark:text-amber-300 font-bold">
                      <ShieldCheck size={16} />
                      <span>Action Preview: {msg.actionPreview.title}</span>
                    </div>
                    <p className="text-[11px] text-amber-900/80 dark:text-amber-200/80">
                      Ready to apply using <strong>{msg.actionPreview.resume_title}</strong> to:
                    </p>
                    <div className="space-y-1">
                      {msg.actionPreview.targets.map((t, idx) => (
                        <div key={idx} className="flex justify-between p-1.5 rounded-lg bg-white/70 dark:bg-black/30 text-[11px]">
                          <span className="font-semibold">{t.company} — {t.role}</span>
                          <span className="text-emerald-600 font-bold">{t.match} match</span>
                        </div>
                      ))}
                    </div>
                    <div className="flex items-center justify-end gap-2 pt-1">
                      <button
                        onClick={() => handleConfirmAction(msg.id, msg.actionPreview!, false)}
                        className="px-3 py-1 rounded-lg border border-app-border text-[11px] font-semibold text-app-text-muted hover:text-app-text"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleConfirmAction(msg.id, msg.actionPreview!, true)}
                        className="px-3.5 py-1 rounded-lg bg-emerald-600 text-white text-[11px] font-bold hover:bg-emerald-700 shadow-xs"
                      >
                        Confirm & Apply
                      </button>
                    </div>
                  </div>
                )}

                {/* UI cards (jobs, courses, interview launch) */}
                {msg.uiCards && msg.uiCards.length > 0 && (
                  <div className="w-full space-y-2 pt-1">
                    {msg.uiCards.map((card, cIdx) => {
                      if (card.type === "job") {
                        return (
                          <div key={cIdx} className="p-3 rounded-xl border border-app-border bg-app-surface space-y-2 text-xs">
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <h4 className="font-bold text-app-text">{card.title}</h4>
                                <p className="text-[11px] text-app-text-muted">{card.company} · {card.location}</p>
                              </div>
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
                                {card.match_score}% match
                              </span>
                            </div>
                            <div className="flex items-center gap-2 pt-1">
                              <Link
                                href={`/candidate/resumes/tailor/1?role=${encodeURIComponent(card.title)}&company=${encodeURIComponent(card.company)}`}
                                className="text-[11px] font-semibold text-purple-600 dark:text-purple-400 hover:underline flex items-center gap-1"
                              >
                                <FileText size={11} /> Tailor Resume
                              </Link>
                              <span className="text-app-border">|</span>
                              <Link
                                href={`/candidate/interview?role=${encodeURIComponent(card.title)}`}
                                className="text-[11px] font-semibold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                              >
                                <Mic size={11} /> Practice Interview
                              </Link>
                            </div>
                          </div>
                        );
                      }

                      if (card.type === "course") {
                        return (
                          <div key={cIdx} className="p-3 rounded-xl border border-app-border bg-app-surface space-y-1.5 text-xs">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-bold uppercase tracking-wider text-purple-600">Course Recommendation</span>
                              <span className="text-[10px] text-app-text-muted">{card.duration}</span>
                            </div>
                            <h4 className="font-bold text-app-text">{card.title}</h4>
                            <Link
                              href={card.action_url || "/candidate/skill-lab"}
                              className="inline-flex items-center gap-1 text-[11px] font-bold text-purple-600 hover:underline pt-0.5"
                            >
                              Enroll & Start Learning <ArrowRight size={11} />
                            </Link>
                          </div>
                        );
                      }

                      if (card.type === "interview_launch") {
                        return (
                          <div key={cIdx} className="p-3.5 rounded-xl border border-indigo-200 dark:border-indigo-800 bg-indigo-50/40 dark:bg-indigo-950/20 space-y-2 text-xs">
                            <div className="flex items-center justify-between">
                              <h4 className="font-bold text-indigo-900 dark:text-indigo-200">
                                {card.difficulty} {card.interview_type} Interview Prepared
                              </h4>
                              <Mic size={14} className="text-indigo-600" />
                            </div>
                            <p className="text-[11px] text-app-text-secondary italic">
                              &quot;{card.opening_question}&quot;
                            </p>
                            <Link
                              href={card.action_url || "/candidate/interview"}
                              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-indigo-600 text-white font-bold text-xs hover:bg-indigo-700 shadow-xs"
                            >
                              Launch Interview Room <ArrowRight size={12} />
                            </Link>
                          </div>
                        );
                      }

                      return null;
                    })}
                  </div>
                )}
              </div>
            </div>
          ))}

          <div ref={messagesEndRef} />
        </div>

        {/* ── Quick Action Chips ── */}
        <div className="px-3 py-2 border-t border-app-border bg-app-surface/60 overflow-x-auto whitespace-normal flex flex-wrap max-h-24 overflow-y-auto gap-1.5 scrollbar-none shrink-0">
          {quickActions.map((prompt, pIdx) => (
            <button
              key={pIdx}
              disabled={loading}
              onClick={() => handleSendMessage(prompt)}
              className="px-2.5 py-1 rounded-full text-[10px] font-medium border border-app-border bg-app-surface text-app-text-muted hover:text-purple-600 hover:border-purple-400 shrink-0 transition-colors disabled:opacity-50"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* ── Input Bar ── */}
        <div className="p-3 border-t border-app-border bg-app-surface flex items-end gap-2 shrink-0">
          {/* Voice microphone */}
          {speechSupported && (
            <button
              type="button"
              onClick={toggleVoiceInput}
              title={isListening ? "Listening… click to stop" : "Speak to Agent"}
              className={`p-2.5 rounded-xl transition-all shrink-0 ${
                isListening
                  ? "bg-red-500 text-white animate-pulse shadow-md"
                  : "border border-app-border text-app-text-muted hover:text-purple-600 hover:border-purple-400"
              }`}
            >
              {isListening ? <MicOff size={15} /> : <Mic size={15} />}
            </button>
          )}

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            placeholder={isListening ? "Listening…" : "Ask me anything… (Shift+Enter for new line)"}
            className="flex-1 min-w-0 max-h-28 min-h-[40px] resize-none text-xs px-3.5 py-2.5 rounded-xl border border-app-border bg-app-bg text-app-text focus:outline-none focus:ring-2 focus:ring-purple-500 font-sans"
          />

          {/* Send */}
          <button
            disabled={!input.trim() || loading || !!inflightRef.current}
            onClick={() => handleSendMessage()}
            aria-label="Send Message"
            className="p-2.5 rounded-xl bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 transition-colors shadow-xs shrink-0"
          >
            <Send size={15} />
          </button>
        </div>
      </aside>
    </>
  );
}
