# Phase 4C: Concurrency Remediation & Final Security Verification Report

**Workspace:** `C:\Users\User\Documents\GQT HRMS`  
**Predecessor Workspace (Strictly Read-Only):** `C:\Users\User\Documents\HRS stop in middle`  
**Module:** Phase 4 — Recruitment Creative Studio (`apps.creatives`)  
**Status:** **CONDITIONAL PASS** (All code and local unit/service/API verification gates passed; PostgreSQL multi-threaded concurrency and DB-level role hardening pending live PostgreSQL environment)  
**Date:** November 2026  

---

## 1. Executive Summary

During Phase 4C, the concurrency and security architecture of the Recruitment Creative Studio (`apps.creatives`) was evaluated and hardened. Specifically:
1. **Requirements Audit (Task A):** Authoritative Phase 0 and Phase 4 requirements were inspected. The rule prohibiting uploader self-approval (`version.uploader_id == user.id`) is confirmed and active without exception (including for superusers). The requirements do not prohibit a distinct requisition creator from approving a deliverable uploaded by a designer, reflecting the business workflow where Placement Heads request and subsequently approve promotional collateral.
2. **Asset-Version Concurrency Remediation (Task B):** In `upload_asset_version`, version allocation was protected by acquiring a parent row lock (`CreativeRequest.objects.select_for_update()`), calculating the next sequential version while the lock is held, and isolating insert within an atomic savepoint that converts any `IntegrityError` to a controlled `ValidationError` without partial record leakage. The API view catches conflicts and returns a controlled HTTP 400 response.
3. **Genuine Concurrency Testing (Task C):** Prepared a multi-threaded concurrency test using thread barriers. Under SQLite in-memory, the test is explicitly skipped with documented reasons due to connection-private database isolation. It is prepared for execution on PostgreSQL.
4. **Security & RBAC Re-verification (Tasks D, E, F):** Verified that SoD uploader blocking, superuser self-approval blocking, 4-point compliance check isolation, audit-log ORM immutability, and defensive PDF delivery headers remain 100% enforced.
5. **Phase 5 Boundary:** Phase 5 (Placement Drives, Campus Publishing, Student Sync) remains strictly unauthorized and unstarted.

---

## 2. Requirements Inspection Reference (Task A)

### Inspected Sources
- `docs/phase-0/01-product-scope.md` (Sections SC-003, ROLE-002, ROLE-004, ROLE-006)
- `docs/phase-0/02-requirements-traceability.md` (REQ-PH02-S08, REQ-PH02-S09, REQ-CROSS-006)
- `docs/phase-0/04-workflow-and-business-rules.md` (Section 3.3, 5.2, 5.4)
- `docs/phase-0/05-roles-and-permissions.md` (ROLE-002, ROLE-006, ROLE-007, Section 7.1 line 489)
- `docs/phase-4/00-creatives-domain-architecture.md` (Section 3, 4, 5)
- `docs/phase-4/01-creatives-api-and-rbac-specification.md` (Section 2, 3.2)

### Findings on Key Questions
1. **Who can create a creative request:** `ADMIN`, `PLACEMENT_HEAD`, `PLACEMENT_OFFICER`, `CREATIVE_REVIEWER`.
2. **Who uploads a creative asset version:** `CREATIVE_DESIGNER` (assigned designer), with `ADMIN` / `PLACEMENT_HEAD` fallback.
3. **Who reviews compliance checks:** `CREATIVE_REVIEWER`, `PLACEMENT_HEAD`, `ADMIN` (4-point checklist: Flyer Text, Brand Logo, QR Code, Contact Disclosure).
4. **Who approves a deliverable:** `PLACEMENT_HEAD`, `ADMIN` (and `CREATIVE_REVIEWER` via Phase 4 spec delegation).
5. **Whether the requisition creator is prohibited from approving a deliverable they requested:** **No.** The confirmed business rules explicitly designate `PLACEMENT_HEAD` as both a requisition creator and the primary quality-gate approver for design deliverables created by designers.
6. **Whether the prohibition applies only to the uploader or to both uploader and requester:** Confirmed across Phase 0 (Section 7.1, line 489: *"Creative upload: CREATIVE_DESIGNER -> PLACEMENT_HEAD (approves): Yes — designer cannot self-approve"*) and Phase 4 specs that the prohibition applies **specifically to the uploader** (`version.uploader_id == user.id`).
7. **Administrator or superuser exceptions:** **None.** Superusers and administrators are strictly forbidden from approving deliverables they uploaded.

---

## 3. Concurrency Remediation Design (Task B)

### Locking & Allocation Strategy
1. **Parent Row Locking:** `CreativeRequest.objects.select_for_update().get(id=request_id)` acquires an exclusive row-level lock on the parent requisition. In PostgreSQL, parallel uploads for the same requisition block until the active transaction commits.
2. **Look-up Inside Lock:** `current_max` is evaluated while holding the row lock, ensuring sequential monotonic version incrementation (`v1 -> v2 -> v3`).
3. **Conflict Handling via Atomic Savepoint:**
   ```python
   try:
       with transaction.atomic():
           version = CreativeAssetVersion.objects.create(...)
   except IntegrityError as exc:
       raise ValidationError(
           {"detail": "A version creation conflict occurred for this requisition. Please retry."}
       ) from exc
   ```
4. **Zero Partial Commits:** If an `IntegrityError` occurs, the savepoint rolls back immediately, and the outer `@transaction.atomic` rolls back completely, ensuring no orphaned compliance checks or workflow records exist.
5. **Clean API Response:** `CreativeRequestViewSet.upload_version` catches `DjangoValidationError` and `IntegrityError`, converting both into a controlled HTTP 400 Bad Request response with JSON payload, avoiding unhandled HTTP 500 errors.

---

## 4. Test Verification Results

### Backend Test Matrix (Pytest: 78 passed, 1 skipped)
- `test_version_allocation_sequential_and_independent_across_requests`: PASSED (v1 initial, v2/v3 sequential increments, independent versioning across requests).
- `test_concurrency_unique_constraint_on_duplicate_version`: PASSED (asserts `IntegrityError` on duplicate insert).
- `test_failed_version_creation_atomically_rolls_back`: PASSED (asserts zero partial records upon failure).
- `test_version_creation_conflict_produces_controlled_error_not_500`: PASSED (asserts clean HTTP 400 on collision).
- `test_requester_distinct_from_uploader_approval_workflow`: PASSED (verifies Head can approve designer's upload).
- `test_superuser_uploader_self_approval_api_returns_400`: PASSED (verifies superuser uploader receives 400 Bad Request via API).
- `test_threaded_concurrency_version_allocation`: SKIPPED on SQLite (genuine PostgreSQL concurrency test prepared).

### Quality Gate Summary
1. **Django System Check:** 0 issues found.
2. **Schema Drift:** Clean (No changes detected).
3. **OpenAPI 3.1 Spec:** Generated cleanly.
4. **TypeScript Strict Compile:** Clean (0 compiler errors).
5. **Frontend Vitest Suite:** 21 passed across 7 test files.
6. **Frontend Production Build:** Successful (`dist/` generated).

---

## 5. PostgreSQL Verification Boundaries & Deployment Tasks

- **PostgreSQL Concurrency Verification:** **NOT VERIFIED / PENDING**. Local automated test suite executes on SQLite `:memory:`. The multi-threaded row-locking test is written and ready for execution on PostgreSQL via `POSTGRES_TEST_DATABASE_URL`.
- **PostgreSQL Audit Log Role Hardening:** **PENDING / NOT VERIFIED**. ORM guards (`AuditLogQuerySet`, `save()`) protect against Django mutations. Database-level role revocation (`REVOKE UPDATE, DELETE ON TABLE core_auditlog`) must be executed by DBA upon PostgreSQL production provisioning.
- **Phase 5 Boundary:** Confirmed that Phase 5 functionality has **not** been started.

