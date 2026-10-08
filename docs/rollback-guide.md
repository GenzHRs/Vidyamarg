# VidyaMarg AI — Rollback & Disaster Recovery Guide

This guide details emergency rollback procedures, database migration downgrades, and disaster recovery runbooks for VidyaMarg AI.

---

## 1. Principles of Safe Rollbacks

1. **Schema Reversibility**: All Alembic migrations in VidyaMarg AI are bidirectional and contain explicit `upgrade()` and `downgrade()` functions.
2. **Data Preservation**: Never execute destructive rollback operations (e.g. dropping columns or tables with live candidate data) without creating an immediate point-in-time database snapshot.
3. **Container Decoupling**: Database rollbacks and application container rollbacks are executed as distinct steps to avoid racing conditions.

---

## 2. Database Migration Rollback

### Inspect Current Revision
Determine which migration revision is currently active in the database:

```bash
# Docker Compose environment:
docker compose run --rm backend python -m alembic current

# Local Python environment:
python -m alembic current
```

### Rollback by One Revision
To roll back the most recently applied migration revision:

```bash
# Docker Compose:
docker compose run --rm backend python -m alembic downgrade -1

# Local Python:
python -m alembic downgrade -1
```

### Rollback to a Specific Revision
To roll back to a known stable revision ID (e.g., `001_initial_schema`):

```bash
# Docker Compose:
docker compose run --rm backend python -m alembic downgrade 001_initial_schema
```

### Reset to Base (Empty Database Schema)
> ⚠️ **CAUTION**: This drops all managed application tables. Use only in staging or testing environments.

```bash
docker compose run --rm backend python -m alembic downgrade base
```

---

## 3. Application Container Rollback

If a code regression occurs requiring a deployment rollback to a previous version:

1. **Revert Git Release / Tag**:
   ```bash
   git checkout <previous-stable-tag>
   ```

2. **Check Migration Compatibility**:
   Ensure the previous version is compatible with the current schema or apply the matching migration downgrade first:
   ```bash
   docker compose run --rm backend python -m alembic current
   # If schema is ahead of the target release:
   docker compose run --rm backend python -m alembic downgrade <target-revision>
   ```

3. **Rebuild and Restart Containers**:
   ```bash
   docker compose build
   docker compose up -d --remove-orphans
   ```

4. **Verify Health and Readiness**:
   ```bash
   curl -I http://localhost:8000/health
   curl -I http://localhost:8000/ready
   ```

---

## 4. Disaster Recovery Runbook (Restoring Backups)

### PostgreSQL Database Restore
In the event of database corruption or unrecoverable schema state:

1. Stop application traffic to prevent partial writes:
   ```bash
   docker compose stop backend scheduler frontend
   ```

2. Drop and recreate the database:
   ```bash
   docker compose exec postgres dropdb -U vidyamarg vidyamarg
   docker compose exec postgres createdb -U vidyamarg vidyamarg
   ```

3. Restore from the latest compressed snapshot:
   ```bash
   gunzip -c backup_20261004_120000.sql.gz | docker compose exec -T postgres psql -U vidyamarg -d vidyamarg
   ```

4. Verify Alembic schema stamping:
   ```bash
   docker compose run --rm backend python -m alembic current
   ```

5. Restart core services:
   ```bash
   docker compose up -d
   ```

### Storage Volume Restore
Restore uploaded resumes and candidate documents to the storage volume:

```bash
tar -xzvf storage_backup_20261004.tar.gz -C storage/
```
