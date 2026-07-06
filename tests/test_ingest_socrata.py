"""Shared Socrata pager unit tests (no network): pagination arithmetic,
short-page termination, max_rows caps."""

from lp_reit_lab.ingest import socrata


class _FakeSession:
    pass


def _fake_get_json(pages: list[list[dict]]):
    """A get_json stand-in serving `pages` in order, recording params."""
    calls: list[dict] = []

    def fake(session, url, *, params=None, headers=None):
        calls.append(dict(params))
        idx = len(calls) - 1
        page = pages[idx] if idx < len(pages) else []
        return page[: params["$limit"]]

    fake.calls = calls
    return fake


def _rows(n: int, start: int = 0) -> list[dict]:
    return [{"id": str(i)} for i in range(start, start + n)]


def test_paged_stops_on_short_page(monkeypatch):
    fake = _fake_get_json([_rows(3), _rows(1, 3)])
    monkeypatch.setattr(socrata, "get_json", fake)
    out = socrata.paged(_FakeSession(), "http://x", select="id", where="1=1", order=":id",
                        page_size=3, courtesy_sleep_s=0)
    assert [r["id"] for r in out] == ["0", "1", "2", "3"]
    assert [c["$offset"] for c in fake.calls] == [0, 3]


def test_paged_max_rows_caps_mid_page(monkeypatch):
    fake = _fake_get_json([_rows(3), _rows(3, 3)])
    monkeypatch.setattr(socrata, "get_json", fake)
    out = socrata.paged(_FakeSession(), "http://x", select="id", where="1=1", order=":id",
                        page_size=3, courtesy_sleep_s=0, max_rows=4)
    assert len(out) == 4
    # second request must shrink its $limit to the remaining budget
    assert fake.calls[1]["$limit"] == 1


def test_paged_max_rows_zero_requests_nothing(monkeypatch):
    fake = _fake_get_json([_rows(3)])
    monkeypatch.setattr(socrata, "get_json", fake)
    out = socrata.paged(_FakeSession(), "http://x", select="id", where="1=1", order=":id",
                        page_size=3, courtesy_sleep_s=0, max_rows=0)
    assert out == []
    assert fake.calls == []


def test_paged_exact_multiple_terminates(monkeypatch):
    # a full page followed by an empty page must terminate, not loop
    fake = _fake_get_json([_rows(2), []])
    monkeypatch.setattr(socrata, "get_json", fake)
    out = socrata.paged(_FakeSession(), "http://x", select="id", where="1=1", order=":id",
                        page_size=2, courtesy_sleep_s=0)
    assert len(out) == 2
    assert len(fake.calls) == 2


def test_paged_app_token_header(monkeypatch):
    seen: list[dict | None] = []

    def fake(session, url, *, params=None, headers=None):
        seen.append(headers)
        return []

    monkeypatch.setattr(socrata, "get_json", fake)
    socrata.paged(_FakeSession(), "http://x", select="id", where="1=1", order=":id",
                  page_size=2, courtesy_sleep_s=0, app_token="tok")
    assert seen == [{"X-App-Token": "tok"}]
