import React from "react";
import { AlertTriangle } from "lucide-react";
import { Button } from "./Button";
import { cn } from "../../lib/utils";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Something went wrong",
  message = "An error occurred while loading this view. Please try again.",
  onRetry,
  className,
}) => (
  <div className={cn("flex flex-col items-center justify-center p-8 text-center", className)}>
    <div className="mb-4 rounded-full bg-red-50 p-3 text-red-500">
      <AlertTriangle className="h-8 w-8" />
    </div>
    <h3 className="text-base font-semibold text-brand-dark">{title}</h3>
    <p className="mt-1 text-sm text-brand-muted max-w-sm">{message}</p>
    {onRetry && (
      <div className="mt-6">
        <Button variant="outline" onClick={onRetry}>
          Try Again
        </Button>
      </div>
    )}
  </div>
);
