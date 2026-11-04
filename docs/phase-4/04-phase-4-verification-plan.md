# GQT HRMS — Phase 4: Verification Plan & Quality Gates

## 1. Quality Gates Objective

To sign off Phase 4, the implementation must satisfy all 7 mandatory project quality gates without regressions in Phase 1, Phase 2, or Phase 3 capabilities.

---

## 2. Seven Standard Quality Gates

1. **Gate 1: Django System Diagnostics**: `python manage.py check --deploy` must report zero issues or warnings.
2. **Gate 2: Schema & Migration Consistency**: `python manage.py makemigrations --check --dry-run` must report zero model changes or unapplied migration drift.
3. **Gate 3: Backend Test Suite**: `pytest` must pass 100% of tests (all prior 51 tests plus comprehensive new Phase 4 test suite).
4. **Gate 4: OpenAPI 3.1 Specification**: `python manage.py spectacular --file docs/schema/openapi.yaml --validate` must generate valid schema without unresolvable errors.
5. **Gate 5: Frontend TypeScript Strict Check**: `tsc -b --noEmit` must report zero type errors in strict mode (`noImplicitAny`, `noUncheckedIndexedAccess`).
6. **Gate 6: Frontend Vitest Suite**: `npx vitest run` must pass all test suites including new Phase 4 creative studio test suite.
7. **Gate 7: Production Frontend Build**: `npm run build` (`vite build`) must generate production assets cleanly under `dist/`.

---

## 3. Phase 4 Specific Verification Scenarios

| Test ID | Scenario | Expected Outcome |
| :--- | :--- | :--- |
| **TC-CR-01** | Create Requisition with minimal valid fields | Status is `DRAFT`, request code `CR-YYYY-0001` is issued. |
| **TC-CR-02** | Submit Requisition | Status advances from `DRAFT` to `SUBMITTED`, enters Triage queue. |
| **TC-CR-03** | Triage and Designer Assignment | Reviewer assigns designer, status advances to `ASSIGNED`. |
| **TC-CR-04** | Upload Valid Asset Version (PNG/JPEG) | Version is saved, SHA-256 computed, 4 compliance checks generated in `PENDING`. Status advances to `IN_REVIEW`. |
| **TC-CR-05** | Upload Disguised Executable or Script | Rejected with `400 Bad Request` based on magic byte header inspection. |
| **TC-CR-06** | Upload Oversized File (>15MB) | Rejected with `400 Bad Request` file size limit exceeded. |
| **TC-CR-07** | Evaluate Compliance Checks | Reviewer marks checks as `PASSED` or `FLAGGED` with mandatory notes. |
| **TC-CR-08** | Attempt Approval with Incomplete Checks | Blocked with `400 Bad Request` ("All 4 compliance checks must be passed before approval"). |
| **TC-CR-09** | Segregation of Duties (SoD) Enforcement | If `uploader == reviewer`, approval attempt is rejected with `403 Forbidden`. |
| **TC-CR-10** | Independent Approval Sign-Off | Requisition and active version advance to `APPROVED`. |
| **TC-CR-11** | Request Changes Feedback Loop | Version status set to `CHANGES_REQUESTED`, requisition set to `CHANGES_REQUESTED`. |
| **TC-CR-12** | Subsequent Version Upload Numbering | Uploading after changes request creates `v2`, supersedes `v1`. |
| **TC-CR-13** | Handoff to Placement Operations | Authorized role marks approved asset as `READY_FOR_HANDOFF`. |
| **TC-CR-14** | Authenticated Private File Download | Valid JWT session streams binary file with `X-Content-Type-Options: nosniff`. Unauthenticated receives `401`. |
| **TC-CR-15** | Cross-Domain Audit Trail Logging | All actions generate correlated `AuditLog` rows. |
| **TC-CR-16** | Studio Throughput Metrics Aggregation | Accurately aggregates counts by status, priority, and queue. |

