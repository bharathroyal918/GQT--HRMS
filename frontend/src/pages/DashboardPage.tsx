import React from "react";
import {
  Building2,
  Briefcase,
  Users,
  Calendar,
  CheckCircle2,
  TrendingUp,
  FileCheck,
  UserCheck,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { Card, CardHeader, CardContent } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/StatusBadge";
import { Button } from "../components/ui/Button";

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  const metrics = [
    {
      title: "Target Companies",
      value: "148",
      subtext: "+12 added this month",
      icon: Building2,
      trend: "up",
    },
    {
      title: "Active Job Drives",
      value: "24",
      subtext: "8 pending head approval",
      icon: Briefcase,
      trend: "neutral",
    },
    {
      title: "Eligible Students",
      value: "840",
      subtext: "Synced with Student Portal",
      icon: Users,
      trend: "up",
    },
    {
      title: "Scheduled Interviews",
      value: "42",
      subtext: "Next drive starts tomorrow",
      icon: Calendar,
      trend: "neutral",
    },
  ];

  const recentDrives = [
    {
      company: "Infosys Technologies",
      role: "Associate Software Engineer",
      driveDate: "Nov 08, 2026",
      status: "Approved",
      eligibleCount: 165,
    },
    {
      company: "TCS Enterprise",
      role: "Systems Engineer (Ninja & Digital)",
      driveDate: "Nov 12, 2026",
      status: "Pending Approval",
      eligibleCount: 210,
    },
    {
      company: "Cognizant GenC",
      role: "Programmer Analyst Trainee",
      driveDate: "Nov 15, 2026",
      status: "Design Ready",
      eligibleCount: 140,
    },
    {
      company: "Wipro Turbo",
      role: "Project Engineer",
      driveDate: "Nov 20, 2026",
      status: "Draft",
      eligibleCount: 95,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome & Role Context Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-xl bg-brand-navy p-6 text-white shadow-sm">
        <div>
          <h1 className="text-xl font-bold tracking-tight">
            Welcome back, {user?.firstName || user?.fullName || "Staff Member"}!
          </h1>
          <p className="mt-1 text-xs text-slate-300">
            Global Quest Technologies • Placement Operations & Recruitment CRM
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {user?.roles.map((role) => (
              <span
                key={role}
                className="inline-flex items-center rounded-md bg-white/10 px-2.5 py-0.5 text-xs font-medium text-white backdrop-blur-sm"
              >
                {role}
              </span>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" leftIcon={<FileCheck className="h-4 w-4" />}>
            New Drive Req
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="bg-transparent border-white/20 text-white hover:bg-white/10"
            leftIcon={<UserCheck className="h-4 w-4" />}
          >
            Review Students
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <Card key={metric.title} className="p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-brand-muted">{metric.title}</span>
                <div className="rounded-lg bg-slate-100 p-2 text-brand-blue">
                  <Icon className="h-4 w-4" />
                </div>
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-brand-dark">{metric.value}</span>
                <span className="text-[11px] text-emerald-600 flex items-center gap-0.5">
                  <TrendingUp className="h-3 w-3" />
                  active
                </span>
              </div>
              <p className="mt-1 text-[11px] text-slate-500">{metric.subtext}</p>
            </Card>
          );
        })}
      </div>

      {/* Primary Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Drives Table */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-brand-dark">Active Placement Drives</h2>
                <p className="text-xs text-slate-500">Pipeline from acquisition to selection</p>
              </div>
              <Button variant="ghost" size="sm" className="text-xs text-brand-blue">
                View All
              </Button>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 border-b border-slate-100">
                    <tr>
                      <th className="px-4 py-3 font-medium">Company</th>
                      <th className="px-4 py-3 font-medium">Role</th>
                      <th className="px-4 py-3 font-medium">Drive Date</th>
                      <th className="px-4 py-3 font-medium">Eligible</th>
                      <th className="px-4 py-3 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {recentDrives.map((drive) => (
                      <tr key={drive.company} className="hover:bg-slate-50">
                        <td className="px-4 py-3 font-medium text-brand-dark">{drive.company}</td>
                        <td className="px-4 py-3 text-slate-600">{drive.role}</td>
                        <td className="px-4 py-3 text-slate-500">{drive.driveDate}</td>
                        <td className="px-4 py-3 text-slate-600">{drive.eligibleCount}</td>
                        <td className="px-4 py-3">
                          <StatusBadge
                            variant={
                              drive.status === "Approved"
                                ? "success"
                                : drive.status === "Pending Approval"
                                ? "warning"
                                : "info"
                            }
                            dot
                          >
                            {drive.status}
                          </StatusBadge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Operational Security & System Readiness Panel */}
        <div>
          <Card>
            <CardHeader>
              <h2 className="text-sm font-semibold text-brand-dark">System & Gateway Status</h2>
              <p className="text-xs text-slate-500">Security gates and integration health</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-600">Auth & RBAC Subsystem</span>
                <StatusBadge variant="success" dot>
                  Enforcing
                </StatusBadge>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-600">Audit Trail Logging</span>
                <StatusBadge variant="success" dot>
                  Immutable
                </StatusBadge>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-600">GQT Student Portal Gateway</span>
                <StatusBadge variant="neutral" dot>
                  Sandbox / Mock
                </StatusBadge>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-600">Session Security</span>
                <StatusBadge variant="success" dot>
                  HttpOnly Cookie
                </StatusBadge>
              </div>

              <div className="rounded-md bg-slate-50 p-3 text-xs text-slate-600 border border-slate-200 mt-4">
                <div className="flex items-center gap-1.5 font-medium text-brand-dark mb-1">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  Phase 1 Quality Invariants
                </div>
                <p className="text-[11px] leading-relaxed">
                  All requests carry correlation IDs. Sensitive authentication credentials and tokens
                  are strictly filtered from application log streams.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
