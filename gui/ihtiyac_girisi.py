# gui/ihtiyac_girisi.py
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import openpyxl
from openpyxl.styles import Font
import os

from gui.dosya_yardimci import alim_klasoru_getir, klasoru_ac
from models.ihtiyac import IhtiyacKalemi
from services.birimler import BIRIMLER
from utils.ui_helpers import fare_tekerlegi_bagla


class OtomatikTamamlamaEntry(ttk.Frame):
    """Yazarken altında anlık liste açan, odağı çalmayan özel giriş kutusu."""
    def __init__(self, master, values, width=15, **kwargs):
        super().__init__(master, **kwargs)
        self.values = values
        self.entry = ttk.Entry(self, width=width)
        self.entry.grid(row=0, column=0, sticky="ew")
        self.columnconfigure(0, weight=1)

        self.popup = None
        self.listbox = None

        self.entry.bind('<KeyRelease>', self.on_keyrelease)
        self.entry.bind('<FocusOut>', self.on_focusout)
        self.entry.bind('<Down>', self.on_down)

    def on_keyrelease(self, event):
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Return', 'Escape', 'Tab'):
            return

        typed = self.entry.get().lower()
        if not typed:
            self.hide_popup()
            return

        starts_with = [v for v in self.values if v.lower().startswith(typed)]
        contains = [v for v in self.values if typed in v.lower() and v not in starts_with]
        filtered = starts_with + contains

        if filtered:
            self.show_popup(filtered)
        else:
            self.hide_popup()

    def show_popup(self, filtered):
        if self.popup is None:
            self.popup = tk.Toplevel(self)
            self.popup.overrideredirect(True)
            self.popup.attributes('-topmost', True)

            self.listbox = tk.Listbox(
                self.popup,
                height=min(8, len(filtered)),
                bg="white",
                fg="black",
                selectbackground="#3498DB",
                font=("Arial", 10)
            )
            self.listbox.pack(fill=tk.BOTH, expand=True)

            self.listbox.bind('<ButtonRelease-1>', self.on_select)
            self.listbox.bind('<Return>', self.on_select)
            self.listbox.bind('<Escape>', lambda e: self.hide_popup())

        self.listbox.delete(0, tk.END)
        for item in filtered:
            self.listbox.insert(tk.END, item)

        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        w = self.entry.winfo_width()
        h = self.listbox.winfo_reqheight()
        self.popup.geometry(f"{w}x{h}+{x}+{y}")

    def hide_popup(self):
        if self.popup:
            self.popup.destroy()
            self.popup = None
            self.listbox = None

    def on_select(self, event=None):
        if self.listbox:
            selection = self.listbox.curselection()
            if selection:
                value = self.listbox.get(selection[0])
                self.entry.delete(0, tk.END)
                self.entry.insert(0, value)
                self.hide_popup()
                self.entry.focus_set()
                self.entry.icursor(tk.END)

    def on_down(self, event):
        if self.listbox:
            self.listbox.focus_set()
            if not self.listbox.curselection():
                self.listbox.selection_set(0)
                self.listbox.activate(0)

    def on_focusout(self, event):
        self.after(200, self.check_focus)

    def check_focus(self):
        if self.popup:
            focused = self.focus_get()
            if focused != self.listbox and focused != self.entry:
                self.hide_popup()

    def get(self):
        return self.entry.get()

    def set(self, value):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)

    def destroy(self):
        self.hide_popup()
        super().destroy()


class OkasAramaPenceresi:
    """OKAS/CPV kodu arama ve seçme penceresi."""
    def __init__(self, parent, db, mevcut_kod="", secim_callback=None):
        self.db = db
        self.secim_callback = secim_callback
        self.pencere = ttk.Toplevel(parent)
        self.pencere.title("🔍 OKAS Kodu Ara")
        self.pencere.geometry("880x560")
        self.pencere.minsize(720, 420)
        self.pencere.transient(parent.winfo_toplevel() if hasattr(parent, 'winfo_toplevel') else parent)
        self.pencere.grab_set()
        self._olustur(mevcut_kod)

    def _olustur(self, mevcut_kod):
        ust = ttk.Frame(self.pencere, padding=10)
        ust.pack(fill=tk.X)
        ttk.Label(ust, text="Ara (kod veya isim):", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

        self.arama_var = tk.StringVar(value=mevcut_kod or "")
        self.entry_ara = ttk.Entry(ust, textvariable=self.arama_var, width=45, font=("Arial", 10))
        self.entry_ara.pack(side=tk.LEFT, padx=5)
        self.entry_ara.focus_set()

        ttk.Button(ust, text="🔍 Ara", command=self._ara, bootstyle="primary").pack(side=tk.LEFT, padx=5)
        ttk.Button(ust, text="Tümünü Göster", command=self._tumunu_getir, bootstyle="secondary").pack(side=tk.LEFT, padx=5)

        tablo_frame = ttk.Frame(self.pencere, padding=(10, 0))
        tablo_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("cpv", "isim", "tur")
        self.tree = ttk.Treeview(tablo_frame, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("cpv", text="CPV Kodu")
        self.tree.heading("isim", text="Kalem Adı")
        self.tree.heading("tur", text="Tür")
        self.tree.column("cpv", width=120, anchor="center")
        self.tree.column("isim", width=560, anchor="w")
        self.tree.column("tur", width=120, anchor="center")

        sb = ttk.Scrollbar(tablo_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", lambda e: self._sec())

        alt = ttk.Frame(self.pencere, padding=10)
        alt.pack(fill=tk.X)
        self.durum_lbl = ttk.Label(alt, text="", font=("Arial", 9))
        self.durum_lbl.pack(side=tk.LEFT, padx=5)

        ttk.Button(alt, text="✔ Seç", command=self._sec, bootstyle="success").pack(side=tk.RIGHT, padx=5)
        ttk.Button(alt, text="✖ İptal", command=self.pencere.destroy, bootstyle="danger-outline").pack(side=tk.RIGHT, padx=5)

        self.entry_ara.bind("<Return>", lambda e: self._ara())

        if mevcut_kod:
            self._ara()
        else:
            self._tumunu_getir()

    def _tumunu_getir(self):
        try:
            sonuclar = self.db.okas_ara("", limit=500)
            self._listele(sonuclar)
        except Exception as e:
            messagebox.showerror("Hata", f"Arama hatası:\n{e}", parent=self.pencere)

    def _ara(self):
        q = self.arama_var.get().strip()
        try:
            sonuclar = self.db.okas_ara(q, limit=500)
            self._listele(sonuclar)
        except Exception as e:
            messagebox.showerror("Hata", f"Arama hatası:\n{e}", parent=self.pencere)

    def _listele(self, rows):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in rows:
            self.tree.insert("", "end", values=(
                r.get('cpv_kodu', ''),
                r.get('kalem_adi', ''),
                r.get('kalem_turu', '') or ''
            ))

        self.durum_lbl.config(text=f"{len(rows)} sonuç gösteriliyor")

    def _sec(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Lütfen bir OKAS kodu seçin.", parent=self.pencere)
            return
        vals = self.tree.item(sel[0])['values']
        if self.secim_callback:
            self.secim_callback(str(vals[0]), str(vals[1]))
        self.pencere.destroy()


class OkasKoduEntry(ttk.Frame):
    """OKAS kodu için Entry + arama butonu içeren kompozit widget."""
    def __init__(self, master, db, width=14, initial=""):
        super().__init__(master)
        self.db = db

        self.entry = ttk.Entry(self, width=width, font=("Arial", 10))
        self.entry.pack(side=tk.LEFT)
        if initial:
            self.entry.insert(0, str(initial))

        self.btn = ttk.Button(self, text="🔍", width=3, command=self._ara, bootstyle="secondary-outline")
        self.btn.pack(side=tk.LEFT, padx=(2, 0))

    def _ara(self):
        OkasAramaPenceresi(self, self.db, self.get(), self._sec)

    def _sec(self, kod, isim):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, kod)

    def get(self):
        return self.entry.get().strip()

    def set(self, value):
        self.entry.delete(0, tk.END)
        if value:
            self.entry.insert(0, str(value))


class IhtiyacGirisi:
    def __init__(self, parent, db, alim_id, ana_pencere):
        self.parent = parent
        self.db = db
        self.alim_id = alim_id
        self.ana_pencere = ana_pencere
        self.ihtiyac_entryleri = []
        self.satir_sayisi = 0
        self.placeholderlar = {}
        self.canvas = None
        self.scrollable_frame = None
        self.frame = None
        self.btn_yeni = None
        self.btn_frame = None
        self.ebys_entry = None
        self._olustur()

    def _placeholder_ekle(self, entry, ornek):
        self.placeholderlar[entry] = f"Örn. {ornek}"
        self._placeholder_goster(entry)
        entry.bind("<FocusIn>", lambda event, e=entry: self._placeholder_temizle(e))
        entry.bind("<FocusOut>", lambda event, e=entry: self._placeholder_goster(e))

    def _placeholder_goster(self, entry):
        if not entry.get().strip():
            entry.delete(0, tk.END)
            entry.insert(0, self.placeholderlar[entry])
            entry.configure(foreground='gray')

    def _placeholder_temizle(self, entry):
        if entry.get().strip() == self.placeholderlar.get(entry):
            entry.delete(0, tk.END)
            entry.configure(foreground='black')

    def _entry_degeri(self, entry):
        deger = entry.get().strip()
        return "" if deger == self.placeholderlar.get(entry) else deger

    def _olustur(self):
        self.frame = ttk.LabelFrame(self.parent, text="📦 İHTİYAÇ LİSTESİ", padding=15)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Üst Kısım: EBYS ve Excel İşlemleri
        ust_frame = ttk.Frame(self.frame)
        ust_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(ust_frame, text="EBYS Onay Sayısı:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(5, 5))
        self.ebys_entry = ttk.Entry(ust_frame, width=20, font=("Arial", 10))
        self.ebys_entry.pack(side=tk.LEFT, padx=5)

        if self.alim_id:
            mevcut_alim = self.db.alim_getir(self.alim_id)
            if mevcut_alim and getattr(mevcut_alim, 'ebys_onay_sayisi', ''):
                self.ebys_entry.insert(0, mevcut_alim.ebys_onay_sayisi)

        ttk.Button(ust_frame, text="📥 Excel'den Yükle", command=self._excel_yukle, bootstyle="success").pack(side=tk.RIGHT, padx=5)
        ttk.Button(ust_frame, text="📤 Şablon İndir", command=self._sablon_indir, bootstyle="info").pack(side=tk.RIGHT, padx=5)

        # Liste Alanı
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Fare tekerleği desteği
        fare_tekerlegi_bagla(self.scrollable_frame, self.canvas)

        headers = ["Sıra", "Malzeme Adı", "OKAS Kodu", "Miktar", "Birim", ""]
        for col, header in enumerate(headers):
            ttk.Label(self.scrollable_frame, text=header, font=("Arial", 10, "bold")).grid(row=0, column=col, padx=5, pady=5, sticky='w')

        self.ihtiyac_entryleri = []
        self.satir_sayisi = 0

        mevcut_liste = []
        if self.alim_id:
            mevcut_liste = self.db.ihtiyac_getir(self.alim_id)

        if mevcut_liste:
            for kalem in mevcut_liste:
                self._kalem_ekle(kalem.malzeme_adi, kalem.miktar, kalem.birim, update_buttons=False, placeholder=False, kalem_id=kalem.id, okas_kodu=kalem.okas_kodu or "")
        else:
            self._kalem_ekle("Örnek Kalem", "1", "adet", update_buttons=False, placeholder=True)

        self._butonlari_ekle()
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _sablon_indir(self):
        dosya = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile="Ihtiyac_Sablonu.xlsx", filetypes=[("Excel", "*.xlsx")])
        if not dosya: return
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Malzeme Adı", "Miktar", "Birim", "OKAS Kodu"])
        ws["A1"].font = Font(bold=True)
        ws["B1"].font = Font(bold=True)
        ws["C1"].font = Font(bold=True)
        ws["D1"].font = Font(bold=True)
        ws.append(["Kalem Silgi", 10, "adet", "30192100"])
        ws.column_dimensions['A'].width = 40
        wb.save(dosya)
        messagebox.showinfo("Başarılı", "Şablon indirildi. Doldurup 'Excel'den Yükle' butonunu kullanabilirsiniz.")

    def _excel_yukle(self):
        dosya = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if not dosya: return
        try:
            wb = openpyxl.load_workbook(dosya)
            ws = wb.active
            # Mevcut satırları temizle
            for entry in list(self.ihtiyac_entryleri):
                self._satir_sil(entry['row'])
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[0] and row[1]:
                    self._kalem_ekle(
                        malzeme=str(row[0]), 
                        miktar=str(row[1]), 
                        birim=str(row[2]) if len(row) > 2 and row[2] else "adet",
                        okas_kodu=str(row[3]) if len(row) > 3 and row[3] else ""
                    )
            messagebox.showinfo("Başarılı", "Excel başarıyla yüklendi!")
        except Exception as e:
            messagebox.showerror("Hata", f"Excel okunamadı:\n{e}")

    def _butonlari_ekle(self):
        if hasattr(self, 'btn_yeni') and self.btn_yeni: self.btn_yeni.destroy()
        if hasattr(self, 'btn_frame') and self.btn_frame: self.btn_frame.destroy()
        
        btn_row = self.satir_sayisi + 1

        self.btn_yeni = ttk.Button(self.scrollable_frame, text="➕ Yeni Kalem Ekle", command=self._yeni_kalem_ekle, bootstyle="info-outline")
        self.btn_yeni.grid(row=btn_row, column=0, columnspan=3, pady=10, sticky='w')

        self.btn_frame = ttk.Frame(self.scrollable_frame)
        self.btn_frame.grid(row=btn_row, column=3, columnspan=3, pady=10, sticky='e')

        ttk.Button(self.btn_frame, text="💾 KAYDET", command=self.kaydet, bootstyle="success").pack(side=tk.LEFT, padx=5)
        ttk.Button(self.btn_frame, text="📄 WORD RAPOR", command=self._word_rapor_olustur, bootstyle="primary").pack(side=tk.LEFT, padx=5)
        ttk.Button(self.btn_frame, text="📝 WORD MEKTUP", command=self._word_mektup_olustur, bootstyle="primary").pack(side=tk.LEFT, padx=5)

        self.scrollable_frame.update_idletasks()
        if self.canvas: self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _kalem_ekle(self, malzeme="", miktar="", birim="adet", update_buttons=True, placeholder=False, kalem_id=None, okas_kodu=""):
        self.satir_sayisi += 1
        row = self.satir_sayisi

        lbl_sira = ttk.Label(self.scrollable_frame, text=str(row), font=("Arial", 10))
        lbl_sira.grid(row=row, column=0, padx=5, pady=3, sticky='w')

        entry_adi = ttk.Entry(self.scrollable_frame, width=50, font=("Arial", 10))
        if placeholder and malzeme:
            self._placeholder_ekle(entry_adi, malzeme)
        elif malzeme:
            entry_adi.insert(0, malzeme)
        entry_adi.grid(row=row, column=1, padx=5, pady=3, sticky='w')

        okas_entry = OkasKoduEntry(self.scrollable_frame, db=self.db, width=14, initial=okas_kodu or "")
        okas_entry.grid(row=row, column=2, padx=5, pady=3, sticky='w')

        entry_miktar = ttk.Entry(self.scrollable_frame, width=10, font=("Arial", 10))
        if placeholder and miktar:
            self._placeholder_ekle(entry_miktar, miktar)
        elif miktar:
            entry_miktar.insert(0, str(miktar))
        entry_miktar.grid(row=row, column=3, padx=5, pady=3)

        entry_birim = OtomatikTamamlamaEntry(self.scrollable_frame, values=BIRIMLER, width=15)
        entry_birim.set(birim if birim else "adet")
        entry_birim.grid(row=row, column=4, padx=5, pady=3, sticky="ew")

        sil_btn = ttk.Button(self.scrollable_frame, text="🗑️", width=4, command=lambda r=row: self._satir_sil(r), bootstyle="danger-outline")
        sil_btn.grid(row=row, column=5, padx=5, pady=3)

        self.ihtiyac_entryleri.append({
            'row': row, 'adi': entry_adi, 'okas': okas_entry, 'miktar': entry_miktar, 'birim': entry_birim, 'sil_btn': sil_btn, 'lbl_sira': lbl_sira, 'id': kalem_id
        })

        if update_buttons: self._butonlari_ekle()

    def _satir_sil(self, row):
        silinecek = None
        for i, entry in enumerate(self.ihtiyac_entryleri):
            if entry['row'] == row:
                silinecek = i
                break

        if silinecek is not None:
            entry = self.ihtiyac_entryleri[silinecek]
            entry['adi'].destroy()
            entry['okas'].destroy()
            entry['miktar'].destroy()
            entry['birim'].destroy()
            entry['sil_btn'].destroy()
            entry['lbl_sira'].destroy()

            self.ihtiyac_entryleri.pop(silinecek)
            self.satir_sayisi -= 1
            self._siralari_yeniden_duzenle()
            self._butonlari_ekle()

    def _siralari_yeniden_duzenle(self):
        for i, entry in enumerate(self.ihtiyac_entryleri, 1):
            entry['lbl_sira'].config(text=str(i))
            entry['row'] = i
            entry['lbl_sira'].grid_configure(row=i, column=0)
            entry['adi'].grid_configure(row=i, column=1)
            entry['okas'].grid_configure(row=i, column=2)
            entry['miktar'].grid_configure(row=i, column=3)
            entry['birim'].grid_configure(row=i, column=4)
            entry['sil_btn'].grid_configure(row=i, column=5)

    def _yeni_kalem_ekle(self):
        self._kalem_ekle("", "1", "adet", update_buttons=True, placeholder=False, okas_kodu="")

    def _word_rapor_olustur(self):
        try:
            from services.rapor_service import RaporService
            import datetime

            if not self.alim_id:
                messagebox.showwarning("Uyarı", "Önce alım kaydını oluşturun!")
                return
            if not self.kaydet(): return

            alim = self.db.alim_getir(self.alim_id)
            kurum = self.db.kurum_getir()
            if not kurum:
                messagebox.showerror("Hata", "Kurum bilgisi bulunamadı!")
                return

            ihtiyaclar = self.db.ihtiyac_getir(self.alim_id)
            if not ihtiyaclar:
                messagebox.showwarning("Uyarı", "İhtiyaç listesi boş!")
                return

            yil = alim.yil if alim.yil else datetime.datetime.now().year
            rapor = RaporService(output_dir=alim_klasoru_getir(self.db, self.alim_id))
            dosya = rapor.ihtiyac_listesi_raporu(alim, kurum, ihtiyaclar, yil)

            messagebox.showinfo("Başarılı", f"✅ Word raporu oluşturuldu:\n{dosya}")
            klasoru_ac(alim_klasoru_getir(self.db, self.alim_id))
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def _word_mektup_olustur(self):
        try:
            from services.rapor_service import RaporService

            if not self.alim_id:
                messagebox.showwarning("Uyarı", "Önce alım kaydını oluşturun!")
                return
            if not self.kaydet(): return

            alim = self.db.alim_getir(self.alim_id)
            kurum = self.db.kurum_getir()
            if not kurum:
                messagebox.showerror("Hata", "Kurum bilgisi bulunamadı!")
                return
            if not kurum.detsis_no:
                messagebox.showwarning("Uyarı", "Önce Kurum Bilgileri'nden DETSIS No'yu girin!")
                return

            ihtiyaclar = self.db.ihtiyac_getir(self.alim_id)
            if not ihtiyaclar:
                messagebox.showwarning("Uyarı", "İhtiyaç listesi boş!")
                return

            rapor = RaporService(output_dir=alim_klasoru_getir(self.db, self.alim_id))
            dosya = rapor.yaklasik_fiyat_arastirma_mektubu_word(alim, kurum, ihtiyaclar)

            messagebox.showinfo("Başarılı", f"✅ Word mektup oluşturuldu:\n{dosya}")
            klasoru_ac(alim_klasoru_getir(self.db, self.alim_id))
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def kaydet(self) -> bool:
        try:
            if not self.alim_id:
                messagebox.showwarning("Uyarı", "Önce kurum bilgilerini kaydedin!")
                return False

            kalemler = []
            for entry in self.ihtiyac_entryleri:
                adi = self._entry_degeri(entry['adi'])
                miktar_str = self._entry_degeri(entry['miktar'])
                birim = entry['birim'].get().strip()
                okas = entry['okas'].get()

                if adi and miktar_str:
                    try:
                        miktar = float(miktar_str.replace(',', '.'))
                        if miktar > 0:
                            kalem = IhtiyacKalemi(
                                malzeme_adi=adi,
                                miktar=miktar,
                                birim=birim if birim else "adet",
                                alim_id=self.alim_id,
                                sira_no=entry['row'],
                                okas_kodu=okas if okas else None,
                                id=entry.get('id')
                            )
                            kalemler.append(kalem)
                    except ValueError:
                        pass

            if not kalemler:
                messagebox.showwarning("Uyarı", "En az bir kalem giriniz!")
                return False

            self.db.ihtiyac_kaydet(kalemler)

            # EBYS Onay Sayısı'nı kaydet
            try:
                alim = self.db.alim_getir(self.alim_id)
                if alim:
                    yeni_ebys = (self.ebys_entry.get().strip() if self.ebys_entry else "")
                    if (alim.ebys_onay_sayisi or "") != yeni_ebys:
                        alim.ebys_onay_sayisi = yeni_ebys
                        self.db.alim_guncelle(alim)
            except Exception as e:
                print(f"EBYS güncelleme hatası: {e}")

            if self.ana_pencere:
                self.ana_pencere.durum_guncelle(f"🟢 {len(kalemler)} kalem ihtiyaç kaydedildi ✅")

            messagebox.showinfo("Başarılı", f"✅ {len(kalemler)} kalem ihtiyaç listesi kaydedildi!")
            return True

        except Exception as e:
            messagebox.showerror("Hata", f"❌ İhtiyaç kayıt hatası: {str(e)}")
            return False