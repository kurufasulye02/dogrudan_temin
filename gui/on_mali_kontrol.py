# gui/on_mali_kontrol.py
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from services.on_mali_kontrol_maddeleri import (
    ON_MALI_KONTROL_MADDELERI, ana_madde_mi, CEVAPLANABILIR_MADDE_SAYISI, RADYO_GEREKTIRMEYEN_SATIRLAR
)
from services.rapor_service import RaporService
from gui.dosya_yardimci import alim_klasoru_getir, klasoru_ac
from utils.ui_helpers import fare_tekerlegi_bagla


class OnMaliKontrolPenceresi:
    """Ön Mali Kontrol Listesi (EK-32) doldurma penceresi."""

    def __init__(self, parent, db, alim_id, kaydet_sonrasi_callback=None):
        self.db = db
        self.alim_id = alim_id
        self.kaydet_sonrasi_callback = kaydet_sonrasi_callback
        self.secim_degiskenleri = {}
        self.radio_widgetlari = {}

        self.pencere = tk.Toplevel(parent)
        self.pencere.title("Ön Mali Kontrol Listesi (EK-32)")
        self.pencere.geometry("1000x750")
        self.pencere.minsize(800, 500)
        
        # Pencere simgesi (varsa)
        try:
            self.pencere.iconbitmap("icon.ico")
        except:
            pass

        self.pencere.protocol("WM_DELETE_WINDOW", self._kapat)
        self.pencere.transient(parent)
        
        # SORUNU ÇÖZEN AYARLAR:
        # grab_set() KALDIRILDI. Böylece masaüstüne geçiş yapıp geri dönebilirsiniz.
        # focus_force() ile ilk açılışta öne gelmesi sağlanır.
        self.pencere.focus_force() 
        
        self.kapandi = False

        self._olustur()

    def _olustur(self):
        kurum = self.db.kurum_getir()
        alim = self.db.alim_getir(self.alim_id)

        isin_niteligi = (alim.isin_niteligi if alim and hasattr(alim, 'isin_niteligi') and alim.isin_niteligi else '-')

        ust_frame = ttk.LabelFrame(self.pencere, text="Bilgiler", padding=10)
        ust_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        ttk.Label(ust_frame, text=f"Harcama Birimi: {kurum.kurum_adi if kurum else '-'}", font=("Arial", 10, "bold")).pack(anchor='w')
        ttk.Label(ust_frame, text=f"İşin Adı: {isin_niteligi}", font=("Arial", 10, "bold")).pack(anchor='w')
        ttk.Label(ust_frame, text=f"Gerçekleştirme Görevlisi: {kurum.gerceklestirme_gorevlisi_ad if kurum else '-'}", font=("Arial", 10, "bold")).pack(anchor='w')

        canvas_frame = ttk.Frame(self.pencere)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(canvas_frame, bg='white')
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Fare tekerleği desteği
        fare_tekerlegi_bagla(scrollable, canvas)

        basliklar = ["No", "Kontrol Edilecek Bilgi ve Belgeler", "Zorunlu\nDeğil", "Evet", "Hayır"]
        for col, baslik in enumerate(basliklar):
            ttk.Label(
                scrollable, 
                text=baslik, 
                font=("Arial", 9, "bold"), 
                background='#E8E8E8', 
                relief=tk.RIDGE, 
                padding=3, 
                justify='center'
            ).grid(row=0, column=col, sticky='nsew', padx=1, pady=1)
            
        scrollable.columnconfigure(1, weight=1)

        mevcut_cevaplar = self.db.on_mali_kontrol_getir(self.alim_id)

        for grid_row, (satir_no, sira_no, metin) in enumerate(ON_MALI_KONTROL_MADDELERI, start=1):
            ana_madde = ana_madde_mi(sira_no)
            font_stil = ("Arial", 9, "bold") if ana_madde else ("Arial", 9)
            arka_plan = '#F4F6F6' if ana_madde else None

            no_lbl = ttk.Label(scrollable, text=sira_no, font=font_stil, anchor='center')
            no_lbl.grid(row=grid_row, column=0, sticky='nsew', padx=1, pady=1)

            metin_lbl = tk.Label(scrollable, text=metin, font=font_stil, anchor='w', justify='left', wraplength=600, bg=arka_plan or 'SystemButtonFace')
            metin_lbl.grid(row=grid_row, column=1, sticky='nsew', padx=1, pady=1)

            var = tk.StringVar(value=mevcut_cevaplar.get(satir_no, ""))
            self.secim_degiskenleri[satir_no] = var

            if satir_no in RADYO_GEREKTIRMEYEN_SATIRLAR:
                self.radio_widgetlari[satir_no] = []
                continue

            rb_listesi = []
            for col, secenek in ((2, 'zorunlu_degil'), (3, 'evet'), (4, 'hayir')):
                rb = ttk.Radiobutton(scrollable, variable=var, value=secenek, command=lambda sn=satir_no, sira=sira_no, s=secenek: self._secim_degisti(sn, sira, s))
                rb.grid(row=grid_row, column=col, padx=1, pady=1)
                rb_listesi.append(rb)
            self.radio_widgetlari[satir_no] = rb_listesi

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        alt_frame = ttk.Frame(self.pencere, padding=10)
        alt_frame.pack(fill=tk.X)
        
        self.durum_lbl = ttk.Label(alt_frame, text="", font=("Arial", 10, "bold"))
        self.durum_lbl.pack(side=tk.LEFT)
        
        ttk.Button(alt_frame, text="💾 Kaydet", command=self._kaydet, bootstyle="success").pack(side=tk.RIGHT, padx=5)
        ttk.Button(alt_frame, text="📄 Word Rapor Oluştur", command=self._rapor_olustur, bootstyle="primary").pack(side=tk.RIGHT, padx=5)

        self._durumu_guncelle()

    def _secim_degisti(self, satir_no, sira_no, secim):
        if secim == 'zorunlu_degil' and ana_madde_mi(sira_no):
            konum = next(i for i, (sn, _, _) in enumerate(ON_MALI_KONTROL_MADDELERI) if sn == satir_no)
            for sonraki_satir_no, sonraki_sira_no, _ in ON_MALI_KONTROL_MADDELERI[konum + 1:]:
                if ana_madde_mi(sonraki_sira_no):
                    break
                self.secim_degiskenleri[sonraki_satir_no].set('zorunlu_degil')
        self._durumu_guncelle()

    def _durumu_guncelle(self):
        doldurulan = sum(1 for v in self.secim_degiskenleri.values() if v.get())
        toplam = CEVAPLANABILIR_MADDE_SAYISI
        if doldurulan >= toplam:
            self.durum_lbl.config(text=f"✅ Tamamlandı ({doldurulan}/{toplam})", bootstyle="success")
        else:
            self.durum_lbl.config(text=f"⏳ {doldurulan}/{toplam} madde işaretlendi", bootstyle="warning")

    def _cevaplari_topla(self) -> dict:
        return {sn: v.get() for sn, v in self.secim_degiskenleri.items() if v.get()}

    def _kaydet(self):
        cevaplar = self._cevaplari_topla()
        self.db.on_mali_kontrol_kaydet(self.alim_id, cevaplar)
        messagebox.showinfo("Kaydedildi", f"✅ {len(cevaplar)}/{CEVAPLANABILIR_MADDE_SAYISI} madde kaydedildi.", parent=self.pencere)
        self._durumu_guncelle()
        if self.kaydet_sonrasi_callback:
            self.kaydet_sonrasi_callback()

    def _rapor_olustur(self):
        cevaplar = self._cevaplari_topla()
        if len(cevaplar) < CEVAPLANABILIR_MADDE_SAYISI:
            eksik = CEVAPLANABILIR_MADDE_SAYISI - len(cevaplar)
            if not messagebox.askyesno("Eksik Maddeler", f"{eksik} madde henüz işaretlenmedi. Yine de rapor oluşturulsun mu?", parent=self.pencere):
                return
        self.db.on_mali_kontrol_kaydet(self.alim_id, cevaplar)

        alim = self.db.alim_getir(self.alim_id)
        kurum = self.db.kurum_getir()
        if not kurum:
            messagebox.showwarning("Uyarı", "Kurum bilgisi bulunamadı!", parent=self.pencere)
            return

        try:
            rapor = RaporService(output_dir=alim_klasoru_getir(self.db, self.alim_id))
            dosya = rapor.on_mali_kontrol_raporu(alim, kurum, cevaplar)
            messagebox.showinfo("Başarılı", f"✅ Rapor oluşturuldu:\n{dosya}", parent=self.pencere)
            klasoru_ac(alim_klasoru_getir(self.db, self.alim_id))
        except Exception as e:
            messagebox.showerror("Hata", f"❌ Rapor oluşturma hatası: {str(e)}", parent=self.pencere)

        self._durumu_guncelle()
        if self.kaydet_sonrasi_callback:
            self.kaydet_sonrasi_callback()

    def _kapat(self):
        if self.kapandi:
            return
        self.kapandi = True
        if self.kaydet_sonrasi_callback:
            self.kaydet_sonrasi_callback()
        self.pencere.destroy()

    def kapat(self):
        self._kapat()