# GQT HRMS & Recruitment CRM Platform — Product Scope

> **Status:** Phase 0 Documentation — Not Approved for Implementation
> **Prepared:** 2026-11-03
> **Document ID:** DOC-SCOPE-001
> **Version:** 0.1.0 (Draft)
> **Cross-references:** [`02-requirements-traceability.md`](./02-requirements-traceability.md) · [`03-module-inventory.md`](./03-module-inventory.md)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [First-Release Scope](#2-first-release-scope)
3. [Explicit Exclusions](#3-explicit-exclusions)
4. [Integration Scope](#4-integration-scope)
5. [Target Users & Personas](#5-target-users--personas)
6. [Success Criteria](#6-success-criteria)
7. [Assumptions](#7-assumptions)
8. [Constraints](#8-constraints)
9. [Revision History](#9-revision-history)

---

## 1. Executive Summary

### 1.1 Platform Identity

**GQT HRMS** (Global Quantum Technologies Human Resource Management System) is a purpose-built, end-to-end **Recruitment & Placement CRM Platform** designed specifically for institutional placement cells, training institutions, and recruitment coordinators that facilitate campus-to-corporate hiring at scale.

Unlike general-purpose HRMS products, GQT HRMS is scoped exclusively to the **recruitment lifecycle** — from the first contact with a prospective corporate partner through to a student's confirmed joining date. The system does not manage employee payroll, attendance, leave, or post-joining HR workflows.

### 1.2 The Problem It Solves

Campus placement operations are operationally complex and data-intensive, yet most institutions manage them through disconnected spreadsheets, WhatsApp groups, and email threads. This leads to:

- **Lost opportunities:** HR contacts go cold due to untracked follow-ups
- **Compliance failures:** Job descriptions go unverified; salary claims and company legitimacy go unchecked
- **Quality inconsistency:** Student preparation activities lack structured tracking
- **Submission chaos:** Candidate packages are dispatched without version-controlled, traceable records
- **Outcome blindness:** Placement outcomes, offer acceptance, and joining confirmations are never systematically captured

GQT HRMS eliminates all of these failure modes by providing a single, role-governed, audited, notification-driven platform that every stakeholder — recruiter, coordinator, trainer, student, and corporate HR — interacts with at the right stage of the workflow.

### 1.3 Who Uses It

The platform serves **two primary institution types**:

1. **Training Institutions / Placement Cells** — internal staff who manage companies, prepare students, and orchestrate placements
2. **Corporate HR Partners** — external contacts whose job requirements trigger the entire downstream workflow

Ten distinct user roles operate within the system. See [Section 5](#5-target-users--personas) for full persona descriptions.

### 1.4 Platform Philosophy

- **Workflow-first:** Every action is a step in a defined business process with enforced state transitions
- **Auditability by default:** Every create, update, approve, and dispatch event is logged with actor identity and timestamp
- **Notification-driven:** No manual follow-up is required; the system proactively reminds actors of pending actions
- **Separation of concerns:** Corporate CRM data, student data, and placement outcomes are modular but fully traceable across the lifecycle

---

## 2. First-Release Scope

> The following 15 capability areas constitute the confirmed scope of the first production release. Each item is assigned a unique Scope ID (SC-xxx) for traceability. Status values are **confirmed** (from requirements audit), **proposed** (scoping decision), or **unresolved** (pending decision).

### 2.1 Scope Summary Table

| SC-ID | Capability Area | Phase Coverage | Steps | Status |
|-------|----------------|----------------|-------|--------|
| SC-001 | Corporate CRM & HR Directory | Phase 1 | 1–4 | confirmed |
| SC-002 | Job Requirements & Verification | Phase 2 | 5–9 | confirmed |
| SC-003 | Creative Studio & Asset Management | Phase 2 | 8–9 | confirmed |
| SC-004 | Student Registration & Eligibility Engine | Phase 3 | 10–14 | confirmed |
| SC-005 | Student Preparation Tracking | Phase 4 | 15–23 | confirmed |
| SC-006 | Candidate Submission & Profile Dispatch | Phase 5 | 24–28 | confirmed |
| SC-007 | Interview Management | Phase 6–7 | 29–35 | confirmed |
| SC-008 | Placement Outcome Management | Phase 8 | 36–41 | confirmed |
| SC-009 | Feedback Collection | Phase 9 | — | confirmed |
| SC-010 | CRM Database Reconciliation | Phase 10 | — | confirmed |
| SC-011 | Reports & Analytics | Phase 11 | — | confirmed |
| SC-012 | Automated Follow-Up Worker | Phase 12 | — | confirmed |
| SC-013 | Continuous Improvement Hub | Phase 13 | — | confirmed |
| SC-014 | Accounts, Auth & Role Management | Cross-cutting | all | confirmed |
| SC-015 | Core Notifications & Audit Infrastructure | Cross-cutting | all | confirmed |

### 2.2 Capability Descriptions

#### SC-001 · Corporate CRM & HR Directory
Manages the full lifecycle of corporate partnerships. Recruiters identify prospective companies, log initial contact attempts, record HR contact details (name, designation, email, phone), and track follow-up cadence. The system maintains a living directory of corporate HR partners with communication history, relationship status, and associated job requirement records.

*Maps to:* Phase 1 (Steps 1–4), MOD-002
*Key actors:* Recruiter, Admin

#### SC-002 · Job Requirements & Verification
Captures job descriptions submitted by corporate HR contacts and subjects each job to a **mandatory 5-point verification checklist** before internal approval. The five checks are: `ELIGIBILITY`, `SALARY_AUTHENTICITY`, `COMPANY_AUTHENTICITY`, `INTERVIEW_PROCESS`, and `REGISTRATION_DEADLINE`. No job proceeds to student-facing publication without passing all five checks and receiving internal approval.

*Maps to:* Phase 2 (Steps 5–9), MOD-003
*Key actors:* Recruiter, Admin/Approver

#### SC-003 · Creative Studio & Asset Management
Once a job is internally approved, the requirement is sent to the design team to produce a student-facing creative asset (poster, notification card). The system tracks creative briefs, design submissions, and approval states. Approved creatives are linked to job notifications sent to students.

*Maps to:* Phase 2 (Steps 8–9), MOD-004
*Key actors:* Design Staff, Admin/Approver

#### SC-004 · Student Registration & Eligibility Engine
Manages the student-facing side of job notifications: publishing the job, accepting student registrations, collecting profiles and resumes, running the eligibility verification engine against job criteria, and finalising the candidate cohort for a given drive.

*Maps to:* Phase 3 (Steps 10–14), MOD-005
*Key actors:* Student, Placement Coordinator, Admin

#### SC-005 · Student Preparation Tracking
Tracks the structured preparation journey of each registered candidate: resume review and improvement cycles, aptitude assessment, technical assessment, communication sessions, grooming sessions, one-on-one mock interviews (with rubric scoring), and final placement resume approval. Enforces gate logic — a student cannot proceed to submission without passing the final resume approval gate.

*Maps to:* Phase 4 (Steps 15–23), MOD-006
*Key actors:* Trainer, Placement Coordinator, Student

#### SC-006 · Candidate Submission & Profile Dispatch
Manages the packaging and dispatch of candidate profiles to corporate HR. This includes assembling the submission package, maintaining a master candidate roster spreadsheet, attaching certified resumes, dispatching profiles (with dispatch log), and recording company acknowledgement of receipt.

*Maps to:* Phase 5 (Steps 24–28), MOD-007
*Key actors:* Placement Coordinator, Admin

#### SC-007 · Interview Management
Tracks all interview activities from recruiter shortlist intake through to multi-round evaluation outcomes and corporate HR follow-up. Manages student drive invitations, automated reminders, attendance confirmation, interview occurrence recording, and per-round outcome capture.

*Maps to:* Phases 6–7 (Steps 29–35), MOD-008
*Key actors:* Recruiter, Student, Placement Coordinator

#### SC-008 · Placement Outcome Management
Captures final placement results: recording final outcomes per student, updating candidate status, sending contextual notifications to students based on outcome, managing offer letter uploads, tracking offer acceptance, and confirming joining status.

*Maps to:* Phase 8 (Steps 36–41), MOD-009
*Key actors:* Placement Coordinator, Student, Admin

#### SC-009 · Feedback Collection
Structured feedback collection from students post-placement and from corporate HR post-drive. Feedback data feeds into the Continuous Improvement Hub and analytics reporting.

*Maps to:* Phase 9, MOD-010
*Key actors:* Student, Corporate HR (external), Placement Coordinator

#### SC-010 · CRM Database Reconciliation
Periodic or triggered reconciliation of CRM records — de-duplication of company records, validation of HR contact details, archival of stale records, and correction of data inconsistencies accumulated across placement cycles.

*Maps to:* Phase 10, MOD-002 (CRM sub-function)
*Key actors:* Admin, Data Coordinator

#### SC-011 · Reports & Analytics
Provides aggregated reporting across all phases: placement rate by batch/company/programme, funnel drop-off analysis, preparation effectiveness metrics, interview-to-placement conversion, offer acceptance rates, and joining confirmation rates. Exportable to PDF and Excel.

*Maps to:* Phase 11, MOD-011
*Key actors:* Admin, Management, Placement Coordinator

#### SC-012 · Automated Follow-Up Worker
A background task worker (Celery-based) that monitors pending actions across the system and dispatches automated reminders, escalations, and status-change notifications without human intervention. Includes cadence control to avoid notification fatigue.

*Maps to:* Phase 12, MOD-013 (Core Infrastructure sub-function)
*Key actors:* System (automated)

#### SC-013 · Continuous Improvement Hub
Aggregates feedback, analytics, and process audit data to surface recurring bottlenecks, drop-off points, and improvement opportunities. Enables administrators to document process changes and track their impact over subsequent placement cycles.

*Maps to:* Phase 13, MOD-012
*Key actors:* Admin, Management

#### SC-014 · Accounts, Auth & Role Management
Manages user registration, authentication (JWT via HttpOnly cookies), role assignment, and permission enforcement. Supports all 10+ platform roles with per-role access control at API and UI levels.

*Maps to:* Cross-cutting all phases, MOD-001
*Key actors:* Admin, all users

#### SC-015 · Core Notifications & Audit Infrastructure
Platform-level infrastructure providing: in-app and email notification dispatch, audit trail logging (actor + action + timestamp + entity ID), notification preference management, and background task orchestration plumbing.

*Maps to:* Cross-cutting all phases, MOD-013
*Key actors:* System (automated), Admin

---

## 3. Explicit Exclusions

> The following capabilities are explicitly **out of scope** for the first release. Inclusion of any of these items requires a formal scope change request and re-approval.

| Exclusion ID | Excluded Capability | Rationale |
|---|---|---|
| EX-001 | Employee Payroll Processing | GQT HRMS manages recruitment pipelines, not post-joining compensation |
| EX-002 | Attendance & Leave Management | No employee lifecycle management; scope ends at joining confirmation |
| EX-003 | Conventional Employee Onboarding/Offboarding | Post-offer, post-joining HR processes are outside platform boundaries |
| EX-004 | Performance Appraisal & KPIs | Employee performance management is a separate domain |
| EX-005 | Asset Management (IT/Physical) | IT inventory and asset tracking are outside scope |
| EX-006 | General LMS / Learning Management | Course delivery and curriculum management are outside scope; only placement-context preparation tracking is included |
| EX-007 | Direct Interview Scheduling with Corporate Calendar Sync | Tentatively deferred; interview scheduling is recorded, not calendar-integrated in v1 |
| EX-008 | Video Interview / Proctoring | No in-platform video calling or remote proctoring in first release |
| EX-009 | Resume Parsing / AI Auto-Fill | AI-driven resume parsing is noted as a future enhancement; not in v1 scope |
| EX-010 | Public-Facing Company Job Board | GQT HRMS is an internal operations platform; no public job board |
| EX-011 | Background Verification (BGV) Integration | Third-party BGV API integration is deferred to a future phase |
| EX-012 | Offer Negotiation Workflows | Offer acceptance is tracked; negotiation workflows are outside scope |

---

## 4. Integration Scope

### 4.1 GQT Student Portal Integration

| Attribute | Detail |
|---|---|
| **Integration Name** | GQT Student Portal ↔ GQT HRMS |
| **Direction** | Bidirectional (student data flows both ways) |
| **Boundary** | Student Portal is a separate system; GQT HRMS does not own student authentication for the portal |
| **Status** | proposed |

**Data flowing FROM Student Portal TO GQT HRMS:**
- Student registration and basic profile (name, programme, batch, roll number)
- Contact information and PII required for placement eligibility assessment
- Academic records / CGPA data required for job eligibility checks

**Data flowing FROM GQT HRMS TO Student Portal:**
- Job notification publication (students see available drives via portal)
- Placement status updates (shortlisted, selected, not-selected, offer received, joined)
- Preparation activity schedules and results (where portal surfaces them to students)

**Integration Method:** REST API calls between systems. Authentication method between systems is unresolved — JWT service-to-service token or API key pending architecture decision.

**Boundary Principle:** GQT HRMS treats the Student Portal as an authoritative source for student identity data. Any duplication of student PII within HRMS is a read-copy for operational purposes only.

### 4.2 Other Integrations (Future / Unresolved)

| Integration | Status | Notes |
|---|---|---|
| Email service (SMTP / SendGrid / SES) | proposed | Required for notification delivery in first release |
| WhatsApp Business API | unresolved | Considered for student reminders; no decision yet |
| Google Drive / cloud storage | unresolved | Creative asset storage; local file storage as fallback |
| Calendar API (Google/Outlook) | deferred | Interview scheduling calendar sync deferred to v2 |
| BGV Provider API | deferred | Background verification excluded from v1 |

---

## 5. Target Users & Personas

> The platform supports **10 primary user roles**. All roles are internal to the institution except Corporate HR (external read-only access) and Students (limited self-service access).

| Role ID | Role Name | Role Type | Primary Responsibilities |
|---|---|---|---|
| ROLE-01 | **Platform Admin** | Internal Staff | Full system access; user management; configuration; master data maintenance; CRM reconciliation; reporting |
| ROLE-02 | **Placement Coordinator** | Internal Staff | Day-to-day recruitment coordination; job registration management; candidate submission packaging; interview and outcome tracking |
| ROLE-03 | **Recruiter** | Internal Staff | Company identification; HR outreach; follow-up; shortlist intake from corporate HR; drive facilitation |
| ROLE-04 | **Approver / Manager** | Internal Staff | Internal approval gate for job requirements; creative review and approval; final placement resume sign-off |
| ROLE-05 | **Trainer / Preparation Coach** | Internal Staff | Deliver and record preparation sessions (aptitude, technical, communication, grooming, mock interviews); score rubrics |
| ROLE-06 | **Design Staff** | Internal Staff | Receive creative briefs; produce and upload student-facing job notification assets; revise on feedback |
| ROLE-07 | **Data Coordinator** | Internal Staff | CRM database reconciliation; data quality management; de-duplication; archival |
| ROLE-08 | **Management / Reporting User** | Internal Staff | Read-only access to analytics dashboards and placement outcome reports; no operational data entry |
| ROLE-09 | **Student** | External (limited) | Self-register for drives; submit profile/resume; view preparation schedules; receive status notifications; view outcome |
| ROLE-10 | **Corporate HR Contact** | External (limited) | Submit job requirements; acknowledge candidate profile receipt; provide post-drive feedback; view shortlist status |

### 5.1 Persona Briefs

**ROLE-01 · Platform Admin**
The admin is the system owner within the institution. They configure the platform, manage user accounts and role assignments, oversee CRM data quality, run reconciliation cycles, and consume executive-level reports. They can perform any action on behalf of any other role in exceptional cases.

**ROLE-02 · Placement Coordinator**
The placement coordinator is the operational hub of the system. They receive verified job requirements from approvers, manage student eligibility cohorts, package candidate submissions, track interview scheduling and attendance, and record final placement outcomes. This is the most data-intensive role.

**ROLE-03 · Recruiter**
The recruiter focuses on the corporate relationship layer — identifying new companies, making cold contact, logging HR information, and conducting follow-up. They also handle drive logistics: issuing student invitations and following up with corporate HR post-drive.

**ROLE-04 · Approver / Manager**
The approver acts as a quality gate. They review job requirements against the 5-point checklist, approve creatives for publication, and sign off final placement resumes before submission dispatch. They do not conduct operational data entry.

**ROLE-05 · Trainer / Preparation Coach**
Trainers deliver structured preparation activities and record outcomes. They enter assessment scores, session attendance, rubric evaluations from mock interviews, and flag students requiring additional support. Their input feeds the eligibility status for submission.

**ROLE-06 · Design Staff**
Design staff receive creative briefs auto-generated from approved job requirements. They upload finished creative assets (posters, notification cards), receive revision notes from approvers, and re-submit until approved. Their deliverables are the student-facing communication assets.

**ROLE-07 · Data Coordinator**
Data coordinators maintain the integrity of the corporate CRM database. They run periodic reconciliation jobs, resolve duplicate company/HR records, validate contact details, and archive stale entries. This role may be combined with Admin in smaller institutions.

**ROLE-08 · Management / Reporting User**
A read-only consumer of analytics and reports. May include department heads, institution directors, or board-level stakeholders who need placement outcome data without operational system access.

**ROLE-09 · Student**
Students have a limited self-service interface. They register their interest in specific job drives, submit their profile and resume, view their preparation session schedule, and receive automated status notifications at each milestone. They do not have access to internal platform data.

**ROLE-10 · Corporate HR Contact**
Corporate HR contacts interact with the platform at two touchpoints: submitting job requirements (which may be via a simplified portal or mediated by the recruiter), and providing post-drive feedback. They may view the status of dispatched candidate profiles if a shared access portal is implemented.

---

## 6. Success Criteria

> These high-level business outcomes define whether the first release is considered successful. Each criterion maps to one or more measurable metrics that will be defined in the acceptance testing phase.

| SC-ID | Success Criterion | Measurement Approach | Related Scope |
|---|---|---|---|
| SUCC-01 | **Zero unverified jobs reach students** — Every student-facing job notification has passed the 5-point verification gate and received internal approval | Audit log query: 0 published jobs without all 5 checks = PASS | SC-002 |
| SUCC-02 | **Complete placement funnel visibility** — Every student's journey from registration to joining confirmation is traceable in one system | Data completeness report: % of placements with no null states in funnel | SC-001 through SC-008 |
| SUCC-03 | **Reduction in coordinator manual overhead** — Automated reminders eliminate manual follow-up communications by ≥ 70% compared to previous process | Recruiter/coordinator self-reported hours per placement cycle | SC-012 |
| SUCC-04 | **Offer letter and joining status captured for ≥ 95% of placed candidates** | Analytics report: placed candidates with offer letter upload + joining status ≠ NULL | SC-008 |
| SUCC-05 | **Preparation outcomes are recorded for all candidates in a cohort** — No student proceeds to submission without a preparation record | Database integrity check: 0 submission records without linked preparation record | SC-005, SC-006 |
| SUCC-06 | **Corporate HR contact data is complete and deduplicated** | CRM data quality report: < 5% duplicate rate, > 90% records with valid email | SC-001, SC-010 |
| SUCC-07 | **Placement reports are generated without manual data collation** | Report generation time < 30 seconds; no external spreadsheet required | SC-011 |
| SUCC-08 | **Role-based access is enforced with zero privilege escalation incidents** | Security audit: 0 incidents of a lower-privilege role accessing restricted data | SC-014 |

---

## 7. Assumptions

| Assumption ID | Assumption Statement | Impact if False |
|---|---|---|
| ASSUM-01 | The GQT Student Portal exists and exposes a stable API for student profile data | Student registration and eligibility flows must be redesigned; significant scope increase |
| ASSUM-02 | Each placement drive maps to one job requirement from one corporate HR contact | Data model simplification; if multi-HR drives exist, the submissions module must be extended |
| ASSUM-03 | The institution has a fixed set of preparation activity types (aptitude, technical, communication, grooming, mock interview) | If custom activity types are required per drive, the preparation module needs a configurable activity type registry |
| ASSUM-04 | A student can participate in multiple drives simultaneously | The eligibility and preparation models must support many-to-many student-to-drive relationships |
| ASSUM-05 | Corporate HR contacts will not have real-time login access to the platform in v1 | If corporate HR requires a self-service portal, a separate access tier and UI must be scoped |
| ASSUM-06 | Creative assets are image-based (JPEG/PNG/PDF) and do not require in-platform editing | If in-platform design tools are needed, the Creative Studio module scope expands significantly |
| ASSUM-07 | Email is the primary notification channel for all actors in v1 | If WhatsApp or SMS is mandated, notification infrastructure must be extended |
| ASSUM-08 | The institution runs on a single timezone | Multi-timezone support is not scoped; all timestamps are in the institution's local timezone |
| ASSUM-09 | The `HRMS Work-Flow.pdf` source document will be made available for review before implementation begins | If unavailable, requirements must be validated against the audit document and stakeholder interviews |
| ASSUM-10 | The prior codebase at `HRS stop in middle` is reference material only and will not be migrated | If code migration is required, a separate migration assessment must be conducted |

---

## 8. Constraints

### 8.1 Business Constraints

| Constraint ID | Constraint | Category |
|---|---|---|
| BCON-01 | The platform must support the **full 13-phase, 41-step workflow** as documented in the requirements audit — no phase may be omitted from the final release | Scope |
| BCON-02 | All **5 job verification checks** (`ELIGIBILITY`, `SALARY_AUTHENTICITY`, `COMPANY_AUTHENTICITY`, `INTERVIEW_PROCESS`, `REGISTRATION_DEADLINE`) are mandatory; the system must enforce them and prevent bypass | Compliance |
| BCON-03 | Student PII must be handled in compliance with applicable data protection regulations; no PII may be stored in log files or exposed in error responses | Privacy |
| BCON-04 | The `HRMS Work-Flow.pdf` source document has not been located on the filesystem; requirements are based on the audit document from the prior project — final validation against the source PDF is required before implementation | Documentation |
| BCON-05 | The new project workspace starts clean; no code from `HRS stop in middle` may be directly reused without explicit review and approval | Project |

### 8.2 Technical Constraints

| Constraint ID | Constraint | Category |
|---|---|---|
| TCON-01 | Backend: **Django 5.1.x** with Django REST Framework — no alternative backend framework | Framework |
| TCON-02 | Database: **PostgreSQL 16** — no alternative RDBMS | Database |
| TCON-03 | Frontend: **React (TypeScript)** with Vite, TanStack Query, React Hook Form + Zod, Axios | Framework |
| TCON-04 | Authentication: **JWT via HttpOnly cookies** — no localStorage token storage; no session-cookie auth | Security |
| TCON-05 | API design: **RESTful**, versioned under `/api/v1/` prefix | API |
| TCON-06 | Brand palette must be used consistently: Deep Navy `#001B4D`, Vivid Blue `#005BBB`, Charcoal `#1E293B`, Neutral Gray `#64748B`, Light Gray `#F1F5F9`, White `#FFFFFF` | Design |
| TCON-07 | All background/async tasks must use **Celery** with a Redis or RabbitMQ broker | Infrastructure |
| TCON-08 | File uploads (resumes, creatives, offer letters) must be validated for type and size before storage | Security |
| TCON-09 | All API endpoints must require authentication except explicitly defined public endpoints | Security |
| TCON-10 | The system must produce a complete audit trail for all create, update, approve, and delete actions | Compliance |

---

## 9. Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1.0 | 2026-11-03 | Phase 0 Documentation Agent | Initial draft created from requirements audit and Phase 0 brief |

---

*This document is part of the GQT HRMS Phase 0 Documentation Suite.*
*Next: [`02-requirements-traceability.md`](./02-requirements-traceability.md)*
