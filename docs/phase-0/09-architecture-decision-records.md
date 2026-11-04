# 09 — Architecture Decision Records (ADRs)
**GQT HRMS & Recruitment CRM Platform**  
**Document Status:** Phase 0 Documentation — Proposed Architecture (Not Approved for Implementation)  
**Document ID:** GQT-DOC-P0-009  
**Prepared:** 2026-11-03  
**Author:** Software Architecture Working Group  

---

## 1. Architectural Decision Framework

Every technical decision governing the GQT HRMS & Recruitment CRM Platform is formally evaluated under the Architecture Decision Record (ADR) methodology. 

> [!IMPORTANT]
> All records contained herein are classified as **PROPOSED**. No architecture decision is considered binding or finalized until formally signed off by the GQT Technical Architecture Board and Business Leadership prior to the commencement of Phase 1.

---

## 2. ADR Summary Register

| ADR ID | Decision Title | Proposed Choice | Primary Alternative | GQT Approval Required |
|:---|:---|:---|:---|:---:|
| **ADR-001** | Repository Architecture | Unified Monorepo (`frontend/`, `backend/`, `docs/`) | Polyrepo (split repos) | Yes |
| **ADR-002** | JWT Token Storage & Transport | HttpOnly, SameSite=Lax Secure Cookies | `localStorage` / `sessionStorage` | Yes |
| **ADR-003** | Backend Architectural Pattern | Models &rarr; Selectors &rarr; Services &rarr; Serializers &rarr; Views | Fat Models / Fat Serializers | No (Technical) |
| **ADR-004** | Primary Relational Database Engine | PostgreSQL 16 (psycopg3 driver) | MySQL / SQLite / MongoDB | Yes |
| **ADR-005** | Cryptographic Password Hashing | Argon2id (`argon2-cffi`) | PBKDF2 / bcrypt | No (Technical) |
| **ADR-006** | Frontend Server State Management | TanStack Query v5 | Redux Toolkit / SWR | No (Technical) |
| **ADR-007** | Frontend Form & Schema Validation | React Hook Form + Zod | Formik + Yup | No (Technical) |
| **ADR-008** | Document & Resume Vault Storage | Private Media Storage with Stream Proxy | Direct Public S3 / CDN URLs | Yes |
| **ADR-009** | API Authorization Architecture | Deny-by-Default DRF Permission Base | AllowAny Default + Ad-hoc Checks | Yes |
| **ADR-010** | Asynchronous Processing & Schedules | Celery + Redis Task Queue | Django-Q2 / Cron Threads | Yes |
| **ADR-011** | External Multi-Channel Dispatch | Pluggable Provider Pattern (Simulated vs Live) | Hardcoded Vendor SDKs | Yes |
| **ADR-012** | API Specification & Contract Schema | OpenAPI 3.1 via `drf-spectacular` | Manual Postman / Swagger 2.0 | No (Technical) |
| **ADR-013** | Student Portal Integration Pattern | Scoped Service-to-Service REST Integration | Shared Database / Event Bus | Yes |
| **ADR-014** | Configuration & Secret Management | Environment Variables via `django-environ` | Hardcoded Settings / INI Files | Yes |
| **ADR-015** | Frontend Tooling & Build System | Vite 6 + TypeScript (Strict) | Create React App / Next.js SPA | No (Technical) |
| **ADR-016** | Security Audit Trail Immutability | Append-Only Database Records with Hook Defense | Mutable Logging Table | Yes |
| **ADR-017** | Target Python Runtime Lifecycle | Python 3.12 LTS / 3.13 Stable Target | Python 3.14 (Unreleased Series) | Yes |
| **ADR-018** | UI Design System & Component Styling | Tailwind CSS v3/v4 + Headless UI Primitives | Styled Components / Material UI | No (Technical) |

---

## 3. Comprehensive Decision Records

### ADR-001: Monorepo vs Polyrepo Architecture
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** The GQT HRMS platform requires strict synchronization between the Django REST Framework API contracts and TypeScript client types, unified deployment scripts (Docker/Nginx), and centralized documentation.
- **Decision:** Adopt a clean single repository structure containing `backend/`, `frontend/`, `docs/`, `infrastructure/`, and `scripts/`.
- **Alternatives Considered:**
  1. *Polyrepo:* Separate GitHub repositories for `gqt-hrms-backend` and `gqt-hrms-frontend`.
- **Trade-offs:** Monorepo simplifies atomic pull requests, end-to-end integration tests, and shared CI workflows, while requiring unified branch protection and git tagging conventions.
- **Security Implications:** Access to the repository grants visibility to both frontend and backend logic. Access control must be managed at the organization level.
- **GQT Approval Required:** Yes — Affects GitHub repository organization and developer access provisioning.

---

### ADR-002: JWT Token Storage and Session Transport
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** Storing JWT tokens in browser `localStorage` or `sessionStorage` exposes the platform to catastrophic token exfiltration via Cross-Site Scripting (XSS).
- **Decision:** Transmit and store JWT Access Tokens (15 min lifetime) and Refresh Tokens (7 day lifetime) strictly in browser cookies configured with `HttpOnly=True`, `SameSite=Lax`, and `Secure=True` (in production). Include SimpleJWT token blacklist enforcement on logout.
- **Alternatives Considered:**
  1. *Bearer Tokens in Web Storage (`localStorage`):* Highly vulnerable to script injection.
  2. *In-Memory Access Token + HttpOnly Refresh Cookie:* Acceptable, but complicates page reloads and iframe lifecycle.
- **Trade-offs:** Mitigates XSS token theft entirely. Requires CSRF protection on mutation requests (`X-CSRFToken` header validation).
- **Security Implications:** Highest security standard for single-organization enterprise web applications.
- **GQT Approval Required:** Yes — Sets the authentication security baseline across all staff and student sessions.

---

### ADR-003: Backend Architecture — Service Layer Pattern
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** Complex business workflows (5-point verification, Step 23 readiness certification, concurrency-safe dispatch) result in brittle, unmaintainable code if embedded directly in Django Model classes ("fat models") or DRF Serializer classes ("fat serializers").
- **Decision:** Mandate a strict 5-tier architecture across all Django apps:
  $$\text{Models} \longrightarrow \text{Selectors (Reads)} \longrightarrow \text{Services (Writes/Workflows)} \longrightarrow \text{Serializers} \longrightarrow \text{Views/Endpoints}$$
- **Alternatives Considered:**
  1. *Fat Models / Fat Serializers:* Standard Django defaults, leading to cross-app circular imports and testing friction.
  2. *Domain-Driven Design (Full Hexagonal):* Over-engineered for DRF-based systems.
- **Trade-offs:** Increases file count per app (`selectors.py`, `services.py`), but delivers testability, clear transaction boundaries (`@transaction.atomic`), and separation of concerns.
- **Security Implications:** Enforces security checks and audit logging at the service layer, preventing bypass via internal calls.
- **GQT Approval Required:** No — Internal engineering excellence standard.

---

### ADR-004: Primary Relational Database Engine
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** The recruitment platform requires ACID compliance, row-level concurrency locking (`select_for_update`), JSONB query performance for test results, and robust referential integrity.
- **Decision:** Standardize on **PostgreSQL 16** utilizing the modern non-blocking `psycopg` (v3) driver. For local offline developer workstations where PostgreSQL is uninstalled, a managed SQLite configuration is permitted only when `ENVIRONMENT=development` and explicitly toggled.
- **Alternatives Considered:**
  1. *MySQL 8:* Less flexible JSON handling and index capabilities.
  2. *MongoDB / NoSQL:* Unacceptable for relational transactional workflows involving financial CTC data and student grades.
- **Trade-offs:** Requires PostgreSQL runtime and configuration in staging/production.
- **Security Implications:** Enables PostgreSQL native row-level security (RLS), SSL connection enforcement (`sslmode=require`), and strict constraint checks.
- **GQT Approval Required:** Yes — Dictates cloud infrastructure requirements (e.g., Supabase PostgreSQL 16 or managed VPS PostgreSQL).

---

### ADR-005: Cryptographic Password Hashing Algorithm
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** Default Django password hashing utilizes PBKDF2 with SHA-256. Modern GPU cracking advances mandate memory-hard password derivation.
- **Decision:** Configure `argon2-cffi` (Argon2id) as the primary password hasher in `PASSWORD_HASHERS`.
- **Alternatives Considered:**
  1. *Default PBKDF2:* Susceptible to specialized ASIC/GPU cracking.
  2. *bcrypt:* Strong, but less memory-hard than Argon2id.
- **Trade-offs:** Slightly higher CPU/memory consumption during authentication calculations (negligible for expected staff/student concurrency).
- **Security Implications:** Industry-leading password storage security complying with OWASP guidelines.
- **GQT Approval Required:** No — Non-breaking configuration hardening.

---

### ADR-006: Frontend Server State Management
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** Recruitment dashboards require frequent background synchronization, optimistic UI updates for calling outreach, cache invalidation, and pagination handling.
- **Decision:** Adopt **TanStack Query (React Query) v5** for all server-state caching, fetching, and mutations.
- **Alternatives Considered:**
  1. *Redux Toolkit Query:* Verbose boilerplate; excessive for pure REST caching.
  2. *SWR:* Lacks advanced mutation hooks and dependent query primitives present in TanStack Query.
- **Trade-offs:** Separates server cache from local UI state (handled by simple React hooks/context).
- **Security Implications:** Query caches are scoped in-memory and invalidated automatically upon user logout.
- **GQT Approval Required:** No — Frontend architectural standard.

---

### ADR-007: Frontend Form & Schema Validation
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** Multi-step forms (Job creation, Candidate onboarding, Assessment rubrics) require client-side feedback and schema validation mirroring backend DRF serializers.
- **Decision:** Standardize on **React Hook Form** paired with **Zod** schema resolvers.
- **Alternatives Considered:**
  1. *Formik + Yup:* Heavier bundle size and re-render performance bottlenecks on large forms.
- **Trade-offs:** Requires defining TypeScript types derived directly from Zod schemas (`z.infer<typeof schema>`).
- **Security Implications:** Provides instant input sanitization and prevents malformed payloads from reaching backend ingress.
- **GQT Approval Required:** No — Frontend implementation convention.

---

### ADR-008: Document & Resume Vault Storage Architecture
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** Student resumes, candidate photos, and corporate offer letters contain sensitive PII. Exposing them via public cloud URLs or static media folders enables Insecure Direct Object References (IDOR).
- **Decision:** Store all files in a non-public filesystem location (e.g., `media/private/`). Files are served exclusively through an authenticated Django endpoint (`apps.students.views.serve_resume`) utilizing `FileResponse` and enforcing object-level ownership checks (`IsStudentOwnerOrStaff`). Enforce binary magic byte validation (`%PDF-`) and SHA-256 hash generation on upload.
- **Alternatives Considered:**
  1. *Public S3 Bucket with Obfuscated Names:* Obfuscation is not security; link sharing leaks PII.
  2. *Presigned S3 URLs:* Acceptable, but complex to revoke and monitor.
- **Trade-offs:** Streaming files through Django consumes application worker threads during large downloads.
- **Security Implications:** Eliminates unauthenticated access to student resumes and corporate offer letters.
- **GQT Approval Required:** Yes — Governs student data protection and privacy policy.

---

### ADR-009: API Authorization — Deny-by-Default Architecture
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** An accidental omission of a permission class on a newly created DRF endpoint could inadvertently expose candidate data or allow unauthorized job approval.
- **Decision:** Configure DRF default permissions globally as:
  ```python
  REST_FRAMEWORK = {
      "DEFAULT_PERMISSION_CLASSES": [
          "rest_framework.permissions.IsAuthenticated",
      ]
  }
  ```
  Every public route (Login, Health check) must explicitly declare `permission_classes = [AllowAny]`. All domain routes must apply role-specific permission guards (e.g., `IsPlacementHead`, `IsPlacementOfficerOrHead`).
- **Alternatives Considered:**
  1. *AllowAny Default:* Standard DRF behavior; high risk of developer oversight.
- **Trade-offs:** New endpoints fail closed with HTTP 401 until permissions are intentionally declared.
- **Security Implications:** Core architectural control preventing unauthorized API exposure.
- **GQT Approval Required:** Yes — Defines fundamental platform security policy.

---

### ADR-010: Background Asynchronous Processing & Task Scheduling
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** Automated interview reminders (24h, 2h, 30m), follow-up SLA escalations, candidate roster Excel exports, and email dispatches must not block synchronous HTTP request-response cycles.
- **Decision:** Deploy **Celery** with **Redis** as the task broker and result backend, scheduled via `django-celery-beat`.
- **Alternatives Considered:**
  1. *Django-Q2:* Python-native alternative, but less proven for high-concurrency enterprise workloads.
  2. *Cron Scripts calling `manage.py`:* High process startup overhead; lacks retry handling.
- **Trade-offs:** Introduces two additional container services (Celery Worker, Celery Beat, and Redis instance).
- **Security Implications:** Redis broker must be secured with a strong password and network isolation.
- **GQT Approval Required:** Yes — Defines background infrastructure requirements.

---

### ADR-011: Multi-Channel Communication Provider Architecture
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** The recruitment platform must dispatch emails (interview invites, offer letters) and WhatsApp notifications (reminders). Development environments must never dispatch live messages to real recipients.
- **Decision:** Implement a **Pluggable Provider Pattern**:
  - `BaseEmailAdapter` &rarr; `SimulatedEmailAdapter` (Dev/Test) / `DjangoSMTPEmailAdapter` (Production).
  - `BaseWhatsAppAdapter` &rarr; `SimulatedWhatsAppAdapter` (Dev/Test) / `MetaWhatsAppAdapter` (Production Cloud API).
  Provider backend is toggled via `EMAIL_PROVIDER_BACKEND` and `WHATSAPP_PROVIDER_BACKEND` environment variables.
- **Alternatives Considered:**
  1. *Direct Vendor SDK Calls:* Causes external API dependency errors in offline test environments.
- **Trade-offs:** Requires writing simulation mocks and logging telemetry for offline verification.
- **Security Implications:** Prevents accidental data leaks and message spam during development and QA.
- **GQT Approval Required:** Yes — Governs external communication costs and API vendor selection.

---

### ADR-012: API Specification & OpenAPI Documentation
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** Frontend developers, QA engineers, and automated contract tests require an authoritative, machine-readable API specification.
- **Decision:** Integrate **`drf-spectacular`** generating OpenAPI 3.1 schemas at `/api/v1/schema/` with interactive Swagger UI and Redoc documentation.
- **Alternatives Considered:**
  1. *Manual Postman Collections:* Out of sync with code changes.
  2. *drf-yasg:* Deprecated and incompatible with modern DRF / OpenAPI 3.x standards.
- **Trade-offs:** Requires decorating non-standard views with `@extend_schema`.
- **Security Implications:** Interactive documentation endpoints must be restricted to authenticated staff or disabled in production.
- **GQT Approval Required:** No — Engineering documentation tool.

---

### ADR-013: Student Portal Integration Architecture
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** The GQT HRMS must synchronize student eligibility and publish placement drives to the existing GQT Student Portal without compromising system boundaries.
- **Decision:** Treat the Student Portal as an external system of record accessed exclusively via **backend-to-backend REST API integration** using dedicated service credentials. The HRMS frontend client will never contact the Student Portal directly.
- **Alternatives Considered:**
  1. *Shared PostgreSQL Database:* Violates domain boundaries and introduces schema lock contention.
  2. *Direct Client-Side Integration:* Exposes portal API keys to browser environments.
- **Trade-offs:** Requires implementing retry queues, timeout handling, and stale data indicators.
- **Security Implications:** Zero portal credentials exposed to browser; all cross-system calls logged in audit trail.
- **GQT Approval Required:** Yes — Affects institutional data architecture and student portal operations.

---

### ADR-014: Environment Configuration & Secret Management
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** Database credentials, JWT signing keys, and third-party tokens must never be hardcoded or checked into version control.
- **Decision:** Enforce twelve-factor app configuration using `django-environ` reading from `.env`. Provide a comprehensive `.env.example` documenting all configuration keys. In `config/settings/production.py`, enforce fail-closed validations that abort startup if weak secrets or wildcard hosts are detected.
- **Alternatives Considered:**
  1. *Separate unversioned `local_settings.py`:* Error-prone and lacks container parity.
- **Trade-offs:** Requires configuring environment variables across local, CI, staging, and production environments.
- **Security Implications:** Prevents credential exposure in Git repositories.
- **GQT Approval Required:** Yes — Establishes secret management policy.

---

### ADR-015: Frontend Build Tooling & Runtime
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** Fast developer feedback, optimized production bundling, and strict TypeScript compilation are required for the recruitment console.
- **Decision:** Standardize on **Vite 6** paired with **React 19** and **TypeScript** with strict type checking enabled (`strict: true`, `noImplicitAny: true`).
- **Alternatives Considered:**
  1. *Create React App (CRA):* Deprecated and unmaintained.
  2. *Next.js:* Full-stack framework unnecessary since backend is hosted on Django DRF; adds SSR deployment complexity.
- **Trade-offs:** Production output is a static SPA served via high-performance Nginx web server.
- **Security Implications:** Standard static bundle reduces server-side execution attack surfaces.
- **GQT Approval Required:** No — Modern frontend toolchain selection.

---

### ADR-016: Security Audit Trail Immutability
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** Institutional compliance and accreditation mandate that audit trails of approvals, overrides, and credential changes cannot be altered or purged by staff.
- **Decision:** Implement `apps.core.models.GlobalAuditTrail` as an append-only table. Override model `.delete()` and `.update()` methods to raise runtime `PermissionDenied` exceptions. Audit records contain immutable timestamps, actor IDs, client IP, action codes, and JSON delta payloads.
- **Alternatives Considered:**
  1. *Application File Logging Only:* Difficult to query, aggregate, and correlate with database entities.
- **Trade-offs:** Database table grows monotonically; requires partition/archival planning for multi-year operations.
- **Security Implications:** High forensic value during security incident investigations.
- **GQT Approval Required:** Yes — Compliance and audit policy requirement.

---

### ADR-017: Target Python Runtime Lifecycle & Compatibility
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** The developer workstation environment has Python 3.14.7 installed. Python 3.14 is currently an unreleased/development series. Django 5.1.x officially supports Python 3.10, 3.11, 3.12, and 3.13.
- **Decision:** Target **Python 3.12 LTS** (or Python 3.13 Stable) for official staging, containerization, and production deployments. While the codebase will maintain syntactic compatibility with Python 3.14 for local development, production Docker containers must build on `python:3.12-slim-bookworm` to guarantee vendor support and ecosystem stability.
- **Alternatives Considered:**
  1. *Standardize Production on Python 3.14:* High risk of third-party C-extension crashes and unsupported Django behavior.
  2. *Downgrade to Python 3.10:* Older LTS, missing modern typing and performance optimizations.
- **Trade-offs:** Developers running Python 3.14 locally must be mindful of libraries requiring compiled binary wheels.
- **Security Implications:** Unreleased runtimes do not receive enterprise security backports.
- **GQT Approval Required:** Yes — Governs hosting and runtime provisioning.

---

### ADR-018: Design System & Styling Architecture
- **Status:** PROPOSED — Requires GQT approval before implementation
- **Date:** 2026-11-03
- **Context:** The GQT HRMS must project a polished, authoritative enterprise operations aesthetic adhering strictly to the official GQT brand palette (Deep Navy `#001B4D`, Vivid Blue `#005BBB`, Charcoal `#1E293B`).
- **Decision:** Standardize on **Tailwind CSS** with design tokens configured in `tailwind.config.js`. Implement reusable UI primitives (`Button`, `Card`, `StatusBadge`, `Input`, `EmptyState`, `WorkflowRoadmap`). Prohibit relying solely on color to communicate state (must combine icon, label, and accessible contrast).
- **Alternatives Considered:**
  1. *Component Libraries (MUI / Ant Design):* Bulky bundle size; difficult to customize to GQT's brand palette.
  2. *Plain CSS / CSS Modules:* High maintenance overhead; lack of unified design token enforcement.
- **Trade-offs:** Requires team familiarity with Tailwind utility classes.
- **Security Implications:** Zero runtime CSS injection vulnerabilities.
- **GQT Approval Required:** No — Design implementation standard.

---

## 4. Cross-References

- Environmental baseline & Python runtime analysis &rarr; `00-project-baseline.md`
- System architecture & deployment topology &rarr; `07-proposed-system-architecture.md`
- Threat modeling & security controls &rarr; `08-data-classification-and-threat-review.md`
- Open business decisions & ADR sign-off queue &rarr; `11-open-decisions-and-assumptions.md`
- Phase 0 acceptance gate &rarr; `12-phase-0-acceptance-report.md`

