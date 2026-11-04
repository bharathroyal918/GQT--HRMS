# 07 — Proposed System Architecture

> **Status:** Phase 0 Documentation — Not Approved for Implementation
> **Prepared:** 2026-11-03
> **Project:** GQT HRMS & Recruitment CRM Platform

---

> [!IMPORTANT]
> This document describes a **proposed** architecture. Every design decision herein is preliminary and requires GQT review and approval before any implementation work begins. See `09-architecture-decision-records.md` for individual ADRs.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Backend Architecture](#2-backend-architecture)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Authentication Architecture](#4-authentication-architecture)
5. [Database Architecture](#5-database-architecture)
6. [File Storage Architecture](#6-file-storage-architecture)
7. [Background Jobs](#7-background-jobs)
8. [Design System](#8-design-system)
9. [Environment Configuration](#9-environment-configuration)
10. [Infrastructure (Proposed)](#10-infrastructure-proposed)

---

## 1. Architecture Overview

The GQT HRMS & Recruitment CRM Platform is a **multi-module, single-tenant web application** serving the Training & Placement (T&P) operations of GQT. It provides:

- A **React SPA** frontend consumed by staff roles (Placement Head, Officers, Trainers, Coordinators) and optionally Students.
- A **Django/DRF REST API** backend that enforces all business rules, permissions, and data integrity.
- An **integration layer** to the existing **GQT Student Portal** (separate system), consuming its TPO APIs.
- **Background job workers** (Celery) for reminders, notifications, and portal sync.
- **Pluggable adapters** for Email (SMTP) and WhatsApp (Meta Cloud API).

### 1.1 High-Level Architecture Diagram

```mermaid
flowchart TD
    Browser["🌐 Browser / Client"]

    subgraph DMZ["DMZ — Nginx Reverse Proxy"]
        Nginx["Nginx\n(SSL termination, static files,\nproxy_pass to backend)"]
    end

    subgraph Frontend["HRMS Frontend (Vite / React SPA)"]
        ReactApp["React 19 + TypeScript\nTailwind CSS\nTanStack Query\nReact Hook Form + Zod\nAxios (HttpOnly cookie JWT)"]
    end

    subgraph Backend["HRMS Backend (Django 5.1.x / DRF)"]
        API["REST API\n/api/v1/"]
        AuthLayer["Auth & RBAC Layer\n(JWT HttpOnly Cookies,\nDeny-by-default)"]
        ServiceLayer["Service Layer\n(Selectors → Services)"]
        CeleryWorker["Celery Worker\n(Background Jobs)"]
        CeleryBeat["Celery Beat\n(Scheduled Tasks)"]
    end

    subgraph DataStores["Data Stores"]
        PG["PostgreSQL 16\n(Primary Database)"]
        Redis["Redis\n(Cache + Celery Broker)"]
        FileStorage["Private File Storage\n(media/ — not public URL)"]
    end

    subgraph ExternalServices["External Services"]
        StudentPortal["GQT Student Portal API\n/api/v1/tpo/\n(Service-to-Service)"]
        EmailSMTP["Email Provider\n(SMTP Adapter)"]
        WhatsApp["WhatsApp Provider\n(Meta Cloud API Adapter)"]
    end

    Browser -->|"HTTPS"| Nginx
    Nginx -->|"Static assets"| ReactApp
    Nginx -->|"proxy_pass /api/"| API
    ReactApp -->|"Axios + HttpOnly cookie\n/api/v1/"| Nginx

    API --> AuthLayer
    AuthLayer --> ServiceLayer
    ServiceLayer --> PG
    ServiceLayer --> FileStorage
    ServiceLayer --> Redis

    API --> CeleryWorker
    CeleryBeat --> CeleryWorker
    CeleryWorker --> Redis
    CeleryWorker --> PG
    CeleryWorker --> StudentPortal
    CeleryWorker --> EmailSMTP
    CeleryWorker --> WhatsApp

    ServiceLayer -->|"Sync calls (proposed)"| StudentPortal
```

### 1.2 Architectural Principles

| Principle | Description |
|-----------|-------------|
| **Security by default** | Deny-by-default RBAC; no permission = no access |
| **Backend is the authority** | All business rules enforced server-side; frontend role checks are display-only |
| **No public file URLs** | All sensitive files streamed via authenticated endpoints |
| **Fail-closed configuration** | Production with weak or missing secrets raises `ImproperlyConfigured` at startup |
| **Pluggable integrations** | Email and WhatsApp use adapter interfaces; dev uses simulated/console adapters |
| **Observable** | Structured logging with correlation IDs; Sentry-compatible error capture |
| **Idempotent jobs** | Background tasks use `select_for_update(skip_locked=True)` to prevent duplicates |

---

## 2. Backend Architecture

### 2.1 Django Project Structure (Proposed)

```
gqt_hrms/                          ← Repository root
├── config/                        ← Project configuration package
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py                ← Shared settings
│   │   ├── development.py         ← Dev overrides (DEBUG=True, console email)
│   │   └── production.py          ← Production (fail-closed, SSL, Argon2)
│   ├── urls.py                    ← Root URL config (delegates to /api/v1/)
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py                  ← Celery app definition
├── apps/                          ← All domain application modules
│   ├── core/                      ← Base models, mixins, utilities, audit log
│   ├── accounts/                  ← Users, roles, JWT auth, RBAC
│   ├── crm/                       ← Companies, HR contacts, outreach, follow-ups
│   ├── jobs/                      ← Job descriptions, verification checklist, approvals
│   ├── creatives/                 ← Creative requests, assets, review workflow
│   ├── students/                  ← Student profiles, resumes, eligibility
│   ├── preparation/               ← Resume review, assessments, mock interviews
│   ├── submissions/               ← Candidate rosters, dispatch
│   ├── interviews/                ← Interview rounds, attendance, results
│   ├── placements/                ← Offers, acceptance, joining, deferral
│   ├── feedback/                  ← Post-placement feedback
│   ├── analytics/                 ← Reports, dashboards, export
│   └── ai/                        ← AI features (JD parser, outreach assistant, etc.)
├── manage.py
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── .env.example
├── pytest.ini
└── docker-compose.yml
```

### 2.2 Service Layer Pattern

The proposed service layer follows a strict separation of concerns:

```mermaid
flowchart LR
    M["Models\n(Django ORM)"]
    S["Selectors\n(Read-only queries,\nno business logic)"]
    SV["Services\n(Write operations,\nbusiness rules,\natomic transactions)"]
    SR["Serializers\n(Validation,\nrepresentation,\nfield-level auth)"]
    V["Views / ViewSets\n(HTTP layer only,\nno business logic)"]

    M --> S
    M --> SV
    S --> SR
    SV --> SR
    SR --> V
```

| Layer | Responsibility | Rules |
|-------|---------------|-------|
| **Models** | Schema, constraints, properties | No business logic beyond field validation |
| **Selectors** | Read queries, filtering, prefetch | No writes; returns QuerySets or instances |
| **Services** | Create/update/delete, state transitions, triggers | `@transaction.atomic` for multi-step ops; raises domain exceptions |
| **Serializers** | Input validation, output representation, field-level permissions | No database writes |
| **Views** | HTTP method dispatch, throttling, auth decorators | Calls selectors/services; no direct ORM queries |

### 2.3 Settings Architecture

```python
# Production fail-closed checks (example — not implementation):
# settings/production.py raises ImproperlyConfigured if:
# - len(SECRET_KEY) < 50
# - '*' in ALLOWED_HOSTS
# - DATABASE_URL contains default password 'postgres'
# - SECURE_SSL_REDIRECT is not True
# - SESSION_COOKIE_SECURE is not True
```

| Setting File | Context | Notable Behavior |
|---|---|---|
| `base.py` | All environments | Shared apps, middleware, Auth backends, logging skeleton |
| `development.py` | Local dev | DEBUG=True, console email, relaxed CORS, SQLite optional |
| `production.py` | Production | Fail-closed checks, SSL, Argon2, structured JSON logging |

### 2.4 URL Structure

```
/api/v1/
├── auth/                  ← accounts app (login, logout, refresh, me)
├── users/                 ← accounts app (user management)
├── companies/             ← crm app
├── hr-contacts/           ← crm app
├── outreach/              ← crm app
├── jobs/                  ← jobs app
├── creatives/             ← creatives app
├── students/              ← students app
├── resumes/               ← students app (file endpoints)
├── preparation/           ← preparation app
├── submissions/           ← submissions app
├── interviews/            ← interviews app
├── placements/            ← placements app
├── feedback/              ← feedback app
├── analytics/             ← analytics app
├── ai/                    ← ai app
└── schema/                ← OpenAPI schema (drf-spectacular)
```

### 2.5 App Module Summary

| App | API Prefix | Core Responsibility |
|-----|-----------|---------------------|
| `core` | — | Base models, mixins (UUIDModel, TimestampMixin, SoftDeleteMixin), audit log, exceptions |
| `accounts` | `/api/v1/auth/`, `/api/v1/users/` | User management, role assignment, JWT auth, token blacklist |
| `crm` | `/api/v1/companies/`, `/api/v1/hr-contacts/`, `/api/v1/outreach/` | Company database, HR contact CRM, outreach campaigns, follow-up scheduler |
| `jobs` | `/api/v1/jobs/` | Job descriptions, 5-point verification checklist, approval workflow, JD lock |
| `creatives` | `/api/v1/creatives/` | Creative asset requests, versioning, design review, approval |
| `students` | `/api/v1/students/`, `/api/v1/resumes/` | Student profiles, PDF resume upload, eligibility engine, cohort management |
| `preparation` | `/api/v1/preparation/` | Resume feedback, aptitude assessments, mock interviews, readiness gate |
| `submissions` | `/api/v1/submissions/` | Candidate roster creation, Excel dispatch, company acknowledgement |
| `interviews` | `/api/v1/interviews/` | Interview rounds, schedules, attendance, result recording, follow-up |
| `placements` | `/api/v1/placements/` | Offer letters, acceptance, CTC, joining date, deferral |
| `feedback` | `/api/v1/feedback/` | Post-placement student and employer feedback |
| `analytics` | `/api/v1/analytics/` | Placement statistics, reports, exports |
| `ai` | `/api/v1/ai/` | JD parser, outreach assistant, resume analyzer, mock interview engine |

---

## 3. Frontend Architecture

### 3.1 Technology Stack

| Technology | Role |
|-----------|------|
| React 19 + TypeScript (strict) | UI framework |
| Vite | Build tool and dev server |
| Tailwind CSS | Utility-first styling with GQT brand tokens |
| TanStack Query v5 | Server state management, caching, background refetch |
| React Hook Form + Zod | Form state and validation |
| Axios | HTTP client with interceptor chain |
| React Router v6 | Client-side routing with protected routes |

### 3.2 Directory Structure (Proposed)

```
frontend/
├── src/
│   ├── api/               ← Axios instance, per-module API client functions
│   │   ├── client.ts      ← Configured Axios instance (baseURL, interceptors)
│   │   ├── auth.ts
│   │   ├── companies.ts
│   │   ├── jobs.ts
│   │   └── ...
│   ├── components/        ← Shared/reusable UI components
│   │   ├── ui/            ← Primitives (Button, Input, Card, Badge, etc.)
│   │   ├── layout/        ← AppShell, Sidebar, Header
│   │   ├── tables/        ← DataTable with search/filter/sort/pagination
│   │   ├── states/        ← LoadingState, EmptyState, ErrorState
│   │   └── workflow/      ← WorkflowRoadmap, StatusBadge
│   ├── pages/             ← Route-level page components (feature modules)
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── companies/
│   │   ├── jobs/
│   │   ├── students/
│   │   └── ...
│   ├── context/           ← React context providers (AuthContext, ThemeContext)
│   ├── hooks/             ← Custom hooks (useAuth, usePermission, useDebounce)
│   ├── lib/               ← Utilities (date formatting, file download, cn helper)
│   ├── types/             ← TypeScript interfaces and type definitions
│   ├── schemas/           ← Zod validation schemas (form validation)
│   └── test/              ← Test setup, factories, MSW handlers
│       ├── setup.ts
│       ├── factories/
│       └── handlers/
├── public/
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json          ← strict: true
└── vitest.config.ts
```

### 3.3 State Management Architecture

```mermaid
flowchart TD
    subgraph ServerState["Server State — TanStack Query"]
        QCache["Query Cache\n(auto-invalidation, background refetch)"]
        Mutations["Mutations\n(optimistic updates, error rollback)"]
    end

    subgraph ClientState["Client State — React Context / useState"]
        AuthCtx["AuthContext\n(current user, role, permissions)"]
        UIState["UI State\n(sidebar open, modal state)"]
    end

    subgraph FormState["Form State — React Hook Form + Zod"]
        Schema["Zod Schema\n(runtime type validation)"]
        RHF["React Hook Form\n(field registration, errors, submission)"]
    end

    API["Axios API Client\n(/api/v1/)"] --> QCache
    Mutations --> API
    Schema --> RHF
    QCache --> AuthCtx
```

### 3.4 Routing and Protected Routes

```
/ (AppShell layout)
├── /login                           ← Public
├── /dashboard                       ← Authenticated
├── /companies                       ← PLACEMENT_HEAD, PLACEMENT_OFFICER
├── /jobs                            ← PLACEMENT_HEAD, PLACEMENT_OFFICER
├── /students                        ← All staff roles
├── /students/:id/profile            ← All staff roles
├── /preparation                     ← TRAINER, PLACEMENT_OFFICER
├── /submissions                     ← PLACEMENT_HEAD, PLACEMENT_OFFICER
├── /interviews                      ← PLACEMENT_HEAD, PLACEMENT_OFFICER, INTERVIEW_COORDINATOR
├── /placements                      ← PLACEMENT_HEAD, PLACEMENT_OFFICER
├── /analytics                       ← PLACEMENT_HEAD
└── /settings                        ← PLACEMENT_HEAD (admin)
```

> [!NOTE]
> Frontend route guards are **display-only**. All authorization is enforced by the Django backend. A user who bypasses a frontend guard will receive a `403 Forbidden` from the API.

### 3.5 Axios Instance and JWT Interceptors

The proposed Axios instance will:
1. Set `withCredentials: true` so browsers send `gqt_access_token` HttpOnly cookie automatically.
2. On `401` response: attempt a silent token refresh via `POST /api/v1/auth/token/refresh/`.
3. On successful refresh: retry the original request once.
4. On refresh failure: clear auth state and redirect to `/login`.
5. Attach a `X-Correlation-ID` request header (UUID) for log tracing.
6. Never read, write, or log JWT token values from JavaScript.

---

## 4. Authentication Architecture

### 4.1 JWT Token Strategy

| Property | Value |
|----------|-------|
| Access token cookie name | `gqt_access_token` |
| Refresh token cookie name | `gqt_refresh_token` |
| Storage location | HttpOnly cookies **only** |
| `SameSite` attribute | `Lax` |
| `Secure` attribute | `True` in production, `False` in dev (HTTP) |
| `HttpOnly` attribute | `True` (JavaScript cannot read) |
| Access token lifetime | Short (proposed: 15 minutes — subject to GQT decision) |
| Refresh token lifetime | Longer (proposed: 7 days — subject to GQT decision) |
| localStorage/sessionStorage | **Never used for tokens** |

### 4.2 Token Lifecycle

```mermaid
sequenceDiagram
    participant Browser
    participant Nginx
    participant API as Django API
    participant DB as PostgreSQL
    participant BL as Token Blacklist

    Browser->>Nginx: POST /api/v1/auth/login/ {credentials}
    Nginx->>API: forward
    API->>DB: validate credentials (Argon2)
    DB-->>API: user object
    API-->>Browser: Set-Cookie: gqt_access_token (HttpOnly)\nSet-Cookie: gqt_refresh_token (HttpOnly)

    Note over Browser: Subsequent requests

    Browser->>Nginx: GET /api/v1/jobs/ (cookie auto-sent)
    Nginx->>API: forward with cookies
    API->>API: validate JWT from cookie
    API-->>Browser: 200 OK + data

    Note over Browser: Access token expires

    Browser->>API: POST /api/v1/auth/token/refresh/ (refresh cookie sent)
    API-->>Browser: New Set-Cookie: gqt_access_token

    Note over Browser: Logout

    Browser->>API: POST /api/v1/auth/logout/
    API->>BL: blacklist refresh token
    API-->>Browser: Clear-Cookie headers
```

### 4.3 RBAC Architecture

| Layer | Mechanism | Authority |
|-------|-----------|-----------|
| **Backend permission classes** | Django REST Framework `permission_classes`, custom `DenyByDefault` | **Authoritative** |
| **Object-level permissions** | `IsStudentOwnerOrStaff`, `IsSelectedCandidateOrStaff`, etc. | **Authoritative** |
| **Frontend route guards** | React `<ProtectedRoute role="PLACEMENT_HEAD">` | Display-only |
| **Frontend UI visibility** | `usePermission()` hook hides buttons | Display-only |

> [!CAUTION]
> Never rely on frontend role checks for security. They exist solely to improve UX by hiding irrelevant UI elements. The backend must independently verify every request.

### 4.4 Proposed Roles

| Role | Description |
|------|-------------|
| `PLACEMENT_HEAD` | Full system access; approves jobs, overrides, sees analytics |
| `PLACEMENT_OFFICER` | Manages companies, students, submissions, interviews |
| `TRAINER` | Student preparation module; limited profile read |
| `INTERVIEW_COORDINATOR` | Interview scheduling and result entry |
| `STUDENT` | Self-service portal (if enabled — see OD-004) |
| `SYSTEM` | Internal service account for Celery/integration tasks |

---

## 5. Database Architecture

### 5.1 PostgreSQL 16 Configuration

| Property | Value |
|----------|-------|
| Engine | PostgreSQL 16 |
| Driver | `psycopg3` (psycopg) |
| ORM | Django ORM (no raw queries except where documented) |
| Connection | `DATABASE_URL` via `django-environ` |
| SSL | Required in production (`sslmode=require`) |

### 5.2 Base Model Mixins (Proposed)

```python
# Proposed — not implementation code
# apps/core/models.py

class UUIDModel(models.Model):
    """All models use UUID primary keys (not sequential integers)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimestampMixin(models.Model):
    """Audit timestamps on all records."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """PROPOSED — needs GQT decision (OD-005 related). Marks records deleted without removing."""
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        abstract = True
```

> [!NOTE]
> **Soft delete is proposed** and requires a GQT decision. Hard deletes with cascade or PROTECT foreign keys are the alternative. See `11-open-decisions-and-assumptions.md`.

### 5.3 UUID Primary Keys Rationale

- Prevents IDOR attacks via sequential ID enumeration (e.g., `/students/1/`, `/students/2/`).
- UUIDs are globally unique, safe to expose in URLs.
- PostgreSQL 16 supports UUID natively with efficient B-tree indexing.

### 5.4 Migration Strategy

| Practice | Approach |
|----------|----------|
| Migration generation | `python manage.py makemigrations` — never edited manually |
| Migration consistency check | CI step: `makemigrations --check --dry-run` must exit 0 |
| Backward compatibility | Additive migrations preferred; destructive changes require review |
| Zero-downtime migrations | Additive first, then data migration, then constraint enforcement (multi-step) |
| Squashing | Periodic squash after stable releases |

### 5.5 Index Strategy (Proposed)

| Table | Composite Index Candidates |
|-------|---------------------------|
| `students` | `(cohort_year, eligibility_status)`, `(portal_student_id)` |
| `jobs` | `(status, created_at)`, `(company_id, status)` |
| `interviews` | `(scheduled_at, status)`, `(job_id, round_number)` |
| `placements` | `(student_id, status)`, `(offer_status, joining_date)` |
| `audit_logs` | `(entity_type, entity_id, created_at)`, `(actor_id, created_at)` |

### 5.6 Transaction Strategy

All multi-step state transitions must use `@transaction.atomic`:

- Job approval (status update + audit log + notification trigger)
- Candidate submission dispatch (roster lock + status update + acknowledgement)
- Offer letter issuance (placement record + file association + status change)
- Student eligibility override (eligibility update + audit entry + reason record)

---

## 6. File Storage Architecture

### 6.1 Storage Principles

| Principle | Implementation |
|-----------|---------------|
| No public URLs | Files never served directly by Nginx; always via Django `FileResponse` |
| Authentication required | Every file request validated against user's role and object ownership |
| Object-level isolation | Resumes: student owner or staff only; Offer letters: SELECTED candidate or staff only |
| Format restriction | PDFs only for resumes and offer letters (magic bytes enforced) |
| Size limit | 5 MB maximum per file upload |
| Integrity | SHA-256 hash stored at upload; verified on retrieval |

### 6.2 Upload Validation Pipeline

```mermaid
flowchart TD
    Upload["File Upload Request"] --> ExtCheck["Extension check\n(.pdf only)"]
    ExtCheck --> SizeCheck["Size check\n(≤ 5MB)"]
    SizeCheck --> MagicBytes["Magic bytes check\n('%PDF-' header)"]
    MagicBytes --> HashCalc["SHA-256 hash\n(stored to DB)"]
    HashCalc --> AuthCheck["Object-level auth\n(IsStudentOwnerOrStaff)"]
    AuthCheck --> Store["Store to media/\nyear/month/uuid_filename.pdf"]
    Store --> AuditLog["Audit log entry"]
    AuditLog --> Response["201 Created + metadata (no file URL)"]

    ExtCheck -->|Fail| Reject400["400 Bad Request"]
    SizeCheck -->|Fail| Reject413["413 Payload Too Large"]
    MagicBytes -->|Fail| Reject400
    AuthCheck -->|Fail| Reject403["403 Forbidden"]
```

### 6.3 Storage Path Convention (Proposed)

```
media/
├── resumes/
│   └── 2026/11/
│       └── {uuid}_{original_name_sanitized}.pdf
└── offer_letters/
    └── 2026/11/
        └── {uuid}_{original_name_sanitized}.pdf
```

### 6.4 File Download Endpoint

```
GET /api/v1/resumes/{uuid}/download/
  → Permission: IsStudentOwnerOrStaff
  → Returns: FileResponse (Content-Disposition: attachment)

GET /api/v1/placements/{uuid}/offer-letter/download/
  → Permission: IsSelectedCandidateOrStaff
  → Returns: FileResponse (Content-Disposition: attachment)
```

---

## 7. Background Jobs

### 7.1 Celery Architecture (Proposed)

```mermaid
flowchart LR
    subgraph Django["Django Application"]
        Views["API Views"]
        Services["Service Layer"]
        Beat["Celery Beat\n(Scheduler)"]
    end

    subgraph Broker["Redis (Broker + Cache)"]
        Queue["Task Queue"]
        ResultBackend["Result Backend"]
    end

    subgraph Workers["Celery Workers"]
        RemindersWorker["Interview Reminder Worker"]
        SyncWorker["Portal Sync Worker"]
        NotifyWorker["Email/WhatsApp Worker"]
        EscalationWorker["Follow-up Escalation Worker"]
    end

    subgraph External["External Services"]
        SMTP["SMTP Email Adapter"]
        WhatsApp["WhatsApp Adapter\n(Meta Cloud API)"]
        Portal["GQT Student Portal API"]
    end

    Services -->|"delay() / apply_async()"| Queue
    Beat -->|"Periodic tasks"| Queue
    Queue --> RemindersWorker
    Queue --> SyncWorker
    Queue --> NotifyWorker
    Queue --> EscalationWorker

    RemindersWorker --> SMTP
    RemindersWorker --> WhatsApp
    NotifyWorker --> SMTP
    NotifyWorker --> WhatsApp
    SyncWorker --> Portal
```

### 7.2 Proposed Task Inventory

| Task | Trigger | Frequency | Idempotency Mechanism |
|------|---------|-----------|----------------------|
| Interview reminder (24h) | Celery Beat | Hourly check | `skip_locked=True` on task lock record |
| Interview reminder (2h) | Celery Beat | Every 15 min | `skip_locked=True` |
| Interview reminder (30min) | Celery Beat | Every 5 min | `skip_locked=True` |
| Follow-up escalation | Celery Beat | Daily | `select_for_update(skip_locked=True)` |
| Portal student sync | Celery Beat | Configurable | Idempotent upsert by `portal_student_id` |
| Email dispatch | Service trigger | On-demand | Task deduplication key |
| WhatsApp dispatch | Service trigger | On-demand | Task deduplication key |

### 7.3 Idempotency Pattern

```python
# Proposed pattern — not implementation code
# Prevents duplicate reminder sends under concurrent workers

with transaction.atomic():
    reminder = InterviewReminder.objects.select_for_update(
        skip_locked=True
    ).filter(
        interview=interview,
        reminder_type='24H',
        sent=False,
        scheduled_at__lte=timezone.now()
    ).first()

    if not reminder:
        return  # Already locked by another worker or already sent

    # send notification...
    reminder.sent = True
    reminder.sent_at = timezone.now()
    reminder.save()
```

---

## 8. Design System

### 8.1 Color Tokens

| Token Name | Hex Value | Usage |
|-----------|----------|-------|
| `--color-deep-navy` | `#001B4D` | Primary brand; page header, sidebar background |
| `--color-vivid-blue` | `#005BBB` | Primary action buttons, links, active states |
| `--color-charcoal` | `#1E293B` | Body text, secondary headings |
| `--color-neutral-gray` | `#64748B` | Secondary text, placeholder text, borders |
| `--color-light-gray` | `#F1F5F9` | Page backgrounds, card backgrounds |
| `--color-white` | `#FFFFFF` | Card surfaces, input backgrounds |

**Status colors** (must be paired with icon + label — not color alone):

| Status | Color | Icon | Label |
|--------|-------|------|-------|
| Success / Placed | `#16A34A` (green-600) | ✓ checkmark | "Placed" |
| Warning / Pending | `#D97706` (amber-600) | ⚠ triangle | "Pending Review" |
| Error / Rejected | `#DC2626` (red-600) | ✕ cross | "Rejected" |
| Info / Draft | `#2563EB` (blue-600) | ℹ info | "Draft" |
| Neutral / Inactive | `#64748B` (neutral-gray) | — dash | "Inactive" |

> [!IMPORTANT]
> Status indicators must **never** rely on color alone. Every status must display an icon + text label + color to meet WCAG 2.1 AA accessibility requirements and to serve colorblind users.

### 8.2 Typography Scale (Proposed)

| Scale | Tailwind Class | Usage |
|-------|--------------|-------|
| Page Title | `text-2xl font-bold` | Page `<h1>` |
| Section Heading | `text-xl font-semibold` | Section `<h2>` |
| Card Title | `text-lg font-semibold` | Card headings `<h3>` |
| Body | `text-base` (16px) | Default body text |
| Body Small | `text-sm` (14px) | Table data, secondary info |
| Caption | `text-xs` (12px) | Timestamps, helper text |
| Font Family | `Inter` (sans-serif) | All UI text |

### 8.3 Spacing System

Tailwind CSS default spacing scale (4px base unit):
- `space-1` = 4px, `space-2` = 8px, `space-4` = 16px, `space-6` = 24px, `space-8` = 32px, `space-12` = 48px

Standard component spacing:
- Page padding: `px-6 py-8` (desktop), `px-4 py-6` (mobile)
- Card padding: `p-6`
- Form field gap: `space-y-4`
- Table cell padding: `px-4 py-3`

### 8.4 Component Library (Proposed)

| Component | Props / Variants | Notes |
|-----------|----------------|-------|
| `Button` | `variant: primary\|secondary\|danger\|ghost`, `size: sm\|md\|lg`, `loading`, `disabled` | Loading state shows spinner; disabled prevents click |
| `Card` | `title`, `description`, `actions`, `footer` | Standard container for content blocks |
| `Input` | `label`, `error`, `helperText`, `required`, `disabled` | Pairs with React Hook Form `register()` |
| `StatusBadge` | `status`, `showIcon` | Icon + label + color; never color-only |
| `EmptyState` | `icon`, `title`, `description`, `action` | Shown when list is empty; must always include action |
| `ErrorState` | `title`, `description`, `retry` | Shown on API error; retry calls `refetch()` |
| `LoadingState` | `rows` (skeleton count) | Skeleton loaders; not spinner-only |
| `WorkflowRoadmap` | `steps`, `currentStep`, `orientation` | Visual pipeline tracker for multi-step workflows |
| `DataTable` | `columns`, `data`, `pagination`, `filters`, `bulkActions` | Standard table with server-side pagination |

### 8.5 Data Display Standards

All list/table views must include:
- **Search**: debounced text search (300ms), sent as query param to backend
- **Filter**: by relevant status, date range, role-specific fields
- **Sort**: by common fields (created_at, name, status); server-side
- **Pagination**: server-side; page size selector (10/25/50)
- **Bulk actions**: checkbox selection + bulk status change / export
- **Export**: CSV/PDF download for authorized roles with formula injection protection

### 8.6 Application Layout

```mermaid
flowchart TD
    AppShell["AppShell"]
    Sidebar["Sidebar Navigation\n(role-aware — shows only permitted modules)\n• Dashboard\n• Companies (staff only)\n• Jobs\n• Students\n• Preparation\n• Submissions\n• Interviews\n• Placements\n• Analytics (Head only)\n• Settings (Head only)"]
    Header["Header\n• GQT Logo\n• Global Search\n• Notification Bell\n• User Avatar + Role\n• Logout"]
    MainContent["Main Content Area\n(page-specific content)"]

    AppShell --> Sidebar
    AppShell --> Header
    AppShell --> MainContent
```

### 8.7 UI States — All Must Be Handled

Every data-fetching page must explicitly handle all five states:

| State | Component | Trigger |
|-------|-----------|---------|
| **Loading** | `<LoadingState rows={5} />` | TanStack Query `isLoading` |
| **Empty** | `<EmptyState>` with create action | `data.length === 0` |
| **Error** | `<ErrorState retry={refetch}>` | TanStack Query `isError` |
| **Offline** | Banner + cached data indicator | `navigator.onLine === false` |
| **Permission Denied** | Friendly 403 page (not blank) | Backend returns 403 |

### 8.8 Responsive Breakpoints

| Breakpoint | Width | Layout Behavior |
|-----------|-------|----------------|
| Mobile | < 640px | Sidebar collapses to drawer; single-column forms |
| Tablet | 640px–1024px | Sidebar collapses; two-column grids |
| Desktop | > 1024px | Full sidebar; multi-column layouts |

### 8.9 Accessibility Requirements

- WCAG 2.1 AA contrast ratio minimum: 4.5:1 for normal text, 3:1 for large text
- All interactive elements keyboard-navigable (Tab, Enter, Space, Arrow keys)
- All form fields have associated `<label>` elements
- Error messages associated with inputs via `aria-describedby`
- All icons have `aria-label` or `<title>` equivalent
- Focus indicators visible and high-contrast
- Screen reader announcements for dynamic content changes (`aria-live`)

---

## 9. Environment Configuration

### 9.1 .env File Strategy

| Principle | Implementation |
|-----------|---------------|
| Never committed | `.env` in `.gitignore`; only `.env.example` committed |
| Documentation | `.env.example` documents every required key with description and example |
| Loading | `django-environ` reads `.env` at settings load time |
| Validation | Production settings validate all required keys at startup |

### 9.2 Required Environment Variables (Proposed)

```bash
# .env.example — committed to repository

# ── Django Core ─────────────────────────────────────────────────────────────
SECRET_KEY=                         # Min 50 chars; fail-closed if short
DEBUG=False                         # Must be False in production
ALLOWED_HOSTS=                      # Comma-separated; no wildcards in production
DJANGO_SETTINGS_MODULE=config.settings.production

# ── Database ─────────────────────────────────────────────────────────────────
DATABASE_URL=postgresql://user:pass@host:5432/dbname?sslmode=require

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ── CORS ─────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS=https://hrms.gqt.in

# ── JWT Cookie Settings ───────────────────────────────────────────────────────
JWT_COOKIE_SECURE=True              # Must be True in production
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=15
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# ── Email (SMTP) ──────────────────────────────────────────────────────────────
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend  # Use console in dev
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@gqt.in

# ── WhatsApp (Meta Cloud API) ─────────────────────────────────────────────────
WHATSAPP_API_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_WEBHOOK_VERIFY_TOKEN=
WHATSAPP_WEBHOOK_SECRET=           # HMAC-SHA256 signature verification

# ── GQT Student Portal Integration ───────────────────────────────────────────
STUDENT_PORTAL_BASE_URL=https://portal.gqt.in
STUDENT_PORTAL_SERVICE_TOKEN=      # Service account token (see OD-012)
STUDENT_PORTAL_TIMEOUT_SECONDS=10

# ── File Storage ─────────────────────────────────────────────────────────────
MEDIA_ROOT=/var/www/hrms/media/
MAX_UPLOAD_SIZE_MB=5

# ── Observability ─────────────────────────────────────────────────────────────
SENTRY_DSN=                         # Leave blank to disable
LOG_LEVEL=INFO
```

### 9.3 Production Fail-Closed Checks

The following conditions must cause the application to **refuse to start** in production:

| Check | Condition | Error Message |
|-------|-----------|---------------|
| SECRET_KEY length | `len(SECRET_KEY) < 50` | `ImproperlyConfigured: SECRET_KEY too short` |
| ALLOWED_HOSTS wildcard | `'*' in ALLOWED_HOSTS` | `ImproperlyConfigured: Wildcard ALLOWED_HOSTS not permitted` |
| DEBUG in production | `DEBUG=True` | `ImproperlyConfigured: DEBUG must be False in production` |
| SSL redirect | `SECURE_SSL_REDIRECT=False` | `ImproperlyConfigured: SSL redirect must be enabled` |
| Cookie security | `SESSION_COOKIE_SECURE=False` | `ImproperlyConfigured: Secure cookies required` |
| Database password | Password is `postgres` or `password` | Warning logged; consider fail-closed (TBD) |

---

## 10. Infrastructure (Proposed)

> [!WARNING]
> All infrastructure decisions are proposed. Deployment target (Hostinger VPS) is unconfirmed — see OD-016 in `11-open-decisions-and-assumptions.md`.

### 10.1 Nginx Configuration (Proposed)

```
# Proposed nginx responsibility split:
# - SSL/TLS termination (certificate management)
# - Static file serving (frontend build artifacts)
# - Reverse proxy to Django/Gunicorn (/api/v1/, /admin/)
# - Security headers (X-Frame-Options, HSTS, CSP)
# - Rate limiting (connection limits)
# - Gzip compression for static assets
```

### 10.2 Docker Architecture (Proposed)

```yaml
# docker-compose.yml services (proposed — not implementation):
services:
  db:          # PostgreSQL 16
  redis:       # Redis (cache + Celery broker)
  backend:     # Django + Gunicorn
  celery:      # Celery worker
  celery-beat: # Celery beat scheduler
  frontend:    # Node build step (dev only; prod served by nginx)
  nginx:       # Nginx reverse proxy
```

### 10.3 CI/CD Pipeline (Proposed — GitHub Actions)

```mermaid
flowchart LR
    Push["Git Push\n(PR or main)"] --> Checkout["Checkout Code"]
    Checkout --> TypeCheck["TypeScript\ntsc --noEmit"]
    Checkout --> PyCheck["Python\nruff lint + flake8"]

    TypeCheck --> FETest["Frontend Tests\nvitest --run"]
    PyCheck --> BESetup["Setup PostgreSQL 16\nservice container"]

    BESetup --> MigCheck["Migration check\nmakemigrations --check --dry-run"]
    MigCheck --> BETest["Backend Tests\npytest --cov --cov-fail-under=80"]

    FETest --> Gate["Quality Gate\n(all must pass)"]
    BETest --> Gate

    Gate -->|Pass| Deploy["Deploy\n(on main branch only)"]
    Gate -->|Fail| Reject["❌ PR Blocked"]
```

### 10.4 CI Environment Variables

GitHub Actions CI must configure:
- `DATABASE_URL` pointing to the PostgreSQL 16 service container
- `SECRET_KEY` as a test-only secret
- `DJANGO_SETTINGS_MODULE=config.settings.development`
- No real email/WhatsApp credentials (console adapters used)
- No real Student Portal credentials (mocked/stubbed)

### 10.5 Deployment Target Notes

| Item | Status | Notes |
|------|--------|-------|
| VPS Provider | **Unconfirmed** | Prior project notes suggest Hostinger; needs GQT confirmation (OD-016) |
| Server OS | Unknown | Likely Ubuntu LTS (assumption) |
| SSL Certificate | Unknown | Let's Encrypt (proposed) or GQT-managed cert |
| Domain Name | Unknown | `hrms.gqt.in` assumed; needs confirmation |
| Backup Strategy | Unknown | Needs GQT decision (see T-014 in threat review) |

---

*End of Document 07 — Proposed System Architecture*

