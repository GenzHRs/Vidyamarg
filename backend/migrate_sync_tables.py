"""Explicit HR sync migration. Back up the DB before running this script."""
from app.core.database import engine

if __name__ == "__main__":
    conn = engine.raw_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hr_synced_jobs (
                id SERIAL PRIMARY KEY,
                hr_job_id VARCHAR(100) UNIQUE NOT NULL,
                tenant_slug VARCHAR(100),
                title VARCHAR(255),
                description TEXT,
                company_name VARCHAR(255),
                location VARCHAR(255),
                salary_min FLOAT,
                salary_max FLOAT,
                currency VARCHAR(20),
                employment_type VARCHAR(100),
                location_type VARCHAR(100),
                requirements TEXT,
                skills TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                synced_at TIMESTAMPTZ DEFAULT now(),
                created_at TIMESTAMPTZ DEFAULT now()
            );
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hr_synced_applications (
                id SERIAL PRIMARY KEY,
                hr_application_id VARCHAR(100) UNIQUE NOT NULL,
                candidate_email VARCHAR(320) NOT NULL,
                hr_job_id VARCHAR(100),
                job_title VARCHAR(255),
                current_status VARCHAR(50) DEFAULT 'APPLIED',
                synced_at TIMESTAMPTZ DEFAULT now(),
                created_at TIMESTAMPTZ DEFAULT now()
            );
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hr_application_stages (
                id SERIAL PRIMARY KEY,
                hr_application_id VARCHAR(100) NOT NULL,
                stage_number INTEGER NOT NULL,
                stage_name VARCHAR(100),
                status VARCHAR(30) DEFAULT 'LOCKED',
                score FLOAT,
                feedback TEXT,
                scheduled_at TIMESTAMPTZ,
                completed_at TIMESTAMPTZ,
                synced_at TIMESTAMPTZ DEFAULT now(),
                UNIQUE (hr_application_id, stage_number)
            );
        """)
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_synced_jobs_slug ON hr_synced_jobs(tenant_slug);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_synced_apps_email ON hr_synced_applications(candidate_email);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_synced_stages_appid ON hr_application_stages(hr_application_id);")
        
        conn.commit()
        print("Migration complete!")
        cur.close()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
