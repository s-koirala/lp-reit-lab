import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";

export const Route = createFileRoute("/methodology")({
  head: () => ({ meta: [{ title: "Methodology — Lincoln Park Property Lab" }] }),
  component: () => (
    <AppShell>
      <header className="rule-b pb-6 mb-8">
        <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted-foreground mb-2">
          Notes on method
        </p>
        <h1 className="text-5xl md:text-6xl max-w-3xl">
          How every estimate on this site is built.
        </h1>
      </header>

      <p className="text-sm text-ink-soft max-w-3xl mb-8">
        Sections 05–06 (the carrying-cost engine and the go/no-go scoring) are live: config-driven
        and parity-gated against the Python engine. Sections 01–04 describe the planned price, rent,
        time-on-market, and appreciation models — currently backed by synthetic placeholders (see
        08) until the real data and fitted models land.
      </p>

      <article className="grid grid-cols-12 gap-10 max-w-none">
        <Section n="01" title="Fair-price model">
          A hedonic regression on assessor &amp; sales data — beds, baths, sf, vintage, condition,
          and submarket fixed effects — produces a fair-price point estimate plus a prediction band
          (an illustrative ±6% on today's synthetic data). It renders as the deal memo's "Predicted
          price vs. list" band.
        </Section>
        <Section n="02" title="Rent model">
          Comparable-rent regression on active and recent leases in the same submarket, scaled by
          bed count, sf, and unit type. Output is a monthly rent point estimate plus an illustrative
          ±8% band on synthetic data.
        </Section>
        <Section n="03" title="Time-on-market">
          Survival model over the trailing 24 months of listings, conditioned on price-to-comp ratio
          and submarket liquidity. Reported as expected DOM in days.
        </Section>
        <Section n="04" title="Appreciation forecast">
          A repeat-sales price index (Case-Shiller style) drives a 5-year CAGR forecast per
          submarket, blended with a structural component from job, transit, and inventory signals.
        </Section>
        <Section n="05" title="Carrying-cost stack">
          A deterministic engine — a parity-gated TypeScript mirror of the Python finance module —
          applies cited, config-driven assumptions: 25% down on a 30-year fixed at 7.0%, property
          tax 1.66% of value, vacancy 5%, and maintenance and management each 8% of effective gross
          income, plus insurance and HOA. NOI is income net of those operating costs (before debt
          service); monthly cash flow then nets the mortgage. Every assumption lives in
          config/assumptions.yaml with a source and is user-adjustable.
        </Section>
        <Section n="06" title="Verdict scoring">
          Screens, not valuation. Four cited go/no-go gates — cash-on-cash, DSCR, cap-rate spread
          over the 10-year Treasury, and break-even occupancy — each map to a traffic light against
          bands in config/scoring.yaml. A weighted composite (cash-on-cash 30%, cap-spread 25%, DSCR
          25%, break-even 20%; green = 1, amber = 0.5, red = 0) yields{" "}
          <strong className="text-go-strong">GO</strong> (≥ 0.75),{" "}
          <strong className="text-watch-strong">WATCH</strong> (≥ 0.50), or{" "}
          <strong className="text-nogo-strong">NO-GO</strong>. Lincoln Park is appreciation-led and
          largely cash-flow-negative, so most candidates screen WATCH/NO-GO as income plays — by
          design. The confidence figure reflects the width of the price &amp; rent prediction bands.
        </Section>
        <Section n="07" title="Tenant-fit, plainly">
          The "market demand for 3BR+ family units" metric measures rent levels, occupancy, and
          time-on-market for that configuration in a submarket. It informs whether the building is
          positioned for resilient cashflow. It is <strong>not</strong> a tenant-screening signal.
          Familial status is a protected class under the Fair Housing Act; this tool will not be
          used to select, steer, or exclude renters, and language across the product is framed
          around market demand for unit configurations and locations, never around tenant selection.
        </Section>
        <Section n="08" title="Demo data">
          All ~50 properties on this site are synthetic and drawn to be representative of Chicago
          North Side price and rent levels. No real listing is referenced.
        </Section>
      </article>
    </AppShell>
  ),
});

function Section({ n, title, children }: { n: string; title: string; children: React.ReactNode }) {
  return (
    <>
      <div className="col-span-12 md:col-span-3 font-mono text-xs uppercase tracking-[0.22em] text-muted-foreground rule-t pt-4">
        {n} · {title}
      </div>
      <div className="col-span-12 md:col-span-9 rule-t pt-4 text-base leading-relaxed text-ink-soft mb-6">
        {children}
      </div>
    </>
  );
}
