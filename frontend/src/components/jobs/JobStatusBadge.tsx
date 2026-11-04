import React from "react";
import { StatusBadge, BadgeVariant } from "../ui/StatusBadge";
import { JobStatus } from "../../types/jobs";

interface JobStatusBadgeProps {
  status: JobStatus;
}

export const JobStatusBadge: React.FC<JobStatusBadgeProps> = ({ status }) => {
  const map: Record<JobStatus, { variant: BadgeVariant; label: string }> = {
    DRAFT: { variant: "neutral", label: "Draft" },
    PENDING_VERIFICATION: { variant: "warning", label: "Pending Verification" },
    UNDER_VERIFICATION: { variant: "warning", label: "Under Verification" },
    CHANGES_REQUESTED: { variant: "warning", label: "Changes Requested" },
    PENDING_APPROVAL: { variant: "info", label: "Pending Approval" },
    APPROVED: { variant: "success", label: "Approved" },
    REJECTED: { variant: "danger", label: "Rejected" },
  };

  const cfg = map[status] || { variant: "neutral", label: status };
  return (
    <StatusBadge variant={cfg.variant} dot>
      {cfg.label}
    </StatusBadge>
  );
};

