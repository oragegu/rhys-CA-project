# Infomaniak kDrive Bulk Sharing Link Manager

A small Windows-oriented Tkinter application for safely inventorying MP4 recordings, preserving existing kDrive public links, creating only missing password-protected links, and exporting an Excel-compatible CSV.

This project has been tested with mocked API responses. It has **not** been tested against the teacher's live account, and the Windows executable has **not** been built or run on Windows from this macOS development environment.

## Safety model

- Scanning is read-only and is the default workflow.
- Existing, expired, blocked, public, download-disabled, and uncertain links are never modified.
- A missing link is rechecked immediately before creation.
- `POST` requests are never automatically retried.
- An ambiguous write stops the batch and instructs the user to rescan.
- Bulk creation stays disabled until one newly created link is manually verified.
- Tokens and passwords stay in memory and are never logged or exported.

See [AUDIT.md](AUDIT.md) for the prototype assessment and [API_NOTES.md](API_NOTES.md) for verified API details.
Use [MANUAL_LIVE_TEST_GUIDE.md](MANUAL_LIVE_TEST_GUIDE.md) for the first supervised test with a real kDrive account.
Technical helpers can use [MAC_LINUX_MANUAL_TEST_GUIDE.md](MAC_LINUX_MANUAL_TEST_GUIDE.md) to validate the source application on macOS or Linux.
The teacher can use [TEACHER_PRE_MEETING_GUIDE.md](TEACHER_PRE_MEETING_GUIDE.md) to prepare a safe practice folder and explore read-only features before the supervised session.
The observed macOS setup and offline-test results are recorded in [MACOS_SETUP_AND_TEST_LOG.md](MACOS_SETUP_AND_TEST_LOG.md).

## Architecture

```text
src/kdrive_link_manager/
├── api_client.py   HTTP, discovery, pagination, retries, share-link routes
├── sharing.py      classification, dry-run scanning, idempotent creation
├── exporter.py     UTF-8-BOM and formula-safe CSV
├── gui.py          responsive Tkinter workflow
├── config.py       non-secret constants
└── main.py         application entry point
```

The only runtime dependency outside Python's standard library is `requests`.

## Authentication

For this single-user desktop utility, create a personal API token in Infomaniak Manager with the minimum scopes:

- `accounts` — discover account IDs without asking the teacher for them.
- `drive` — list drives/files and manage public share links.

The teacher creates and enters the token locally; it is not sent to the developer or any third party. The application intentionally does not remember it between launches.

## Development setup

Python 3.11 or newer is required.

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements-dev.txt
py run_app.py
```

On macOS/Linux, replace the activation command with `source .venv/bin/activate` and use `python` instead of `py`.

## Tests

All normal tests are offline and mock the API:

```powershell
py -m pytest -m "not integration"
```

An opt-in integration smoke test lists drives only; it performs no writes:

```powershell
set KDRIVE_INTEGRATION=1
set KDRIVE_TOKEN=your-dedicated-test-token
py -m pytest -m integration
```

Never use automated write tests against the teacher's account. Controlled link creation should use a dedicated test folder and the GUI's one-link test gate.

## Build the Windows executable

Run `build_windows.bat` on Windows 10/11. It installs build dependencies, runs offline tests, and creates:

```text
dist\kDrive-Link-Manager.exe
```

PyInstaller does not cross-compile a Windows executable from macOS. Build and launch the result on Windows before distribution. No administrator privileges should be needed. An unsigned executable may trigger a Windows SmartScreen warning.

## Build the macOS application

The project-local build entry point packages and launches the Tkinter app with PyInstaller:

```bash
./script/build_and_run.sh
```

Use `./script/build_and_run.sh --verify` to build, launch, and confirm that the process is running. The current release artifact is an unsigned Apple-silicon build for macOS 26 or newer. See [MACOS_INSTALL_INSTRUCTIONS.txt](MACOS_INSTALL_INSTRUCTIONS.txt) for recipient installation and Gatekeeper instructions.

## Troubleshooting

- **Access denied:** recreate the token with both `accounts` and `drive` scopes and confirm the user can manage the selected files.
- **Folder not found:** check spelling, then click **Find folders**. Search runs across every accessible kDrive.
- **Several matches:** select the correct drive/path from the Match list.
- **Uncertain after creation:** do not click create again. Rescan first; the link may already exist.
- **Expired or incompatible:** the app reports the link but deliberately leaves it unchanged. Adjust it manually in kDrive if desired.
- **Rate limit or temporary outage:** read requests use bounded backoff. Creation is never blindly retried.

