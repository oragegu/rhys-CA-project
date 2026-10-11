# kDrive Link Manager — Safe Practice Before Our Meeting

Hello!

This guide lets you become familiar with the kDrive Link Manager before we meet. You will work only with a new practice folder and a few harmless test videos.

Please do **not** use the real `CA Lilly recordings` folder yet. We will work with the real recordings together after the practice test succeeds.

## What the application does

The kDrive Link Manager can:

- Find a folder in your kDrive.
- List the MP4 videos in that folder.
- Show which videos already have sharing links.
- Show which videos do not have sharing links.
- Create password-protected links for videos that do not have one.
- Save the filenames and links in a CSV file for Excel.

It is designed not to replace or change an existing sharing link.

## The most important safety rule

For practice, always use this folder name:

```text
CA Lilly recordings TEST
```

Before clicking **Scan recordings**, look at the selected folder and make sure the word `TEST` is present.

If the selected folder says only `CA Lilly recordings`, stop and close the application.

---

## Part 1 — Create the practice folder

1. Open kDrive in your normal web browser.
2. Go to a place where you are allowed to create a folder.
3. Create a new folder.
4. Name it exactly:

   ```text
   CA Lilly recordings TEST
   ```

5. Open the new folder.

This is separate from the real recordings folder. Nothing in the real folder needs to be moved or copied.

## Part 2 — Add a few harmless test videos

Add three short videos that are safe to use for practice. They should not contain a real class or anything private.

If possible, rename them:

```text
20261001-TEST-001.mp4
20261002-TEST-002.mp4
20261003-TEST-003.mp4
```

The videos can all contain the same harmless test recording. They only need to be valid MP4 files that open normally.

Do not upload all the real class recordings to this test folder.

## Part 3 — Prepare different sharing examples

This part helps us check whether the application understands existing links correctly.

### Test video 1 — Existing protected link

In the normal kDrive website:

1. Select `20261001-TEST-001.mp4`.
2. Create a sharing link.
3. Protect it with a temporary test password.
4. Allow downloading.
5. Copy the URL into a temporary note.

Do not use the real class password. Use a temporary practice password that you can remember during the test.

### Test video 2 — No link

Leave `20261002-TEST-002.mp4` without a sharing link.

### Test video 3 — Optional different settings

For `20261003-TEST-003.mp4`, you may either:

- Leave it without a sharing link; or
- Create a public link without a password; or
- Create a link but turn downloading off.

This third example is optional. We can prepare it together during our meeting.

---

## Part 4 — Create the API token

The application needs a special Infomaniak token. The token allows the application to work with kDrive without knowing your Infomaniak password.

Treat the token like a password:

- Do not email it.
- Do not send it in a message.
- Do not put it in a screenshot.
- Do not paste it into a document.
- Do not give it to the developer.

Open the [Infomaniak API token page](https://manager.infomaniak.com/v3/ng/accounts/token/list) while signed in to your own account.

Create a token with these two permissions:

- `accounts`
- `drive`

If you are unsure about any option, stop here. We can create the token together during our meeting.

The application does not save the token. Closing the application removes it from the application.

---

## Part 5 — Open the application

Before we have a Windows executable, the application may need to be started by the person helping with the test. If you have already been given a working application file, open it in the normal way.

You should see a window called:

```text
kDrive Link Manager
```

The window has four main areas:

1. **Connection**
2. **Folder and dry-run scan**
3. **Scan results**
4. **New sharing links**

## Part 6 — Connect to the practice folder

1. Paste your token into **API token**.
2. In **Folder name**, enter:

   ```text
   CA Lilly recordings TEST
   ```

3. Click **Connect to kDrive**.
4. Wait for the search to finish.

The practice folder should appear in the **Match** list.

If several folders appear, choose the one whose name ends in `TEST` and whose location you recognise.

Stop if:

- No test folder appears.
- You see only the real `CA Lilly recordings` folder.
- You do not recognise the kDrive or folder location.
- The application reports a permission or authentication error.

Do not guess which folder is correct.

## Part 7 — Safe practice: scan the folder

Scanning is read-only. It should not create, remove, or change any sharing links.

Before scanning, check again that the selected folder contains the word `TEST`.

Then:

1. Leave **Include subfolders** unticked.
2. Click **Scan recordings**.
3. Wait for the table to fill.

You should see your three test filenames.

Possible statuses are:

- **Existing** — the video already has a password-protected link and downloading is allowed.
- **Missing** — the video does not have a public sharing link.
- **Existing — check settings** — the existing link may have no password or may not allow downloading. The application leaves it unchanged.
- **Existing — expired** — the link has expired. The application leaves it unchanged.
- **Uncertain** — the application could not safely understand the result. Do not create anything for this file.

Compare the URL shown for `TEST-001` with the URL you copied from kDrive. They should be exactly the same.

You may safely practise connecting and scanning several times. Repeated scans should not change anything.

## Part 8 — What you may try before our meeting

You may safely practise these actions alone:

- Open and close the application.
- Enter the token.
- Search for `CA Lilly recordings TEST`.
- Select the practice folder.
- Scan the practice folder.
- Read the results.
- Export the practice results to a CSV file.
- Open the CSV in Excel.

The CSV contains sharing URLs, so delete the practice CSV when you no longer need it.

## Part 9 — What to leave for our meeting

Please wait for our meeting before clicking:

- **Create one test link**
- **Generate remaining links**

These buttons make changes on kDrive. We will create one link together, then test the password and downloading in a private browser window.

Never click **Generate remaining links** while the real recordings folder is selected unless we have reviewed the complete scan together.

---

## If something goes wrong

Stop and close the application if:

- You are not sure which folder is selected.
- An existing link is shown as missing.
- A URL is different from the one shown in kDrive.
- The application reports `Uncertain`.
- You see an error you do not understand.
- You accidentally select the real recordings folder.

Closing the application is safe. Do not keep clicking a button after an error.

You may take a screenshot of the error, but first hide or remove:

- The API token.
- The sharing password.
- Any private URL you do not want to share.

## Checklist before our meeting

If you are comfortable doing so, prepare the following:

- [ ] The folder `CA Lilly recordings TEST` exists.
- [ ] It contains two or three harmless MP4 videos.
- [ ] At least one test video has a password-protected link with downloading allowed.
- [ ] At least one test video has no sharing link.
- [ ] You know how to reach the Infomaniak token page.
- [ ] The application can find the test folder.
- [ ] A read-only scan shows the expected files.
- [ ] You have not used **Generate remaining links**.

It is completely fine to leave the token creation and application testing until our meeting. Preparing only the practice folder and videos will already save us time.
