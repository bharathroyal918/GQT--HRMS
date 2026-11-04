# 00 — Project Baseline
**GQT HRMS & Recruitment CRM Platform**
**Document Status:** Phase 0 — Verified Baseline (Not Approved for Implementation)
**Prepared:** 2026-11-03
**Prepared By:** Phase 0 Discovery Process

---

## 1. Workspace Inspection Results

| Item | Finding | Status |
|------|---------|--------|
| Workspace path | `C:\Users\User\Documents\GQT HRMS` | ✅ Confirmed |
| Operating system | Microsoft Windows NT 10.0.26300.0 (Windows 11) — AMD64 | ✅ Confirmed |
| Workspace contents | **Empty** — no application source files, no existing codebase | ✅ Confirmed |
| Existing Git repository | None detected in workspace | ✅ Confirmed (none) |
| GQT Product Requirements Blueprint | **Not found** as a standalone document in workspace | ⚠️ Missing |
| GQT Logo asset | `C:\Users\User\Documents\logo_gqt_backup.jpeg` (88,098 bytes, dated 2026-09-18) — located in parent Documents folder, not inside workspace | ✅ Located (not in workspace) |
| GQT Student Portal (reference system) | `C:\Users\User\Documents\GQT Student Portal` — full codebase present with backend, frontend, docs, migrations | ✅ Located |
| GQT CSR project | `C:\Users\User\Documents\GQT CSR` — separate project, not in scope | ✅ Noted |

### 1.1 Available Runtimes and Tools

| Runtime / Tool | Version | Notes |
|---------------|---------|-------|
| Python | 3.14.7 | Available. Target is Django 5.1.x; Python 3.12+ is required. 3.14 is a pre-release/unreleased series — **compatibility review required** (see Section 4). |
| pip | 26.2.1 | Available |
| Node.js | 24.21.0 | Available. Compatible with Vite + React |
| npm | 11.19.0 | Available |
| Git | 2.55.0.windows.5 | Available |
| Django (installed globally) | Not verified — no application virtualenv exists yet | ⚠️ Not installed in project context |
| PostgreSQL client / server | Not verified — PostgreSQL 16 is the target | ⚠️ Not confirmed |
| Redis | Not verified — required for background jobs | ⚠️ Not confirmed |

> [!WARNING]
> Python 3.14 is an **unreleased/development version** as of the documentation date. Django 5.1.x officially supports Python 3.10, 3.11, 3.12, and 3.13. This must be formally reviewed before any environment setup. The GQT Student Portal's own `requirements.txt` already uses `Django==5.1.15` in a 3.14-based environment, suggesting it may work, but official support confirmation is required.

### 1.2 GQT Student Portal — Reference Inventory

The following was discovered in the adjacent Student Portal project and is relevant to integration planning:

| Asset | Location | Relevance |
|-------|----------|-----------|
| Backend Django apps | `accounts`, `students`, `placements`, `notifications`, `analytics`, `courses`, `modules`, `assignments`, `scoring`, `leaderboard`, `certificates`, `common`, `reports`, `tasks`, `projects`, `ai_assistant`, `contact` | Integration surface |
| TPO Data Mapping specification | `TPO_DATA_MAPPING.md` | API contract reference for student data |
| TPO Authorization design | `TPO_AUTHORIZATION_DESIGN.md` | Role/permission reference |
| TPO Implementation plan | `TPO_IMPLEMENTATION_PLAN.md` | Integration design reference |
| User roles | ADMIN, STUDENT, TPO | Established role model |
| JWT authentication | `djangorestframework_simplejwt` with token blacklist | Auth mechanism reference |
| API versioning | `/api/v1/` prefix | Matches HRMS target |
| Placement Drive model | `PlacementDrive`, `PlacementApplication` — confirmed models with fields | Data model reference |
| Student Portal tech stack | Django 5.1.15, DRF 3.17, Celery, Redis, PostgreSQL/SQLite, Supabase, JWT, React (Next.js variant) | Established pattern |
| Placement eligibility tests | `test_placement_eligibility.py`, `test_placement_resume_security.py` | Test design reference |

### 1.3 Prior HRMS Codebase — Critical Discovery

A **predecessor HRMS project** was found at `C:\Users\User\Documents\HRS stop in middle`. This represents substantial prior work that was stopped mid-development. Key facts confirmed by inspection:

| Attribute | Confirmed Value |
|-----------|----------------|
| Location | `C:\Users\User\Documents\HRS stop in middle` |
| Status | Stopped in development — not in production |
| Backend framework | Django 5.1.x, DRF 3.15+, psycopg3, Argon2 |
| Frontend framework | React 19, TypeScript, Vite, TanStack Query, Axios |
| Backend apps (confirmed) | 13 apps: `accounts`, `crm`, `jobs`, `creatives`, `students`, `preparation`, `submissions`, `interviews`, `placements`, `feedback`, `analytics`, `ai`, `core` |
| Backend test count | 355 pytest tests across 22 test modules (per requirements audit) |
| Frontend test count | 147 vitest tests across 21 test files |
| API prefix | `/api/v1/` with drf-spectacular OpenAPI 3.1 documentation |
| Authentication | JWT in HttpOnly cookies (`gqt_access_token`, `gqt_refresh_token`), SameSite=Lax |
| Database configured | PostgreSQL 16 via Supabase (psycopg3), SQLite fallback for local dev |
| CI/CD | GitHub Actions with PostgreSQL 16 service container |
| Infrastructure | Docker + Nginx, docker-compose |
| Production target | `hrms.gqtech.in` (noted in `.env.example`) — not yet deployed |
| External communication | Pluggable SMTP (SendGrid/Hostinger/SES) + Meta WhatsApp Cloud API |
| AI features | JD parser, outreach assistant, resume analyzer, mock interview (deterministic heuristics — no external API cost) |
| Requirements audit doc | `docs/release/HRMS_REQUIREMENTS_AUDIT.md` — 354 lines, covers all 41 steps across 13 phases |
| Source of truth cited | `HRMS Work-Flow.pdf` (referenced in audit but not found on local filesystem) |
| Environment template | `.env.example` with all configuration keys documented (5923 bytes) |

> [!IMPORTANT]
> **Decision OD-001 is BLOCKING Phase 1:** GQT must formally decide whether to:
> 1. **Fresh start** — begin development from scratch in `C:\Users\User\Documents\GQT HRMS`, using the prior codebase only as architectural reference
> 2. **Migration/continuation** — copy the prior codebase into the new workspace, review its state, and continue development from that point
>
> This decision affects Phase 1 scope, timeline, and approach entirely. **Phase 1 cannot begin without this decision.** See `11-open-decisions-and-assumptions.md` OD-001.

---

## 2. Requirements Source Assessment

| Item | Status | Detail |
|------|--------|--------|
| Formal requirements blueprint | **NOT in target workspace** | No PDF/DOCX/MD blueprint was found inside `C:\Users\User\Documents\GQT HRMS` (target workspace). |
| Prior HRMS requirements audit | **FOUND** at `C:\Users\User\Documents\HRS stop in middle\docs\release\HRMS_REQUIREMENTS_AUDIT.md` | A 354-line formal audit document covering 13 phases, 41 workflow steps, 19 CRM modules — **this is treated as the primary requirements source for Phase 0** |
| Prior HRMS codebase | **FOUND** at `C:\Users\User\Documents\HRS stop in middle\` | A partially-built predecessor HRMS application — Django 5.1, 13 backend apps, 355 backend tests, 147 frontend tests, React 19 SPA |
| Source document referenced in audit | `HRMS Work-Flow.pdf` + `docs/requirements/workflow_traceability.md` | These are listed as the "Source of Truth" within the audit but **not found** directly in the filesystem — the PDF is the original source document, likely with GQT team |
| Requirement source used for this Phase 0 | Phase 0 brief prompt + `HRMS_REQUIREMENTS_AUDIT.md` | Combined. Traceability to the original `HRMS Work-Flow.pdf` is noted as **pending verification** |
| GQT CSR project | Found at `C:\Users\User\Documents\GQT CSR` | Separate project — not in scope |

> [!IMPORTANT]
> A **prior partially-built HRMS codebase exists** at `C:\Users\User\Documents\HRS stop in middle`. This is a predecessor project that was stopped mid-development. The new `GQT HRMS` workspace is a **clean-start project**. GQT must formally decide whether to:
> 1. Start fresh in the new workspace (using the prior code only as reference), or
> 2. Copy/migrate the prior codebase into the new workspace and continue from that point.
> **This is an unresolved business decision that blocks Phase 1 start.** It is documented in `11-open-decisions-and-assumptions.md` as decision OD-001.

> [!NOTE]
> The original `HRMS Work-Flow.pdf` document — cited as the authoritative source in the requirements audit — was not found on the local filesystem. The Phase 0 brief and the `HRMS_REQUIREMENTS_AUDIT.md` together provide a strong derived baseline, but complete source traceability cannot be claimed until the original PDF is located and confirmed.

---

## 3. Workspace State Summary

```
C:\Users\User\Documents\GQT HRMS\
└── docs\
    └── phase-0\          ← Created during Phase 0 (documentation only)
        ├── 00-project-baseline.md          (this file)
        ├── 01-product-scope.md
        ├── 02-requirements-traceability.md
        ├── 03-module-inventory.md
        ├── 04-workflow-and-business-rules.md
        ├── 05-roles-and-permissions.md
        ├── 06-student-portal-integration-discovery.md
        ├── 07-proposed-system-architecture.md
        ├── 08-data-classification-and-threat-review.md
        ├── 09-architecture-decision-records.md
        ├── 10-phase-roadmap-and-quality-gates.md
        ├── 11-open-decisions-and-assumptions.md
        └── 12-phase-0-acceptance-report.md
```

No application source code, migrations, environment files, configuration, or installed dependencies exist. The workspace is clean for a new project start.

---

## 4. Compatibility and Lifecycle Concerns

| Concern | Severity | Required Action |
|---------|----------|----------------|
| Python 3.14 is a pre-release series | HIGH | Confirm Django 5.1.x compatibility; consider targeting Python 3.12 LTS or 3.13 for production |
| No PostgreSQL confirmed locally | MEDIUM | PostgreSQL 16 installation and configuration required before Phase 1 backend setup |
| No Redis confirmed locally | MEDIUM | Required for Celery background jobs; installation required before Phase 1 |
| No project virtualenv exists | LOW | Standard — will be created during Phase 1 environment setup |
| No `.env` file in HRMS workspace | LOW | Standard — will be created from `.env.example` during Phase 1 |
| Node.js 24 is current LTS | LOW | Compatible with Vite and React — no concern |

---

## 5. Brand Assets

| Asset | Location | Status |
|-------|----------|--------|
| GQT Logo (JPEG) | `C:\Users\User\Documents\logo_gqt_backup.jpeg` and `C:\Users\User\Documents\logo.jpeg` | ✅ Located. 88,098 bytes each. |
| GQT Logo PNG | `C:\Users\User\Documents\GQT CSR\frontend\public\gqt-logo.png` (69,356 bytes) | ✅ Located in GQT CSR project |
| GQT Emblem PNG | `C:\Users\User\Documents\HRS stop in middle\frontend\public\gqt-emblem.png` (17,546 bytes) | ✅ Located in prior HRMS project |
| GQT Logo Tight PNG | `C:\Users\User\Documents\HRS stop in middle\frontend\public\gqt-logo-tight.png` (38,356 bytes) | ✅ Located in prior HRMS project |
| GQT SVG Logo (dark) | `C:\Users\User\Documents\GQT CSR\public\images\brand\gqt-logo-dark.svg` (1,389 bytes) | ✅ Located in GQT CSR project |
| GQT SVG Logo (light) | `C:\Users\User\Documents\GQT CSR\public\images\brand\gqt-logo-light.svg` (1,580 bytes) | ✅ Located in GQT CSR project |
| GQT SVG small icon | `C:\Users\User\Documents\GQT CSR\public\images\companies\gqt.svg` (703 bytes) | ✅ Located |
| GQT Seal PNG | `C:\Users\User\Documents\GQT CSR\public\images\signatures\gqt-seal.png` (20,902 bytes) | ✅ Located |
| Brand color tokens | Defined in Phase 0 brief | ✅ Documented in `07-proposed-system-architecture.md` |
| Favicon / icon set | Available via emblem PNG and SVGs above | ✅ Assets exist; ICO/favicons to be generated during Phase 1 |

> [!TIP]
> All brand assets should be consolidated into `frontend/public/` and `frontend/src/assets/brand/` at the start of Phase 1. The SVG variants (dark/light) from GQT CSR are recommended for scalable UI use. Authorization from GQT to copy these assets into the new project should be confirmed.

---

## 6. Cross-References

- Product scope → `01-product-scope.md`
- Requirements traceability → `02-requirements-traceability.md`
- Architecture decisions → `09-architecture-decision-records.md`
- Phase 0 acceptance gate → `12-phase-0-acceptance-report.md`
