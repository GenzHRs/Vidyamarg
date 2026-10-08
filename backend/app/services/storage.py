"""Authenticated API object references with contained local or MinIO storage."""
import io
import logging
from pathlib import Path, PurePosixPath
from urllib.parse import quote
from app.core.config import settings

logger = logging.getLogger(__name__)
STORAGE_DIR = Path(settings.STORAGE_DIR).resolve()
MAX_FILE_SIZE = 50 * 1024 * 1024
ALLOWED_MIME_TYPES = {"application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                      "image/jpeg", "image/png", "image/webp", "image/gif", "video/mp4", "video/webm",
                      "audio/mpeg", "audio/wav", "audio/webm", "text/plain", "text/markdown", "application/json",
                      "application/x-tex", "text/x-tex"}

def get_user_folder_name(user):
    name = getattr(user, "full_name", None) or (getattr(user, "email", "").split("@")[0]) or "user"
    name = "".join(c if c.isalnum() or c in (" ", "_", "-") else "" for c in name).strip().replace(" ", "_") or "user"
    return f"{name}_{user.id}"

def safe_object_path(folder, filename):
    if not filename or "/" in filename or "\\" in filename:
        raise ValueError("Invalid object filename")
    raw = f"{folder}/{filename}" if folder else filename
    parts = raw.split("/")
    if any(x in {"", ".", ".."} for x in parts) or "\\" in raw or any(ord(c) < 32 for c in raw):
        raise ValueError("Invalid object path")
    path = PurePosixPath(raw)
    if path.is_absolute():
        raise ValueError("Invalid object path")
    target = (STORAGE_DIR / path).resolve()
    if not target.is_relative_to(STORAGE_DIR.resolve()):
        raise ValueError("Object path escapes storage root")
    return path.as_posix(), target

class StorageService:
    def __init__(self):
        self.use_minio = bool(settings.MINIO_ENDPOINT)
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from minio import Minio
            import urllib3
            self._client = Minio(settings.MINIO_ENDPOINT, access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY, secure=settings.MINIO_SECURE, region=settings.MINIO_REGION,
                http_client=urllib3.PoolManager(timeout=urllib3.Timeout(connect=3, read=20), retries=1))
        return self._client

    def validate_upload(self, content, mime_type=None):
        if len(content) > MAX_FILE_SIZE:
            raise ValueError("File exceeds the 50MB limit")
        if mime_type and mime_type not in ALLOWED_MIME_TYPES:
            raise ValueError("Unsupported MIME type")

    def upload_file(self, folder, filename, content, mime_type=None):
        self.validate_upload(content, mime_type)
        key, target = safe_object_path(folder, filename)
        if self.use_minio:
            self.client.put_object(settings.MINIO_BUCKET, key, io.BytesIO(content), len(content), content_type=mime_type or "application/octet-stream")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        return "/api/v1/storage/" + quote(key, safe="/")

    def get_presigned_url(self, folder, filename, expires_hours=1):
        # Keep the public method name for compatibility; API checks auth on each read.
        key, _ = safe_object_path(folder, filename)
        return "/api/v1/storage/" + quote(key, safe="/")

    def get_file_content(self, folder, filename):
        key, target = safe_object_path(folder, filename)
        if self.use_minio:
            from minio.error import S3Error
            try:
                response = self.client.get_object(settings.MINIO_BUCKET, key)
            except S3Error as exc:
                if exc.code in {"NoSuchKey", "NoSuchObject"}:
                    return b""
                raise
            try:
                return response.read()
            finally:
                response.close()
                response.release_conn()
        return target.read_bytes() if target.is_file() else b""

    def delete_file(self, folder, filename):
        key, target = safe_object_path(folder, filename)
        if self.use_minio:
            self.client.remove_object(settings.MINIO_BUCKET, key)
        else:
            target.unlink(missing_ok=True)

storage_service = StorageService()
