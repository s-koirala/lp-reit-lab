"""Shared Socrata SODA pagination — one deterministic pager for every connector.

Offset pagination is only reproducible when `$order` is a *total* order; every
caller passes `:id` (the Socrata system row id, unique per row). Lifted out of
`sources/cook_county.py` so the Chicago-portal connectors reuse the identical
access path instead of re-implementing it.
"""

from __future__ import annotations

import time
from typing import Any

import requests

from .http_client import get_json


def soql_count(session: requests.Session, url: str, *, where: str,
               app_token: str | None = None) -> int:
    """Server-side row count under `where` — the pagination consistency anchor.

    Offset pagination has no snapshot isolation: upstream inserts/deletes
    between pages can silently skip rows. Callers compare this count (taken
    just before paging) with the assembled row count and fail loudly on
    mismatch (audit F-1-9).
    """
    headers = {"X-App-Token": app_token} if app_token else None
    rows = get_json(session, url, params={"$select": "count(*) as n", "$where": where},
                    headers=headers)
    try:
        return int(rows[0]["n"]) if rows else 0
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"malformed count payload from {url}: {rows!r}") from exc


def paged(session: requests.Session, url: str, *, select: str, where: str, order: str,
          app_token: str | None = None, page_size: int, courtesy_sleep_s: float,
          max_rows: int | None = None) -> list[dict[str, Any]]:
    """Deterministic offset pagination (`$order` must be a total order); optional cap."""
    headers = {"X-App-Token": app_token} if app_token else None
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        limit = page_size if max_rows is None else min(page_size, max_rows - len(rows))
        if limit <= 0:
            break
        params = {"$select": select, "$where": where, "$order": order,
                  "$limit": limit, "$offset": offset}
        page = get_json(session, url, params=params, headers=headers)
        rows.extend(page)
        if len(page) < limit:
            break
        offset += len(page)
        time.sleep(courtesy_sleep_s)
    return rows
