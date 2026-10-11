from __future__ import annotations

from kdrive_link_manager.api_client import AmbiguousWriteError, KDriveError
from kdrive_link_manager.sharing import LinkStatus, Recording, SharingService, classify_share_link

from conftest import StubClient


def protected_link(url: str = "https://kdrive.infomaniak.com/app/share/a/b") -> dict:
    return {
        "url": url,
        "right": "password",
        "valid_until": None,
        "capabilities": {"can_download": True},
        "access_blocked": False,
    }


def test_existing_sharing_link_retrieval() -> None:
    status, url, *_ = classify_share_link(protected_link(), now=100)
    assert status == LinkStatus.EXISTING
    assert url.startswith("https://")


def test_missing_sharing_link_detection() -> None:
    assert classify_share_link(None)[0] == LinkStatus.MISSING


def test_expired_and_incompatible_links_are_not_missing() -> None:
    expired = {**protected_link(), "valid_until": 99}
    public = {**protected_link(), "right": "public"}
    no_download = {**protected_link(), "capabilities": {"can_download": False}}
    assert classify_share_link(expired, now=100)[0] == LinkStatus.EXPIRED
    assert classify_share_link(public, now=100)[0] == LinkStatus.INCOMPATIBLE
    assert classify_share_link(no_download, now=100)[0] == LinkStatus.INCOMPATIBLE


def test_empty_folder(folder) -> None:
    assert SharingService(StubClient()).scan_folder(folder) == []


def test_scan_mp4_only_and_duplicate_filenames(folder) -> None:
    stub = StubClient(
        children_pages={(10, 30): [
            {"id": 1, "name": "Lesson.mp4", "type": "file"},
            {"id": 2, "name": "lesson.MP4", "type": "file"},
            {"id": 3, "name": "notes.txt", "type": "file"},
        ]},
        links={(10, 1): None, (10, 2): protected_link()},
    )
    rows = SharingService(stub).scan_folder(folder)
    assert len(rows) == 2
    assert all("Duplicate filename" in row.note for row in rows)


def test_repeated_execution_does_not_duplicate_link() -> None:
    stub = StubClient(links={(10, 1): protected_link()})
    row = Recording(1, "lesson.mp4", 10, 30, status=LinkStatus.MISSING)
    result = SharingService(stub).create_missing([row], "secret")
    assert result[0].status == LinkStatus.EXISTING
    assert stub.created == []


def test_password_protected_link_creation() -> None:
    stub = StubClient(
        links={(10, 1): None}, create_results={(10, 1): protected_link()}
    )
    row = Recording(1, "lesson.mp4", 10, 30, status=LinkStatus.MISSING)
    result = SharingService(stub).create_missing([row], "same-password")
    assert result[0].status == LinkStatus.CREATED
    assert result[0].can_download is True
    assert stub.created == [(10, 1, "same-password")]


def test_partial_batch_failure_continues_after_definitive_error() -> None:
    stub = StubClient(
        links={(10, 1): None, (10, 2): None},
        create_results={(10, 1): KDriveError("denied"), (10, 2): protected_link()},
    )
    rows = [
        Recording(1, "one.mp4", 10, 30, status=LinkStatus.MISSING),
        Recording(2, "two.mp4", 10, 30, status=LinkStatus.MISSING),
    ]
    result = SharingService(stub).create_missing(rows, "secret")
    assert [row.status for row in result] == [LinkStatus.FAILED, LinkStatus.CREATED]


def test_ambiguous_write_stops_batch() -> None:
    stub = StubClient(
        links={(10, 1): None, (10, 2): None},
        create_results={(10, 1): AmbiguousWriteError("rescan"), (10, 2): protected_link()},
    )
    rows = [
        Recording(1, "one.mp4", 10, 30, status=LinkStatus.MISSING),
        Recording(2, "two.mp4", 10, 30, status=LinkStatus.MISSING),
    ]
    result = SharingService(stub).create_missing(rows, "secret")
    assert result[0].status == LinkStatus.UNCERTAIN
    assert result[1].status == LinkStatus.MISSING
    assert len(stub.created) == 1

