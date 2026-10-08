# VidyaMarg AI — Known Limitations and System Advisories

This document outlines architectural constraints, external service dependencies, and dependency advisories for VidyaMarg AI.

---

## 1. External AI Providers & Graceful Degradation

### Behavioral Guarantee
- The application will **never invent scores, mock assessments, or fabricate AI mentorship outputs** when external AI providers are unavailable, rate-limited, or misconfigured.
- When an AI service is unavailable:
  - The backend raises `AIProviderUnavailableException` (HTTP 503 Service Unavailable).
  - The frontend displays an explicit error message prompting the user to try again later or contact the administrator.

### Provider Chain
- The unified AI service (`app.services.ai_provider.AIProviderService`) follows an automatic fallback chain:
  `Google Gemini` ➔ `NVIDIA NIM` ➔ `Groq`
- If no provider keys are provided, the system gracefully operates in offline lexical mode for resume parsing and keyword matching, while disabling AI-driven scoring.

---

## 2. Telegram Job Discovery Crawler

- **Authentication**: Telegram crawler functionality requires `TG_API_ID` and `TG_API_HASH` from [my.telegram.org](https://my.telegram.org).
- **Session String**: For containerized or headless environments, provide `TG_SESSION_STRING`. If running interactively, the process will prompt for phone verification and generate a session file.
- **Graceful Failure**: If Telegram credentials are omitted or session authentication fails, the scheduled job logs the failure and terminates the cycle cleanly without interrupting the web API or crashing the scheduler runner.

---

## 3. Dependency Advisories & Vulnerability Status

### Frontend: `braces` Advisory (CVE / GHSA-vfj7-8cjw-p6xm)
- **Status**: An npm audit warning is reported on `braces` via `@next/eslint-plugin-next` -> `eslint-config-next`.
- **Root Cause**: `eslint-config-next` bundles an older transitive dependency on `micromatch`/`fast-glob`. Running `npm audit fix --force` would downgrade `eslint-config-next` to version `14.2.35`, which breaks compatibility with Next.js 16.3.8 and React 19.
- **Remediation**:
  1. An explicit npm override (`"overrides": { "braces": "^3.0.3" }`) is configured in `frontend/package.json`.
  2. The dependency is strictly a development/build-time linter (`devDependency`) and is completely excluded from the production Docker runner container (`node:20-alpine` production stage).
  3. No untrusted user input is passed to glob pattern matching at runtime.

### Python Site-Packages (Local Environment vs Container)
- In local developer workstations, system-wide Python environments may report version warnings across global tools.
- Production deployments use Docker containers built with `backend/requirements-lock.txt`, providing fully pinned, hermetic dependencies tested against Python 3.12.

---

## 4. Storage & Platform Security Constraints

### Windows Unprivileged Symlinks
- On Windows systems where the developer account lacks `SeCreateSymbolicLinkPrivilege`, symlink creation triggers `OSError: symbolic link privilege not held`.
- The storage layer sanitizes all file paths using strict basename checks, directory traversal blocking (`..`, `\`, `/`), and MIME type validation (`application/pdf`, `image/png`, etc.).
- Unit tests gracefully skip the symlink OS-level test when unprivileged, while executing all path traversal test cases.

### Object Storage Fallback Policy
- When `MINIO_ENDPOINT` is configured, uploads target the configured MinIO private bucket. If MinIO is unreachable, the system returns an explicit 502/503 storage error rather than silently writing files to an unprotected local path.
