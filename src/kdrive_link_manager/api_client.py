"""Small, documented Infomaniak kDrive REST client.

Write requests are deliberately never retried: after a lost response it is not
safe to assume that the server did not create the link.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any, Callable
from urllib.parse import urlparse

import requests

from .config import (
    API_BASE_URL,
    MAX_READ_RETRIES,
    MIN_REQUEST_INTERVAL,
    REQUEST_TIMEOUT,
)


class KDriveError(Exception):
    """A safe, user-displayable kDrive error."""


class AuthenticationError(KDriveError):
    """The access token is missing, invalid, expired, or under-scoped."""


class NotFoundError(KDriveError):
    """The requested resource does not exist."""


class AmbiguousWriteError(KDriveError):
    """A write may have reached kDrive; the caller must rescan before retrying."""


@dataclass(frozen=True)
class Drive:
    id: int
    name: str
    account_id: int


@dataclass(frozen=True)
class Folder:
    drive_id: int
    drive_name: str
    id: int
    name: str
    path: str = ""

    @property
    def label(self) -> str:
        location = self.path or f"folder {self.id}"
        return f"{self.drive_name} — {location}"


def valid_https_url(value: Any) -> str:
    """Return a usable public URL or an empty string; never fabricate one."""
    if not isinstance(value, str):
        return ""
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username:
        return ""
    return value


class KDriveClient:
    def __init__(
        self,
        token: str,
        *,
        session: requests.Session | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not token.strip():
            raise AuthenticationError("An API token is required.")
        self.session = session or requests.Session()
        self._owns_session = session is None
        self.session.headers.update(
            {"Authorization": f"Bearer {token.strip()}", "Accept": "application/json"}
        )
        self._sleep = sleeper
        self._clock = clock
        self._last_call = 0.0

    def close(self) -> None:
        if self._owns_session:
            self.session.close()

    def __enter__(self) -> "KDriveClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _throttle(self) -> None:
        delay = MIN_REQUEST_INTERVAL - (self._clock() - self._last_call)
        if delay > 0:
            self._sleep(delay)
        self._last_call = self._clock()

    @staticmethod
    def _retry_delay(response: requests.Response, attempt: int) -> float:
        value = response.headers.get("Retry-After", "")
        if value:
            try:
                return min(max(float(value), 0.0), 60.0)
            except ValueError:
                try:
                    retry_at = parsedate_to_datetime(value).timestamp()
                    return min(max(retry_at - time.time(), 0.0), 60.0)
                except (TypeError, ValueError, OverflowError):
                    pass
        return min(2**attempt, 8)

    @staticmethod
    def _error_details(response: requests.Response) -> tuple[str, str]:
        try:
            error = response.json().get("error", {})
        except (ValueError, AttributeError):
            error = {}
        if not isinstance(error, dict):
            error = {}
        code = str(error.get("code") or "api_error")
        description = str(error.get("description") or "API request failed")[:240]
        return code, description

    def request(
        self,
        method: str,
        route: str,
        *,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        method = method.upper()
        attempts = MAX_READ_RETRIES if method == "GET" else 1
        for attempt in range(attempts):
            self._throttle()
            try:
                response = self.session.request(
                    method,
                    f"{API_BASE_URL}{route}",
                    params=params,
                    json=payload,
                    timeout=REQUEST_TIMEOUT,
                )
            except requests.RequestException as exc:
                if method != "GET":
                    raise AmbiguousWriteError(
                        "The response to link creation was lost. Rescan before doing anything else; "
                        "the link may already exist."
                    ) from None
                if attempt + 1 < attempts:
                    self._sleep(min(2**attempt, 8))
                    continue
                raise KDriveError(
                    f"Network problem while reading kDrive ({exc.__class__.__name__})."
                ) from None

            if response.status_code in (429, 502, 503, 504) and method == "GET" and attempt + 1 < attempts:
                self._sleep(self._retry_delay(response, attempt))
                continue
            if response.status_code == 401:
                raise AuthenticationError(
                    "The API token is invalid or expired. Create a token with the required scopes and reconnect."
                )
            code, description = self._error_details(response)
            if response.status_code == 403:
                raise AuthenticationError(
                    f"Access denied ({code}). Check that the token has accounts and drive scopes, "
                    "and that this user may manage the file."
                )
            if response.status_code == 404:
                raise NotFoundError(description)
            if not response.ok:
                error = KDriveError(f"kDrive returned HTTP {response.status_code}: {description}")
                if method != "GET" and response.status_code >= 500:
                    raise AmbiguousWriteError(
                        "kDrive failed while creating a link. Rescan before retrying; the link may exist."
                    ) from error
                raise error
            try:
                result = response.json()
            except ValueError:
                if method != "GET":
                    raise AmbiguousWriteError(
                        "Link creation returned an unreadable response. Rescan before retrying."
                    ) from None
                raise KDriveError("kDrive returned a non-JSON response.") from None
            if not isinstance(result, dict) or result.get("result") != "success":
                error = result.get("error", {}) if isinstance(result, dict) else {}
                description = error.get("description") if isinstance(error, dict) else None
                raise KDriveError(str(description or "Unsuccessful API response")[:240])
            return result
        raise KDriveError("The API request did not complete.")

    def accounts(self) -> list[dict[str, Any]]:
        """Return accessible accounts used to satisfy /2/drive's account_id."""
        accounts: list[dict[str, Any]] = []
        page = 1
        while True:
            response = self.request("GET", "/1/accounts", params={"page": page, "per_page": 100})
            data = response.get("data", [])
            if not isinstance(data, list):
                raise KDriveError("Unexpected account-list response.")
            accounts.extend(
                item for item in data if isinstance(item, dict) and isinstance(item.get("id"), int)
            )
            pages = int(response.get("pages") or 1)
            if page >= pages:
                return accounts
            page += 1

    def drives(self) -> list[Drive]:
        found: dict[int, Drive] = {}
        for account in self.accounts():
            account_id = int(account["id"])
            page = 1
            while True:
                response = self.request(
                    "GET", "/2/drive", params={"account_id": account_id, "page": page, "per_page": 100}
                )
                data = response.get("data", [])
                if not isinstance(data, list):
                    raise KDriveError("Unexpected drive-list response.")
                for item in data:
                    if isinstance(item, dict) and isinstance(item.get("id"), int):
                        found[item["id"]] = Drive(
                            id=item["id"],
                            name=str(item.get("name") or f"kDrive {item['id']}"),
                            account_id=account_id,
                        )
                pages = int(response.get("pages") or 1)
                if page >= pages:
                    break
                page += 1
        return sorted(found.values(), key=lambda drive: (drive.name.casefold(), drive.id))

    @staticmethod
    def drive_path(drive_id: int, suffix: str, version: int = 3) -> str:
        return f"/{version}/drive/{drive_id}{suffix}"

    def folder_matches(self, drive: Drive, folder_name: str) -> list[Folder]:
        response = self.request(
            "GET",
            self.drive_path(drive.id, "/files/search"),
            params={"query": folder_name, "directory_id": 1, "depth": "unlimited", "limit": 100},
        )
        data = response.get("data", [])
        if not isinstance(data, list):
            raise KDriveError("Unexpected folder-search response.")
        matches: list[Folder] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "dir" or str(item.get("name", "")).casefold() != folder_name.casefold():
                continue
            if not isinstance(item.get("id"), int):
                continue
            matches.append(
                Folder(
                    drive_id=drive.id,
                    drive_name=drive.name,
                    id=item["id"],
                    name=str(item["name"]),
                    path=str(item.get("path") or item.get("name") or ""),
                )
            )
        return matches

    def discover_folders(self, folder_name: str) -> tuple[list[Drive], list[Folder]]:
        drives = self.drives()
        matches: list[Folder] = []
        for drive in drives:
            matches.extend(self.folder_matches(drive, folder_name))
        return drives, matches

    def children(self, drive_id: int, folder_id: int) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        cursor: str | None = None
        seen: set[str] = set()
        while True:
            params = {"cursor": cursor} if cursor else None
            response = self.request(
                "GET", self.drive_path(drive_id, f"/files/{folder_id}/files"), params=params
            )
            data = response.get("data", [])
            if not isinstance(data, list):
                raise KDriveError("Unexpected directory-list response.")
            results.extend(item for item in data if isinstance(item, dict))
            if not response.get("has_more"):
                return results
            next_cursor = response.get("cursor")
            if not isinstance(next_cursor, str) or not next_cursor or next_cursor in seen:
                raise KDriveError("Directory pagination returned a missing or repeated cursor.")
            seen.add(next_cursor)
            cursor = next_cursor

    def get_share_link(self, drive_id: int, file_id: int) -> dict[str, Any] | None:
        try:
            response = self.request(
                "GET", self.drive_path(drive_id, f"/files/{file_id}/link", version=2)
            )
        except NotFoundError:
            return None
        data = response.get("data")
        if not isinstance(data, dict):
            raise KDriveError("Unexpected share-link response.")
        return data

    def create_share_link(self, drive_id: int, file_id: int, password: str) -> dict[str, Any]:
        if not password:
            raise KDriveError("A password is required for new links.")
        response = self.request(
            "POST",
            self.drive_path(drive_id, f"/files/{file_id}/link", version=2),
            payload={
                "right": "password",
                "password": password,
                "can_download": True,
                "can_edit": False,
                "can_comment": False,
                "can_request_access": False,
                "can_see_info": False,
                "can_see_stats": False,
            },
        )
        data = response.get("data")
        if not isinstance(data, dict) or not valid_https_url(data.get("url")):
            raise AmbiguousWriteError(
                "Link creation returned no usable URL. Rescan before retrying; do not repeat the request blindly."
            )
        return data
