import { Link } from "@tanstack/react-router";
import type { ReactNode } from "react";

const NAV = [
  { to: "/", label: "Screener" },
  { to: "/map", label: "Map" },
  { to: "/neighborhoods", label: "Neighborhoods" },
  { to: "/market", label: "Market" },
  { to: "/methodology", label: "Method" },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background paper-grain">
      <header className="rule-b bg-background/95 backdrop-blur sticky top-0 z-40">
        <div className="mx-auto max-w-[1500px] px-6 py-4 flex items-end justify-between gap-8">
          <Link to="/" className="flex items-baseline gap-3 group">
            <span className="font-display text-3xl leading-none">Lincoln Park</span>
            <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
              Property Lab · est. 2026
            </span>
          </Link>
          <nav className="flex items-center gap-1">
            {NAV.map((n) => (
              <Link
                key={n.to}
                to={n.to}
                activeOptions={{ exact: n.to === "/" }}
                className="px-3 py-1.5 text-sm font-mono uppercase tracking-wider text-muted-foreground hover:text-foreground data-[status=active]:text-foreground data-[status=active]:border-b data-[status=active]:border-foreground transition-colors"
              >
                {n.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="mx-auto max-w-[1500px] px-6 pb-2 flex items-center justify-between text-[10px] font-mono uppercase tracking-[0.22em] text-muted-foreground">
          <span>Vol. I · No. 1</span>
          <span>Chicago North Side — Residential Investment Index</span>
          <span>{new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}</span>
        </div>
      </header>
      <main className="mx-auto max-w-[1500px] px-6 py-8">{children}</main>
      <footer className="rule-t mt-16">
        <div className="mx-auto max-w-[1500px] px-6 py-8 text-xs text-muted-foreground flex flex-wrap gap-x-8 gap-y-2 justify-between">
          <span>Synthetic demonstration data. Estimates carry statistical uncertainty.</span>
          <span className="font-mono uppercase tracking-wider">Fair Housing compliant · market-demand framing only</span>
        </div>
      </footer>
    </div>
  );
}
