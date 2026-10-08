/**
 * VidyamargAI Global Agent Tool Registry.
 *
 * Single, unfiltered registry of all candidate platform capabilities.
 * These tools are available to the VidyamargAI Career Agent on EVERY page.
 * Tools are NEVER filtered by current route.
 */

export interface AgentToolDefinition {
  name: string;
  category: "Navigation" | "Resume" | "Jobs" | "Applications" | "Learning" | "Mentor" | "Interview" | "Profile" | "Platform";
  description: string;
  riskLevel: "low" | "high";
}

export const GLOBAL_AGENT_TOOLS: AgentToolDefinition[] = [
  // Navigation
  { name: "navigate_to_page", category: "Navigation", description: "Navigate user to an authorized platform route", riskLevel: "low" },

  // Resume
  { name: "get_active_resume", category: "Resume", description: "Fetch candidate's active primary resume", riskLevel: "low" },
  { name: "analyze_resume", category: "Resume", description: "Perform full ATS analysis and scoring on active resume", riskLevel: "low" },
  { name: "update_resume", category: "Resume", description: "Update sections or content of active resume", riskLevel: "low" },
  { name: "tailor_resume", category: "Resume", description: "Optimize resume keywords for a specific job description", riskLevel: "low" },
  { name: "change_resume_template", category: "Resume", description: "Change visual template of active resume", riskLevel: "low" },

  // Jobs
  { name: "search_jobs", category: "Jobs", description: "Search live job database with location, title, or remote filters", riskLevel: "low" },
  { name: "match_jobs", category: "Jobs", description: "Score and match candidate active profile against job listings", riskLevel: "low" },
  { name: "analyze_job", category: "Jobs", description: "Deep-dive analysis into job description requirements and skill match", riskLevel: "low" },
  { name: "save_job", category: "Jobs", description: "Bookmark or save a job to candidate favorites", riskLevel: "low" },

  // Applications
  { name: "get_applications", category: "Applications", description: "Retrieve candidate application history and status updates", riskLevel: "low" },
  { name: "apply_to_job", category: "Applications", description: "Submit resume application for a job (requires confirmation)", riskLevel: "high" },
  { name: "application_status", category: "Applications", description: "Check current stage of a submitted job application", riskLevel: "low" },

  // Learning
  { name: "search_courses", category: "Learning", description: "Search available skill lab courses and tutorials", riskLevel: "low" },
  { name: "recommend_courses", category: "Learning", description: "Get personalized course recommendations based on candidate skill gaps", riskLevel: "low" },
  { name: "get_learning_progress", category: "Learning", description: "Track completed courses, lessons, and certificates", riskLevel: "low" },

  // Mentor
  { name: "analyze_skill_gaps", category: "Mentor", description: "Evaluate missing skills for candidate's target career role", riskLevel: "low" },
  { name: "create_learning_plan", category: "Mentor", description: "Generate structured multi-week study roadmap", riskLevel: "low" },
  { name: "career_guidance", category: "Mentor", description: "Provide career path planning, salary insights, and role advice", riskLevel: "low" },

  // Interview
  { name: "prepare_interview", category: "Interview", description: "Initialize tailored technical or behavioral mock interview session", riskLevel: "low" },
  { name: "generate_questions", category: "Interview", description: "Generate role-specific interview practice questions and answers", riskLevel: "low" },
  { name: "get_interview_history", category: "Interview", description: "Fetch past interview attempt scores and AI feedback reports", riskLevel: "low" },

  // Profile
  { name: "get_profile", category: "Profile", description: "Fetch candidate career profile, target role, and preferences", riskLevel: "low" },
  { name: "update_profile", category: "Profile", description: "Update target role, career goals, or skills list", riskLevel: "low" },

  // Platform
  { name: "change_theme", category: "Platform", description: "Switch interface theme between light, dark, and system", riskLevel: "low" },
  { name: "get_notifications", category: "Platform", description: "Retrieve recent system notifications and alerts", riskLevel: "low" },
];
