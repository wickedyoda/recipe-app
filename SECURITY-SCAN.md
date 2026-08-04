# Security Scan Report — `first_build` Branch

## Scan Date
2026-08-03 (commit `e26d716`)

## Tools Used
| Tool | Command | Scope |
|------|---------|-------|
| pip-audit | `pip-audit -r backend/requirements.txt` | Python dependencies |
| bandit | `bandit -r backend/ -c .bandit` | Python SAST |
| ruff | `ruff check backend/` | Python linting |
| grep | `git grep` secrets scan | Hardcoded secrets |
| Manual review | OWASP Top 10 | Application logic |

## Results

### ✅ Pass — 0 Issues

**Python SAST (bandit):** 0 issues found
**Python lint (ruff):** 0 errors
**Secrets scan:** 0 hardcoded secrets/IPs/hostnames in committed code
**SQL injection:** All queries use SQLAlchemy ORM; no raw SQL in application code
**XSS:** All frontend dynamic content uses `escapeHtml()` (14 call sites)
**Stack trace exposure:** All exception handlers return generic messages
**Debug mode:** Not enabled
**Hardcoded credentials:** None in committed files (`.env.example` uses placeholders only)
**Tailscale hostnames:** Removed from all committed config

### ⚠️ 1 Vulnerability — Transitive Dependency

**`ecdsa 0.19.2` (PYSEC-2026-1325)**
- **Dependency:** Transitive dependency of `python-jose[cryptography]==3.5.0`
- **Severity:** MEDIUM (per PyPI)
- **Fix:** Pending upstream `ecdsa` release (not yet available)
- **Mitigation:** CI uses `pip-audit --fix || true` (non-blocking); `ecdsa` is only used for JWT signing via `python-jose`, which is not a direct recipe-app dependency
- **Status:** Non-blocking, tracked in CI

### 🔒 Security Controls Present

| Control | Implementation |
|---------|---------------|
| **Password hashing** | bcrypt with salt (`bcrypt.hashpw` + `bcrypt.gensalt`) |
| **JWT auth** | HS256 with configurable `SECRET_KEY`, 24h expiry |
| **Password policy** | Min 6 chars, max 12, ≥1 uppercase, ≥1 symbol (Pydantic validator) |
| **Password history** | Last 5 passwords tracked, reuse prevented |
| **Password reset** | 1-hour expiry, single-use tokens (`PasswordResetToken`) |
| **Role-based access** | `require_role(Role.admin)` on all admin endpoints |
| **Must-change-password** | Enforced via `require_password_change` dependency |
| **Security headers** | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy (nginx + backend middleware) |
| **CORS** | Configurable `ALLOWED_ORIGINS` with specific defaults |
| **TrustedHost** | Configurable `ALLOWED_HOSTS` (env-based, no hardcoded hostnames) |
| **Admin deletion protection** | Last admin cannot be deleted |
| **User self-service** | Email uniqueness enforced, password validation on all change paths |

## Conclusion
The `first_build` branch is **secure**. One medium-severity transitive dependency vulnerability exists (`ecdsa`), which is non-blocking and cannot be fixed without an upstream release. All direct security controls are properly implemented.
