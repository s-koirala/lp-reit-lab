import { NEIGHBORHOODS } from "./neighborhoods";

// Repeat-sales appreciation index, monthly, 2015-01 = 100
function buildIndex(slug: string, cagr: number, vol: number, seed: number) {
  const months: { date: string; value: number; lower: number; upper: number }[] = [];
  let v = 100;
  let r = seed;
  const noise = () => {
    r = (r * 9301 + 49297) % 233280;
    return r / 233280 - 0.5;
  };
  for (let i = 0; i < 132; i++) {
    const year = 2015 + Math.floor(i / 12);
    const month = (i % 12) + 1;
    const monthlyCagr = Math.pow(1 + cagr, 1 / 12) - 1;
    const shock = i === 60 ? -0.012 : i === 84 ? 0.018 : 0;
    v = v * (1 + monthlyCagr + noise() * vol + shock);
    const band = v * 0.018;
    months.push({
      date: `${year}-${String(month).padStart(2, "0")}`,
      value: +v.toFixed(2),
      lower: +(v - band).toFixed(2),
      upper: +(v + band).toFixed(2),
    });
  }
  return { slug, series: months };
}

export const PRICE_INDEX = NEIGHBORHOODS.map((n, i) =>
  buildIndex(n.slug, n.appreciation5y, 0.006, 1000 + i * 137)
);

export const RENT_INDEX = NEIGHBORHOODS.map((n, i) =>
  buildIndex(n.slug, n.appreciation5y * 0.7 + 0.012, 0.004, 2000 + i * 191)
);

// market liquidity — monthly DOM averages, last 36 months
export const LIQUIDITY = NEIGHBORHOODS.map((n, i) => {
  let r = 333 + i * 17;
  const noise = () => { r = (r * 9301 + 49297) % 233280; return r / 233280 - 0.5; };
  return {
    slug: n.slug,
    series: Array.from({ length: 36 }, (_, k) => {
      const year = 2023 + Math.floor(k / 12);
      const month = (k % 12) + 1;
      return {
        date: `${year}-${String(month).padStart(2, "0")}`,
        dom: Math.max(14, Math.round(n.domMedian + noise() * 18)),
      };
    }),
  };
});
