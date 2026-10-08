"use client";

import { useState, useRef, useEffect } from "react";
import { useAuthStore } from "@/store/authStore";
import { useGlobalAgentStore } from "@/store/globalAgentStore";
import { useResumeStore } from "@/store/resumeStore";
import { apiService } from "@/services/api";
import {
  Bot,
  Send,
  User,
  Sparkles,
  RefreshCw,
  FileText,
  Briefcase,
  BookOpen,
  Mic2,
  TrendingUp,
  Copy,
  Check,
  ShieldCheck,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";

const GLOBAL_SUGGESTED_PROMPTS = [
  { icon: Briefcase, text: "Find matching jobs", color: "text-blue-500" },
  { icon: FileText, text: "Analyze my resume", color: "text-violet-500" },
  { icon: TrendingUp, text: "Find my skill gaps", color: "text-emerald-500" },
  { icon: BookOpen, text: "Recommend courses", color: "text-amber-500" },
  { icon: Mic2, text: "Prepare me for an interview", color: "text-indigo-500" },
  { icon: Sparkles, text: "Show my applications", color: "text-rose-500" },
];

function MessageBubble({ msg }: { msg: any }) {
  const [copied, setCopied] = useState(false);
  const isUser = msg.role === "user";

  const copyText = () => {
    navigator.clipboard.writeText(msg.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"} group`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1 ${
          isUser
            ? "bg-purple-600 text-white font-bold text-xs"
            : "bg-gradient-to-br from-violet-500 to-indigo-600 text-white"
        }`}
      >
        {isUser ? "You" : <Bot size={15} />}
      </div>

      <div className={`flex flex-col gap-1.5 max-w-[85%] ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? "bg-purple-600 text-white rounded-tr-sm"
              : "bg-app-surface border border-app-border text-app-text rounded-tl-sm shadow-xs"
          }`}
        >
          {msg.content.split("\n").map((line: string, i: number) => (
            <span key={i}>
              {line}
              {i < msg.content.split("\n").length - 1 && <br />}
            </span>
          ))}
        </div>

        {/* Action preview card if present */}
        {msg.actionPreview && (
          <div className="w-full p-3.5 rounded-xl border border-amber-300 dark:border-amber-800/60 bg-amber-50/50 dark:bg-amber-950/20 space-y-2 text-xs">
            <div className="flex items-center gap-2 text-amber-800 dark:text-amber-300 font-bold">
              <ShieldCheck size={16} />
              <span>Action Preview: {msg.actionPreview.title}</span>
            </div>
            <div className="space-y-1">
              {msg.actionPreview.targets.map((t: any, idx: number) => (
                <div key={idx} className="flex justify-between p-1.5 rounded-lg bg-white/70 dark:bg-black/30 text-[11px]">
                  <span className="font-semibold">{t.company} — {t.role}</span>
                  <span className="text-emerald-600 font-bold">{t.match} match</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* UI cards if present */}
        {msg.uiCards && msg.uiCards.length > 0 && (
          <div className="w-full space-y-2 pt-1">
            {msg.uiCards.map((card: any, cIdx: number) => (
              <div key={cIdx} className="p-3 rounded-xl border border-app-border bg-app-surface space-y-1 text-xs">
                <div className="flex items-center justify-between font-bold">
                  <span>{card.title}</span>
                  {card.match_score && <span className="text-emerald-600">{card.match_score}% match</span>}
                </div>
                {card.company && <p className="text-[11px] text-app-text-muted">{card.company} · {card.location}</p>}
                {card.action_url && (
                  <Link href={card.action_url} className="inline-flex items-center gap-1 text-purple-600 text-[11px] font-bold hover:underline pt-1">
                    View Details <ArrowRight size={11} />
                  </Link>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Copy button */}
        {!isUser && (
          <button
            onClick={copyText}
            className="flex items-center gap-1 text-[10px] text-app-text-muted opacity-0 group-hover:opacity-100 transition-opacity hover:text-app-text"
          >
            {copied ? <Check size={10} className="text-emerald-500" /> : <Copy size={10} />}
            {copied ? "Copied!" : "Copy"}
          </button>
        )}
      </div>
    </div>
  );
}

export default function MentorPage() {
  const { fullName } = useAuthStore();
  const resumeState = useResumeStore();

  const messages = useGlobalAgentStore((state) => state.messages);
  const addMessage = useGlobalAgentStore((state) => state.addMessage);
  const updateMessage = useGlobalAgentStore((state) => state.updateMessage);
  const clearMessages = useGlobalAgentStore((state) => state.clearMessages);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async (text?: string) => {
    const messageText = text || input.trim();
    if (!messageText || loading) return;

    setInput("");
    setLoading(true);

    // Add user message to global store
    addMessage({
      role: "user",
      content: messageText,
      status: "success",
    });

    // Add pending placeholder for agent
    const agentMsgId = addMessage({
      role: "agent",
      content: "",
      status: "pending",
    });

    try {
      // Build conversation history from global messages
      const history = messages
        .filter((m) => m.status === "success")
        .slice(-10)
        .map((m) => ({
          role: m.role === "user" ? "user" : "assistant",
          content: m.content,
        }));

      const res = await apiService.chatWithCareerAgent({
        message: messageText,
        page_context: {
          pathname: "/candidate/mentor",
          page_name: "AI Mentor",
          active_resume_id: resumeState.activeResume?.id ?? null,
        },
        history,
      });

      updateMessage(agentMsgId, {
        content: res.response || "Task completed successfully.",
        plan: res.plan,
        actionPreview: res.action_preview,
        uiCards: res.ui_cards,
        status: "success",
      });
    } catch (err: any) {
      updateMessage(agentMsgId, {
        content: err.message || "Failed to complete request. Please check your connection.",
        status: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="h-screen flex flex-col bg-app-bg text-app-text font-sans overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 px-4 sm:px-6 py-4 border-b border-app-border bg-app-surface flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-white shadow-md">
            <Bot size={20} />
          </div>
          <div>
            <h1 className="font-bold text-app-text text-base">AI Agent</h1>
          </div>
        </div>
        <button
          onClick={clearMessages}
          className="flex items-center gap-1.5 px-3 py-2 rounded-xl border border-app-border text-xs font-medium text-app-text-muted hover:text-app-text hover:bg-app-bg transition-colors"
        >
          <RefreshCw size={12} /> Clear History
        </button>
      </div>



      {/* Messages */}
      <div className="flex-1 min-h-0 overflow-y-auto px-4 sm:px-6 py-5 space-y-5">
        {messages.length === 0 && (
          <div className="text-center py-10 space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-violet-100 dark:bg-violet-950/40 text-violet-600 mx-auto flex items-center justify-center">
              <Bot size={24} />
            </div>
            <h3 className="text-sm font-bold text-app-text">Hello{fullName ? `, ${fullName.split(" ")[0]}` : ""}!</h3>
            <p className="text-xs text-app-text-muted max-w-sm mx-auto">
              I am your single VidyamargAI Career Agent for the entire platform. How can I help you today?
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}

        {/* Loading indicator */}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 text-white flex items-center justify-center shrink-0">
              <Bot size={15} />
            </div>
            <div className="bg-app-surface border border-app-border px-4 py-3 rounded-2xl rounded-tl-sm flex items-center gap-2">
              <div className="flex gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-1.5 h-1.5 rounded-full bg-violet-500 animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
              <span className="text-xs text-app-text-muted">Analyzing workspace…</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested global quick actions */}
      {messages.length <= 2 && !loading && (
        <div className="flex-shrink-0 px-4 sm:px-6 py-3 border-t border-app-border">
          <p className="text-[11px] text-app-text-muted font-medium mb-2">Global Quick Actions:</p>
          <div className="flex flex-wrap gap-2">
            {GLOBAL_SUGGESTED_PROMPTS.map((p) => {
              const Icon = p.icon;
              return (
                <button
                  key={p.text}
                  onClick={() => sendMessage(p.text)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-app-surface border border-app-border text-xs font-medium text-app-text-muted hover:text-app-text hover:border-purple-300 dark:hover:border-purple-800 transition-all"
                >
                  <Icon size={11} className={p.color} />
                  {p.text}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="flex-shrink-0 px-4 sm:px-6 py-4 border-t border-app-border bg-app-surface">
        <div className="flex items-end gap-3 max-w-4xl mx-auto">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask VidyamargAI Career Agent anything… (Enter to send, Shift+Enter for new line)"
            rows={1}
            className="flex-1 px-4 py-3 rounded-xl border border-app-border bg-app-bg text-sm text-app-text placeholder:text-app-text-muted focus:outline-none focus:ring-2 focus:ring-purple-500/40 resize-none transition-all"
            style={{ minHeight: "44px", maxHeight: "120px" }}
          />
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || loading}
            className="w-11 h-11 rounded-xl bg-purple-600 text-white flex items-center justify-center hover:bg-purple-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
