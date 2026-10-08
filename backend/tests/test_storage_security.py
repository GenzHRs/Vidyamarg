import io
import pytest
from app.core.security import create_access_token
from app.models.models import CandidateResume
from app.services.storage import storage_service

def test_resume_upload_size_limit(environment):
    client, db, owner, other, admin, candidate, _ = environment
    token = create_access_token(owner.email, "candidate")
    headers = {"Authorization": f"Bearer {token}"}

    # Generate oversized content (> 5MB)
    oversized = b"%PDF-1.4 " + (b"A" * (5 * 1024 * 1024 + 10))
    file_payload = {"file": ("large_resume.pdf", io.BytesIO(oversized), "application/pdf")}

    response = client.post(
        "/api/v1/candidates/resume",
        headers=headers,
        files=file_payload
    )
    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"].lower()

def test_resume_upload_invalid_mime_type(environment):
    client, db, owner, other, admin, candidate, _ = environment
    token = create_access_token(owner.email, "candidate")
    headers = {"Authorization": f"Bearer {token}"}

    # Text file disguised with .pdf or text/plain
    invalid_payload = {"file": ("malicious.exe", io.BytesIO(b"MZ\x90\x00not a pdf"), "application/octet-stream")}

    response = client.post(
        "/api/v1/candidates/resume",
        headers=headers,
        files=invalid_payload
    )
    assert response.status_code == 400

def test_storage_path_traversal_rejection(environment):
    client, db, owner, other, admin, candidate, _ = environment
    token = create_access_token(owner.email, "candidate")
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt directory traversal attacks
    traversals = [
        "/api/v1/storage/../../etc/passwd",
        "/api/v1/storage/users/..%2f..%2f..%2fsecret.txt",
        "/api/v1/storage/%2e%2e/%2e%2e/test.pdf"
    ]
    for url in traversals:
        resp = client.get(url, headers=headers)
        assert resp.status_code in {400, 404}

def test_unauthorized_storage_access_rejected(environment):
    client, db, owner, other, admin, candidate, _ = environment
    # Store a file
    url = storage_service.upload_file("resumes", "secure_doc.pdf", b"%PDF-1.4 private data", "application/pdf")
    db.add(CandidateResume(candidate_id=candidate.id, resume_url=url))
    db.commit()

    # 1. Unauthenticated request -> 401
    assert client.get(url).status_code == 401

    # 2. Other candidate request -> 404 (does not leak existence)
    other_token = create_access_token(other.email, "candidate")
    assert client.get(url, headers={"Authorization": f"Bearer {other_token}"}).status_code == 404

    # 3. Owner request -> 200 with no-store
    owner_token = create_access_token(owner.email, "candidate")
    owner_resp = client.get(url, headers={"Authorization": f"Bearer {owner_token}"})
    assert owner_resp.status_code == 200
    assert "no-store" in owner_resp.headers.get("cache-control", "").lower()
    assert owner_resp.headers.get("x-content-type-options") == "nosniff"

    # 4. Admin request -> 200 with no-store
    admin_token = create_access_token(admin.email, "admin")
    admin_resp = client.get(url, headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_resp.status_code == 200
