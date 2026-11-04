import React, { useState } from "react";
import { Menu, LogOut, ChevronDown } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { GQTLogo } from "./GQTLogo";
import { StatusBadge } from "../ui/StatusBadge";

interface HeaderProps {
  onToggleSidebar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
  const { user, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200 bg-white px-4 md:px-6 shadow-sm">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onToggleSidebar}
          className="rounded-md p-1.5 text-slate-500 hover:bg-slate-100 hover:text-brand-dark md:hidden focus:outline-none focus:ring-2 focus:ring-brand-blue"
          aria-label="Toggle navigation drawer"
        >
          <Menu className="h-5 w-5" />
        </button>
        <GQTLogo size="md" />
        <div className="hidden sm:flex flex-col border-l border-slate-200 pl-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-brand-navy">
            HRMS & Recruitment CRM
          </span>
          <span className="text-[11px] text-slate-500">Placement Operations Platform</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {user && (
          <div className="relative">
            <button
              type="button"
              onClick={() => setDropdownOpen((prev) => !prev)}
              className="flex items-center gap-2 rounded-full p-1 text-sm text-brand-dark hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-brand-blue"
              aria-expanded={dropdownOpen}
              aria-haspopup="true"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-navy text-xs font-semibold text-white">
                {user.firstName ? user.firstName[0]?.toUpperCase() : user.email[0]?.toUpperCase()}
              </div>
              <div className="hidden text-left md:block">
                <p className="text-xs font-medium leading-none text-brand-dark">{user.fullName}</p>
                <p className="text-[10px] text-slate-500 leading-tight mt-0.5">{user.email}</p>
              </div>
              <ChevronDown className="h-4 w-4 text-slate-400" />
            </button>

            {dropdownOpen && (
              <div
                className="absolute right-0 mt-2 w-64 origin-top-right rounded-md border border-slate-200 bg-white p-2 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-50"
                role="menu"
              >
                <div className="border-b border-slate-100 px-3 py-2">
                  <p className="text-sm font-semibold text-brand-dark">{user.fullName}</p>
                  <p className="text-xs text-slate-500 truncate">{user.email}</p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {user.roles.slice(0, 3).map((role) => (
                      <StatusBadge key={role} variant="info" className="text-[10px]">
                        {role}
                      </StatusBadge>
                    ))}
                    {user.roles.length > 3 && (
                      <span className="text-[10px] text-slate-400">+{user.roles.length - 3}</span>
                    )}
                  </div>
                </div>

                <div className="pt-1">
                  <button
                    type="button"
                    onClick={() => {
                      setDropdownOpen(false);
                      logout();
                    }}
                    className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-xs font-medium text-red-600 hover:bg-red-50 transition-colors"
                    role="menuitem"
                  >
                    <LogOut className="h-4 w-4" />
                    Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
};
