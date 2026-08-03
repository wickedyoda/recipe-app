#!/bin/bash
set -euo pipefail

REPO_URL="https://github.com/wickedyoda/recipe-app.git"
LOCAL_DIR="${LOCAL_DIR:-$HOME/.hermes/recipe-app}"
PRESERVE_FILES=(docker-compose.yml .env .env.local docker-compose.override.yml)
BRANCH="${BRANCH:-first_build}"

mkdir -p "$LOCAL_DIR"

if [ ! -d "$LOCAL_DIR/.git" ]; then
  echo "[sync] Cloning $REPO_URL -> $LOCAL_DIR"
  git clone "$REPO_URL" "$LOCAL_DIR"
  cd "$LOCAL_DIR"
  git checkout "$BRANCH"
else
  echo "[sync] Updating existing repo in $LOCAL_DIR"
  cd "$LOCAL_DIR"
  git remote set-url origin "$REPO_URL"
  git fetch origin
  git checkout "$BRANCH"
  git pull --no-rebase origin "$BRANCH"
fi

# Preserve local config files
BACKUP_DIR="$(mktemp -d)"
for f in "${PRESERVE_FILES[@]}"; do
  if [ -f "$LOCAL_DIR/$f" ]; then
    echo "[sync] Backing up $f"
    cp "$LOCAL_DIR/$f" "$BACKUP_DIR/$f"
  fi
done

# Checkout the branch to ensure clean state
git checkout "$BRANCH" --
git clean -fd

# Restore preserved files
for f in "${PRESERVE_FILES[@]}"; do
  if [ -f "$BACKUP_DIR/$f" ]; then
    echo "[sync] Restoring $f"
    cp "$BACKUP_DIR/$f" "$LOCAL_DIR/$f"
  fi
done

rm -rf "$BACKUP_DIR"
echo "[sync] Done. Local config files preserved."
