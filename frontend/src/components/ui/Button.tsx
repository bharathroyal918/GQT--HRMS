import React from "react";
import { Loader2 } from "lucide-react";
import { cn } from "../../lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      isLoading = false,
      leftIcon,
      rightIcon,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const variantStyles = {
      primary: "bg-brand-navy hover:bg-opacity-90 text-white shadow-sm focus-visible:ring-brand-blue",
      secondary: "bg-brand-blue hover:bg-opacity-90 text-white shadow-sm focus-visible:ring-brand-navy",
      danger: "bg-red-600 hover:bg-red-700 text-white shadow-sm focus-visible:ring-red-500",
      outline: "border border-slate-300 bg-white hover:bg-slate-50 text-brand-dark focus-visible:ring-brand-navy",
      ghost: "hover:bg-slate-100 text-brand-dark focus-visible:ring-brand-navy",
    };

    const sizeStyles = {
      sm: "h-8 px-3 text-xs font-medium rounded-md gap-1.5",
      md: "h-10 px-4 text-sm font-medium rounded-md gap-2",
      lg: "h-12 px-6 text-base font-medium rounded-lg gap-2.5",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          "inline-flex items-center justify-center transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 select-none",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {isLoading && <Loader2 className="h-4 w-4 animate-spin" data-testid="button-spinner" />}
        {!isLoading && leftIcon && <span className="inline-flex shrink-0">{leftIcon}</span>}
        <span>{children}</span>
        {!isLoading && rightIcon && <span className="inline-flex shrink-0">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = "Button";
