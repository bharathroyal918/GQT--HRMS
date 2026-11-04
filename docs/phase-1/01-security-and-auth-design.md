# GQT HRMS & Recruitment CRM Platform — Phase 1: Security & Authentication Design

## 1. Threat Landscape & Security Posture

The GQT HRMS platform processes proprietary corporate relationships, hiring requirements, and sensitive student placement records. Security is built into the foundation at every layer rather than treated as an afterthought.

---

## 2. Authentication Architecture

### 2.1 Identity & Password Hashing
- **Identity Attribute**: Case-insensitively normalized email address (`apps.accounts.models.User.email`).
- **Primary Key**: Cryptographically random UUIDv4 (`apps.accounts.models.User.id`).
- **Password Hasher**: Argon2id (`django.contrib.auth.hashers.Argon2PasswordHasher`), exceeding OWASP 2024 password storage guidelines.
  - PBKDF2 and BCrypt are configured solely as legacy transition fallbacks.
  - MD5 hasher is strictly confined to `config.settings.test` to accelerate test execution.

### 2.2 JWT In HttpOnly Cookies
The application uses SimpleJWT tokens delivered via secure HTTP cookies rather than browser `localStorage` or `sessionStorage`:
- `gqt_access_token`: 15-minute lifespan, `HttpOnly=True`, `SameSite=Lax`, `Path=/`, `Secure=True` (in production).
- `gqt_refresh_token`: 7-day lifespan, `HttpOnly=True`, `SameSite=Lax`, `Path=/`, `Secure=True` (in production).

Benefits:
- Eliminates JavaScript-based credential theft via Cross-Site Scripting (XSS).
- Automatic token dispatch across authenticated API calls.
- Silent token rotation via `POST /api/v1/auth/token/refresh/` using the refresh cookie.
- Token revocation and blacklist table persistence on `POST /api/v1/auth/logout/`.

---

## 3. Role-Based Access Control (RBAC)

### 3.1 Ten Canonical Institutional Roles
Enforced via `RoleCatalog` in `apps.accounts.models`:
1. `ADMIN` — System configuration, user provisioning, global overrides.
2. `SUPERUSER` — Framework superuser privileges.
3. `PLACEMENT_HEAD` — Final job approvals, placement policy sign-off.
4. `PLACEMENT_OFFICER` — Job requirements, candidate mapping, drive execution.
5. `CALLING_EXECUTIVE` — Company acquisition, calls, outreach notes.
6. `CRM_EXECUTIVE` — Recruitment CRM pipelines, relationships.
7. `CREATIVE_DESIGNER` — Poster design, creative asset uploads.
8. `CREATIVE_REVIEWER` — Review and approval of job flyers.
9. `TRAINER` — Mock interviews, assessments, student readiness tracking.
10. `INTERVIEW_COORDINATOR` — Scheduling rounds, interview attendance, results.
11. `AUDITOR` — Compliance, reporting, immutable audit trail oversight.

### 3.2 Authorization Model
- **Default Policy**: Deny-by-default via DRF settings:
  ```python
  REST_FRAMEWORK = {
      "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
  }
  ```
- Public endpoints (`/api/v1/health/`, `/api/v1/ready/`, `/api/v1/auth/login/`) explicitly declare `permission_classes = [permissions.AllowAny]`.
- User provisioning (`/api/v1/auth/users/`) strictly requires `IsAdminOrSuperUser`.
- Public self-registration is **prohibited and unimplemented**. All accounts must be provisioned by authenticated administrators.

---

## 4. Audit Trail & Log Sanitization

### 4.1 Immutable Audit Log
`apps.core.models.AuditLog` records:
- `user`: Foreign key to `accounts.User` (nullable for unauthenticated attempts).
- `action`: Canonical action string (e.g., `AUTH_LOGIN_SUCCESS`, `AUTH_LOGIN_FAILED`, `USER_CREATED`, `ROLE_ASSIGNED`).
- `resource_type`: Target entity name (e.g., `accounts.User`, `crm.Company`).
- `resource_id`: Stringified primary key or identifier.
- `ip_address`: Remote IP from request metadata.
- `user_agent`: Client user agent string.
- `correlation_id`: Distributed tracing UUID matching `X-Correlation-ID`.
- `changes`: JSON delta describing mutation details.
- `created_at`: UTC timestamp.

**Immutability Protection**:
`AuditLog.delete()` explicitly raises `PermissionError("Audit logs are strictly immutable and cannot be deleted.")`.

### 4.2 Sensitive Data Redaction
`apps.core.logging.SensitiveDataFilter` intercepts all log records across `django.request`, redacting:
- Password parameters (`password=...`)
- Bearer tokens (`bearer eyJ...`)
- Secret keys and API tokens
Replacing sensitive values with `[REDACTED]`.

---

## 5. Fail-Closed Production Invariants

`config.settings.production` performs runtime checks on startup:
1. **Secret Key Invariant**: Fails with `ImproperlyConfigured` if `DJANGO_SECRET_KEY` is missing, shorter than 40 characters, or contains `"insecure"`.
2. **Allowed Hosts Invariant**: Fails if `DJANGO_ALLOWED_HOSTS` is empty, contains `"*"`, or only contains `"localhost"`.
3. **SSL / Cookie Flags**: Automatically enforces `AUTH_COOKIE_SECURE = True`, `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`, `SECURE_SSL_REDIRECT = True`, and `SECURE_HSTS_SECONDS = 31536000`.

