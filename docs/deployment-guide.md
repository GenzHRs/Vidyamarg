# VidyaMarg AI — Production Deployment Guide

This guide covers deployment procedures for **VidyaMarg AI** across local environments, Docker Compose (Windows Docker Desktop and Linux VMs), Staging, and Production infrastructure.

---

## 1. System Requirements & Architecture

VidyaMarg AI consists of five primary components:
1. **Frontend**: Next.js 16 (React 19, Turbopack, App Router) running on port `3000`.
2. **Backend**: FastAPI 0.111 (Python 3.12, Uvicorn, SQLAlchemy 2, Alembic) running on port `8000` (or `8080`).
3. **Database**: PostgreSQL 15+ (Production/Staging) or SQLite (Local Testing).
4. **Cache & Queue**: Redis 7 (Distributed locking, token delay queues, rate limiting).
5. **Scheduler & Discovery Worker**: APScheduler runner running as a single dedicated instance per cluster (profile `discovery`).

---

## 2. Environment Configuration

1. Create `.env` from `.env.example`:
   ```bash
   cp .env.example .env
   ```

2. Generate a cryptographically secure `SECRET_KEY` (minimum 32 characters):
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
   Paste the output into `SECRET_KEY` in `.env`.

3. Configure Database and Cache:
   ```env
   POSTGRES_PASSWORD=your_secure_postgres_password
   DATABASE_URL=postgresql://vidyamarg:your_secure_postgres_password@postgres:5432/vidyamarg
   REDIS_URL=redis://redis:6379/0
   RATE_LIMIT_STORAGE_URI=redis://redis:6379/1
   ```

4. Configure CORS and Origins:
   ```env
   # JSON array or comma-separated list
   CORS_ORIGINS=["https://app.vidyamarg.com","http://localhost:3000"]
   ```

5. AI & External Integration Keys (Optional — system degrades gracefully without them):
   ```env
   GEMINI_API_KEY=AIzaSy...
   NVIDIA_API_KEY=nvapi-...
   GROQ_API_KEY=gsk_...
   ```

---

## 3. Docker Compose Deployment (Recommended)

### Step 1: Build Container Images
```bash
docker compose build
```

### Step 2: Apply Database Migrations
> **IMPORTANT**: In accordance with production security invariants, the backend container does **NOT** auto-generate or modify database tables on boot. Schema upgrades must be explicitly commanded.

Run the pre-configured migration runner:
```bash
docker compose run --rm migrate
```
*(Alternatively: `docker compose run --rm backend python -m alembic upgrade head`)*

If you are stamping an existing database previously created by legacy `create_all`:
```bash
docker compose run --rm backend python -m alembic stamp head
```

### Step 3: Launch Core Services
```bash
docker compose up -d
```
This boots `postgres`, `redis`, `backend`, and `frontend`.

### Step 4: Verify Health and Readiness
Verify that the backend is responding and database tables are verified:
```bash
# Liveness probe
curl -I http://localhost:8000/health
# HTTP/1.1 200 OK

# Readiness probe (verifies database schema readiness)
curl -I http://localhost:8000/ready
# HTTP/1.1 200 OK (returns 503 Service Unavailable if unmigrated)
```

### Step 5: (Optional) Launch Scheduler & Telegram Discovery Worker
Run the background scheduler as a single instance using the `discovery` profile:
```bash
docker compose --profile discovery up -d scheduler
```

---

## 4. Local Host Deployment (Without Docker)

### Backend:
1. Create and activate a Python 3.12 virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set environment variables:
   ```bash
   export SECRET_KEY="your-32-character-or-longer-secret"
   export DATABASE_URL="sqlite:///./vidyamarg.db"
   ```
4. Run migrations:
   ```bash
   python -m alembic upgrade head
   ```
5. Start Uvicorn:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend:
1. Install dependencies:
   ```bash
   cd frontend
   npm ci
   ```
2. Configure `.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
   ```
3. Start development server:
   ```bash
   npm run dev
   ```
   Or build and run production server:
   ```bash
   npm run build
   npm run start
   ```

---

## 5. Reverse Proxy & HTTPS Hardening (Nginx Example)

In production, place an SSL-terminating reverse proxy (e.g. Nginx, Caddy, Cloudflare) in front of the services:

```nginx
server {
    listen 443 ssl http2;
    server_name app.vidyamarg.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/app.vidyamarg.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.vidyamarg.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Frontend routes
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API routes
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSockets
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 6. Backup and Recovery

### PostgreSQL Backups:
```bash
docker compose exec postgres pg_dump -U vidyamarg vidyamarg | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Storage Uploads:
Back up the `uploads` Docker volume or the `/app/storage` directory regularly:
```bash
tar -czvf storage_backup_$(date +%Y%m%d).tar.gz storage/
```
