"use client";

import React from "react";

/**
 * SmoothScroll component
 * Uses native browser smooth scrolling to ensure uninterrupted, highly-responsive mouse wheel,
 * trackpad, and touch scrolling across all browsers without wheel-event hijacking.
 */
export default function SmoothScroll({ children }: { children: React.ReactNode }) {
  return <div className="w-full min-h-screen">{children}</div>;
}
