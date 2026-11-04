# GQT HRMS & Recruitment CRM Platform — Phase 1: Architecture Baseline

## 1. Executive Overview

This document formalizes the production-oriented technical architecture established during Phase 1 for the **GQT HRMS & Recruitment CRM Platform**, engineered from scratch for **Global Quest Technologies (GQT)**.

### Architectural Tenets
1. **Fresh Implementation**: Zero code, models, migrations, or configurations copied from the predecessor codebase.
2. **Deterministic Quality Gates**: Every merge and deployment is governed by automated tests, migration drift validation, and static type checks.
3. **Deny-by-Default Security**: Unauthenticated requests to non-whitelisted endpoints fail closed; every mutation records an immutable audit log with correlation ID.
4. **Resilient Gateway Boundaries**: The external GQT Student Portal integration is isolated behind a dedicated client gateway with configurable sandbox/mock fallbacks during foundation development.

---

## 2. System Topology & Component Layout

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 CLIENT BROWSER                         │
                  │   React 18/19 SPA + TypeScript Strict + Tailwind CSS   │
                  └──────────────────────────┬─────────────────────────────┘
                                             │ HTTPS / SameSite Cookies
                                             ▼
                  ┌────────────────────────────────────────────────────────┐
                  │               REVERSE PROXY / GATEWAY                  │
                  │         (Nginx in Prod / Vite Proxy in Dev)            │
                  └──────────────────────────┬─────────────────────────────┘
                                             │ /api/v1/*
                                             ▼
                  ┌────────────────────────────────────────────────────────┐
                  │                 DJANGO 5.1 APPLICATION                 │
                  │  ┌───────────────────┐        ┌─────────────────────┐  │
                  │  │ CorrelationIdMid  │───────▶│ SensitiveDataFilter │  │
                  │  └───────────────────┘        └─────────────────────┘  │
                  │                          │                             │
                  │                          ▼                             │
                  │  ┌──────────────────────────────────────────────────┐  │
                  │  │               apps.accounts                      │  │
                  │  │  - User (UUID PK, Normalized Email)              │  │
                  │  │  - RoleCatalog (10 Canonical Institutional Roles)│  │
                  │  │  - JWTCookieAuthentication (HttpOnly tokens)     │  │
                  │  │  - RBAC Permission Classes                       │  │
                  │  └──────────────────────────────────────────────────┘  │
                  │                          │                             │
                  │  ┌──────────────────────────────────────────────────┐  │
                  │  │                  apps.core                       │  │
                  │  │  - TimeStampedModel (UUID Base)                  │  │
                  │  │  - AuditLog (Immutable ORM Records)              │  │
                  │  │  - HealthCheck & Readiness Diagnostics           │  │
                  │  └──────────────────────────────────────────────────┘  │
                  │                          │                             │
                  │  ┌──────────────────────────────────────────────────┐  │
                  │  │                 apps.portal                      │  │
                  │  │  - StudentPortalClient (Retries, Timeouts, Mock) │  │
                  │  │  - Status API View                               │  │
                  │  └──────────────────────────────────────────────────┘  │
                  └──────────────┬──────────────────────────┬──────────────┘
                                 │                          │
                                 ▼                          ▼
                  ┌────────────────────────┐      ┌────────────────────────┐
                  │     DATABASE LAYER     │      │   EXTERNAL SERVICES    │
                  │ PostgreSQL 16 (Prod)   │      │   GQT Student Portal   │
                  │ SQLite3 (Dev/Test)     │      │   (Sandbox Fallback)   │
                  └────────────────────────┘      └────────────────────────┘
```

---

## 3. Directory Layout & Module Structure

```
c:\Users\User\Documents\GQT HRMS\
├── .env.example                       # Canonical environment configuration template
├── .gitignore                         # Comprehensive repository exclusion rules
├── gqt logo.png                       # Official GQT corporate asset
├── backend\
│   ├── manage.py                      # Django CLI runner
│   ├── pytest.ini                     # Test configuration targeting config.settings.test
│   ├── requirements.txt               # Pinned Python package dependencies
│   ├── openapi-schema.yaml            # OpenAPI 3.1 specification export
│   ├── config\
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── wsgi.py
│   │   ├── urls.py                    # Root /api/v1/ router & OpenAPI docs
│   │   └── settings\
│   │       ├── __init__.py
│   │       ├── base.py                # 5-layer base settings
│   │       ├── local.py               # Offline local dev settings
│   │       ├── production.py          # Strict fail-closed production settings
│   │       └── test.py                # Fast in-memory test settings
│   ├── apps\
│   │   ├── accounts\                  # Identity, authentication, user management & RBAC
│   │   ├── core\                      # Audit trail, middleware, health/readiness probes
│   │   └── portal\                    # GQT Student Portal client gateway boundary
│   └── tests\                         # 21 automated backend tests
├── frontend\
│   ├── package.json                   # Vite, React, TanStack Query, Tailwind, Vitest
│   ├── tsconfig.json                  # Project reference aggregator
│   ├── tsconfig.app.json              # Strict TypeScript options (strict: true, noImplicitAny: true)
│   ├── tsconfig.node.json             # Tooling TypeScript configuration
│   ├── vite.config.ts                 # Dev server proxy, path aliases, vitest setup
│   ├── tailwind.config.js             # Official GQT brand palette tokens
│   ├── postcss.config.js
│   ├── index.html
│   ├── public\images\gqt-logo.png     # Official high-resolution logo asset
│   └── src\
│       ├── api\apiClient.ts           # Axios instance with HttpOnly cookies & correlation IDs
│       ├── context\AuthContext.tsx    # Global session & RBAC state provider
│       ├── components\
│       │   ├── ui\                    # Button, Input, Card, StatusBadge, Empty/Error/Loading
│       │   └── layout\                # AppShell, Header, Sidebar, Footer, MobileDrawer, GQTLogo
│       ├── pages\                     # LoginPage, DashboardPage, AccessDeniedPage, NotFoundPage
│       └── test\                      # 9 automated Vitest component & integration tests
├── scripts\
│   └── verify_foundation.ps1          # End-to-end 7-gate quality runner
└── docs\
    ├── phase-0\                       # 13 requirements baseline documents
    ├── phase-1a-audit\                # 12 predecessor audit reports
    └── phase-1\                       # Phase 1 architecture & verification documents
```

---

## 4. Key Architectural Decisions

1. **UUIDv4 Primary Keys**: All domain models (`User`, `Role`, `UserRoleAssignment`, `AuditLog`) utilize cryptographically random UUID primary keys to eliminate enumeration attacks and ease distributed database replication.
2. **Stateless HttpOnly Cookie Auth**: SimpleJWT tokens are issued inside HttpOnly, SameSite=Lax cookies, completely eliminating the vulnerability of local storage token theft via XSS.
3. **Immutable Audit Logging**: The `AuditLog` model overrides `.delete()` to raise a `PermissionError`, ensuring an unbroken append-only audit trail.
4. **Fail-Closed Production Invariants**: `config.settings.production` raises `ImproperlyConfigured` if `DJANGO_SECRET_KEY` is empty/placeholder or `DJANGO_ALLOWED_HOSTS` includes wildcards.
5. **Disposable Test Storage**: `config.settings.test` assigns `MEDIA_ROOT` to a temporary directory via `tempfile.gettempdir()`, preventing workspace media pollution.
