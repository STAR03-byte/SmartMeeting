from __future__ import annotations

import re
import sys
from pathlib import Path


SOURCE_PATTERN = re.compile(r"^\s*SOURCE\s+([^;]+);\s*$", re.IGNORECASE)


def extract_sources(sql_text: str) -> list[str]:
    entries: list[str] = []
    for line in sql_text.splitlines():
        match = SOURCE_PATTERN.match(line)
        if match:
            entries.append(match.group(1).strip())
    return entries


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    run_all_path = repo_root / "scripts" / "db" / "run_all.sql"
    migrations_dir = repo_root / "database" / "migrations"

    run_all_text = run_all_path.read_text(encoding="utf-8")
    sources = extract_sources(run_all_text)
    migration_sources = [s for s in sources if s.startswith("database/migrations/")]
    migration_files = sorted(path.name for path in migrations_dir.glob("*.sql"))
    expected_sources = [f"database/migrations/{name}" for name in migration_files]

    if migration_sources != expected_sources:
        print("[db-order] run_all.sql migration SOURCES mismatch")
        print(f"[db-order] expected: {expected_sources}")
        print(f"[db-order] actual:   {migration_sources}")
        return 1

    print("[db-order] run_all.sql migration SOURCES match migrations directory")
    return 0


if __name__ == "__main__":
    sys.exit(main())
