import Link from "next/link";
import { AlertCircle, Inbox, Loader2, type LucideIcon } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

export function Card({
  children,
  className = "",
  hover = false,
}: {
  children: ReactNode;
  className?: string;
  hover?: boolean;
}) {
  return (
    <div
      className={`rounded-xl border border-border bg-surface shadow-[var(--shadow-sm)] transition-shadow duration-200 ${
        hover ? "hover:shadow-[var(--shadow-md)]" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
}

/** Lets a wide table scroll horizontally on narrow screens instead of crushing columns. */
export function TableScroll({ children, minWidth = 560 }: { children: ReactNode; minWidth?: number }) {
  return (
    <div className="overflow-x-auto">
      <div style={{ minWidth }}>{children}</div>
    </div>
  );
}

export function PageHeader({
  title,
  description,
  action,
  icon: Icon,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  icon?: LucideIcon;
}) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div className="flex min-w-0 items-start gap-3">
        {Icon && (
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent-soft text-accent">
            <Icon className="h-[18px] w-[18px]" strokeWidth={2} />
          </div>
        )}
        <div className="min-w-0">
          <h1 className="text-lg font-semibold tracking-tight text-foreground sm:text-xl">{title}</h1>
          {description && <p className="mt-1 text-sm text-muted">{description}</p>}
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

type ButtonVariant = "primary" | "secondary" | "danger" | "success" | "ghost";

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    "bg-accent text-accent-foreground shadow-[var(--shadow-xs)] hover:bg-accent-hover active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100",
  secondary:
    "border border-border bg-surface text-foreground shadow-[var(--shadow-xs)] hover:bg-surface-muted active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100",
  danger:
    "bg-danger text-white shadow-[var(--shadow-xs)] hover:opacity-90 active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100",
  success:
    "bg-success text-white shadow-[var(--shadow-xs)] hover:opacity-90 active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100",
  ghost: "text-muted hover:bg-surface-muted hover:text-foreground disabled:opacity-50",
};

export function Button({
  variant = "primary",
  className = "",
  children,
  loading = false,
  disabled,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant; loading?: boolean }) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-medium transition-all duration-150 ${VARIANT_CLASSES[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
      {children}
    </button>
  );
}

export function LinkButton({
  href,
  variant = "primary",
  className = "",
  children,
}: {
  href: string;
  variant?: ButtonVariant;
  className?: string;
  children: ReactNode;
}) {
  return (
    <Link
      href={href}
      className={`inline-flex items-center justify-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-medium transition-all duration-150 ${VARIANT_CLASSES[variant]} ${className}`}
    >
      {children}
    </Link>
  );
}

export function StatTile({
  label,
  value,
  href,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  href?: string;
  icon?: LucideIcon;
}) {
  const inner = (
    <div className="flex items-start justify-between gap-3">
      <div>
        <div className="text-2xl font-semibold tracking-tight text-foreground">{value}</div>
        <div className="mt-0.5 text-xs text-muted">{label}</div>
      </div>
      {Icon && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent-soft text-accent">
          <Icon className="h-4 w-4" strokeWidth={2} />
        </div>
      )}
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="block">
        <Card hover className="px-4 py-3.5 hover:border-accent/40">
          {inner}
        </Card>
      </Link>
    );
  }

  return <Card className="px-4 py-3.5">{inner}</Card>;
}

export function EmptyState({
  title,
  description,
  icon: Icon = Inbox,
}: {
  title: string;
  description?: string;
  icon?: LucideIcon;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-surface/50 py-14 text-center">
      <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-surface-muted text-muted">
        <Icon className="h-5 w-5" strokeWidth={1.75} />
      </div>
      <p className="text-sm font-medium text-foreground">{title}</p>
      {description && <p className="mt-1 max-w-sm px-4 text-sm text-muted">{description}</p>}
    </div>
  );
}

export function Spinner({ className = "" }: { className?: string }) {
  return <Loader2 className={`h-4 w-4 animate-spin ${className}`} aria-label="Loading" />;
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2.5 rounded-lg border border-danger/30 bg-danger-soft px-4 py-3 text-sm text-danger">
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" strokeWidth={2} />
      <span>{message}</span>
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton rounded-md ${className}`} />;
}
