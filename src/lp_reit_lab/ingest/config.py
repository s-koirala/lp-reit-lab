"""Ingestion configuration — thresholds, URLs, and codes with cited rationale.

No magic numbers live elsewhere in the ingest package; every constant here carries
a source comment. Engineering knobs (page size, retry/backoff) are documented
operational defaults, not analytic parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict

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
class SocrataDomain:
    """One Socrata portal: shared URL builders + pagination knobs.

    `page_size` = SODA 2.0 max page size, safe under 2.1 (source:
    dev.socrata.com/docs/queries/limit). `courtesy_sleep_s` = 0.1s inter-page
    gap => <=10 req/s burst, far below the documented per-hour throttle for
    keyless clients (source: dev.socrata.com/docs/app-tokens, throttling).
    """

    domain: str
    page_size: int = 50_000
    courtesy_sleep_s: float = 0.1

    def resource_url(self, resource_id: str) -> str:
        return f"https://{self.domain}/resource/{resource_id}.json"

    def metadata_url(self, resource_id: str) -> str:
        """Socrata view metadata (carries `rowsUpdatedAt` = the dataset version)."""
        return f"https://{self.domain}/api/views/{resource_id}.json"

    def geospatial_export_url(self, resource_id: str) -> str:
        """Geospatial export endpoint for a true geo DATASET id.

        Only valid for dataset-type assets: a `visualization_canvas_map`
        wrapper id returns a truncated 53-byte skeleton here (audit finding
        F-1-1, probed 2026-07-06) — resolve wrappers to their parent dataset
        first (see CPS_BOUNDARY_VINTAGES, which pins parents only).
        """
        return (f"https://{self.domain}/api/geospatial/{resource_id}"
                "?method=export&format=GeoJSON")


@dataclass(frozen=True)
class SocrataConfig(SocrataDomain):
    """Cook County Assessor open datasets (Socrata SODA 2.1)."""

    domain: str = "datacatalog.cookcountyil.gov"
    parcel_sales_id: str = "wvhk-k5uv"          # Assessor Parcel Sales
    characteristics_id: str = "x54s-btds"        # SF/MF (<7-unit) Improvement Characteristics
    parcel_universe_id: str = "nj4t-kc8j"        # Parcel Universe (geography spine)
    pin_chunk: int = 500          # PINs per server-side `in(...)` clause


@dataclass(frozen=True)
class ChicagoPortalConfig(SocrataDomain):
    """City of Chicago open-data portal (Socrata SODA 2.1) — H002 auxiliaries.

    Dataset IDs verified live against the portal on 2026-07-06 (catalog API
    `api.us.socrata.com/api/catalog/v1?domains=data.cityofchicago.org`).
    """

    domain: str = "data.cityofchicago.org"
    building_permits_id: str = "ydr8-5enu"   # Building Permits (2006-present, probed)


BoundaryLevel = Literal["elementary", "high_school"]

# CPS attendance-boundary vintages, school year -> geo DATASET id, per level.
# One vintage per school year is REQUIRED for point-in-time boundary assignment
# (H002 design.md §2 roll-handling: "point-in-polygon assignment uses the boundary
# vintage in force on the sale_date, not the current boundary"). Discovered from
# the Socrata catalog API (q="attendance", 178 results) on 2026-07-06; the two
# design-cited ids (elementary `u959-tya7`, high-school `fkiq-5i7q`) are the
# portal's undated "current"/SY2223-map aliases of the same layer family — the
# dated per-vintage ids below supersede them for point-in-time work.
# SY0607–SY1819 catalog entries are `visualization_canvas_map` WRAPPERS whose
# export truncates (audit F-1-1); the ids pinned here are their PARENT datasets,
# resolved live 2026-07-06 via api/views/{wrapper}.json
# displayFormat.visualizationCanvasMetadata.vifs[].series[].dataSource.datasetUid
# (wrapper ids retained in CPS_BOUNDARY_WRAPPERS for provenance). All 40 pinned
# ids verified live 2026-07-06: upstream dataset name matches both the school
# year and the level (the same binding the connector re-asserts on every pull).
# Coverage floor: no vintage exists before SY0607, so sales dated before the
# 2006-07 school year cannot be side-labelled point-in-time (freeze-time filter).
CPS_BOUNDARY_VINTAGES: dict[str, dict[BoundaryLevel, str]] = {
    #  SY        elementary     high_school
    "SY0607": {"elementary": "asie-aked", "high_school": "icxs-hp99"},
    "SY0708": {"elementary": "xyyf-bnfu", "high_school": "vq9d-qgdn"},
    "SY0809": {"elementary": "48tf-ubnt", "high_school": "5mbh-yu9n"},
    "SY0910": {"elementary": "j9ch-yf5i", "high_school": "up9a-4856"},
    "SY1011": {"elementary": "d5vw-2kcs", "high_school": "it84-h78n"},
    "SY1112": {"elementary": "hr9c-szde", "high_school": "sp5c-ihm9"},
    "SY1213": {"elementary": "h8qh-dq5s", "high_school": "s2in-k2mg"},
    "SY1314": {"elementary": "sege-i4a9", "high_school": "kuh7-icv2"},
    "SY1415": {"elementary": "mvv3-naxt", "high_school": "94tp-gppc"},
    "SY1516": {"elementary": "ppjj-9kn7", "high_school": "i8xf-caea"},
    "SY1617": {"elementary": "ciye-b75s", "high_school": "negq-mr8b"},
    "SY1718": {"elementary": "n45m-yz4n", "high_school": "juf9-y87b"},
    "SY1819": {"elementary": "rau8-hz9p", "high_school": "se26-22jn"},
    "SY1920": {"elementary": "abk6-gwwr", "high_school": "d95y-ue9h"},
    "SY2021": {"elementary": "gaak-qc7r", "high_school": "da2c-wnfg"},
    "SY2122": {"elementary": "a3xm-ett9", "high_school": "is3f-j4ke"},
    "SY2223": {"elementary": "d8hd-y5ce", "high_school": "4m25-hh4h"},
    "SY2324": {"elementary": "8k6e-w34s", "high_school": "gba7-ip5a"},
    "SY2425": {"elementary": "5ihw-cbdn", "high_school": "4kfz-zr3a"},
    "SY2526": {"elementary": "x72b-38qv", "high_school": "xg7c-d8rm"},
}

# Catalog wrapper ids for the legacy vintages (SY0607–SY1819): what the portal
# catalog lists, kept for provenance/documentation only — NEVER pulled from.
CPS_BOUNDARY_WRAPPERS: dict[str, dict[BoundaryLevel, str]] = {
    "SY0607": {"elementary": "qbay-3nnc", "high_school": "rwav-ux96"},
    "SY0708": {"elementary": "r2h7-fxir", "high_school": "wifq-a78y"},
    "SY0809": {"elementary": "8jx5-pt46", "high_school": "fede-88y6"},
    "SY0910": {"elementary": "sra3-5rba", "high_school": "csqr-8bm8"},
    "SY1011": {"elementary": "7jn2-4muy", "high_school": "4ytu-3pkn"},
    "SY1112": {"elementary": "6tkx-ju8g", "high_school": "s7sc-q48d"},
    "SY1213": {"elementary": "rfrd-v47v", "high_school": "9xc2-zddf"},
    "SY1314": {"elementary": "g7sv-g285", "high_school": "azwk-fxgp"},
    "SY1415": {"elementary": "e75y-e6uw", "high_school": "47bj-3f4s"},
    "SY1516": {"elementary": "asty-4xrr", "high_school": "vff3-x5qg"},
    "SY1617": {"elementary": "acyp-2sus", "high_school": "bwum-4mhg"},
    "SY1718": {"elementary": "7edu-z2e8", "high_school": "y9da-bb2y"},
    "SY1819": {"elementary": "whkz-sk6f", "high_school": "bv6n-449d"},
}

# Building Permits dataset coverage start. Probed live 2026-07-06:
# min(issue_date) over community areas 6/7/8 = 2006-01-03; floored to the year
# start because an inclusive `>=` lower bound strictly before the probed min is
# harmless and stays stable if upstream backfills early-2006 rows. Pairs whose
# first sale predates this cannot be renovation-flagged point-in-time
# (freeze-time caveat).
PERMITS_EPOCH: str = "2006-01-01"

# Building Permits columns pulled. Deliberately EXCLUDES the contact_* fields
# (personal names/addresses of owners and contractors) — data minimization; the
# renovation flag (H002 design.md §3 `reno_permit_flag`) needs dates, type, cost,
# and the parcel key only. `pin_list` carries semicolon/comma-joined 10-digit PIN
# prefixes (CCAO `pin10`) — the permit->parcel join key.
PERMIT_SELECT_COLS: tuple[str, ...] = (
    "id", "permit_", "permit_type", "review_type", "application_start_date",
    "issue_date", "work_description", "reported_cost", "pin_list",
    "community_area", "census_tract", "ward", "latitude", "longitude",
)


class ReportCardFiles(TypedDict):
    """One ISBE report-card year: canonical data URL, optional layout, sha pin."""

    data: str
    layout: str | None
    sha256: str


# ISBE Report Card public data sets — one canonical file per report-card year.
# URLs are NOT templatable (naming churns yearly: rc{yy}.zip era with ad-hoc
# suffixes, then four different xlsx name patterns 2018-2025), so the map is
# pinned explicitly. Verification 2026-07-06: all 20 data files + 12 layout
# files DOWNLOADED in full and container-validated (ZIP magic), shas below
# (supersedes the initial 18-URL HEAD sweep). rc label year N = school year
# (N-1)-N, e.g. rc07 = SY2006-07 (the first CPS boundary vintage). Coverage is
# aligned to the boundary-vintage floor (SY0607): earlier report cards exist
# (back to 1997) but no boundary vintage exists to join them to.
# 2015-2017 trap: the base rc{15,16,17}.zip files EXCLUDE assessment data; the
# canonical full sets are the *-assessment variants pinned here. `layout` is
# the record layout for the zip-era semicolon-delimited txt; the 2018+ xlsx
# era is self-describing (no positional layout published).
# `sha256` = expected digest of the data file, pinned from the 2026-07-06
# landing: ISBE files carry no version signal and the 2018 URL is undated, so
# a re-pull that no longer matches fails loudly instead of silently swapping
# vintage content (audit F-1-3). An upstream RESTATEMENT therefore requires an
# explicit re-pin here — that is the intended friction.
ISBE_REPORT_CARD_FILES: dict[int, ReportCardFiles] = {
    2006: {"data": "https://www.isbe.net/Documents/rc06.zip",
           "layout": "https://www.isbe.net/Documents/RC06_layout.xls",
           "sha256": "1335d9f7f2de95dffafae5e764148f62a262cb801ecef69a9e8228fdaaad3e88"},
    2007: {"data": "https://www.isbe.net/Documents/rc07.zip",
           "layout": "https://www.isbe.net/Documents/RC07_layout.xls",
           "sha256": "a53999769a3d62cb6bc14b56cedf41b38d4ffeb8c64e715747b25df0f3b224ba"},
    2008: {"data": "https://www.isbe.net/Documents/rc08u.zip",
           "layout": "https://www.isbe.net/Documents/RC08_layout.xls",
           "sha256": "b4b5b8d1ef08a9a79c8304d26b7c85ea327aae1ea0d66c1013e0f4e52c9d3fbd"},
    2009: {"data": "https://www.isbe.net/Documents/rc09.zip",
           "layout": "https://www.isbe.net/Documents/RC09_layout.xls",
           "sha256": "37e018902d8c610d811ee070e8a08845f24cd426eb619906a5ce6a8233e056db"},
    2010: {"data": "https://www.isbe.net/Documents/rc10.zip",
           "layout": "https://www.isbe.net/Documents/RC10_layout.xls",
           "sha256": "f6128079b839709db98850a0914a85dd99f78874700b6fbd6b2f1fe36168e6f9"},
    2011: {"data": "https://www.isbe.net/Documents/rc11.zip",
           "layout": "https://www.isbe.net/Documents/RC11_layout.xls",
           "sha256": "abdadfed576e012e1673ac515f4ec2fe36d8babfcca7ec5962052f1b9ad076a5"},
    2012: {"data": "https://www.isbe.net/Documents/rc12.zip",
           "layout": "https://www.isbe.net/Documents/RC12-layout.xls",
           "sha256": "3f802800a3595bea09412c20a29c713cb6385f9a5a463dd2f25e7b3aef22b2f0"},
    2013: {"data": "https://www.isbe.net/Documents/rc13.zip",
           "layout": "https://www.isbe.net/Documents/RC13_layout.xlsx",
           "sha256": "eb99061a03431e45033e93d007dae558f681885230b0b7579270e9c5869f26d7"},
    2014: {"data": "https://www.isbe.net/Documents/rc14.zip",
           "layout": "https://www.isbe.net/Documents/RC14_layout.xlsx",
           "sha256": "b5b7447e41191fca96ad9f0398950f7f3f4ab4c8ecf94a52244ba4e3de9fbfdf"},
    2015: {"data": "https://www.isbe.net/Documents/rc15-assessment.zip",
           "layout": "https://www.isbe.net/Documents/RC15-layout.xlsx",
           "sha256": "539d51240ab8d939023b61873c68e1d0c4b4615609d53a58afaa0a87cb695d1b"},
    2016: {"data": "https://www.isbe.net/Documents/rc16_assessment.zip",
           "layout": "https://www.isbe.net/Documents/RC16-layout.xlsx",
           "sha256": "15dabc6099a63c2b22813dd42d18fc19cdec6bae4b3933c220b4eb3ea41357a9"},
    2017: {"data": "https://www.isbe.net/Documents/rc17_assessment.zip",
           "layout": "https://www.isbe.net/Documents/RC17_layout.xlsx",
           "sha256": "37f495b3a89721af9ee851f2bc87b3a13b0ad676f6a7595d6a5f7596827082bf"},
    2018: {"data": "https://www.isbe.net/Documents/Report-Card-Public-Data-Set.xlsx",
           "layout": None,
           "sha256": "35b96aa88033591d01eb220f363ebfec4582401abb6a6684d385a2528e2243ac"},
    2019: {"data": "https://www.isbe.net/Documents/2019-Report-Card-Public-Data-Set.xlsx",
           "layout": None,
           "sha256": "071913dbc531560f24abadc80670d0a4728a33a225f9f959c9515b11429ae436"},
    2020: {"data": "https://www.isbe.net/Documents/2020-Report-Card-Public-Data-Set.xlsx",
           "layout": None,
           "sha256": "14a38185fa41565acd2a52662cbd87d485cbb7396d37f7f8e16bd79b8d79a99b"},
    2021: {"data": "https://www.isbe.net/Documents/2021-RC-Pub-Data-Set.xlsx",
           "layout": None,
           "sha256": "b0a1a4fcfa51514e7f5e15562d395367b1c36d27dd4abe2ae9b16119e4fd8864"},
    2022: {"data": "https://www.isbe.net/Documents/2022-Report-Card-Public-Data-Set.xlsx",
           "layout": None,
           "sha256": "6575e1b5bfbb8a133c763d4b93273cc75749b9bfc8289420b2ef226318e08a1d"},
    2023: {"data": "https://www.isbe.net/Documents/23-RC-Pub-Data-Set.xlsx",
           "layout": None,
           "sha256": "951536d6f81cdfdebb75e41775d0d80cde37bdd81fe256a6f31e2e571b7088ba"},
    2024: {"data": "https://www.isbe.net/Documents/24-RC-Pub-Data-Set.xlsx",
           "layout": None,
           "sha256": "bab4981cd42a5355cfa8a62515b8364b981ff5e2397f4521deb0061034befa29"},
    2025: {"data": "https://www.isbe.net/Documents/2025-Report-Card-Public-Data-Set.xlsx",
           "layout": None,
           "sha256": "459ac146b52bafe7ce79fd76a95a65daa68d0472cce5205fa777cde19fb58cdf"},
}

# Chicago Public Schools district RCDTS prefix (City of Chicago SD 299) — the
# row filter for school-level records in every ISBE file era. Structure is
# region(2)-county(3)-district(4): 15-016-2990. Source: ISBE Report Card RCDTS
# field convention (full district code 15-016-2990-25); see the rc-year layout
# files landed under data/raw/isbe_report_card/ and isbe.net entity lookup.
CPS_RCDTS_DISTRICT_PREFIX: str = "150162990"


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


# Transient statuses — retry these only (never 4xx auth/not-found).
# Sources: RFC 9110 (408, 5xx), RFC 6585 (429), RFC 8470 (425).
RETRY_STATUSES: frozenset[int] = frozenset({408, 425, 429, 500, 502, 503, 504})
