/**
 * VidyamargAI Application Route Registry.
 * Centralized map for platform navigation used by UI and AI Career Agent.
 */
export const APP_ROUTES = {
  dashboard: "/candidate/dashboard",
  resume: "/candidate/resumes",
  jobs: "/candidate/jobs",
  courses: "/candidate/skill-lab",
  mentor: "/candidate/mentor",
  interview: "/candidate/interview",
  applications: "/candidate/applications",
  profile: "/candidate/profile",
  settings: "/candidate/settings",
} as const;

export type AppRouteKey = keyof typeof APP_ROUTES;
