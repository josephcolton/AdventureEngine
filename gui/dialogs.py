"""Small pop-up windows: messages, questions, text reports and lists.

They are drawn with the program's own colors (instead of the system's
message boxes) so they match the light and dark themes, and so buttons can
say exactly what they do ("Save", "Don't Save") instead of "Yes" / "No".
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class _Dialog(tk.Toplevel):
    def __init__(self, app, title: str):
        super().__init__(app.root)
        self.app = app
        self.result = None
        p = app.palette
        self.title(title)
        self.configure(background=p["bg"], padx=18, pady=16)
        self.transient(app.root)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.bind("<Escape>", lambda e: self.cancel())

    def run(self):
        """Show the dialog over the main window and wait until it closes."""
        self.update_idletasks()
        root = self.app.root
        x = root.winfo_rootx() + max(0, (root.winfo_width() - self.winfo_reqwidth()) // 2)
        y = root.winfo_rooty() + max(0, (root.winfo_height() - self.winfo_reqheight()) // 3)
        self.geometry(f"+{x}+{y}")
        self.grab_set()
        self.focus_force()
        self.wait_window()
        return self.result

    def finish(self, value) -> None:
        self.result = value
        self.grab_release()
        self.destroy()

    def cancel(self) -> None:
        self.finish(None)

    def button_row(self, buttons: list[tuple[str, object]], default: int = 0) -> ttk.Frame:
        row = ttk.Frame(self)
        row.pack(side="bottom", anchor="e", pady=(14, 0))
        for n, (label, value) in enumerate(buttons):
            b = ttk.Button(row, text=label, command=lambda v=value: self.finish(v))
            b.pack(side="left", padx=(8 if n else 0, 0))
            if n == default:
                b.focus_set()
                self.bind("<Return>", lambda e, v=value: self.finish(v))
        return row


def choose(app, title: str, message: str, buttons: list[str],
           default: int = 0, cancel: str | None = None) -> str | None:
    """Ask a question with several buttons. Returns the label clicked."""
    d = _Dialog(app, title)
    d.button_row([(b, b) for b in buttons], default)
    ttk.Label(d, text=message, wraplength=420, justify="left").pack(anchor="w")
    if cancel:
        d.cancel = lambda: d.finish(cancel)
        d.protocol("WM_DELETE_WINDOW", d.cancel)
        d.bind("<Escape>", lambda e: d.cancel())
    return d.run()


def info(app, title: str, message: str) -> None:
    choose(app, title, message, ["OK"])


def confirm(app, title: str, message: str, yes: str = "Yes", no: str = "No") -> bool:
    return choose(app, title, message, [yes, no], cancel=no) == yes


def ask_text(app, title: str, prompt: str, initial: str = "") -> str | None:
    """Ask for a line of text. Returns None if cancelled."""
    d = _Dialog(app, title)
    p = app.palette
    var = tk.StringVar(value=initial)
    d.button_row([("OK", True), ("Cancel", None)])
    ttk.Label(d, text=prompt).pack(anchor="w", pady=(0, 6))
    entry = tk.Entry(d, textvariable=var, width=36, font=app.fonts.story,
                     background=p["field"], foreground=p["fg"], insertbackground=p["fg"],
                     relief="solid", borderwidth=1, highlightthickness=0)
    entry.pack(fill="x")
    entry.select_range(0, "end")
    entry.focus_set()
    d.bind("<Return>", lambda e: d.finish(True))
    if d.run():
        return var.get().strip() or None
    return None


def pick(app, title: str, prompt: str, labels: list[str], ok: str = "OK") -> int | None:
    """Choose one line from a list. Returns its index, or None."""
    d = _Dialog(app, title)
    d.resizable(True, True)
    p = app.palette

    def chosen():
        sel = box.curselection()
        return sel[0] if sel else None

    row = ttk.Frame(d)
    row.pack(side="bottom", anchor="e", pady=(14, 0))
    ttk.Button(row, text=ok, command=lambda: d.finish(chosen())).pack(side="left")
    ttk.Button(row, text="Cancel", command=d.cancel).pack(side="left", padx=(8, 0))

    ttk.Label(d, text=prompt).pack(anchor="w", pady=(0, 6))
    frame = ttk.Frame(d)
    frame.pack(fill="both", expand=True)
    box = tk.Listbox(frame, width=60, height=min(14, max(4, len(labels))),
                     font=app.fonts.ui, activestyle="none", exportselection=False,
                     background=p["field"], foreground=p["fg"],
                     selectbackground=p["select"], selectforeground=p["fg"],
                     relief="solid", borderwidth=1, highlightthickness=0)
    bar = ttk.Scrollbar(frame, command=box.yview)
    box.configure(yscrollcommand=bar.set)
    box.pack(side="left", fill="both", expand=True)
    bar.pack(side="right", fill="y")
    for label in labels:
        box.insert("end", label)
    if labels:
        box.selection_set(0)
    box.focus_set()
    box.bind("<Double-Button-1>", lambda e: d.finish(chosen()))
    d.bind("<Return>", lambda e: d.finish(chosen()))
    return d.run()


def show_text(app, title: str, text: str, heading: str = "") -> None:
    """A scrollable, read-only page of text (reports, help)."""
    d = _Dialog(app, title)
    d.resizable(True, True)
    p = app.palette
    d.button_row([("Close", None)])
    if heading:
        ttk.Label(d, text=heading, style="Bold.TLabel").pack(anchor="w", pady=(0, 8))
    frame = ttk.Frame(d)
    frame.pack(fill="both", expand=True)
    box = tk.Text(frame, wrap="word", width=78, height=min(26, max(6, text.count("\n") + 3)),
                  font=app.fonts.ui, background=p["field"], foreground=p["fg"],
                  relief="solid", borderwidth=1, highlightthickness=0, padx=10, pady=8)
    bar = ttk.Scrollbar(frame, command=box.yview)
    box.configure(yscrollcommand=bar.set)
    box.pack(side="left", fill="both", expand=True)
    bar.pack(side="right", fill="y")
    box.tag_configure("head", font=app.fonts.ui_bold)
    for line in text.splitlines():
        tag = ("head",) if line.endswith(":") and not line.startswith(" ") else ()
        box.insert("end", line + "\n", tag)
    box.configure(state="disabled")
    d.run()
