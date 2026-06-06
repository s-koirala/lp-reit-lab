import { DATA_PROVENANCE } from "@/lib/data/source";
import { cn } from "@/lib/utils";

// Per-section data-provenance caption, driven by the single DATA_PROVENANCE
// source. Keeps the synthetic basis + vintage explicit wherever data is shown
// (honesty / research-integrity), complementing the global footer disclaimer.
export function ProvenanceNote({ className }: { className?: string }) {
  const p = DATA_PROVENANCE;
  return (
    <p
      title={p.basis}
      className={cn(
        "text-[10px] font-mono uppercase tracking-wider text-muted-foreground",
        className,
      )}
    >
      {p.label} · vintage {p.asOf}
      {p.source === "synthetic" ? " · not real listings" : ""}
    </p>
  );
}

// Reusable empty-state for data sections (charts, tables) — shown when a series or
// query yields no rows. Real-data-readiness: synthetic fixtures are never empty,
// but real feeds can be (a submarket with no sales in a window, a filtered-out set).
export function EmptyState({ label }: { label: string }) {
  return (
    <div className="flex h-full min-h-32 items-center justify-center p-8 text-center text-xs text-muted-foreground">
      {label}
    </div>
  );
}
