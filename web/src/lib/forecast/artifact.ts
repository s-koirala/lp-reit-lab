// Forecast / Monte-Carlo artifact contract (P5).
//
// ADR-0003: forecasting + MC run in the Python venv (where emit-repro-log fires)
// and the SPA renders the PRECOMPUTED artifact — never computing forecasts in the
// browser. The real compiler is DEFERRED: it is pre-registration-governed (the
// hypotheses H001–H004 must be frozen + a power analysis run before any model is
// fitted on real data). Until then this module defines the artifact SCHEMA (the
// contract the compiler must emit) and a clearly-labelled illustrative SAMPLE so
// the stub view can be built. When the compiler lands, it emits artifacts of this
// exact shape with status "fitted", replacing buildSampleForecast.

import type { Property } from "@/lib/data/properties";

export const FORECAST_SCHEMA_VERSION = "0.1.0";

export interface PercentileBand {
  p10: number;
  p50: number;
  p90: number;
}

export interface ForecastYear {
  year: number;
  /** Cumulative appreciation from t0 (fraction), as a predictive band. */
  cumReturn: PercentileBand;
}

export interface ForecastArtifact {
  schemaVersion: string;
  /** "sample" until the real model is fitted; the UI must not present a sample as a forecast. */
  status: "sample" | "fitted";
  propertyId: string;
  /** ISO timestamp of the compiler run; null for samples (no real run). */
  generatedAt: string | null;
  horizonYears: number;
  appreciationPath: ForecastYear[];
  monteCarlo: {
    /** Number of MC draws; null for samples. */
    runs: number | null;
    fiveYearReturn: PercentileBand;
    terminalValue: PercentileBand;
  };
  method: string;
  disclaimer: string;
}

export const SAMPLE_DISCLAIMER =
  "Illustrative sample — the forecast model is not yet fitted. Real forecasts (repeat-sales / hedonic index + Monte-Carlo terminal-value simulation) are produced by the Python artifact compiler once data is ingested and the hypotheses (H001–H004) are pre-registered with a power analysis.";

// Derive an illustrative sample artifact from the synthetic property's appreciation
// band. NOT a fitted model — bands simply compound the property's expected /
// low / high CAGR over the horizon. Deterministic; status is always "sample".
// horizonYears defaults to 5 to mirror the appreciation5y CAGR window the
// neighborhood index is defined over (and the deal-memo "5-year outlook" framing).
export function buildSampleForecast(p: Property, horizonYears = 5): ForecastArtifact {
  const cum = (rate: number, year: number) => (1 + rate) ** year - 1;
  const appreciationPath: ForecastYear[] = Array.from({ length: horizonYears }, (_, i) => {
    const year = i + 1;
    return {
      year,
      cumReturn: {
        p10: cum(p.expectedAppreciationLow, year),
        p50: cum(p.expectedAppreciation, year),
        p90: cum(p.expectedAppreciationHigh, year),
      },
    };
  });
  const last = appreciationPath[appreciationPath.length - 1].cumReturn;
  return {
    schemaVersion: FORECAST_SCHEMA_VERSION,
    status: "sample",
    propertyId: p.id,
    generatedAt: null,
    horizonYears,
    appreciationPath,
    monteCarlo: {
      runs: null,
      fiveYearReturn: last,
      terminalValue: {
        p10: p.listPrice * (1 + last.p10),
        p50: p.listPrice * (1 + last.p50),
        p90: p.listPrice * (1 + last.p90),
      },
    },
    method:
      "Sample: compounds the property's expected/low/high appreciation. Real method = repeat-sales/hedonic index + Monte-Carlo terminal-value simulation (deferred, pre-registration-governed).",
    disclaimer: SAMPLE_DISCLAIMER,
  };
}
