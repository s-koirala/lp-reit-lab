import { NEIGHBORHOODS, type Neighborhood } from "./neighborhoods";

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
  tenantFitScore: number; // 0-100 demand for 3BR+ family units
  hoa: number; // monthly
  propertyTaxAnnual: number;
  insuranceAnnual: number;
  // map coords (internal 0-1000)
  x: number;
  y: number;
};

// Deterministic PRNG so the mock dataset is stable per build
function mulberry32(seed: number) {
  return function () {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const rand = mulberry32(20260605);
const rng = (min: number, max: number) => min + (max - min) * rand();
const pick = <T,>(arr: T[]) => arr[Math.floor(rand() * arr.length)];

const STREETS = [
  "N Cleveland Ave","W Belden Ave","W Webster Ave","N Halsted St","W Armitage Ave",
  "N Sheffield Ave","W Wrightwood Ave","N Burling St","W Dickens Ave","N Orchard St",
  "W Diversey Pkwy","N Racine Ave","W Altgeld St","N Mohawk St","W Fullerton Pkwy",
  "N Larrabee St","W Drummond Pl","N Kenmore Ave","W Wellington Ave","N Magnolia Ave",
];

function pointInPoly(neigh: Neighborhood) {
  // sample within bbox until inside polygon
  const xs = neigh.polygon.map((p) => p[0]);
  const ys = neigh.polygon.map((p) => p[1]);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  for (let i = 0; i < 200; i++) {
    const x = rng(minX, maxX), y = rng(minY, maxY);
    if (inside(x, y, neigh.polygon)) return [x, y] as [number, number];
  }
  return neigh.centroid;
}
function inside(x: number, y: number, poly: [number, number][]) {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    const intersect = yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;
    if (intersect) c = !c;
  }
  return c;
}

function genProperty(i: number): Property {
  const neigh = NEIGHBORHOODS[i % NEIGHBORHOODS.length];
  const type = pick(["Single Family","Single Family","Townhouse","Townhouse","Condo","2-Flat"] as const);
  const beds = type === "Condo" ? pick([2,3,3,4]) : pick([3,3,4,4,5]);
  const baths = Math.max(1, Math.round((beds - 1) * 0.7 + rand() * 1.5));
  const sqft = Math.round(800 + beds * 450 + rng(-200, 400));
  const yearBuilt = Math.round(rng(1895, 2022));
  const ppsf = neigh.medianPrice / 2400 * rng(0.82, 1.18);
  const listPrice = Math.round(sqft * ppsf / 5000) * 5000;
  const fairPrice = Math.round(listPrice * rng(0.92, 1.09));
  const predBand = listPrice * 0.06;
  const rentBase = neigh.medianRent3br * (beds / 3) ** 0.55 * rng(0.88, 1.10);
  const predictedRent = Math.round(rentBase / 25) * 25;
  const rentBand = predictedRent * 0.08;
  const apprMean = neigh.appreciation5y + rng(-0.012, 0.012);
  const tax = Math.round(listPrice * rng(0.018, 0.024));
  const ins = Math.round(800 + listPrice * rng(0.0028, 0.0042));
  const hoa = type === "Condo" ? Math.round(rng(280, 720)) : type === "Townhouse" ? Math.round(rng(0, 380)) : 0;
  const [x, y] = pointInPoly(neigh);
  const tenantFit = Math.round(
    40 +
      (beds >= 3 ? 25 : 8) +
      (sqft > 1600 ? 12 : 4) +
      neigh.schoolScore * 0.25 +
      rng(-6, 6)
  );
  return {
    id: `LP-${String(1000 + i)}`,
    address: `${Math.round(rng(400, 3200))} ${pick(STREETS)}`,
    neighborhoodSlug: neigh.slug,
    beds, baths, sqft, type, yearBuilt,
    listPrice,
    assessedValue: Math.round(listPrice * rng(0.62, 0.78) / 1000) * 1000,
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
    hoa, propertyTaxAnnual: tax, insuranceAnnual: ins,
    x, y,
  };
}

export const PROPERTIES: Property[] = Array.from({ length: 52 }, (_, i) => genProperty(i));

// ----- Financial model -----
export type Financing = {
  downPct: number;
  ratePct: number;
  termYears: number;
};
export const DEFAULT_FINANCING: Financing = { downPct: 0.25, ratePct: 6.85, termYears: 30 };

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

export function monthlyMortgage(principal: number, ratePct: number, years: number) {
  const r = ratePct / 100 / 12;
  const n = years * 12;
  if (r === 0) return principal / n;
  return (principal * r) / (1 - Math.pow(1 + r, -n));
}

export function computeMetrics(p: Property, fin: Financing = DEFAULT_FINANCING): Metrics {
  const down = p.listPrice * fin.downPct;
  const loan = p.listPrice - down;
  const closing = p.listPrice * 0.015;
  const mortgage = monthlyMortgage(loan, fin.ratePct, fin.termYears);
  const tax = p.propertyTaxAnnual / 12;
  const insurance = p.insuranceAnnual / 12;
  const hoa = p.hoa;
  const maintenance = (p.listPrice * 0.008) / 12;
  const vacancy = p.predictedRent * 0.06;
  const management = p.predictedRent * 0.08;
  const total = mortgage + tax + insurance + hoa + maintenance + vacancy + management;
  const carry: CarryingCosts = { mortgage, tax, insurance, hoa, maintenance, vacancy, management, total };

  const grossAnnualRent = p.predictedRent * 12;
  const opex = (tax + insurance + hoa + maintenance + vacancy + management) * 12;
  const noi = grossAnnualRent - opex;
  const capRate = noi / p.listPrice;
  const grossRentYield = grossAnnualRent / p.listPrice;
  const netRentYield = noi / p.listPrice;
  const annualCashflow = noi - mortgage * 12;
  const monthlyCashflow = annualCashflow / 12;
  const cashInvested = down + closing;
  const cashOnCash = annualCashflow / cashInvested;
  const pricePremium = (p.listPrice - p.predictedPrice) / p.predictedPrice;

  const reasons: string[] = [];
  let score = 0;
  if (pricePremium <= -0.03) { score += 2; reasons.push(`List sits ${(Math.abs(pricePremium)*100).toFixed(1)}% below model fair price.`); }
  else if (pricePremium >= 0.05) { score -= 2; reasons.push(`List sits ${(pricePremium*100).toFixed(1)}% above model fair price.`); }
  else { reasons.push(`Priced within model band (±5%).`); }

  if (netRentYield >= 0.045) { score += 2; reasons.push(`Net yield ${(netRentYield*100).toFixed(2)}% clears the 4.5% threshold.`); }
  else if (netRentYield < 0.032) { score -= 2; reasons.push(`Net yield ${(netRentYield*100).toFixed(2)}% below 3.2% floor.`); }
  else { reasons.push(`Net yield ${(netRentYield*100).toFixed(2)}% — adequate but not standout.`); }

  if (p.expectedAppreciation >= 0.040) { score += 1; reasons.push(`Forecast appreciation ${(p.expectedAppreciation*100).toFixed(1)}%/yr.`); }
  if (p.tenantFitScore >= 75) { score += 1; reasons.push(`Strong market demand for 3BR+ family units in this submarket.`); }
  if (p.expectedDom > 55) { score -= 1; reasons.push(`Forecast time-on-market ${p.expectedDom}d signals weaker liquidity.`); }
  if (monthlyCashflow < -1500) { score -= 1; reasons.push(`Negative monthly cashflow exceeds −$1,500.`); }

  let verdict: Verdict = "watch";
  if (score >= 3) verdict = "go";
  else if (score <= -2) verdict = "no-go";

  // Confidence proxy: tighter prediction bands → higher confidence
  const priceBandRel = (p.predictedPriceHigh - p.predictedPriceLow) / p.predictedPrice;
  const rentBandRel = (p.predictedRentHigh - p.predictedRentLow) / p.predictedRent;
  const confidence = Math.max(0.35, Math.min(0.95, 1 - (priceBandRel + rentBandRel) * 0.9));

  return {
    pricePremium, grossRentYield, netRentYield, capRate, cashOnCash,
    monthlyCashflow, carry, verdict, verdictConfidence: confidence,
    verdictReasons: reasons,
  };
}

export const blendedScore = (p: Property, m: Metrics) =>
  m.netRentYield * 100 * 0.55 + p.expectedAppreciation * 100 * 0.45 - Math.max(0, m.pricePremium) * 20;

export const getProperty = (id: string) => PROPERTIES.find((p) => p.id === id);
