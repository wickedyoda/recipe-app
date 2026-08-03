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
- `yt-dlp` and `whisper` execute external commands. Inputs should be validated and outputs sandboxed in production.
- File uploads are stored under `MEDIA_ROOT`. Ensure this directory is not web-accessible.
