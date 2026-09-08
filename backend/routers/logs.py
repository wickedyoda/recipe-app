from fastapi import APIRouter, HTTPException, Request
import json

from backend.services.email import send_email

router = APIRouter(prefix="/logs", tags=["logs"])

@router.post("/submit", response_model=dict)
async def submit_logs(request: Request):
    """Email application logs to alerts@tyates.one.

    Expects JSON body: {"subject": "...", "body": "..."}
    The 'subject' from the app is used for the email subject line.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    subject = body.get("subject", "WhiskFul Diag Logs")
    log_content = body.get("body", "")

    html_body = (
        f"<p>Application logs submitted from mobile device:</p>"
        f"<pre style='font-family:monospace;font-size:12px;background:#f5f5f5;padding:12px;border-radius:4px;'>{log_content}</pre>"
    )

    if not send_email("alerts@tyates.one", subject, html_body):
        raise HTTPException(status_code=500, detail="Unable to send logs — SMTP not configured or send failed")

    return {"status": "ok", "message": "Logs emailed to alerts@tyates.one"}