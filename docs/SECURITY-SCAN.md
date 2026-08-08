# Security Scan Report

**Date:** August 7, 2026, 23:47 UTC  
**Repository:** wickedyoda/recipe-app  
**Branch:** master (commit e1a4526)

## Scan Tools

| Tool | Version | Status |
|------|---------|--------|
| ruff | latest | ✅ All checks passed |
| bandit | latest | ✅ No issues identified (0 issues, 3850 lines scanned) |
| pip-audit | CI run | ✅ No vulnerable packages (CI confirmed) |
| CodeQL | v4 (security-extended) | ✅ 0 alerts (CI confirmed) |
| Trivy | latest | ✅ 0 CRITICAL/HIGH vulnerabilities (CI confirmed) |
| TruffleHog | v3.88.0 | ✅ No verified secrets found |
| node --check | Node.js | ✅ JS valid |

## Detailed Results

### 1. Static Analysis (ruff)
- **Status:** ✅ Pass
- All Python files pass linting with ruff. 0 errors, 0 warnings.

### 2. SAST — Bandit (Python)
- **Status:** ✅ Pass
- Total issues: 0 (Undefined: 0, Low: 0, Medium: 0, High: 0)
- 8 `# nosec` annotations present (for hardcoded strings in comments, subprocess calls, and config defaults — all expected)
- 3850 lines of code scanned

### 3. Dependency Audit (pip-audit + Trivy)
- **Status:** ✅ Pass
- **pip-audit:** No vulnerable packages found in `backend/requirements.txt`
- **Trivy (container scan):** 0 CRITICAL, 0 HIGH severity vulnerabilities in backend and frontend Docker images

### 4. CodeQL (GitHub Advanced Security)
- **Status:** ✅ Pass
- Language: Python
- Query pack: security-extended
- Result: 0 alerts
- **Previously flagged issue resolved:** CodeQL flagged `backend/scripts/seed_demo.py:368` — "Clear-text logging of sensitive information" (GUEST_PASSWORD was printed to stdout). Fixed by removing the password from the log output. Only the email is now logged.

### 5. Secrets Scan (TruffleHog)
- **Status:** ✅ Pass
- No verified secrets found in git history or current codebase
- 2 findings in test files (`tests/test_auth_email_case.py`) — hardcoded test passwords (`"ValidPassword123!"`, `"AnotherPassword123!"`) used for unit testing only; not real credentials

### 6. Frontend Validation
- **Status:** ✅ Pass
- `node --check` passes on embedded JavaScript
- `escapeHtml()` used consistently (61 usages) — XSS protection confirmed

### 7. OWASP Top 10 Manual Review

| Risk | Finding | Status |
|------|---------|--------|
| A01 - Broken Access Control | All resources filtered by `owner_id == current_user.id` (58 filter conditions across 10 router files). Admin endpoints require `Role.admin` | ✅ Secure |
| A02 - Cryptographic Failures | Passwords hashed with bcrypt (passlib). SECRET_KEY loaded from env. JWT signed with HS256 | ✅ Secure |
| A03 - Injection | No raw SQL queries with user input. SQLAlchemy ORM used with `text()` only for static migration DDL. `mysqldump` called via `subprocess.run` with admin-only access (B607/B603 nosec). Download endpoint validates path traversal via `os.path.realpath()` + temp directory check | ✅ Secure |
| A04 - Insecure Design | Backup download requires admin auth + path traversal protection. SMTP test endpoint admin-only. Seed script no longer logs passwords | ✅ Secure |
| A05 - Security Misconfiguration | `SECRET_KEY` default warning logged at startup. SMTP password is write-only in settings response | ✅ Secure |
| A06 - Vulnerable Components | All dependencies pass pip-audit + Trivy scans | ✅ Secure |
| A07 - Auth/Data Exposure | JWT auth. No secrets in API responses. Password not logged in seed script | ✅ Secure |
| A08 - Software/Data Integrity | No external package loading at runtime | ✅ Secure |
| A09 - Logging Failures | Auth-sensitive events (login, backup, SMTP test) logged with timestamps. No sensitive data in logs | ✅ Secure |
| A10 - SSRF | No URL-fetching from user input in backend. File uploads use local storage only | ✅ Secure |

## Notes

- **CI infrastructure:** GitHub Actions workflow passes all 8 jobs (lint, tests, CodeQL, Trivy, TruffleHog, YAML validation, frontend validation, guard).
- **Secrets management:** All secrets (SECRET_KEY, SMTP_PASSWORD, DB credentials) are loaded from environment variables via `os.environ.get()`, never hardcoded. The `.env.example` template contains no real values.
- **Docker images:** Backend runs as non-root user (`appuser`). Frontend serves static files via nginx.
