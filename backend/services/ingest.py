import os
import subprocess
import uuid
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Recipe, Cookbook, Store

MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", "/media"))
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
(MEDIA_ROOT / "audio").mkdir(exist_ok=True)
(MEDIA_ROOT / "subtitles").mkdir(exist_ok=True)
(MEDIA_ROOT / "raw").mkdir(exist_ok=True)

def ensure_local_cookbook(db: Session, user_id: int) -> Cookbook:
    cb = db.query(Cookbook).filter(Cookbook.owner_id==user_id, Cookbook.name=="Imported Videos", Cookbook.store==Store.local).first()
    if not cb:
        cb = Cookbook(name="Imported Videos", description="Auto-imported social videos", store=Store.local, owner_id=user_id)
        db.add(cb)
        db.commit()
        db.refresh(cb)
    return cb

def download_media(url: str, user_id: int) -> dict:
    workdir = MEDIA_ROOT / "raw" / f"{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex}"
    workdir.mkdir(parents=True, exist_ok=True)
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
    video = next((p for p in files if p.suffix.lower() in {".mp4",".mkv",".webm",".mov"}), None)
    audio = next((p for p in files if p.suffix.lower() in {".m4a",".mp3",".wav",".aac"}), None)
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
    db = SessionLocal()
    cookbook = ensure_local_cookbook(db, user_id)
    recipe = Recipe(
        title=workdir.name,
        source_url=url,
        source_path=str(video) if video else None,
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
