import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Building2,
  PhoneCall,
  Briefcase,
  Palette,
  GraduationCap,
  CalendarCheck,
  ShieldAlert,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { cn } from "../../lib/utils";
import { RoleCode } from "../../types";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  requiredRoles?: RoleCode[];
}

const navigationItems: NavItem[] = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Companies & Contacts",
    href: "/companies",
    icon: Building2,
    requiredRoles: ["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "CALLING_EXECUTIVE", "CRM_EXECUTIVE", "AUDITOR"],
  },
  {
    name: "Calling & Outreach",
    href: "/outreach",
    icon: PhoneCall,
    requiredRoles: ["ADMIN", "PLACEMENT_HEAD", "CALLING_EXECUTIVE", "CRM_EXECUTIVE", "AUDITOR"],
  },
  {
    name: "Job Requirements & Verification",
    href: "/jobs",
    icon: Briefcase,
    requiredRoles: ["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "CALLING_EXECUTIVE", "CRM_EXECUTIVE", "AUDITOR"],
  },
  {
    name: "Creative Studio",
    href: "/creatives",
    icon: Palette,
    requiredRoles: ["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "CREATIVE_DESIGNER", "CREATIVE_REVIEWER", "AUDITOR"],
  },
  {
    name: "Students & Readiness",
    href: "/students",
    icon: GraduationCap,
    requiredRoles: ["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "TRAINER"],
  },
  {
    name: "Interviews & Drives",
    href: "/interviews",
    icon: CalendarCheck,
    requiredRoles: ["ADMIN", "PLACEMENT_HEAD", "PLACEMENT_OFFICER", "INTERVIEW_COORDINATOR"],
  },
  {
    name: "Audit & Compliance",
    href: "/audit",
    icon: ShieldAlert,
    requiredRoles: ["ADMIN", "AUDITOR"],
  },
];

interface SidebarProps {
  onItemClick?: () => void;
  className?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ onItemClick, className }) => {
  const { hasAnyRole, user } = useAuth();

  const filteredItems = navigationItems.filter((item) => {
    if (!item.requiredRoles) return true;
    if (user?.isSuperuser) return true;
    return hasAnyRole(item.requiredRoles);
  });

  return (
    <aside
      className={cn(
        "flex h-full w-64 flex-col border-r border-slate-200 bg-white",
        className
      )}
    >
      <div className="flex-1 overflow-y-auto px-3 py-4">
        <nav className="space-y-1">
          {filteredItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.href}
                onClick={onItemClick}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-brand-navy text-white shadow-sm"
                      : "text-slate-600 hover:bg-slate-50 hover:text-brand-dark"
                  )
                }
              >
                <Icon className="h-4 w-4 shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      <div className="border-t border-slate-100 p-4">
        <div className="rounded-md bg-slate-50 p-3 text-xs text-slate-500">
          <p className="font-semibold text-brand-dark">GQT HRMS v1.0</p>
          <p className="mt-0.5 text-[11px]">Strict RBAC & Audit Active</p>
        </div>
      </div>
    </aside>
  );
};
