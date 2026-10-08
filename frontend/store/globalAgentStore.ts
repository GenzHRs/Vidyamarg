/**
 * GlobalAgentStore — Zustand store with user-scoped localStorage persistence.
 *
 * Design constraints:
 * - One source of truth for panel state, unread badge, and conversation history.
 * - Persisted messages survive navigation, refresh, and tab closure.
 * - Storage is scoped to the authenticated user's email to prevent cross-account leakage.
 * - Transient state (isOpen, hasUnread) is always reset on rehydration.
 * - Schema version guards against corrupt or outdated stored data.
 * - Does NOT persist raw resume text, resume files, or credentials.
 */

import { create } from "zustand";
import { persist, createJSONStorage, StorageValue } from "zustand/middleware";

// ─── Schema version — increment when AgentMessage shape changes ───────────────
const STORE_VERSION = 2;
const MAX_PERSISTED_MESSAGES = 50;

// ─── Types ────────────────────────────────────────────────────────────────────

export interface PlanStep {
  id: string;
  label: string;
  status: "pending" | "running" | "completed" | "failed" | "waiting_confirmation";
}

export interface ActionPreview {
  action_id: string;
  action_type: string;
  title: string;
  targets: Array<{ company: string; role: string; match: string }>;
  resume_title: string;
  payload: Record<string, any>;
}

export interface UICard {
  type: "job" | "course" | "interview_launch" | "skill_gaps";
  [key: string]: any;
}

export interface AgentMessage {
  id: string;
  role: "user" | "agent";
  content: string;
  status: "pending" | "success" | "error";
  plan?: PlanStep[];
  actionPreview?: ActionPreview | null;
  uiCards?: UICard[];
  timestamp: string;
}

// ─── Persisted slice (survives storage) ───────────────────────────────────────
interface PersistedState {
  /** Bounded conversation history (capped to MAX_PERSISTED_MESSAGES). */
  messages: AgentMessage[];
  /** Opaque session identifier for the backend, if issued. */
  sessionId: string | null;
  /** Email of the owner of this conversation — used to invalidate on account switch. */
  ownerEmail: string | null;
}

// ─── Full store shape ─────────────────────────────────────────────────────────
interface GlobalAgentState extends PersistedState {
  /** Whether the agent panel is currently open. NOT persisted. */
  isOpen: boolean;
  /** Whether there is an unread agent message while the panel is closed. NOT persisted. */
  hasUnread: boolean;

  // ── Actions ──
  open: () => void;
  close: () => void;
  toggle: () => void;
  setHasUnread: (value: boolean) => void;

  /**
   * Add a new message. Returns the message id.
   */
  addMessage: (msg: Omit<AgentMessage, "id" | "timestamp">) => string;

  /**
   * Patch an existing message by id. Used to upgrade status from pending → success/error,
   * or to attach plan steps / action previews after streaming.
   */
  updateMessage: (id: string, patch: Partial<AgentMessage>) => void;

  /**
   * Remove all messages and reset session identifiers.
   * Also clears the persisted copy in localStorage.
   */
  clearMessages: () => void;

  /**
   * Called on login / user switch. Associates messages with the current user.
   * If the stored owner differs from the supplied email, conversation is wiped.
   */
  setOwnerEmail: (email: string) => void;
}

// ─── Default welcome message factory ─────────────────────────────────────────
function makeWelcomeMessage(): AgentMessage {
  return {
    id: "welcome_init",
    role: "agent",
    content:
      "Hello! I'm your **VidyamargAI Career Agent**.\n\nI work across the whole platform. Ask me to find matching jobs, optimize your resume, map skill gaps, recommend courses, switch themes, or launch an interview — from any page.",
    status: "success",
    timestamp: new Date().toISOString(),
  };
}

// ─── User-scoped localStorage key ────────────────────────────────────────────
const STORAGE_KEY_PREFIX = "vidyamarg_agent_v";

function buildStorageKey(email: string | null): string {
  // Scope by sanitised email so accounts never share storage.
  if (!email) return `${STORAGE_KEY_PREFIX}${STORE_VERSION}_anonymous`;
  const sanitised = email.toLowerCase().replace(/[^a-z0-9]/g, "_");
  return `${STORAGE_KEY_PREFIX}${STORE_VERSION}_${sanitised}`;
}

// ─── Custom storage adapter that supports dynamic keys ────────────────────────
// Zustand persist middleware requires a fixed storage key, but we want per-user keys.
// We use a thin wrapper that reads the current key from the store's own ownerEmail.
let _currentStorageKey = buildStorageKey(null);

const userScopedStorage = {
  getItem: (name: string): string | null => {
    try {
      return localStorage.getItem(_currentStorageKey);
    } catch {
      return null;
    }
  },
  setItem: (name: string, value: string): void => {
    try {
      localStorage.setItem(_currentStorageKey, value);
    } catch {
      // Storage full or unavailable — silently ignore.
    }
  },
  removeItem: (name: string): void => {
    try {
      localStorage.removeItem(_currentStorageKey);
    } catch {}
  },
};

// ─── Store ────────────────────────────────────────────────────────────────────
export const useGlobalAgentStore = create<GlobalAgentState>()(
  persist(
    (set, get) => ({
      // ── Persisted defaults ──
      messages: [makeWelcomeMessage()],
      sessionId: null,
      ownerEmail: null,

      // ── Transient defaults (always reset on rehydration) ──
      isOpen: false,
      hasUnread: false,

      // ── Actions ──
      open: () => set({ isOpen: true, hasUnread: false }),
      close: () => set({ isOpen: false }),
      toggle: () => {
        const next = !get().isOpen;
        set({ isOpen: next, ...(next ? { hasUnread: false } : {}) });
      },

      setHasUnread: (value: boolean) => set({ hasUnread: value }),

      addMessage: (msg) => {
        const id = `${msg.role}_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
        const full: AgentMessage = {
          ...msg,
          id,
          timestamp: new Date().toISOString(),
        };
        set((state) => {
          // Bound history to avoid unbounded localStorage growth.
          const next = [...state.messages, full];
          const bounded =
            next.length > MAX_PERSISTED_MESSAGES
              ? next.slice(next.length - MAX_PERSISTED_MESSAGES)
              : next;
          return { messages: bounded };
        });
        return id;
      },

      updateMessage: (id, patch) => {
        set((state) => ({
          messages: state.messages.map((m) => (m.id === id ? { ...m, ...patch } : m)),
        }));
      },

      clearMessages: () => {
        const email = get().ownerEmail;
        set({
          messages: [makeWelcomeMessage()],
          sessionId: null,
          hasUnread: false,
        });
        // Also purge the persisted copy so a refresh doesn't restore old messages.
        try {
          const key = buildStorageKey(email);
          localStorage.removeItem(key);
        } catch {}
      },

      setOwnerEmail: (email: string) => {
        const current = get().ownerEmail;
        _currentStorageKey = buildStorageKey(email);

        if (current !== null && current !== email) {
          // Different account logged in — wipe conversation immediately.
          set({
            messages: [makeWelcomeMessage()],
            sessionId: null,
            ownerEmail: email,
            isOpen: false,
            hasUnread: false,
          });
          // Also remove the old user's stored data from the new key path
          // (in case it was coincidentally the same key).
          try {
            localStorage.removeItem(_currentStorageKey);
          } catch {}
        } else {
          set({ ownerEmail: email });
          // Attempt to hydrate from the user-scoped key.
          try {
            const raw = localStorage.getItem(_currentStorageKey);
            if (raw) {
              const parsed = JSON.parse(raw);
              const state = parsed?.state;
              if (
                state &&
                typeof state === "object" &&
                Array.isArray(state.messages) &&
                state.messages.length > 0
              ) {
                set({
                  messages: state.messages,
                  sessionId: state.sessionId ?? null,
                  ownerEmail: email,
                  // Reset transient state
                  isOpen: false,
                  hasUnread: false,
                });
              }
            }
          } catch {
            // Corrupt data — ignore and use defaults.
          }
        }
      },
    }),
    {
      name: "global-agent-store", // Used as fallback key by persist middleware.
      storage: createJSONStorage(() => userScopedStorage),

      // Only persist the durable subset of state.
      partialize: (state): PersistedState => ({
        messages: (() => {
          const all = state.messages;
          return all.length > MAX_PERSISTED_MESSAGES
            ? all.slice(all.length - MAX_PERSISTED_MESSAGES)
            : all;
        })(),
        sessionId: state.sessionId,
        ownerEmail: state.ownerEmail,
      }),

      version: STORE_VERSION,

      // Migration: wipe any state from an older schema version.
      migrate: (_persistedState, version) => {
        if (version !== STORE_VERSION) {
          return {
            messages: [makeWelcomeMessage()],
            sessionId: null,
            ownerEmail: null,
          } satisfies PersistedState;
        }
        return _persistedState as PersistedState;
      },

      // After rehydration, always reset transient fields.
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.isOpen = false;
          state.hasUnread = false;
        }
      },
    }
  )
);
