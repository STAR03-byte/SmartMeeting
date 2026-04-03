#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FEATURE_FLAGS_SH="$ROOT_DIR/scripts/rollback/feature_flags.sh"

if [[ ! -f "$FEATURE_FLAGS_SH" ]]; then
  printf 'Missing feature flag helper: %s\n' "$FEATURE_FLAGS_SH" >&2
  exit 1
fi

source "$FEATURE_FLAGS_SH"

set_flags ENABLE_FRONTEND_REFACTOR false
assert_flag ENABLE_FRONTEND_REFACTOR false

printf 'rollback_frontend_refactor: verified\n'
