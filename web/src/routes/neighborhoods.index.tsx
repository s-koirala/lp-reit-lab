import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { NEIGHBORHOODS } from "@/lib/data/neighborhoods";
import { PROPERTIES } from "@/lib/data/properties";
import { fmtMoney, fmtPct } from "@/lib/format";

export const Route = createFileRoute("/neighborhoods/")({
  head: () => ({ meta: [{ title: "Neighborhoods — Lincoln Park Property Lab" }] }),
  component: NeighborhoodIndex,
});

function NeighborhoodIndex() {
  return (
    <AppShell>
      <header className="rule-b pb-6 mb-8">
        <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted-foreground mb-2">
          Submarket atlas
        </p>
        <h1 className="text-5xl">Six pockets, six personalities.</h1>
      </header>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-rule rule-t rule-b">
        {NEIGHBORHOODS.map((n) => {
          const count = PROPERTIES.filter((p) => p.neighborhoodSlug === n.slug).length;
          return (
            <Link
              key={n.slug}
              to="/neighborhoods/$slug"
              params={{ slug: n.slug }}
              className="bg-card p-6 hover:bg-secondary/40 transition-colors"
            >
              <div className="flex items-start justify-between">
                <h2 className="text-3xl">{n.name}</h2>
                <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                  {count} listings
                </span>
              </div>
              <p className="text-sm text-ink-soft mt-3 max-w-md">{n.blurb}</p>
              <div className="grid grid-cols-4 gap-4 mt-5 rule-t pt-4 tabular">
                <Mini label="Median" value={fmtMoney(n.medianPrice, { compact: true })} />
                <Mini label="3BR rent" value={`$${(n.medianRent3br / 1000).toFixed(1)}k`} />
                <Mini label="Net yield" value={fmtPct(n.yieldMedian, 1)} />
                <Mini label="5y appr" value={fmtPct(n.appreciation5y, 1)} />
              </div>
            </Link>
          );
        })}
      </div>
    </AppShell>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div className="font-mono text-base mt-0.5">{value}</div>
    </div>
  );
}
