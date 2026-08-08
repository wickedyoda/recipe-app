from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

router = APIRouter(prefix="/docs", tags=["docs"])

_DOCS_DIR = Path(__file__).resolve().parent.parent.parent


def _read_doc(filename: str) -> str:
    """Read a markdown file from the repo root."""
    file_path = _DOCS_DIR / filename
    if not file_path.is_file():
        raise HTTPException(404, f"{filename} not found")
    return file_path.read_text(encoding="utf-8")


@router.get("/changelog", response_class=PlainTextResponse)
def get_changelog():
    return _read_doc("CHANGELOG.md")


@router.get("/license", response_class=PlainTextResponse)
def get_license():
    # LICENSE has no extension
    file_path = _DOCS_DIR / "LICENSE"
    if not file_path.is_file():
        raise HTTPException(404, "LICENSE not found")
    return file_path.read_text(encoding="utf-8")


@router.get("/privacy", response_class=PlainTextResponse)
def get_privacy():
    return _read_doc("PRIVACY.md")
