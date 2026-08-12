import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import sync_universe


def make_cfg(**overrides):
    cfg = {
        "markets": ["XOSL"],
        "include": [],
        "exclude": set(),
        "guards": dict(sync_universe.DEFAULT_GUARDS),
    }
    cfg.update(overrides)
    return cfg


def row(symbol, mic="XOSL", name="TEST"):
    return {"symbol": symbol, "mic": mic, "name": name, "isin": "NO0000000000"}


def test_rows_to_tickers_filters_on_market():
    tickers, _ = make_tickers([row("EQNR"), row("CAMBI", mic="MERK")])
    assert tickers == ["EQNR.OL"]


def make_tickers(rows, **cfg_overrides):
    return sync_universe.rows_to_tickers(rows, make_cfg(**cfg_overrides))


def test_rows_to_tickers_applies_exclude_and_include():
    tickers, skipped = make_tickers(
        [row("EQNR"), row("ASAS", name="ATLANTIC SAPPHI TR")],
        exclude={"ASAS.OL"},
        include=["PYRUM.OL"],
    )

    assert tickers == ["EQNR.OL", "PYRUM.OL"]
    assert any("ASAS.OL" in s for s in skipped)


def test_rows_to_tickers_skips_malformed_symbols():
    tickers, skipped = make_tickers([row("EQNR"), row("BAD SYMBOL"), row("")])

    assert tickers == ["EQNR.OL"]
    assert len(skipped) == 2


def test_rows_to_tickers_dedupes_include_already_in_market():
    tickers, _ = make_tickers([row("EQNR")], include=["EQNR.OL"])

    assert tickers == ["EQNR.OL"]


def test_load_universe_config_requires_markets(tmp_path):
    path = tmp_path / "universe.yaml"
    path.write_text("markets: []\n")

    with pytest.raises(sync_universe.SyncError):
        sync_universe.load_universe_config(str(path))


def test_check_guards_accepts_normal_run():
    current = [f"T{i}.OL" for i in range(100)]
    new = current[1:] + ["NEW.OL"]

    assert sync_universe.check_guards(200, current, new, sync_universe.DEFAULT_GUARDS) == []


def test_check_guards_blocks_large_removal():
    current = [f"T{i}.OL" for i in range(100)]
    new = current[:80]

    problems = sync_universe.check_guards(200, current, new, sync_universe.DEFAULT_GUARDS)

    assert len(problems) == 1
    assert "20.0 %" in problems[0]


def test_check_guards_blocks_short_fetch_and_empty_list():
    problems = sync_universe.check_guards(3, ["A.OL"], [], sync_universe.DEFAULT_GUARDS)

    assert any("tom" in p for p in problems)
    assert any("min_fetched" in p for p in problems)


def test_main_leaves_tickers_file_untouched_when_guard_trips(tmp_path, monkeypatch, capsys):
    universe = tmp_path / "universe.yaml"
    universe.write_text("markets:\n  - XOSL\n")
    tickers = tmp_path / "tickers.txt"
    original = "".join(f"T{i}.OL\n" for i in range(100))
    tickers.write_text(original)

    monkeypatch.setattr(sync_universe, "UNIVERSE_FILE", str(universe))
    monkeypatch.setattr(sync_universe, "TICKERS_FILE", str(tickers))
    monkeypatch.setattr(sync_universe, "fetch_rows", lambda markets, session=None: [row("EQNR")])

    assert sync_universe.main() == 1
    assert tickers.read_text() == original
    assert "avbrutt" in capsys.readouterr().err


def test_main_writes_tickers_on_healthy_sync(tmp_path, monkeypatch):
    universe = tmp_path / "universe.yaml"
    universe.write_text("markets:\n  - XOSL\ninclude:\n  - PYRUM.OL\n")
    tickers = tmp_path / "tickers.txt"
    tickers.write_text("EQNR.OL\nOLD.OL\n")

    rows = [row(f"S{i}") for i in range(200)] + [row("EQNR")]
    monkeypatch.setattr(sync_universe, "UNIVERSE_FILE", str(universe))
    monkeypatch.setattr(sync_universe, "TICKERS_FILE", str(tickers))
    monkeypatch.setattr(sync_universe, "fetch_rows", lambda markets, session=None: rows)
    monkeypatch.setenv("FORCE_SYNC", "1")  # OLD.OL forsvinner = 50 % fjernet

    assert sync_universe.main() == 0

    written = tickers.read_text().splitlines()
    assert "EQNR.OL" in written
    assert "PYRUM.OL" in written
    assert "OLD.OL" not in written
    assert written == sorted(written)


def test_strip_html_and_normalize():
    assert sync_universe.strip_html('<div title="Oslo Børs">XOSL</div>') == "XOSL"
    assert sync_universe.normalize("eqnr") == "EQNR.OL"
    assert sync_universe.normalize("EQNR.OL") == "EQNR.OL"
