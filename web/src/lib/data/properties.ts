import { NEIGHBORHOODS, type Neighborhood } from "./neighborhoods";
import {
  ASSUMPTIONS,
  SCORING,
  carryMonthly,
  evaluateProperty,
  scoreProperty,
  type EvaluateResult,
  type ScoreResult,
  type Verdict as EngineVerdict,
} from "../engine";

export type Verdict = "go" | "watch" | "no-go";

export type Property = {
  id: string;
  address: string;
  neighborhoodSlug: string;
  beds: number;
  baths: number;
  sqft: number;
  type: "Single Family" | "Townhouse" | "Condo" | "2-Flat";
  yearBuilt: number;
  listPrice: number;
  assessedValue: number;
  predictedPrice: number;
  predictedPriceLow: number;
  predictedPriceHigh: number;
  predictedRent: number;
  predictedRentLow: number;
  predictedRentHigh: number;
  expectedDom: number;
  expectedAppreciation: number; // 5y CAGR
  expectedAppreciationLow: number;
  expectedAppreciationHigh: number;
  tenantFitScore: number; // 0-100 market-demand proxy for 3BR+ units (size/school/transit driven)
  hoa: number; // monthly
  propertyTaxAnnual: number;
  insuranceAnnual: number;
  // real WGS84 location (synthetic, jittered within the submarket) for the map
  lat: number;
  lng: number;
};

// Deterministic PRNG so the mock dataset is stable per build
function mulberry32(seed: number) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(20260605);
const rng = (min: number, max: number) => min + (max - min) * rand();
const pick = <T>(arr: T[]) => arr[Math.floor(rand() * arr.length)];

const STREETS = [
  "N Cleveland Ave",
  "W Belden Ave",
  "W Webster Ave",
  "N Halsted St",
  "W Armitage Ave",
  "N Sheffield Ave",
  "W Wrightwood Ave",
  "N Burling St",
  "W Dickens Ave",
  "N Orchard St",
  "W Diversey Pkwy",
  "N Racine Ave",
  "W Altgeld St",
  "N Mohawk St",
  "W Fullerton Pkwy",
  "N Larrabee St",
  "W Drummond Pl",
  "N Kenmore Ave",
  "W Wellington Ave",
  "N Magnolia Ave",
];

function genProperty(i: number): Property {
  const neigh = NEIGHBORHOODS[i % NEIGHBORHOODS.length];
  const type = pick([
    "Single Family",
    "Single Family",
    "Townhouse",
    "Townhouse",
    "Condo",
    "2-Flat",
  ] as const);
  const beds = type === "Condo" ? pick([2, 3, 3, 4]) : pick([3, 3, 4, 4, 5]);
  const baths = Math.max(1, Math.round((beds - 1) * 0.7 + rand() * 1.5));
  const sqft = Math.round(800 + beds * 450 + rng(-200, 400));
  const yearBuilt = Math.round(rng(1895, 2022));
  const ppsf = (neigh.medianPrice / 2400) * rng(0.82, 1.18);
  const listPrice = Math.round((sqft * ppsf) / 5000) * 5000;
  const fairPrice = Math.round(listPrice * rng(0.92, 1.09));
  const predBand = listPrice * 0.06;
  const rentBase = neigh.medianRent3br * (beds / 3) ** 0.55 * rng(0.88, 1.1);
  const predictedRent = Math.round(rentBase / 25) * 25;
  const rentBand = predictedRent * 0.08;
  const apprMean = neigh.appreciation5y + rng(-0.012, 0.012);
  const tax = Math.round(listPrice * rng(0.018, 0.024));
  const ins = Math.round(800 + listPrice * rng(0.0028, 0.0042));
  const hoa =
    type === "Condo"
      ? Math.round(rng(280, 720))
      : type === "Townhouse"
        ? Math.round(rng(0, 380))
        : 0;
  // Synthetic geocoordinate: jitter within ~±0.006° (~0.5-0.7 km) of the submarket
  // centroid so dots scatter realistically over real tiles. Demo data, not a listing.
  const lat = neigh.lat + rng(-0.006, 0.006);
  const lng = neigh.lng + rng(-0.006, 0.006);
  const tenantFit = Math.round(
    40 + (beds >= 3 ? 25 : 8) + (sqft > 1600 ? 12 : 4) + neigh.schoolScore * 0.25 + rng(-6, 6),
  );
  return {
    id: `LP-${String(1000 + i)}`,
    address: `${Math.round(rng(400, 3200))} ${pick(STREETS)}`,
    neighborhoodSlug: neigh.slug,
    beds,
    baths,
    sqft,
    type,
    yearBuilt,
    listPrice,
    assessedValue: Math.round((listPrice * rng(0.62, 0.78)) / 1000) * 1000,
    predictedPrice: fairPrice,
    predictedPriceLow: Math.round(fairPrice - predBand),
    predictedPriceHigh: Math.round(fairPrice + predBand),
    predictedRent,
    predictedRentLow: Math.round(predictedRent - rentBand),
    predictedRentHigh: Math.round(predictedRent + rentBand),
    expectedDom: Math.round(neigh.domMedian * rng(0.7, 1.4)),
    expectedAppreciation: apprMean,
    expectedAppreciationLow: apprMean - 0.012,
    expectedAppreciationHigh: apprMean + 0.012,
    tenantFitScore: Math.max(20, Math.min(99, tenantFit)),
    hoa,
    propertyTaxAnnual: tax,
    insuranceAnnual: ins,
    lat,
    lng,
  };
}

export const PROPERTIES: Property[] = Array.from({ length: 52 }, (_, i) => genProperty(i));

// ----- Financial model -----
export type Financing = {
  downPct: number;
  ratePct: number;
  termYears: number;
};
// Display-facing financing terms, derived from the engine's canonical assumptions
// (config/assumptions.yaml) so the deal memo's stated rate/down/term always match
// the numbers the engine actually used.
export const DEFAULT_FINANCING: Financing = {
  downPct: ASSUMPTIONS.down_payment_fraction,
  ratePct: ASSUMPTIONS.mortgage_rate_annual * 100,
  termYears: ASSUMPTIONS.amortization_years,
};

export type CarryingCosts = {
  mortgage: number; // monthly P&I
  tax: number;
  insurance: number;
  hoa: number;
  maintenance: number;
  vacancy: number;
  management: number;
  total: number;
};

export type Metrics = {
  pricePremium: number; // (list - predicted) / predicted
  grossRentYield: number;
  netRentYield: number;
  capRate: number;
  cashOnCash: number;
  monthlyCashflow: number;
  carry: CarryingCosts;
  verdict: Verdict;
  verdictConfidence: number; // 0-1
  verdictReasons: string[];
};

const VERDICT_MAP: Record<EngineVerdict, Verdict> = {
  GO: "go",
  WATCH: "watch",
  "NO-GO": "no-go",
};

function reasonsFor(ev: EvaluateResult, score: ScoreResult, pricePremium: number): string[] {
  const pct = (x: number, d = 1) => `${(x * 100).toFixed(d)}%`;
  const reasons: string[] = [];
  if (pricePremium <= -0.03)
    reasons.push(`List sits ${pct(Math.abs(pricePremium))} below model fair price.`);
  else if (pricePremium >= 0.05)
    reasons.push(`List sits ${pct(pricePremium)} above model fair price.`);
  else reasons.push(`Priced within the model band (±5%).`);
  reasons.push(`Cash-on-cash ${pct(ev.cash_on_cash, 2)} (${score.lights.cash_on_cash}).`);
  reasons.push(
    `DSCR ${ev.dscr.toFixed(2)} (${score.lights.dscr}); cap-rate spread over 10y ${pct(ev.cap_rate_spread, 2)} (${score.lights.cap_rate_spread}).`,
  );
  if (ev.monthly_cash_flow < 0)
    reasons.push(
      `Cash-flow negative at $${Math.round(ev.monthly_cash_flow).toLocaleString("en-US")}/mo — an appreciation play, not income.`,
    );
  return reasons;
}

// computeMetrics now delegates to the deterministic engine (a parity-gated mirror
// of src/lp_reit_lab/finance), replacing the former magic-number mock. The Metrics
// shape is preserved for the UI; netRentYield == capRate == going-in cap (NOI/price).
export function computeMetrics(p: Property): Metrics {
  // Fail-closed: the engine throws on non-positive price/rent (division-by-zero
  // guards). Synthetic PROPERTIES are always > 0, but real listings (P3/P4) may
  // carry blank/zero fields — return a NO-GO sentinel rather than crash the route.
  if (!(p.listPrice > 0) || !(p.predictedRent > 0) || !(p.predictedPrice > 0)) {
    const zero: CarryingCosts = {
      mortgage: 0,
      tax: 0,
      insurance: 0,
      hoa: 0,
      maintenance: 0,
      vacancy: 0,
      management: 0,
      total: 0,
    };
    return {
      pricePremium: 0,
      grossRentYield: 0,
      netRentYield: 0,
      capRate: 0,
      cashOnCash: 0,
      monthlyCashflow: 0,
      carry: zero,
      verdict: "no-go",
      verdictConfidence: 0,
      verdictReasons: ["Insufficient data to score (missing price or rent)."],
    };
  }

  const ev = evaluateProperty(p.listPrice, p.predictedRent, p.hoa, ASSUMPTIONS);
  const carry = carryMonthly(p.listPrice, p.predictedRent, p.hoa, ASSUMPTIONS);
  const score = scoreProperty(ev, SCORING);
  const pricePremium = (p.listPrice - p.predictedPrice) / p.predictedPrice;

  // Confidence proxy: tighter model prediction bands -> higher confidence. A
  // provisional presentational heuristic (band width is a monotone uncertainty
  // proxy); the [0.35, 0.95] clamp and 0.9 scale are display bounds, not analytic
  // thresholds. Superseded when the real prediction model lands (P5).
  const priceBandRel = (p.predictedPriceHigh - p.predictedPriceLow) / p.predictedPrice;
  const rentBandRel = (p.predictedRentHigh - p.predictedRentLow) / p.predictedRent;
  const confidence = Math.max(0.35, Math.min(0.95, 1 - (priceBandRel + rentBandRel) * 0.9));

  return {
    pricePremium,
    grossRentYield: ev.gross_potential_rent / p.listPrice,
    netRentYield: ev.going_in_cap,
    capRate: ev.going_in_cap,
    cashOnCash: ev.cash_on_cash,
    monthlyCashflow: ev.monthly_cash_flow,
    carry: {
      mortgage: carry.mortgage,
      tax: carry.tax,
      insurance: carry.insurance,
      hoa: carry.hoa,
      maintenance: carry.maintenance,
      vacancy: carry.vacancy,
      management: carry.management,
      total: carry.total,
    },
    verdict: VERDICT_MAP[score.verdict],
    verdictConfidence: confidence,
    verdictReasons: reasonsFor(ev, score, pricePremium),
  };
}

// Provisional list-ranking heuristic (sort order only, not a verdict): weights the
// two estimands — yield vs appreciation — with a price-premium penalty. The
// weights are presentational defaults, not fitted; to be migrated to a cited
// `ranking` block in config/scoring.yaml alongside the real models (P4/P5).
export const blendedScore = (p: Property, m: Metrics) =>
  m.netRentYield * 100 * 0.55 +
  p.expectedAppreciation * 100 * 0.45 -
  Math.max(0, m.pricePremium) * 20;

export const getProperty = (id: string) => PROPERTIES.find((p) => p.id === id);
