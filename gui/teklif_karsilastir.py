# gui/teklif_karsilastir.py
import os
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from models.teklif import Teklif
from services.rapor_service import RaporService
from gui.dosya_yardimci import alim_klasoru_getir, klasoru_ac
from utils.ui_helpers import fare_tekerlegi_bagla

class TeklifKarsilastir:
    def __init__(self, parent, db, alim_id, ana_pencere):
        self.parent = parent
        self.db = db
        self.alim_id = alim_id
        self.ana_pencere = ana_pencere
        self.frame = None

        self.ihtiyaclar = []
        self.firmalar = []
        self.satir_hucreleri = {}
        self.firma_entry_sutunlari = []
        self.main_container = None

        self._olustur()

    def _olustur(self):
        self.frame = ttk.LabelFrame(self.parent, text="📊 TEKLİF KARŞILAŞTIRMA (Firmalardan Gelen Yazılı Teklifler)", padding=10)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.main_container = ttk.Frame(self.frame)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self._icerik_olustur()

    def yenile(self):
        """Ana pencere tarafından sekme değişiminde çağrılır."""
        if self.main_container and self.main_container.winfo_exists():
            for child in self.main_container.winfo_children():
                child.destroy()
            self._icerik_olustur()

    def _icerik_olustur(self):
        if not self.alim_id:
            ttk.Label(self.main_container, text="⚠️ Önce alım kaydını oluşturun!", bootstyle="danger").pack(pady=20)
            return

        self.ihtiyaclar = self.db.ihtiyac_getir(self.alim_id)
        if not self.ihtiyaclar:
            ttk.Label(self.main_container, text="⚠️ Önce ihtiyaç listesini girin!", bootstyle="danger").pack(pady=20)
            return

        informel_teklifler = self.db.teklifleri_getir(self.alim_id)
        if not informel_teklifler:
            ttk.Label(
                self.main_container,
                text="⚠️ Henüz firma/teklif girilmemiş! Önce Firma & Teklif Girişi adımını tamamlayın.",
                bootstyle="danger"
            ).pack(pady=20)
            return

        self.firmalar = []
        gorulen = set()
        for t in informel_teklifler:
            if t['firma_id'] not in gorulen:
                gorulen.add(t['firma_id'])
                self.firmalar.append({'firma_id': t['firma_id'], 'unvan': t['unvan']})
        self.firmalar.sort(key=lambda f: f['unvan'])

        # KDV Oranlarını Çek (EN GÜNCEL HALİ)
        self.db.cursor.execute("SELECT malzeme_adi, kdv_orani FROM yaklasik_maliyet WHERE alim_id=?", (self.alim_id,))
        self.kdv_dict = {row['malzeme_adi']: row['kdv_orani'] for row in self.db.cursor.fetchall()}

        ttk.Label(
            self.main_container,
            text="📌 Firmalara gönderilen Teklif Mektubu'ndan geri gelen K.D.V. hariç birim fiyatları giriniz.",
            font=("Arial", 10, "bold"),
            bootstyle="warning",
            wraplength=900,
            justify='left'
        ).pack(anchor='w', pady=5, padx=10)

        giris_frame = ttk.LabelFrame(self.main_container, text="💰 Firmalardan Gelen Teklif Fiyatları", padding=5)
        giris_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

        self.canvas = tk.Canvas(giris_frame, bg='white', highlightthickness=0)
        h_scrollbar = ttk.Scrollbar(giris_frame, orient="horizontal", command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(giris_frame, orient="vertical", command=self.canvas.yview)
        
        self.scrollable = ttk.Frame(self.canvas)
        self.scrollable.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        self.canvas.bind('<Configure>', self._canvas_configure)
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        fare_tekerlegi_bagla(self.scrollable, self.canvas)

        sabit_kolon = 3
        for col, baslik in enumerate(["No", "Malzeme Adı", "Miktar"]):
            lbl = ttk.Label(
                self.scrollable, text=baslik, font=("Arial", 9, "bold"),
                background='#E8E8E8', relief=tk.RIDGE, padding=3,
                width=(30 if col == 1 else 8)
            )
            lbl.grid(row=0, column=col, rowspan=2, padx=1, pady=1, sticky='nsew')

        for f_idx, firma in enumerate(self.firmalar):
            baslik_col = sabit_kolon + 3 * f_idx
            ttk.Label(
                self.scrollable, text=firma['unvan'], font=("Arial", 9, "bold"),
                background='#D6EAF8', relief=tk.RIDGE, padding=3
            ).grid(row=0, column=baslik_col, columnspan=3, padx=1, pady=1, sticky='nsew')
            ttk.Label(self.scrollable, text="Birim Fiyat", font=("Arial", 8, "bold"), background='#EAF2F8', relief=tk.RIDGE, padding=2, width=11).grid(row=1, column=baslik_col, padx=1, pady=1, sticky='nsew')
            ttk.Label(self.scrollable, text="Toplam (KDV'siz)", font=("Arial", 8, "bold"), background='#EAF2F8', relief=tk.RIDGE, padding=2, width=11).grid(row=1, column=baslik_col + 1, padx=1, pady=1, sticky='nsew')
            ttk.Label(self.scrollable, text="Toplam (KDV'li)", font=("Arial", 8, "bold"), background='#EAF2F8', relief=tk.RIDGE, padding=2, width=11).grid(row=1, column=baslik_col + 2, padx=1, pady=1, sticky='nsew')

        mevcut_resmi = {}
        for t in self.db.resmi_teklifleri_getir(self.alim_id):
            mevcut_resmi.setdefault(t['ihtiyac_id'], {})[t['firma_id']] = t['birim_fiyat']

        self.firma_entry_sutunlari = [[] for _ in self.firmalar]
        self.satir_hucreleri = {}

        for row_idx, kalem in enumerate(self.ihtiyaclar):
            grid_row = row_idx + 2
            kdv_orani = self.kdv_dict.get(kalem.malzeme_adi, 20.0)

            ttk.Label(self.scrollable, text=str(kalem.sira_no), font=("Arial", 10)).grid(row=grid_row, column=0, padx=2, pady=2)
            ttk.Label(self.scrollable, text=kalem.malzeme_adi[:35], width=30, anchor='w').grid(row=grid_row, column=1, padx=2, pady=2, sticky='w')
            ttk.Label(self.scrollable, text=f"{kalem.miktar} {kalem.birim}", width=10).grid(row=grid_row, column=2, padx=2, pady=2)

            hucreler = []
            for f_idx, firma in enumerate(self.firmalar):
                baslik_col = sabit_kolon + 3 * f_idx
                entry = ttk.Entry(self.scrollable, width=10, font=("Arial", 10))
                entry.grid(row=grid_row, column=baslik_col, padx=1, pady=1)

                toplam_label = ttk.Label(self.scrollable, text="", width=11, anchor='e', font=("Arial", 10))
                toplam_label.grid(row=grid_row, column=baslik_col + 1, padx=1, pady=1)
                
                kdvli_label = ttk.Label(self.scrollable, text="", width=11, anchor='e', font=("Arial", 10, "bold"), bootstyle="success")
                kdvli_label.grid(row=grid_row, column=baslik_col + 2, padx=1, pady=1)

                onceki = mevcut_resmi.get(kalem.id, {}).get(firma['firma_id'])
                if onceki:
                    entry.insert(0, str(onceki))

                entry.bind('<KeyRelease>', lambda e, ent=entry, lbl=toplam_label, lbl_kdv=kdvli_label, miktar=kalem.miktar, kdv=kdv_orani: self._toplam_guncelle(ent, lbl, lbl_kdv, miktar, kdv))
                entry.bind('<Return>', lambda e, col=f_idx, row=row_idx: self._entry_ileri_gotur(col, row))
                entry.bind('<Down>', lambda e, col=f_idx, row=row_idx: self._entry_ileri_gotur(col, row))

                self._toplam_guncelle(entry, toplam_label, kdvli_label, kalem.miktar, kdv_orani)

                hucreler.append({'entry': entry, 'toplam_label': toplam_label, 'kdvli_label': kdvli_label})
                self.firma_entry_sutunlari[f_idx].append(entry)

            self.satir_hucreleri[kalem.id] = hucreler

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        action_frame = ttk.Frame(self.main_container)
        action_frame.pack(fill=tk.X, pady=10, padx=10)

        ttk.Button(action_frame, text="💾 TEKLİFLERİ KAYDET", command=self._teklifleri_kaydet, bootstyle="success").pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="📋 PİYASA FİYAT ARAŞTIRMA TUTANAĞI", command=self._piyasa_tutanagi_olustur, bootstyle="info").pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="📝 KARAR TUTANAĞI", command=self._karar_tutanagi_olustur, bootstyle="primary").pack(side=tk.LEFT, padx=5)

        self.karsilastirma_frame = ttk.LabelFrame(self.main_container, text="🏆 Karşılaştırma Sonucu", padding=10)
        self.karsilastirma_frame.pack(fill=tk.X, pady=10, padx=10)
        self._karsilastirmayi_goster()

    def _canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _toplam_guncelle(self, entry, toplam_label, kdvli_label, miktar, kdv_orani):
        fiyat_str = entry.get().strip().replace(',', '.')
        if not fiyat_str:
            toplam_label.config(text="")
            kdvli_label.config(text="")
            return
        try:
            birim_fiyat = float(fiyat_str)
        except ValueError:
            toplam_label.config(text="")
            kdvli_label.config(text="")
            return
        toplam = birim_fiyat * miktar
        toplam_label.config(text=f"{toplam:,.2f}")
        kdvli = toplam * (1 + kdv_orani / 100)
        kdvli_label.config(text=f"{kdvli:,.2f}")

    def _entry_ileri_gotur(self, firma_index, satir_index):
        sutun = self.firma_entry_sutunlari[firma_index]
        if not sutun: return
        sonraki = satir_index + 1
        if sonraki >= len(sutun): sonraki = 0
        hedef = sutun[sonraki]
        hedef.focus_set()
        hedef.select_range(0, tk.END)

    def _teklifleri_kaydet(self):
        try:
            teklifler = []
            guncel_ihtiyaclar = self.db.ihtiyac_getir(self.alim_id)
            sira_to_id = {k.sira_no: k.id for k in guncel_ihtiyaclar}
            
            for eski_ihtiyac_id, hucreler in self.satir_hucreleri.items():
                kalem = next((k for k in self.ihtiyaclar if k.id == eski_ihtiyac_id), None)
                if not kalem: continue
                guncel_ihtiyac_id = sira_to_id.get(kalem.sira_no, eski_ihtiyac_id)

                for f_idx, hucre in enumerate(hucreler):
                    fiyat_str = hucre['entry'].get().strip().replace(',', '.')
                    if fiyat_str:
                        try:
                            birim_fiyat = float(fiyat_str)
                        except ValueError:
                            continue
                        if birim_fiyat > 0:
                            teklifler.append(Teklif(
                                alim_id=self.alim_id,
                                firma_id=self.firmalar[f_idx]['firma_id'],
                                ihtiyac_id=guncel_ihtiyac_id,
                                birim_fiyat=birim_fiyat,
                                toplam_fiyat=birim_fiyat * kalem.miktar
                            ))

            if not teklifler:
                messagebox.showwarning("Uyarı", "En az bir teklif fiyatı giriniz!")
                return

            self.db.resmi_teklif_kaydet(teklifler)
            if self.ana_pencere:
                self.ana_pencere.durum_guncelle(f"🟢 {len(teklifler)} resmi teklif kaydedildi ✅")

            messagebox.showinfo("Başarılı", f"✅ {len(teklifler)} teklif kaydedildi!")
            self._karsilastirmayi_goster()
        except Exception as e:
            messagebox.showerror("Hata", f"❌ Teklif kayıt hatası: {str(e)}")

    def _karsilastirmayi_goster(self):
        for child in self.karsilastirma_frame.winfo_children():
            child.destroy()

        sonuclar = self.db.resmi_teklif_karsilastir(self.alim_id)
        if not sonuclar:
            ttk.Label(self.karsilastirma_frame, text="Henüz kaydedilmiş resmi teklif yok.", bootstyle="secondary").pack(pady=5)
            return

        for i, sonuc in enumerate(sonuclar, 1):
            row = ttk.Frame(self.karsilastirma_frame)
            row.pack(fill=tk.X, pady=3)
            ttk.Label(row, text=f"#{i}", font=("Arial", 11, "bold"), width=4).pack(side=tk.LEFT, padx=5)
            ttk.Label(row, text=sonuc['unvan'], font=("Arial", 10), width=30, anchor='w').pack(side=tk.LEFT, padx=5)
            toplam = sonuc['toplam'] or 0
            ttk.Label(row, text=f"₺{toplam:,.2f} (KDV'siz)", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
            if i == 1:
                ttk.Label(row, text="🏆 EN UYGUN", font=("Arial", 9, "bold"), bootstyle="success").pack(side=tk.LEFT, padx=10)

        ttk.Button(
            self.karsilastirma_frame,
            text="✅ EN UYGUN TEKLİFİ KARAR TUTANAĞINA KAYDET",
            command=lambda: self._kazanan_sec(sonuclar),
            bootstyle="success"
        ).pack(pady=10)

    def _kazanan_sec(self, sonuclar):
        if not sonuclar: return
        kazanan = sonuclar[0]
        firma_id = kazanan['firma_id']
        toplam = kazanan['toplam'] or 0

        alim = self.db.alim_getir(self.alim_id)
        if alim and alim.alim_no:
            karar_no = f"KARAR-{alim.alim_no}"
        else:
            karar_no = f"KARAR-{datetime.now().year}-{self.alim_id}"

        self.db.kazanan_kaydet(self.alim_id, firma_id, toplam, karar_no)

        if self.ana_pencere:
            self.ana_pencere.durum_guncelle(f"🟢 Kazanan: {kazanan['unvan']} ✅")

        messagebox.showinfo("Başarılı", f"✅ Kazanan firma kaydedildi:\n{kazanan['unvan']}\nToplam: ₺{toplam:,.2f}\nKarar No: {karar_no}")

    def _output_dir(self) -> str:
        return alim_klasoru_getir(self.db, self.alim_id)

    def _cikti_klasoru_ac(self):
        klasoru_ac(self._output_dir())

    def _piyasa_tutanagi_olustur(self):
        try:
            alim = self.db.alim_getir(self.alim_id)
            kurum = self.db.kurum_getir()
            if not kurum:
                messagebox.showwarning("Uyarı", "Önce kurum bilgilerini girin!")
                return
            if not kurum.satin_alma_gorevlileri():
                messagebox.showwarning("Uyarı", "Kurum bilgilerinde Satın Alma Görevlileri girilmemiş!")
                return

            resmi_teklifler = self.db.resmi_teklifleri_getir(self.alim_id)
            if not resmi_teklifler:
                messagebox.showwarning("Uyarı", "Önce firmalardan gelen teklifleri girip kaydedin!")
                return

            rapor = RaporService(output_dir=self._output_dir())
            dosya = rapor.piyasa_fiyat_arastirma_tutanagi(alim, kurum, self.ihtiyaclar, resmi_teklifler)

            messagebox.showinfo("Başarılı", f"✅ Piyasa Fiyat Araştırma Tutanağı oluşturuldu:\n{os.path.basename(dosya)}")
            self._cikti_klasoru_ac()
        except Exception as e:
            messagebox.showerror("Hata", f"❌ Rapor oluşturma hatası: {str(e)}")

    def _karar_tutanagi_olustur(self):
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

            firma = self.db.firma_getir(karar['firma_id'])
            if not firma:
                messagebox.showerror("Hata", "Firma bilgisi bulunamadı!")
                return

            toplam_teklif_sayisi = len(self.firmalar)

            rapor = RaporService(output_dir=self._output_dir())
            dosya = rapor.karar_tutanagi(alim, kurum, firma, karar['kazanan_toplam_tutar'], karar['karar_no'], toplam_teklif_sayisi)

            messagebox.showinfo("Başarılı", f"✅ Karar Tutanağı oluşturuldu:\n{os.path.basename(dosya)}")
            self._cikti_klasoru_ac()
        except Exception as e:
            messagebox.showerror("Hata", f"❌ Rapor oluşturma hatası: {str(e)}")

    def kaydet(self) -> bool:
        return True