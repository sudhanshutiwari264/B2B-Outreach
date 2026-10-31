import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-border bg-surface shadow-sm ${className}`}>
      {children}
    </div>
  );
}

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-6 flex items-start justify-between gap-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-foreground">{title}</h1>
        {description && <p className="mt-1 text-sm text-muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}

type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: "bg-accent text-accent-foreground hover:opacity-90 disabled:opacity-50",
  secondary: "border border-border bg-surface text-foreground hover:bg-surface-muted disabled:opacity-50",
  danger: "bg-danger text-white hover:opacity-90 disabled:opacity-50",
  ghost: "text-muted hover:bg-surface-muted disabled:opacity-50",
};

export function Button({
  variant = "primary",
  className = "",
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-1.5 rounded-md px-3.5 py-2 text-sm font-medium transition-colors ${VARIANT_CLASSES[variant]} ${className}`}
      {...props}
    >
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
      className={`inline-flex items-center justify-center gap-1.5 rounded-md px-3.5 py-2 text-sm font-medium transition-colors ${VARIANT_CLASSES[variant]} ${className}`}
    >
      {children}
    </Link>
  );
}

export function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <Card className="px-4 py-3.5">
      <div className="text-2xl font-semibold tracking-tight text-foreground">{value}</div>
      <div className="mt-0.5 text-xs text-muted">{label}</div>
    </Card>
  );
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-14 text-center">
      <p className="text-sm font-medium text-foreground">{title}</p>
      {description && <p className="mt-1 max-w-sm text-sm text-muted">{description}</p>}
    </div>
  );
}

export function Spinner({ className = "" }: { className?: string }) {
  return (
    <span
      className={`inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent ${className}`}
      aria-label="Loading"
    />
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-danger/30 bg-danger-soft px-4 py-3 text-sm text-danger">
      {message}
    </div>
  );
}
