#!/usr/bin/env bash
# ==============================================================================
# GQT HRMS — Private Media Storage Backup Script
# Archives private deliverable assets and documents with checksums & retention.
# ==============================================================================
set -euo pipefail

# Configuration defaults (override via environment variables)
SOURCE_MEDIA_DIR="${SOURCE_MEDIA_DIR:-/srv/gqt-hrms/media/private}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/gqt-hrms/media}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
TIMESTAMP="$(date +'%Y%m%d_%H%M%S')"
BACKUP_FILENAME="gqt_hrms_private_media_${TIMESTAMP}.tar.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"
CHECKSUM_PATH="${BACKUP_PATH}.sha256"

# Ensure BACKUP_DIR is safe and not root or empty
if [[ -z "${BACKUP_DIR}" || "${BACKUP_DIR}" == "/" || "${BACKUP_DIR}" == "/home" || "${BACKUP_DIR}" == "/etc" ]]; then
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [ERROR] Unsafe BACKUP_DIR specified: '${BACKUP_DIR}'. Aborting." >&2
    exit 1
fi

# Ensure source media directory exists
if [[ ! -d "${SOURCE_MEDIA_DIR}" ]]; then
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [WARNING] Source media directory '${SOURCE_MEDIA_DIR}' does not exist or is empty. Creating directory if absent."
    mkdir -p "${SOURCE_MEDIA_DIR}"
fi

# Ensure backup directory exists with strict permissions
mkdir -p "${BACKUP_DIR}"
chmod 0700 "${BACKUP_DIR}"

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [INFO] Starting Private Media archive..."
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [INFO] Source: ${SOURCE_MEDIA_DIR}"
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [INFO] Destination: ${BACKUP_PATH}"

# Create compressed tarball
PARENT_DIR="$(dirname "${SOURCE_MEDIA_DIR}")"
BASE_DIR="$(basename "${SOURCE_MEDIA_DIR}")"

if tar -czf "${BACKUP_PATH}" -C "${PARENT_DIR}" "${BASE_DIR}"; then
    chmod 0600 "${BACKUP_PATH}"
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [INFO] Tarball created successfully. Generating SHA-256 checksum..."
    sha256sum "${BACKUP_PATH}" > "${CHECKSUM_PATH}"
    chmod 0600 "${CHECKSUM_PATH}"
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [INFO] Media backup verified. SHA-256: $(cat "${CHECKSUM_PATH}")"
else
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [ERROR] Media archiving failed! Removing partial archive." >&2
    rm -f "${BACKUP_PATH}"
    exit 1
fi

# Rotate media backups older than retention days
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [INFO] Pruning media archives older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -type f \( -name "gqt_hrms_private_media_*.tar.gz" -o -name "gqt_hrms_private_media_*.tar.gz.sha256" \) -mtime "+${RETENTION_DAYS}" -exec rm -v {} \;

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] [INFO] Private Media backup process finished successfully."

