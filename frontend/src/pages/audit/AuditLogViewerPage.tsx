import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ShieldAlert,
  Search,
  Download,
  RefreshCw,
  Eye,
  CheckCircle2,
  AlertTriangle,
  Clock,
  User as UserIcon,
  X,
} from "lucide-react";
import { auditApi } from "../../api/auditApi";
import { AuditLogItem, AuditFilterParams } from "../../types/audit";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { EmptyState } from "../../components/ui/EmptyState";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";

export const AuditLogViewerPage: React.FC = () => {
  const [filters, setFilters] = useState<AuditFilterParams>({
    page: 1,
    page_size: 20,
    search: "",
    action: "",
    resource_type: "",
  });

  const [selectedLog, setSelectedLog] = useState<AuditLogItem | null>(null);

  const {
    data: summaryData,
    isLoading: isSummaryLoading,
  } = useQuery({
    queryKey: ["auditSummary"],
    queryFn: () => auditApi.getAuditSummary(),
  });

  const {
    data: logsData,
    isLoading: isLogsLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["auditLogs", filters],
    queryFn: () => auditApi.getAuditLogs(filters),
  });

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters((prev) => ({ ...prev, search: e.target.value, page: 1 }));
  };

  const handleExportCsv = () => {
    const url = auditApi.exportAuditCsvUrl(filters);
    window.open(url, "_blank");
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-7 w-7 text-brand-navy" />
            <h1 className="text-2xl font-bold text-brand-dark">Audit Logs & Compliance Oversight</h1>
          </div>
          <p className="text-sm text-brand-muted mt-1">
            Tamper-evident, immutable audit trail tracking all recruitment operations, verifications, and approvals.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={() => refetch()} className="flex items-center gap-1.5">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
          <Button variant="primary" size="sm" onClick={handleExportCsv} className="flex items-center gap-1.5">
            <Download className="h-4 w-4" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 border-l-4 border-l-brand-blue bg-white">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Audit Events</span>
            <Clock className="h-4 w-4 text-brand-blue" />
          </div>
          <p className="text-2xl font-bold text-brand-dark mt-2">
            {isSummaryLoading ? "..." : summaryData?.total_count.toLocaleString() ?? 0}
          </p>
          <p className="text-xs text-brand-muted mt-1">Platform lifetime events</p>
        </Card>

        <Card className="p-4 border-l-4 border-l-brand-teal bg-white">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Events Today</span>
            <CheckCircle2 className="h-4 w-4 text-brand-teal" />
          </div>
          <p className="text-2xl font-bold text-brand-dark mt-2">
            {isSummaryLoading ? "..." : summaryData?.today_count.toLocaleString() ?? 0}
          </p>
          <p className="text-xs text-brand-muted mt-1">Since 00:00 UTC</p>
        </Card>

        <Card className="p-4 border-l-4 border-l-indigo-600 bg-white">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Actors</span>
            <UserIcon className="h-4 w-4 text-indigo-600" />
          </div>
          <p className="text-2xl font-bold text-brand-dark mt-2">
            {isSummaryLoading ? "..." : summaryData?.unique_actors ?? 0}
          </p>
          <p className="text-xs text-brand-muted mt-1">Distinct users recorded</p>
        </Card>

        <Card className="p-4 border-l-4 border-l-amber-500 bg-white">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Critical Actions</span>
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          </div>
          <p className="text-2xl font-bold text-brand-dark mt-2">
            {isSummaryLoading
              ? "..."
              : (summaryData?.recent_critical_actions ?? []).reduce((acc, curr) => acc + curr.count, 0)}
          </p>
          <p className="text-xs text-brand-muted mt-1">Approvals & state changes</p>
        </Card>
      </div>

      {/* Filter and Search Bar */}
      <Card className="p-4 bg-white">
        <div className="flex flex-col md:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by action, resource type, user email, or correlation ID..."
              value={filters.search}
              onChange={handleSearchChange}
              className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-blue"
            />
          </div>
          <div className="flex items-center gap-2 w-full md:w-auto">
            <select
              value={filters.action}
              onChange={(e) => setFilters((prev) => ({ ...prev, action: e.target.value, page: 1 }))}
              className="px-3 py-2 border border-slate-300 rounded-md text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-brand-blue"
            >
              <option value="">All Actions</option>
              <option value="JOB_REQUIREMENT_APPROVED">Job Approved</option>
              <option value="CREATIVE_APPROVED">Creative Approved</option>
              <option value="COMPANY_CREATED">Company Created</option>
              <option value="OUTREACH_LOGGED">Outreach Logged</option>
              <option value="SECURITY_ALERT">Security Alert</option>
            </select>
            <select
              value={filters.resource_type}
              onChange={(e) => setFilters((prev) => ({ ...prev, resource_type: e.target.value, page: 1 }))}
              className="px-3 py-2 border border-slate-300 rounded-md text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-brand-blue"
            >
              <option value="">All Resources</option>
              <option value="JobRequirement">Job Requirement</option>
              <option value="CreativeRequest">Creative Request</option>
              <option value="Company">Company</option>
              <option value="User">User</option>
              <option value="OutreachActivity">Outreach Activity</option>
            </select>
            {(filters.search || filters.action || filters.resource_type) && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setFilters({ page: 1, page_size: 20, search: "", action: "", resource_type: "" })}
                className="text-xs text-brand-muted hover:text-brand-dark"
              >
                Clear
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* Audit Log Table */}
      <Card className="overflow-hidden bg-white shadow-sm border border-slate-200">
        {isLogsLoading ? (
          <div className="p-8">
            <LoadingState message="Loading audit trail records..." />
          </div>
        ) : isError ? (
          <div className="p-8">
            <ErrorState message="Failed to load audit trail. Please verify your permissions." />
          </div>
        ) : !logsData?.results || logsData.results.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No Audit Logs Found"
              description="No audit records match the selected search or filter criteria."
            />
          </div>
        ) : (
          <div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                    <th className="py-3 px-4">Timestamp (UTC)</th>
                    <th className="py-3 px-4">Action</th>
                    <th className="py-3 px-4">Resource</th>
                    <th className="py-3 px-4">Actor</th>
                    <th className="py-3 px-4">IP / Host</th>
                    <th className="py-3 px-4">Correlation ID</th>
                    <th className="py-3 px-4 text-right">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {logsData.results.map((log) => {
                    const isCritical =
                      log.action.includes("APPROVE") ||
                      log.action.includes("REJECT") ||
                      log.action.includes("SECURITY") ||
                      log.action.includes("DELETE");

                    return (
                      <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                        <td className="py-3 px-4 font-mono text-slate-500 whitespace-nowrap">
                          {new Date(log.created_at).toISOString().replace("T", " ").substring(0, 19)}
                        </td>
                        <td className="py-3 px-4 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold ${
                              isCritical
                                ? "bg-amber-100 text-amber-800"
                                : "bg-slate-100 text-slate-700"
                            }`}
                          >
                            {log.action}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <div className="font-medium text-slate-800">{log.resource_type}</div>
                          <div className="font-mono text-[10px] text-slate-400 truncate max-w-[140px]" title={log.resource_id}>
                            {log.resource_id}
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          {log.user ? (
                            <div>
                              <div className="font-medium text-slate-800">{log.user.full_name}</div>
                              <div className="text-[11px] text-slate-500">{log.user.email}</div>
                            </div>
                          ) : (
                            <span className="text-slate-400 italic">SYSTEM</span>
                          )}
                        </td>
                        <td className="py-3 px-4 font-mono text-slate-500 whitespace-nowrap">
                          {log.ip_address || "—"}
                        </td>
                        <td className="py-3 px-4 font-mono text-[11px] text-slate-500 truncate max-w-[120px]" title={log.correlation_id}>
                          {log.correlation_id || "—"}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setSelectedLog(log)}
                            className="text-xs text-brand-blue hover:text-brand-dark p-1"
                            title="Inspect log details"
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center justify-between p-4 border-t border-slate-200 text-xs text-slate-500">
              <div>
                Showing page {filters.page} of {Math.ceil((logsData.count || 1) / (filters.page_size || 20))} (
                {logsData.count} total records)
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!logsData.previous}
                  onClick={() => setFilters((prev) => ({ ...prev, page: Math.max(1, (prev.page || 1) - 1) }))}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!logsData.next}
                  onClick={() => setFilters((prev) => ({ ...prev, page: (prev.page || 1) + 1 }))}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Details Slide-Over / Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
              <div className="flex items-center gap-2">
                <ShieldAlert className="h-5 w-5 text-brand-navy" />
                <h3 className="font-bold text-brand-dark">Audit Event Detail</h3>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="text-slate-400 hover:text-slate-600 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-slate-500 uppercase">Action</label>
                  <p className="font-semibold text-brand-dark mt-0.5">{selectedLog.action}</p>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500 uppercase">Timestamp</label>
                  <p className="font-mono text-xs text-slate-700 mt-0.5">{selectedLog.created_at}</p>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500 uppercase">Resource Type</label>
                  <p className="font-medium text-slate-800 mt-0.5">{selectedLog.resource_type}</p>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500 uppercase">Resource ID</label>
                  <p className="font-mono text-xs text-slate-600 mt-0.5">{selectedLog.resource_id}</p>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500 uppercase">Actor</label>
                  <p className="text-slate-800 mt-0.5">
                    {selectedLog.user ? `${selectedLog.user.full_name} (${selectedLog.user.email})` : "SYSTEM"}
                  </p>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500 uppercase">IP Address</label>
                  <p className="font-mono text-xs text-slate-600 mt-0.5">{selectedLog.ip_address || "None"}</p>
                </div>
                <div className="col-span-2">
                  <label className="text-xs font-semibold text-slate-500 uppercase">Correlation ID</label>
                  <p className="font-mono text-xs text-slate-600 mt-0.5">{selectedLog.correlation_id || "None"}</p>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-500 uppercase">Changes Payload (JSON)</label>
                <pre className="mt-1 p-3 bg-slate-900 text-slate-100 rounded-md text-xs font-mono overflow-x-auto max-h-60">
                  {JSON.stringify(selectedLog.changes, null, 2)}
                </pre>
              </div>
            </div>

            <div className="px-6 py-3 border-t border-slate-200 bg-slate-50 flex justify-end">
              <Button variant="outline" size="sm" onClick={() => setSelectedLog(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
