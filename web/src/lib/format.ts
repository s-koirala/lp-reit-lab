export const fmtMoney = (n: number, opts: { decimals?: number; compact?: boolean } = {}) => {
  const { decimals = 0, compact = false } = opts;
  if (compact && Math.abs(n) >= 1_000_000)
    return `$${(n / 1_000_000).toFixed(2)}M`;
  if (compact && Math.abs(n) >= 1_000)
    return `$${(n / 1_000).toFixed(0)}k`;
  return n.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

export const fmtPct = (n: number, decimals = 1) =>
  `${(n * 100).toFixed(decimals)}%`;

export const fmtSignedPct = (n: number, decimals = 1) =>
  `${n >= 0 ? "+" : ""}${(n * 100).toFixed(decimals)}%`;

export const fmtInt = (n: number) => Math.round(n).toLocaleString("en-US");
