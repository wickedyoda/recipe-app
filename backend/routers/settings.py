import gzip
import logging
import os
import shutil
import subprocess  # noqa: S404  # nosec B404 - required for DB backup (mysqldump), admin-only
import tempfile
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, field_validator

from backend.config import settings
from backend.models import Role, User
from backend.services.auth import require_role
from backend.services.email import send_email

router = APIRouter(prefix="/settings", tags=["settings"])


class TestEmailRequest(BaseModel):
    email: str


class SettingsOut(BaseModel):
    media_root: str
    frontend_port: int
    backend_port: int
    smtp_host: Optional[str] = None
    smtp_port: int
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_use_tls: bool
    public_url: Optional[str]
    disk_usage_gb: Optional[float] = None
    disk_total_gb: Optional[str] = None
    disk_used_gb: Optional[str] = None
    disk_free_gb: Optional[str] = None
    guest_login_enabled: bool = True
    guest_email: Optional[str] = None


@router.get("/", response_model=SettingsOut)
def get_settings(_: User = Depends(require_role(Role.admin))):
    media_root = settings.MEDIA_ROOT
    disk_gb = None
    try:
        if os.path.isdir(media_root):
            total = sum(
                f.stat().st_size for f in os.scandir(media_root) if f.is_file()
            )
            disk_gb = round(total / (1024**3), 2)
    except Exception as exc:
        logging.getLogger(__name__).warning("Could not compute disk usage: %s", exc)
    return SettingsOut(
        media_root=media_root,
        frontend_port=settings.FRONTEND_PORT if hasattr(settings, "FRONTEND_PORT") else 3000,
        backend_port=settings.BACKEND_PORT,
        smtp_host=settings.SMTP_HOST or None,
        smtp_port=settings.SMTP_PORT,
        smtp_username=settings.SMTP_USERNAME or None,
        smtp_password=None,  # Never return password in API response (write-only)
        smtp_from_email=settings.SMTP_FROM_EMAIL or None,
        smtp_use_tls=settings.SMTP_USE_TLS,
        public_url=settings.PUBLIC_URL or None,
        disk_usage_gb=disk_gb,
        guest_login_enabled=settings.GUEST_LOGIN_ENABLED,
        guest_email=settings.DEFAULT_GUEST_EMAIL,
    )


class GuestLoginToggle(BaseModel):
    enabled: bool = True


class SmtpSettings(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_use_tls: Optional[bool] = True

    @field_validator("smtp_port")
    @classmethod
    def validate_port(cls, v):
        if v is not None and (v < 1 or v > 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v


@router.post("/guest-login", response_model=dict)
def toggle_guest_login(
    payload: GuestLoginToggle,
    _: User = Depends(require_role(Role.admin)),
):
    enabled = payload.enabled
    _update_env("GUEST_LOGIN_ENABLED", "true" if enabled else "false")
    object.__setattr__(settings, "GUEST_LOGIN_ENABLED", enabled)
    return {"status": "ok", "guest_login_enabled": enabled, "message": "Guest login " + ("enabled" if enabled else "disabled")}


@router.get("/guest-login-enabled", response_model=dict)
def get_guest_login_enabled():
    return {"enabled": settings.GUEST_LOGIN_ENABLED}


@router.get("/storage", response_model=dict)
def get_storage_info(_: User = Depends(require_role(Role.admin))):
    media_root = settings.MEDIA_ROOT
    usage: dict = {"media_root": media_root, "files": 0, "total_bytes": 0, "total_gb": 0}
    try:
        if os.path.isdir(media_root):
            for root, _, files in os.walk(media_root):
                for f in files:
                    fp = os.path.join(root, f)
                    usage["files"] += 1
                    usage["total_bytes"] += os.path.getsize(fp)
            usage["total_gb"] = round(usage["total_bytes"] / (1024**3), 2)
    except Exception:
        usage["error"] = "Unable to read media storage"
    disk = shutil.disk_usage(media_root if os.path.isdir(media_root) else "/")
    usage["disk_total_gb"] = round(disk.total / (1024**3), 2)
    usage["disk_used_gb"] = round(disk.used / (1024**3), 2)
    usage["disk_free_gb"] = round(disk.free / (1024**3), 2)
    return usage


@router.post("/backup", response_model=dict)
def backup_database(_: User = Depends(require_role(Role.admin))):
    """Create a compressed database backup (MySQL dump or SQLite copy), then return a download URL."""
    db_url = settings.DATABASE_URL
    try:
        fd, raw_path = tempfile.mkstemp(suffix=".sql", prefix="recipe_app_backup_")
        os.close(fd)
        backup_path = raw_path + ".gz"
        if db_url.startswith("sqlite"):
            db_path = db_url.replace("sqlite:///", "")
            if not os.path.isfile(db_path):
                raise FileNotFoundError("SQLite database not found")
            shutil.copy2(db_path, raw_path)
        elif "mysql" in db_url:
            parsed = urlparse(db_url)
            user = parsed.username or ""
            password = parsed.password or ""
            host = parsed.hostname or "localhost"
            port = parsed.port or 3306
            db = parsed.path.lstrip("/")
            env = os.environ.copy()
            env["MYSQL_PWD"] = password
            mysqldump = shutil.which("mysqldump") or "mysqldump"
            result = subprocess.run(  # nosec B607,B603 - mysqldump on admin-only backup endpoint
                [mysqldump, f"-h{host}", f"-P{port}", f"-u{user}", db],
                capture_output=True, text=True, env=env
            )
            if result.returncode != 0:
                raise RuntimeError("Database backup failed")
            with open(raw_path, "w") as f:
                f.write(result.stdout)
        else:
            raise ValueError("Unsupported database type")
        # Compress the backup
        with open(raw_path, "rb") as f_in:
            with gzip.open(backup_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.unlink(raw_path)
        file_size = os.path.getsize(backup_path)
        return {
            "status": "ok",
            "backup_path": backup_path,
            "download_url": f"/settings/backup/download?path={backup_path}",
            "size_mb": round(file_size / (1024**2), 2),
        }
    except RuntimeError:
        raise HTTPException(status_code=500, detail="Database backup failed")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Database file not found")
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error during backup")


@router.get("/backup/download", response_class=Response)
def download_backup(
    path: str,
    _: User = Depends(require_role(Role.admin)),
):
    """Download a compressed database backup file."""
    # Security: only allow downloading files from the temp directory
    real_path = os.path.realpath(path)
    tmp_dir = os.path.realpath(tempfile.gettempdir())
    if not real_path.startswith(tmp_dir) or not path.endswith(".sql.gz"):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.isfile(real_path):
        raise HTTPException(status_code=404, detail="Backup file not found")
    filename = os.path.basename(real_path)
    with open(real_path, "rb") as f:
        file_data = f.read()
    return Response(
        content=file_data,
        media_type="application/gzip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _update_env(key: str, value: str):
    """Update or add a key=value pair in the .env file."""
    env_path = ".env"
    lines = []
    found = False
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.strip().startswith(key + "="):
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f"{key}={value}\n")
    with open(env_path, "w") as f:
        f.writelines(lines)


@router.post("/smtp", response_model=dict)
def update_smtp_settings(
    payload: SmtpSettings,
    _: User = Depends(require_role(Role.admin)),
):
    """Update SMTP/email configuration and write to .env file."""
    updates = {}
    if payload.smtp_host is not None:
        updates["SMTP_HOST"] = payload.smtp_host.strip()
        object.__setattr__(settings, "SMTP_HOST", payload.smtp_host.strip())
    if payload.smtp_port is not None:
        updates["SMTP_PORT"] = str(payload.smtp_port)
        object.__setattr__(settings, "SMTP_PORT", payload.smtp_port)
    if payload.smtp_username is not None:
        updates["SMTP_USERNAME"] = payload.smtp_username.strip()
        object.__setattr__(settings, "SMTP_USERNAME", payload.smtp_username.strip())
    if payload.smtp_password is not None:
        updates["SMTP_PASSWORD"] = payload.smtp_password
        object.__setattr__(settings, "SMTP_PASSWORD", payload.smtp_password)
    if payload.smtp_from_email is not None:
        updates["SMTP_FROM_EMAIL"] = payload.smtp_from_email.strip()
        object.__setattr__(settings, "SMTP_FROM_EMAIL", payload.smtp_from_email.strip())
    if payload.smtp_use_tls is not None:
        updates["SMTP_USE_TLS"] = "true" if payload.smtp_use_tls else "false"
        object.__setattr__(settings, "SMTP_USE_TLS", payload.smtp_use_tls)
    for key, value in updates.items():
        _update_env(key, value)
    return {
        "status": "ok",
        "message": "SMTP settings updated. Restart the backend container to apply changes.",
        "smtp_host": settings.SMTP_HOST,
        "smtp_port": settings.SMTP_PORT,
        "smtp_from_email": settings.SMTP_FROM_EMAIL,
        "smtp_use_tls": settings.SMTP_USE_TLS,
    }


@router.post("/smtp/test", response_model=dict)
def test_smtp_settings(
    payload: TestEmailRequest,
    _: User = Depends(require_role(Role.admin)),
):
    """Send a test email to verify SMTP settings are working."""
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        raise HTTPException(status_code=400, detail="SMTP settings are not configured")
    sent = send_email(
        to=payload.email,
        subject="CookieRue SMTP Test",
        body="<h2>✅ SMTP is working!</h2><p>If you received this email, your SMTP configuration is correct.</p><p> — CookieRue</p>",
    )
    if not sent:
        raise HTTPException(status_code=502, detail="Failed to send test email — check SMTP settings and credentials")
    return {"status": "ok", "message": "Test email sent to " + payload.email}
