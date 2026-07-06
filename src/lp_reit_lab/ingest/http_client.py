"""HTTP client: a requests session with application-level retry/backoff.

Retries only transient failures (RFC 9110 408/5xx, RFC 6585 429, RFC 8470 425,
plus connection/timeout), never 4xx auth/not-found, with exponential backoff +
jitter (jitter avoids synchronized retry storms). Every request carries an
explicit timeout — requests has no default and would otherwise hang forever.
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Any, NamedTuple

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
_CHUNK = 1 << 20  # 1 MiB streaming read — bounded memory, not a tunable threshold


class TransientHTTPError(requests.exceptions.RequestException):
    """A retryable HTTP response (status in RETRY_STATUSES).

    Subclasses RequestException so that retry EXHAUSTION (tenacity reraise)
    still lands in callers' transport except-paths instead of escaping as an
    unhandled bare Exception (audit CR-1-1).
    """


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


class DownloadResult(NamedTuple):
    """One completed download: size, digest, and the server's version signal."""

    n_bytes: int
    sha256: str
    last_modified: str | None


@retry(
    stop=stop_after_attempt(_R.max_attempts),
    wait=wait_exponential_jitter(initial=_R.initial_wait_s, max=_R.max_wait_s, jitter=_R.jitter_s),
    retry=retry_if_exception_type(
        (TransientHTTPError, requests.exceptions.ConnectionError, requests.exceptions.Timeout)
    ),
    before_sleep=before_sleep_log(log, logging.WARNING),
    reraise=True,
)
def download_file(session: requests.Session, url: str, dest: str | Path,
                  *, headers: dict[str, str] | None = None) -> DownloadResult:
    """Stream `url` to `dest` atomically; return (n_bytes, sha256, last_modified).

    Streams through a `.tmp` sibling then `os.replace`s into place, so an
    interrupted download can never masquerade as a completed artifact. Retries
    restart the whole file (Range resumption is not attempted — the sources
    here are tens of MB, and a byte-exact restart is simpler to reason about
    for content addressing). `last_modified` echoes the HTTP Last-Modified
    header when the server sends one — the only version observable for plain
    file hosts like isbe.net.
    """
    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest_path.with_suffix(dest_path.suffix + ".tmp")
    digest = hashlib.sha256()
    written = 0
    with session.get(
        url, headers=headers, stream=True,
        timeout=(_R.connect_timeout_s, _R.read_timeout_s),
    ) as resp:
        if resp.status_code in RETRY_STATUSES:
            raise TransientHTTPError(f"{resp.status_code} for {url}")
        resp.raise_for_status()
        last_modified = resp.headers.get("Last-Modified")
        with tmp.open("wb") as handle:
            for block in resp.iter_content(chunk_size=_CHUNK):
                handle.write(block)
                digest.update(block)
                written += len(block)
    os.replace(tmp, dest_path)
    return DownloadResult(written, digest.hexdigest(), last_modified)
