import os
import sys
from pathlib import Path
# This suite never loads uploaded credentials or opens an external service.
os.environ.update(SECRET_KEY='test-only-secret-with-at-least-32-characters',
    DATABASE_URL='postgresql://test:test@127.0.0.1:1/test', REDIS_URL='',
    MINIO_ENDPOINT='', SCHEDULER_ENABLED='false', RATE_LIMIT_STORAGE_URI='memory://',
    GEMINI_API_KEY='', NVIDIA_API_KEY='', GROQ_API_KEY='', ADMIN_REGISTRATION_KEY='', HR_SYNC_SECRET='')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.core.database import get_db
from app.models.models import User, Candidate, CandidateProfile, CandidateResume, UserPreference, OTP, UserRefreshToken
from app.core.security import create_access_token, get_password_hash
import main

@pytest.fixture
def environment(monkeypatch, tmp_path):
    from app.core.database import Base
    import app.models
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    db = factory()
    owner = User(email='owner@example.com', full_name='Owner', role='candidate', password_hash=get_password_hash('correct-password'))
    other = User(email='other@example.com', full_name='Other', role='candidate', password_hash=get_password_hash('correct-password'))
    admin = User(email='admin@example.com', full_name='Admin', role='admin', password_hash=get_password_hash('correct-password'))
    db.add_all([owner, other, admin]); db.flush()
    candidate = Candidate(user_id=owner.id)
    second = Candidate(user_id=other.id)
    db.add_all([candidate, second]); db.commit()
    def override_db():
        yield db
    main.app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(main, 'SessionLocal', factory)
    from app.services import storage
    monkeypatch.setattr(storage, 'STORAGE_DIR', tmp_path)
    main.limiter.reset()
    from app.api.helpers import _RESUME_UPLOAD_TIMESTAMPS
    _RESUME_UPLOAD_TIMESTAMPS.clear()
    from app.core.ws import manager
    manager.active_connections.clear()
    # Login's motivational side effect is external to authentication tests.
    from app.agents import learning_os
    monkeypatch.setattr(learning_os, 'trigger_learning_os_agents', lambda *a, **k: None)
    with TestClient(main.app) as client:
        yield client, db, owner, other, admin, candidate, tmp_path
    main.app.dependency_overrides.clear()
    db.close(); engine.dispose()

def headers(user):
    return {'Authorization': 'Bearer ' + create_access_token(user.email, user.role)}
