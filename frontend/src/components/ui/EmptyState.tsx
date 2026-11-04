import React from "react";
import { FolderOpen } from "lucide-react";
import { cn } from "../../lib/utils";

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = "No data available",
  description = "There are no records matching your criteria.",
  icon,
  action,
  actionText,
  onAction,
  className,
}) => (
  <div className={cn("flex flex-col items-center justify-center p-8 text-center", className)}>
    <div className="mb-4 rounded-full bg-slate-100 p-3 text-slate-400">
      {icon || <FolderOpen className="h-8 w-8" />}
    </div>
    <h3 className="text-base font-semibold text-brand-dark">{title}</h3>
    <p className="mt-1 text-sm text-brand-muted max-w-sm">{description}</p>
    {(action || (actionText && onAction)) && (
      <div className="mt-6">
        {action || (
          <button
            type="button"
            onClick={onAction}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 transition"
          >
            {actionText}
          </button>
        )}
      </div>
    )}
  </div>
);
