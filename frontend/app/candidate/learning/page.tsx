"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

// "My Learning" redirects to the Skill Lab's My Learning tab
export default function MyLearningPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/candidate/skill-lab");
  }, [router]);
  return (
    <div className="min-h-screen bg-app-bg flex items-center justify-center">
      <div className="w-8 h-8 rounded-full border-4 border-t-blue-500 border-app-border animate-spin" />
    </div>
  );
}
