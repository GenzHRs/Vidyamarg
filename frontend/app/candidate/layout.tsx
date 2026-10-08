"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { useResumeStore } from "@/store/resumeStore";
import { useGlobalAgentStore } from "@/store/globalAgentStore";
import Sidebar from "@/components/Sidebar";
import CandidateHeader from "@/components/CandidateHeader";
import AskVidyamargAgent from "@/components/AskVidyamargAgent";

import { AgentActionBridge } from "@/services/agentActionBridge";

export default function CandidateLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const { isAuthenticated, email, initialize } = useAuthStore();
  const fetchActiveResume = useResumeStore((state) => state.fetchActiveResume);
  const [mounted, setMounted] = useState(false);

  // Register router with AgentActionBridge for website control execution
  useEffect(() => {
    AgentActionBridge.registerRouter(router);
    return () => {
      AgentActionBridge.unregisterRouter();
    };
  }, [router]);

  // Global agent panel state — read directly from the shared store.
  const isAgentOpen = useGlobalAgentStore((state) => state.isOpen);
  const toggleAgent = useGlobalAgentStore((state) => state.toggle);
  const closeAgent = useGlobalAgentStore((state) => state.close);
  const setOwnerEmail = useGlobalAgentStore((state) => state.setOwnerEmail);

  useEffect(() => {
    initialize();
    setMounted(true);
  }, [initialize]);

  useEffect(() => {
    if (mounted && isAuthenticated) {
      fetchActiveResume();
    }
  }, [mounted, isAuthenticated, fetchActiveResume]);

  // Scope the persisted conversation to the authenticated user.
  useEffect(() => {
    if (mounted && isAuthenticated && email) {
      setOwnerEmail(email);
    }
  }, [mounted, isAuthenticated, email, setOwnerEmail]);

  useEffect(() => {
    if (mounted && !isAuthenticated) {
      router.push("/");
    }
  }, [mounted, isAuthenticated, router]);

  if (!mounted || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-4 border-t-primary border-muted animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-screen w-full bg-app-bg flex flex-row overflow-hidden relative font-sans transition-colors duration-300">
      <Sidebar portal="candidate" />

      {/* Main content column — min-w-0 prevents it from overflowing the flex container */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden relative">
        <CandidateHeader
          isAgentOpen={isAgentOpen}
          onToggleAgent={toggleAgent}
        />
        <main className="flex-1 min-w-0 min-h-0 overflow-y-auto overflow-x-hidden bg-app-bg text-app-text transition-colors duration-300 font-sans pb-16 sm:pb-0 workspace-container">
          {children}
        </main>
      </div>

      {/* AI Agent panel — always mounted so conversation persists across navigations.
          The panel renders null internally when closed, keeping the mount stable. */}
      <AskVidyamargAgent isOpen={isAgentOpen} onClose={closeAgent} />
    </div>
  );
}
