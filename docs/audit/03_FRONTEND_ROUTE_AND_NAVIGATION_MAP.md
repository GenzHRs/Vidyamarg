# Complete Frontend Route and Navigation Map

## 1. Candidate Application Routes

| Route | Page File | Purpose & Status | Backend API Calls |
| :--- | :--- | :--- | :--- |
| `/candidate/dashboard` | `app/candidate/dashboard/page.tsx` | Main candidate hub, application metrics, quick actions | `GET /api/v1/user-stats`, `GET /api/v1/resumes/active` |
| `/candidate/resumes` | `app/candidate/resumes/page.tsx` | Resume Center repository (Master Resume + Derived) | `GET /api/v1/resumes`, `POST /api/v1/resumes/upload` |
| `/candidate/resumes/tailor/[resumeId]` | `app/candidate/resumes/tailor/[resumeId]/page.tsx` | **Tailor Studio**: Mode A/B JD optimization, diffs, approval | `POST /api/v1/resume/optimize`, `GET /download/pdf`, `POST /approve` |
| `/candidate/resumes/templates` | `app/candidate/resumes/templates/page.tsx` | 15 ATS LaTeX/ReportLab template gallery | `GET /api/v1/resume-templates` |
| `/candidate/jobs` | `app/candidate/jobs/page.tsx` | Recommended jobs, skill matching, JD inspection | `GET /api/v1/jobs/recommended`, `POST /jobs/{id}/react` |
| `/candidate/job-agent` | `app/candidate/job-agent/page.tsx` | Autonomous AI Job Agent monitor and controls | `GET /api/v1/job-agent/status`, `POST /job-agent/run` |
| `/candidate/applications` | `app/candidate/applications/page.tsx` | My Applications tracker & Kanban pipeline | `GET /api/v1/job-agent/applications`, `PATCH /applications/{id}` |
| `/candidate/interview` | `app/candidate/interview/page.tsx` | Job-specific interview preparation grounded in resume | `GET /api/v1/job-agent/interview-prep/{jobId}` |
| `/candidate/interview-history`| `app/candidate/interview-history/page.tsx`| Past interview session analytics & question history | `GET /api/v1/interview-history` |
| `/candidate/learning` | `app/candidate/learning/page.tsx` | Learning OS recommendations & skill gap courses | `GET /api/v1/learning/courses`, `POST /learning/enroll` |
| `/candidate/skill-lab` | `app/candidate/skill-lab/page.tsx` | Interactive assessments & code challenges | `GET /api/v1/skill-lab/challenges` |
| `/candidate/mentor` | `app/candidate/mentor/page.tsx` | AI Career Mentor live copilot chat | `POST /api/v1/ai-mentor/chat`, `GET /ai-mentor/sessions` |
| `/candidate/profile` | `app/candidate/profile/page.tsx` | Candidate Profile (Target roles, verified skills, 1-col projects) | `GET /api/v1/candidates/profile`, `PUT /candidates/profile` |
| `/candidate/notifications`| `app/candidate/notifications/page.tsx`| Agent match notifications & application alerts | `GET /api/v1/notifications`, `PUT /notifications/{id}/read` |
| `/candidate/settings` | `app/candidate/settings/page.tsx` | Password reset, security, account preferences | `PUT /api/v1/users/me/preferences` |

---

## 2. Authentication & Admin Routes

| Route | Page File | Purpose & Status | Backend API Calls |
| :--- | :--- | :--- | :--- |
| `/login` | `app/login/page.tsx` | Candidate & User login | `POST /api/v1/auth/login` |
| `/signup` | `app/signup/page.tsx` | New candidate registration | `POST /api/v1/auth/signup` |
| `/admin-login` | `app/admin-login/page.tsx` | Admin & HR portal authentication | `POST /api/v1/auth/login` |
| `/admin` | `app/admin/page.tsx` | Administrative dashboard | `GET /api/v1/admin/stats` |
| `/admin/candidates` | `app/admin/candidates/page.tsx` | Candidate pool browser for recruiters | `GET /api/v1/admin/candidates` |
| `/admin/courses` | `app/admin/courses/page.tsx` | Course curriculum manager | `GET /api/v1/admin/courses` |
