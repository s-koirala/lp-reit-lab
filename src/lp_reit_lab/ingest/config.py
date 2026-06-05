"""Ingestion configuration — thresholds, URLs, and codes with cited rationale.

No magic numbers live elsewhere in the ingest package; every constant here carries
a source comment. Engineering knobs (page size, retry/backoff) are documented
operational defaults, not analytic parameters.
"""

from __future__ import annotations

from dataclasses import dataclass

# Chicago community-area codes (City of Chicago / CMAP, 1-77). The Parcel Universe
# field `chicago_community_area_num` stores these UN-PADDED as strings ("7", not "07").
# Source: Cook County Assessor Parcel Universe (nj4t-kc8j); Chicago community areas.
TARGET_COMMUNITY_AREAS: dict[str, str] = {
    "6": "LAKE VIEW",
    "7": "LINCOLN PARK",
    "8": "NEAR NORTH SIDE",
}
# Secondary ZIP filter (ZIPs straddle community-area boundaries — use as cross-check).
TARGET_ZIPS: tuple[str, ...] = ("60614", "60657", "60610")


@dataclass(frozen=True)
class SocrataConfig:
    """Cook County Assessor open datasets (Socrata SODA 2.1)."""

    domain: str = "datacatalog.cookcountyil.gov"
    parcel_sales_id: str = "wvhk-k5uv"          # Assessor Parcel Sales
    characteristics_id: str = "x54s-btds"        # SF/MF (<7-unit) Improvement Characteristics
    parcel_universe_id: str = "nj4t-kc8j"        # Parcel Universe (geography spine)
    # SODA 2.0 max page size; safe under 2.1. Source: dev.socrata.com/docs/queries/limit.
    page_size: int = 50_000
    pin_chunk: int = 500          # PINs per server-side `in(...)` clause
    courtesy_sleep_s: float = 0.1  # gap between pages; well under any rate limit

    def resource_url(self, resource_id: str) -> str:
        return f"https://{self.domain}/resource/{resource_id}.json"

    def metadata_url(self, resource_id: str) -> str:
        """Socrata view metadata (carries `rowsUpdatedAt` = the dataset version)."""
        return f"https://{self.domain}/api/views/{resource_id}.json"


@dataclass(frozen=True)
class CookCountyBounds:
    """Validation envelope for Cook County ingested rows."""

    # Approx Cook County, IL geographic bounding box (lat/lon sanity bounds).
    lat_min: float = 41.4
    lat_max: float = 42.2
    lon_min: float = -88.3
    lon_max: float = -87.5
    # Parcel Sales coverage start (CCAO documents 1999-present).
    sales_epoch_start: str = "1999-01-01"
    beds_min: int = 0
    beds_max: int = 10
    # At or below this, a "sale" is a non-arms-length nominal transfer. CCAO's
    # sale_filter_less_than_10k flags sale_price <= 10000; the `> min` condition is a
    # redundant defensive cross-check. Source: CCAO sale-validation (ccao-data).
    min_arms_length_price: int = 10_000


@dataclass(frozen=True)
class Assessment:
    """Assessed-value → implied-market-value factors (Class 2 residential)."""

    # Class 2 residential level of assessment = 10% of fair market value.
    # Source: Cook County Assessor; Civic Federation assessment primer.
    level_of_assessment: float = 0.10
    # IDOR final 2024 Cook County equalizer (assessment-year-specific; do not reuse).
    # Source: tax.illinois.gov 2024 Cook County Final Multiplier.
    state_equalizer_2024: float = 3.0355
    # Homeowner exemption reduces EAV (not market value); owner-occupied only.
    homeowner_exemption_eav: int = 10_000


@dataclass(frozen=True)
class RetryConfig:
    """HTTP retry/backoff operational defaults (transport + application layer)."""

    max_attempts: int = 5
    backoff_factor: float = 0.5
    backoff_jitter: float = 0.3
    initial_wait_s: float = 1.0
    max_wait_s: float = 30.0
    jitter_s: float = 1.0
    connect_timeout_s: float = 10.0
    # Large Socrata geography scans (124-col Parcel Universe) are slow without an
    # app token; allow generous read time. Production pulls should set SOCRATA_APP_TOKEN.
    read_timeout_s: float = 120.0


# RFC 7231/6585 transient statuses — retry these only (never 4xx auth/not-found).
RETRY_STATUSES: frozenset[int] = frozenset({408, 425, 429, 500, 502, 503, 504})
