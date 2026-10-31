"""Simple desktop GUI for the catalog generator (double-click run_gui.bat or: python app_gui.py)"""
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import generate_catalog as gc

BASE = os.path.dirname(os.path.abspath(__file__))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Raj & Sons - Catalog Generator")
        self.geometry("560x340")
        self.resizable(False, False)
        self.excel = tk.StringVar(value=os.path.join(BASE, "data", "website_export.xlsx"))
        self.images = tk.StringVar(value=os.path.join(BASE, "product_images"))
        self.out = tk.StringVar(value=os.path.join(BASE, "output_catalogs"))
        self.phone = tk.StringVar(value=gc.PHONE)
        self.status = tk.StringVar(value="Excel load karke 'Load Categories' dabayein.")
        self.df = None

        pad = {"padx": 10, "pady": 5}
        for r, (label, var, kind) in enumerate([
                ("Excel file", self.excel, "file"),
                ("Images folder", self.images, "dir"),
                ("Output folder", self.out, "dir")]):
            tk.Label(self, text=label).grid(row=r, column=0, sticky="w", **pad)
            tk.Entry(self, textvariable=var, width=48).grid(row=r, column=1, **pad)
            tk.Button(self, text="Browse",
                      command=lambda v=var, k=kind: self.browse(v, k)).grid(row=r, column=2, **pad)

        tk.Label(self, text="WhatsApp No.").grid(row=3, column=0, sticky="w", **pad)
        tk.Entry(self, textvariable=self.phone, width=48).grid(row=3, column=1, **pad)

        tk.Button(self, text="Load Categories", command=self.load).grid(row=4, column=0, **pad)
        self.combo = ttk.Combobox(self, state="readonly", width=45)
        self.combo.grid(row=4, column=1, **pad)

        tk.Button(self, text="Generate Selected", bg="#7A0C0C", fg="white",
                  command=lambda: self.run(False)).grid(row=5, column=1, sticky="w", **pad)
        tk.Button(self, text="Generate ALL", command=lambda: self.run(True)).grid(
            row=5, column=1, sticky="e", **pad)
        tk.Label(self, textvariable=self.status, fg="#333", wraplength=520,
                 justify="left").grid(row=6, column=0, columnspan=3, **pad)

    def browse(self, var, kind):
        p = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")]) if kind == "file" \
            else filedialog.askdirectory()
        if p:
            var.set(p)

    def load(self):
        try:
            self.df = gc.load_data(self.excel.get())
            cats = gc.list_categories(self.df)
            self.combo["values"] = cats
            if cats:
                self.combo.current(0)
            self.status.set(f"{len(cats)} categories mili.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def run(self, everything):
        if self.df is None:
            self.load()
            if self.df is None:
                return
        cats = list(self.combo["values"]) if everything else [self.combo.get()]
        if not cats or not cats[0]:
            messagebox.showwarning("Category", "Pehle category chunein.")
            return
        gc.PHONE = self.phone.get().strip() or gc.PHONE
        self.status.set("PDF ban rahi hai, thoda rukiye...")
        threading.Thread(target=self.work, args=(cats,), daemon=True).start()

    def work(self, cats):
        try:
            logo = os.path.join(BASE, "assets", "logo.png")
            for c in cats:
                pdf = os.path.join(self.out.get(), f"{gc.safe_name(c)}_Catalog.pdf")
                gc.build_catalog(self.excel.get(), self.images.get(), c, pdf, logo, df=self.df)
            self.after(0, lambda: self.status.set(f"Ho gaya! PDF yahan hai: {self.out.get()}"))
            self.after(0, lambda: messagebox.showinfo("Done", "Catalog ban gaya."))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))


if __name__ == "__main__":
    App().mainloop()
