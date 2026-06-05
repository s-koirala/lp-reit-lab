import { Link } from "@tanstack/react-router";
import { NEIGHBORHOODS } from "@/lib/data/neighborhoods";
import { PROPERTIES, computeMetrics } from "@/lib/data/properties";

const W = 1000, H = 800;

export function PropertyMap({
  highlightId,
  filterIds,
}: {
  highlightId?: string;
  filterIds?: Set<string>;
}) {
  const props = filterIds ? PROPERTIES.filter((p) => filterIds.has(p.id)) : PROPERTIES;

  return (
    <div className="rule-t rule-b bg-card overflow-hidden">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto block">
        {/* Lake Michigan suggestion */}
        <rect x={750} y={0} width={250} height={H} fill="oklch(0.85 0.04 220)" opacity={0.35} />
        <text x={870} y={120} className="font-display" fontSize={32} fill="oklch(0.45 0.08 220)" opacity={0.6}>
          Lake Michigan
        </text>

        {/* River suggestion */}
        <path d="M 90 0 Q 140 200 100 400 T 180 800" stroke="oklch(0.8 0.05 220)" strokeWidth={18} fill="none" opacity={0.5} />

        {/* CTA Red line */}
        <line x1={400} y1={0} x2={420} y2={H} stroke="oklch(0.55 0.2 22)" strokeWidth={2} strokeDasharray="6 6" opacity={0.45} />
        <text x={406} y={780} fontSize={10} fill="oklch(0.55 0.2 22)" className="font-mono uppercase tracking-wider">CTA Red</text>

        {/* Neighborhood polygons */}
        {NEIGHBORHOODS.map((n) => (
          <g key={n.slug}>
            <polygon
              points={n.polygon.map((p) => p.join(",")).join(" ")}
              fill="oklch(0.92 0.02 80)"
              stroke="oklch(0.45 0.05 80)"
              strokeWidth={1.2}
              opacity={0.55}
            />
            <text
              x={n.centroid[0]}
              y={n.centroid[1] - 8}
              textAnchor="middle"
              className="font-display"
              fontSize={22}
              fill="oklch(0.25 0.03 250)"
            >
              {n.name}
            </text>
            <text
              x={n.centroid[0]}
              y={n.centroid[1] + 12}
              textAnchor="middle"
              fontSize={10}
              fill="oklch(0.4 0.02 250)"
              className="font-mono uppercase tracking-wider"
            >
              ${(n.medianPrice/1000).toFixed(0)}k · {(n.yieldMedian*100).toFixed(1)}% yld
            </text>
          </g>
        ))}

        {/* Properties */}
        {props.map((p) => {
          const m = computeMetrics(p);
          const color =
            m.verdict === "go" ? "oklch(0.52 0.13 155)" :
            m.verdict === "watch" ? "oklch(0.72 0.15 75)" :
            "oklch(0.55 0.2 22)";
          const r = highlightId === p.id ? 14 : 7;
          return (
            <Link key={p.id} to="/property/$id" params={{ id: p.id }}>
              <g className="cursor-pointer hover:opacity-100" opacity={0.9}>
                <circle cx={p.x} cy={p.y} r={r} fill={color} stroke="oklch(0.18 0.025 250)" strokeWidth={1} />
                {highlightId === p.id && (
                  <circle cx={p.x} cy={p.y} r={r + 8} fill="none" stroke={color} strokeWidth={2} opacity={0.5} />
                )}
              </g>
            </Link>
          );
        })}
      </svg>
      <div className="rule-t px-4 py-2 flex items-center gap-5 text-[11px] font-mono uppercase tracking-wider text-muted-foreground bg-background">
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-go" /> Go</span>
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-watch" /> Watch</span>
        <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-nogo" /> No-go</span>
        <span className="ml-auto">{props.length} candidate {props.length === 1 ? "property" : "properties"}</span>
      </div>
    </div>
  );
}
