#!/usr/bin/env bash
# Refresh local Garmin session (optional) and upload ~/.garminconnect to GitHub Actions secret GARMINTOKENS_B64.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="${GARMIN_TOKENS_SECRET_REPO:-dalarconics/python-garminconnect}"
SECRET_NAME="${GARMIN_TOKENS_SECRET_NAME:-GARMINTOKENS_B64}"
SKIP_REFRESH=0
RUN_COLLECT=0

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Uploads Garmin token files for GitHub Actions (secret: ${SECRET_NAME}).

Options:
  --skip-refresh   Do not run scripts/refresh_garmin_session.py first
  --run-collect    After upload, dispatch coaching-daily-collect.yml on master
  -h, --help       Show this help

Environment:
  GARMIN_TOKENS_SECRET_REPO   GitHub repo (default: ${REPO})
  GARMINTOKENS                  Token directory (default: ~/.garminconnect)

Requires: gh auth login with secret write access on the target repo.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-refresh) SKIP_REFRESH=1; shift ;;
    --run-collect) RUN_COLLECT=1; shift ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: gh CLI not found. Install: https://cli.github.com/" >&2
  exit 1
fi

TOKEN_DIR="${GARMINTOKENS:-$HOME/.garminconnect}"
TOKEN_DIR="$(cd "${TOKEN_DIR/#\~/$HOME}" && pwd)"

if [[ "$SKIP_REFRESH" -eq 0 ]]; then
  echo "Refreshing Garmin session…"
  if ! "$ROOT/.venv/bin/python" "$ROOT/scripts/refresh_garmin_session.py"; then
    echo "ERROR: refresh failed; fix login locally before publishing tokens." >&2
    exit 1
  fi
fi

if [[ ! -d "$TOKEN_DIR" ]] || [[ -z "$(ls -A "$TOKEN_DIR" 2>/dev/null || true)" ]]; then
  echo "ERROR: no token files in $TOKEN_DIR" >&2
  exit 1
fi

echo "Publishing ${SECRET_NAME} to ${REPO}…"
tar czf - -C "$TOKEN_DIR" . | base64 | gh secret set "$SECRET_NAME" --repo "$REPO"
echo "OK: ${SECRET_NAME} updated on ${REPO}"

# Sync tokens to Supabase if credentials exist in env or .env.local
if [[ -f "$ROOT/.env.local" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env.local"
  set +a
fi

if [[ -n "${SUPABASE_URL:-}" ]] && [[ -n "${SUPABASE_SERVICE_ROLE_KEY:-}" ]]; then
  echo "Syncing tokens to Supabase…"
  if "$ROOT/.venv/bin/python" -c 'import sys; sys.path.insert(0, "scripts"); from garmin_auth import persist_tokens_to_supabase; ok = persist_tokens_to_supabase("'"$TOKEN_DIR"'"); sys.exit(0 if ok else 1)'; then
    echo "OK: tokens synced to Supabase"
  else
    echo "WARNING: failed to sync tokens to Supabase" >&2
  fi
fi

if [[ "$RUN_COLLECT" -eq 1 ]]; then
  echo "Dispatching coaching-daily-collect.yml…"
  gh workflow run coaching-daily-collect.yml --repo "$REPO" --ref master
  echo "Workflow started. Check: https://github.com/${REPO}/actions"
fi
