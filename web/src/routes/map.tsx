import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { PropertyMap } from "@/components/PropertyMap";

export const Route = createFileRoute("/map")({
  head: () => ({ meta: [{ title: "Map — Lincoln Park Property Lab" }] }),
  component: () => (
    <AppShell>
      <header className="rule-b pb-6 mb-6">
        <p className="font-mono text-xs uppercase tracking-[0.22em] text-muted-foreground mb-2">Spatial view</p>
        <h1 className="text-5xl">The candidate universe, mapped.</h1>
        <p className="mt-3 text-ink-soft max-w-2xl">
          Each dot is a candidate property, color-coded by headline verdict. Submarket polygons
          carry their median price and net yield. Click any dot for the deal memo.
        </p>
      </header>
      <PropertyMap />
    </AppShell>
  ),
});
