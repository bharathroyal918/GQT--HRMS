# GQT HRMS — Staging & Production Deployment Runbook

> **DEPLOYMENT STATUS: NOT PROVISIONED**  
> *This document provides the operational runbook and configuration blueprints for staging and production hosting. Infrastructure provisioning and live cloud deployment remain subject to administrative authorization.*

---

## 1. System Architecture & Prerequisites

### 1.1 Architecture Topology
```
Internet
   │
   ▼ HTTPS (Port 443)
[ Nginx Reverse Proxy / Static Web Server ]
   ├── Static Frontend SPA Assets ──> /var/www/gqt-hrms/dist
   ├── Django Static Files        ──> /srv/gqt-hrms/staticfiles
   └── /api/ REST Endpoints       ──> UNIX Socket: /run/gqt-hrms/gunicorn.sock
                                             │
                                             ▼
                                   [ Gunicorn WSGI Master ]
                                   ├── Worker 1 (Python 3.14 / Django 5.1)
                                   ├── Worker 2
                                   └── Worker 3
                                             │
                                             ▼ TCP / UNIX Socket
                                   [ PostgreSQL 16 Server ]
                                   ├── Database: gqt_hrms
                                   └── Role: gqt_hrms_app_user
```

### 1.2 Target Hardware & Operating System
* **Hosting Platform:** Hostinger KVM VPS (or standard Ubuntu Cloud instance)
* **Operating System:** Ubuntu 24.04 LTS (Noble Numbat)
* **Compute Minimum:** 2 vCPU, 4 GB RAM, 50 GB NVMe Storage
* **Compute Recommended:** 4 vCPU, 8 GB RAM, 100 GB NVMe Storage
* **Runtimes:**
  * Python: 3.14+
  * Node.js: 22.x LTS & npm 10.x
  * PostgreSQL: 16.x
  * Nginx: 1.24+

---

## 2. Server Base Provisioning

### 2.1 OS Package Installation
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git ufw certbot python3-certbot-nginx \
    nginx postgresql-16 postgresql-contrib-16 \
    build-essential libpq-dev libmagic1

# Install Node.js 22 LTS
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2.2 Dedicated Service User & File Tree
Create an unprivileged system user `gqt_app` to run the application:
```bash
sudo useradd -r -s /bin/bash -d /srv/gqt-hrms -m gqt_app
sudo usermod -aG www-data gqt_app

# Create application directories
sudo mkdir -p /srv/gqt-hrms/backend \
              /srv/gqt-hrms/frontend \
              /srv/gqt-hrms/media/private \
              /srv/gqt-hrms/staticfiles \
              /var/log/gqt-hrms \
              /var/backups/gqt-hrms/postgres \
              /var/backups/gqt-hrms/media \
              /var/www/gqt-hrms/dist \
              /run/gqt-hrms

# Set permissions
sudo chown -R gqt_app:www-data /srv/gqt-hrms /var/log/gqt-hrms /run/gqt-hrms /var/www/gqt-hrms
sudo chown -R gqt_app:gqt_app /var/backups/gqt-hrms
sudo chmod 0750 /srv/gqt-hrms /var/log/gqt-hrms /run/gqt-hrms
sudo chmod 0700 /srv/gqt-hrms/media/private /var/backups/gqt-hrms
```

### 2.3 Firewall Configuration
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

---

## 3. Database Setup & Hardening

### 3.1 Three-Tier PostgreSQL Role Architecture
To enforce strict defense-in-depth and guarantee audit log immutability against application vulnerabilities or SQL injection, database access is divided into three distinct roles:

| Role Name | Scope & Purpose | Privileges | Used By |
|---|---|---|---|
| **`postgres`** | Cluster Administrator / DBA | Superuser / Cluster Admin | Initial setup, role provisioning |
| **`gqt_hrms_migration_user`** | Schema Owner / DDL Migrations | Schema owner, DDL on `public` (`CREATE`, `ALTER`, `DROP`) | Release deployments (`manage.py migrate`) |
| **`gqt_hrms_app_user`** | Web Application Runtime | Non-owner, DML only (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) | Gunicorn / Django web workers (`DATABASE_URL`) |

### 3.2 PostgreSQL Role & Database Provisioning
Connect as PostgreSQL administrator:
```bash
sudo -u postgres psql
```
```sql
-- 1. Create schema migration user (schema owner) with strong password
CREATE USER gqt_hrms_migration_user WITH PASSWORD '<REPLACE_WITH_STRONG_MIGRATION_PASSWORD>';

-- 2. Create runtime application user (unprivileged non-owner) with strong password
CREATE USER gqt_hrms_app_user WITH PASSWORD '<REPLACE_WITH_STRONG_APP_PASSWORD>';

-- 3. Create database owned by migration user
CREATE DATABASE gqt_hrms OWNER gqt_hrms_migration_user;

-- 4. Connect to gqt_hrms database
\c gqt_hrms

-- 5. Configure schema ownership and base privileges
ALTER SCHEMA public OWNER TO gqt_hrms_migration_user;
GRANT CONNECT ON DATABASE gqt_hrms TO gqt_hrms_app_user;
GRANT USAGE ON SCHEMA public TO gqt_hrms_app_user;

-- 6. Configure default privileges for future tables created by migration user
ALTER DEFAULT PRIVILEGES FOR ROLE gqt_hrms_migration_user IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO gqt_hrms_app_user;

ALTER DEFAULT PRIVILEGES FOR ROLE gqt_hrms_migration_user IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO gqt_hrms_app_user;
```

### 3.3 Initial Migration Execution as Schema Owner
Run initial migrations using the `gqt_hrms_migration_user` role so all tables are created with proper ownership:
```bash
sudo -u gqt_app -i
cd /srv/gqt-hrms
DATABASE_URL=postgres://gqt_hrms_migration_user:<STRONG_MIGRATION_PASSWORD>@127.0.0.1:5432/gqt_hrms \
    /srv/gqt-hrms/backend/.venv/bin/python /srv/gqt-hrms/backend/manage.py migrate --settings=config.settings.production
```

### 3.4 Audit Log Immutability Enforcement
> **CRITICAL SECURITY REQUIREMENT (SEC-4E-002):**  
> Because `core_audit_log` is owned by `gqt_hrms_migration_user` (and NOT by `gqt_hrms_app_user`), revoking `UPDATE`, `DELETE`, and `TRUNCATE` privileges from `gqt_hrms_app_user` completely prevents the application from tampering with audit records. The application user cannot re-grant privileges to itself or alter table definitions.

**Execute the following SQL as administrator or schema owner after migrations:**
```sql
\c gqt_hrms

-- Grant base table DML to app user across standard domain tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO gqt_hrms_app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO gqt_hrms_app_user;

-- Explicitly revoke mutation rights on the immutable audit log table
REVOKE UPDATE, DELETE, TRUNCATE ON TABLE core_audit_log FROM gqt_hrms_app_user;

-- Ensure app user possesses strictly append-only (INSERT) and read (SELECT) privileges
GRANT SELECT, INSERT ON TABLE core_audit_log TO gqt_hrms_app_user;
```

### 3.5 Staging Verification Protocol
Verify the privilege design in staging prior to production cutover:
```sql
-- Connect as runtime application user
\c gqt_hrms gqt_hrms_app_user

-- 1. Test AuditLog creation (MUST SUCCEED)
-- AuditLog records use client-generated UUID primary keys and insert directly
INSERT INTO core_audit_log (id, action, resource_type, resource_id, created_at, changes, user_agent, correlation_id)
VALUES (gen_random_uuid(), 'SECURITY_VERIFY', 'system.test', 'probe-1', NOW(), '{}', 'psql-probe', 'corr-probe');

-- 2. Test AuditLog read (MUST SUCCEED)
SELECT count(*) FROM core_audit_log WHERE action = 'SECURITY_VERIFY';

-- 3. Test AuditLog update (MUST FAIL with permission denied)
UPDATE core_audit_log SET action = 'TAMPERED' WHERE resource_id = 'probe-1';
-- Expected result: ERROR: permission denied for table core_audit_log

-- 4. Test AuditLog deletion (MUST FAIL with permission denied)
DELETE FROM core_audit_log WHERE resource_id = 'probe-1';
-- Expected result: ERROR: permission denied for table core_audit_log

-- 5. Test AuditLog truncation (MUST FAIL with permission denied)
TRUNCATE TABLE core_audit_log;
-- Expected result: ERROR: permission denied for table core_audit_log

-- 6. Test self-grant elevation (MUST FAIL because app user is not table owner)
GRANT ALL ON TABLE core_audit_log TO gqt_hrms_app_user;
-- Expected result: WARNING: no privileges were granted for "core_audit_log" (or ERROR: must be owner)
```

### 3.6 Future Schema Migrations Workflow
When future release phases (e.g. Phase 8 Audit Log Viewer) introduce migrations altering `core_audit_log`:
1. Migrations are executed using `gqt_hrms_migration_user` (the schema owner).
2. Because the migration role owns the table, PostgreSQL permits all DDL operations (`ALTER TABLE`, `ADD COLUMN`, `CREATE INDEX`).
3. The runtime role `gqt_hrms_app_user` remains permanently restricted to `SELECT, INSERT`, preserving runtime immutability without manual privilege intervention.

---

## 4. Application Configuration & Deployment

### 4.1 Production Environment Variables (`/srv/gqt-hrms/.env`)
Create `/srv/gqt-hrms/.env` with `0600` permissions (owned by `gqt_app`):
```ini
DJANGO_ENV=production
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=<GENERATE_64_CHAR_HEX_KEY>
DEBUG=False
ALLOWED_HOSTS=hrms.globalquest.in,api.hrms.globalquest.in

# Database Connection
DATABASE_URL=postgres://gqt_hrms_app_user:<STRONG_PASSWORD>@127.0.0.1:5432/gqt_hrms

# Storage Paths
MEDIA_ROOT=/srv/gqt-hrms/media
PRIVATE_MEDIA_ROOT=/srv/gqt-hrms/media/private
STATIC_ROOT=/srv/gqt-hrms/staticfiles

# Security Cookies & Headers
AUTH_COOKIE_SECURE=True
AUTH_COOKIE_SAMESITE=Lax
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=False # Handled upstream by Nginx
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# CORS & CSRF
CORS_ALLOWED_ORIGINS=https://hrms.globalquest.in
CSRF_TRUSTED_ORIGINS=https://hrms.globalquest.in

# JWT Settings
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=15
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Student Portal Client (Disabled until authorized)
PORTAL_SYNC_ENABLED=False
```

### 4.2 Backend Python Setup
```bash
sudo -u gqt_app -i
cd /srv/gqt-hrms

# Clone or copy codebase
# (Code deployment is staged into /srv/gqt-hrms/backend)

# Create virtual environment
python3.14 -m venv /srv/gqt-hrms/backend/.venv
source /srv/gqt-hrms/backend/.venv/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r /srv/gqt-hrms/backend/requirements.txt
pip install gunicorn

# Run migrations
python /srv/gqt-hrms/backend/manage.py migrate --settings=config.settings.production

# Collect static files
python /srv/gqt-hrms/backend/manage.py collectstatic --noinput --settings=config.settings.production
```

### 4.3 Frontend SPA Build
```bash
cd /srv/gqt-hrms/frontend
npm ci
npm run build

# Copy build artifacts to Nginx web root
cp -r /srv/gqt-hrms/frontend/dist/* /var/www/gqt-hrms/dist/
```

---

## 5. Systemd Service Specification

Create `/etc/systemd/system/gqt-hrms.service`:
```ini
[Unit]
Description=GQT HRMS Django Gunicorn Application Server
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=gqt_app
Group=www-data
WorkingDirectory=/srv/gqt-hrms/backend
RuntimeDirectory=gqt-hrms
EnvironmentFile=/srv/gqt-hrms/.env
ExecStart=/srv/gqt-hrms/backend/.venv/bin/gunicorn config.wsgi:application \
    --name gqt_hrms \
    --workers 3 \
    --threads 2 \
    --worker-class gthread \
    --worker-tmp-dir /dev/shm \
    --bind unix:/run/gqt-hrms/gunicorn.sock \
    --access-logfile /var/log/gqt-hrms/gunicorn_access.log \
    --error-logfile /var/log/gqt-hrms/gunicorn_error.log \
    --log-level info \
    --capture-output

ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=15
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gqt-hrms
sudo systemctl start gqt-hrms
sudo systemctl status gqt-hrms
```

---

## 6. Nginx Server Configuration

Create `/etc/nginx/sites-available/gqt-hrms`:
```nginx
# Upstream Gunicorn Unix Socket
upstream gqt_django {
    server unix:/run/gqt-hrms/gunicorn.sock fail_timeout=0;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name hrms.globalquest.in;
    return 301 https://$host$request_uri;
}

# HTTPS Server Block
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name hrms.globalquest.in;

    # SSL Certificates (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/hrms.globalquest.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hrms.globalquest.in/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Defensive Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Client body limit for file uploads (max 10MB)
    client_max_body_size 12M;

    # Frontend Single Page Application Root
    root /var/www/gqt-hrms/dist;
    index index.html;

    # Static Assets Caching (Vite hashed bundles)
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Django Collected Static Files
    location /static/ {
        alias /srv/gqt-hrms/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # CRITICAL SECURITY: Never serve /media/private directly via Nginx
    location ^~ /media/private/ {
        internal;
        return 403;
    }

    # API and Django Admin Reverse Proxy
    location ~ ^/(api|admin)/ {
        proxy_pass http://gqt_django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $request_id;
        proxy_redirect off;
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
    }

    # SPA Fallback Routing
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/gqt-hrms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 7. TLS Certificate Issuance

```bash
sudo certbot --nginx -d hrms.globalquest.in
# Certbot automatically tests and sets up systemd timer for auto-renewal:
sudo systemctl status certbot.timer
```

---

## 8. Verification & Post-Deployment Smoke Tests

Execute smoke tests immediately after starting services:
```bash
# 1. Health check probe
curl -f -i https://hrms.globalquest.in/api/v1/health/
# Must return: HTTP 200 OK {"status": "healthy"}

# 2. Readiness check probe (verifies database connection)
curl -f -i https://hrms.globalquest.in/api/v1/ready/
# Must return: HTTP 200 OK {"status": "ready", "database": "ok"}

# 3. Security headers check
curl -I https://hrms.globalquest.in/
# Verify X-Frame-Options: DENY, X-Content-Type-Options: nosniff, Strict-Transport-Security

# 4. Gunicorn process status
sudo systemctl status gqt-hrms --no-pager
```

---

## 9. Rollback Procedure

If a release fails smoke testing:
1. Stop incoming traffic by placing a temporary maintenance page if necessary.
2. Stop application service: `sudo systemctl stop gqt-hrms`.
3. Roll back backend code to previous commit or release tag.
4. If database migrations were run, revert them:
   ```bash
   python manage.py migrate <app_name> <previous_migration_name>
   ```
5. If database corruption occurred, restore latest backup per `docs/production/backup-and-recovery.md`.
6. Roll back frontend `/var/www/gqt-hrms/dist` from the previous build archive.
7. Restart service: `sudo systemctl start gqt-hrms`.
8. Verify `/api/v1/ready/` returns HTTP 200.

