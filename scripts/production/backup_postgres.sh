#!/usr/bin/env bash
# ==============================================================================
# GQT HRMS — PostgreSQL Database Backup Script
# Automated daily backup with compression, checksums, and retention rotation.
# ==============================================================================
set -euo pipefail

# Configuration defaults (override via environment variables)
BACKUP_DIR="${BACKUP_DIR:-/var/backups/gqt-hrms/postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
TIMESTAMP="$(date +'%Y%m%d_%H%M%S')"
BACKUP_FILENAME="gqt_hrms_db_${TIMESTAMP}.sql.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"
CHECKSUM_PATH="${BACKUP_PATH}.sha256"

# Ensure BACKUP_DIR is safe and not root or empty
if [[ -z "${BACKUP_DIR}" || "${BACKUP_DIR}" == "/" || "${BACKUP_DIR}" == "/home" || "${BACKUP_DIR}" == "/etc" ]]; then
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [ERROR] Unsafe BACKUP_DIR specified: '${BACKUP_DIR}'. Aborting." >&2
    exit 1
fi

# Ensure backup directory exists with strict permissions (owner read/write/exec only)
mkdir -p "${BACKUP_DIR}"
chmod 0700 "${BACKUP_DIR}"

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [INFO] Starting PostgreSQL database backup..."
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [INFO] Target destination: ${BACKUP_PATH}"

# Verify pg_dump is available
if ! command -v pg_dump >/dev/null 2>&1; then
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [ERROR] 'pg_dump' utility not found. Please install postgresql-client." >&2
    exit 1
fi

# Execute pg_dump with gzip compression
# Database connection settings (PGHOST, PGPORT, PGUSER, PGDATABASE, PGPASSWORD) are expected via env or ~/.pgpass
if pg_dump --format=plain --no-owner --no-privileges | gzip -9 > "${BACKUP_PATH}"; then
    chmod 0600 "${BACKUP_PATH}"
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [INFO] Dump completed successfully. Generating SHA-256 checksum..."
    sha256sum "${BACKUP_PATH}" > "${CHECKSUM_PATH}"
    chmod 0600 "${CHECKSUM_PATH}"
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [INFO] Backup verified. SHA-256: $(cat "${CHECKSUM_PATH}")"
else
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [ERROR] pg_dump failed! Removing incomplete backup." >&2
    rm -f "${BACKUP_PATH}"
    exit 1
fi

# Rotate backups older than retention days
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [INFO] Pruning backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -type f \( -name "gqt_hrms_db_*.sql.gz" -o -name "gqt_hrms_db_*.sql.gz.sha256" \) -mtime "+${RETENTION_DAYS}" -exec rm -v {} \;

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [INFO] PostgreSQL backup process finished successfully."

