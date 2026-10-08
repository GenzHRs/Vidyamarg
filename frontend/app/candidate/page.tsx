"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function CandidateRoot() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/candidate/dashboard");
  }, [router]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="w-8 h-8 rounded-full border-4 border-t-blue-500 border-muted animate-spin" />
    </div>
  );
}
