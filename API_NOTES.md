# Verified Infomaniak API behavior

Verified against the official developer portal and Infomaniak's official kDrive MCP implementation on 11 October 2026.

| Purpose | Verified route / behavior |
|---|---|
| Authentication | OAuth 2 bearer token in `Authorization: Bearer ...` |
| Accounts | `GET /1/accounts`; requires the `accounts` scope |
| Accessible drives | `GET /2/drive?account_id=...`; requires the `drive` scope |
| Search folders | `GET /3/drive/{drive_id}/files/search` with `query`, `directory_id`, and `depth` |
| List folder | `GET /3/drive/{drive_id}/files/{file_id}/files`; cursor pagination uses `has_more` and `cursor` |
| Root folder | File ID `1` is the documented drive root |
| Read public link | `GET /2/drive/{drive_id}/files/{file_id}/link` |
| Create public link | `POST /2/drive/{drive_id}/files/{file_id}/link` |
| Password mode | `right: "password"` with the `password` field |
| Downloads | `can_download: true`; returned under `capabilities.can_download` |
| Expiry / blocking | Returned as `valid_until` and `access_blocked` on the Share Link resource |
| Internal access | Email invitations use a separate `/access/invitations` API and are not public links |

The documented per-file public-link resource is singular. The application therefore preserves the one link returned for a file and never tries to enumerate or replace hypothetical additional links. A `404` from the link endpoint for a file that was just listed successfully is treated as “Missing”. Any malformed or failed read is “Uncertain” and is never eligible for automatic creation.

References:

- [Infomaniak API getting started](https://developer.infomaniak.com/getting-started)
- [List accounts](https://developer.infomaniak.com/docs/api/get/1/accounts)
- [Accessible drives](https://developer.infomaniak.com/docs/api/get/2/drive)
- [Get file or directory](https://developer.infomaniak.com/docs/api/get/3/drive/%7Bdrive_id%7D/files/%7Bfile_id%7D)
- [List folder children](https://developer.infomaniak.com/docs/api/get/3/drive/%7Bdrive_id%7D/files/%7Bfile_id%7D/files)
- [Get share link](https://developer.infomaniak.com/docs/api/get/2/drive/%7Bdrive_id%7D/files/%7Bfile_id%7D/link)
- [Create share link](https://developer.infomaniak.com/docs/api/post/2/drive/%7Bdrive_id%7D/files/%7Bfile_id%7D/link)
- [Official Infomaniak kDrive MCP server](https://github.com/Infomaniak/mcp-server-kdrive)

