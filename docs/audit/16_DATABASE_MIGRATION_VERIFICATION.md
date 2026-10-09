# VidyamargAI — Database & Migration Verification

**Audit Date**: October 9, 2026  
**Auditor**: Principal Database Architect  
**Mode**: Read-Only Engine & Schema Inspection  

---

## 1. Engine & Connection Configuration

Located in `backend/app/core/database.py`:
- **Engine Type**: Synchronous SQLAlchemy engine connecting via `psycopg2` for PostgreSQL or SQLite for local/test execution.
- **Connection Pooling**: Uses `NullPool` to prevent idle connection accumulation and stale pool disconnects in serverless/containerized environments.
- **Execution Safeguards**:
  - `statement_timeout = 120000` (120 seconds maximum query execution time).
  - `lock_timeout = 5000` (5 seconds lock acquisition timeout to prevent deadlock freezes).

---

## 2. Migration Architecture & Schema Evolution

### Migration Tooling
- **Current Mechanism**: Python migration runner scripts located in `backend/migrations/` (e.g. `add_resume_snapshot_fields.py`).
- **Alembic Status**: No `alembic/` configuration directory is present. Migrations execute programmatic raw SQL DDL with dialect detection (`sqlite` vs `postgresql`).

### Migration Safety Mechanisms
Inspected in `backend/migrations/add_resume_snapshot_fields.py`:
- `safe_add_column(engine, table, column_name, column_type)`:
  - Queries `PRAGMA table_info` (SQLite) or `information_schema.columns` (PostgreSQL) prior to issuing `ALTER TABLE ADD COLUMN`.
  - Avoids transaction abortion when columns already exist.
- `safe_create_index(engine, table, index_name, columns, unique, where_clause)`:
  - SQLite: Uses `CREATE UNIQUE INDEX IF NOT EXISTS ... WHERE ...`.
  - PostgreSQL: Attempts conditional partial unique index; catches syntax exceptions and falls back gracefully.

---

## 3. Resume & Storage Optimization Models

### `resumes` Table
- Stores Master Resumes and parsed original documents.
- Active resume pointer is tracked directly on the `Candidate` model (`candidate.active_resume_id`) as well as `resumes.is_active`.
- **Finding**: While transactional updates in Python enforce single active resume per candidate (`candidate.active_resume_id = new_resume_id`), adding a PostgreSQL partial unique index `CREATE UNIQUE INDEX uq_candidate_active_resume ON resumes(candidate_id) WHERE is_active = True;` provides strong database-level guarantees. **[Status: PARTIALLY VERIFIED]**

### `resume_optimizations` Table
Contains full structured snapshot and immutability controls:
- `id` (String UUID, Primary Key)
- `candidate_id` (String FK -> `candidates.id`, indexed)
- `master_resume_id` (String FK -> `resumes.id`, indexed)
- `job_id` (String FK -> `jobs.id`, nullable, indexed)
- `application_id` (String FK -> `applications.id`, nullable, indexed)
- `jd_hash` (String, SHA256 of normalized job description)
- `render_mode` (String: `template` or `original_layout`)
- `generated_resume_data` (JSON/TEXT containing full evidence-backed resume payload)
- `is_submitted` (Boolean, default False)
- `is_immutable` (Boolean, default False)
- `submitted_at` (DateTime, timestamp of submission lock)
- `preserved_file_url` (String, storage path to submitted PDF/DOCX)

### Partial Unique Index Verification
```sql
CREATE UNIQUE INDEX IF NOT EXISTS uq_optimization_candidate_resume_jd
ON resume_optimizations (candidate_id, master_resume_id, jd_hash)
WHERE jd_hash IS NOT NULL;
```
- **Behavior**: Ensures that for a given candidate and master resume, an identical job description cannot generate redundant duplicate optimization rows.
- **Verification**: Verified in migration code and covered by tests `test_2_reopening_job_returns_saved_version_without_llm` and `test_8_different_jd_creates_new_version`. **[Status: VERIFIED]**

---

## 4. Legacy Tables & Deprecations

1. **Legacy Tables (22 tables)**: Identified models retained for backwards compatibility (e.g., deprecated telegram scrape logs, legacy feedback tables). No active endpoints write to deprecated legacy models, but schemas remain in metadata.
2. **`datetime.utcnow()` Usage**: SQLAlchemy models utilize `datetime.utcnow` which is deprecated in Python 3.12+ in favor of timezone-aware `datetime.now(timezone.utc)`. Runtime operates without failure, but modernization is recommended before Python 3.13 migration.

---

## 5. Summary Verdict
The database schema and snapshot optimization tables satisfy the architectural requirements. Database-level partial index for `active_resume` and migration standardization to Alembic are recommended improvements prior to large-scale enterprise scaling.
