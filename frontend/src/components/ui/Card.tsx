import React from "react";
import { cn } from "../../lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "elevated" | "bordered";
}

export const Card: React.FC<CardProps> = ({
  className,
  variant = "default",
  children,
  ...props
}) => {
  const variantStyles = {
    default: "bg-white border border-slate-200 shadow-sm",
    elevated: "bg-white shadow-md border border-slate-100",
    bordered: "bg-white border-2 border-slate-200",
  };

  return (
    <div className={cn("rounded-lg overflow-hidden", variantStyles[variant], className)} {...props}>
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => (
  <div className={cn("px-6 py-4 border-b border-slate-100", className)} {...props}>
    {children}
  </div>
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => (
  <div className={cn("p-6", className)} {...props}>
    {children}
  </div>
);

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => (
  <div className={cn("px-6 py-4 bg-slate-50 border-t border-slate-100", className)} {...props}>
    {children}
  </div>
);
