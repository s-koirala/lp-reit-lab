import type { Verdict } from "@/lib/data/properties";
import { cn } from "@/lib/utils";

const STYLES: Record<Verdict, { label: string; cls: string; dot: string }> = {
  "go": { label: "GO", cls: "text-go border-go/40 bg-go/10", dot: "bg-go" },
  "watch": { label: "WATCH", cls: "text-watch border-watch/40 bg-watch/10", dot: "bg-watch" },
  "no-go": { label: "NO-GO", cls: "text-nogo border-nogo/40 bg-nogo/10", dot: "bg-nogo" },
};

export function VerdictBadge({
  verdict,
  confidence,
  size = "md",
  className,
}: {
  verdict: Verdict;
  confidence?: number;
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const s = STYLES[verdict];
  const sizeCls =
    size === "lg" ? "px-3 py-1.5 text-sm" : size === "sm" ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-1 text-xs";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 border font-mono uppercase tracking-wider rounded-sm",
        sizeCls, s.cls, className,
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full", s.dot)} />
      {s.label}
      {confidence !== undefined && (
        <span className="opacity-70 ml-1">{Math.round(confidence * 100)}%</span>
      )}
    </span>
  );
}
