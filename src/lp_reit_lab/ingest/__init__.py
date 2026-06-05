"""Reproducible, point-in-time real-estate data ingestion.

Open/free-first sources (ADR-0001): Cook County Assessor (Socrata), Census ACS,
FHFA HPI, Zillow/Redfin research files. Discipline (research memo §6, §9, §11):
- pandera schema validation at the raw→processed gate (`schemas.py`);
- content-addressed SHA-256 checksums in an ingestion manifest
  (`data/processed/_provenance/ingest_manifest.json`, written by `scripts/ingest.py`;
  distinct from the committed-dataset `data/_manifest.json` — see ADR-0001);
- no look-ahead — `sale_date` bounded by the pull snapshot; deterministic `$order`
  + pinned CSV serialization so re-pulls are byte-reproducible;
- money with fractional precision uses integer cents (`money.py`); whole-dollar
  ingested amounts (`sale_price`) stay int64 USD;
- all thresholds/URLs/codes live in `config.py` with a cited rationale.
"""
