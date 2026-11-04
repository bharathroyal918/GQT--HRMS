import React from "react";
import { Loader2 } from "lucide-react";
import { cn } from "../../lib/utils";

interface LoadingStateProps {
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = "Loading...",
  className,
}) => (
  <div className={cn("flex flex-col items-center justify-center p-12 text-center", className)}>
    <Loader2 className="h-8 w-8 animate-spin text-brand-blue mb-3" />
    <p className="text-sm text-brand-muted">{message}</p>
  </div>
);
