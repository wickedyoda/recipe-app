from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import shutil
import tempfile
from backend.config import settings
from backend.services.auth import get_current_user, require_role
from backend.models import Role

router = APIRouter(prefix="/settings", tags=["settings"])


class HostUpdate(BaseModel):
    host: str


class SettingsOut(BaseModel):
    allowed_hosts: list[str]
    allowed_origins: list[str]
    media_root: str
    frontend_port: int
    backend_port: int
    smtp_host: Optional[str] = None
    smtp_port: int
    smtp_from_email: Optional[str] = None
    smtp_use_tls: bool
    public_url: Optional[str]
    disk_usage_gb: Optional[float] = None


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
    except Exception:
        pass

    return SettingsOut(
        allowed_hosts=settings.ALLOWED_HOSTS_LIST,
        allowed_origins=settings.ALLOWED_ORIGINS_LIST,
        media_root=media_root,
        frontend_port=settings.FRONTEND_PORT if hasattr(settings, "FRONTEND_PORT") else 3000,
        backend_port=settings.BACKEND_PORT,
        smtp_host=settings.SMTP_HOST or None,
        smtp_port=settings.SMTP_PORT,
        smtp_from_email=settings.SMTP_FROM_EMAIL or None,
        smtp_use_tls=settings.SMTP_USE_TLS,
        public_url=settings.PUBLIC_URL or None,
        disk_usage_gb=disk_gb,
    )


@router.post("/allowed-hosts", response_model=dict)
def add_allowed_host(
    payload: HostUpdate,
    _: User = Depends(require_role(Role.admin)),
):
    hosts = settings.ALLOWED_HOSTS_LIST
    if payload.host in hosts:
        return {"status": "ok", "allowed_hosts": hosts, "message": "Host already in list"}
    hosts.append(payload.host)
    new_str = ",".join(hosts)
    # Update the settings object (for runtime use)
    settings.__dict__["_settings__fields_set"] = True
    # Write to .env file
    _update_env("ALLOWED_HOSTS", new_str)
    # Update runtime setting
    object.__setattr__(settings, "ALLOWED_HOSTS", new_str)
    return {"status": "ok", "allowed_hosts": settings.ALLOWED_HOSTS_LIST, "message": f"Added {payload.host}"}


@router.delete("/allowed-hosts/{host}", response_model=dict)
def remove_allowed_host(
    host: str,
    _: User = Depends(require_role(Role.admin)),
):
    hosts = settings.ALLOWED_HOSTS_LIST
    if host not in hosts:
        return {"status": "ok", "allowed_hosts": hosts, "message": "Host not in list"}
    if host in ("localhost", "127.0.0.1", "*"):
        return {"status": "error", "message": "Cannot remove default host"}
    hosts.remove(host)
    new_str = ",".join(hosts)
    _update_env("ALLOWED_HOSTS", new_str)
    object.__setattr__(settings, "ALLOWED_HOSTS", new_str)
    return {"status": "ok", "allowed_hosts": settings.ALLOWED_HOSTS_LIST, "message": f"Removed {host}"}


@router.get("/storage", response_model=dict)
def get_storage_info(_: User = Depends(require_role(Role.admin))):
    media_root = settings.MEDIA_ROOT
    usage = {"media_root": media_root, "files": 0, "total_bytes": 0, "total_gb": 0}
    try:
        if os.path.isdir(media_root):
            for root, dirs, files in os.walk(media_root):
                for f in files:
                    fp = os.path.join(root, f)
                    usage["files"] += 1
                    usage["total_bytes"] += os.path.getsize(fp)
            usage["total_gb"] = round(usage["total_bytes"] / (1024**3), 2)
    except Exception as e:
        usage["error"] = str(e)
    # Also report disk space
    disk = shutil.disk_usage(media_root if os.path.isdir(media_root) else "/")
    usage["disk_total_gb"] = round(disk.total / (1024**3), 2)
    usage["disk_used_gb"] = round(disk.used / (1024**3), 2)
    usage["disk_free_gb"] = round(disk.free / (1024**3), 2)
    return usage


@router.post("/backup", response_model=dict)
def backup_database(_: User = Depends(require_role(Role.admin))):
    """Create a database backup (MySQL dump or SQLite copy)."""
    db_url = settings.DATABASE_URL
    try:
        if db_url.startswith("sqlite"):
            db_path = db_url.replace("sqlite:///", "")
            if not os.path.isfile(db_path):
                raise FileNotFoundError(f"SQLite database not found at {db_path}")
            backup_path = "/tmp/recipe_app_backup.sql"
            shutil.copy2(db_path, backup_path)
        elif "mysql" in db_url:
            import re
            # Parse connection info from DATABASE_URL
            match = re.match(r'mysql\+mysqlconnector://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', db_url)
            if not match:
                raise ValueError("Could not parse MySQL DATABASE_URL")
            user, password, host, port, db = match.groups()
            backup_path = "/tmp/recipe_app_backup.sql"
            import subprocess
            result = subprocess.run(
                ["mysqldump", f"-h{host}", f"-P{port}", f"-u{user}", f"-p{password}", db],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"mysqldump failed: {result.stderr}")
            with open(backup_path, "w") as f:
                f.write(result.stdout)
        else:
            raise ValueError(f"Unsupported database type: {db_url[:10]}")
        file_size = os.path.getsize(backup_path)
        return {
            "status": "ok",
            "backup_path": backup_path,
            "size_bytes": file_size,
            "size_mb": round(file_size / (1024**2), 2),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _update_env(key: str, value: str):
    """Update or add a key=value pair in the .env file."""
    env_path = ".env"
    lines = []
    found = False
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
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
