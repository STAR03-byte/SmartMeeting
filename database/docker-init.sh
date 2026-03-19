#!/bin/bash
set -e

for f in /docker-entrypoint-initdb.d/migrations/*.sql; do
  echo "Running migration: $f"
  mysql -u root -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE" < "$f"
done

echo "All migrations applied."
