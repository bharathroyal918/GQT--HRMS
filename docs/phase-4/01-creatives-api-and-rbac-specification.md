# GQT HRMS — Phase 4: Creative Studio API & RBAC Specification

## 1. Authentication & Base URL

- **Base URL**: `/api/v1/creatives/`
- **Authentication**: JWT Cookie Authentication (`gqt_access_token`) or `Authorization: Bearer <token>`.
- **Global Policy**: Deny by default. Unauthenticated access receives `401 Unauthorized`.

---

## 2. Role-Based Access Control (RBAC) Matrix

| Endpoint / Operation | ADMIN | PLACEMENT_HEAD | PLACEMENT_OFFICER | CREATIVE_REVIEWER | CREATIVE_DESIGNER | AUDITOR | STUDENT |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **List / Retrieve Creative Requests** | Full | Full | Own / All | Full | Assigned | Read-Only | Denied |
| **Create Creative Request (Draft)** | Yes | Yes | Yes | Yes | No | No | Denied |
| **Submit Creative Request** | Yes | Yes | Yes (Own) | Yes | No | No | Denied |
| **Triage & Assign Designer** | Yes | Yes | No | Yes | No | No | Denied |
| **Update Assignment / Priority** | Yes | Yes | No | Yes | No | No | Denied |
| **Upload Asset Version** | Yes | Yes | No | No | Assigned Only | No | Denied |
| **Submit Version for Review** | Yes | Yes | No | No | Uploader Only | No | Denied |
| **Evaluate Compliance Checks** | Yes | Yes | No | Yes | No | No | Denied |
| **Approve Asset Version (SoD)** | Yes* | Yes* | No | Yes* | No (Deny) | No | Denied |
| **Request Changes on Version** | Yes | Yes | No | Yes | No | No | Denied |
| **Mark Ready for Handoff** | Yes | Yes | No | Yes | No | No | Denied |
| **Download Asset File** | Yes | Yes | Yes | Yes | Assigned Only | Read-Only | Denied |
| **Studio Metrics & Dashboard** | Full | Full | Read-Only | Full | Assigned Only| Read-Only | Denied |

*\*Note on SoD: Even for ADMIN, PLACEMENT_HEAD, or CREATIVE_REVIEWER, if the reviewer is the same user who uploaded the asset version, the approval action is strictly rejected with `403 Forbidden` ("Segregation of duties violation: Designers cannot self-approve their own asset submissions").*

---

## 3. REST API Endpoint Specifications

### 3.1 Creative Requests

#### `GET /api/v1/creatives/requests/`
Lists creative requisitions with filtering, search, and pagination.
- Query parameters:
  - `status`: Filter by `CreativeStatus`
  - `priority`: Filter by `CreativePriority`
  - `creative_type`: Filter by `CreativeType`
  - `assigned_to`: Filter by designer UUID
  - `search`: Full text search on title, request_code, brief
  - `page`, `page_size`: Standard pagination

#### `POST /api/v1/creatives/requests/`
Creates a new creative requisition in `DRAFT` status.
- Payload:
  ```json
  {
    "title": "Infosys Campus Drive 2026 Announcement",
    "creative_type": "JOB_FLYER",
    "aspect_ratio": "4:5",
    "deliverable_format": "PNG",
    "brief": "Highlight 9.5 LPA CTC, Python/Java skills, Bangalore location. Include GQT official logo.",
    "priority": "HIGH",
    "target_completion_date": "2026-11-20",
    "job_requirement": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "company": "11111111-1111-1111-1111-111111111111"
  }
  ```

#### `GET /api/v1/creatives/requests/{id}/`
Returns full details of a creative requisition, including active version, assigned designer, historical versions, and workflow transition history.

#### `PATCH /api/v1/creatives/requests/{id}/`
Updates brief, title, or target date of a requisition in `DRAFT` or `SUBMITTED` status.

#### `POST /api/v1/creatives/requests/{id}/submit/`
Transitions status from `DRAFT` to `SUBMITTED` and enqueues for design triage.

#### `POST /api/v1/creatives/requests/{id}/assign/`
Assigns the requisition to a specific designer.
- Payload:
  ```json
  {
    "assigned_designer_id": "22222222-2222-2222-2222-222222222222",
    "priority": "HIGH",
    "notes": "Fast track for upcoming Monday announcement."
  }
  ```

#### `POST /api/v1/creatives/requests/{id}/cancel/`
Cancels the requisition with a mandatory reason.

---

### 3.2 Asset Versions & Deliverables

#### `POST /api/v1/creatives/requests/{id}/versions/`
Uploads a new design asset deliverable version (`multipart/form-data`).
- Form Data:
  - `file`: Binary file (`.png`, `.jpg`, `.jpeg`, `.webp`, `.pdf`, max 15MB)
  - `designer_notes`: Text explaining iterations or adjustments
- Automated processing:
  - Generates sequential version number (`v1`, `v2`, etc.)
  - Sanitizes filename
  - Validates magic bytes / MIME type
  - Computes SHA-256 hash
  - Instantiates 4 mandatory `DesignComplianceCheck` records in `PENDING` status
  - Transitions requisition status to `IN_REVIEW`

#### `GET /api/v1/creatives/requests/{id}/versions/`
Lists all uploaded versions for this requisition in descending order of version number.

#### `GET /api/v1/creatives/versions/{version_id}/`
Retrieves detailed metadata for a specific version, including compliance checklist evaluations and review decisions.

#### `POST /api/v1/creatives/versions/{version_id}/checks/{check_type}/`
Evaluates a specific compliance check on the version.
- Path parameters:
  - `check_type`: `FLYER_TEXT_ACCURACY`, `BRAND_ASSETS_COMPLIANCE`, `QR_CODE_INTEGRITY`, `CONTACT_DISCLOSURE`
- Payload:
  ```json
  {
    "status": "PASSED",
    "notes": "Verified CTC text against approved JobRequirement #JOB-2026-0042."
  }
  ```

#### `POST /api/v1/creatives/versions/{version_id}/approve/`
Approves the asset version.
- Enforces:
  1. All 4 compliance checks must be `PASSED`.
  2. SoD check: Request user != version uploader.
  3. Requisition status transitions to `APPROVED`.
- Payload:
  ```json
  {
    "review_feedback": "Typography, brand guidelines, and legal disclaimers all verified. Approved for campus release."
  }
  ```

#### `POST /api/v1/creatives/versions/{version_id}/request-changes/`
Requests revisions from the designer.
- Transitions requisition status to `CHANGES_REQUESTED`.
- Payload:
  ```json
  {
    "review_feedback": "Please replace the outdated company logo with the high-res SVG provided in attachments and fix the application deadline date."
  }
  ```

#### `POST /api/v1/creatives/requests/{id}/handoff/`
Marks the approved requisition as `READY_FOR_HANDOFF` for placement drive publishing.

---

### 3.3 Secure File Access & Streaming

#### `GET /api/v1/creatives/versions/{version_id}/download/`
Streams the validated file to authorized users with proper security headers:
- `Content-Type`: Checked MIME type
- `Content-Disposition`: `inline; filename="<sanitized_filename>"` or `attachment` (via `?download=true`)
- `X-Content-Type-Options: nosniff`
- Cache-Control: `private, no-cache, no-store, must-revalidate`

---

### 3.4 Operational Queues & Studio Metrics

#### `GET /api/v1/creatives/queues/triage/`
Returns submitted requisitions awaiting designer assignment.

#### `GET /api/v1/creatives/queues/designer/`
Returns active requisitions assigned to the currently logged-in designer.

#### `GET /api/v1/creatives/queues/review/`
Returns versions currently awaiting formal compliance evaluation and sign-off.

#### `GET /api/v1/creatives/queues/handoff/`
Returns approved requisitions ready for drive collateral distribution.

#### `GET /api/v1/creatives/metrics/`
Returns studio KPI aggregations:
- Total active requisitions
- Pending triage count
- In-design count
- Awaiting review count
- Average review turnaround
- Rejection/revision rate

