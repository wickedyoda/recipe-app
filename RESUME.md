# Recipe App — Resume for Morning Development

Last session: 2026-08-29 04:52 UTC
Branch: first_build (5 commits ahead of origin)
Latest commit: fb8e7d2

## ✅ What's Been Completed

### Security Scan (Complete)
- **TruffleHog**: 0 secrets found (codebase + git history + deployed)
- **Bandit**: 4 LOW only (all false positives — seed password defaults, subprocess with nosec)
- **Ruff security (S rules)**: 16 warnings, all S105/S603/S607 false positives
- **pip-audit**: 0 vulnerabilities
- **Semgrep**: 0 findings

### Fixes Applied
1. Removed unused imports: `logging` (config.py), `Recipe` (settings.py), `os` (auth.py)
2. Removed duplicate items in `CookING_VERBS` set
3. Removed unused metadata dict duplicate construction in `_download_media`
4. Fixed all PLW2901 loop variable overwrite warnings (3 locations)
5. Fixed unused loop variable `model` → `_` in db-diagnostic loop

### Feature Work (from previous session)
- **Recipe Re-process endpoint** (`POST /recipes/{id}/reprocess`): Retries extraction on failed recipes
- **Recipe Dedupe endpoint** (`POST /recipes/dedupe`): Finds/removes duplicate recipes by source_url
- **Blog search for TikTok**: Stage 5 fallback — searches creator's blog ({uploader}.com) for full recipe
- **`_split_recipe_paragraph()`**: Splits long instruction text into individual steps
- **`_is_recipe_step()`**: Filters non-recipe sentences from OCR output
- **`_extract_ingredients_from_instructions()`**: Extracts ingredients mentioned in instruction text
- **Graceful TikTok download**: Metadata extracted first, then video download attempted separately
- **Frontend UI**: Reprocess button (🔄) on recipe detail, Dedupe button (🗂️) in admin panel
- **curl_cffi** added for TikTok browser impersonation
- **DB state**: 182 recipes, 0 orphaned, 0 duplicates

## 🚧 Remaining Issues to Fix

### 1. Blog Search Doesn't Trigger for TikTok (PRIORITY)
- **Location**: `backend/services/ingest.py` ~line 880-920
- **Problem**: Blog search (Stage 5) is blocked because OCR produces garbage ingredients (e.g., "Makes 6 Meals", "kimles") that pass the `if not (parsed.get("ingredients") or parsed.get("instructions"))` check
- **Fix needed**: Move blog search BEFORE the OCR-result return at line ~921. For TikTok URLs, always run blog search regardless of OCR quality
- **Creator blog confirmed working**: `yourbarefootneighbor.com` has recipe at `corndog-casserole/` with JSON-LD

### 2. TikTok Recipes Still Can't Be Processed (PRIORITY)
- **Recipe 65**: `https://www.tiktok.com/t/ZP8nRD8eh/` — creator "yourbarefootneighbor"
- **Recipe 67**: `https://www.tiktok.com/t/ZP8nkqDYe/` — creator "zachcoen"
- **Recipe 68**: `https://www.facebook.com/reel/1501496821453220` — was fixed, has ingredients + instructions (but may need CSS fix for recipe button display)
- **Root cause**: TikTok blocks yt-dlp even with curl_cffi for some videos; OCR produces garbled text from stylized overlays

### 3. DB Health/Diagnostic Cleanup (PRIORITY)
- `db-diag` shows 5 recipes missing ingredients/instructions — these need the blog search fix to trigger reprocessing

## 📋 Morning To-Do List

1. **[Fix] Blog search trigger condition** — Move Stage 5 (blog search) before the OCR-result return in `_extract_recipe_text_from_metadata` so it runs for all TikTok URLs regardless of OCR quality
2. **[Fix] Deploy updated ingest.py** to `100.125.168.30` via docker cp + restart
3. **[Test] Re-process recipe 65** (TikTok yourbarefootneighbor) via `POST /recipes/65/reprocess`
4. **[Test] Re-process recipe 67** (TikTok zachcoen) — expected to still fail (no blog) but verify graceful error message
5. **[Test] Verify blog search** finds `corndog-casserole/` recipe from RSS feed on `yourbarefootneighbor.com`
6. **[Fix] Add `#recipeCategoryFilters` element** — already added but verify CSS/display works
7. **[Fix] Recipe detail click** — verify recipe card click handlers work (was blocked by missing element)
8. **[Deploy] Frontend and backend** together after all fixes
9. **[Run] Final full security scan** to confirm everything is still clean
10. **[Commit] All remaining fixes** with descriptive commit messages

## 🔧 Environment Details

- **Codebase**: `/root/.hermes/recipe-app/` (branch: first_build)
- **Deploy host**: `100.125.168.30` (port 122)
- **SSH key**: `/root/.ssh/id_ed25519_flint4`
- **Backend containers**: `recipe-app-backend-1`, `recipe-app-frontend-1`
- **Deploy path**: `/root/docker/recipe-app/`
- **API**: nginx reverse proxy on port 3000 on recipe host, proxied to backend:8000
- **Admin login**: `traveryates@gmail.com` / `a6e3se2aD@`
- **GitHub**: PAT in `/root/.hermes/profiles/wickedyoda/.env` as `GITHUB_TOKEN`

## 📁 Key Files

- `backend/services/ingest.py` — Recipe extraction pipeline (latest changes)
- `backend/routers/recipes.py` — `/reprocess` and `/dedupe` endpoints
- `backend/routers/settings.py` — `/db-health`, `/db-diag`, `/db-repair` endpoints
- `frontend/src/index.html` — Recipe list, detail view, admin panel with Reprocess/Dedupe buttons
- `Dockerfile.backend` — Has tesseract, ffmpeg, curl_cffi build deps
- `docker-compose.yml` — Local dev compose
