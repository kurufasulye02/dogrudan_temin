# utils/ui_helpers.py
import tkinter as tk
from tkinter import ttk
import logging
import os
from datetime import datetime

# 1. LOGLAMA SİSTEMİ
def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = os.path.join(log_dir, f"hata_log_{datetime.now().strftime('%Y-%m-%d')}.txt")
    logging.basicConfig(
        filename=log_file,
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s',
        encoding='utf-8'
    )

# 2. FARE TEKERLEĞİ DESTEĞİ
def fare_tekerlegi_bagla(widget, canvas):
    def _on_mousewheel(event):
        if canvas and canvas.winfo_exists():
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    def _on_mousewheel_linux(event):
        if canvas and canvas.winfo_exists():
            canvas.yview_scroll(int(-1 * event.num), "units")
    def _bagla(w):
        w.bind("<MouseWheel>", _on_mousewheel, add="+")
        w.bind("<Button-4>", _on_mousewheel_linux, add="+")
        w.bind("<Button-5>", _on_mousewheel_linux, add="+")
        for child in w.winfo_children():
            _bagla(child)
    _bagla(widget)

# 3. ONDALIK SAYI FORMATLAMA (Currency Entry)
class CurrencyEntry(ttk.Entry):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.bind("<FocusOut>", self._format)
        self.bind("<FocusIn>", self._unformat)

    def _format(self, event=None):
        val = self.get().strip().replace('.', '').replace(',', '.')
        try:
            if val:
                num = float(val)
                formatted = f"{num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                self.delete(0, tk.END)
                self.insert(0, formatted)
        except ValueError:
            pass

    def _unformat(self, event=None):
        val = self.get().strip()
        if val:
            val = val.replace('.', '').replace(',', '.')
            self.delete(0, tk.END)
            self.insert(0, val)

    def get_float(self) -> float:
        val = self.get().strip().replace('.', '').replace(',', '.')
        try:
            return float(val) if val else 0.0
        except ValueError:
            return 0.0