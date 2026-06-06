import { afterAll, describe, expect, it } from "vitest";

import goldenJson from "./__fixtures__/golden_vectors.json";
import {
  annualDebtService,
  carryMonthly,
  evaluateProperty,
  projectProforma,
  scoreProperty,
  type Assumptions,
  type ScoringBands,
} from "./engine";
import { ASSUMPTIONS, SCORING } from "./index";

type Case = {
  input: { price: number; monthly_rent: number; hoa_monthly: number };
  expected: Record<string, number | string | null>;
  carry_monthly: Record<string, number>;
  proforma: Array<Record<string, number>>;
  score: { verdict: string; composite_score: number; lights: Record<string, string> };
};

const golden = goldenJson as unknown as {
  assumptions: Assumptions;
  scoring: ScoringBands;
  cases: Case[];
};

// Parity tolerance: both engines use IEEE-754 doubles with identical formulas, so
// any residual is floating-point noise (observed max relative residual ~6.6e-16,
// ~3 ULP; logged in afterAll). Combined numpy.isclose-form criterion
// |a-e| <= ATOL + RTOL*|e| so near-zero fields (cap_rate_spread, net_reversion)
// have an absolute floor rather than an unstable pure-relative error. RTOL matches
// the Python side's rel=1e-9 discipline (tests/test_finance_metrics.py).
const RTOL = 1e-9;
const ATOL = 1e-9;
// IRR is Python-only (numpy_financial root selection is not reproducible for the
// cash-flow-negative, sign-changing LP streams); proforma rows are asserted
// separately from the scalar outputs.
const SKIP = new Set(["levered_irr", "unlevered_irr", "proforma"]);

let maxResidual = 0;
function close(actual: number, expected: number): boolean {
  const diff = Math.abs(actual - expected);
  const rel = Math.abs(expected) === 0 ? diff : diff / Math.abs(expected);
  if (rel > maxResidual) maxResidual = rel;
  return diff <= ATOL + RTOL * Math.abs(expected);
}

describe("TS engine parity vs Python golden vectors", () => {
  it("runtime config matches the golden-vector oracle config", () => {
    expect(ASSUMPTIONS).toEqual(golden.assumptions);
    expect(SCORING).toEqual(golden.scoring);
  });

  // Pin reversion-branch coverage: both the exit-cap (NOI>0) and appreciation
  // (NOI<=0 fallback) terminal bases must stay represented, so a future CASES
  // edit can't silently de-cover the appreciation branch.
  it("golden vectors cover both reversion terminal bases", () => {
    const bases = new Set(golden.cases.map((c) => c.expected.terminal_basis));
    expect(bases.has("exit-cap")).toBe(true);
    expect(bases.has("appreciation")).toBe(true);
  });

  for (const c of golden.cases) {
    const { price, monthly_rent, hoa_monthly } = c.input;
    it(`evaluate ${price}/${monthly_rent}/${hoa_monthly}`, () => {
      const ev = evaluateProperty(price, monthly_rent, hoa_monthly, golden.assumptions);
      const evRec = ev as unknown as Record<string, number | string | null>;

      for (const [k, exp] of Object.entries(c.expected)) {
        // every gated expected key must exist on the result (catches a renamed/
        // dropped field silently losing coverage)
        expect(k in evRec).toBe(true);
        if (SKIP.has(k)) continue;
        if (typeof exp === "number") {
          expect(close(evRec[k] as number, exp)).toBe(true);
        } else if (exp === null) {
          const v = evRec[k];
          expect(v === null || (typeof v === "number" && Number.isNaN(v))).toBe(true);
        } else {
          expect(evRec[k]).toEqual(exp); // strings, e.g. terminal_basis
        }
      }

      const carry = carryMonthly(
        price,
        monthly_rent,
        hoa_monthly,
        golden.assumptions,
      ) as unknown as Record<string, number>;
      for (const [k, exp] of Object.entries(c.carry_monthly)) {
        expect(close(carry[k], exp)).toBe(true);
      }

      const loan = price * (1 - golden.assumptions.down_payment_fraction);
      const ds = annualDebtService(
        loan,
        golden.assumptions.mortgage_rate_annual,
        golden.assumptions.amortization_years,
      );
      const pf = projectProforma(price, monthly_rent, hoa_monthly, golden.assumptions, ds);
      expect(pf.length).toBe(c.proforma.length);
      pf.forEach((row, i) => {
        const r = row as unknown as Record<string, number>;
        for (const [k, exp] of Object.entries(c.proforma[i])) {
          expect(close(r[k], exp)).toBe(true);
        }
      });

      const sc = scoreProperty(ev, golden.scoring);
      expect(sc.verdict).toBe(c.score.verdict);
      expect(sc.lights).toEqual(c.score.lights);
      expect(close(sc.composite_score, c.score.composite_score)).toBe(true);
    });
  }

  afterAll(() => {
    // eslint-disable-next-line no-console
    console.log(
      `[engine parity] max relative residual = ${maxResidual.toExponential(3)} (RTOL ${RTOL}, ATOL ${ATOL})`,
    );
  });
});
