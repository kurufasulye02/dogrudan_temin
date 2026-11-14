# gui/muayene_kabul.py
import os
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkcalendar import DateEntry

from services.rapor_service import RaporService
from gui.dosya_yardimci import alim_klasoru_getir, klasoru_ac
from utils.ui_helpers import fare_tekerlegi_bagla

class MuayeneKabul:
    def __init__(self, parent, db, alim_id, ana_pencere):
        self.parent = parent
        self.db = db
        self.alim_id = alim_id
        self.ana_pencere = ana_pencere
        self.frame = None
        self.main_container = None
        self.muayene_entryleri = []
        self.teslim_tarihi_entry = None
        self.ihtiyaclar = []
        self.hizmet_entries = {}

        self._olustur()
        self.frame.bind("<Map>", self._ekran_yenile)

    def _olustur(self):
        self.frame = ttk.LabelFrame(self.parent, text="✅ MUAYENE VE KABUL", padding=15)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.main_container = ttk.Frame(self.frame)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self._icerik_olustur()

    def _ekran_yenile(self, event):
        if event.widget == self.frame:
            for child in self.main_container.winfo_children():
                child.destroy()
            self._icerik_olustur()

    def _icerik_olustur(self):
        if not self.alim_id:
            ttk.Label(self.main_container, text="⚠️ Önce alım kaydını oluşturun!", bootstyle="danger").pack(pady=20)
            return

        alim = self.db.alim_getir(self.alim_id)
        if not alim:
            ttk.Label(self.main_container, text="⚠️ Alım bulunamadı!", bootstyle="danger").pack(pady=20)
            return

        karar = self.db.kazanan_getir(self.alim_id)
        if not karar:
            ttk.Label(
                self.main_container, 
                text="⚠️ Önce Teklif Karşılaştırma adımında en uygun teklifi karar tutanağına kaydedin!", 
                bootstyle="danger", wraplength=600
            ).pack(pady=20)
            return

        firma = self.db.firma_getir(karar['firma_id'])
        if not firma:
            ttk.Label(self.main_container, text="⚠️ Kazanan firma bilgisi bulunamadı!", bootstyle="danger").pack(pady=20)
            return

        if alim.alim_turu == "hizmet":
            self._hizmet_arayuz_olustur(alim, karar, firma)
        else:
            self._mal_arayuz_olustur(alim, karar, firma)

    def _mal_arayuz_olustur(self, alim, karar, firma):
        ttk.Label(
            self.main_container, 
            text="📦 Teslim alınan malzemelerin kalem bazında muayene ve kabul işlemleri",
            font=("Arial", 11), bootstyle="primary"
        ).pack(pady=10)

        self.ihtiyaclar = self.db.ihtiyac_getir(self.alim_id)
        if not self.ihtiyaclar:
            ttk.Label(self.main_container, text="⚠️ İhtiyaç listesi boş!", bootstyle="danger").pack(pady=10)
            return

        ttk.Label(
            self.main_container, 
            text=f"🏢 Teslim eden firma: {firma.unvan}", 
            font=("Arial", 10, "bold"), bootstyle="success"
        ).pack(anchor='w', pady=2)

        tarih_frame = ttk.Frame(self.main_container)
        tarih_frame.pack(anchor='w', pady=10)
        
        ttk.Label(tarih_frame, text="Teslim Tarihi:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.teslim_tarihi_entry = DateEntry(tarih_frame, width=15, background='#2C3E50', foreground='white', borderwidth=2, date_pattern='dd.mm.yyyy', locale='tr_TR')
        self.teslim_tarihi_entry.pack(side=tk.LEFT)

        muayene_frame = ttk.Frame(self.main_container)
        muayene_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        canvas = tk.Canvas(muayene_frame, height=300, bg='white')
        scrollbar = ttk.Scrollbar(muayene_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        fare_tekerlegi_bagla(scrollable_frame, canvas)

        headers = ["No", "Malzeme", "Miktar", "Kabul Edilen", "Red Edilen"]
        for col, header in enumerate(headers):
            ttk.Label(scrollable_frame, text=header, font=("Arial", 9, "bold"), background='#E8E8E8', relief=tk.RIDGE, padding=3).grid(row=0, column=col, padx=1, pady=1, sticky='nsew')

        self.muayene_entryleri = []

        for row, kalem in enumerate(self.ihtiyaclar, 1):
            ttk.Label(scrollable_frame, text=str(kalem.sira_no)).grid(row=row, column=0, padx=5, pady=2)
            ttk.Label(scrollable_frame, text=kalem.malzeme_adi[:40], width=40, anchor='w').grid(row=row, column=1, padx=5, pady=2, sticky='w')
            ttk.Label(scrollable_frame, text=f"{kalem.miktar} {kalem.birim}", width=12).grid(row=row, column=2, padx=5, pady=2)

            entry_kabul = ttk.Entry(scrollable_frame, width=10)
            miktar_metin = str(int(kalem.miktar)) if kalem.miktar == int(kalem.miktar) else str(kalem.miktar)
            entry_kabul.insert(0, miktar_metin)
            entry_kabul.grid(row=row, column=3, padx=5, pady=2)

            entry_red = ttk.Entry(scrollable_frame, width=10)
            entry_red.insert(0, "0")
            entry_red.grid(row=row, column=4, padx=5, pady=2)

            self.muayene_entryleri.append((kalem.id, kalem.miktar, entry_kabul, entry_red))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = ttk.Frame(self.main_container)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="💾 MUAYENE KABUL KAYDET", command=self._mal_kaydet, bootstyle="success").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📋 KABUL TUTANAĞI OLUŞTUR", command=self._mal_rapor_olustur, bootstyle="primary").pack(side=tk.LEFT, padx=5)

    def _hizmet_arayuz_olustur(self, alim, karar, firma):
        ttk.Label(
            self.main_container, 
            text="📝 Hizmet İşleri Kabul İşlemleri",
            font=("Arial", 11), bootstyle="primary"
        ).pack(pady=10)

        mevcut = self.db.hizmet_kabul_getir(self.alim_id)

        # Kaydırılabilir form
        canvas = tk.Canvas(self.main_container, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        fare_tekerlegi_bagla(scrollable, canvas)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Form Alanları
        form_frame = ttk.Frame(scrollable, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        form_frame.columnconfigure(1, weight=1)

        def add_row(row, label, widget):
            ttk.Label(form_frame, text=label, font=("Arial", 10, "bold")).grid(row=row, column=0, sticky='e', padx=5, pady=5)
            widget.grid(row=row, column=1, sticky='w', padx=5, pady=5)

        # Bilgiler
        ttk.Label(form_frame, text=f"İşin Adı: {alim.isin_niteligi}", font=("Arial", 10)).grid(row=0, column=0, columnspan=2, sticky='w', pady=5)
        ttk.Label(form_frame, text=f"Yüklenici: {firma.unvan}", font=("Arial", 10)).grid(row=1, column=0, columnspan=2, sticky='w', pady=5)

        self.hizmet_entries['sozlesme_tarihi'] = DateEntry(form_frame, width=15, date_pattern='dd.mm.yyyy', locale='tr_TR')
        if mevcut.get('sozlesme_tarihi'):
            self.hizmet_entries['sozlesme_tarihi'].set_date(datetime.strptime(mevcut['sozlesme_tarihi'], '%d.%m.%Y'))
        add_row(2, "Sözleşme Tarihi:", self.hizmet_entries['sozlesme_tarihi'])

        self.hizmet_entries['sozlesme_bedeli'] = ttk.Entry(form_frame, width=20)
        if mevcut.get('sozlesme_bedeli'): self.hizmet_entries['sozlesme_bedeli'].insert(0, str(mevcut['sozlesme_bedeli']))
        add_row(3, "Sözleşme Bedeli (TL):", self.hizmet_entries['sozlesme_bedeli'])

        self.hizmet_entries['is_suresi'] = ttk.Entry(form_frame, width=10)
        if mevcut.get('is_suresi'): self.hizmet_entries['is_suresi'].insert(0, str(mevcut['is_suresi']))
        add_row(4, "İşin Süresi (Takvim Günü):", self.hizmet_entries['is_suresi'])

        self.hizmet_entries['is_bitis_tarihi'] = DateEntry(form_frame, width=15, date_pattern='dd.mm.yyyy', locale='tr_TR')
        if mevcut.get('is_bitis_tarihi'):
            self.hizmet_entries['is_bitis_tarihi'].set_date(datetime.strptime(mevcut['is_bitis_tarihi'], '%d.%m.%Y'))
        add_row(5, "İşin Bitiş Tarihi:", self.hizmet_entries['is_bitis_tarihi'])

        self.hizmet_entries['sure_uzatimi'] = ttk.Entry(form_frame, width=10)
        self.hizmet_entries['sure_uzatimi'].insert(0, str(mevcut.get('sure_uzatimi', 0)))
        add_row(6, "Varsa Süre Uzatımı (Gün):", self.hizmet_entries['sure_uzatimi'])

        self.hizmet_entries['uzatim_dahil_bitis'] = DateEntry(form_frame, width=15, date_pattern='dd.mm.yyyy', locale='tr_TR')
        if mevcut.get('uzatim_dahil_bitis'):
            self.hizmet_entries['uzatim_dahil_bitis'].set_date(datetime.strptime(mevcut['uzatim_dahil_bitis'], '%d.%m.%Y'))
        add_row(7, "Uzatım Dahil Bitiş Tarihi:", self.hizmet_entries['uzatim_dahil_bitis'])

        self.hizmet_entries['isin_bitirildigi_tarih'] = DateEntry(form_frame, width=15, date_pattern='dd.mm.yyyy', locale='tr_TR')
        if mevcut.get('isin_bitirildigi_tarih'):
            self.hizmet_entries['isin_bitirildigi_tarih'].set_date(datetime.strptime(mevcut['isin_bitirildigi_tarih'], '%d.%m.%Y'))
        add_row(8, "İşin Bitirildiği Tarih:", self.hizmet_entries['isin_bitirildigi_tarih'])

        ttk.Separator(form_frame, orient='horizontal').grid(row=9, column=0, columnspan=2, sticky='ew', pady=10)

        # Karar Türü
        self.hizmet_entries['karar_turu'] = tk.StringVar(value=mevcut.get('karar_turu', 'Öğretmenler Kurulu Kararı'))
        kr_frame = ttk.Frame(form_frame)
        ttk.Radiobutton(kr_frame, text="Öğretmenler Kurulu Kararı", variable=self.hizmet_entries['karar_turu'], value="Öğretmenler Kurulu Kararı").pack(side=tk.LEFT)
        ttk.Radiobutton(kr_frame, text="Makam Oluru", variable=self.hizmet_entries['karar_turu'], value="Makam Oluru").pack(side=tk.LEFT, padx=10)
        add_row(10, "Karar Türü:", kr_frame)

        self.hizmet_entries['karar_tarihi'] = DateEntry(form_frame, width=15, date_pattern='dd.mm.yyyy', locale='tr_TR')
        if mevcut.get('karar_tarihi'):
            self.hizmet_entries['karar_tarihi'].set_date(datetime.strptime(mevcut['karar_tarihi'], '%d.%m.%Y'))
        add_row(11, "Karar Tarihi:", self.hizmet_entries['karar_tarihi'])

        ttk.Separator(form_frame, orient='horizontal').grid(row=12, column=0, columnspan=2, sticky='ew', pady=10)

        self.hizmet_entries['kabul_baslangic'] = DateEntry(form_frame, width=15, date_pattern='dd.mm.yyyy', locale='tr_TR')
        if mevcut.get('kabul_baslangic'):
            self.hizmet_entries['kabul_baslangic'].set_date(datetime.strptime(mevcut['kabul_baslangic'], '%d.%m.%Y'))
        add_row(13, "Kabul Başlangıç Tarihi:", self.hizmet_entries['kabul_baslangic'])

        self.hizmet_entries['kabul_bitis'] = DateEntry(form_frame, width=15, date_pattern='dd.mm.yyyy', locale='tr_TR')
        if mevcut.get('kabul_bitis'):
            self.hizmet_entries['kabul_bitis'].set_date(datetime.strptime(mevcut['kabul_bitis'], '%d.%m.%Y'))
        add_row(14, "Kabul Bitiş Tarihi:", self.hizmet_entries['kabul_bitis'])

        ttk.Label(form_frame, text="Ancak (1):", font=("Arial", 10, "bold")).grid(row=15, column=0, sticky='ne', padx=5, pady=5)
        self.hizmet_entries['ancak_notu'] = tk.Text(form_frame, height=3, width=50, font=("Arial", 10))
        self.hizmet_entries['ancak_notu'].grid(row=15, column=1, sticky='w', padx=5, pady=5)
        self.hizmet_entries['ancak_notu'].insert("1.0", mevcut.get('ancak_notu', ''))

        self.hizmet_entries['makam_adi'] = ttk.Entry(form_frame, width=40)
        self.hizmet_entries['makam_adi'].insert(0, mevcut.get('makam_adi', 'OKUL MÜDÜRLÜĞÜ'))
        add_row(16, "Onay Makamı:", self.hizmet_entries['makam_adi'])

        self.hizmet_entries['tutanak_tarihi'] = DateEntry(form_frame, width=15, date_pattern='dd.mm.yyyy', locale='tr_TR')
        if mevcut.get('tutanak_tarihi'):
            self.hizmet_entries['tutanak_tarihi'].set_date(datetime.strptime(mevcut['tutanak_tarihi'], '%d.%m.%Y'))
        else:
            self.hizmet_entries['tutanak_tarihi'].set_date(datetime.now())
        add_row(17, "Tutanak Tarihi:", self.hizmet_entries['tutanak_tarihi'])

        btn_frame = ttk.Frame(self.main_container)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="💾 KAYDET", command=self._hizmet_kaydet, bootstyle="success").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📋 HİZMET KABUL TUTANAĞI OLUŞTUR", command=self._hizmet_rapor_olustur, bootstyle="primary").pack(side=tk.LEFT, padx=5)


    def _mal_kaydet(self) -> bool:
        try:
            karar = self.db.kazanan_getir(self.alim_id)
            if not karar:
                messagebox.showwarning("Uyarı", "Önce karar verilmeli!")
                return False

            kalemler = []
            toplam_kabul = 0.0
            toplam_red = 0.0
            for ihtiyac_id, miktar, entry_kabul, entry_red in self.muayene_entryleri:
                try:
                    kabul = float(entry_kabul.get().strip().replace(',', '.') or 0)
                    red = float(entry_red.get().strip().replace(',', '.') or 0)
                except ValueError:
                    messagebox.showwarning("Uyarı", "Kabul/Red miktarları sayısal olmalı!")
                    return False

                if kabul + red > miktar + 1e-9:
                    messagebox.showwarning("Uyarı", f"Kabul + Red toplamı, sipariş miktarını ({miktar}) aşamaz!")
                    return False

                kalemler.append({'ihtiyac_id': ihtiyac_id, 'kabul_miktar': kabul, 'red_miktar': red})
                toplam_kabul += kabul
                toplam_red += red

            self.db.muayene_kabul_detay_kaydet(self.alim_id, kalemler)

            teslim_tarihi = self.teslim_tarihi_entry.get() if self.teslim_tarihi_entry else None
            self.db.muayene_kabul_kaydet(self.alim_id, karar['firma_id'], toplam_kabul, toplam_red, "Muayene kabul tamamlandı", teslim_tarihi)

            if self.ana_pencere:
                self.ana_pencere.durum_guncelle("🟢 Muayene kabul kaydedildi ✅")

            messagebox.showinfo("Başarılı", "✅ Muayene kabul kaydedildi!")
            return True

        except Exception as e:
            messagebox.showerror("Hata", str(e))
            return False

    def _mal_rapor_olustur(self):
        try:
            karar = self.db.kazanan_getir(self.alim_id)
            if not karar:
                messagebox.showwarning("Uyarı", "Önce en uygun teklifi karar tutanağına kaydedin!")
                return

            alim = self.db.alim_getir(self.alim_id)
            kurum = self.db.kurum_getir()
            if not kurum:
                messagebox.showwarning("Uyarı", "Önce kurum bilgilerini girin!")
                return
            if not kurum.muayene_kabul_gorevlileri():
                messagebox.showwarning("Uyarı", "Kurum bilgilerinde Muayene ve Kabul Komisyonu Görevlileri girilmemiş!")
                return

            firma = self.db.firma_getir(karar['firma_id'])
            if not firma:
                messagebox.showerror("Hata", "Firma bilgisi bulunamadı!")
                return

            muayene_detaylari = self.db.muayene_kabul_detaylarini_getir(self.alim_id)
            if not muayene_detaylari:
                messagebox.showwarning("Uyarı", "Önce muayene kabul verilerini girip kaydedin!")
                return

            teslim_tarihi = self.teslim_tarihi_entry.get() if self.teslim_tarihi_entry else None

            rapor = RaporService(output_dir=alim_klasoru_getir(self.db, self.alim_id))
            dosya = rapor.muayene_kabul_tutanagi(alim, kurum, firma, muayene_detaylari, teslim_tarihi)

            messagebox.showinfo("Başarılı", f"✅ Muayene ve Kabul Tutanağı oluşturuldu:\n{os.path.basename(dosya)}")
            klasoru_ac(alim_klasoru_getir(self.db, self.alim_id))
        except Exception as e:
            messagebox.showerror("Hata", f"❌ Rapor oluşturma hatası: {str(e)}")

    def _hizmet_kaydet(self) -> bool:
        try:
            veriler = {}
            for key in ['sozlesme_tarihi', 'is_bitis_tarihi', 'uzatim_dahil_bitis', 'isin_bitirildigi_tarih', 'karar_tarihi', 'kabul_baslangic', 'kabul_bitis', 'tutanak_tarihi']:
                if hasattr(self.hizmet_entries[key], 'get_date'):
                    veriler[key] = self.hizmet_entries[key].get_date().strftime('%d.%m.%Y')
                else:
                    veriler[key] = self.hizmet_entries[key].get()
            
            veriler['sozlesme_bedeli'] = float(self.hizmet_entries['sozlesme_bedeli'].get().replace(',', '.') or 0)
            veriler['is_suresi'] = int(self.hizmet_entries['is_suresi'].get() or 0)
            veriler['sure_uzatimi'] = int(self.hizmet_entries['sure_uzatimi'].get() or 0)
            veriler['karar_turu'] = self.hizmet_entries['karar_turu'].get()
            veriler['ancak_notu'] = self.hizmet_entries['ancak_notu'].get("1.0", tk.END).strip()
            veriler['makam_adi'] = self.hizmet_entries['makam_adi'].get()

            self.db.hizmet_kabul_kaydet(self.alim_id, veriler)
            
            if self.ana_pencere:
                self.ana_pencere.durum_guncelle("🟢 Hizmet kabul kaydedildi ✅")
            messagebox.showinfo("Başarılı", "✅ Hizmet kabul verileri kaydedildi!")
            return True
        except Exception as e:
            messagebox.showerror("Hata", f"Kayıt hatası: {e}")
            return False

    def _hizmet_rapor_olustur(self):
        if not self._hizmet_kaydet(): return

        alim = self.db.alim_getir(self.alim_id)
        kurum = self.db.kurum_getir()
        karar = self.db.kazanan_getir(self.alim_id)
        firma = self.db.firma_getir(karar['firma_id'])
        veriler = self.db.hizmet_kabul_getir(self.alim_id)

        try:
            rapor = RaporService(output_dir=alim_klasoru_getir(self.db, self.alim_id))
            dosya = rapor.hizmet_kabul_tutanagi(alim, kurum, firma, veriler)
            messagebox.showinfo("Başarılı", f"✅ Hizmet İşleri Kabul Tutanağı oluşturuldu:\n{os.path.basename(dosya)}")
            klasoru_ac(alim_klasoru_getir(self.db, self.alim_id))
        except Exception as e:
            messagebox.showerror("Hata", f"Rapor oluşturulamadı: {e}")

    def kaydet(self) -> bool:
        alim = self.db.alim_getir(self.alim_id)
        if alim and alim.alim_turu == "hizmet":
            return self._hizmet_kaydet()
        return self._mal_kaydet()