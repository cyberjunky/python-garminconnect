#!/usr/bin/env bash
# Production deploy for apps/web (requires `vercel login` on the machine).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/apps/web"
exec vercel deploy --prod --yes
