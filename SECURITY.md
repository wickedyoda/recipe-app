# Security Policy

## Reporting a Vulnerability
If you find a security issue, please do not open a public issue.
Instead, email security@example.com with:
- A description of the issue
- Steps to reproduce
- Potential impact

We will acknowledge within 3 business days and provide a detailed response within 10 business days.

## Supported Versions
| Version | Supported          |
| ------- | ------------------ |
| main    | Yes                |
| older   | No                 |

## Security Best Practices for Contributors
- Never commit secrets, API keys, or credentials.
- Run `make security-check` before pushing.
- Keep dependencies updated; review `pip-audit` and `bandit` output.
- Validate all external inputs, especially file uploads and user-provided URLs.
- Use parameterized queries via SQLAlchemy; avoid raw SQL.
- Follow the principle of least privilege for database access.

## Known Considerations
- `yt-dlp`, `ffmpeg`, `whisper`, and `textract` execute external commands for media processing. Inputs are validated file paths or admin-configured URLs; outputs are sandboxed in temporary directories. See `backend/services/ingest.py` and `backend/services/media_text.py`.
- File uploads are stored under `MEDIA_ROOT`. Ensure this directory is not web-accessible (nginx config restricts access to `/media/static/` only).
- The guest/demo account is read-only (`is_readonly=1`). Admin can disable guest login entirely via `GUEST_LOGIN_ENABLED` env var or the System Settings page.
- JSON file export is disabled — recipe exports are text/markdown only.
