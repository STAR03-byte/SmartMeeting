#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${SMARTMEETING_ENV_FILE:-$ROOT_DIR/backend/.env}"
BACKUP_FILE="${SMARTMEETING_ENV_BACKUP_FILE:-$ROOT_DIR/backend/.env.rollback.backup}"

ensure_env_file() {
  if [[ ! -f "$ENV_FILE" ]]; then
    : > "$ENV_FILE"
  fi
}

backup_env_file() {
  ensure_env_file
  if [[ -f "$ENV_FILE" && ! -f "$BACKUP_FILE" ]]; then
    cp "$ENV_FILE" "$BACKUP_FILE"
  fi
}

set_flag() {
  local key="$1"
  local value="$2"

  ensure_env_file
  python - "$ENV_FILE" "$key" "$value" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3]

lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
pattern = re.compile(rf"^{re.escape(key)}=")
updated = []
found = False

for line in lines:
    if pattern.match(line):
        updated.append(f"{key}={value}")
        found = True
    else:
        updated.append(line)

if not found:
    if updated and updated[-1] != "":
        updated.append("")
    updated.append(f"{key}={value}")

path.write_text("\n".join(updated) + ("\n" if updated else ""), encoding="utf-8")
PY
}

get_flag() {
  local key="$1"
  python - "$ENV_FILE" "$key" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
key = sys.argv[2]
pattern = re.compile(rf"^{re.escape(key)}=(.*)$")

if not path.exists():
    raise SystemExit(1)

for line in path.read_text(encoding="utf-8").splitlines():
    match = pattern.match(line)
    if match:
        print(match.group(1))
        raise SystemExit(0)

raise SystemExit(1)
PY
}

assert_flag() {
  local key="$1"
  local expected="$2"
  local actual

  actual="$(get_flag "$key")"
  if [[ "$actual" != "$expected" ]]; then
    printf 'Flag %s expected %s but found %s\n' "$key" "$expected" "$actual" >&2
    return 1
  fi
}

set_flags() {
  if (( $# % 2 != 0 )); then
    printf 'set_flags requires key/value pairs\n' >&2
    return 1
  fi

  backup_env_file
  while (( $# > 0 )); do
    set_flag "$1" "$2"
    shift 2
  done
}

show_flags() {
  local keys=("$@")
  local key

  for key in "${keys[@]}"; do
    if value="$(get_flag "$key" 2>/dev/null)"; then
      printf '%s=%s\n' "$key" "$value"
    else
      printf '%s=<unset>\n' "$key"
    fi
  done
}

main() {
  case "${1:-}" in
    set)
      shift
      set_flags "$@"
      ;;
    enable)
      shift
      backup_env_file
      while (( $# > 0 )); do
        set_flag "$1" "true"
        shift
      done
      ;;
    disable)
      shift
      backup_env_file
      while (( $# > 0 )); do
        set_flag "$1" "false"
        shift
      done
      ;;
    show)
      shift
      show_flags "$@"
      ;;
    "")
      printf 'Usage: %s {set|enable|disable|show} ...\n' "${0##*/}" >&2
      exit 1
      ;;
    *)
      printf 'Unknown command: %s\n' "$1" >&2
      exit 1
      ;;
  esac
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
