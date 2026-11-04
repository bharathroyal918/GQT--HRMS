import React from "react";
import { StatusBadge, BadgeVariant } from "../ui/StatusBadge";
import { CreativeStatus } from "../../types/creatives";

interface CreativeStatusBadgeProps {
  status: CreativeStatus;
  className?: string;
}

export const CreativeStatusBadge: React.FC<CreativeStatusBadgeProps> = ({ status, className }) => {
  const map: Record<CreativeStatus, { variant: BadgeVariant; label: string }> = {
    DRAFT: { variant: "neutral", label: "Draft" },
    SUBMITTED: { variant: "warning", label: "Submitted for Triage" },
    ASSIGNED: { variant: "info", label: "Assigned" },
    IN_DESIGN: { variant: "info", label: "In Design" },
    IN_REVIEW: { variant: "warning", label: "Under Review" },
    CHANGES_REQUESTED: { variant: "danger", label: "Changes Requested" },
    APPROVED: { variant: "success", label: "Approved" },
    READY_FOR_HANDOFF: { variant: "success", label: "Ready for Handoff" },
    CANCELLED: { variant: "neutral", label: "Cancelled" },
  };

  const cfg = map[status] || { variant: "neutral", label: status };

  return (
    <StatusBadge variant={cfg.variant} dot className={className}>
      {cfg.label}
    </StatusBadge>
  );
};

