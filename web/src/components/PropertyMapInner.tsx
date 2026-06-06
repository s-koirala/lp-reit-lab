import { Link } from "@tanstack/react-router";
import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";

import { useTheme } from "@/hooks/use-theme";
import { NEIGHBORHOODS } from "@/lib/data/neighborhoods";
import { computeMetrics, type Property } from "@/lib/data/properties";
import { fmtMoney, fmtPct } from "@/lib/format";

// Lazy-loaded by PropertyMap.tsx (client-only) so Leaflet's window access never
// runs during SSR. CARTO basemap (free OSM tiles, no Mapbox lock-in per ADR-0002).
const NORTH_SIDE_CENTER: [number, number] = [41.927, -87.65];
const MAP_HEIGHT = 480;

// CARTO Positron / Dark Matter — switched live with the theme.
const TILE_LIGHT = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";
const TILE_DARK = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

export default function PropertyMapInner({
  props,
  highlightId,
}: {
  props: Property[];
  highlightId?: string;
}) {
  // Re-render on dark-toggle so the tiles AND the token-derived marker colours
  // both track the active theme (they are read from the live CSS custom props).
  const theme = useTheme();
  const cs = getComputedStyle(document.documentElement);
  const tok = (v: string) => cs.getPropertyValue(v).trim();
  const verdictColor: Record<string, string> = {
    go: tok("--go"),
    watch: tok("--watch"),
    "no-go": tok("--nogo"),
  };
  const tileUrl = theme === "dark" ? TILE_DARK : TILE_LIGHT;

  return (
    <MapContainer
      center={NORTH_SIDE_CENTER}
      zoom={13}
      scrollWheelZoom={false}
      style={{ height: MAP_HEIGHT }}
    >
      {/* key on theme so react-leaflet swaps the basemap when it changes */}
      <TileLayer key={theme} url={tileUrl} attribution={TILE_ATTRIBUTION} />
      {NEIGHBORHOODS.map((n) => (
        <CircleMarker
          key={n.slug}
          center={[n.lat, n.lng]}
          radius={4}
          pathOptions={{ color: tok("--muted-foreground"), weight: 1, fillOpacity: 0.3 }}
        >
          <Tooltip direction="top">
            {n.name} · {fmtMoney(n.medianPrice, { compact: true })} median ·{" "}
            {fmtPct(n.yieldMedian, 1)} yld
          </Tooltip>
        </CircleMarker>
      ))}
      {props.map((p) => {
        const m = computeMetrics(p);
        const hl = highlightId === p.id;
        return (
          <CircleMarker
            key={p.id}
            center={[p.lat, p.lng]}
            radius={hl ? 11 : 6}
            pathOptions={{
              color: tok("--background"),
              weight: 1,
              fillColor: verdictColor[m.verdict],
              fillOpacity: 0.9,
            }}
          >
            <Popup>
              <Link to="/property/$id" params={{ id: p.id }} className="font-mono text-xs">
                {p.address}
              </Link>
              <div className="text-[10px] uppercase tracking-wider">
                {m.verdict} · {Math.round(m.cashOnCash * 100)}% CoC
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
