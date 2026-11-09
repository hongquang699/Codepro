#!/usr/bin/env bash
set -Eeuo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
backup_dir="${CODEPRO_BACKUP_DIR:-$repo_root/backups}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
umask 077
mkdir -p "$backup_dir"

database_file="$backup_dir/database-$timestamp.sql.gz"
files_file="$backup_dir/files-$timestamp.tar.gz"
trap 'rm -f "$database_file" "$files_file"' ERR

cd "$repo_root"
docker compose exec -T postgres sh -c 'exec pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip -c > "$database_file"
tar -czf "$files_file" problem-data contest-data storage
gzip -t "$database_file"
tar -tzf "$files_file" >/dev/null

echo "Backup created: $database_file and $files_file"
