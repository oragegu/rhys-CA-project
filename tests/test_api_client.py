from __future__ import annotations

from unittest.mock import Mock

import pytest
import requests

from kdrive_link_manager.api_client import (
    AmbiguousWriteError,
    AuthenticationError,
    Drive,
    KDriveClient,
    KDriveError,
)


def response(status: int, body: dict, headers: dict | None = None) -> Mock:
    result = Mock()
    result.status_code = status
    result.ok = 200 <= status < 300
    result.json.return_value = body
    result.headers = headers or {}
    return result


def client_with(*responses: Mock) -> tuple[KDriveClient, Mock]:
    session = Mock()
    session.headers = {}
    session.request.side_effect = responses
    client = KDriveClient("secret", session=session, sleeper=lambda _: None, clock=Mock(side_effect=range(100)))
    return client, session


def test_successful_authentication_and_drive_discovery() -> None:
    client, session = client_with(
        response(200, {"result": "success", "data": [{"id": 7, "name": "Account"}]}),
        response(
            200,
            {"result": "success", "data": [{"id": 9, "name": "Drive"}], "page": 1, "pages": 1},
        ),
    )
    assert client.drives() == [Drive(id=9, name="Drive", account_id=7)]
    assert session.request.call_args_list[1].kwargs["params"]["account_id"] == 7


def test_invalid_authentication() -> None:
    client, _ = client_with(
        response(401, {"result": "error", "error": {"code": "unauthorized"}})
    )
    with pytest.raises(AuthenticationError, match="invalid or expired"):
        client.accounts()


def test_folder_discovery_exact_name_and_multiple_matches(drive: Drive) -> None:
    client, _ = client_with(
        response(
            200,
            {
                "result": "success",
                "data": [
                    {"id": 1, "name": "CA Lilly recordings", "type": "dir", "path": "/one"},
                    {"id": 2, "name": "ca lilly RECORDINGS", "type": "dir", "path": "/two"},
                    {"id": 3, "name": "CA Lilly recordings old", "type": "dir"},
                ],
            },
        )
    )
    matches = client.folder_matches(drive, "CA Lilly recordings")
    assert [item.id for item in matches] == [1, 2]


def test_file_cursor_pagination() -> None:
    client, session = client_with(
        response(200, {"result": "success", "data": [{"id": 1}], "has_more": True, "cursor": "next"}),
        response(200, {"result": "success", "data": [{"id": 2}], "has_more": False}),
    )
    assert [item["id"] for item in client.children(10, 30)] == [1, 2]
    assert session.request.call_args_list[1].kwargs["params"] == {"cursor": "next"}


def test_rate_limit_retries_get_only() -> None:
    client, session = client_with(
        response(429, {"result": "error", "error": {"description": "slow"}}, {"Retry-After": "0"}),
        response(200, {"result": "success", "data": []}),
    )
    assert client.accounts() == []
    assert session.request.call_count == 2


def test_api_failure_is_reported() -> None:
    client, _ = client_with(
        response(500, {"result": "error", "error": {"description": "server problem"}}),
        response(500, {"result": "error", "error": {"description": "server problem"}}),
        response(500, {"result": "error", "error": {"description": "server problem"}}),
    )
    with pytest.raises(KDriveError, match="server problem"):
        client.accounts()


def test_network_get_is_retried() -> None:
    session = Mock()
    session.headers = {}
    session.request.side_effect = [
        requests.ConnectionError("offline"),
        response(200, {"result": "success", "data": []}),
    ]
    client = KDriveClient("secret", session=session, sleeper=lambda _: None, clock=Mock(side_effect=range(100)))
    assert client.accounts() == []


def test_create_payload_password_and_downloads() -> None:
    client, session = client_with(
        response(
            201,
            {
                "result": "success",
                "data": {
                    "url": "https://kdrive.infomaniak.com/app/share/x/y",
                    "right": "password",
                    "capabilities": {"can_download": True},
                },
            },
        )
    )
    client.create_share_link(10, 99, "class-secret")
    payload = session.request.call_args.kwargs["json"]
    assert payload["right"] == "password"
    assert payload["password"] == "class-secret"
    assert payload["can_download"] is True
    assert session.request.call_count == 1


def test_get_share_link_uses_public_link_route_and_404_means_missing() -> None:
    client, session = client_with(
        response(404, {"result": "error", "error": {"code": "object_not_found"}})
    )
    assert client.get_share_link(10, 99) is None
    assert session.request.call_args.args[1] == "https://api.infomaniak.com/2/drive/10/files/99/link"


def test_create_network_failure_is_not_retried() -> None:
    session = Mock()
    session.headers = {}
    session.request.side_effect = requests.ConnectionError("lost response")
    client = KDriveClient("secret", session=session, sleeper=lambda _: None, clock=Mock(side_effect=range(100)))
    with pytest.raises(AmbiguousWriteError, match="Rescan"):
        client.create_share_link(10, 99, "class-secret")
    assert session.request.call_count == 1

