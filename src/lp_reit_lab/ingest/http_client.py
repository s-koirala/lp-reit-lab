"""HTTP client: a requests session with application-level retry/backoff.

Retries only transient failures (RFC 7231/6585 statuses + connection/timeout),
never 4xx auth/not-found, with exponential backoff + jitter (jitter avoids
synchronized retry storms). Every request carries an explicit timeout — requests
has no default and would otherwise hang forever.
"""

from __future__ import annotations

import logging
from typing import Any

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from .config import RETRY_STATUSES, RetryConfig

log = logging.getLogger(__name__)
_R = RetryConfig()


class TransientHTTPError(Exception):
    """A retryable HTTP response (status in RETRY_STATUSES)."""


def build_session() -> requests.Session:
    """A plain session; retry logic lives in `get_json` (tenacity)."""
    return requests.Session()


@retry(
    stop=stop_after_attempt(_R.max_attempts),
    wait=wait_exponential_jitter(initial=_R.initial_wait_s, max=_R.max_wait_s, jitter=_R.jitter_s),
    retry=retry_if_exception_type(
        (TransientHTTPError, requests.exceptions.ConnectionError, requests.exceptions.Timeout)
    ),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)
def get_json(session: requests.Session, url: str, *, params: dict[str, Any] | None = None,
             headers: dict[str, str] | None = None) -> Any:
    """GET `url` and return parsed JSON, retrying only transient failures."""
    resp = session.get(
        url, params=params, headers=headers,
        timeout=(_R.connect_timeout_s, _R.read_timeout_s),
    )
    if resp.status_code in RETRY_STATUSES:
        raise TransientHTTPError(f"{resp.status_code} for {url}")
    resp.raise_for_status()
    return resp.json()
