export type Neighborhood = {
  slug: string;
  name: string;
  // synthetic polygon coords in our internal 0-1000 map space
  polygon: [number, number][];
  centroid: [number, number];
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
    polygon: [[380, 320],[560, 300],[600, 460],[580, 560],[420, 580],[360, 500]],
    centroid: [480, 440],
    medianPrice: 1_185_000, medianRent3br: 5400,
    appreciation5y: 0.041, appreciation1y: 0.028,
    yieldMedian: 0.046, domMedian: 38,
    transitScore: 88, schoolScore: 92, amenityScore: 95, inventory: 142,
    blurb: "Premium North Side anchor. Mature appreciation, deep rental demand for 3BR+ family units near Oz Park and the lakefront.",
  },
  {
    slug: "lakeview",
    name: "Lakeview",
    polygon: [[380, 140],[600, 130],[620, 290],[560, 310],[380, 320],[350, 220]],
    centroid: [480, 220],
    medianPrice: 895_000, medianRent3br: 4400,
    appreciation5y: 0.038, appreciation1y: 0.031,
    yieldMedian: 0.052, domMedian: 32,
    transitScore: 90, schoolScore: 84, amenityScore: 93, inventory: 188,
    blurb: "Dense, transit-rich, broad rental pool. Yields trend higher than Lincoln Park with comparable liquidity.",
  },
  {
    slug: "old-town",
    name: "Old Town",
    polygon: [[560, 540],[680, 520],[720, 640],[620, 680],[540, 640]],
    centroid: [620, 600],
    medianPrice: 1_320_000, medianRent3br: 5800,
    appreciation5y: 0.046, appreciation1y: 0.034,
    yieldMedian: 0.042, domMedian: 41,
    transitScore: 85, schoolScore: 88, amenityScore: 90, inventory: 64,
    blurb: "Tight historic inventory. Strongest pricing power on the list; yields compressed by scarcity premium.",
  },
  {
    slug: "depaul",
    name: "DePaul",
    polygon: [[260, 380],[380, 360],[400, 480],[300, 500],[240, 460]],
    centroid: [320, 430],
    medianPrice: 1_050_000, medianRent3br: 5000,
    appreciation5y: 0.039, appreciation1y: 0.026,
    yieldMedian: 0.048, domMedian: 36,
    transitScore: 87, schoolScore: 90, amenityScore: 89, inventory: 78,
    blurb: "University-adjacent stability. Consistent rental absorption and a deep buyer pool for 3BR resales.",
  },
  {
    slug: "sheffield-wrightwood",
    name: "Sheffield / Wrightwood Neighbors",
    polygon: [[200, 260],[360, 250],[380, 360],[260, 380],[200, 340]],
    centroid: [290, 320],
    medianPrice: 1_220_000, medianRent3br: 5600,
    appreciation5y: 0.044, appreciation1y: 0.033,
    yieldMedian: 0.043, domMedian: 40,
    transitScore: 86, schoolScore: 93, amenityScore: 88, inventory: 51,
    blurb: "Tree-lined SFR pocket with the area's most coveted school assignment. Long holds, low turnover.",
  },
  {
    slug: "ranch-triangle",
    name: "RANCH Triangle",
    polygon: [[600, 470],[760, 450],[780, 560],[680, 560],[600, 540]],
    centroid: [690, 510],
    medianPrice: 1_140_000, medianRent3br: 5200,
    appreciation5y: 0.042, appreciation1y: 0.030,
    yieldMedian: 0.045, domMedian: 39,
    transitScore: 82, schoolScore: 86, amenityScore: 87, inventory: 47,
    blurb: "Compact townhouse-heavy enclave bordered by Armitage, North, and the river. Stable, family-buyer driven.",
  },
];

export const getNeighborhood = (slug: string) =>
  NEIGHBORHOODS.find((n) => n.slug === slug);
