"""Excel-compatible, formula-safe CSV export."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .sharing import Recording


def spreadsheet_safe(value: object) -> str:
    text = "" if value is None else str(value)
    if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text


def export_csv(path: str | Path, recordings: Iterable[Recording]) -> None:
    rows = sorted(recordings, key=lambda row: (row.filename.casefold(), row.file_id))
    with Path(path).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Filename", "Shareable Link", "Status", "Notes"])
        for row in rows:
            writer.writerow(
                [
                    spreadsheet_safe(row.filename),
                    spreadsheet_safe(row.url),
                    spreadsheet_safe(row.status.value),
                    spreadsheet_safe(row.note),
                ]
            )
