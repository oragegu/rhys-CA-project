from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from kdrive_link_manager.api_client import Drive, Folder


@dataclass
class StubClient:
    children_pages: dict[tuple[int, int], list[dict[str, Any]]] = field(default_factory=dict)
    links: dict[tuple[int, int], dict[str, Any] | None | Exception] = field(default_factory=dict)
    created: list[tuple[int, int, str]] = field(default_factory=list)
    create_results: dict[tuple[int, int], dict[str, Any] | Exception] = field(default_factory=dict)

    def children(self, drive_id: int, folder_id: int) -> list[dict[str, Any]]:
        return self.children_pages.get((drive_id, folder_id), [])

    def get_share_link(self, drive_id: int, file_id: int) -> dict[str, Any] | None:
        value = self.links.get((drive_id, file_id))
        if isinstance(value, Exception):
            raise value
        return value

    def create_share_link(self, drive_id: int, file_id: int, password: str) -> dict[str, Any]:
        self.created.append((drive_id, file_id, password))
        value = self.create_results.get((drive_id, file_id))
        if isinstance(value, Exception):
            raise value
        assert isinstance(value, dict)
        return value


@pytest.fixture
def drive() -> Drive:
    return Drive(id=10, name="Teaching Drive", account_id=20)


@pytest.fixture
def folder() -> Folder:
    return Folder(drive_id=10, drive_name="Teaching Drive", id=30, name="CA Lilly recordings")

