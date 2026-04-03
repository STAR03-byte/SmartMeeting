#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FEATURE_FLAGS_SH="$ROOT_DIR/scripts/rollback/feature_flags.sh"

if [[ ! -f "$FEATURE_FLAGS_SH" ]]; then
  printf 'Missing feature flag helper: %s\n' "$FEATURE_FLAGS_SH" >&2
  exit 1
fi

source "$FEATURE_FLAGS_SH"

set_flags \
  USE_FASTER_WHISPER false \
  WHISPER_MODEL small \
  WHISPER_DEVICE cpu

assert_flag USE_FASTER_WHISPER false
assert_flag WHISPER_MODEL small
assert_flag WHISPER_DEVICE cpu

printf 'rollback_whisper_upgrade: verified\n'
