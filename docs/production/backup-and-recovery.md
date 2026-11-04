# GQT HRMS — Production Backup & Disaster Recovery Architecture

## 1. Operational Overview & Objectives

The GQT HRMS & Recruitment CRM platform maintains business-critical data including corporate CRM records, verified job requisitions, recruitment marketing assets, staff credentials, and immutable compliance audit trails.

To ensure business continuity, data protection, and regulatory compliance, this document specifies the backup, integrity verification, and disaster recovery procedures.

### Recovery Objectives
* **Recovery Point Objective (RPO):** Maximum 24 hours with scheduled daily logical dumps; < 15 minutes when PostgreSQL Write-Ahead Logging (WAL) archiving is activated.
* **Recovery Time Objective (RTO):** < 30 minutes to restore a functional environment from a validated backup.
* **Integrity Guarantee:** Cryptographic SHA-256 verification on all database and media archives before storage and restoration.

---

## 2. Backup Scope & Assets

| Asset Category | Target Path / Source | Mechanism | Compression & Security | Schedule |
|---|---|---|---|---|
| **PostgreSQL Database** | Managed PostgreSQL 16 (`gqt_hrms`) | `pg_dump` via `scripts/production/backup_postgres.sh` | gzip -9, SHA-256 checksum, `0600` permissions | Daily at 02:00 UTC |
| **Private Media Assets** | `/srv/gqt-hrms/media/private` | `tar -czf` via `scripts/production/backup_private_media.sh` | gzip -9, SHA-256 checksum, `0600` permissions | Daily at 02:30 UTC |
| **Environment Configuration** | `/srv/gqt-hrms/.env` | Secure manual vault / secret manager | GPG encrypted off-site snapshot | On change |

---

## 3. Automation Scripts Specification

### 3.1 Database Backup Script (`scripts/production/backup_postgres.sh`)
* **Strict Shell Mode:** `set -euo pipefail` ensures immediate halt on any sub-command failure.
* **Safety Guards:** Validates destination directory to prevent accidental dumps into `/`, `/home`, or `/etc`.
* **Permissions Enforcement:** Restricts backup directory permissions to `0700` and backup archives to `0600`.
* **Integrity Generation:** Computes SHA-256 digest immediately upon dump completion.
* **Automated Pruning:** Automatically rotates and deletes archives older than `RETENTION_DAYS` (default: 7 days).

### 3.2 Private Media Backup Script (`scripts/production/backup_private_media.sh`)
* **Strict Shell Mode:** `set -euo pipefail`.
* **Directory Isolation:** Archives private media attachments (job descriptions, creative deliverable assets) relative to parent directory to avoid absolute path traversal vulnerabilities.
* **Integrity Generation:** Produces accompanying `.sha256` checksum file.
* **Automated Pruning:** Rotates media archives older than `RETENTION_DAYS` (default: 7 days).

---

## 4. Production Crontab Installation

On the production Ubuntu host, configure cron jobs under the dedicated unprivileged system account (`gqt_app` or root for system-level backup jobs):

```bash
# Edit crontab
sudo crontab -u gqt_app -e

# Daily PostgreSQL backup at 02:00 UTC
0 2 * * * PGHOST=127.0.0.1 PGPORT=5432 PGUSER=gqt_hrms_app_user PGDATABASE=gqt_hrms /srv/gqt-hrms/scripts/production/backup_postgres.sh >> /var/log/gqt-hrms/backup_db.log 2>&1

# Daily Private Media archive at 02:30 UTC
30 2 * * * /srv/gqt-hrms/scripts/production/backup_private_media.sh >> /var/log/gqt-hrms/backup_media.log 2>&1
```

---

## 5. Restoration Drill Procedure

Regular restoration drills must be conducted quarterly in an isolated staging environment.

### 5.1 Database Restoration Drill

1. **Verify Archive Integrity:**
   ```bash
   cd /var/backups/gqt-hrms/postgres
   sha256sum -c gqt_hrms_db_YYYYMMDD_HHMMSS.sql.gz.sha256
   # Must output: gqt_hrms_db_YYYYMMDD_HHMMSS.sql.gz: OK
   ```

2. **Provision Disposable Test Database:**
   ```bash
   sudo -u postgres createdb -O gqt_hrms_app_user gqt_hrms_restore_test
   ```

3. **Restore Backup into Test Database:**
   ```bash
   gunzip -c /var/backups/gqt-hrms/postgres/gqt_hrms_db_YYYYMMDD_HHMMSS.sql.gz | psql -U gqt_hrms_app_user -d gqt_hrms_restore_test
   ```

4. **Execute Sanity Verification Checks:**
   ```sql
   -- Connect and verify table row counts and schema integrity
   \c gqt_hrms_restore_test

   -- 1. Verify user accounts
   SELECT count(*) FROM accounts_user;

   -- 2. Verify immutable audit log records
   SELECT count(*) FROM core_audit_log;

   -- 3. Verify CRM companies
   SELECT count(*) FROM crm_company;

   -- 4. Verify job requirements and verification checks
   SELECT count(*) FROM jobs_jobrequirement;
   SELECT count(*) FROM jobs_jobverificationcheck;

   -- 5. Verify creative requisitions and asset versions
   SELECT count(*) FROM creatives_creativerequest;
   SELECT count(*) FROM creatives_creativeassetversion;
   ```

5. **Clean Up Test Database:**
   ```bash
   sudo -u postgres dropdb gqt_hrms_restore_test
   ```

### 5.2 Private Media Restoration Drill

1. **Verify Media Archive Integrity:**
   ```bash
   cd /var/backups/gqt-hrms/media
   sha256sum -c gqt_hrms_private_media_YYYYMMDD_HHMMSS.tar.gz.sha256
   ```

2. **Extract Archive into Staging Location:**
   ```bash
   mkdir -p /tmp/media_restore_test
   tar -xzf gqt_hrms_private_media_YYYYMMDD_HHMMSS.tar.gz -C /tmp/media_restore_test
   ```

3. **Validate File Counts & Permissions:**
   ```bash
   ls -la /tmp/media_restore_test/private
   # Verify ownership and file accessibility
   ```

4. **Clean Up:**
   ```bash
   rm -rf /tmp/media_restore_test
   ```

---

## 6. Point-in-Time Recovery (PITR) Architecture

For zero data-loss resilience in production, PostgreSQL Write-Ahead Log (WAL) archiving should be enabled in `postgresql.conf`:

```ini
# postgresql.conf WAL Archiving Settings
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /var/backups/gqt-hrms/wal_archive/%f && cp %p /var/backups/gqt-hrms/wal_archive/%f'
archive_timeout = 900 # Force WAL switch every 15 minutes
```

### Off-Site Backup Recommendation
Local disk backups (`/var/backups/gqt-hrms/`) protect against database corruption and administrative error, but not host-level storage failure or VPS destruction.
* **Secondary Target:** Configure encrypted daily sync to an S3-compatible object store (e.g., Wasabi, AWS S3, Cloudflare R2) using `rclone` or AWS CLI.
* **GPG Encryption:** Encrypt archives before off-site transmission:
  ```bash
  gpg --batch --yes --encrypt --recipient ops@gqt.local gqt_hrms_db_YYYYMMDD_HHMMSS.sql.gz
  ```

---

## 7. Disaster Recovery Runbook Checklist

In the event of total server loss:

1. [ ] Provision fresh Ubuntu 24.04 LTS instance with static IP.
2. [ ] Follow `docs/production/deployment-runbook.md` to install PostgreSQL 16, Python 3.14, Node.js 22, Nginx.
3. [ ] Configure PostgreSQL application user `gqt_hrms_app_user` and database `gqt_hrms`.
4. [ ] Retrieve latest verified database backup `.sql.gz` and `.sha256` from off-site storage.
5. [ ] Verify SHA-256 checksum: `sha256sum -c gqt_hrms_db_*.sql.gz.sha256`.
6. [ ] Restore database: `gunzip -c gqt_hrms_db_*.sql.gz | psql -U gqt_hrms_app_user -d gqt_hrms`.
7. [ ] Execute audit-log immutability SQL role hardening:
       `REVOKE UPDATE, DELETE, TRUNCATE ON TABLE core_audit_log FROM gqt_hrms_app_user;`
8. [ ] Restore private media directory `/srv/gqt-hrms/media/private` from latest verified media tarball.
9. [ ] Run Django migration check: `python manage.py showmigrations`.
10. [ ] Start Gunicorn systemd service and reload Nginx.
11. [ ] Verify `/api/v1/health/` and `/api/v1/ready/` return HTTP 200 `healthy` and `ready`.

