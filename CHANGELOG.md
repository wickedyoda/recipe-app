# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project uses modified MIT licensing with attribution to upstream tool owners.

## [0.2.0] - 2026-08-05

### Added
- 5-star recipe rating system with average display and per-user ratings
- 5 color themes: light, dark, dawn, cozy, high-contrast (high contrast)
- Per-user profiles with avatar upload or 10 vegetable avatar selections (125×125px)
- Guest/demo account with read-only access (`is_readonly=1`)
- Admin can enable/disable guest login via System Settings page
- Top navigation bar with text labels (persistent across all pages)
- Admin-only settings page for server config and user management
- Recipe multi-select export
- Recipe and meal plan deletion with cascade delete
- PWA manifest with icons
- Password reset capability for admin to reset user passwords
- `GET /settings/guest-login-enabled` public endpoint
- `POST /settings/guest-login` admin toggle endpoint
- `POST /settings/smtp` admin endpoint for configuring SMTP email settings (writes to .env)
- SMTP configuration fields in `GET /settings/` response (host, port, username, from email, TLS)
- Recipe detail Share button with Web Share API + clipboard fallback
- Compact header navigation with icon buttons + 3-line hamburger dropdown menu
- PWA Android home screen icons (192×192 and 512×512 with `purpose: maskable any`)
- READ-ONLY badge moved below email on its own row in header
- Responsive recipe detail layout: full-screen on mobile, centered modal on desktop
- SMTP configuration UI in settings page with input fields + Save button

### Fixed
- Login name/email case sensitivity (email comparison is now case-insensitive)
- Recipe edit now correctly passes recipe ID (fixed nulling issue)
- XSS vulnerability in `escapeHtml()` — now escapes quotes (`"` and `'`)
- N+1 query optimization in recipe list with batch queries
- Duplicate recipe prevention (name + first 5 words of description)
- Grocery list share/export functionality (blob API preserves auth headers)
- `JSONResponse` import fixed in grocery router
- Recipe detail metadata labels — `.detail-meta-labels` now uses `display:flex` so label/value pairs have proper spacing (prevents "Servings6" run-together)
- Recipe detail ingredient checkboxes — `align-items:flex-start` with `margin-top:2px` for consistent vertical alignment
- `DBIA0415` import-outside-function ruff errors in app.py
- Removed missing `authArea` reference that caused JS error in `loadProfile()`, blocking admin button visibility
- CodeQL workflow restructured into separate job with v4 action (was failing due to v3 deprecation + incorrect init order)

### Security
- Full security scan: Bandit 0 issues, ruff 0 errors, pip-audit 0 vulnerabilities
- Comprehensive SECURITY-SCAN.md report generated with findings from Bandit, pip-audit, Trivy, CodeQL, and manual review
- `try/except/pass` replaced with proper logging in 7 locations
- Subprocess security alerts suppressed with `# nosec` comments for trusted commands
- CSP updated to include `img-src 'self' data: https:`
- Security headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection

### Changed
- Top navigation bar consolidated into a compact single header row centered under the logo with icon buttons and hamburger dropdown menu (☰)

### Removed
- SMS share option from frontend and backend
- JSON file export from recipe multi-select and grocery share
- JSON file import (`POST /recipes/import` endpoint removed)

## [0.1.0] - 2026-08-02

### Added
- Initial public release
- User authentication with `admin` and `user` roles
- Per-user profiles with display name and avatar
- Admin approval flow for new accounts
- Media ingest from TikTok, YouTube, Facebook Reels
- Local video/audio file upload support
- Audio extraction with `ffmpeg`
- Subtitle extraction with `yt-dlp` and Whisper
- MySQL-backed recipe/media storage
- Mobile-first web UI
- Docker Compose stack
- GitHub Packages publish workflow
