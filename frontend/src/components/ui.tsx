import Link from "next/link";
import { AlertCircle, Inbox, Loader2, type LucideIcon } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";

/** A hairline panel: 1px rule, one surface step up, no shadow (Console never floats a card). */
export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-card border border-rule bg-paper-2 ${className}`}>{children}</div>
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
        {Icon && <Icon className="mt-0.5 h-5 w-5 shrink-0 text-muted" strokeWidth={1.75} />}
        <div className="min-w-0">
          <h1 className="text-lg text-ink">{title}</h1>
          {description && <p className="mt-1 text-sm text-muted">{description}</p>}
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

type ButtonVariant = "primary" | "secondary" | "danger" | "success" | "ghost";

// Console's pair: an amber fill primary beside a rule-outline secondary. Ok/bad exist only
// for diffs and status, never as a button fill, so danger/success stay outline + text tint.
const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: "bg-accent text-accent-ink hover:brightness-110 active:brightness-95 disabled:opacity-50",
  secondary:
    "border border-rule-2 bg-paper-2 text-ink hover:bg-paper-3 active:bg-paper disabled:opacity-50",
  danger: "border border-rule-2 bg-paper-2 text-bad hover:bg-bad-soft disabled:opacity-50",
  success: "border border-rule-2 bg-paper-2 text-ok hover:bg-ok-soft disabled:opacity-50",
  ghost: "text-muted hover:bg-paper-3 hover:text-ink disabled:opacity-50",
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
      className={`inline-flex h-9 items-center justify-center gap-1.5 rounded-pill px-3.5 text-sm font-medium transition-colors duration-150 ${VARIANT_CLASSES[variant]} ${className}`}
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
      className={`inline-flex h-9 items-center justify-center gap-1.5 rounded-pill px-3.5 text-sm font-medium transition-colors duration-150 ${VARIANT_CLASSES[variant]} ${className}`}
    >
      {children}
    </Link>
  );
}

/** A reading: the figure in the measured (mono) face, tabular, the label beneath it in the
 * body face. No icon tile, no gradient, no trend arrow nobody measured (app-screen figures). */
export function StatTile({ label, value, href }: { label: string; value: string | number; href?: string }) {
  const inner = (
    <>
      <div className="font-outlier text-2xl tabular-nums text-ink">{value}</div>
      <div className="mt-0.5 text-sm text-muted">{label}</div>
    </>
  );

  if (href) {
    return (
      <Link href={href} className="block">
        <Card className="px-4 py-3.5 transition-colors hover:bg-paper-3">{inner}</Card>
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
    <div className="flex flex-col items-center justify-center rounded-card border border-dashed border-rule py-14 text-center">
      <Icon className="mb-3 h-5 w-5 text-muted" strokeWidth={1.5} />
      <p className="text-sm text-ink">{title}</p>
      {description && <p className="mt-1 max-w-sm px-4 text-sm text-muted">{description}</p>}
    </div>
  );
}

export function Spinner({ className = "" }: { className?: string }) {
  return <Loader2 className={`h-4 w-4 animate-spin ${className}`} aria-label="Loading" />;
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-2.5 rounded-card border border-rule bg-bad-soft px-4 py-3 text-sm text-bad">
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" strokeWidth={2} />
      <span>{message}</span>
    </div>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton rounded-md ${className}`} />;
}
