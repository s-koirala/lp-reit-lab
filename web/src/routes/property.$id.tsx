import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { VerdictBadge } from "@/components/VerdictBadge";
import { PropertyMap } from "@/components/PropertyMap";
import { ForecastPanel } from "@/components/ForecastPanel";
import { computeMetrics, getProperty, DEFAULT_FINANCING } from "@/lib/data/properties";
import { getNeighborhood } from "@/lib/data/neighborhoods";
import { fmtMoney, fmtPct, fmtSignedPct } from "@/lib/format";
import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  XAxis,
  YAxis,
  ReferenceLine,
  Tooltip,
} from "recharts";

export const Route = createFileRoute("/property/$id")({
  loader: ({ params }) => {
    const p = getProperty(params.id);
    if (!p) throw notFound();
    return { property: p };
  },
  head: ({ loaderData }) => ({
    meta: loaderData
      ? [
          { title: `${loaderData.property.address} — Deal Memo` },
          {
            name: "description",
            content: `Investment analysis for ${loaderData.property.address}. Verdict, carrying-cost stack, and model confidence.`,
          },
        ]
      : [{ title: "Deal Memo" }],
  }),
  errorComponent: ({ error }) => (
    <AppShell>
      <p className="py-20 text-center">Could not load: {error.message}</p>
    </AppShell>
  ),
  notFoundComponent: () => (
    <AppShell>
      <div className="py-24 text-center">
        <h1 className="font-display text-5xl">Property not found</h1>
        <Link
          to="/"
          className="mt-6 inline-block font-mono text-xs uppercase tracking-wider rule-b border-foreground pb-1"
        >
          Back to screener
        </Link>
      </div>
    </AppShell>
  ),
  component: DealMemo,
});

function DealMemo() {
  const { property: p } = Route.useLoaderData();
  const m = computeMetrics(p);
  const neigh = getNeighborhood(p.neighborhoodSlug)!;

  const stack = [
    { name: "Mortgage P&I", v: m.carry.mortgage },
    { name: "Property tax", v: m.carry.tax },
    { name: "Insurance", v: m.carry.insurance },
    { name: "HOA / assessments", v: m.carry.hoa },
    { name: "Maintenance reserve", v: m.carry.maintenance },
    { name: "Vacancy allowance", v: m.carry.vacancy },
    { name: "Management", v: m.carry.management },
  ];

  const priceCompare = [
    {
      name: "Model fair",
      value: p.predictedPrice,
      low: p.predictedPriceLow,
      high: p.predictedPriceHigh,
    },
    { name: "List", value: p.listPrice, low: p.listPrice, high: p.listPrice },
  ];

  const rentCompare = [
    {
      name: "Model rent",
      value: p.predictedRent,
      low: p.predictedRentLow,
      high: p.predictedRentHigh,
    },
  ];

  return (
    <AppShell>
      <div className="mb-3 text-xs font-mono uppercase tracking-[0.22em] text-muted-foreground flex gap-3 items-center">
        <Link to="/" className="hover:text-foreground">
          Screener
        </Link>
        <span>/</span>
        <Link
          to="/neighborhoods/$slug"
          params={{ slug: neigh.slug }}
          className="hover:text-foreground"
        >
          {neigh.name}
        </Link>
        <span>/</span>
        <span className="text-foreground">{p.id}</span>
      </div>

      {/* Headline */}
      <header className="rule-b pb-8 mb-8 grid grid-cols-12 gap-6 items-end">
        <div className="col-span-12 lg:col-span-8">
          <h1 className="text-5xl md:text-6xl leading-[0.95]">{p.address}</h1>
          <p className="mt-3 text-base text-ink-soft">
            {p.beds} bed · {p.baths} bath · {p.sqft.toLocaleString()} sf · {p.type} · built{" "}
            {p.yearBuilt} · {neigh.name}
          </p>
        </div>
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-3 items-start lg:items-end">
          <VerdictBadge verdict={m.verdict} confidence={m.verdictConfidence} size="lg" />
          <p className="text-xs text-muted-foreground max-w-xs lg:text-right">
            Confidence reflects the tightness of model prediction bands for price &amp; rent.
          </p>
        </div>
      </header>

      {/* Why this verdict */}
      <section className="grid grid-cols-12 gap-6 mb-10">
        <div className="col-span-12 lg:col-span-4 bg-card p-6 rule-t rule-b">
          <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-muted-foreground mb-3">
            Verdict rationale
          </div>
          <ul className="space-y-3">
            {m.verdictReasons.map((r, i) => (
              <li key={i} className="text-sm flex gap-3">
                <span className="font-mono text-xs text-muted-foreground mt-0.5">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="col-span-12 lg:col-span-8 grid grid-cols-2 md:grid-cols-4 gap-px bg-rule rule-t rule-b">
          <BigStat
            label="Going-in cap rate"
            value={fmtPct(m.capRate, 2)}
            sub="NOI ÷ price (pre-debt)"
          />
          <BigStat
            label="Expected appreciation"
            value={fmtPct(p.expectedAppreciation, 1)}
            sub={`Band ${fmtPct(p.expectedAppreciationLow, 1)}–${fmtPct(p.expectedAppreciationHigh, 1)}`}
          />
          <BigStat
            label="Price vs. model"
            value={fmtSignedPct(m.pricePremium)}
            sub={m.pricePremium < 0 ? "Discount to fair value" : "Premium to fair value"}
            accent={m.pricePremium < 0 ? "go" : m.pricePremium > 0.05 ? "nogo" : undefined}
          />
          <BigStat
            label="Cash-on-cash"
            value={fmtPct(m.cashOnCash, 2)}
            sub={`Monthly CF ${fmtMoney(m.monthlyCashflow, { decimals: 0 })}`}
            accent={m.monthlyCashflow >= 0 ? "go" : "nogo"}
          />
        </div>
      </section>

      {/* Predicted vs list */}
      <section className="grid grid-cols-12 gap-8 mb-12">
        <div className="col-span-12 lg:col-span-7">
          <h2 className="text-2xl mb-1">Predicted price vs. list</h2>
          <p className="text-sm text-muted-foreground mb-4">
            The hedonic model produces a fair-price band from beds, baths, square footage, vintage,
            and submarket comps.
          </p>
          <div className="bg-card rule-t rule-b p-4" style={{ height: 220 }}>
            <ResponsiveContainer>
              <BarChart layout="vertical" data={priceCompare} margin={{ left: 60, right: 40 }}>
                <XAxis
                  type="number"
                  domain={[
                    Math.min(p.predictedPriceLow, p.listPrice) * 0.96,
                    Math.max(p.predictedPriceHigh, p.listPrice) * 1.04,
                  ]}
                  tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                  tick={{ fontSize: 11, fontFamily: "IBM Plex Mono" }}
                  stroke="currentColor"
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 12 }}
                  stroke="currentColor"
                />
                <Tooltip
                  formatter={(v: number) => fmtMoney(v)}
                  contentStyle={{
                    background: "var(--paper)",
                    border: "1px solid var(--rule)",
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="value" barSize={28}>
                  {priceCompare.map((d, i) => (
                    <Cell key={i} fill={i === 0 ? "oklch(0.55 0.12 220)" : "var(--foreground)"} />
                  ))}
                </Bar>
                <ReferenceLine
                  x={p.predictedPriceLow}
                  stroke="oklch(0.55 0.12 220)"
                  strokeDasharray="3 3"
                />
                <ReferenceLine
                  x={p.predictedPriceHigh}
                  stroke="oklch(0.55 0.12 220)"
                  strokeDasharray="3 3"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-2 text-xs font-mono text-muted-foreground flex justify-between">
            <span>
              Fair: {fmtMoney(p.predictedPriceLow)} – {fmtMoney(p.predictedPriceHigh)}
            </span>
            <span>List: {fmtMoney(p.listPrice)}</span>
          </div>
        </div>
        <div className="col-span-12 lg:col-span-5">
          <h2 className="text-2xl mb-1">Predicted rent</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Comparable units in {neigh.name} with similar bed count and sf.
          </p>
          <div className="bg-card rule-t rule-b p-6 tabular">
            <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-muted-foreground">
              Monthly market rent
            </div>
            <div className="font-display text-5xl mt-2 leading-none">
              {fmtMoney(p.predictedRent)}
            </div>
            <div className="text-sm text-muted-foreground mt-2">
              90% band {fmtMoney(p.predictedRentLow)} – {fmtMoney(p.predictedRentHigh)}
            </div>
            <div className="rule-t mt-5 pt-4 grid grid-cols-2 gap-4">
              <div>
                <div className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
                  Expected time on market
                </div>
                <div className="font-mono text-xl mt-1">{p.expectedDom} days</div>
              </div>
              <div>
                <div className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
                  Tenant-fit score
                </div>
                <div className="font-mono text-xl mt-1">{p.tenantFitScore}/100</div>
                <div className="text-[10px] text-muted-foreground mt-1">
                  Market demand for 3BR+ family units
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Carrying-cost stack */}
      <section className="grid grid-cols-12 gap-8 mb-12">
        <div className="col-span-12 lg:col-span-7">
          <h2 className="text-2xl mb-1">Carrying-cost stack</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Monthly burden assuming {fmtPct(DEFAULT_FINANCING.downPct, 0)} down at{" "}
            {DEFAULT_FINANCING.ratePct}% over {DEFAULT_FINANCING.termYears}y.
          </p>
          <div className="bg-card rule-t rule-b">
            <table className="w-full text-sm tabular">
              <tbody>
                {stack.map((row) => (
                  <tr key={row.name} className="rule-b last:border-0">
                    <td className="px-4 py-2.5 text-ink-soft">{row.name}</td>
                    <td className="px-4 py-2.5 text-right font-mono">{fmtMoney(row.v)}</td>
                    <td className="px-4 py-2.5 w-1/2">
                      <div className="h-1.5 bg-secondary">
                        <div
                          className="h-full bg-foreground"
                          style={{ width: `${(row.v / m.carry.total) * 100}%` }}
                        />
                      </div>
                    </td>
                    <td className="px-4 py-2.5 text-right text-xs font-mono text-muted-foreground">
                      {((row.v / m.carry.total) * 100).toFixed(0)}%
                    </td>
                  </tr>
                ))}
                <tr className="bg-secondary/60">
                  <td className="px-4 py-3 font-medium">Total monthly carry</td>
                  <td className="px-4 py-3 text-right font-mono font-medium">
                    {fmtMoney(m.carry.total)}
                  </td>
                  <td colSpan={2} className="px-4 py-3 text-right text-sm">
                    Rent {fmtMoney(p.predictedRent)} · CF{" "}
                    <span
                      className={m.monthlyCashflow >= 0 ? "text-go-strong" : "text-nogo-strong"}
                    >
                      {fmtMoney(m.monthlyCashflow)}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div className="col-span-12 lg:col-span-5">
          <h2 className="text-2xl mb-1">Listing facts</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Source: assessor &amp; MLS (synthetic for demo).
          </p>
          <div className="bg-card rule-t rule-b p-5 text-sm tabular">
            <Fact k="Listing ID" v={p.id} />
            <Fact k="List price" v={fmtMoney(p.listPrice)} />
            <Fact k="Assessed value" v={fmtMoney(p.assessedValue)} />
            <Fact k="Annual property tax" v={fmtMoney(p.propertyTaxAnnual)} />
            <Fact k="Annual insurance" v={fmtMoney(p.insuranceAnnual)} />
            <Fact k="HOA / assessments" v={p.hoa ? `${fmtMoney(p.hoa)}/mo` : "None"} />
            <Fact k="Year built" v={String(p.yearBuilt)} />
            <Fact
              k="Configuration"
              v={`${p.beds}BR / ${p.baths}BA / ${p.sqft.toLocaleString()} sf`}
            />
            <Fact k="Submarket" v={neigh.name} />
            <Fact
              k="Transit / school / amenity"
              v={`${neigh.transitScore} · ${neigh.schoolScore} · ${neigh.amenityScore}`}
              last
            />
          </div>
        </div>
      </section>

      {/* 5-year forecast (P5 stub: illustrative sample artifact) */}
      <ForecastPanel property={p} />

      {/* Location */}
      <section className="mb-8">
        <h2 className="text-2xl mb-1">Location context</h2>
        <p className="text-sm text-muted-foreground mb-4">{neigh.blurb}</p>
        <PropertyMap highlightId={p.id} />
      </section>

      <p className="text-xs text-muted-foreground mt-10 italic max-w-3xl">
        Tenant-fit reflects measurable market demand for 3BR+ family unit configurations in this
        submarket (rent, occupancy, time-on-market). It is not a tenant-screening signal. Familial
        status is a protected class under the Fair Housing Act; this tool will not be used to select
        or exclude renters.
      </p>
    </AppShell>
  );
}

function BigStat({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: "go" | "nogo";
}) {
  return (
    <div className="bg-card p-5">
      <div className="text-[10px] font-mono uppercase tracking-[0.22em] text-muted-foreground">
        {label}
      </div>
      <div
        className={`font-display text-4xl mt-2 leading-none ${accent === "go" ? "text-go-strong" : accent === "nogo" ? "text-nogo-strong" : ""}`}
      >
        {value}
      </div>
      {sub && <div className="text-xs text-muted-foreground mt-2 font-mono">{sub}</div>}
    </div>
  );
}

function Fact({ k, v, last }: { k: string; v: string; last?: boolean }) {
  return (
    <div className={`flex justify-between py-2 ${last ? "" : "rule-b"}`}>
      <span className="text-muted-foreground">{k}</span>
      <span className="font-mono">{v}</span>
    </div>
  );
}
