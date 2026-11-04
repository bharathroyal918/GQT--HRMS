import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Palette,
  Plus,
  Search,
  Filter,
  ArrowRight,
  Clock,
  ShieldCheck,
} from "lucide-react";
import { creativesApi } from "../../api/creativesApi";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { CreativeStatusBadge } from "../../components/creatives/CreativeStatusBadge";

export const CreativeDirectoryPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  const {
    data: creativesData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["creativesDirectory", search, statusFilter, priorityFilter, typeFilter],
    queryFn: () =>
      creativesApi.getRequests({
        search: search || undefined,
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
        creative_type: typeFilter || undefined,
      }),
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
            <h1 className="text-2xl font-bold text-slate-900">Creative Requisition Directory</h1>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Browse and manage all recruitment flyers, social posters, and brand collateral workflows.
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <Link to="/creatives/triage-queue">
            <Button variant="outline" size="sm" className="flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-amber-500" />
              <span>Triage</span>
            </Button>
          </Link>

          <Link to="/creatives/review-queue">
            <Button variant="outline" size="sm" className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-indigo-600" />
              <span>Review Queue</span>
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

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <Input
            value={search}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearch(e.target.value)}
            placeholder="Search code, title, brief, company..."
            className="pl-9"
          />
        </div>

        <div className="flex items-center gap-2.5 flex-wrap w-full md:w-auto">
          <div className="flex items-center gap-1.5">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setStatusFilter(e.target.value)}
              className="text-xs rounded-lg border border-slate-300 p-2 bg-white text-slate-700 outline-none focus:border-indigo-500"
            >
              <option value="">All Statuses</option>
              <option value="DRAFT">Draft</option>
              <option value="SUBMITTED">Submitted / Triage</option>
              <option value="ASSIGNED">Assigned</option>
              <option value="IN_DESIGN">In Design</option>
              <option value="IN_REVIEW">In Review</option>
              <option value="CHANGES_REQUESTED">Changes Requested</option>
              <option value="APPROVED">Approved</option>
              <option value="READY_FOR_HANDOFF">Ready for Handoff</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>

          <select
            value={priorityFilter}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setPriorityFilter(e.target.value)}
            className="text-xs rounded-lg border border-slate-300 p-2 bg-white text-slate-700 outline-none focus:border-indigo-500"
          >
            <option value="">All Priorities</option>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
            <option value="URGENT">Urgent</option>
          </select>

          <select
            value={typeFilter}
            onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setTypeFilter(e.target.value)}
            className="text-xs rounded-lg border border-slate-300 p-2 bg-white text-slate-700 outline-none focus:border-indigo-500"
          >
            <option value="">All Asset Types</option>
            <option value="JOB_FLYER">Job Flyer</option>
            <option value="WHATSAPP_BANNER">WhatsApp Banner</option>
            <option value="INSTAGRAM_POST">Instagram Post</option>
            <option value="LINKEDIN_BANNER">LinkedIn Banner</option>
            <option value="EMAIL_HEADER">Email Header</option>
            <option value="CAMPUS_POSTER">Campus Poster</option>
            <option value="CUSTOM">Custom</option>
          </select>
        </div>
      </div>

      {/* Directory Table */}
      {isLoading ? (
        <LoadingState message="Loading creative directory..." />
      ) : isError ? (
        <ErrorState
          title="Error loading directory"
          message={(error as any)?.message || "Failed to load directory."}
          onRetry={refetch}
        />
      ) : !creativesData?.results || creativesData.results.length === 0 ? (
        <EmptyState
          title="No creative requisitions found"
          description="Adjust your search criteria or create a new requisition."
          actionText={canCreate ? "Create Requisition" : undefined}
          onAction={canCreate ? () => navigate("/creatives/new") : undefined}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="py-3 px-4">Code & Title</th>
                  <th className="py-3 px-4">Type & Format</th>
                  <th className="py-3 px-4">Target Company / Job</th>
                  <th className="py-3 px-4">Designer</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Active Deliverable</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                {creativesData.results.map((req) => (
                  <tr
                    key={req.id}
                    onClick={() => navigate(`/creatives/${req.id}`)}
                    className="hover:bg-slate-50/70 transition-colors cursor-pointer"
                  >
                    <td className="py-3 px-4">
                      <div className="font-mono text-[11px] text-indigo-600 font-semibold">
                        {req.request_code}
                      </div>
                      <div className="font-semibold text-slate-900 hover:text-indigo-600 transition-colors">
                        {req.title}
                      </div>
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
                      <div className="text-[11px] text-slate-500 truncate max-w-[180px]">
                        {req.job_title || "General Requisition"}
                      </div>
                    </td>

                    <td className="py-3 px-4 text-slate-700">
                      {req.assigned_designer_name}
                    </td>

                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[11px] font-bold ${
                          req.priority === "URGENT"
                            ? "bg-rose-100 text-rose-800"
                            : req.priority === "HIGH"
                            ? "bg-amber-100 text-amber-800"
                            : "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {req.priority}
                      </span>
                    </td>

                    <td className="py-3 px-4">
                      <CreativeStatusBadge status={req.status} />
                    </td>

                    <td className="py-3 px-4 font-mono text-slate-600">
                      {req.active_version_number ? (
                        <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-semibold text-[11px]">
                          v{req.active_version_number}
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>

                    <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => navigate(`/creatives/${req.id}`)}
                        className="text-xs py-1 px-2.5"
                      >
                        <span>View</span>
                        <ArrowRight className="w-3.5 h-3.5 ml-1" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

