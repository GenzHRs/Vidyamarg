# VidyamargAI — Database Migration Plan

**Date:** 2026-10-04  
**Author:** Production Engineering Lead  
**Scope:** PostgreSQL & SQLite Alembic Migration Strategy  

---

## 1. Overview & Strategy

VidyamargAI uses SQLAlchemy ORM models mapped to PostgreSQL in production and SQLite in local developer/testing environments. To ensure operational safety and zero-downtime deployments:
1. **No Automatic DDL at Runtime**: The API server (`backend.main:app`) does **not** create or alter tables at startup.
2. **Deterministic Versioning**: All schema changes are tracked via Alembic revision scripts under `backend/alembic/versions/`.
3. **Explicit Operator Commands**: Migrations are run manually or during CI/CD release stages via `alembic upgrade head`.

---

## 2. Migration Revisions Hierarchy

```
[base]
  │
  ▼
001_initial_schema (Creates core tables, job intelligence, MCP models)
  │
  ▼
002_hr_sync_tables (Creates HR synchronization tables & indexes)
  │
  ▼
[head]
```

### Table Breakdown

#### 001_initial_schema:
- **Core Entities**:
  - `users` (Authentication, roles, XP, streaks)
  - `candidates` (Candidate profiles, resume pointers)
  - `candidate_profiles` (Detailed work history, education)
  - `candidate_resumes` (Stored resume objects, file URLs)
  - `notifications` & `email_notifications` (User alerts)
  - `audit_logs` (Security and administrative audit trail)
  - `otps` (Hashed one-time passwords for authentication and password reset)
  - `user_refresh_tokens` (Refresh token hashes and expiry timestamps)
  - `user_preferences` & `user_consents` (Candidate privacy choices)
- **Job Intelligence**:
  - `companies`, `jobs`, `job_sources`
  - `candidate_agents`, `candidate_agent_preferences`, `agent_runs`, `agent_actions`
  - `matches`, `recommendations`, `applications`, `application_events`
  - `interview_preparations`, `skill_gap_analysis`, `career_insights`, `market_intelligence`
  - `resume_versions`, `resume_embeddings`, `candidate_skill_graph`, `candidate_career_graph`
  - `candidate_career_dna`, `career_paths`, `career_opportunities`, `resume_improvements`
  - `career_eligibility_matrix`, `resume_ai_analysis`
- **MCP & Agent Memory**:
  - `agent_activities`, `human_action_items`, `agent_memory`, `vector_memory_chunks`
  - `agent_health`, `mcp_audit_logs`, `dead_letter_jobs`, `circuit_breaker_states`

#### 002_hr_sync_tables:
- `hr_synced_jobs` (Synchronized jobs from HR Agent AI)
- `hr_synced_applications` (Synchronized applications)
- `hr_application_stages` (Stage progression, scores, and interview schedules)

---

## 3. Operational Procedures

### A. Fresh Database Setup
For a newly provisioned PostgreSQL or SQLite database:
1. Ensure `DATABASE_URL` is configured in `.env`.
2. Run the migration to head:
   ```bash
   cd backend
   alembic upgrade head
   ```
3. Verify that all tables and indexes are created:
   ```bash
   python -c "from app.core.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"
   ```

### B. Migration Upgrade
To apply pending migrations:
```bash
cd backend
alembic upgrade head
```
To check current migration revision:
```bash
alembic current
```

### C. Migration Rollback
To roll back the most recent migration:
```bash
cd backend
alembic downgrade -1
```
To roll back to base (empty schema):
```bash
alembic downgrade base
```

### D. Backup and Restore

#### PostgreSQL Backup:
```bash
pg_dump -h localhost -U vidyamarg -d vidyamarg -F c -b -v -f backup_$(date +%Y%m%d_%H%M%S).dump
```

#### PostgreSQL Restore:
```bash
pg_restore -h localhost -U vidyamarg -d vidyamarg -v --clean backup_file.dump
```

#### SQLite Backup:
```bash
cp vidyamarg.db vidyamarg_backup_$(date +%Y%m%d_%H%M%S).db
```

---

## 4. Production Database Compatibility

When adopting Alembic on an existing production database where tables were created previously:
1. Do not re-run DDL on existing tables.
2. Stamp the database with the baseline revision:
   ```bash
   cd backend
   alembic stamp 001_initial_schema
   ```
3. If HR sync tables already exist, stamp to head:
   ```bash
   alembic stamp head
   ```
4. Verify consistency:
   ```bash
   alembic current
   ```
