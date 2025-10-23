import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import github_latest as gh


class DummyResponse:
    def __init__(self, data: bytes, status: int = 200, headers: dict | None = None):
        self._data = data
        self.status = status
        self._headers = headers or {"Content-Type": "text/csv"}

    def read(self) -> bytes:
        return self._data

    def getcode(self) -> int:
        return self.status

    @property
    def headers(self):
        return self._headers

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_download_latest_falls_back(monkeypatch, tmp_path):
    calls: list[str] = []

    def fake_urlopen(req, timeout=0):
        calls.append(req.full_url)
        if len(calls) == 1:
            raise gh.urllib.error.URLError("boom")
        return DummyResponse(b"ticker,date\nAAA,2025-01-01\n")

    monkeypatch.setattr(gh.urllib.request, "urlopen", fake_urlopen)

    dest = tmp_path / "latest.csv"
    src = gh.download_latest_csv(dest, cache_bust=False)

    assert dest.read_text() == "ticker,date\nAAA,2025-01-01\n"
    assert calls[0].startswith(gh.DEFAULT_SOURCES[0].url)
    assert calls[1].startswith(gh.DEFAULT_SOURCES[1].url)
    assert src.name == gh.DEFAULT_SOURCES[1].name


def test_download_uses_token_only_when_allowed(monkeypatch, tmp_path):
    seen_auth: list[str | None] = []

    def fake_urlopen(req, timeout=0):
        seen_auth.append(req.headers.get("Authorization"))
        if len(seen_auth) == 1:
            raise gh.urllib.error.URLError("fail")
        return DummyResponse(b"ticker,date\nBBB,2025-01-02\n")

    monkeypatch.setattr(gh.urllib.request, "urlopen", fake_urlopen)

    dest = tmp_path / "latest.csv"
    gh.download_latest_csv(dest, cache_bust=False, token="abc123")

    assert seen_auth[0] is None  # GitHub Pages – no auth header
    assert seen_auth[1] == "token abc123"  # Raw endpoint gets the token


def test_ensure_latest_skips_when_present(monkeypatch, tmp_path):
    dest = tmp_path / "latest.csv"
    dest.write_text("ticker,date\nCCC,2025-01-03\n")

    called = False

    def fake_download(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("should not be called")

    monkeypatch.setattr(gh, "download_latest_csv", fake_download)

    result = gh.ensure_latest_csv(dest, refresh=False)

    assert result is False
    assert dest.read_text() == "ticker,date\nCCC,2025-01-03\n"
    assert called is False


def test_ensure_latest_raises_runtime_error(monkeypatch, tmp_path):
    def fake_download(*args, **kwargs):
        raise gh.DownloadError("nope")

    monkeypatch.setattr(gh, "download_latest_csv", fake_download)

    with pytest.raises(RuntimeError):
        gh.ensure_latest_csv(tmp_path / "missing.csv", refresh=True)
