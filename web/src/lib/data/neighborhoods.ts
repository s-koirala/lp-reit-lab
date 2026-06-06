export type Neighborhood = {
  slug: string;
  name: string;
  // Real (approximate) WGS84 centroid of the submarket, for the Leaflet map.
  lat: number;
  lng: number;
  medianPrice: number;
  medianRent3br: number;
  appreciation5y: number; // CAGR
  appreciation1y: number;
  yieldMedian: number;
  domMedian: number; // days on market
  transitScore: number;
  schoolScore: number;
  amenityScore: number;
  inventory: number;
  blurb: string;
};

export const NEIGHBORHOODS: Neighborhood[] = [
  {
    slug: "lincoln-park",
    name: "Lincoln Park",
    lat: 41.921,
    lng: -87.648,
    medianPrice: 1_185_000,
    medianRent3br: 5400,
    appreciation5y: 0.041,
    appreciation1y: 0.028,
    yieldMedian: 0.046,
    domMedian: 38,
    transitScore: 88,
    schoolScore: 92,
    amenityScore: 95,
    inventory: 142,
    blurb:
      "Premium North Side anchor. Mature appreciation, deep rental demand for 3BR+ family units near Oz Park and the lakefront.",
  },
  {
    slug: "lakeview",
    name: "Lakeview",
    lat: 41.943,
    lng: -87.653,
    medianPrice: 895_000,
    medianRent3br: 4400,
    appreciation5y: 0.038,
    appreciation1y: 0.031,
    yieldMedian: 0.052,
    domMedian: 32,
    transitScore: 90,
    schoolScore: 84,
    amenityScore: 93,
    inventory: 188,
    blurb:
      "Dense, transit-rich, broad rental pool. Yields trend higher than Lincoln Park with comparable liquidity.",
  },
  {
    slug: "old-town",
    name: "Old Town",
    lat: 41.91,
    lng: -87.638,
    medianPrice: 1_320_000,
    medianRent3br: 5800,
    appreciation5y: 0.046,
    appreciation1y: 0.034,
    yieldMedian: 0.042,
    domMedian: 41,
    transitScore: 85,
    schoolScore: 88,
    amenityScore: 90,
    inventory: 64,
    blurb:
      "Tight historic inventory. Strongest pricing power on the list; yields compressed by scarcity premium.",
  },
  {
    slug: "depaul",
    name: "DePaul",
    lat: 41.924,
    lng: -87.654,
    medianPrice: 1_050_000,
    medianRent3br: 5000,
    appreciation5y: 0.039,
    appreciation1y: 0.026,
    yieldMedian: 0.048,
    domMedian: 36,
    transitScore: 87,
    schoolScore: 90,
    amenityScore: 89,
    inventory: 78,
    blurb:
      "University-adjacent stability. Consistent rental absorption and a deep buyer pool for 3BR resales.",
  },
  {
    slug: "sheffield-wrightwood",
    name: "Sheffield / Wrightwood Neighbors",
    lat: 41.929,
    lng: -87.653,
    medianPrice: 1_220_000,
    medianRent3br: 5600,
    appreciation5y: 0.044,
    appreciation1y: 0.033,
    yieldMedian: 0.043,
    domMedian: 40,
    transitScore: 86,
    schoolScore: 93,
    amenityScore: 88,
    inventory: 51,
    blurb:
      "Tree-lined SFR pocket with the area's most coveted school assignment. Long holds, low turnover.",
  },
  {
    slug: "ranch-triangle",
    name: "RANCH Triangle",
    lat: 41.917,
    lng: -87.655,
    medianPrice: 1_140_000,
    medianRent3br: 5200,
    appreciation5y: 0.042,
    appreciation1y: 0.03,
    yieldMedian: 0.045,
    domMedian: 39,
    transitScore: 82,
    schoolScore: 86,
    amenityScore: 87,
    inventory: 47,
    blurb:
      "Compact townhouse-heavy enclave bordered by Armitage, North, and the river. Stable, family-buyer driven.",
  },
];

export const getNeighborhood = (slug: string) => NEIGHBORHOODS.find((n) => n.slug === slug);
