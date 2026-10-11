"""Opt-in, read-only integration smoke test for a dedicated test account.

Run only when KDRIVE_INTEGRATION=1 and KDRIVE_TOKEN is set. It never creates,
updates, or deletes anything.
"""

import os

import pytest

from kdrive_link_manager.api_client import KDriveClient


@pytest.mark.integration
def test_list_drives_read_only() -> None:
    if os.environ.get("KDRIVE_INTEGRATION") != "1":
        pytest.skip("read-only integration mode is disabled")
    token = os.environ.get("KDRIVE_TOKEN", "")
    if not token:
        pytest.skip("KDRIVE_TOKEN is not set")
    with KDriveClient(token) as client:
        assert isinstance(client.drives(), list)

