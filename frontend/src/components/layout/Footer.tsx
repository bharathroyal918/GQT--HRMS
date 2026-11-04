import React from "react";

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-slate-200 bg-white py-4 px-6 text-center text-xs text-slate-500">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2 max-w-7xl mx-auto">
        <p>© {new Date().getFullYear()} Global Quest Technologies (GQT). All rights reserved.</p>
        <p className="text-[11px] text-slate-400">
          Internal Recruitment CRM & Placement Operations Platform • Single-Tenant Architecture
        </p>
      </div>
    </footer>
  );
};
