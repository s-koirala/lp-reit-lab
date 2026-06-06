// Deterministic income-property finance engine — a faithful TypeScript mirror of
// the Python engine in src/lp_reit_lab/finance (metrics.py, cashflow.py,
// evaluate.py, scoring.py). The Python side is the source of truth; this mirror
// is parity-gated against golden vectors it emits (see __fixtures__/golden_vectors.json
// and engine.test.ts). Data keys are snake_case to match the Python outputs and
// the generated config 1:1, so the parity comparison is a direct deep-equal and
// there is no hand-maintained camelCase mapping to drift.
//
// IRR (levered/unlevered) is intentionally NOT computed here: numpy_financial.irr
// selects among multiple real roots for the sign-changing, cash-flow-negative
// streams typical of LP appreciation plays, which a TS root-finder cannot be
// guaranteed to match. NPV (fixed discount rate) and the equity multiple are
// deterministic and are mirrored + gated. See finance/cashflow.py::irr.

export const MONTHS_PER_YEAR = 12;

export type Light = "green" | "amber" | "red";
export type Verdict = "GO" | "WATCH" | "NO-GO";

export interface Assumptions {
  mortgage_rate_annual: number;
  amortization_years: number;
  down_payment_fraction: number;
  closing_cost_fraction: number;
  vacancy_rate: number;
  rent_growth_annual: number;
  other_income_fraction: number;
  property_tax_rate_of_value: number;
  insurance_annual: number;
  maintenance_reserve_fraction: number;
  property_management_fraction: number;
  owner_paid_utilities_monthly: number;
  hoa_monthly_default: number;
  cost_inflation_annual: number;
  hold_years: number;
  exit_cap_spread: number;
  selling_cost_fraction: number;
  appreciation_annual: number;
  discount_rate: number;
  treasury_10y: number;
}

export interface ProformaRow {
  year: number;
  gross_potential_rent: number;
  egi: number;
  opex: number;
  noi: number;
  debt_service: number;
  levered_cash_flow: number;
}

export interface EvaluateResult {
  price: number;
  monthly_rent: number;
  hoa_monthly: number;
  gross_potential_rent: number;
  egi: number;
  opex: number;
  noi: number;
  going_in_cap: number;
  cap_rate_spread: number;
  loan: number;
  equity_invested: number;
  annual_debt_service: number;
  annual_cash_flow: number;
  monthly_cash_flow: number;
  cash_on_cash: number;
  dscr: number;
  grm: number;
  oer: number;
  break_even_occupancy: number;
  ltv: number;
  levered_irr: number | null; // Python-only (see header); not parity-gated
  unlevered_irr: number | null;
  npv: number;
  equity_multiple: number;
  total_equity_in: number;
  terminal_basis: "exit-cap" | "appreciation";
  exit_cap: number;
  sale_price: number;
  net_reversion: number;
  proforma: ProformaRow[];
}

export interface CarryMonthly {
  mortgage: number;
  tax: number;
  insurance: number;
  hoa: number;
  maintenance: number;
  management: number;
  vacancy: number;
  total: number;
}

// --- single-period primitives (metrics.py) -----------------------------------

export function mortgagePayment(loan: number, annualRate: number, years: number): number {
  if (years <= 0) throw new Error("years must be positive");
  if (loan < 0) throw new Error("loan must be non-negative");
  const n = years * MONTHS_PER_YEAR;
  const r = annualRate / MONTHS_PER_YEAR;
  if (r === 0) return loan / n;
  const factor = (1 + r) ** n;
  return (loan * r * factor) / (factor - 1);
}

export function remainingBalance(
  loan: number,
  annualRate: number,
  years: number,
  monthsElapsed: number,
): number {
  if (years <= 0) throw new Error("years must be positive");
  if (loan < 0) throw new Error("loan must be non-negative");
  const n = years * MONTHS_PER_YEAR;
  const k = Math.max(0, Math.min(monthsElapsed, n));
  const r = annualRate / MONTHS_PER_YEAR;
  if (r === 0) return loan * (1 - k / n);
  const factorN = (1 + r) ** n;
  const factorK = (1 + r) ** k;
  return (loan * (factorN - factorK)) / (factorN - 1);
}

export function annualDebtService(loan: number, annualRate: number, years: number): number {
  return mortgagePayment(loan, annualRate, years) * MONTHS_PER_YEAR;
}

export function grossPotentialRent(monthlyRent: number): number {
  return monthlyRent * MONTHS_PER_YEAR;
}

export function effectiveGrossIncome(
  monthlyRent: number,
  vacancyRate: number,
  otherIncomeFraction = 0,
): number {
  if (!(vacancyRate >= 0 && vacancyRate < 1)) throw new Error("vacancy_rate must be in [0, 1)");
  const gpr = grossPotentialRent(monthlyRent);
  return gpr * (1 - vacancyRate) + gpr * otherIncomeFraction;
}

export function capRate(noi: number, value: number): number {
  if (value <= 0) throw new Error("value must be positive");
  return noi / value;
}

export function cashInvested(
  price: number,
  downPaymentFraction: number,
  closingCostFraction: number,
): number {
  return price * downPaymentFraction + price * closingCostFraction;
}

export function preTaxCashFlow(noi: number, debtService: number): number {
  return noi - debtService;
}

export function cashOnCash(annualCashFlow: number, equityInvested: number): number {
  if (equityInvested <= 0) throw new Error("equity_invested must be positive");
  return annualCashFlow / equityInvested;
}

export function debtServiceCoverageRatio(noi: number, debtService: number): number {
  if (debtService <= 0) throw new Error("debt_service must be positive");
  return noi / debtService;
}

export function grossRentMultiplier(price: number, gprAnnual: number): number {
  if (gprAnnual <= 0) throw new Error("gross_potential_rent_annual must be positive");
  return price / gprAnnual;
}

export function operatingExpenseRatio(opex: number, egi: number): number {
  if (egi <= 0) throw new Error("egi must be positive");
  return opex / egi;
}

export function breakEvenOccupancy(opex: number, debtService: number, gprAnnual: number): number {
  if (gprAnnual <= 0) throw new Error("gross_potential_rent_annual must be positive");
  return (opex + debtService) / gprAnnual;
}

export function loanToValue(loan: number, value: number): number {
  if (value <= 0) throw new Error("value must be positive");
  return loan / value;
}

// --- multi-year pro forma (cashflow.py) --------------------------------------

export function opexForYear(
  price: number,
  egiYear: number,
  hoaMonthly: number,
  a: Assumptions,
  yearIndex: number,
): number {
  const valueT = price * (1 + a.appreciation_annual) ** yearIndex;
  const costInflator = (1 + a.cost_inflation_annual) ** yearIndex;
  const propertyTax = valueT * a.property_tax_rate_of_value;
  const insurance = a.insurance_annual * costInflator;
  const hoa = hoaMonthly * MONTHS_PER_YEAR * costInflator;
  const utilities = a.owner_paid_utilities_monthly * MONTHS_PER_YEAR * costInflator;
  const management = egiYear * a.property_management_fraction;
  const maintenance = egiYear * a.maintenance_reserve_fraction;
  return propertyTax + insurance + hoa + utilities + management + maintenance;
}

export function noiForYear(
  price: number,
  monthlyRent: number,
  hoaMonthly: number,
  a: Assumptions,
  yearIndex: number,
): number {
  const rentT = monthlyRent * (1 + a.rent_growth_annual) ** yearIndex;
  const egiT = effectiveGrossIncome(rentT, a.vacancy_rate, a.other_income_fraction);
  return egiT - opexForYear(price, egiT, hoaMonthly, a, yearIndex);
}

export function projectProforma(
  price: number,
  monthlyRent: number,
  hoaMonthly: number,
  a: Assumptions,
  debtService: number,
): ProformaRow[] {
  const rows: ProformaRow[] = [];
  for (let year = 1; year <= a.hold_years; year++) {
    const idx = year - 1;
    const rentT = monthlyRent * (1 + a.rent_growth_annual) ** idx;
    const egiT = effectiveGrossIncome(rentT, a.vacancy_rate, a.other_income_fraction);
    const opexT = opexForYear(price, egiT, hoaMonthly, a, idx);
    const noiT = egiT - opexT;
    rows.push({
      year,
      gross_potential_rent: rentT * MONTHS_PER_YEAR,
      egi: egiT,
      opex: opexT,
      noi: noiT,
      debt_service: debtService,
      levered_cash_flow: noiT - debtService,
    });
  }
  return rows;
}

export interface Reversion {
  exit_cap: number;
  noi_next: number;
  sale_price: number;
  selling_costs: number;
  loan_balance: number;
  terminal_basis: "exit-cap" | "appreciation";
  net_reversion: number;
}

export function reversion(
  price: number,
  monthlyRent: number,
  hoaMonthly: number,
  a: Assumptions,
  goingInCap: number,
  loan: number,
): Reversion {
  const exitCap = goingInCap + a.exit_cap_spread;
  const noiNext = noiForYear(price, monthlyRent, hoaMonthly, a, a.hold_years);
  let salePrice: number;
  let terminalBasis: "exit-cap" | "appreciation";
  if (noiNext > 0) {
    salePrice = noiNext / exitCap;
    terminalBasis = "exit-cap";
  } else {
    salePrice = price * (1 + a.appreciation_annual) ** a.hold_years;
    terminalBasis = "appreciation";
  }
  const sellingCosts = salePrice * a.selling_cost_fraction;
  const loanBalance = remainingBalance(
    loan,
    a.mortgage_rate_annual,
    a.amortization_years,
    a.hold_years * MONTHS_PER_YEAR,
  );
  return {
    exit_cap: exitCap,
    noi_next: noiNext,
    sale_price: salePrice,
    selling_costs: sellingCosts,
    loan_balance: loanBalance,
    terminal_basis: terminalBasis,
    net_reversion: salePrice - sellingCosts - loanBalance,
  };
}

/** Net present value; cashflows[0] is the undiscounted t=0 flow (matches numpy_financial.npv). */
export function npv(rate: number, cashflows: number[]): number {
  return cashflows.reduce((acc, cf, t) => acc + cf / (1 + rate) ** t, 0);
}

// --- top-level evaluation (evaluate.py) --------------------------------------

export function evaluateProperty(
  price: number,
  monthlyRent: number,
  hoaMonthly: number,
  a: Assumptions,
): EvaluateResult {
  const gpr = grossPotentialRent(monthlyRent);
  const egi = effectiveGrossIncome(monthlyRent, a.vacancy_rate, a.other_income_fraction);
  const opex = opexForYear(price, egi, hoaMonthly, a, 0);
  const noi = egi - opex;
  const goingInCap = capRate(noi, price);

  const loan = price * (1 - a.down_payment_fraction);
  const debtService = annualDebtService(loan, a.mortgage_rate_annual, a.amortization_years);
  const equity = cashInvested(price, a.down_payment_fraction, a.closing_cost_fraction);
  const annualCf = preTaxCashFlow(noi, debtService);

  const proforma = projectProforma(price, monthlyRent, hoaMonthly, a, debtService);
  const rev = reversion(price, monthlyRent, hoaMonthly, a, goingInCap, loan);

  // Only the levered stream is consumed (for NPV); unlevered/levered IRR is
  // Python-only (see header), so the unlevered cash-flow array is not built here.
  const leveredCfs = [-equity, ...proforma.map((r) => r.levered_cash_flow)];
  leveredCfs[leveredCfs.length - 1] += rev.net_reversion;

  // Equity multiple via the capital-calls method (matches evaluate.py): interim
  // negative cash flows are additional equity in; distributions are positive CFs
  // plus net sale proceeds.
  const operatingCfs = proforma.map((r) => r.levered_cash_flow);
  const totalEquityIn = equity + operatingCfs.filter((cf) => cf < 0).reduce((s, cf) => s - cf, 0);
  const totalDistributions =
    operatingCfs.filter((cf) => cf > 0).reduce((s, cf) => s + cf, 0) +
    Math.max(rev.net_reversion, 0);
  const equityMultiple = totalEquityIn > 0 ? totalDistributions / totalEquityIn : NaN;

  return {
    price,
    monthly_rent: monthlyRent,
    hoa_monthly: hoaMonthly,
    gross_potential_rent: gpr,
    egi,
    opex,
    noi,
    going_in_cap: goingInCap,
    cap_rate_spread: goingInCap - a.treasury_10y,
    loan,
    equity_invested: equity,
    annual_debt_service: debtService,
    annual_cash_flow: annualCf,
    monthly_cash_flow: annualCf / MONTHS_PER_YEAR,
    cash_on_cash: cashOnCash(annualCf, equity),
    dscr: debtServiceCoverageRatio(noi, debtService),
    grm: grossRentMultiplier(price, gpr),
    oer: operatingExpenseRatio(opex, egi),
    break_even_occupancy: breakEvenOccupancy(opex, debtService, gpr),
    ltv: loanToValue(loan, price),
    levered_irr: null,
    unlevered_irr: null,
    npv: npv(a.discount_rate, leveredCfs),
    equity_multiple: equityMultiple,
    total_equity_in: totalEquityIn,
    terminal_basis: rev.terminal_basis,
    exit_cap: rev.exit_cap,
    sale_price: rev.sale_price,
    net_reversion: rev.net_reversion,
    proforma,
  };
}

/** Year-0 monthly carrying-cost breakdown for the deal-memo display (see exporter). */
export function carryMonthly(
  price: number,
  monthlyRent: number,
  hoaMonthly: number,
  a: Assumptions,
): CarryMonthly {
  const loan = price * (1 - a.down_payment_fraction);
  const egiAnnual = effectiveGrossIncome(monthlyRent, a.vacancy_rate, a.other_income_fraction);
  const mortgage = mortgagePayment(loan, a.mortgage_rate_annual, a.amortization_years);
  const tax = (price * a.property_tax_rate_of_value) / MONTHS_PER_YEAR;
  const insurance = a.insurance_annual / MONTHS_PER_YEAR;
  const hoa = hoaMonthly;
  const maintenance = (egiAnnual * a.maintenance_reserve_fraction) / MONTHS_PER_YEAR;
  const management = (egiAnnual * a.property_management_fraction) / MONTHS_PER_YEAR;
  const vacancy = monthlyRent * a.vacancy_rate;
  return {
    mortgage,
    tax,
    insurance,
    hoa,
    maintenance,
    management,
    vacancy,
    total: mortgage + tax + insurance + hoa + maintenance + management + vacancy,
  };
}

// --- scoring (scoring.py) ----------------------------------------------------

export interface ScoringBands {
  dscr: { red_below: number; amber_below: number };
  cash_on_cash: { red_below: number; amber_below: number };
  cap_rate_spread_over_treasury: { red_below: number; amber_below: number };
  break_even_occupancy: { red_above: number; amber_above: number };
  // Present in config/scoring.yaml but not consumed by the composite (UI Tier-3
  // tripwires); typed optional so config.generated.json loads without a wide cast.
  rules_of_thumb?: { one_percent_rule: number; fifty_percent_expense_rule: number };
  composite: {
    light_scores: Record<Light, number>;
    weights: {
      cash_on_cash: number;
      cap_rate_spread: number;
      dscr: number;
      break_even_occupancy: number;
    };
    green_min: number;
    amber_min: number;
  };
}

export interface ScoreResult {
  lights: {
    cash_on_cash: Light;
    dscr: Light;
    cap_rate_spread: Light;
    break_even_occupancy: Light;
  };
  composite_score: number;
  verdict: Verdict;
}

export function lightBelow(value: number, amberBelow: number, redBelow: number): Light {
  if (value < redBelow) return "red";
  if (value < amberBelow) return "amber";
  return "green";
}

export function lightAbove(value: number, amberAbove: number, redAbove: number): Light {
  if (value > redAbove) return "red";
  if (value > amberAbove) return "amber";
  return "green";
}

export function scoreProperty(metrics: EvaluateResult, s: ScoringBands): ScoreResult {
  const coc = lightBelow(
    metrics.cash_on_cash,
    s.cash_on_cash.amber_below,
    s.cash_on_cash.red_below,
  );
  const dscr = lightBelow(metrics.dscr, s.dscr.amber_below, s.dscr.red_below);
  const spread = lightBelow(
    metrics.cap_rate_spread,
    s.cap_rate_spread_over_treasury.amber_below,
    s.cap_rate_spread_over_treasury.red_below,
  );
  const beo = lightAbove(
    metrics.break_even_occupancy,
    s.break_even_occupancy.amber_above,
    s.break_even_occupancy.red_above,
  );
  const ls = s.composite.light_scores;
  const w = s.composite.weights;
  const composite =
    ls[coc] * w.cash_on_cash +
    ls[spread] * w.cap_rate_spread +
    ls[dscr] * w.dscr +
    ls[beo] * w.break_even_occupancy;
  let verdict: Verdict = "NO-GO";
  if (composite >= s.composite.green_min) verdict = "GO";
  else if (composite >= s.composite.amber_min) verdict = "WATCH";
  return {
    lights: { cash_on_cash: coc, dscr, cap_rate_spread: spread, break_even_occupancy: beo },
    composite_score: composite,
    verdict,
  };
}
