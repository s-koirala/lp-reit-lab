import { lazy, Suspense, useEffect, useState } from "react";

import { EmptyState } from "@/components/ProvenanceNote";
import { PROPERTIES } from "@/lib/data/properties";

// Leaflet only runs in the browser; lazy + a mount gate keep it out of SSR.
const PropertyMapInner = lazy(() => import("./PropertyMapInner"));

const MAP_HEIGHT = 480;

export function PropertyMap({
  highlightId,
  filterIds,
}: {
  highlightId?: string;
  filterIds?: Set<string>;
}) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const props = filterIds ? PROPERTIES.filter((p) => filterIds.has(p.id)) : PROPERTIES;

  return (
    <div className="rule-t rule-b overflow-hidden bg-card">
      {!mounted ? (
        <MapPlaceholder />
      ) : props.length === 0 ? (
        <div style={{ height: MAP_HEIGHT }}>
          <EmptyState label="No candidates to map." />
        </div>
      ) : (
        <Suspense fallback={<MapPlaceholder />}>
          <PropertyMapInner props={props} highlightId={highlightId} />
        </Suspense>
      )}
      <div className="rule-t flex items-center gap-5 bg-background px-4 py-2 text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
        <LegendDot token="bg-go" label="Go" />
        <LegendDot token="bg-watch" label="Watch" />
        <LegendDot token="bg-nogo" label="No-go" />
        <span className="ml-auto">
          {props.length} candidate {props.length === 1 ? "property" : "properties"}
        </span>
      </div>
    </div>
  );
}

function MapPlaceholder() {
  return (
    <div
      style={{ height: MAP_HEIGHT }}
      className="flex items-center justify-center text-xs text-muted-foreground"
      aria-busy
    >
      Loading map…
    </div>
  );
}

function LegendDot({ token, label }: { token: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className={`h-2 w-2 rounded-full ${token}`} />
      {label}
    </span>
  );
}
