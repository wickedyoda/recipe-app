import os
import re
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from backend.database import SessionLocal
from backend.models import Cookbook, Recipe, Store
from sqlalchemy.orm import Session

MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", "/media"))
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
(MEDIA_ROOT / "audio").mkdir(exist_ok=True)
(MEDIA_ROOT / "subtitles").mkdir(exist_ok=True)
(MEDIA_ROOT / "raw").mkdir(exist_ok=True)

_VALID_SCHEMES = {"http", "https"}
_MAX_URL_LENGTH = 2048
_URL_RE = re.compile(r"^https?://[^\s]+$")


def _sanitize_media_url(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        raise ValueError("url must be a non-empty string")
    if len(url) > _MAX_URL_LENGTH:
        raise ValueError("url exceeds maximum allowed length")
    parsed = urlparse(url)
    if parsed.scheme not in _VALID_SCHEMES:
        raise ValueError("unsupported url scheme")
    if not parsed.netloc:
        raise ValueError("url must include a host")
    if not _URL_RE.match(url):
        raise ValueError("invalid url format")
    return url.strip()


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-1000:] if proc.stderr else "external command failed")


def ensure_local_cookbook(db: Session, user_id: int) -> Cookbook:
    cb = db.query(Cookbook).filter(Cookbook.owner_id==user_id, Cookbook.name=="Imported Recipes", Cookbook.store==Store.local).first()
    if not cb:
        cb = Cookbook(name="Imported Recipes", description="Auto-imported social recipes", store=Store.local, owner_id=user_id)
        db.add(cb)
        db.commit()
        db.refresh(cb)
    return cb


def _download_media(url: str, workdir: Path) -> dict:
    sanitized_url = _sanitize_media_url(url)
    opts = {
        "no_warnings": True,
        "noplaylist": True,
        "outtmpl": str(workdir / "%(id)s.%(ext)s"),
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en"],
        "convertsubtitles": "srt",
        "quiet": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:  # type: ignore[arg-type]
            ydl.download([sanitized_url])
    except Exception:
        raise RuntimeError("media download failed")

    files = list(workdir.iterdir())
    video = next((p for p in files if p.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}), None)
    audio = next((p for p in files if p.suffix.lower() in {".m4a", ".mp3", ".wav", ".aac"}), None)
    subs = sorted([p for p in files if p.suffix.lower() == ".srt"])

    if audio is None and video is not None:
        audio = workdir / "audio.wav"
        _run([
            "ffmpeg", "-y", "-i", str(video),
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(audio)
        ])

    if not subs and audio is not None:
        whisper_available = shutil.which("whisper")
        if whisper_available:
            try:
                _run([
                    whisper_available, str(audio),
                    "--model", os.getenv("WHISPER_MODEL", "tiny"),
                    "--language", "en",
                    "--output_format", "srt",
                    "--output_dir", str(workdir)
                ])
                subs = sorted([p for p in workdir.iterdir() if p.suffix.lower() == ".srt"])
            except Exception:
                pass  # whisper failed, continue without subtitles

    subtitle_path = subs[0] if subs else None
    return {"video": video, "audio": audio, "subtitle": subtitle_path, "workdir": workdir}


def _clean_srt_text(text: str) -> str:
    text = re.sub(r"\d+\n", "", text)
    text = re.sub(r"\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def _normalize_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r'^\s*[-•*]\s*', '', line)
    line = re.sub(r'^\d+\.\s*', '', line)
    return line.strip()


def _is_ingredient_like(line: str) -> bool:
    if not line or len(line) > 220:
        return False
    lower = line.lower()
    if any(lower.startswith(k) for k in ["step ", "instruction", "first", "next", "then", "now", "after"]):
        return False
    return bool(re.search(r'\b\d+(\.\d+)?\b', line) or any(u in lower for u in ['cup', 'tbsp', 'tsp', 'oz', 'gram', 'kg', 'ml', 'l', 'pound', 'lb', 'pinch', 'dash', 'clove', 'slice', 'piece', 'can', 'bunch', 'sprig', 'tablespoon', 'teaspoon', 'gallon', 'quart', 'pint', 'package', 'bottle', 'jar', 'stick', 'sheet', 'scoop']))


def _extract_recipe_from_text(text: str) -> dict:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return {"title": None, "ingredients": None, "instructions": None}

    title = lines[0]
    normalized = [_normalize_line(line) for line in lines[1:] if _normalize_line(line)]
    ingredients: list[str] = []
    instructions: list[str] = []
    section = "ingredients"

    for line in normalized:
        lower = line.lower()
        if lower.startswith(("instruction", "step", "how to", "directions", "method")):
            section = "instructions"
            continue
        if section == "ingredients":
            if _is_ingredient_like(line):
                ingredients.append(line)
            elif len(ingredients) >= 2 and not lower.startswith(("ingredient", "you'll need", "what you need")):
                section = "instructions"
                instructions.append(line)
            elif lower.startswith(("ingredient", "you'll need", "what you need")):
                continue
            else:
                ingredients.append(line)
        elif section == "instructions":
            instructions.append(line)

    return {
        "title": title,
        "ingredients": "\n".join(ingredients) if ingredients else None,
        "instructions": "\n".join(instructions) if instructions else None,
    }


def _extract_from_transcript(transcript_path: Path | None, fallback_audio: Path | None, workdir: Path) -> dict:
    if transcript_path and transcript_path.exists():
        raw_text = _clean_srt_text(transcript_path.read_text(errors="ignore") or "")
        return _extract_recipe_from_text(raw_text)

    if fallback_audio is None or not fallback_audio.exists():
        return {"title": None, "ingredients": None, "instructions": None}

    whisper_available = shutil.which("whisper")
    if not whisper_available:
        return {"title": None, "ingredients": None, "instructions": None}

    try:
        _run([
            whisper_available, str(fallback_audio),
            "--model", os.getenv("WHISPER_MODEL", "tiny"),
            "--language", "en",
            "--output_format", "srt",
            "--output_dir", str(workdir)
        ])
    except Exception:
        return {"title": None, "ingredients": None, "instructions": None}

    subs = sorted([p for p in workdir.iterdir() if p.suffix.lower() == ".srt"])
    if not subs:
        return {"title": None, "ingredients": None, "instructions": None}

    raw_text = _clean_srt_text(subs[0].read_text(errors="ignore") or "")
    return _extract_recipe_from_text(raw_text)


def download_media(url: str, user_id: int) -> dict:
    workdir = MEDIA_ROOT / "raw" / f"{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex}"
    workdir.mkdir(parents=True, exist_ok=True)
    result = _download_media(url, workdir)
    if not result.get("ok") and "error" in result:
        return result

    subtitle_path = result.get("subtitle")
    description = str(subtitle_path) if subtitle_path else None
    db = SessionLocal()
    db.expire_on_commit = False
    try:
        cookbook = ensure_local_cookbook(db, user_id)
        recipe = Recipe(
            title=workdir.name,
            source_url=url,
            source_path=str(result.get("video") or result.get("audio") or ""),
            store=Store.local,
            owner_id=user_id,
            cookbook_id=cookbook.id,
            description=description,
        )
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
    finally:
        db.close()
    return {
        "ok": True,
        "recipe_id": recipe.id,
        "video": str(result.get("video")) if result.get("video") else None,
        "audio": str(result.get("audio")) if result.get("audio") else None,
        "subtitles": str(subtitle_path) if subtitle_path else None,
        "cookbook_id": cookbook.id,
    }


def extract_recipe_from_url(url: str, user_id: int) -> dict:
    workdir = MEDIA_ROOT / "raw" / f"{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex}"
    workdir.mkdir(parents=True, exist_ok=True)
    result = _download_media(url, workdir)
    if not result.get("ok") and "error" in result:
        return result

    parsed = _extract_from_transcript(result.get("subtitle"), result.get("audio"), workdir)
    db = SessionLocal()
    db.expire_on_commit = False
    try:
        cookbook = ensure_local_cookbook(db, user_id)
        recipe = Recipe(
            title=parsed.get("title") or workdir.name,
            description=parsed.get("instructions") or workdir.name,
            ingredients=parsed.get("ingredients"),
            instructions=parsed.get("instructions"),
            source_url=url,
            source_path=str(result.get("video") or result.get("audio") or ""),
            store=Store.local,
            owner_id=user_id,
            cookbook_id=cookbook.id,
        )
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
    finally:
        db.close()
    return {
        "ok": True,
        "recipe_id": recipe.id,
        "title": recipe.title,
        "ingredients": recipe.ingredients,
        "instructions": recipe.instructions,
        "source_url": url,
        "cookbook_id": cookbook.id,
    }


def ingest_upload(file, user_id: int) -> dict:
    suffix = Path(file.filename or "upload").suffix.lower()
    workdir = MEDIA_ROOT / "raw" / f"{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex}"
    workdir.mkdir(parents=True, exist_ok=True)
    dest = workdir / f"upload{suffix}"
    with dest.open("wb") as f:
        f.write(file.file.read())

    video = dest if suffix in {".mp4", ".mkv", ".webm", ".mov"} else None
    audio = dest if suffix in {".m4a", ".mp3", ".wav", ".aac"} else None
    if video:
        audio = workdir / "audio.wav"
        _run([
            "ffmpeg", "-y", "-i", str(video),
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(audio)
        ])
    if not video and not audio:
        return {"ok": False, "error": "Unsupported file type"}

    subs = []
    if audio is not None:
        _run([
            "whisper", str(audio),
            "--model", os.getenv("WHISPER_MODEL", "tiny"),
            "--language", "en",
            "--output_format", "srt",
            "--output_dir", str(workdir)
        ])
        subs = sorted([p for p in workdir.iterdir() if p.suffix.lower() == ".srt"])

    subtitle_path = subs[0] if subs else None
    db = SessionLocal()
    try:
        cookbook = ensure_local_cookbook(db, user_id)
        recipe = Recipe(
            title=workdir.name,
            source_path=str(video or audio),
            store=Store.local,
            owner_id=user_id,
            cookbook_id=cookbook.id,
            description=str(subtitle_path) if subtitle_path else None,
        )
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
    finally:
        db.close()
    return {
        "ok": True,
        "recipe_id": recipe.id,
        "video": str(video) if video else None,
        "audio": str(audio) if audio else None,
        "subtitles": str(subtitle_path) if subtitle_path else None,
        "cookbook_id": cookbook.id,
    }


def extract_recipe_from_upload(file, user_id: int) -> dict:
    suffix = Path(file.filename or "upload").suffix.lower()
    workdir = MEDIA_ROOT / "raw" / f"{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex}"
    workdir.mkdir(parents=True, exist_ok=True)
    dest = workdir / f"upload{suffix}"
    with dest.open("wb") as f:
        f.write(file.file.read())

    video = dest if suffix in {".mp4", ".mkv", ".webm", ".mov"} else None
    audio = dest if suffix in {".m4a", ".mp3", ".wav", ".aac"} else None
    if video:
        audio = workdir / "audio.wav"
        _run([
            "ffmpeg", "-y", "-i", str(video),
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", str(audio)
        ])
    if not video and not audio:
        return {"ok": False, "error": "Unsupported file type"}

    parsed = _extract_from_transcript(None, audio, workdir)
    db = SessionLocal()
    try:
        cookbook = ensure_local_cookbook(db, user_id)
        recipe = Recipe(
            title=parsed.get("title") or workdir.name,
            description=parsed.get("instructions") or workdir.name,
            ingredients=parsed.get("ingredients"),
            instructions=parsed.get("instructions"),
            source_path=str(video or audio),
            store=Store.local,
            owner_id=user_id,
        )
        db.add(recipe)
        db.commit()
        db.refresh(recipe)
    finally:
        db.close()
    return {
        "ok": True,
        "recipe_id": recipe.id,
        "title": recipe.title,
        "ingredients": recipe.ingredients,
        "instructions": recipe.instructions,
        "source_path": str(video or audio),
        "cookbook_id": cookbook.id,
    }
