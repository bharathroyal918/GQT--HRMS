import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Calendar,
  Clock,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Building2,
  UserCheck,
} from "lucide-react";
import { crmApi } from "../../api/crmApi";
import { FollowUp } from "../../types/crm";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/Button";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { Card, CardHeader, CardContent } from "../../components/ui/Card";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { CompleteFollowUpModal } from "../../components/crm/CompleteFollowUpModal";
import { CancelFollowUpModal } from "../../components/crm/CancelFollowUpModal";

export const FollowUpDashboardPage: React.FC = () => {
  const { hasAnyRole } = useAuth();
  const [activeFilter, setActiveFilter] = useState<"all" | "due_today" | "overdue">("due_today");
  const [completeTarget, setCompleteTarget] = useState<FollowUp | null>(null);
  const [cancelTarget, setCancelTarget] = useState<FollowUp | null>(null);

  const canEdit = hasAnyRole(["ADMIN", "PLACEMENT_HEAD", "CALLING_EXECUTIVE", "CRM_EXECUTIVE"]);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["follow-ups", activeFilter],
    queryFn: () =>
      crmApi.getFollowUps({
        filter_type: activeFilter === "all" ? undefined : activeFilter,
        status: "PENDING",
      }),
  });

  const getPriorityVariant = (p: string) => {
    switch (p) {
      case "URGENT":
        return "danger";
      case "HIGH":
        return "warning";
      case "MEDIUM":
        return "info";
      default:
        return "neutral";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-brand-dark flex items-center gap-2">
            <Clock className="h-6 w-6 text-brand-blue" />
            Outreach Follow-Up Action Queue
          </h1>
          <p className="mt-1 text-xs text-brand-muted">
            Manage scheduled corporate recruiter callbacks, requirements follow-ups, and meetings.
          </p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-6">
          <button
            type="button"
            onClick={() => setActiveFilter("due_today")}
            className={`py-3 px-1 border-b-2 font-medium text-xs inline-flex items-center gap-1.5 ${
              activeFilter === "due_today"
                ? "border-brand-navy text-brand-navy font-bold"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            <Calendar className="h-4 w-4" />
            Due Today
          </button>

          <button
            type="button"
            onClick={() => setActiveFilter("overdue")}
            className={`py-3 px-1 border-b-2 font-medium text-xs inline-flex items-center gap-1.5 ${
              activeFilter === "overdue"
                ? "border-red-600 text-red-600 font-bold"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            <AlertCircle className="h-4 w-4 text-red-500" />
            Overdue Tasks
          </button>

          <button
            type="button"
            onClick={() => setActiveFilter("all")}
            className={`py-3 px-1 border-b-2 font-medium text-xs inline-flex items-center gap-1.5 ${
              activeFilter === "all"
                ? "border-brand-navy text-brand-navy font-bold"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            <Clock className="h-4 w-4" />
            All Pending
          </button>
        </nav>
      </div>

      {/* Tasks Queue Card */}
      <Card>
        <CardHeader className="py-3">
          <h2 className="text-xs font-semibold text-brand-dark">
            Showing {data?.results?.length || 0} Actionable Follow-Up Tasks
          </h2>
        </CardHeader>

        <CardContent className="p-4">
          {isLoading && <LoadingState message="Loading follow-up tasks..." />}

          {isError && (
            <ErrorState
              title="Failed to load tasks"
              message="Could not retrieve the follow-up task queue from backend."
              onRetry={() => refetch()}
            />
          )}

          {!isLoading && !isError && data?.results?.length === 0 && (
            <EmptyState
              title="No pending tasks in this view"
              description="Great job! There are no follow-up callbacks or tasks pending in this queue."
            />
          )}

          {!isLoading && !isError && data && data.results.length > 0 && (
            <div className="space-y-3">
              {data.results.map((task: FollowUp) => (
                <div
                  key={task.id}
                  className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-lg border border-slate-200 p-4 hover:bg-slate-50 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-xs text-brand-dark">{task.title}</span>
                      <StatusBadge variant={getPriorityVariant(task.priority)} className="text-[10px]">
                        {task.priority}
                      </StatusBadge>
                      {task.is_overdue && (
                        <StatusBadge variant="danger" dot className="text-[10px]">
                          OVERDUE
                        </StatusBadge>
                      )}
                    </div>

                    <div className="flex items-center gap-3 text-xs text-slate-600">
                      <Link
                        to={`/companies/${task.company}`}
                        className="inline-flex items-center gap-1 font-semibold text-brand-navy hover:text-brand-blue"
                      >
                        <Building2 className="h-3.5 w-3.5 text-slate-400" />
                        {task.company_name}
                      </Link>

                      {task.contact_name && (
                        <span className="inline-flex items-center gap-1 text-slate-500">
                          <UserCheck className="h-3.5 w-3.5 text-slate-400" />
                          {task.contact_name}
                        </span>
                      )}
                    </div>

                    {task.description && (
                      <p className="text-xs text-slate-600 max-w-xl">{task.description}</p>
                    )}

                    <p className="text-[11px] text-slate-400 pt-1">
                      Due: {new Date(task.due_date).toLocaleString()} • Assigned: {task.assigned_to_name}
                    </p>
                  </div>

                  {canEdit && (
                    <div className="flex items-center gap-2 shrink-0">
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-emerald-700 hover:bg-emerald-50 border-emerald-200"
                        leftIcon={<CheckCircle2 className="h-3.5 w-3.5" />}
                        onClick={() => setCompleteTarget(task)}
                      >
                        Complete
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-600 hover:bg-red-50"
                        leftIcon={<XCircle className="h-3.5 w-3.5" />}
                        onClick={() => setCancelTarget(task)}
                      >
                        Cancel
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modals */}
      <CompleteFollowUpModal
        followUp={completeTarget}
        isOpen={!!completeTarget}
        onClose={() => setCompleteTarget(null)}
        onSuccess={() => refetch()}
      />

      <CancelFollowUpModal
        followUp={cancelTarget}
        isOpen={!!cancelTarget}
        onClose={() => setCancelTarget(null)}
        onSuccess={() => refetch()}
      />
    </div>
  );
};

