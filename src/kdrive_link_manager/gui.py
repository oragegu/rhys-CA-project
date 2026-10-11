"""Tkinter interface designed for a simple, guarded teacher workflow."""

from __future__ import annotations

import threading
import webbrowser
from pathlib import Path
from tkinter import BooleanVar, StringVar, Tk, filedialog, messagebox, ttk
from typing import Callable

from .api_client import Folder, KDriveClient, KDriveError
from .config import DEFAULT_EXPORT_NAME, DEFAULT_FOLDER_NAME
from .exporter import export_csv
from .sharing import LinkStatus, Recording, SharingService


class LinkManagerApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        root.title("kDrive Link Manager")
        root.geometry("1050x720")
        root.minsize(850, 600)

        self.token = StringVar()
        self.show_token = BooleanVar(value=False)
        self.folder_name = StringVar(value=DEFAULT_FOLDER_NAME)
        self.folder_choice = StringVar()
        self.password = StringVar()
        self.show_password = BooleanVar(value=False)
        self.recursive = BooleanVar(value=False)
        self.status = StringVar(value="Ready. Connecting and scanning are read-only.")
        self.summary = StringVar(value="No recordings scanned yet.")
        self.folders: list[Folder] = []
        self.folder_by_label: dict[str, Folder] = {}
        self.recordings: list[Recording] = []
        self.connected_token = ""
        self.busy = False
        self.test_verified = False
        self.verified_password = ""

        self._build()
        self.password.trace_add("write", lambda *_: self._update_buttons())
        self._update_buttons()

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(3, weight=1)

        ttk.Label(outer, text="kDrive Link Manager", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )

        connection = ttk.LabelFrame(outer, text="1. Connection", padding=10)
        connection.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        connection.columnconfigure(1, weight=1)
        ttk.Label(connection, text="API token").grid(row=0, column=0, sticky="w")
        self.token_entry = ttk.Entry(connection, textvariable=self.token, show="•")
        self.token_entry.grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Checkbutton(
            connection,
            text="Show",
            variable=self.show_token,
            command=lambda: self.token_entry.configure(show="" if self.show_token.get() else "•"),
        ).grid(row=0, column=2)
        self.connect_button = ttk.Button(connection, text="Connect to kDrive", command=self.connect)
        self.connect_button.grid(row=0, column=3, padx=(8, 0))

        folder_box = ttk.LabelFrame(outer, text="2. Folder and dry-run scan", padding=10)
        folder_box.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        folder_box.columnconfigure(1, weight=1)
        ttk.Label(folder_box, text="Folder name").grid(row=0, column=0, sticky="w")
        ttk.Entry(folder_box, textvariable=self.folder_name).grid(row=0, column=1, sticky="ew", padx=8)
        self.find_button = ttk.Button(folder_box, text="Find folders", command=self.find_folders)
        self.find_button.grid(row=0, column=2, padx=(0, 8))
        ttk.Label(folder_box, text="Match").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.folder_combo = ttk.Combobox(
            folder_box, textvariable=self.folder_choice, state="readonly", values=[]
        )
        self.folder_combo.grid(row=1, column=1, sticky="ew", padx=8, pady=(8, 0))
        self.scan_button = ttk.Button(folder_box, text="Scan recordings", command=self.scan)
        self.scan_button.grid(row=1, column=2, padx=(0, 8), pady=(8, 0))
        ttk.Checkbutton(folder_box, text="Include subfolders", variable=self.recursive).grid(
            row=1, column=3, sticky="w", pady=(8, 0)
        )

        result_box = ttk.LabelFrame(outer, text="3. Scan results", padding=10)
        result_box.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        result_box.columnconfigure(0, weight=1)
        result_box.rowconfigure(1, weight=1)
        ttk.Label(result_box, textvariable=self.summary).grid(row=0, column=0, sticky="w", pady=(0, 7))
        columns = ("filename", "url", "status", "notes")
        self.table = ttk.Treeview(result_box, columns=columns, show="headings", height=12)
        headings = {"filename": "Filename", "url": "Sharing link", "status": "Status", "notes": "Notes"}
        widths = {"filename": 280, "url": 310, "status": 160, "notes": 260}
        for column in columns:
            self.table.heading(column, text=headings[column])
            self.table.column(column, width=widths[column], minwidth=90)
        scroll = ttk.Scrollbar(result_box, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.grid(row=1, column=0, sticky="nsew")
        scroll.grid(row=1, column=1, sticky="ns")

        actions = ttk.LabelFrame(outer, text="4. New sharing links", padding=10)
        actions.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        actions.columnconfigure(1, weight=1)
        ttk.Label(actions, text="Password for new links").grid(row=0, column=0, sticky="w")
        self.password_entry = ttk.Entry(actions, textvariable=self.password, show="•")
        self.password_entry.grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Checkbutton(
            actions,
            text="Show",
            variable=self.show_password,
            command=lambda: self.password_entry.configure(show="" if self.show_password.get() else "•"),
        ).grid(row=0, column=2)
        ttk.Label(actions, text="Downloads are enabled for every new link.").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )
        self.test_button = ttk.Button(actions, text="Create one test link", command=self.create_test)
        self.test_button.grid(row=1, column=2, padx=8, pady=(8, 0))
        self.all_button = ttk.Button(actions, text="Generate remaining links", command=self.create_all)
        self.all_button.grid(row=1, column=3, pady=(8, 0))

        footer = ttk.Frame(outer)
        footer.grid(row=5, column=0, sticky="ew")
        footer.columnconfigure(1, weight=1)
        self.export_button = ttk.Button(footer, text="Export to CSV", command=self.export)
        self.export_button.grid(row=0, column=0, padx=(0, 12))
        ttk.Label(footer, textvariable=self.status, wraplength=730).grid(row=0, column=1, sticky="w")
        self.progress = ttk.Progressbar(footer, mode="determinate", length=180)
        self.progress.grid(row=0, column=2, sticky="e")

    def _set_busy(self, busy: bool) -> None:
        self.busy = busy
        self._update_buttons()

    def _run(self, work: Callable[[], object], done: Callable[[object], None]) -> None:
        self._set_busy(True)

        def target() -> None:
            try:
                result = work()
            except Exception as exc:  # converted to a UI error on the main thread
                self.root.after(0, lambda error=exc: self._failed(error))
            else:
                self.root.after(0, lambda: self._finished(done, result))

        threading.Thread(target=target, daemon=True).start()

    def _finished(self, done: Callable[[object], None], result: object) -> None:
        try:
            done(result)
        finally:
            self._set_busy(False)

    def _failed(self, exc: Exception) -> None:
        self._set_busy(False)
        message = str(exc) or exc.__class__.__name__
        self.status.set(message)
        messagebox.showerror("kDrive Link Manager", message)

    def _progress(self, current: int, total: int, name: str) -> None:
        def update() -> None:
            self.progress.configure(maximum=max(total, 1), value=current)
            self.status.set(f"Processing {current} of {total}: {name}")

        self.root.after(0, update)

    def _update_buttons(self) -> None:
        missing = any(row.status == LinkStatus.MISSING for row in self.recordings)
        connected = bool(self.connected_token)
        folder_selected = self.folder_choice.get() in self.folder_by_label
        normal = "normal"
        disabled = "disabled"
        self.connect_button.configure(state=disabled if self.busy else normal)
        self.find_button.configure(state=normal if connected and not self.busy else disabled)
        self.scan_button.configure(state=normal if folder_selected and not self.busy else disabled)
        self.test_button.configure(state=normal if missing and not self.busy else disabled)
        same_password = bool(self.verified_password) and self.password.get() == self.verified_password
        self.all_button.configure(
            state=normal if missing and self.test_verified and same_password and not self.busy else disabled
        )
        self.export_button.configure(state=normal if self.recordings and not self.busy else disabled)

    def connect(self) -> None:
        token = self.token.get().strip()
        if not token:
            messagebox.showwarning("API token required", "Enter the API token created in Infomaniak Manager.")
            return
        folder_name = self.folder_name.get().strip() or DEFAULT_FOLDER_NAME
        self.connected_token = ""
        self.folder_by_label = {}
        self.status.set("Connecting and finding the recordings folder…")

        def work() -> object:
            with KDriveClient(token) as client:
                return client.discover_folders(folder_name)

        def done(result: object) -> None:
            _, folders = result  # type: ignore[misc]
            self.connected_token = token
            self._set_folders(folders)

        self._run(work, done)

    def find_folders(self) -> None:
        token = self.token.get().strip()
        if token != self.connected_token:
            messagebox.showwarning("Reconnect required", "The API token changed. Connect again first.")
            return
        name = self.folder_name.get().strip()
        if not name:
            messagebox.showwarning("Folder name required", "Enter the recordings folder name.")
            return
        self.status.set("Searching all available kDrives…")

        def work() -> object:
            with KDriveClient(token) as client:
                return client.discover_folders(name)

        self._run(work, lambda result: self._set_folders(result[1]))  # type: ignore[index]

    def _set_folders(self, folders: list[Folder]) -> None:
        self.folders = folders
        self.folder_by_label = {folder.label: folder for folder in folders}
        values = list(self.folder_by_label)
        self.folder_combo.configure(values=values)
        self.folder_choice.set(values[0] if values else "")
        if not folders:
            self.status.set(f"Connected, but no folder named '{self.folder_name.get().strip()}' was found.")
            messagebox.showwarning("Folder not found", self.status.get())
        elif len(folders) == 1:
            self.status.set("Connected. The recordings folder is ready to scan.")
        else:
            self.status.set(f"Connected. {len(folders)} matching folders found; select the correct one.")
        self._update_buttons()

    def scan(self) -> None:
        folder = self.folder_by_label.get(self.folder_choice.get())
        if folder is None:
            return
        if self.token.get().strip() != self.connected_token:
            messagebox.showwarning("Reconnect required", "The API token changed. Connect again first.")
            return
        token = self.connected_token
        recursive = self.recursive.get()
        self.test_verified = False
        self.verified_password = ""
        self.status.set("Scanning is read-only. No kDrive settings will be changed.")
        self.progress.configure(value=0)

        def work() -> object:
            with KDriveClient(token) as client:
                return SharingService(client).scan_folder(folder, recursive=recursive, progress=self._progress)

        self._run(work, self._after_scan)

    def _after_scan(self, result: object) -> None:
        self.recordings = list(result)  # type: ignore[arg-type]
        self._refresh()
        if not self.recordings:
            self.status.set("The selected folder contains no MP4 recordings.")
        else:
            self.status.set("Dry run complete. Review every expired, incompatible, or uncertain row.")

    def _refresh(self) -> None:
        self.table.delete(*self.table.get_children())
        for index, row in enumerate(self.recordings):
            self.table.insert(
                "", "end", iid=str(index), values=(row.filename, row.url, row.status.value, row.note)
            )
        counts = {status: sum(row.status == status for row in self.recordings) for status in LinkStatus}
        self.summary.set(
            f"Total: {len(self.recordings)}   Existing: {counts[LinkStatus.EXISTING]}   "
            f"Missing: {counts[LinkStatus.MISSING]}   Needs attention: "
            f"{counts[LinkStatus.EXPIRED] + counts[LinkStatus.INCOMPATIBLE] + counts[LinkStatus.UNCERTAIN] + counts[LinkStatus.FAILED]}"
        )
        self._update_buttons()

    def _create(self, *, one: bool) -> None:
        password = self.password.get()
        if not password:
            messagebox.showwarning("Password required", "Enter the password to use for new sharing links.")
            return
        if self.token.get().strip() != self.connected_token:
            messagebox.showwarning("Reconnect required", "The API token changed. Connect and scan again first.")
            return
        if not one and password != self.verified_password:
            self.test_verified = False
            messagebox.showwarning(
                "Test again", "The password changed after the test. Create and verify one new test link again."
            )
            self._update_buttons()
            return
        missing = sum(row.status == LinkStatus.MISSING for row in self.recordings)
        amount = 1 if one else missing
        if not messagebox.askyesno(
            "Confirm link creation",
            f"Create {amount} new password-protected link(s) with downloads enabled?\n\n"
            "Existing, expired, and incompatible links will not be changed.",
        ):
            return
        token = self.connected_token

        def work() -> object:
            with KDriveClient(token) as client:
                return SharingService(client).create_missing(
                    self.recordings, password, limit=1 if one else None, progress=self._progress
                )

        self._run(work, lambda result: self._after_create(result, one, password))

    def create_test(self) -> None:
        self._create(one=True)

    def create_all(self) -> None:
        if not self.test_verified:
            messagebox.showwarning("Test first", "Create and verify one test link before the remaining links.")
            return
        self._create(one=False)

    def _after_create(self, result: object, one: bool, tested_password: str) -> None:
        previous = self.recordings
        self.recordings = list(result)  # type: ignore[arg-type]
        self._refresh()
        if one:
            created = [new for old, new in zip(previous, self.recordings) if old.status != new.status and new.status == LinkStatus.CREATED]
            if created:
                row = created[0]
                if messagebox.askyesno(
                    "Verify the test link",
                    "The test link will open in your browser. Use a private/incognito window.\n\n"
                    "After testing, click Yes only if it required the password and downloading worked.",
                ):
                    webbrowser.open(row.url)
                    self.test_verified = messagebox.askyesno(
                        "Test result",
                        "Did the link require the password AND allow the video to be downloaded?",
                    )
                    self.verified_password = tested_password if self.test_verified else ""
        self.status.set("Link creation finished. Rescan before retrying any Uncertain item.")
        self._update_buttons()

    def export(self) -> None:
        destination = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=DEFAULT_EXPORT_NAME,
            filetypes=[("CSV files", "*.csv")],
        )
        if not destination:
            return
        try:
            export_csv(destination, self.recordings)
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        self.status.set(f"CSV saved as {Path(destination).name}. No token or password was exported.")
        messagebox.showinfo("Export complete", "The CSV was saved successfully.")

