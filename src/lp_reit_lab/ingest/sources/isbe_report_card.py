"""ISBE Report Card raw-file ingestion — the H002 `isbe_quality` substrate.

Downloads the canonical per-year Report Card public data set (plus the zip-era
record layout where one exists) as OPAQUE raw files; parsing and the
quality-signal reconstruction (design.md §3 `isbe_quality`) are analysis-stage
concerns whose recipe is pre-specified at freeze, not here. URLs are pinned in
`config.ISBE_REPORT_CARD_FILES` because the naming is not templatable.

Content binding: every data file's sha256 must match the pin recorded in the
config map (frozen from the verified 2026-07-06 landing) — ISBE files carry no
version signal, the 2018 URL is undated, and a silent upstream swap would
otherwise relabel a different year's data as rc2018 (audit F-1-3). The HTTP
Last-Modified header is captured as the only observable source version.

Container validation is structural: data files and .xlsx layouts must open
with the ZIP local-file-header magic (PKWARE APPNOTE.TXT §4.3.7; OOXML is a
zip), legacy .xls layouts with the OLE2 compound-file signature (MS-CFB §2.2).
A soft-404 HTML error page fails either check immediately.

No-look-ahead: a report-card year N is knowable only from its PUBLIC RELEASE,
not from the school year's end. ISBE must prepare the report card by October
31 (105 ILCS 5/10-17a) and releases the public data set in late October of
year N (e.g. 2024 Report Card released 2024-10-30); the conservative
knowability floor is therefore November 1 of year N (audit F-1-2).
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import requests

from ..config import ISBE_REPORT_CARD_FILES
from ..http_client import download_file

# ZIP local file header signature (PKWARE APPNOTE.TXT §4.3.7). xlsx = OOXML = zip.
_ZIP_MAGIC = b"PK\x03\x04"
# OLE2 / Compound File Binary header signature (MS-CFB §2.2). Legacy .xls.
_OLE2_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

# rc year N is publicly knowable from Nov 1 of year N: statutory preparation
# deadline Oct 31 (105 ILCS 5/10-17a) + observed late-October releases.
_RC_RELEASE_MONTH = 10


class LandedFile(NamedTuple):
    """One file landed by fetch_report_card."""

    path: Path
    url: str
    n_bytes: int
    sha256: str
    last_modified: str | None


def report_card_years() -> list[int]:
    """Configured report-card years, ascending."""
    return sorted(ISBE_REPORT_CARD_FILES)


def years_knowable_at(snapshot: str) -> list[int]:
    """Report-card years PUBLICLY RELEASED by the snapshot date.

    Gate is the release date, not the school-year end: between July and late
    October of year N the SY (N-1)-N data exists at ISBE but is not public, so
    admitting it would leak the quality signal into that window (audit F-1-2).
    Knowable <=> snapshot >= Nov 1 of year N.
    """
    year_s, month_s, _ = snapshot.split("-")
    year, month = int(year_s), int(month_s)
    cutoff = year if month > _RC_RELEASE_MONTH else year - 1
    return [n for n in report_card_years() if n <= cutoff]


def validate_zip_container(path: str | Path) -> None:
    """Fail unless `path` starts with the ZIP magic and is non-empty."""
    _validate_magic(path, _ZIP_MAGIC, "ZIP container")


def validate_ole2_container(path: str | Path) -> None:
    """Fail unless `path` starts with the OLE2 compound-file magic."""
    _validate_magic(path, _OLE2_MAGIC, "OLE2 compound file")


def _validate_magic(path: str | Path, magic: bytes, kind: str) -> None:
    p = Path(path)
    with p.open("rb") as handle:
        head = handle.read(len(magic))
    if head != magic:
        raise ValueError(
            f"{p.as_posix()}: not a {kind} (got {head!r}) — "
            "likely an HTML error page from the server"
        )


def _validate_layout(path: Path) -> None:
    """Layout files: .xlsx is a zip, legacy .xls is OLE2 (audit F-1-7)."""
    if path.suffix.lower() == ".xlsx":
        validate_zip_container(path)
    else:
        validate_ole2_container(path)


def fetch_report_card(session: requests.Session, rc_year: int, out_dir: str | Path,
                      ) -> list[LandedFile]:
    """Download + validate the canonical data file (+ layout if any) for one rc year.

    The data file must match the config-pinned sha256; a mismatch means the
    upstream file was restated or swapped and requires an explicit re-pin
    (fail-loud vintage binding, audit F-1-3).
    """
    spec = ISBE_REPORT_CARD_FILES[rc_year]
    out = Path(out_dir)
    landed: list[LandedFile] = []

    data_url = spec["data"]
    data_dest = out / f"rc{rc_year}_{Path(data_url).name}"
    result = download_file(session, data_url, data_dest)
    if result.n_bytes == 0:
        raise ValueError(f"{data_dest.as_posix()}: empty download")
    validate_zip_container(data_dest)
    if result.sha256 != spec["sha256"]:
        raise ValueError(
            f"rc{rc_year}: sha256 {result.sha256[:12]}... does not match the pinned "
            f"{spec['sha256'][:12]}... — upstream restatement or swapped content; "
            "verify manually and re-pin config.ISBE_REPORT_CARD_FILES"
        )
    landed.append(LandedFile(data_dest, data_url, result.n_bytes, result.sha256,
                             result.last_modified))

    layout_url = spec["layout"]
    if layout_url is not None:
        layout_dest = out / f"rc{rc_year}_{Path(layout_url).name}"
        result = download_file(session, layout_url, layout_dest)
        if result.n_bytes == 0:
            raise ValueError(f"{layout_dest.as_posix()}: empty download")
        _validate_layout(layout_dest)
        landed.append(LandedFile(layout_dest, layout_url, result.n_bytes,
                                 result.sha256, result.last_modified))
    return landed
