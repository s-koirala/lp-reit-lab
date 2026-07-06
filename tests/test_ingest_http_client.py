"""HTTP client unit tests (no network): download atomicity, digest correctness,
retryable-exception taxonomy."""

import hashlib

import pytest
import requests

from lp_reit_lab.ingest import http_client


def test_transient_error_is_a_requests_exception():
    # Retry exhaustion must be catchable by the CLI's RequestException handlers;
    # a bare-Exception subclass would escape every documented exit-4 path.
    assert issubclass(http_client.TransientHTTPError, requests.exceptions.RequestException)


class _FakeResponse:
    def __init__(self, status_code: int, payload: bytes,
                 headers: dict[str, str] | None = None):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(str(self.status_code))

    def iter_content(self, chunk_size):
        for i in range(0, len(self._payload), chunk_size):
            yield self._payload[i:i + chunk_size]


class _FakeSession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def get(self, url, **kwargs):
        self.calls += 1
        return self._responses.pop(0)


def test_download_file_writes_atomically_with_correct_digest(tmp_path):
    payload = b"x" * (3 << 20) + b"tail"
    dest = tmp_path / "blob.zip"
    session = _FakeSession([_FakeResponse(200, payload,
                                          {"Last-Modified": "Mon, 06 Jul 2026 00:00:00 GMT"})])
    result = http_client.download_file(session, "http://x/blob.zip", dest)
    assert result.n_bytes == len(payload)
    assert result.sha256 == hashlib.sha256(payload).hexdigest()
    assert result.last_modified == "Mon, 06 Jul 2026 00:00:00 GMT"
    assert dest.read_bytes() == payload
    assert not list(tmp_path.glob("*.tmp"))  # no orphaned temp sibling


def test_download_file_retries_transient_then_succeeds(tmp_path, monkeypatch):
    monkeypatch.setattr("tenacity.nap.time.sleep", lambda s: None)  # no real backoff
    payload = b"PK\x03\x04data"
    dest = tmp_path / "blob.zip"
    session = _FakeSession([_FakeResponse(503, b""), _FakeResponse(200, payload)])
    result = http_client.download_file(session, "http://x/blob.zip", dest)
    assert session.calls == 2
    assert dest.read_bytes() == payload
    assert result.n_bytes == len(payload)
    assert result.last_modified is None


def test_download_file_hard_failure_leaves_no_dest(tmp_path):
    dest = tmp_path / "blob.zip"
    session = _FakeSession([_FakeResponse(404, b"")])
    with pytest.raises(requests.exceptions.HTTPError):
        http_client.download_file(session, "http://x/blob.zip", dest)
    assert not dest.exists()
