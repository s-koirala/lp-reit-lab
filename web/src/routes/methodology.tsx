import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";

export const Route = createFileRoute("/methodology")({
  head: () => ({ meta: [{ title: "Methodology — Lincoln Park Property Lab" }] }),
  component: () => (
    <AppShell>
      <header className="rule-b pb-6 mb-8">
        <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted-foreground mb-2">Notes on method</p>
        <h1 className="text-5xl md:text-6xl max-w-3xl">How every estimate on this site is built.</h1>
      </header>

      <article className="grid grid-cols-12 gap-10 max-w-none">
        <Section n="01" title="Fair-price model">
          A hedonic regression on assessor &amp; sales data — beds, baths, sf, vintage, condition,
          and submarket fixed effects — produces a fair-price point estimate plus a 90% prediction
          interval. The interval is what you see in the deal memo's "Predicted price vs. list" band.
        </Section>
        <Section n="02" title="Rent model">
          Comparable-rent regression on active and recent leases in the same submarket, scaled by
          bed count, sf, and unit type. Output is a monthly rent point estimate plus an 80% band.
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
          Default financing: 25% down, 30-year amortization, 6.85% rate. Maintenance reserve is 0.8%
          of price/yr; vacancy 6% of gross rent; management 8%. Tax &amp; insurance pulled from the
          listing facts. All adjustable in a future iteration.
        </Section>
        <Section n="06" title="Verdict scoring">
          Properties earn points for: list price ≥3% below model fair price (+2), net yield ≥4.5%
          (+2), forecast appreciation ≥4%/yr (+1), strong submarket demand for 3BR+ family units
          (+1). They lose points for premium pricing, weak yields, slow liquidity, and large
          negative cashflow. Score ≥3 → <strong className="text-go">GO</strong>; score ≤−2 →{" "}
          <strong className="text-nogo">NO-GO</strong>; otherwise{" "}
          <strong className="text-watch">WATCH</strong>. The confidence figure reflects the width
          of the underlying price &amp; rent prediction bands.
        </Section>
        <Section n="07" title="Tenant-fit, plainly">
          The "market demand for 3BR+ family units" metric measures rent levels, occupancy, and
          time-on-market for that configuration in a submarket. It informs whether the building
          is positioned for resilient cashflow. It is <strong>not</strong> a tenant-screening
          signal. Familial status is a protected class under the Fair Housing Act; this tool will
          not be used to select, steer, or exclude renters, and language across the product is
          framed around market demand for unit configurations and locations, never around
          tenant selection.
        </Section>
        <Section n="08" title="Demo data">
          All ~50 properties on this site are synthetic and drawn to be representative of
          Chicago North Side price and rent levels. No real listing is referenced.
        </Section>
      </article>
    </AppShell>
  ),
});

function Section({ n, title, children }: { n: string; title: string; children: React.ReactNode }) {
  return (
    <>
      <div className="col-span-12 md:col-span-3 font-mono text-xs uppercase tracking-[0.22em] text-muted-foreground rule-t pt-4">{n} · {title}</div>
      <div className="col-span-12 md:col-span-9 rule-t pt-4 text-base leading-relaxed text-ink-soft mb-6">{children}</div>
    </>
  );
}
