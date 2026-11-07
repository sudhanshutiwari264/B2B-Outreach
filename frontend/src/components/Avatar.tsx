function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

const SIZE_CLASSES = {
  sm: "h-6 w-6 text-[10px]",
  md: "h-9 w-9 text-xs",
  lg: "h-12 w-12 text-sm",
};

/** A person's initials, not a figure: on the paper's deepest step, in the muted ink, inside
 * a 1px rule. Console keeps one accent for a person's state, not one per name. */
export function Avatar({ name, size = "md" }: { name: string; size?: keyof typeof SIZE_CLASSES }) {
  return (
    <span
      className={`flex shrink-0 items-center justify-center rounded-full border border-rule bg-paper-3 font-medium text-muted ${SIZE_CLASSES[size]}`}
    >
      {initials(name)}
    </span>
  );
}
