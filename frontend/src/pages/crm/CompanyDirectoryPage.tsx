import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Building2,
  Plus,
  Search,
  Users,
  PhoneCall,
  Clock,
  ExternalLink,
} from "lucide-react";
import { crmApi } from "../../api/crmApi";
import { Company } from "../../types/crm";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { Card, CardHeader, CardContent } from "../../components/ui/Card";
import { LoadingState } from "../../components/ui/LoadingState";
import { ErrorState } from "../../components/ui/ErrorState";
import { EmptyState } from "../../components/ui/EmptyState";
import { CreateCompanyModal } from "../../components/crm/CreateCompanyModal";

export const CompanyDirectoryPage: React.FC = () => {
  const { hasAnyRole } = useAuth();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [industryFilter, setIndustryFilter] = useState("");
  const [page, setPage] = useState(1);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const canEdit = hasAnyRole(["ADMIN", "PLACEMENT_HEAD", "CALLING_EXECUTIVE", "CRM_EXECUTIVE"]);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["companies", search, statusFilter, industryFilter, page],
    queryFn: () =>
      crmApi.getCompanies({
        search: search || undefined,
        status: statusFilter || undefined,
        industry: industryFilter || undefined,
        page,
      }),
  });

  const getStatusVariant = (status: string) => {
    switch (status) {
      case "ACTIVE_HIRING_PARTNER":
        return "success";
      case "ENGAGED":
        return "info";
      case "CONTACTED":
        return "neutral";
      case "LEAD":
        return "neutral";
      case "DORMANT":
        return "warning";
      case "BLACKLISTED":
        return "danger";
      default:
        return "neutral";
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-brand-dark flex items-center gap-2">
            <Building2 className="h-6 w-6 text-brand-blue" />
            Company & Employer Directory
          </h1>
          <p className="mt-1 text-xs text-brand-muted">
            Track hiring partners, acquisition pipeline, and corporate relationships.
          </p>
        </div>

        {canEdit && (
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="h-4 w-4" />}
            onClick={() => setIsCreateModalOpen(true)}
          >
            Add Target Company
          </Button>
        )}
      </div>

      {/* Filter and Search Bar */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 md:grid-cols-4 gap-3">
            <div className="sm:col-span-2">
              <Input
                placeholder="Search companies by name, domain, or notes..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                leftIcon={<Search className="h-4 w-4" />}
              />
            </div>

            <div>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full h-10 rounded-md border border-slate-300 bg-white px-3 text-xs text-brand-dark focus:border-brand-blue focus:ring-1 focus:ring-brand-blue"
              >
                <option value="">All Pipeline Statuses</option>
                <option value="LEAD">Lead / Prospect</option>
                <option value="CONTACTED">Contacted</option>
                <option value="ENGAGED">Engaged</option>
                <option value="ACTIVE_HIRING_PARTNER">Active Hiring Partner</option>
                <option value="DORMANT">Dormant</option>
                <option value="BLACKLISTED">Blacklisted</option>
              </select>
            </div>

            <div>
              <select
                value={industryFilter}
                onChange={(e) => {
                  setIndustryFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full h-10 rounded-md border border-slate-300 bg-white px-3 text-xs text-brand-dark focus:border-brand-blue focus:ring-1 focus:ring-brand-blue"
              >
                <option value="">All Industries</option>
                <option value="IT_SERVICES">IT Services & Consulting</option>
                <option value="PRODUCT_TECH">Product / Software Tech</option>
                <option value="FINTECH">FinTech</option>
                <option value="EDTECH">EdTech</option>
                <option value="HEALTHCARE">Healthcare</option>
                <option value="MANUFACTURING">Manufacturing</option>
                <option value="ECOMMERCE">E-Commerce</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Companies Table / Content Area */}
      <Card>
        <CardHeader className="flex items-center justify-between py-3">
          <div className="text-xs font-semibold text-brand-dark">
            Showing {data?.results?.length || 0} of {data?.count || 0} Companies
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {isLoading && <LoadingState message="Loading target companies..." />}

          {isError && (
            <ErrorState
              title="Failed to load companies"
              message="Could not retrieve the company directory from backend API."
              onRetry={() => refetch()}
            />
          )}

          {!isLoading && !isError && data?.results?.length === 0 && (
            <EmptyState
              title="No companies found"
              description="No target employers match your search or filter criteria."
              action={
                canEdit && (
                  <Button
                    variant="outline"
                    size="sm"
                    leftIcon={<Plus className="h-4 w-4" />}
                    onClick={() => setIsCreateModalOpen(true)}
                  >
                    Add Company
                  </Button>
                )
              }
            />
          )}

          {!isLoading && !isError && data && data.results.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-600 border-b border-slate-100">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Company Name</th>
                    <th className="px-4 py-3 font-semibold">Domain / Website</th>
                    <th className="px-4 py-3 font-semibold">Industry</th>
                    <th className="px-4 py-3 font-semibold">Status</th>
                    <th className="px-4 py-3 font-semibold text-center">Contacts</th>
                    <th className="px-4 py-3 font-semibold text-center">Touchpoints</th>
                    <th className="px-4 py-3 font-semibold text-center">Follow-Ups</th>
                    <th className="px-4 py-3 font-semibold">Assigned Executive</th>
                    <th className="px-4 py-3 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.results.map((comp: Company) => (
                    <tr key={comp.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 font-medium text-brand-dark">
                        <Link
                          to={`/companies/${comp.id}`}
                          className="hover:text-brand-blue hover:underline"
                        >
                          {comp.name}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-slate-500">
                        {comp.canonical_domain ? (
                          <span className="inline-flex items-center gap-1">
                            {comp.canonical_domain}
                            {comp.website && (
                              <a
                                href={comp.website}
                                target="_blank"
                                rel="noreferrer"
                                className="text-slate-400 hover:text-brand-blue"
                              >
                                <ExternalLink className="h-3 w-3" />
                              </a>
                            )}
                          </span>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-600">{comp.industry.replace("_", " ")}</td>
                      <td className="px-4 py-3">
                        <StatusBadge variant={getStatusVariant(comp.status)} dot>
                          {comp.status.replace(/_/g, " ")}
                        </StatusBadge>
                      </td>
                      <td className="px-4 py-3 text-center text-slate-600 font-medium">
                        <span className="inline-flex items-center gap-1">
                          <Users className="h-3 w-3 text-slate-400" />
                          {comp.contacts_count}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center text-slate-600 font-medium">
                        <span className="inline-flex items-center gap-1">
                          <PhoneCall className="h-3 w-3 text-slate-400" />
                          {comp.outreach_count}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center text-slate-600 font-medium">
                        <span className="inline-flex items-center gap-1">
                          <Clock className="h-3 w-3 text-slate-400" />
                          {comp.pending_followups_count}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {comp.assigned_to_name || <span className="text-slate-400">Unassigned</span>}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          to={`/companies/${comp.id}`}
                          className="rounded px-2.5 py-1 text-xs font-medium text-brand-blue hover:bg-sky-50"
                        >
                          View Profile &rarr;
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Modal */}
      <CreateCompanyModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={() => refetch()}
      />
    </div>
  );
};
