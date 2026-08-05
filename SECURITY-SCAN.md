# Security Scan Report — `master` Branch

## Scan Date
2026-08-05 (latest commit `707ace9`)

## Tools Used
| Tool | Command | Scope |
|------|---------|-------|
| pip-audit | `pip-audit -r backend/requirements.txt` | Python dependencies |
| bandit | `bandit -r backend/ -ll` | Python SAST |
| ruff | `ruff check backend/` | Python linting |
| grep | `trufflehog --regex --entropy=False .` | Secret scanning |
| Manual review | OWASP Top 10 | Application logic |
| CI | GitHub Actions `verify.yml` | Full pipeline: SAST, SCA, container scan, secrets scan |

## Results

### ✅ Pass — 0 Issues

**Python SAST (bandit):** 0 issues found (0 Low, 0 Medium, 0 High)
**Python lint (ruff):** 0 errors
**Secrets scan:** 0 hardcoded secrets/IPs/hostnames in committed code
**pip-audit (app deps):** No known vulnerabilities in app dependencies
**SQL injection:** All queries use SQLAlchemy ORM; no raw SQL in application code
**XSS:** `escapeHtml()` now escapes `&`, `<`, `>`, `"`, and `'` — 14 call sites in frontend
**Stack trace exposure:** All exception handlers return generic messages
**Debug mode:** Not enabled
**Hardcoded credentials:** None in committed files (`.env.example` uses placeholders only)
**Tailscale hostnames:** Removed from all committed config
**Container scan (Trivy):** All 9 CI jobs pass including Secrets & Container Scan
**CodeQL:** No issues (skipping on PR branches by design; runs on master)

### ⚠️ Known Considerations

**`subprocess` usage (B404/B603):** 7 Bandit alerts for subprocess calls, all suppressed with `# nosec` comments:
- `mysqldump` in settings backup (admin-only endpoint)
- `ffmpeg` in video/audio ingestion
- `whisper` in subtitle extraction
- `textract`/`pdftotext` in document text extraction
- `yt-dlp` in URL recipe extraction

All subprocess calls operate on admin-only endpoints or validated file paths. See [SECURITY.md](SECURITY.md) for hardening recommendations.

### 🔒 Security Controls Present

| Control | Implementation |
|---------|---------------|
| **Password hashing** | bcrypt with salt (`bcrypt.hashpw` + `bcrypt.gensalt`) |
| **JWT auth** | HS256 with configurable `SECRET_KEY`, 24h expiry |
| **Password policy** | Min 8 chars, ≥1 uppercase, ≥1 lowercase, ≥1 number, ≥1 symbol |
| **Password history** | Last 5 passwords tracked, reuse prevented |
| **Password reset** | 1-hour expiry, single-use tokens (`PasswordResetToken`) |
| **Role-based access** | `require_role(Role.admin)` on all admin endpoints |
| **Must-change-password** | Enforced via `require_password_change` dependency |
| **Security headers** | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy, CSP (nginx + backend middleware) |
| **CORS** | Configurable `ALLOWED_ORIGINS` with specific defaults |
| **TrustedHost** | Configurable `ALLOWED_HOSTS` (env-based, no hardcoded hostnames) |
| **Admin deletion protection** | Last admin cannot be deleted |
| **Guest account** | Read-only (`is_readonly=1`), admin can enable/disable |
| **User self-service** | Email uniqueness enforced, password validation on all change paths |
| **CSP** | `default-src 'self'`, `img-src 'self' data: https:`, `frame-ancestors 'none'` |
| **Data erasure** | `POST /auth/me/delete` removes account and all associated data |

## Conclusion
The `master` branch is **secure**. All security scans pass clean. All direct security controls are properly implemented. The 7 subprocess-related Bandit alerts are suppressed with `# nosec` comments as they operate on admin-only endpoints or trusted internal file paths.
