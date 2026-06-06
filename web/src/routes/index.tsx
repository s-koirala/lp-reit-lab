import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { VerdictBadge } from "@/components/VerdictBadge";
import { NEIGHBORHOODS } from "@/lib/data/neighborhoods";
import {
  PROPERTIES,
  computeMetrics,
  blendedScore,
  type Property,
  type Metrics,
} from "@/lib/data/properties";
import { fmtMoney, fmtPct, fmtSignedPct } from "@/lib/format";
import { ScreenerTable } from "@/components/ScreenerTable";
import { ProvenanceNote } from "@/components/ProvenanceNote";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Screener — Lincoln Park Property Lab" },
      {
        name: "description",
        content:
          "Rank and filter Chicago North Side residential investment candidates by yield, appreciation, and price discount.",
      },
    ],
  }),
  component: ScreenerPage,
});

function ScreenerPage() {
  const [neighborhood, setNeighborhood] = useState<string>("all");
  const [minBeds, setMinBeds] = useState(2);
  const [maxPrice, setMaxPrice] = useState(2_500_000);
  const [minYield, setMinYield] = useState(0);
  const [verdictFilter, setVerdictFilter] = useState<string>("all");

  // Default order is the blended score (drives the shortlist); the ranked table
  // below offers ad-hoc column sorting + free-text search via TanStack Table.
  const rows = useMemo(() => {
    const all = PROPERTIES.map((p) => ({ p, m: computeMetrics(p) }));
    const filtered = all.filter(
      ({ p, m }) =>
        (neighborhood === "all" || p.neighborhoodSlug === neighborhood) &&
        p.beds >= minBeds &&
        p.listPrice <= maxPrice &&
        m.netRentYield >= minYield / 100 &&
        (verdictFilter === "all" || m.verdict === verdictFilter),
    );
    filtered.sort((a, b) => blendedScore(b.p, b.m) - blendedScore(a.p, a.m));
    return filtered;
  }, [neighborhood, minBeds, maxPrice, minYield, verdictFilter]);

  const top = rows.slice(0, 3);
  const stats = useMemo(() => {
    const total = rows.length;
    const goes = rows.filter((r) => r.m.verdict === "go").length;
    const avgYield = total ? rows.reduce((s, r) => s + r.m.netRentYield, 0) / total : 0;
    const avgAppr = total ? rows.reduce((s, r) => s + r.p.expectedAppreciation, 0) / total : 0;
    return { total, goes, avgYield, avgAppr };
  }, [rows]);

  return (
    <AppShell>
      {/* Masthead */}
      <section className="rule-b pb-8 mb-8">
        <div className="grid grid-cols-12 gap-6 items-end">
          <div className="col-span-12 md:col-span-7">
            <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted-foreground mb-3">
              Residential Investment Screener · North Side
            </p>
            <h1 className="text-6xl md:text-7xl leading-[0.95]">
              Find the few buildings <em className="text-muted-foreground">worth</em> the
              conviction.
            </h1>
            <p className="mt-5 text-base text-ink-soft max-w-2xl">
              Every candidate is scored on two axes — long-run appreciation and net rental yield —
              then triaged into a single headline verdict with the statistical confidence behind it.
              Filter, rank, and drill into the deal memo. Lincoln Park is appreciation-led, so most
              candidates screen NO-GO as income plays — by design (see Method).
            </p>
          </div>
          <div className="col-span-12 md:col-span-5 grid grid-cols-2 gap-4">
            <Stat
              label="Candidates"
              value={String(stats.total)}
              sub={`of ${PROPERTIES.length} indexed`}
            />
            <Stat label="Headline GO" value={String(stats.goes)} sub="passing all checks" />
            <Stat
              label="Avg cap rate"
              value={fmtPct(stats.avgYield, 2)}
              sub="operating, pre-debt"
            />
            <Stat label="Avg 5y appr." value={fmtPct(stats.avgAppr, 1)} sub="model forecast" />
          </div>
        </div>
      </section>

      {/* Filters */}
      <section className="grid grid-cols-12 gap-4 mb-8">
        <FilterBlock label="Neighborhood">
          <select
            value={neighborhood}
            onChange={(e) => setNeighborhood(e.target.value)}
            className="w-full bg-transparent rule-b border-foreground py-1.5 text-sm focus:outline-none"
          >
            <option value="all">All North Side</option>
            {NEIGHBORHOODS.map((n) => (
              <option key={n.slug} value={n.slug}>
                {n.name}
              </option>
            ))}
          </select>
        </FilterBlock>
        <FilterBlock label={`Min beds · ${minBeds}+`}>
          <input
            type="range"
            min={1}
            max={5}
            value={minBeds}
            onChange={(e) => setMinBeds(+e.target.value)}
            className="w-full accent-foreground"
          />
        </FilterBlock>
        <FilterBlock label={`Max price · ${fmtMoney(maxPrice, { compact: true })}`}>
          <input
            type="range"
            min={500_000}
            max={3_500_000}
            step={50_000}
            value={maxPrice}
            onChange={(e) => setMaxPrice(+e.target.value)}
            className="w-full accent-foreground"
          />
        </FilterBlock>
        <FilterBlock label={`Min net yield · ${minYield.toFixed(1)}%`}>
          <input
            type="range"
            min={0}
            max={8}
            step={0.1}
            value={minYield}
            onChange={(e) => setMinYield(+e.target.value)}
            className="w-full accent-foreground"
          />
        </FilterBlock>
        <FilterBlock label="Verdict">
          <div className="flex gap-1">
            {[
              ["all", "All"],
              ["go", "Go"],
              ["watch", "Watch"],
              ["no-go", "No-go"],
            ].map(([v, l]) => (
              <button
                key={v}
                onClick={() => setVerdictFilter(v)}
                className={`px-2 py-1 text-[11px] font-mono uppercase tracking-wider border ${verdictFilter === v ? "bg-foreground text-background border-foreground" : "border-rule text-muted-foreground hover:text-foreground"}`}
              >
                {l}
              </button>
            ))}
          </div>
        </FilterBlock>
      </section>

      {/* Shortlist */}
      {top.length > 0 && (
        <section className="mb-10">
          <SectionHead
            kicker="Lead candidates"
            title="Shortlist"
            subtitle="Top 3 by blended yield + appreciation score."
          />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-px bg-rule rule-t rule-b">
            {top.map(({ p, m }, i) => (
              <ShortlistCard key={p.id} p={p} m={m} rank={i + 1} />
            ))}
          </div>
        </section>
      )}

      {/* Full table */}
      <section>
        <SectionHead
          kicker={`${rows.length} matches`}
          title="Ranked candidate universe"
          subtitle="Click any row for the full deal memo."
        />
        <ProvenanceNote className="mb-3" />
        <ScreenerTable rows={rows} />
      </section>
    </AppShell>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rule-t pt-3">
      <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-muted-foreground">
        {label}
      </div>
      <div className="font-display text-3xl mt-1 leading-none">{value}</div>
      {sub && <div className="text-xs text-muted-foreground mt-1">{sub}</div>}
    </div>
  );
}

function FilterBlock({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="col-span-12 sm:col-span-6 lg:col-span-2">
      <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-muted-foreground mb-2">
        {label}
      </div>
      {children}
    </div>
  );
}

function SectionHead({
  kicker,
  title,
  subtitle,
}: {
  kicker: string;
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="flex items-end justify-between mb-4 gap-4">
      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-muted-foreground">
          {kicker}
        </div>
        <h2 className="text-3xl mt-1">{title}</h2>
      </div>
      {subtitle && <p className="text-sm text-muted-foreground max-w-xs text-right">{subtitle}</p>}
    </div>
  );
}

function ShortlistCard({ p, m, rank }: { p: Property; m: Metrics; rank: number }) {
  const neigh = NEIGHBORHOODS.find((n) => n.slug === p.neighborhoodSlug);
  return (
    <Link
      to="/property/$id"
      params={{ id: p.id }}
      className="bg-card p-6 hover:bg-secondary/40 transition-colors group"
    >
      <div className="flex items-start justify-between">
        <span className="font-display text-5xl text-muted-foreground/40 leading-none">
          No. {rank}
        </span>
        <VerdictBadge verdict={m.verdict} confidence={m.verdictConfidence} />
      </div>
      <div className="mt-6">
        <h3 className="text-2xl leading-tight">{p.address}</h3>
        <div className="text-xs font-mono uppercase tracking-wider text-muted-foreground mt-1">
          {neigh?.name} · {p.beds}BR · {p.baths}BA · {p.sqft.toLocaleString()} sf · {p.type}
        </div>
      </div>
      <div className="grid grid-cols-3 gap-4 mt-6 rule-t pt-4 tabular">
        <Mini label="List" value={fmtMoney(p.listPrice, { compact: true })} />
        <Mini
          label="Net yield"
          value={fmtPct(m.netRentYield, 2)}
          accent={m.netRentYield >= 0.045}
        />
        <Mini
          label="Appr 5y"
          value={fmtPct(p.expectedAppreciation, 1)}
          accent={p.expectedAppreciation >= 0.04}
        />
        <Mini
          label="Δ to fair"
          value={fmtSignedPct(m.pricePremium)}
          accent={m.pricePremium < 0}
          negative={m.pricePremium > 0.05}
        />
        <Mini label="DOM est." value={`${p.expectedDom}d`} />
        <Mini label="Tenant fit" value={String(p.tenantFitScore)} />
      </div>
      <div className="text-xs text-muted-foreground mt-4 italic line-clamp-2">
        {m.verdictReasons[0]}
      </div>
    </Link>
  );
}

function Mini({
  label,
  value,
  accent,
  negative,
}: {
  label: string;
  value: string;
  accent?: boolean;
  negative?: boolean;
}) {
  return (
    <div>
      <div className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div
        className={`font-mono text-base mt-0.5 ${accent ? "text-go-strong" : negative ? "text-nogo-strong" : ""}`}
      >
        {value}
      </div>
    </div>
  );
}
