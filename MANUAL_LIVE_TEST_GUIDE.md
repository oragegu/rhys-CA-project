# Manual Live Test Guide

Use this guide while sitting with the teacher after class. The first session should use a separate test folder, not the real `CA Lilly recordings` folder.

## Goal of this session

Confirm that the application can safely:

1. Connect to the teacher's Infomaniak account.
2. Find a kDrive folder without asking for technical IDs.
3. Recognise existing and missing sharing links correctly.
4. Create exactly one password-protected test link.
5. Confirm that downloading works.
6. Rescan without creating a duplicate.
7. Export a usable CSV file.

Do not generate links for the real class recordings during this first session.

---

## A. Prepare before meeting the teacher

### 1. Prepare the computer

On the computer you will use for the test:

1. Install Python 3.11 or newer, including Tkinter.
2. Open a terminal in the project folder.
3. Create and activate a virtual environment.
4. Install the dependencies.
5. Run the offline tests.

On Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements-dev.txt
py -m pytest -m "not integration"
```

Expected result:

```text
21 passed, 1 deselected
```

Then start the application:

```powershell
py run_app.py
```

On macOS, activate the environment with:

```bash
source .venv/bin/activate
```

### 2. Prepare a safe kDrive folder

With the teacher, create a folder named:

```text
CA Lilly recordings TEST
```

Add three short, harmless MP4 files. Do not copy valuable or private class recordings unless necessary.

Suggested names:

```text
20261001-TEST-001.mp4
20261002-TEST-002.mp4
20261003-TEST-003.mp4
```

Set them up like this in the normal kDrive website:

| File | Preparation |
|---|---|
| `20261001-TEST-001.mp4` | Create a password-protected link and allow downloads. |
| `20261002-TEST-002.mp4` | Leave it without a sharing link. |
| `20261003-TEST-003.mp4` | Optional: create a public link without a password or disable downloads. |

Write down the existing link for `TEST-001`. You will compare it with the application's result.

### 3. Choose a temporary sharing password

Choose a password used only for this test. Do not use the real class password during the first test.

Write it on paper temporarily so both of you can type and verify it accurately. Destroy the note after testing if appropriate.

---

## B. Create the API token together

The teacher should create the token himself while signed in to Infomaniak. You may guide him, but he should not send the token to you or save it in an email.

Open the [Infomaniak API token page](https://manager.infomaniak.com/v3/ng/accounts/token/list).

Create a token with these two permissions:

- `accounts`
- `drive`

Copy the token. Keep the Infomaniak page open until the connection test succeeds.

Tell the teacher:

> This token lets the application work with kDrive without knowing your Infomaniak password. The application does not save it. Treat it like a password.

---

## C. Walk through the application

### Step 1 — Connect

1. Paste the token into **API token**.
2. Change **Folder name** to `CA Lilly recordings TEST`.
3. Click **Connect to kDrive**.
4. Wait for the status message.

Expected result:

- The app says it is connected.
- The test folder appears in the **Match** list.
- The teacher is not asked for a drive ID or folder ID.

If several folders appear, ask the teacher to identify the correct drive and folder path. This confirms that the folder chooser works.

Stop if:

- The app reports an authentication or permission error.
- The test folder cannot be found even though it is visible in kDrive.
- A folder from the wrong kDrive is selected.

Do not continue by guessing.

### Step 2 — Run the read-only scan

1. Confirm that the selected folder says `CA Lilly recordings TEST`.
2. Leave **Include subfolders** unticked unless you intentionally added a subfolder.
3. Click **Scan recordings**.

Say to the teacher:

> Scanning only reads information. It does not create, remove, or change any sharing links.

Expected results:

| Prepared file | Expected status |
|---|---|
| Existing password-protected link with downloads | `Existing` |
| No link | `Missing` |
| Public or download-disabled link | `Existing — check settings` |

Check all of the following:

- The correct number of MP4 recordings is shown.
- The filenames are correct.
- The URL for `TEST-001` exactly matches the existing URL you wrote down.
- `TEST-002` is marked `Missing`.
- No existing sharing settings changed in the kDrive website.

Stop if:

- An existing link is shown as `Missing`.
- The URL does not match kDrive.
- Any row says `Uncertain` and you do not understand why.
- Any existing link was changed.

Do not create a link until these checks pass.

### Step 3 — Create exactly one test link

1. Enter the temporary test password in **Password for new links**.
2. Click **Create one test link**.
3. Read the confirmation message aloud.
4. Confirm that it says only one link will be created.
5. Click **Yes**.

Expected result:

- Only `TEST-002` receives a new link.
- The other links remain unchanged.
- The new row says `Newly created`.

If the app reports `Uncertain`, stop. Do not click the button again. The request may have succeeded even if its response was lost. Scan the folder again before deciding what to do.

### Step 4 — Verify the new link privately

Do not rely on a normal browser window where the teacher is already signed in to Infomaniak.

1. When the app asks whether you are ready to verify the test link, click **Yes**. The link opens in the normal browser and the final verification question remains on screen.
2. Copy the URL from the browser's address bar. Do not use the normal signed-in browser window as proof that the link works.
3. Open a separate private or incognito browser window.
4. Paste the URL into that private window.
5. Try an incorrect password first.
6. Confirm that the incorrect password is rejected.
7. Enter the temporary test password.
8. Confirm that the correct video opens.
9. Confirm that a download option is available.
10. Download the small test file and confirm that it opens.
11. Return to the application's final verification question.

Only answer **Yes** to the application's verification question if all of these are true:

- A password was required.
- The wrong password failed.
- The correct password worked.
- The correct video opened.
- Downloading worked.

Otherwise, answer **No** and stop the test.

### Step 5 — Prove that rerunning is safe

1. Click **Scan recordings** again.
2. Wait for the scan to finish.

Expected result:

- The newly created link now appears as `Existing`.
- It is no longer counted as `Missing`.
- The URL is the same one that was just tested.
- No duplicate link is created.

This is the most important repeatability check.

### Step 6 — Export the CSV

1. Click **Export to CSV**.
2. Save it to the Desktop using the suggested filename.
3. Open it in Microsoft Excel.

Confirm:

- It opens normally without an import wizard.
- Every test MP4 has one row.
- Filenames and links are correct.
- Statuses make sense.
- The API token is not present.
- The sharing password is not present.

Delete the test CSV afterward if it is no longer needed.

---

## D. Results checklist

Complete this before testing the real recordings folder.

| Check | Pass / Fail | Notes |
|---|---|---|
| Offline tests pass |  |  |
| Token works with `accounts` and `drive` permissions |  |  |
| App finds the test folder automatically |  |  |
| Existing URL exactly matches kDrive |  |  |
| Missing link is detected correctly |  |  |
| Incompatible link is reported but not changed |  |  |
| One and only one test link is created |  |  |
| Wrong password is rejected |  |  |
| Correct password works |  |  |
| Downloading works |  |  |
| Rescan recognises the new link as existing |  |  |
| No duplicate link is created |  |  |
| CSV opens correctly in Excel |  |  |
| CSV contains no token or password |  |  |

If any check fails, do not use the production folder. Record the exact message, take a screenshot with the token and password hidden, and return to development.

---

## E. When the test passes

Do not create all production links immediately after the test merely because there is time left.

The safer next steps are:

1. Close the application so the temporary token and password leave memory.
2. Decide whether to keep or revoke the test token.
3. Review the completed checklist.
4. Package and test the Windows executable.
5. Arrange a second supervised session for the real `CA Lilly recordings` folder.

During the production session, first scan and export the inventory without creating anything. Review every expired, incompatible, or uncertain row before generating missing links.

