// Public entry for the deterministic finance engine. Loads the runtime config
// generated from the canonical Python sources (config/assumptions.yaml,
// config/scoring.yaml) by scripts/export_web_engine_fixtures.py, so the TS app
// and the Python engine evaluate identical assumptions. Do not edit
// config.generated.json by hand — re-run the exporter.

import config from "./config.generated.json";
import type { Assumptions, ScoringBands } from "./engine";

export * from "./engine";

export const ASSUMPTIONS = config.assumptions as Assumptions;
export const SCORING = config.scoring as ScoringBands;
