import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Palette,
  Plus,
  Clock,
  ShieldCheck,
  CheckCircle2,
  Layers,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { creativesApi } from "../../api/creativesApi";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/Button";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { CreativeStatusBadge } from "../../components/creatives/CreativeStatusBadge";

export const CreativeStudioDashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const {
    data: metrics,
    isLoading: isMetricsLoading,
    isError: isMetricsError,
    error: metricsError,
    refetch: refetchMetrics,
  } = useQuery({
    queryKey: ["creativeStudioMetrics"],
    queryFn: creativesApi.getStudioMetrics,
  });

  const {
    data: recentRequests,
    isLoading: isRequestsLoading,
  } = useQuery({
    queryKey: ["recentCreativeRequests"],
    queryFn: () => creativesApi.getRequests({ page_size: 5 }),
  });

  const canCreate = user?.roles.some((r) =>
    ["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "CREATIVE_REVIEWER"].includes(r)
  );

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-indigo-50 text-indigo-700 rounded-lg">
              <Palette className="w-5 h-5" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900">Creative Studio & Design Operations</h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Recruitment marketing collaterals, campus flyers, 4-point compliance evaluation, and SoD asset sign-off.
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <Link to="/creatives/directory">
            <Button variant="outline" size="sm">
              View All Requisitions
            </Button>
          </Link>

          {canCreate && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate("/creatives/new")}
              className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700"
            >
              <Plus className="w-4 h-4" />
              <span>New Requisition</span>
            </Button>
          )}
        </div>
      </div>

      {/* Studio KPI Cards */}
      {isMetricsLoading ? (
        <LoadingState message="Loading studio throughput metrics..." />
      ) : isMetricsError ? (
        <ErrorState
          title="Error loading studio metrics"
          message={(metricsError as any)?.message || "Failed to load metrics."}
          onRetry={refetchMetrics}
        />
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Requisitions</div>
            <div className="text-2xl font-bold text-slate-900 mt-1">{metrics?.total_requests ?? 0}</div>
            <div className="text-xs text-slate-400 mt-1">Across all hiring campaigns</div>
          </div>

          <Link to="/creatives/triage-queue" className="block hover:opacity-95 transition">
            <div className="bg-white p-4 rounded-xl border border-amber-200/80 bg-amber-50/20 shadow-sm">
              <div className="text-xs font-semibold text-amber-800 uppercase tracking-wider flex items-center justify-between">
                <span>Triage Queue</span>
                <Clock className="w-3.5 h-3.5 text-amber-600" />
              </div>
              <div className="text-2xl font-bold text-amber-700 mt-1">{metrics?.triage_queue_count ?? 0}</div>
              <div className="text-xs text-amber-600 mt-1">Awaiting designer assignment</div>
            </div>
          </Link>

          <Link to="/creatives/review-queue" className="block hover:opacity-95 transition">
            <div className="bg-white p-4 rounded-xl border border-indigo-200/80 bg-indigo-50/20 shadow-sm">
              <div className="text-xs font-semibold text-indigo-800 uppercase tracking-wider flex items-center justify-between">
                <span>Review Queue</span>
                <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
              </div>
              <div className="text-2xl font-bold text-indigo-700 mt-1">{metrics?.in_review_count ?? 0}</div>
              <div className="text-xs text-indigo-600 mt-1">Awaiting 4-point verification</div>
            </div>
          </Link>

          <div className="bg-white p-4 rounded-xl border border-emerald-200/80 bg-emerald-50/20 shadow-sm">
            <div className="text-xs font-semibold text-emerald-800 uppercase tracking-wider flex items-center justify-between">
              <span>Approved & Handoff</span>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            </div>
            <div className="text-2xl font-bold text-emerald-700 mt-1">
              {(metrics?.approved_count ?? 0) + (metrics?.ready_for_handoff_count ?? 0)}
            </div>
            <div className="text-xs text-emerald-600 mt-1">Authorized for campus drives</div>
          </div>
        </div>
      )}

      {/* Operational Queues Navigation Pills */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div
          onClick={() => navigate("/creatives/triage-queue")}
          className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm hover:border-indigo-400 cursor-pointer transition-all flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-amber-50 text-amber-600">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-900">Design Triage & Assignment</div>
              <div className="text-xs text-slate-500">Assign designers to submitted briefs</div>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-400" />
        </div>

        <div
          onClick={() => navigate("/creatives/designer-workspace")}
          className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm hover:border-indigo-400 cursor-pointer transition-all flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-blue-50 text-blue-600">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-900">Designer Workspace</div>
              <div className="text-xs text-slate-500">Upload versions and revise assets</div>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-400" />
        </div>

        <div
          onClick={() => navigate("/creatives/review-queue")}
          className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm hover:border-indigo-400 cursor-pointer transition-all flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-purple-50 text-purple-600">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-900">Compliance & Review Gate</div>
              <div className="text-xs text-slate-500">Evaluate 4-point checks & SoD sign-off</div>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-slate-400" />
        </div>
      </div>

      {/* Recent Creative Requisitions Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <h2 className="text-sm font-bold text-slate-900">Recent Marketing Requisitions</h2>
          </div>
          <Link to="/creatives/directory" className="text-xs text-indigo-600 hover:underline font-semibold">
            View full directory →
          </Link>
        </div>

        {isRequestsLoading ? (
          <div className="p-8">
            <LoadingState message="Loading requisitions..." />
          </div>
        ) : !recentRequests?.results || recentRequests.results.length === 0 ? (
          <EmptyState
            title="No creative requisitions yet"
            description="Create your first marketing brief or flyer requisition to get started."
            actionText={canCreate ? "Create Requisition" : undefined}
            onAction={canCreate ? () => navigate("/creatives/new") : undefined}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Code & Title</th>
                  <th className="py-3 px-4">Format / Type</th>
                  <th className="py-3 px-4">Company / Job</th>
                  <th className="py-3 px-4">Designer</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                {recentRequests.results.map((req) => (
                  <tr
                    key={req.id}
                    onClick={() => navigate(`/creatives/${req.id}`)}
                    className="hover:bg-slate-50/70 transition-colors cursor-pointer"
                  >
                    <td className="py-3 px-4">
                      <div className="font-mono text-[11px] text-indigo-600 font-semibold">
                        {req.request_code}
                      </div>
                      <div className="font-semibold text-slate-900">{req.title}</div>
                    </td>

                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-800">
                        {req.creative_type.replace(/_/g, " ")}
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {req.deliverable_format} • {req.aspect_ratio}
                      </div>
                    </td>

                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900">{req.company_name || "—"}</div>
                      <div className="text-[11px] text-slate-500">{req.job_title || "General Campaign"}</div>
                    </td>

                    <td className="py-3 px-4 text-slate-600">
                      {req.assigned_designer_name}
                    </td>

                    <td className="py-3 px-4">
                      <CreativeStatusBadge status={req.status} />
                    </td>

                    <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => navigate(`/creatives/${req.id}`)}
                        className="text-xs py-1 px-2.5"
                      >
                        <span>Details</span>
                        <ArrowRight className="w-3.5 h-3.5 ml-1" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

