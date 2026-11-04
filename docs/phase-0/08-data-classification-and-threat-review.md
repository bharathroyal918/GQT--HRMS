# 08 — Data Classification and Initial Threat Review

> **Status:** Phase 0 Documentation — Not Approved for Implementation
> **Prepared:** 2026-11-03
> **Project:** GQT HRMS & Recruitment CRM Platform

---

> [!IMPORTANT]
> This document is a **preliminary** data classification and threat review. It is not a security audit. Threats and mitigations are **proposed** — none have been tested or validated. A formal security review must be conducted before production deployment.

---

## Table of Contents

1. [Data Classification Framework](#1-data-classification-framework)
2. [Data Inventory](#2-data-inventory)
3. [Threat Inventory](#3-threat-inventory)
4. [Security Controls Baseline](#4-security-controls-baseline)
5. [Compliance Considerations](#5-compliance-considerations)

---

## 1. Data Classification Framework

The following sensitivity levels are defined for all data handled by the GQT HRMS platform:

| Level | Label | Definition | Handling Requirements |
|-------|-------|-----------|----------------------|
| **L1** | `CRITICAL` | Credentials, tokens, encryption keys, secret keys, service passwords | Never logged; never transmitted in plain text; stored encrypted or hashed; rotation policy required |
| **L2** | `HIGHLY_CONFIDENTIAL` | Resumes, offer letters, salary details, interview feedback, student personal data (PII), private HR contact information | Access-controlled; no public URLs; role + object-level permission; audit log on every access |
| **L3** | `CONFIDENTIAL` | Company contact details, job descriptions, interview schedules, placement outcomes | Role-controlled; internal to authenticated staff; not publicly exported |
| **L4** | `INTERNAL` | Workflow state, audit logs, system configuration, internal notes | Authenticated staff access; not customer-facing; retained per policy |
| **L5** | `PUBLIC` | Approved and published job postings (if any), aggregate placement statistics (if published) | No PII; reviewed before publication |

### 1.1 Classification Principles

- **Default to higher classification** when uncertain.
- **Data in transit** must use TLS 1.2+ for all classifications L1–L4.
- **Data at rest** for L1–L2 must use encryption at the storage layer (PostgreSQL column encryption or OS-level disk encryption).
- **Log sanitization**: L1 and L2 data must never appear in application logs. Structured logging must apply field-level redaction.
- **Export control**: Any export (CSV, PDF) must enforce the exporting user's scope — they cannot export data they cannot read.

---

## 2. Data Inventory

| Data Entity | Classification | Storage Location | Retention | Access Roles | Encryption Required | Export Permitted | Notes |
|------------|---------------|-----------------|-----------|-------------|--------------------|--------------------|-------|
| User passwords | `CRITICAL` (L1) | PostgreSQL (Argon2 hash) | Until account deletion | None (hash only; never read) | Hash is the encryption | No | Argon2id; never stored in plain text or reversibly |
| JWT access tokens | `CRITICAL` (L1) | HttpOnly cookie (client-side); blacklist in DB | Access: 15 min; Refresh: 7 days | None (opaque to application code) | No (short-lived) | No | Never in localStorage, logs, or response bodies |
| JWT refresh tokens | `CRITICAL` (L1) | HttpOnly cookie + blacklist table | 7 days | None | No | No | Blacklisted on logout |
| Integration service credentials (Portal API key) | `CRITICAL` (L1) | Environment variable / secrets manager | Until rotated | SYSTEM role only | Yes (env/vault) | No | Must not appear in frontend API responses |
| SMTP / WhatsApp API keys | `CRITICAL` (L1) | Environment variable | Until rotated | SYSTEM only | Yes (env/vault) | No | Rotation policy TBD |
| Student PII (name, email, phone, roll number, address) | `HIGHLY_CONFIDENTIAL` (L2) | PostgreSQL | Until student graduation + retention period (TBD) | PLACEMENT_HEAD, PLACEMENT_OFFICER, TRAINER (limited), STUDENT (own only) | Yes (disk encryption) | Scoped export by authorized staff only |
| Student academic records (CGPA, backlogs, graduation year) | `HIGHLY_CONFIDENTIAL` (L2) | PostgreSQL (synced from Portal) | Same as PII | PLACEMENT_HEAD, PLACEMENT_OFFICER, TRAINER (see OD-017) | Yes | Scoped export only | Source of truth is Portal; HRMS stores a snapshot |
| Student resumes (PDF files) | `HIGHLY_CONFIDENTIAL` (L2) | Private file storage (`media/resumes/`) | Duration of placement engagement + retention period | PLACEMENT_HEAD, PLACEMENT_OFFICER, student owner | Yes (disk encryption) | No direct URL; authenticated stream only |
| Student offer letters (PDF files) | `HIGHLY_CONFIDENTIAL` (L2) | Private file storage (`media/offer_letters/`) | Permanent (placement record) | PLACEMENT_HEAD, PLACEMENT_OFFICER, SELECTED student only | Yes | Authenticated stream only | Extra restriction: SELECTED status required for student access |
| HR contact private information (personal phone, private email) | `HIGHLY_CONFIDENTIAL` (L2) | PostgreSQL | Until contact removed | PLACEMENT_HEAD, PLACEMENT_OFFICER | Yes | No general export | Business contacts only; no personal data of employees |
| Interview feedback (round scores, evaluator notes) | `HIGHLY_CONFIDENTIAL` (L2) | PostgreSQL | Duration of drive + retention | PLACEMENT_HEAD, PLACEMENT_OFFICER, INTERVIEW_COORDINATOR | Yes | Restricted export (Head only) | Highly sensitive; not visible to students (TBD — see OD-019) |
| Salary / CTC information | `HIGHLY_CONFIDENTIAL` (L2) | PostgreSQL | Permanent (placement record) | PLACEMENT_HEAD, PLACEMENT_OFFICER | Yes | Restricted; no student visibility (see OD-019) | Field-level authorization required |
| Company information (industry, domain, contact history) | `CONFIDENTIAL` (L3) | PostgreSQL | Until company archived | PLACEMENT_HEAD, PLACEMENT_OFFICER | No (business data) | Staff export only | Company profile data; not PII |
| Job descriptions | `CONFIDENTIAL` (L3) | PostgreSQL | Until drive closed + retention | All staff roles | No | Staff export only | Published JDs may become PUBLIC |
| Interview schedules | `CONFIDENTIAL` (L3) | PostgreSQL | Until interview completed | All staff, relevant student (own only) | No | Staff export only | |
| Placement outcomes | `CONFIDENTIAL` (L3) | PostgreSQL | Permanent | All staff | No | Aggregate for analytics; individual is L2 | Individual outcomes are L2; aggregate statistics may be L5 |
| Audit log entries | `INTERNAL` (L4) | PostgreSQL (append-only) | Minimum 1 year (TBD — see OD-011) | PLACEMENT_HEAD only | No | No | Must not contain L1 data; must contain actor, action, timestamp, entity |
| Communication logs (Email/WhatsApp delivery records) | `INTERNAL` (L4) | PostgreSQL | 90 days (proposed) | PLACEMENT_HEAD, PLACEMENT_OFFICER | No | No | Message content not stored; delivery status only |
| Analytics and reports | `INTERNAL` / `PUBLIC` (L4–L5) | PostgreSQL (aggregate) | Rolling | PLACEMENT_HEAD, PLACEMENT_OFFICER | No | Aggregate allowed; PII stripped before export | Individual-level analytics are L2 |
| System configuration | `INTERNAL` (L4) | Environment variables / settings files | N/A | SYSTEM / DevOps | Yes (secrets) | No | `SECRET_KEY`, `DATABASE_URL` etc. |

---

## 3. Threat Inventory

> [!NOTE]
> Severity is rated as: **CRITICAL**, **HIGH**, **MEDIUM**, **LOW**. Ratings are preliminary estimates — a formal threat model review is required before production.

---

### T-001: Unauthorized Access via Stolen JWT Token

| Field | Detail |
|-------|--------|
| **Threat ID** | T-001 |
| **Threat** | Attacker steals a valid JWT access or refresh token and uses it to impersonate a legitimate user |
| **Attack Scenario** | XSS injection reads cookie (if not HttpOnly); network interception (no HTTPS); malware on user device; server-side token storage breach |
| **Proposed Mitigation** | JWT stored in HttpOnly cookies (XSS cannot read); HTTPS enforced in production (network interception blocked); short access token lifetime (15 min); refresh token blacklist on logout; `SameSite=Lax` prevents CSRF token theft |
| **Validation Method** | Test: attempt to read `gqt_access_token` via JavaScript in browser console — must return `undefined`. Confirm cookie flags in response headers |
| **Outstanding Questions** | What is the agreed token lifetime? Device compromise scenario mitigation? |
| **Severity** | **HIGH** |

---

### T-002: Privilege Escalation via Frontend Role Manipulation

| Field | Detail |
|-------|--------|
| **Threat ID** | T-002 |
| **Threat** | Attacker modifies frontend state (localStorage, React context, request payload) to claim a higher-privilege role |
| **Attack Scenario** | User intercepts API request and adds `role=PLACEMENT_HEAD` to payload; modifies React auth context via browser devtools |
| **Proposed Mitigation** | RBAC enforced **exclusively** on backend; JWT payload contains authoritative role claim (signed, not modifiable); backend ignores any role field in request body |
| **Validation Method** | Test: send API request with modified role claim in body — must be ignored. Test: low-privilege user calls high-privilege endpoint — must return 403 |
| **Outstanding Questions** | Role embedded in JWT — should role changes require re-login (token re-issue)? |
| **Severity** | **HIGH** |

---

### T-003: IDOR — Accessing Another Student's Resume

| Field | Detail |
|-------|--------|
| **Threat ID** | T-003 |
| **Threat** | Student A accesses Student B's resume by guessing or enumerating resource IDs |
| **Attack Scenario** | Sequential integer IDs allow enumeration: `/resumes/1/`, `/resumes/2/`. Even with UUIDs, a student may guess or share a URL |
| **Proposed Mitigation** | UUID primary keys (not sequential integers) on all models; object-level permission `IsStudentOwnerOrStaff` on every resume endpoint; no public file URLs — all downloads through authenticated streaming endpoint |
| **Validation Method** | Test: student A authenticates, then requests student B's resume UUID — must return 403. Test: unauthenticated request to resume endpoint — must return 401 |
| **Outstanding Questions** | None currently |
| **Severity** | **HIGH** |

---

### T-004: Approval Bypass via Direct API Call

| Field | Detail |
|-------|--------|
| **Threat ID** | T-004 |
| **Threat** | User skips required workflow steps (e.g., verification checklist) by calling the approval endpoint directly via curl/Postman |
| **Attack Scenario** | Placement Officer calls `POST /api/v1/jobs/{id}/approve/` without completing the 5-point checklist; job transitions to approved state incorrectly |
| **Proposed Mitigation** | Approval service validates state prerequisites server-side before any state transition; incomplete checklist returns `400 Bad Request`; state machine enforced in service layer, not just UI |
| **Validation Method** | Test: submit approval API call with incomplete checklist — must return 400 with field-specific errors. Test: approved job must have all 5 checklist items marked complete in DB |
| **Outstanding Questions** | Who can force-override an incomplete checklist? Placement Head only? |
| **Severity** | **CRITICAL** |

---

### T-005: Malicious File Upload Disguised as PDF

| Field | Detail |
|-------|--------|
| **Threat ID** | T-005 |
| **Threat** | Attacker uploads an executable, script, or polyglot file with `.pdf` extension to gain code execution or serve malware |
| **Attack Scenario** | Attacker renames `malware.exe` to `resume.pdf` and uploads it; server stores it; another user downloads and executes it |
| **Proposed Mitigation** | Magic bytes check: file must start with `%PDF-` (hex: `25 50 44 46 2D`); extension check (`.pdf` only); 5MB size limit; files never served with `Content-Type: application/octet-stream` that triggers execution; files stored outside web root |
| **Validation Method** | Test: upload `.exe` renamed to `.pdf` — must return 400. Test: upload a valid `.pdf` with malicious payload in content — magic bytes pass but file is inert; confirm no execution path |
| **Outstanding Questions** | Should antivirus scanning be added (ClamAV)? |
| **Severity** | **HIGH** |

---

### T-006: Cross-Student Offer Letter Access

| Field | Detail |
|-------|--------|
| **Threat ID** | T-006 |
| **Threat** | A student in a non-selected status accesses another student's offer letter |
| **Attack Scenario** | Student A is in INTERVIEWED status; Student B is SELECTED. Student A obtains or guesses Student B's offer letter UUID |
| **Proposed Mitigation** | Object-level permission `IsSelectedCandidateOrStaff`: student must have `placement_status=SELECTED` AND `student_id` matches the placement record; UUID-based IDs prevent guessing; no public download URL |
| **Validation Method** | Test: student with INTERVIEWED status requests a SELECTED student's offer letter — must return 403. Test: SELECTED student requests their own offer letter — must return 200 with file stream |
| **Outstanding Questions** | Can a student download their offer letter after their joining date has passed? Retention policy? |
| **Severity** | **HIGH** |

---

### T-007: Formula Injection in CSV Exports

| Field | Detail |
|-------|--------|
| **Threat ID** | T-007 |
| **Threat** | Attacker injects spreadsheet formulas into text fields; when exported to CSV and opened in Excel, formulas execute |
| **Attack Scenario** | Student enters name `=CMD|' /C calc'!A0` in a profile field; staff exports student list as CSV; Excel opens file and executes the formula |
| **Proposed Mitigation** | Sanitize CSV cell values: prefix cells starting with `=`, `+`, `-`, `@`, `\t`, `\r` with a single quote (`'`); apply to all string fields in every CSV export function |
| **Validation Method** | Test: create a student record with formula in name field; export CSV; confirm cell value is prefixed with `'` and formula does not execute |
| **Outstanding Questions** | Should CSV export be replaced with a server-rendered PDF report for sensitive data? |
| **Severity** | **MEDIUM** |

---

### T-008: Sensitive Data in Application Logs

| Field | Detail |
|-------|--------|
| **Threat ID** | T-008 |
| **Threat** | Passwords, JWT tokens, API keys, or PII appear in application logs and are accessible to log aggregation systems or future developers |
| **Attack Scenario** | An unhandled exception logs the full request body including `password`; a debug log prints the `Authorization` header; JWT token appears in an error trace |
| **Proposed Mitigation** | Structured logging with field-level redaction list: `password`, `token`, `secret`, `key`, `authorization`, `cookie`; Django `LOGGING` configuration with custom filter; no `print()` statements in production code; `DEBUG=False` prevents Django debug pages |
| **Validation Method** | Test: trigger a login failure; confirm `password` field does not appear in log output. Review log configuration for `SENSITIVE_FIELDS` redaction filter |
| **Outstanding Questions** | Which PII fields (student name, email) are acceptable in logs vs. require redaction? |
| **Severity** | **HIGH** |

---

### T-009: Integration Credential Exposure via Frontend

| Field | Detail |
|-------|--------|
| **Threat ID** | T-009 |
| **Threat** | The Student Portal service token or other backend-only credentials are exposed in frontend API responses or JavaScript bundles |
| **Attack Scenario** | Backend accidentally includes `STUDENT_PORTAL_SERVICE_TOKEN` in an API response; or Vite environment variable (prefixed `VITE_`) is set and bundled into the frontend JS |
| **Proposed Mitigation** | Integration credentials stored only in server-side environment variables; never passed to frontend; Vite environment variable naming policy: `VITE_` prefix only for intentionally public frontend config; backend API returns no credential fields; code review policy for any `VITE_` variable additions |
| **Validation Method** | Test: grep compiled frontend bundle for any known credential patterns. Review all API serializers for credential field exposure |
| **Outstanding Questions** | Who manages credential rotation? (see OD-013) |
| **Severity** | **CRITICAL** |

---

### T-010: Duplicate Candidate Submission Under Race Condition

| Field | Detail |
|-------|--------|
| **Threat ID** | T-010 |
| **Threat** | Two concurrent requests submit the same student to the same job drive simultaneously, creating duplicate placement records |
| **Attack Scenario** | Placement Officer double-clicks submit; or two officers work the same student simultaneously; creates duplicate records causing data inconsistency |
| **Proposed Mitigation** | `select_for_update()` on submission record within `@transaction.atomic`; unique constraint at database level on `(student_id, job_id)` for submission records; idempotency key on submission endpoint |
| **Validation Method** | Test: fire two concurrent POST requests for same student+job; confirm only one record created and second returns 409 Conflict |
| **Outstanding Questions** | Should the API return 409 or silently deduplicate? |
| **Severity** | **MEDIUM** |

---

### T-011: Concurrent Conflicting Approvals

| Field | Detail |
|-------|--------|
| **Threat ID** | T-011 |
| **Threat** | Two Placement Head users simultaneously approve and reject the same entity (job, creative, eligibility override), resulting in inconsistent final state |
| **Attack Scenario** | PH-1 approves a JD at the same millisecond PH-2 rejects it; last write wins, leaving audit log out of sync with final state |
| **Proposed Mitigation** | Optimistic locking via `version` field on approvable models; state transition must check `version` matches; `select_for_update()` in approval service; rejected/approved state is terminal (no re-approval without explicit re-open) |
| **Validation Method** | Test: simulate concurrent approval + rejection; confirm only one succeeds; confirm audit log reflects the winning state |
| **Outstanding Questions** | Is there a scenario where a single Placement Head role is guaranteed? Multi-head support needed? |
| **Severity** | **MEDIUM** |

---

### T-012: Stale/Inconsistent Student Data from Portal Integration

| Field | Detail |
|-------|--------|
| **Threat ID** | T-012 |
| **Threat** | HRMS uses an outdated snapshot of student data from the Portal (CGPA, backlog status, contact info), leading to incorrect eligibility decisions |
| **Attack Scenario** | Student updates their profile on the Portal (e.g., corrects CGPA); HRMS sync has not run; eligibility engine uses stale data and either includes or excludes incorrectly |
| **Proposed Mitigation** | `portal_synced_at` timestamp stored on student profile; eligibility checks flag if sync is stale (configurable threshold); Celery sync worker runs on configurable schedule; Portal sync triggered on key workflow events (drive creation); display last-synced timestamp in UI |
| **Validation Method** | Test: update student data in Portal mock; run eligibility check before sync — confirm stale flag; run sync — confirm updated data used |
| **Outstanding Questions** | What is the acceptable staleness window? (see OD-014 — Portal API rate limits unknown) |
| **Severity** | **HIGH** |

---

### T-013: Lost or Duplicated Notifications

| Field | Detail |
|-------|--------|
| **Threat ID** | T-013 |
| **Threat** | Interview reminder notifications are either not sent (lost) or sent multiple times (duplicated) due to worker crashes or retry logic |
| **Attack Scenario** | Celery worker crashes after sending a reminder but before marking it as sent; on restart, the task is retried and the reminder is sent again |
| **Proposed Mitigation** | `select_for_update(skip_locked=True)` on reminder records; `sent` boolean + `sent_at` timestamp updated atomically with send operation; idempotency key per reminder (interview_id + type + scheduled window); Celery task `acks_late=False` for at-most-once (vs exactly-once tradeoff) |
| **Validation Method** | Test: simulate worker crash mid-task; confirm no duplicate notification sent on retry |
| **Outstanding Questions** | At-most-once vs at-least-once delivery — which is preferred for reminders? |
| **Severity** | **MEDIUM** |

---

### T-014: Inadequate Backup and Recovery

| Field | Detail |
|-------|--------|
| **Threat ID** | T-014 |
| **Threat** | Database or file storage corruption/deletion without recent backup leads to permanent data loss |
| **Attack Scenario** | Hosting provider disk failure; accidental `DROP TABLE`; ransomware on VPS; media directory deleted during deployment |
| **Proposed Mitigation** | Automated daily PostgreSQL backups (pg_dump); backup stored offsite (not same server); backup restoration tested quarterly; `media/` directory backed up alongside database; RTO and RPO defined (to be decided by GQT); backup integrity verification |
| **Validation Method** | Perform a test restore from backup in staging; confirm all tables and media files are intact |
| **Outstanding Questions** | RTO target? RPO target? Who owns backup monitoring? (see Compliance section) |
| **Severity** | **CRITICAL** |

---

### T-015: SQL Injection via Raw Queries

| Field | Detail |
|-------|--------|
| **Threat ID** | T-015 |
| **Threat** | Attacker injects SQL via user input in a raw query context, bypassing ORM protections |
| **Attack Scenario** | A developer uses `cursor.execute(f"SELECT * FROM students WHERE name = '{user_input}'")` for a complex analytics query; attacker sends `name = "'; DROP TABLE students;--"` |
| **Proposed Mitigation** | Use Django ORM for all queries; when raw SQL is unavoidable, use parameterized queries only (`cursor.execute(sql, [params])`); code review checklist item: no f-string SQL interpolation; ruff/pylint rule for string-formatted SQL |
| **Validation Method** | Code review: grep for `cursor.execute(f"`, `cursor.execute("...%s" %`); CI lint rule to flag raw SQL patterns |
| **Outstanding Questions** | Analytics module may require complex raw SQL — establish review process before that phase |
| **Severity** | **HIGH** |

---

### T-016: CSRF on State-Changing API Endpoints

| Field | Detail |
|-------|--------|
| **Threat ID** | T-016 |
| **Threat** | Attacker crafts a malicious page that triggers a state-changing API request (POST/PUT/DELETE) using the victim's session cookies |
| **Attack Scenario** | Victim visits attacker's page; page sends `POST /api/v1/jobs/{id}/approve/` with victim's browser cookies; job is approved without victim's knowledge |
| **Proposed Mitigation** | `SameSite=Lax` on JWT cookies prevents cross-site cookie sending for top-level navigations; DRF `SessionAuthentication` not used (JWT replaces it); CORS `ALLOWED_ORIGINS` restricts which origins can call the API; CSRF token additionally for form submissions (if any non-API forms) |
| **Validation Method** | Test: from a different origin, attempt a state-changing API call with valid cookies — must fail due to CORS policy |
| **Outstanding Questions** | Confirm DRF authentication class does not include `SessionAuthentication` in JWT-only mode |
| **Severity** | **MEDIUM** |

---

### T-017: Unauthorized Access to Audit Logs

| Field | Detail |
|-------|--------|
| **Threat ID** | T-017 |
| **Threat** | A lower-privilege user reads audit log entries, potentially exposing who approved what, salary approvals, or sensitive workflow history |
| **Attack Scenario** | Placement Officer calls `GET /api/v1/audit-logs/` and reads Placement Head's approval decisions and internal notes |
| **Proposed Mitigation** | Audit log endpoint restricted to `PLACEMENT_HEAD` role only; object-level filtering: officers may see audit trail for their own actions only; audit log is append-only (no delete or update endpoint exposed) |
| **Validation Method** | Test: Placement Officer requests audit log list — must return 403. Test: Placement Head requests audit logs — must return 200 |
| **Outstanding Questions** | Should an IT Administrator role have audit log access? |
| **Severity** | **MEDIUM** |

---

### T-018: Sensitive Data in Error Responses

| Field | Detail |
|-------|--------|
| **Threat ID** | T-018 |
| **Threat** | Production error responses include Django debug stack traces, internal file paths, database schema details, or environment variable values |
| **Attack Scenario** | An unhandled exception in production returns a Django debug page or DRF exception detail with internal implementation information |
| **Proposed Mitigation** | `DEBUG=False` in production (fail-closed check prevents startup with `DEBUG=True`); custom DRF exception handler returns generic error messages in production; Sentry captures full stack traces server-side (not in response); `500` response body: `{"detail": "Internal server error", "correlation_id": "<uuid>"}` only |
| **Validation Method** | Test: trigger a 500 error in production-like environment; confirm response body contains no stack trace, file paths, or internal details |
| **Outstanding Questions** | Sentry DSN to be provisioned before production launch |
| **Severity** | **HIGH** |

---

### T-019: WhatsApp Webhook Spoofing

| Field | Detail |
|-------|--------|
| **Threat ID** | T-019 |
| **Threat** | Attacker sends fake WhatsApp webhook events to the HRMS webhook endpoint, triggering fraudulent notifications or data changes |
| **Attack Scenario** | Attacker discovers webhook URL and sends POST with fabricated delivery status or incoming message payload; HRMS processes it as legitimate |
| **Proposed Mitigation** | Meta Cloud API includes `X-Hub-Signature-256` HMAC-SHA256 signature in webhook headers; HRMS verifies signature using `WHATSAPP_WEBHOOK_SECRET` before processing any webhook payload; reject (return 400) if signature missing or invalid; constant-time comparison to prevent timing attacks |
| **Validation Method** | Test: send webhook POST with invalid signature — must return 400 and not process payload. Test: send with valid signature — must process normally |
| **Outstanding Questions** | WhatsApp Business Account setup and webhook URL registration — see OD-010 |
| **Severity** | **HIGH** |

---

### T-020: Mass Student Data Export Without Authorization

| Field | Detail |
|-------|--------|
| **Threat ID** | T-020 |
| **Threat** | A low-privilege user exports the entire student database (PII, academic records) in bulk |
| **Attack Scenario** | Placement Officer calls export endpoint with no filters, downloading all 10,000 student records including PII, CGPA, phone numbers |
| **Proposed Mitigation** | Export endpoints require `PLACEMENT_HEAD` role for full export; officers can export only their assigned cohort/drive students; export scope enforced server-side (query filtered by role); audit log records every export action with actor, scope, and row count; rate limit on export endpoints |
| **Validation Method** | Test: Placement Officer attempts unscoped full export — must return only their assigned students. Test: audit log entry created for every export action |
| **Outstanding Questions** | (see OD-020) What is the authorized export scope for each role? |
| **Severity** | **HIGH** |

---

## 4. Security Controls Baseline

The following table summarizes the proposed baseline security controls:

### 4.1 Authentication Controls

| Control | Proposed Implementation | Status |
|---------|------------------------|--------|
| Password hashing | Argon2id via `django-argon2` | Proposed |
| JWT storage | HttpOnly cookies (not localStorage) | Proposed |
| Token expiry | Short-lived access token (15 min); refresh (7 days) | Proposed — needs GQT confirmation |
| Token blacklist | `rest_framework_simplejwt.token_blacklist` on logout | Proposed |
| Brute force protection | DRF `AnonRateThrottle` on login endpoint | Proposed |
| Password complexity | Django `AUTH_PASSWORD_VALIDATORS` (min length, common password check) | Proposed |
| Multi-factor auth | Not in scope for first release (to be decided) | Deferred |

### 4.2 Authorization Controls

| Control | Proposed Implementation | Status |
|---------|------------------------|--------|
| Default deny | Custom `DenyByDefault` permission class as base | Proposed |
| Role-based access | JWT role claim verified on every request | Proposed |
| Object-level permissions | `IsStudentOwnerOrStaff`, `IsSelectedCandidateOrStaff` etc. | Proposed |
| Field-level authorization | Serializer `to_representation()` filters fields by role | Proposed |
| Approval independence | Self-approval prevention (OD-003 — needs GQT decision) | Open Decision |

### 4.3 Input Validation Controls

| Layer | Control | Proposed Implementation |
|-------|---------|------------------------|
| Frontend | Schema validation | Zod schemas on all form inputs |
| Backend | Request validation | DRF serializer `validate_*` methods |
| File uploads | Magic bytes check | `%PDF-` prefix required |
| File uploads | Size limit | 5MB maximum enforced in view |
| File uploads | Extension check | `.pdf` only for resumes and offer letters |
| SQL | Parameterized queries | Django ORM; raw queries use parameterization |
| Templates | Auto-escaping | Django templates escape by default; DRF JSON responses |

### 4.4 API Security Controls

| Control | Proposed Implementation |
|---------|------------------------|
| API versioning | All endpoints at `/api/v1/` — breaking changes require new version |
| Rate limiting | DRF `UserRateThrottle` and `AnonRateThrottle` on all endpoints |
| CORS | `CORS_ALLOWED_ORIGINS` whitelist; no wildcard in production |
| HTTPS | `SECURE_SSL_REDIRECT=True`; `HSTS_SECONDS=31536000` |
| Content type | `Content-Type: application/json` enforced; no XML |
| Schema exposure | OpenAPI schema endpoint requires authentication in production |

### 4.5 Production Hardening Controls

| Control | Proposed Check |
|---------|---------------|
| `DEBUG=False` | Fail-closed startup check |
| No wildcard `ALLOWED_HOSTS` | Fail-closed startup check |
| Strong `SECRET_KEY` | Fail-closed startup check (min 50 chars) |
| SSL required | `SECURE_SSL_REDIRECT=True` enforced |
| Secure cookies | `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True` |
| Security headers | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin` |

### 4.6 Logging and Observability Controls

| Control | Proposed Implementation |
|---------|------------------------|
| Structured logging | JSON log format in production |
| Correlation IDs | UUID per request; logged and returned in error responses |
| Sensitive field redaction | `password`, `token`, `secret`, `key`, `authorization`, `cookie` fields never logged |
| No credentials in logs | Enforced by redaction filter and code review |
| Audit log | Append-only; actor, action, entity, timestamp, IP address |
| Error capture | Sentry-compatible SDK (DSN provided via environment) |

### 4.7 Data Export Controls

| Control | Proposed Implementation |
|---------|------------------------|
| Formula injection prevention | Prefix CSV cells starting with `=`, `+`, `-`, `@` with `'` |
| Export scope enforcement | Backend filters export by actor's authorized scope |
| Export audit | Every export action logged with actor, scope, row count, timestamp |
| Rate limiting | Export endpoints throttled separately (lower limit) |

---

## 5. Compliance Considerations

> [!IMPORTANT]
> This section identifies **relevant considerations** for GQT's attention. It does **not** claim compliance with any regulation or standard. Formal legal and compliance review must be conducted by GQT.

### 5.1 Personal Data Handling (Student PII)

The HRMS stores and processes personally identifiable information (PII) for students:
- Name, email address, phone number, roll number, home address
- Academic performance data (CGPA, backlog history)
- Career outcome data (placement company, CTC, joining date)

**Considerations:**
- A data processing policy should define the lawful basis for processing student PII.
- Students may have rights to access, correct, or request deletion of their personal data — GQT must decide if and how to support these rights.
- Data shared with third parties (e.g., companies receiving candidate rosters) should be covered by appropriate agreements.

### 5.2 Data Retention Policies

Currently **undefined** — this is an open decision:

| Data Category | Proposed Minimum Retention | GQT Decision Required |
|---|---|---|
| Audit logs | 1 year | Yes (OD-011) |
| Student PII | Duration of engagement + X years | Yes |
| Offer letters | Permanent (legal record) | Confirm with GQT |
| Communication logs | 90 days | Yes |
| Integration credentials | Until rotated | Define rotation schedule |

### 5.3 Right to Access / Right to Delete (Student Data)

- The system **may** need to support student data access requests (export of their own data).
- The system **may** need to support deletion or anonymization of a former student's PII.
- **Decision required from GQT:** Is self-service data access/deletion a requirement? (see OD-004 regarding student self-service)

### 5.4 Backup, Recovery, and Business Continuity

| Metric | Current Status | Recommendation |
|--------|---------------|---------------|
| Recovery Time Objective (RTO) | **Undefined** | GQT to define |
| Recovery Point Objective (RPO) | **Undefined** | GQT to define |
| Backup frequency | **Undefined** | Minimum: daily automated backup |
| Backup location | **Undefined** | Off-site / separate provider |
| Backup test frequency | **Undefined** | Quarterly restore test recommended |

### 5.5 Third-Party Integration Security

- The GQT Student Portal integration exchanges student data between two systems.
- The data sharing boundary and authorization contract must be formally defined.
- Integration credentials must have the minimum required permissions (principle of least privilege).
- The Portal team must be consulted on their data handling policies.

---

*End of Document 08 — Data Classification and Initial Threat Review*

