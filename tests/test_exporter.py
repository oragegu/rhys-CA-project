from __future__ import annotations

from pathlib import Path

from kdrive_link_manager.exporter import export_csv, spreadsheet_safe
from kdrive_link_manager.sharing import LinkStatus, Recording


def test_formula_injection_is_neutralized() -> None:
    assert spreadsheet_safe("=HYPERLINK(\"bad\")") == "'=HYPERLINK(\"bad\")"
    assert spreadsheet_safe("  +1") == "'  +1"
    assert spreadsheet_safe("lesson.mp4") == "lesson.mp4"


def test_csv_export_has_bom_sorting_and_no_password(tmp_path: Path) -> None:
    destination = tmp_path / "links.csv"
    rows = [
        Recording(2, "z.mp4", 10, 30, "https://example/z", LinkStatus.EXISTING),
        Recording(1, "=bad.mp4", 10, 30, "", LinkStatus.MISSING, "No link"),
    ]
    export_csv(destination, rows)
    raw = destination.read_bytes()
    text = raw.decode("utf-8-sig")
    assert raw.startswith(b"\xef\xbb\xbf")
    assert text.splitlines()[1].startswith("'=bad.mp4")
    assert "password" not in text.casefold()
    assert "https://example/z" in text

