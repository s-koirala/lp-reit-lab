import { createFileRoute, Link, notFound } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { VerdictBadge } from "@/components/VerdictBadge";
import { getNeighborhood, NEIGHBORHOODS } from "@/lib/data/neighborhoods";
import { PROPERTIES, computeMetrics } from "@/lib/data/properties";
import { PRICE_INDEX, RENT_INDEX, LIQUIDITY } from "@/lib/data/market";
import { fmtMoney, fmtPct } from "@/lib/format";
import { Area, AreaChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export const Route = createFileRoute("/neighborhoods/$slug")({
  loader: ({ params }) => {
    const n = getNeighborhood(params.slug);
    if (!n) throw notFound();
    return { n };
  },
  head: ({ loaderData }) => ({
    meta: loaderData ? [{ title: `${loaderData.n.name} — Submarket Profile` }] : [{ title: "Submarket" }],
  }),
  errorComponent: ({ error }) => <AppShell><p className="py-20 text-center">Could not load: {error.message}</p></AppShell>,
  notFoundComponent: () => <AppShell><p className="py-20 text-center">Submarket not found.</p></AppShell>,
  component: NeighborhoodPage,
});

function NeighborhoodPage() {
  const { n } = Route.useLoaderData();
  const listings = PROPERTIES.filter((p) => p.neighborhoodSlug === n.slug)
    .map((p) => ({ p, m: computeMetrics(p) }))
    .sort((a, b) => b.m.netRentYield - a.m.netRentYield);

  const price = PRICE_INDEX.find((s) => s.slug === n.slug)!.series;
  const rent = RENT_INDEX.find((s) => s.slug === n.slug)!.series;
  const liq = LIQUIDITY.find((s) => s.slug === n.slug)!.series;

  return (
    <AppShell>
      <div className="mb-3 text-xs font-mono uppercase tracking-[0.22em] text-muted-foreground flex gap-3 items-center">
        <Link to="/neighborhoods" className="hover:text-foreground">Submarkets</Link>
        <span>/</span>
        <span className="text-foreground">{n.name}</span>
      </div>

      <header className="rule-b pb-8 mb-8">
        <h1 className="text-6xl">{n.name}</h1>
        <p className="mt-4 text-base max-w-3xl text-ink-soft">{n.blurb}</p>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-px bg-rule rule-t rule-b mt-6">
          <Cell label="Median price" value={fmtMoney(n.medianPrice, { compact: true })} />
          <Cell label="Median 3BR rent" value={`$${n.medianRent3br.toLocaleString()}`} />
          <Cell label="Net yield (med)" value={fmtPct(n.yieldMedian, 1)} />
          <Cell label="5y appreciation" value={fmtPct(n.appreciation5y, 1)} />
          <Cell label="Median DOM" value={`${n.domMedian}d`} />
          <Cell label="Active inventory" value={String(n.inventory)} />
        </div>
      </header>

      <section className="grid grid-cols-12 gap-8 mb-12">
        <div className="col-span-12 lg:col-span-8">
          <h2 className="text-2xl mb-1">Repeat-sales price index</h2>
          <p className="text-sm text-muted-foreground mb-4">Jan 2015 = 100. Band reflects ±1.8% measurement noise.</p>
          <div className="bg-card rule-t rule-b p-4" style={{ height: 280 }}>
            <ResponsiveContainer>
              <AreaChart data={price} margin={{ left: 0, right: 10, top: 10 }}>
                <defs>
                  <linearGradient id="pi" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.55 0.12 220)" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="oklch(0.55 0.12 220)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="var(--rule)" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} stroke="currentColor"
                  tickFormatter={(v: string) => v.slice(0, 4)} interval={11} />
                <YAxis tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} stroke="currentColor" domain={["dataMin - 5", "dataMax + 5"]} />
                <Tooltip contentStyle={{ background: "var(--paper)", border: "1px solid var(--rule)", fontSize: 12 }} />
                <Area dataKey="upper" stroke="none" fill="url(#pi)" />
                <Area dataKey="lower" stroke="none" fill="var(--paper)" />
                <Line dataKey="value" stroke="oklch(0.18 0.025 250)" strokeWidth={2} dot={false} type="monotone" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="col-span-12 lg:col-span-4">
          <h2 className="text-2xl mb-1">Market liquidity</h2>
          <p className="text-sm text-muted-foreground mb-4">Median days-on-market, last 36 months.</p>
          <div className="bg-card rule-t rule-b p-4" style={{ height: 280 }}>
            <ResponsiveContainer>
              <LineChart data={liq}>
                <CartesianGrid stroke="var(--rule)" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} stroke="currentColor" tickFormatter={(v: string) => v.slice(2, 7)} interval={5} />
                <YAxis tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} stroke="currentColor" />
                <Tooltip contentStyle={{ background: "var(--paper)", border: "1px solid var(--rule)", fontSize: 12 }} />
                <Line dataKey="dom" stroke="oklch(0.55 0.2 22)" strokeWidth={2} dot={false} type="monotone" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="col-span-12">
          <h2 className="text-2xl mb-1">Rent index</h2>
          <p className="text-sm text-muted-foreground mb-4">3BR equivalent rents, Jan 2015 = 100.</p>
          <div className="bg-card rule-t rule-b p-4" style={{ height: 220 }}>
            <ResponsiveContainer>
              <LineChart data={rent}>
                <CartesianGrid stroke="var(--rule)" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} stroke="currentColor" tickFormatter={(v: string) => v.slice(0, 4)} interval={11} />
                <YAxis tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} stroke="currentColor" domain={["dataMin - 5", "dataMax + 5"]} />
                <Tooltip contentStyle={{ background: "var(--paper)", border: "1px solid var(--rule)", fontSize: 12 }} />
                <Line dataKey="value" stroke="oklch(0.52 0.13 155)" strokeWidth={2} dot={false} type="monotone" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl mb-4">Candidate listings in {n.name}</h2>
        <div className="overflow-x-auto rule-t rule-b">
          <table className="w-full text-sm tabular">
            <thead>
              <tr className="text-left text-[10px] font-mono uppercase tracking-wider text-muted-foreground rule-b">
                <th className="px-3 py-3">Verdict</th>
                <th className="px-3 py-3">Address</th>
                <th className="px-3 py-3 text-right">Beds</th>
                <th className="px-3 py-3 text-right">List</th>
                <th className="px-3 py-3 text-right">Net yld</th>
                <th className="px-3 py-3 text-right">5y appr</th>
              </tr>
            </thead>
            <tbody>
              {listings.map(({ p, m }) => (
                <tr key={p.id} className="rule-b hover:bg-secondary/60">
                  <td className="px-3 py-3"><VerdictBadge verdict={m.verdict} size="sm" /></td>
                  <td className="px-3 py-3"><Link to="/property/$id" params={{ id: p.id }} className="hover:underline underline-offset-4">{p.address}</Link></td>
                  <td className="px-3 py-3 text-right font-mono">{p.beds}/{p.baths}</td>
                  <td className="px-3 py-3 text-right font-mono">{fmtMoney(p.listPrice, { compact: true })}</td>
                  <td className="px-3 py-3 text-right font-mono">{fmtPct(m.netRentYield, 2)}</td>
                  <td className="px-3 py-3 text-right font-mono">{fmtPct(p.expectedAppreciation, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="rule-t pt-6 text-xs text-muted-foreground flex justify-between">
        <Link to="/neighborhoods" className="font-mono uppercase tracking-wider hover:text-foreground">← All submarkets</Link>
        <span>Context: {NEIGHBORHOODS.length} North Side submarkets indexed.</span>
      </div>
    </AppShell>
  );
}

function Cell({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-card p-4">
      <div className="text-[9px] font-mono uppercase tracking-[0.22em] text-muted-foreground">{label}</div>
      <div className="font-mono text-lg mt-1">{value}</div>
    </div>
  );
}
