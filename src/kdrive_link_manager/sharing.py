"""Read-only scanning and guarded sharing-link creation workflows."""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable, Iterable

from .api_client import AmbiguousWriteError, Folder, KDriveClient, KDriveError, valid_https_url


class LinkStatus(str, Enum):
    EXISTING = "Existing"
    MISSING = "Missing"
    CREATED = "Newly created"
    EXPIRED = "Existing — expired"
    INCOMPATIBLE = "Existing — check settings"
    FAILED = "Failed"
    UNCERTAIN = "Uncertain"


@dataclass(frozen=True)
class Recording:
    file_id: int
    filename: str
    drive_id: int
    folder_id: int
    url: str = ""
    status: LinkStatus = LinkStatus.MISSING
    note: str = ""
    right: str = ""
    can_download: bool | None = None
    valid_until: int | None = None


Progress = Callable[[int, int, str], None]


def classify_share_link(
    link: dict | None, *, now: int | None = None
) -> tuple[LinkStatus, str, str, str, bool | None, int | None]:
    """Classify without changing an existing link, including unsafe settings."""
    if link is None:
        return LinkStatus.MISSING, "", "", "", None, None
    url = valid_https_url(link.get("url"))
    right = str(link.get("right") or "")
    valid_until = link.get("valid_until")
    if not isinstance(valid_until, int):
        valid_until = None
    capabilities = link.get("capabilities")
    can_download = capabilities.get("can_download") if isinstance(capabilities, dict) else None
    if not isinstance(can_download, bool):
        can_download = None
    if not url:
        return (
            LinkStatus.UNCERTAIN,
            "",
            "kDrive reported a share link but did not provide a valid HTTPS URL.",
            right,
            can_download,
            valid_until,
        )
    timestamp = int(time.time()) if now is None else now
    if valid_until is not None and valid_until <= timestamp:
        return LinkStatus.EXPIRED, url, "This existing link has expired; it was not changed.", right, can_download, valid_until
    if link.get("access_blocked") is True:
        return LinkStatus.INCOMPATIBLE, url, "This existing link is blocked; it was not changed.", right, can_download, valid_until
    issues: list[str] = []
    if right != "password":
        issues.append("not password-protected")
    if can_download is False:
        issues.append("downloads are disabled")
    if can_download is None:
        issues.append("download permission was not reported")
    if issues:
        return (
            LinkStatus.INCOMPATIBLE,
            url,
            "Existing link is " + " and ".join(issues) + "; it was not changed.",
            right,
            can_download,
            valid_until,
        )
    return LinkStatus.EXISTING, url, "", right, can_download, valid_until


class SharingService:
    def __init__(self, client: KDriveClient) -> None:
        self.client = client

    def inspect_file(self, recording: Recording) -> Recording:
        try:
            link = self.client.get_share_link(recording.drive_id, recording.file_id)
            status, url, note, right, can_download, valid_until = classify_share_link(link)
            return replace(
                recording,
                status=status,
                url=url,
                note=note,
                right=right,
                can_download=can_download,
                valid_until=valid_until,
            )
        except KDriveError as exc:
            return replace(recording, status=LinkStatus.UNCERTAIN, note=str(exc))

    def scan_folder(
        self, folder: Folder, *, recursive: bool = False, progress: Progress | None = None
    ) -> list[Recording]:
        pending = [folder.id]
        files: list[dict] = []
        visited: set[int] = set()
        while pending:
            folder_id = pending.pop(0)
            if folder_id in visited:
                continue
            visited.add(folder_id)
            for item in self.client.children(folder.drive_id, folder_id):
                if item.get("type") == "dir" and recursive and isinstance(item.get("id"), int):
                    pending.append(item["id"])
                elif (
                    item.get("type") == "file"
                    and isinstance(item.get("id"), int)
                    and str(item.get("name", "")).lower().endswith(".mp4")
                ):
                    files.append({**item, "folder_id": folder_id})
        files.sort(key=lambda item: (str(item.get("name", "")).casefold(), int(item["id"])))
        names: dict[str, int] = {}
        for item in files:
            key = str(item.get("name", "")).casefold()
            names[key] = names.get(key, 0) + 1
        recordings: list[Recording] = []
        for index, item in enumerate(files, 1):
            filename = str(item.get("name") or f"File {item['id']}")
            if progress:
                progress(index, len(files), filename)
            recording = Recording(
                file_id=int(item["id"]),
                filename=filename,
                drive_id=folder.drive_id,
                folder_id=int(item["folder_id"]),
            )
            inspected = self.inspect_file(recording)
            if names[filename.casefold()] > 1:
                duplicate_note = "Duplicate filename in the selected folder."
                inspected = replace(
                    inspected,
                    note=f"{inspected.note} {duplicate_note}".strip(),
                )
            recordings.append(inspected)
        return recordings

    def create_missing(
        self,
        recordings: Iterable[Recording],
        password: str,
        *,
        limit: int | None = None,
        progress: Progress | None = None,
    ) -> list[Recording]:
        """Create missing links after a fresh per-file check.

        An ambiguous write stops the batch. Definitive per-file API failures are
        recorded and the remaining files continue, enabling partial-batch export.
        """
        rows = list(recordings)
        targets = [index for index, row in enumerate(rows) if row.status == LinkStatus.MISSING]
        if limit is not None:
            targets = targets[:limit]
        for position, index in enumerate(targets, 1):
            original = rows[index]
            if progress:
                progress(position, len(targets), original.filename)
            fresh = self.inspect_file(original)
            if fresh.status != LinkStatus.MISSING:
                rows[index] = fresh
                continue
            try:
                link = self.client.create_share_link(fresh.drive_id, fresh.file_id, password)
                status, url, note, right, can_download, valid_until = classify_share_link(link)
                if status == LinkStatus.EXISTING:
                    status = LinkStatus.CREATED
                elif status == LinkStatus.INCOMPATIBLE:
                    note = "New link was created, but kDrive reported incompatible settings. Verify it manually."
                rows[index] = replace(
                    fresh,
                    status=status,
                    url=url,
                    note=note,
                    right=right,
                    can_download=can_download,
                    valid_until=valid_until,
                )
            except AmbiguousWriteError as exc:
                rows[index] = replace(fresh, status=LinkStatus.UNCERTAIN, note=str(exc))
                break
            except KDriveError as exc:
                rows[index] = replace(fresh, status=LinkStatus.FAILED, note=str(exc))
        return rows

