# kDrive Link Manager — User Guide

## Before you start

You need an Infomaniak API token with **accounts** and **drive** access. Create it in your own Infomaniak Manager. Keep it private, just like a password.

The app does not save your token or the sharing password. You enter them again after closing the app.

## 1. Open the app

Double-click `kDrive-Link-Manager.exe`.

## 2. Connect to kDrive

1. Paste your API token into **API token**.
2. Click **Connect to kDrive**.
3. Wait while the app safely searches your available kDrives.

This step does not change any files or sharing links.

## 3. Select the recordings folder

The folder name is already set to `CA Lilly recordings`.

- If one folder is found, it is selected for you.
- If several folders have that name, open the **Match** list and choose the correct drive and path.
- If none is found, check the spelling and click **Find folders**.

Leave **Include subfolders** unticked unless recordings are also stored inside smaller folders.

## 4. Scan recordings

Click **Scan recordings**. Scanning is a dry run: it reads information but changes nothing.

Review the table:

- **Existing** — the link is password-protected and allows downloads.
- **Missing** — no public sharing link was found.
- **Existing — expired** — the old link has expired. The app leaves it alone.
- **Existing — check settings** — the old link may have no password, blocked access, or disabled downloads. The app leaves it alone.
- **Uncertain** or **Failed** — read the note and do not repeat link creation until you understand the problem.

## 5. Create one test link

1. Enter the password to use for all new links.
2. Click **Create one test link**.
3. Confirm the message.
4. Test the new link in a private/incognito browser window.
5. Check that the password is required and that the video can be downloaded.
6. Answer **Yes** only when both checks pass.

The sharing password is not saved in the CSV.

## 6. Create the remaining links

After the test passes, click **Generate remaining links** and confirm.

Existing links are never replaced. The app checks each missing link again just before creation. If a result is **Uncertain**, scan again before trying anything else.

## 7. Export the CSV

1. Click **Export to CSV**.
2. Choose a folder, such as Documents or Desktop.
3. Keep the suggested name `CA_Lilly_recordings_links.csv`, or choose another name.
4. Click **Save**.

The saved CSV opens in Microsoft Excel. It contains filenames, sharing links, statuses, and notes. It never contains your API token or sharing password.

Treat the CSV as private because anyone with a working link and the class password may be able to view a recording.

