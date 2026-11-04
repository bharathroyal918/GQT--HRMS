# 11 — Open Decisions and Assumptions Register
**GQT HRMS & Recruitment CRM Platform**  
**Document Status:** Phase 0 Documentation — Business Decision Baseline (Pending GQT Sign-off)  
**Document ID:** GQT-DOC-P0-011  
**Prepared:** 2026-11-03  
**Author:** Software Architecture & Business Analysis Working Group  

---

## 1. Executive Summary

This register serves as the authoritative inventory of **Open Decisions (OD)**, **Confirmed Assumptions (AS)**, **Known Unknowns (KU)**, and **Project Risks (RK)** identified during Phase 0 discovery. 

In strict adherence to Phase 0 mandatory instructions, no technical or architectural assumption has been made regarding unresolved business policies. Unresolved items are formally recorded here with explicit decision owners and their blocking impact on future development phases.

---

## 2. Critical Unresolved Business & Technical Decisions

The following 20 decisions require formal review and determination by GQT Executive Leadership and Technical Stakeholders:

| Decision ID | Description & Context | Evaluated Options | Impact if Unresolved | Blocking For | Decision Owner |
|:---|:---|:---|:---|:---|:---:|
| **OD-001** | **Codebase Strategy: Fresh Start vs Predecessor Migration**<br/>A prior partially-built HRMS codebase exists at `C:\Users\User\Documents\HRS stop in middle` with 13 apps, 355 backend tests, and 147 frontend tests. | **Option A (Recommended):** Codebase Migration — ingest and audit the existing codebase into `GQT HRMS`, update dependencies, and continue engineering.<br/>**Option B:** Clean Start — build entirely from scratch in `GQT HRMS`, treating the prior codebase purely as reference. | Unclear repository baseline; potential waste of existing tested engineering or accidental carry-over of legacy defects. | **BLOCKS PHASE 1 START** | GQT Project Sponsor & Architecture Head |
| **OD-002** | **Target Python Runtime Standardization**<br/>Developer machine runs Python 3.14.7 (unreleased). Django 5.1 officially supports Python 3.10–3.13. | **Option A (Recommended):** Standardize containers and staging on Python 3.12 LTS.<br/>**Option B:** Standardize on Python 3.13.<br/>**Option C:** Attempt deployment on Python 3.14. | Risk of runtime segmentation faults in production third-party binary C-extensions. | **Phase 1 (Environment Setup)** | Lead Architect |
| **OD-003** | **Job Verification vs Approval Separation of Duties**<br/>Can the Placement Officer who drafts and checks a job requirement also issue the final approval? | **Option A (Recommended):** Strict Separation of Duties — only `PLACEMENT_HEAD` or `ADMIN` can approve; drafting officer cannot approve.<br/>**Option B:** Allow senior officers to self-approve. | Weakens the 5-point verification gate; risk of publishing inaccurate or unverified company JDs. | **Phase 4 (Job Management)** | GQT Placement Head |
| **OD-004** | **Student Portal Self-Service Scope in Release 1**<br/>Should students log in directly to HRMS, or should all student interaction occur via the existing Student Portal? | **Option A (Recommended):** Hybrid — Students use Portal for applying; HRMS provides minimal candidate self-service (profile, offer acceptance).<br/>**Option B:** Full Student Portal exclusive — HRMS has zero student logins. | Dictates whether candidate-facing routes and auth endpoints are built in HRMS. | **Phase 2 & Phase 6** | Product Manager |
| **OD-005** | **Post-Approval Job Description Mutation Policy**<br/>If a company updates CTC or criteria after approval, how is the change handled? | **Option A (Recommended):** Mandatory Re-Approval — any modification to criteria/salary resets status to `PENDING_VERIFICATION`.<br/>**Option B:** Minor amendments allowed with audit note. | Critical eligibility discrepancies between published flyer and actual recruiter criteria. | **Phase 4 (Job Management)** | GQT Placement Head |
| **OD-006** | **Creative Design Revision Escalation Ceiling**<br/>Maximum number of design revision cycles permitted between reviewer and designer before escalation. | **Option A (Recommended):** Maximum 3 revision cycles; 4th triggers notification to Placement Head.<br/>**Option B:** Unlimited revisions without escalation. | Risk of bottleneck in student announcement broadcasts for urgent recruitment drives. | **Phase 5 (Creative Studio)** | Creative Lead & Placement Head |
| **OD-007** | **Manual Eligibility Override Authorization Level**<br/>Who possesses authority to override a student who fails deterministic eligibility rules? | **Option A (Recommended):** `PLACEMENT_HEAD` only, with mandatory justification and audit log.<br/>**Option B:** Any assigned `PLACEMENT_OFFICER`. | Potential accusations of favoritism; lack of compliance audit trail. | **Phase 6 (Students)** | GQT Placement Head |
| **OD-008** | **Candidate Submission Authorization Model**<br/>Can eligible students submit their own profiles to a company, or does staff exclusively control dispatch? | **Option A (Recommended):** Staff-Exclusive Dispatch — students express interest; placement staff curates and dispatches master roster.<br/>**Option B:** Direct student application dispatch. | Uncurated, uncertified profiles sent directly to corporate recruiters, damaging institutional reputation. | **Phase 7 & Phase 8** | GQT Placement Head |
| **OD-009** | **Deferred Joining Policy & Maximum Duration**<br/>What is the allowable duration for candidate deferred joining, and who approves? | **Option A (Recommended):** Maximum 6 months deferral; requires documented corporate HR consent and Placement Head sign-off.<br/>**Option B:** Case-by-case ad-hoc approval. | Distorts institutional placement statistics and conversion reporting. | **Phase 10 (Placements)** | Placement Operations |
| **OD-010** | **Meta WhatsApp Cloud API Release 1 Requirement**<br/>Is live WhatsApp integration mandatory for Release 1, or is Transactional Email sufficient? | **Option A (Recommended):** Deploy with Email in Release 1; run WhatsApp in simulated mode until Meta Business Account is verified.<br/>**Option B:** Block release until Meta Cloud API is live. | Release delays caused by third-party Meta Business verification bureaucracy. | **Phase 1 & Phase 9** | GQT Executive Sponsor |
| **OD-011** | **Audit Trail Data Retention Schedule**<br/>How long must detailed authentication and workflow audit logs be maintained? | **Option A (Recommended):** 7 years retention for institutional compliance and accreditation audits.<br/>**Option B:** 3 years retention with automated table archiving. | Legal compliance exposure under educational accreditation reviews. | **Phase 2 (Core & Audit)** | Legal & Compliance Officer |
| **OD-012** | **Student Portal Authentication Mechanism**<br/>How will HRMS backend authenticate requests against the GQT Student Portal? | **Option A (Recommended):** Dedicated Service Account JWT with server-to-server secret token.<br/>**Option B:** Static API Bearer Token.<br/>**Option C:** Re-use TPO role credentials. | Security boundary breach if frontend or unauthorized users obtain portal credentials. | **Phase 12 (Portal Integration)** | Student Portal Lead Architect |
| **OD-013** | **Student Portal Credential Provisioning & Rotation**<br/>Who manages the issuance and rotation of integration service keys? | **Option A (Recommended):** Portal Administrator provisions credentials; automated 90-day rotation.<br/>**Option B:** Static long-lived shared secret. | Single point of failure if credentials expire during a live placement drive. | **Phase 12 (Portal Integration)** | Portal Administrator |
| **OD-014** | **Student Portal Rate Limits and Query Throttling**<br/>What are the throughput limits for batch syncing student profiles? | **Option A (Recommended):** Establish batch endpoints (`/api/v1/tpo/students/bulk/`) capped at 100 req/min.<br/>**Option B:** Unthrottled direct pagination queries. | Denial of Service risk against the live Student Portal during campus mega-drives. | **Phase 12 (Portal Integration)** | Student Portal Lead Architect |
| **OD-015** | **AI Capability Inclusion Scope in First Release**<br/>The prior codebase includes 4 deterministic AI assistants (JD parser, outreach writer, resume analyzer, mock interview). | **Option A (Recommended):** Retain deterministic, zero-external-cost heuristic assistants in Release 1.<br/>**Option B:** Remove AI entirely from Release 1.<br/>**Option C:** Connect to external paid LLM APIs (OpenAI/Anthropic). | Unbudgeted API cost overruns (if Option C) or loss of productivity accelerators (if Option B). | **Phase 3 & Phase 7** | GQT Product Owner |
| **OD-016** | **Production Cloud Hosting Target & Topology**<br/>Where will the production containers and database be provisioned? | **Option A (Recommended):** Hostinger VPS (Docker + Nginx) with Supabase Managed PostgreSQL 16.<br/>**Option B:** Full AWS deployment (ECS Fargate + RDS PostgreSQL).<br/>**Option C:** Self-hosted on-premise institutional server. | Dictates infrastructure budget, deployment scripts, and backup automation. | **Phase 14 & Phase 15** | Infrastructure Lead |
| **OD-017** | **Placement Trainer Visibility into Academic History**<br/>Should technical trainers have full read access to student grades, backlogs, and portal coding scores? | **Option A (Recommended):** Scoped Read Access — trainers view coding question progress and scores, but not financial/personal data.<br/>**Option B:** Full academic access. | Potential student data privacy leakage. | **Phase 6 & Phase 7** | Placement Head & Academic Lead |
| **OD-018** | **Interview Coordinator Role Segregation**<br/>Is the Interview Coordinator an independent staff role or an operational alias for Placement Officers? | **Option A (Recommended):** Configurable Role — Placement Officers hold Coordinator permissions by default.<br/>**Option B:** Strict segregated user role. | Staffing overhead if separate personnel are required for each role. | **Phase 2 & Phase 9** | Operations Manager |
| **OD-019** | **Salary & CTC Field-Level Visibility to Candidates**<br/>Should full CTC breakdowns (fixed vs variable vs bond) be visible to candidates during registration? | **Option A (Recommended):** Full Transparency — verified CTC details displayed to eligible students.<br/>**Option B:** Show CTC range only; full breakdown revealed upon offer issuance. | Student dissatisfaction or misinformation regarding service agreements and bonds. | **Phase 3 & Phase 5** | GQT Placement Head |
| **OD-020** | **Report and Data Export Scope Authorization**<br/>Can Placement Officers export candidate CSV data globally, or only for their assigned companies/drives? | **Option A (Recommended):** Scoped Export — Officers export only assigned drive data; `PLACEMENT_HEAD` and `AUDITOR` export globally.<br/>**Option B:** Unrestricted export for all staff. | Mass data exfiltration risk of institutional student databases. | **Phase 11 (Analytics)** | Compliance Officer |

---

## 3. Confirmed Assumptions Register

| Assumption ID | Confirmed Assumption Statement | Evidentiary Basis | Risk if Assumption Fails | Mitigation Strategy |
|:---|:---|:---|:---|:---|
| **AS-001** | The project is a single-organization platform built exclusively for Global Quest Technologies (no multi-tenancy). | Phase 0 Brief Section 1 | High rework if multi-tenancy is required later. | Schema utilizes clean organization context; avoids hardcoded single-tenant SQL. |
| **AS-002** | Conventional employee HR features (payroll, employee attendance, staff leaves) are strictly excluded from Release 1. | Phase 0 Brief Section 3 | Scope creep and missed delivery milestones. | Enforce strict boundaries; reject employee HR tickets in PR reviews. |
| **AS-003** | PostgreSQL 16 is available and supported for staging and production deployments. | Phase 0 Brief Section 4 & Supabase staging findings | Deployment failure if constrained to older SQL engines. | Containerize PostgreSQL 16 in Docker Compose for 100% environment parity. |
| **AS-004** | GQT Student Portal operates an active Django backend under `/api/v1/` accessible over the internal network. | Inspection of `C:\Users\User\Documents\GQT Student Portal` | Integration blocked if portal architecture differs. | Service adapter pattern with simulated fallback for offline development. |
| **AS-005** | Official GQT branding assets located in adjacent directories are authorized for use in the HRMS project. | Discovery of `logo_gqt_backup.jpeg` and SVG brand assets | Re-branding required if assets are superseded. | Design system uses centralized tokens; asset swap is a single-step operation. |
| **AS-006** | Browser clients accessing the console support modern ECMAScript standards and cookies (Chrome, Edge, Firefox, Safari). | Modern enterprise web standard | Login failures on legacy browsers. | Vite build targets modern browser baselines (`es2022`). |

---

## 4. Known Unknowns Register

| Unknown ID | Description of Unknown Factor | Current Impact | Resolution Pathway |
|:---|:---|:---|:---|
| **KU-001** | Exact network latency and throughput between HRMS host and GQT Student Portal production server. | Informs API timeout and retry backoff settings. | Execute network benchmark and ping test during Phase 12 integration spike. |
| **KU-002** | Official corporate email domain used for transactional SMTP dispatch (`noreply@gqtech.in` vs third-party domain). | Informs SPF, DKIM, and DMARC DNS record configuration. | Coordinate with GQT IT Domain Administrator prior to Phase 14. |
| **KU-003** | Production server CPU/RAM specifications on Hostinger VPS. | Informs Celery worker concurrency and PostgreSQL connection pool sizing (`CONN_MAX_AGE`). | Obtain VPS specification sheet from GQT Infrastructure team. |
| **KU-004** | Historical student placement data volume to be migrated from spreadsheets or legacy systems. | Informs data ingestion pipeline and database migration scripts. | Request sample historical placement spreadsheets from Placement Head. |

---

## 5. Project Risk Inventory & Mitigation Matrix

| Risk ID | Risk Description | Likelihood | Impact | Severity | Mitigation & Contingency Strategy | Risk Owner |
|:---|:---|:---:|:---:|:---:|:---|:---:|
| **RK-001** | **Live Credential Exposure**<br/>Accidental pasting of production database credentials or secret keys into chat/tickets. | Medium | Critical | **HIGH** | Enforce pre-commit git hooks (`detect-secrets`); immediately rotate any exposed credentials at the provider dashboard. | Security Lead |
| **RK-002** | **Student Data Privacy Leak (IDOR)**<br/>Candidate accessing unauthorized resumes or offer letters via URL manipulation. | Low | Critical | **HIGH** | Strict object-level DRF permissions (`IsStudentOwnerOrStaff`) on all media streaming endpoints. | Security Architect |
| **RK-003** | **Formula Injection in Exports**<br/>Corporate recruiters entering formula payloads in candidate feedback parsed into Excel. | Medium | High | **HIGH** | Prepend single quote (`'`) to all export cells beginning with `=`, `+`, `-`, `@`, `\t`, `\r`. | Backend Lead |
| **RK-004** | **Student Portal Downtime Impact**<br/>Student Portal outage rendering HRMS student eligibility verification inoperable. | Medium | High | **MEDIUM** | Circuit breaker pattern; cached read snapshots with explicit "Stale Data" visual warnings. | Integration Lead |
| **RK-005** | **Race Condition on Drive Dispatch**<br/>Two officers dispatching overlapping candidate rosters to the same recruiter simultaneously. | Low | High | **MEDIUM** | Database row locking (`select_for_update`) during dispatch package generation. | Database Architect |
| **RK-006** | **Third-Party Messaging SLA Breaches**<br/>Transactional emails or WhatsApp reminders delayed by vendor throttling. | Medium | Medium | **MEDIUM** | Celery task retry with exponential backoff and dead-letter queue alerting. | DevOps Lead |
| **RK-007** | **Python 3.14 Runtime Incompatibility**<br/>Unreleased Python version causing C-extension build failures in production Docker images. | High | High | **HIGH** | Pin production Docker base images strictly to `python:3.12-slim-bookworm` (ADR-017). | Lead Architect |
| **RK-008** | **Scope Creep into Employee HR**<br/>Stakeholders requesting employee leave/attendance during recruitment sprints. | High | Medium | **MEDIUM** | Strictly enforce Phase 0 exclusions (01-product-scope.md Section 3) via Change Control Board. | Product Owner |
| **RK-009** | **Uncoordinated Schema Changes**<br/>Student Portal team altering `StudentProfile` schema without notice to HRMS team. | Low | High | **MEDIUM** | Automated weekly integration contract tests against Student Portal staging API. | Integration Lead |
| **RK-010** | **Loss of Audit Trail Integrity**<br/>Accidental deletion of compliance audit logs during database maintenance. | Low | Critical | **HIGH** | Append-only database model overriding `.delete()`; read-only database user for reporting. | Database Architect |

---

## 6. Action Items for GQT Leadership

To unlock Phase 1 execution, GQT Leadership must provide written determination on the following items:
1. **Decision on OD-001:** Authorize whether to migrate the tested codebase at `HRS stop in middle` or commence a clean-slate rebuild.
2. **Approval of ADRs:** Sign off on Proposed Architecture Decision Records ADR-001 through ADR-018 (`09-architecture-decision-records.md`).
3. **Provisioning Credentials:** Confirm the secure channel for distributing rotated Supabase and staging environment secrets.

---

## 7. Cross-References

- Discovery baseline & environment report &rarr; `00-project-baseline.md`
- Product scope and explicit exclusions &rarr; `01-product-scope.md`
- Module inventory & specifications &rarr; `03-module-inventory.md`
- Proposed architecture decision records &rarr; `09-architecture-decision-records.md`
- Multi-phase roadmap & quality gates &rarr; `10-phase-roadmap-and-quality-gates.md`
- Phase 0 acceptance gate report &rarr; `12-phase-0-acceptance-report.md`

