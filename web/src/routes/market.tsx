import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { NEIGHBORHOODS } from "@/lib/data/neighborhoods";
import { PRICE_INDEX, RENT_INDEX, LIQUIDITY } from "@/lib/data/market";
import { fmtPct } from "@/lib/format";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend } from "recharts";

export const Route = createFileRoute("/market")({
  head: () => ({ meta: [{ title: "Market — Lincoln Park Property Lab" }] }),
  component: Market,
});

const PALETTE = [
  "oklch(0.18 0.025 250)",
  "oklch(0.55 0.12 220)",
  "oklch(0.52 0.13 155)",
  "oklch(0.72 0.13 80)",
  "oklch(0.55 0.2 22)",
  "oklch(0.45 0.05 280)",
];

function mergeSeries(input: typeof PRICE_INDEX) {
  const dates = input[0].series.map((s) => s.date);
  return dates.map((date, i) => {
    const row: any = { date };
    input.forEach((s) => { row[s.slug] = s.series[i].value; });
    return row;
  });
}

function Market() {
  const priceMerged = mergeSeries(PRICE_INDEX);
  const rentMerged = mergeSeries(RENT_INDEX);
  const liqDates = LIQUIDITY[0].series.map((s) => s.date);
  const liqMerged = liqDates.map((date, i) => {
    const row: any = { date };
    LIQUIDITY.forEach((s) => { row[s.slug] = s.series[i].dom; });
    return row;
  });

  return (
    <AppShell>
      <header className="rule-b pb-6 mb-8">
        <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted-foreground mb-2">Longitudinal market view</p>
        <h1 className="text-5xl md:text-6xl">A decade of North Side prices, rents, and liquidity.</h1>
        <p className="mt-4 text-base text-ink-soft max-w-3xl">
          Repeat-sales price indices and 3BR equivalent rent indices for each submarket, plus a
          rolling view of days-on-market. Useful for sanity-checking the model's appreciation
          forecasts against realized history.
        </p>
      </header>

      <ChartBlock title="Repeat-sales price index" subtitle="Jan 2015 = 100. All six submarkets, monthly.">
        <ResponsiveContainer>
          <LineChart data={priceMerged}>
            <CartesianGrid stroke="var(--rule)" vertical={false} />
            <XAxis dataKey="date" tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} stroke="currentColor" tickFormatter={(v: string) => v.slice(0, 4)} interval={11} />
            <YAxis tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} stroke="currentColor" domain={["dataMin - 5", "dataMax + 5"]} />
            <Tooltip contentStyle={{ background: "var(--paper)", border: "1px solid var(--rule)", fontSize: 11 }} />
            <Legend wrapperStyle={{ fontSize: 11, fontFamily: "IBM Plex Mono", textTransform: "uppercase", letterSpacing: "0.1em" }} />
            {NEIGHBORHOODS.map((n, i) => (
              <Line key={n.slug} dataKey={n.slug} name={n.name} stroke={PALETTE[i]} strokeWidth={1.5} dot={false} type="monotone" />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </ChartBlock>

      <ChartBlock title="Rent index (3BR equivalent)" subtitle="Jan 2015 = 100.">
        <ResponsiveContainer>
          <LineChart data={rentMerged}>
            <CartesianGrid stroke="var(--rule)" vertical={false} />
            <XAxis dataKey="date" tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} stroke="currentColor" tickFormatter={(v: string) => v.slice(0, 4)} interval={11} />
            <YAxis tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} stroke="currentColor" domain={["dataMin - 5", "dataMax + 5"]} />
            <Tooltip contentStyle={{ background: "var(--paper)", border: "1px solid var(--rule)", fontSize: 11 }} />
            <Legend wrapperStyle={{ fontSize: 11, fontFamily: "IBM Plex Mono", textTransform: "uppercase", letterSpacing: "0.1em" }} />
            {NEIGHBORHOODS.map((n, i) => (
              <Line key={n.slug} dataKey={n.slug} name={n.name} stroke={PALETTE[i]} strokeWidth={1.5} dot={false} type="monotone" />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </ChartBlock>

      <ChartBlock title="Market liquidity — median days on market" subtitle="36 months trailing. Lower = faster turnover.">
        <ResponsiveContainer>
          <LineChart data={liqMerged}>
            <CartesianGrid stroke="var(--rule)" vertical={false} />
            <XAxis dataKey="date" tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} stroke="currentColor" tickFormatter={(v: string) => v.slice(2, 7)} interval={3} />
            <YAxis tick={{ fontSize: 10, fontFamily: "IBM Plex Mono" }} stroke="currentColor" />
            <Tooltip contentStyle={{ background: "var(--paper)", border: "1px solid var(--rule)", fontSize: 11 }} />
            <Legend wrapperStyle={{ fontSize: 11, fontFamily: "IBM Plex Mono", textTransform: "uppercase", letterSpacing: "0.1em" }} />
            {NEIGHBORHOODS.map((n, i) => (
              <Line key={n.slug} dataKey={n.slug} name={n.name} stroke={PALETTE[i]} strokeWidth={1.5} dot={false} type="monotone" />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </ChartBlock>

      <section className="grid grid-cols-2 md:grid-cols-6 gap-px bg-rule rule-t rule-b mt-12">
        {NEIGHBORHOODS.map((n) => (
          <div key={n.slug} className="bg-card p-4">
            <div className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">{n.name}</div>
            <div className="font-mono text-base mt-2">5y: {fmtPct(n.appreciation5y, 1)}</div>
            <div className="font-mono text-xs text-muted-foreground">1y: {fmtPct(n.appreciation1y, 1)}</div>
            <div className="font-mono text-xs text-muted-foreground mt-1">{n.domMedian}d DOM</div>
          </div>
        ))}
      </section>
    </AppShell>
  );
}

function ChartBlock({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <section className="mb-10">
      <h2 className="text-2xl mb-1">{title}</h2>
      <p className="text-sm text-muted-foreground mb-4">{subtitle}</p>
      <div className="bg-card rule-t rule-b p-4" style={{ height: 340 }}>{children}</div>
    </section>
  );
}
