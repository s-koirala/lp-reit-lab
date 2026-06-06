import { Area, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { Property } from "@/lib/data/properties";
import { fmtMoney, fmtSignedPct } from "@/lib/format";
import { buildSampleForecast } from "@/lib/forecast/artifact";

// P5 stub: renders a forecast/MC artifact (ForecastArtifact). Today the artifact
// is an illustrative SAMPLE (status "sample") built in-browser from the property's
// appreciation band — NOT a fitted model. When the deferred Python compiler lands
// it emits a "fitted" artifact of the same shape and this component renders it
// unchanged. The "Illustrative sample" badge + disclaimer must stay until then.
export function ForecastPanel({ property }: { property: Property }) {
  const fc = buildSampleForecast(property);
  const data = fc.appreciationPath.map((y) => ({
    year: `Y${y.year}`,
    band: [y.cumReturn.p10 * 100, y.cumReturn.p90 * 100] as [number, number],
    p50: y.cumReturn.p50 * 100,
  }));
  const mc = fc.monteCarlo;

  return (
    <section className="mb-12">
      <div className="mb-1 flex items-end justify-between gap-4">
        <h2 className="text-2xl">5-year outlook</h2>
        <span className="rounded-sm border border-watch/40 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-watch-strong">
          Illustrative sample · not fitted
        </span>
      </div>
      <p className="mb-4 max-w-3xl text-sm text-muted-foreground">{fc.disclaimer}</p>
      <div className="grid grid-cols-12 gap-8">
        <div
          className="rule-t rule-b col-span-12 bg-card p-4 lg:col-span-7"
          style={{ height: 240 }}
        >
          <ResponsiveContainer>
            <ComposedChart data={data} margin={{ left: 0, right: 10, top: 10 }}>
              <XAxis
                dataKey="year"
                tick={{ fontSize: 11, fontFamily: "IBM Plex Mono" }}
                stroke="currentColor"
              />
              <YAxis
                tick={{ fontSize: 11, fontFamily: "IBM Plex Mono" }}
                stroke="currentColor"
                tickFormatter={(v: number) => `${v.toFixed(0)}%`}
              />
              <Tooltip
                contentStyle={{
                  background: "var(--paper)",
                  border: "1px solid var(--rule)",
                  fontSize: 12,
                }}
                formatter={(v: number | number[]) =>
                  Array.isArray(v) ? `${v[0].toFixed(1)}–${v[1].toFixed(1)}%` : `${v.toFixed(1)}%`
                }
              />
              {/* p10–p90 predictive band */}
              <Area dataKey="band" stroke="none" fill="var(--ring)" fillOpacity={0.18} />
              {/* median path */}
              <Line
                dataKey="p50"
                stroke="var(--foreground)"
                strokeWidth={2}
                dot={false}
                type="monotone"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        <div className="col-span-12 lg:col-span-5">
          <div className="rule-t rule-b grid grid-cols-3 gap-px bg-rule tabular">
            <Tile label="5y return p10" value={fmtSignedPct(mc.fiveYearReturn.p10)} />
            <Tile label="5y return p50" value={fmtSignedPct(mc.fiveYearReturn.p50)} />
            <Tile label="5y return p90" value={fmtSignedPct(mc.fiveYearReturn.p90)} />
            <Tile label="Value p10" value={fmtMoney(mc.terminalValue.p10, { compact: true })} />
            <Tile label="Value p50" value={fmtMoney(mc.terminalValue.p50, { compact: true })} />
            <Tile label="Value p90" value={fmtMoney(mc.terminalValue.p90, { compact: true })} />
          </div>
          {/* not-fitted qualifier attached to the tiles themselves, so the numbers
              can't be quoted in isolation as a real Monte-Carlo result */}
          <p className="mt-2 font-mono text-[10px] uppercase tracking-wider text-watch-strong">
            Illustrative sample — no Monte-Carlo run; bands compound the appreciation estimate.
          </p>
        </div>
      </div>
    </section>
  );
}

function Tile({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-card p-4">
      <div className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 font-mono text-base">{value}</div>
    </div>
  );
}
