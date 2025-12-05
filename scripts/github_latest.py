"""Utilities for downloading ``latest.csv`` from GitHub.

The daily workflow publishes the CSV both via GitHub Pages and the raw
repository endpoint.  This module adds a small abstraction so scripts can try
multiple sources, optionally using a ``GITHUB_TOKEN``/``GH_TOKEN`` for the raw
endpoint (which honours API rate limits).
"""

from __future__ import annotations

import os
import time
import pathlib as pl
from dataclasses import dataclass
from typing import Iterable, Sequence
import urllib.error
import urllib.request


@dataclass(frozen=True)
class Source:
    """Description of a latest.csv host."""

    name: str
    url: str
    allow_auth: bool = True


DEFAULT_SOURCES: tuple[Source, ...] = (
    Source(
        "GitHub Pages",
        "https://keresell-coder.github.io/oslo-screener/latest.csv",
        allow_auth=False,
    ),
    Source(
        "GitHub Raw",
        "https://raw.githubusercontent.com/keresell-coder/oslo-screener/main/latest.csv",
        allow_auth=True,
    ),
)


class DownloadError(RuntimeError):
    """Raised when every configured source failed."""


def _cache_busted_url(url: str, *, cache_bust: bool) -> str:
    if not cache_bust:
        return url
    stamp = int(time.time())
    joiner = "&" if "?" in url else "?"
    return f"{url}{joiner}t={stamp}"


def _prepare_request(source: Source, token: str | None, *, cache_bust: bool) -> urllib.request.Request:
    url = _cache_busted_url(source.url, cache_bust=cache_bust)
    headers = {"User-Agent": "oslo-screener-gh-fetch/1.0"}
    if token and source.allow_auth:
        headers["Authorization"] = f"token {token}"
    return urllib.request.Request(url, headers=headers)


def download_latest_csv(
    dest: str | pl.Path,
    sources: Sequence[Source] | None = None,
    *,
    timeout: int = 15,
    token: str | None = None,
    cache_bust: bool = True,
) -> Source:
    """Download ``latest.csv`` to *dest*.

    Returns the :class:`Source` that succeeded.  Raises :class:`DownloadError`
    if all sources fail.
    """

    target = pl.Path(dest)
    target.parent.mkdir(parents=True, exist_ok=True)
    sources = sources or DEFAULT_SOURCES

    errors: list[str] = []
    for source in sources:
        req = _prepare_request(source, token, cache_bust=cache_bust)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = getattr(resp, "status", None) or resp.getcode()
                if status != 200:
                    raise DownloadError(f"HTTP {status}")
                data = resp.read()
                if not data:
                    raise DownloadError("Tom respons fra server")
        except (urllib.error.URLError, urllib.error.HTTPError, DownloadError) as exc:
            errors.append(f"{source.name}: {exc}")
            continue

        target.write_bytes(data)
        return source

    raise DownloadError("; ".join(errors))


def ensure_latest_csv(
    dest: str | pl.Path,
    *,
    refresh: bool = False,
    extra_sources: Iterable[str] | None = None,
    timeout: int = 15,
    cache_bust: bool = True,
    token: str | None = None,
) -> bool:
    """Ensure *dest* exists, optionally downloading from GitHub.

    Returns ``True`` if a download happened, ``False`` if the file already
    existed and *refresh* was ``False``.
    """

    target = pl.Path(dest)
    if target.exists() and not refresh:
        return False

    token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")

    custom_sources: list[Source] = []
    if extra_sources:
        for idx, url in enumerate(extra_sources, start=1):
            custom_sources.append(Source(f"custom[{idx}]", url, allow_auth=True))

    sources: list[Source] = [*custom_sources, *DEFAULT_SOURCES]

    try:
        download_latest_csv(
            target,
            sources,
            timeout=timeout,
            token=token,
            cache_bust=cache_bust,
        )
        return True
    except DownloadError as exc:
        raise RuntimeError(str(exc))
