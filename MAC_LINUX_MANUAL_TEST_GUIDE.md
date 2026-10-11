# Mac and Linux Manual Test Guide

This version is for the developer or technical helper. It assumes you are comfortable using a terminal. Use it to validate the source application before building the Windows executable.

The first live test must use a dedicated test folder. Do not begin with the production `CA Lilly recordings` folder.

## 1. Open the project

```bash
cd /path/to/kdrive_link_manager
```

On another computer, replace that path with the location where you copied or cloned the project.

## 2. Check Python and Tkinter

The project requires Python 3.11 or newer.

```bash
python3 --version
python3 -m tkinter
```

The second command should open a small Tk demonstration window. Close it after it appears.

If you see `No module named _tkinter`, that Python installation cannot run the GUI.

### macOS

For a Homebrew Python 3.14 installation, install the matching bindings:

```bash
brew install python-tk@3.14
/opt/homebrew/bin/python3.14 -m tkinter
```

The version number must match the Python interpreter. A `python-tk@3.14` package will not repair a virtual environment created from Apple Python 3.9.

Alternatively, install a current Python 3 release from [python.org](https://www.python.org/downloads/macos/), then reopen Terminal and repeat:

```bash
python3 -m tkinter
```

If several Python installations exist, identify them before creating the environment:

```bash
which -a python3
python3 -c 'import sys; print(sys.executable)'
```

Use the Python executable for which `python3 -m tkinter` succeeds.

#### Avoid accidentally using Apple Python 3.9

Before creating the environment, use the full Homebrew path:

```bash
/opt/homebrew/bin/python3.14 --version
/opt/homebrew/bin/python3.14 -m tkinter
/opt/homebrew/bin/python3.14 -m venv .venv314
source .venv314/bin/activate
python --version
python -c 'import sys; print(sys.executable)'
```

If the activated environment reports Python 3.9.6, it was created from Apple's old system Python. Do not use it for this project. Create a new environment with the explicit Homebrew path above.

A warning that urllib3 is using `LibreSSL 2.8.3` is another sign that the environment came from Apple Python 3.9. Do not hide the warning; correct the interpreter selection.

### Linux

Install the Tkinter package supplied by your Linux distribution if the test window does not open. Common package names are `python3-tk` or `python3-tkinter`. After installation, repeat:

```bash
python3 -m tkinter
```

Do not continue until the Tk window opens successfully.

## 3. Create a clean environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Confirm that the activated interpreter is inside the project:

```bash
python -c 'import sys; print(sys.executable)'
```

The output should end in something similar to:

```text
kdrive_link_manager/.venv/bin/python
```

On the documented Homebrew macOS setup, the environment is named `.venv314`, so the path should instead end in:

```text
kdrive_link_manager/.venv314/bin/python
```

## 4. Run the offline suite

```bash
python -m pytest -m "not integration"
```

Expected result:

```text
21 passed, 1 deselected
```

Do not proceed to a live account if an offline test fails.

## 5. Prepare the live test data

In kDrive, create:

```text
CA Lilly recordings TEST
```

Add three harmless, short MP4 files:

```text
20261001-TEST-001.mp4
20261002-TEST-002.mp4
20261003-TEST-003.mp4
```

Prepare these known states:

| File | Known starting state |
|---|---|
| `TEST-001` | Password-protected public link with downloads enabled |
| `TEST-002` | No public sharing link |
| `TEST-003` | Public link without a password, or downloads disabled |

Record the existing URLs and settings before launching the application. Screenshots are useful, but make sure they do not show the token or sharing password.

## 6. Create the test token

Create a personal API token from the [Infomaniak token page](https://manager.infomaniak.com/v3/ng/accounts/token/list) with:

- `accounts`
- `drive`

Keep the token only in memory or a temporary password manager entry. Do not add it to `.env`, source files, terminal history, screenshots, or test fixtures.

## 7. Optional read-only integration test

This test only lists accessible kDrives. It does not create, update, or delete anything.

Set the token without writing it into a shell command that will be saved in history:

```bash
read -s KDRIVE_TOKEN
export KDRIVE_TOKEN
export KDRIVE_INTEGRATION=1
python -m pytest -m integration
unset KDRIVE_TOKEN KDRIVE_INTEGRATION
```

Paste the token after the `read` command and press Return. The token will not be displayed.

Expected result:

```text
1 passed
```

If it fails, capture the error text without exposing the token. Do not move on to link creation until discovery works.

## 8. Launch the application

```bash
python run_app.py
```

Keep the terminal open. The application intentionally does not print tokens or passwords. Record any traceback if the GUI closes unexpectedly.

## 9. Validate read-only discovery

1. Paste the token into **API token**.
2. Enter `CA Lilly recordings TEST` as the folder name.
3. Click **Connect to kDrive**.
4. Confirm that all expected matching folders appear.
5. Select the correct test folder.
6. Click **Scan recordings**.

Verify:

- No numeric account, drive, or folder ID was requested.
- `TEST-001` is `Existing` and its URL is unchanged.
- `TEST-002` is `Missing`.
- `TEST-003` is `Existing — check settings`.
- The total number of MP4 files is correct.
- Non-MP4 files are ignored.
- Nothing changed in the kDrive web interface.

Stop if an existing link is classified as missing, a URL differs, or any unexpected row is `Uncertain`.

## 10. Validate one controlled write

Use a temporary password that is not used by the real classes.

1. Enter the password under **Password for new links**.
2. Click **Create one test link**.
3. Confirm that the dialog says exactly one link will be created.
4. Allow the application to create the link.
5. When the app asks whether you are ready to verify it, click **Yes**.
6. Copy the URL from the browser that opens.
7. Paste the URL into a separate private/incognito browser window.
8. Confirm that an incorrect password fails.
9. Confirm that the temporary password works.
10. Confirm that the correct file is displayed.
11. Download the file and confirm it opens.
12. Return to the application and answer **Yes** only if every check passed.

If creation becomes `Uncertain`, do not repeat the request. Rescan first because the link may already exist.

## 11. Validate password consistency

After the one-link test passes:

1. Change the password field by one character.
2. Confirm that **Generate remaining links** becomes disabled.
3. Restore the verified test password.
4. Confirm that the button becomes available again if missing test files remain.

This proves that the bulk operation cannot silently use a different password from the verified test.

## 12. Validate repeatability

Click **Scan recordings** again.

Verify:

- The new link is now `Existing`.
- Its URL is identical to the one just tested.
- It is no longer counted as missing.
- No second link was created.

Run a second scan and confirm that the results remain unchanged.

## 13. Validate CSV output

Export to a temporary location:

```text
CA_Lilly_recordings_links.csv
```

Open it in Excel, LibreOffice Calc, or Numbers and check:

- One row exists per MP4.
- Rows are sorted by filename.
- Unicode filenames display correctly.
- URLs and statuses match the GUI.
- The token is absent.
- The sharing password is absent.

You can also verify the UTF-8 BOM from the terminal:

```bash
xxd -l 3 /path/to/CA_Lilly_recordings_links.csv
```

Expected bytes:

```text
ef bb bf
```

Delete the temporary CSV when it is no longer required.

## 14. Safe negative tests

These tests should not modify kDrive:

- Enter an invalid token and confirm that authentication fails clearly.
- Use a token without the `accounts` scope and confirm the permission guidance.
- Search for a nonexistent folder.
- Create two test folders with the same name and confirm both can be selected.
- Scan an empty folder.
- Add a non-MP4 file and confirm it is ignored.
- Disconnect the network during a read-only scan and confirm the app recovers or reports the failure.

Do not intentionally interrupt the network during link creation. That produces an ambiguous result by design.

## 15. Capture the test result

Record:

- Operating system and version.
- Python version and executable path.
- Offline test result.
- Read-only integration result.
- Number of test MP4 files.
- Status shown for each known link state.
- Whether wrong and correct passwords behaved properly.
- Whether downloading worked.
- Whether rescanning preserved the URL.
- Whether CSV opened correctly.
- Any exact error message or traceback.

Never include the API token or sharing password in the report.

## 16. Clean up

When testing is complete:

```bash
unset KDRIVE_TOKEN KDRIVE_INTEGRATION
deactivate
```

Then:

1. Close the application and private browser windows.
2. Delete downloaded test videos and exported test CSV files.
3. Revoke the temporary token if it will not be reused.
4. Remove the test links or test folder manually in kDrive if they are no longer required.

Do not delete or alter the production recordings folder during cleanup.

## Release gate

Proceed to Windows packaging only when all of these are true:

- Offline tests pass.
- Account, drive, and folder discovery work against the live API.
- Existing-link URLs match kDrive exactly.
- Missing and incompatible states are classified correctly.
- One controlled link requires the password and permits download.
- Rescanning does not create a duplicate.
- CSV export contains no credentials.
- No unexplained `Uncertain` result remains.

