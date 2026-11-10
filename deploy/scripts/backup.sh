#!/usr/bin/env bash
set -euo pipefail

data_dir="${LUNGTIC_DATA_DIR:-/srv/lungtic-data}"
backup_dir="${LUNGTIC_BACKUP_DIR:-$data_dir/backups}"
database="${LUNGTIC_DATABASE_URL#sqlite:///}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="$backup_dir/$timestamp"

mkdir -p "$target"
chmod 750 "$backup_dir" "$target"
sqlite3 "$database" ".timeout 5000" ".backup '$target/lungtic.sqlite3'"
tar -C "$data_dir" -czf "$target/assets.tar.gz" assets
install -m 600 /etc/lungtic/lungtic.env "$target/lungtic.env"
sha256sum "$target"/* > "$target/SHA256SUMS"
find "$backup_dir" -mindepth 1 -maxdepth 1 -type d -mtime +30 -print0 | xargs -0r rm -rf --
