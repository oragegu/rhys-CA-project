# Prototype audit

## What the prototype already did well

- Listed direct children with cursor pagination and filtered MP4 files.
- Used background threads so network work did not freeze Tkinter.
- Required an explicit scan, confirmation, and one-link test before bulk creation.
- Rechecked a file immediately before creating a link.
- Never retried a `POST`, stored credentials, or put credentials in CSV.
- Exported UTF-8-with-BOM CSV and neutralised common spreadsheet formulas.

## Important findings

1. Existing-link detection mixed two different concepts. Public share links use the documented singular `GET /2/drive/{drive_id}/files/{file_id}/link`. The fallback `/files/{file_id}/shares` was not the documented public-link route and could misclassify a file.
2. The prototype accepted several guessed URL response shapes. The documented Share Link resource has a direct `url` field; unexpected data must be treated as uncertain.
3. It asked the teacher to supply a numeric drive ID. The API supports account discovery (`GET /1/accounts`) followed by accessible-drive discovery (`GET /2/drive?account_id=...`).
4. Duplicate folder names produced an error instead of a safe chooser.
5. Existing links were not classified as expired, blocked, public (no password), or download-disabled.
6. Read requests had no targeted retry/backoff for rate limits or transient service failures.
7. API, workflow, export, and GUI logic were coupled in one file, which made isolated testing difficult.
8. Tests covered only six happy-path helpers and did not cover discovery, pagination, retries, repeatability, partial failures, expiry, or CSV bytes.
9. The old README required Python and a drive ID, contrary to the intended first-launch experience.

## Security assessment

The prototype did not hardcode or persist secrets, which should be preserved. Tokens and passwords remain memory-only in the revised application. Persistent credential storage is deliberately not enabled, so Windows Credential Manager is not required. The generated CSV contains access URLs and should still be treated as sensitive.

## Architectural decision

The revised code keeps Tkinter and `requests`, but separates the REST client, guarded sharing workflow, CSV exporter, and GUI. It uses the documented API-token flow for the first release. A custom desktop OAuth client would require registering and maintaining an Infomaniak application and redirect flow; that is disproportionate for one teacher and is not needed to avoid sharing credentials with the developer.

