from fastapi import APIRouter, HTTPException

from backend.services.logs import submit_logs_to_email

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("/submit", response_model=dict)
def submit_logs():
    """Email the last 2 hours of application logs to alerts@tyates.one."""
    if not submit_logs_to_email():
        raise HTTPException(status_code=500, detail="Unable to send logs — SMTP not configured or send failed")
    return {"status": "ok", "message": "Logs emailed to alerts@tyates.one"}
