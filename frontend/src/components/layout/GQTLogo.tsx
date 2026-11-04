import React, { useState } from "react";
import { cn } from "../../lib/utils";

interface GQTLogoProps {
  className?: string;
  size?: "sm" | "md" | "lg";
  variant?: "dark" | "light";
}

export const GQTLogo: React.FC<GQTLogoProps> = ({
  className,
  size = "md",
  variant = "dark",
}) => {
  const [imageError, setImageError] = useState(false);

  const sizeClasses = {
    sm: "h-7 w-auto",
    md: "h-9 w-auto",
    lg: "h-12 w-auto",
  };

  return (
    <div className={cn("inline-flex items-center gap-2 select-none", className)}>
      {!imageError ? (
        <img
          src="/images/gqt-logo.png"
          alt="Global Quest Technologies"
          className={cn("object-contain", sizeClasses[size])}
          onError={() => setImageError(true)}
        />
      ) : (
        <div className="flex items-center gap-1.5 font-bold tracking-tight">
          <span className="rounded bg-brand-navy px-1.5 py-0.5 text-xs text-white">GQT</span>
          <span className={cn("text-sm", variant === "light" ? "text-white" : "text-brand-dark")}>
            HRMS
          </span>
        </div>
      )}
    </div>
  );
};
