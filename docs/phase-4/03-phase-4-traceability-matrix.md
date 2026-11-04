# GQT HRMS — Phase 4: Requirements Traceability Matrix (RTM)

## 1. Traceability Mapping

| Blueprint Requirement | Description | Architectural Component | Backend Implementation | Frontend Implementation | Test Coverage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MOD-004-REQ-01** | Creative requisition lifecycle (Draft, Submit, Assign, In-Design, Review, Approved, Handoff) | Requisition Domain | `CreativeRequest` model, `create_creative_request`, `submit_creative_request` | `CreativeRequestFormPage`, `CreativeStatusBadge` | `test_creative_request_lifecycle` |
| **MOD-004-REQ-02** | Sequential human-readable request code (`CR-YYYY-NNNN`) | Sequence Service | `generate_request_code` atomic counter | Displayed in headers, breadcrumbs, and tables | `test_request_code_generation` |
| **MOD-004-REQ-03** | Triage and Designer Assignment by authorized roles | Assignment Service | `triage_and_assign_request`, `CanTriageOrAssignCreative` | `AssignDesignerModal`, `CreativeTriageQueuePage` | `test_triage_and_assignment` |
| **MOD-004-REQ-04** | Sequential deliverable asset versioning (`v1`, `v2`, etc.) | Versioning Domain | `CreativeAssetVersion` model, `upload_asset_version` | `AssetVersionUploadModal`, `VersionHistoryCard` | `test_version_upload_and_numbering` |
| **MOD-004-REQ-05** | Deep magic byte validation & upload security (PNG, JPEG, WEBP, PDF) | Security Service | `validate_and_sanitize_upload`, `inspect_magic_bytes` | File dropzone validation with instant feedback | `test_upload_magic_byte_security` |
| **MOD-004-REQ-06** | SHA-256 cryptographic checksum calculation and storage | Cryptographic Verification | `calculate_sha256_hash` | Displayed checksum badge on version details | `test_sha256_hash_integrity` |
| **MOD-004-REQ-07** | Mandatory 4-Point Design Compliance Checklist | Compliance Engine | `DesignComplianceCheck` model, `evaluate_compliance_check` | `DesignChecklistCard`, `CheckEvaluationModal` | `test_four_point_compliance_checks` |
| **MOD-004-REQ-08** | Segregation of Duties (SoD): Uploader cannot self-approve | Authorization Gate | `approve_asset_version` SoD check (`uploader != reviewer`) | Disabled approval CTA with clear SoD warning | `test_segregation_of_duties_enforcement` |
| **MOD-004-REQ-09** | Revisions & Change Request workflow | Feedback Service | `request_changes_on_version`, state rollback to `IN_DESIGN` | `RequestChangesModal`, feedback banner | `test_request_changes_workflow` |
| **MOD-004-REQ-09B**| Final approval gate (all 4 checks must pass before sign-off) | Sign-Off Gate | `approve_asset_version` check completeness guard | Disabled button with progress counter `x/4` | `test_approval_blocked_until_all_checks_pass` |
| **MOD-004-REQ-10** | Private media storage and authenticated streaming proxy | Storage Gateway | `serve_asset_download_view` with secure headers | Embedded private preview & authenticated download | `test_private_asset_streaming_security` |
| **MOD-004-REQ-11** | Full auditability of all design studio actions | Audit Logging | Centralized `AuditLog.objects.create` integration | Audit history log timeline component | `test_audit_logging_across_creative_actions` |
| **MOD-004-REQ-12** | Role-based operational queues (Triage, Designer, Review, Handoff) | Query Selectors | `apps.creatives.selectors` queue queries | Dedicated queue pages and counters | `test_creative_queues_and_metrics` |
| **MOD-004-REQ-13** | Studio analytics & throughput KPI aggregations | Analytics Selector | `get_creative_studio_metrics` | `CreativeStudioDashboardPage` metric cards | `test_creative_metrics_endpoint` |
| **MOD-004-REQ-14** | Placement Head final handoff to drive publishing | Handoff Service | `mark_ready_for_handoff` | "Handoff to Placement Drive" CTA | `test_ready_for_handoff_workflow` |
| **MOD-004-REQ-15** | Cross-domain linking to `JobRequirement` and `Company` | Foreign Key Integrity | `CreativeRequest.job_requirement`, `CreativeRequest.company` | Requisition link cards with one-click navigation | `test_job_and_company_relationships` |

