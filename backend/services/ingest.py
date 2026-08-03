import os
import subprocess
import re
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from .database import SessionLocal
from backend.models import Recipe, Cookbook, Store, Tag, RecipeTag

MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", "/media"))
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
(MEDIA_ROOT / "audio").mkdir(exist_ok=True)
(MEDIA_ROOT / "subtitles").mkdir(exist_ok=True)
(MEDIA_ROOT / "raw").mkdir(exist_ok=True)

def ensure_local_cookbook(db: Session, user_id: int) -> Cookbook:
    cb = db.query(Cookbook).filter(Cookbook.owner_id==user_id, Cookbook.name=="Imported Recipes", Cookbook.store==Store.local).first()
    if not cb:
        cb = Cookbook(name="Imported Recipes", description="Auto-imported social recipes", store=Store.local, owner_id=user_id)
        db.add(cb)
        db.commit()
        db.refresh(cb)
    return cb

def _download_media(url: str, workdir: Path) -> dict:
    cmd = [
        "yt-dlp", "--no-warnings", "--no-playlist",
        "-o", str(workdir / "%(id)s.%(ext)s"),
        "--write-subs", "--write-auto-sub",
        "--sub-lang", "en", "--convert-subs", "srt",
        url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return {"ok": False, "error": proc.stderr[-1000:]}

    files = list(workdir.iterdir())
    video = next((p for p in files if p.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}), None)
    audio = next((p for p in files if p.suffix.lower() in {".m4a", ".mp3", ".wav", ".aac"}), None)
    subs = sorted([p for p in files if p.suffix.lower()==".srt"])

    if audio is None and video is not None:
        audio = workdir / "audio.wav"
        subprocess.run([
            "ffmpeg","-y","-i",str(video),
            "-vn","-acodec","pcm_s16le","-ar","16000","-ac","1",str(audio)
        ], capture_output=True, text=True)

    if not subs and audio is not None:
        subprocess.run([
            "whisper", str(audio),
            "--model", os.getenv("WHISPER_MODEL","tiny"),
            "--language", "en",
            "--output_format", "srt",
            "--output_dir", str(workdir)
        ], capture_output=True, text=True)
        subs = sorted([p for p in workdir.iterdir() if p.suffix.lower()==".srt"])

    subtitle_path = subs[0] if subs else None
    return {"video": video, "audio": audio, "subtitle": subtitle_path, "workdir": workdir}

def _clean_srt_text(text: str) -> str:
    text = re.sub(r"\d+\n", "", text)
    text = re.sub(r"\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)

def _extract_recipe_from_text(text: str) -> dict:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return {"title": None, "ingredients": None, "instructions": None}

    title = lines[0]
    ingredients: list[str] = []
    instructions: list[str] = []
    section = "title"

    for line in lines[1:]:
        lower = line.lower()
        if lower.startswith("ingredient") or lower.startswith("you'll need") or lower.startswith("what you need"):
            section = "ingredients"
            continue
        if lower.startswith("instruction") or lower.startswith("step") or lower.startswith("how to") or lower.startswith("directions"):
            section = "instructions"
            continue
        if section == "ingredients":
            ingredients.append(line)
        elif section == "instructions":
            instructions.append(line)

    return {
        "title": title,
        "ingredients": "\n".join(ingredients) if ingredients else None,
        "instructions": "\n".join(instructions) if instructions else None,
    }

def download_media(url: str, user_id: int) -> dict:
    workdir = MEDIA_ROOT / "raw" / f"{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex}"
    workdir.mkdir(parents=True, exist_ok=True)
    result = _download_media(url, workdir)
    if not result.get("ok") and "error" in result:
        return result

    subtitle_path = result.get("subtitle")
    description = str(subtitle_path) if subtitle_path else None
    db = SessionLocal()
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

    subtitle_path = result.get("subtitle")
    if not subtitle_path:
        return {"ok": False, "error": "No subtitles or transcript available"}

    raw_text = _clean_srt_text(subtitle_path.read_text(errors="ignore") or "")
    parsed = _extract_recipe_from_text(raw_text)

    db = SessionLocal()
    cookbook = ensure_local_cookbook(db, user_id)
    recipe = Recipe(
        title=parsed.get("title") or workdir.name,
        description=parsed.get("instructions") or raw_text[:1000],
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
        subprocess.run([
            "ffmpeg","-y","-i",str(video),
            "-vn","-acodec","pcm_s16le","-ar","16000","-ac","1",str(audio)
        ], capture_output=True, text=True)
    if not video and not audio:
        return {"ok": False, "error": "Unsupported file type"}

    subs = []
    if audio is not None:
        subprocess.run([
            "whisper", str(audio),
            "--model", os.getenv("WHISPER_MODEL","tiny"),
            "--language", "en",
            "--output_format", "srt",
            "--output_dir", str(workdir)
        ], capture_output=True, text=True)
        subs = sorted([p for p in workdir.iterdir() if p.suffix.lower()==".srt"])

    subtitle_path = subs[0] if subs else None
    db = SessionLocal()
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
    db.close()
    return {
        "ok": True,
        "recipe_id": recipe.id,
        "video": str(video) if video else None,
        "audio": str(audio) if audio else None,
        "subtitles": str(subtitle_path) if subtitle_path else None,
        "cookbook_id": cookbook.id,
    }
