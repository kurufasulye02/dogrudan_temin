# gui/ekap_islemleri.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from gui.dosya_yardimci import alim_klasoru_getir, klasoru_ac
from services.rapor_service import RaporService
from utils.ui_helpers import fare_tekerlegi_bagla

class EkapIslemleri:
    def __init__(self, parent, db, alim_id, ana_pencere):
        self.parent = parent
        self.db = db
        self.alim_id = alim_id
        self.ana_pencere = ana_pencere
        self.frame = None
        self.row_widgets = []
        self.main_container = None

        self._olustur()

    def _olustur(self):
        self.frame = ttk.LabelFrame(self.parent, text="📤 EKAP İŞLEMLERİ (Excel Şablonu Hazırlama)", padding=15)
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

        kazanan = self.db.kazanan_getir(self.alim_id)
        if not kazanan:
            ttk.Label(
                self.main_container, 
                text="⚠️ Önce Teklif Karşılaştırma adımında en uygun teklifi karar tutanağına kaydedin!", 
                bootstyle="danger"
            ).pack(pady=20)
            return

        firma = self.db.firma_getir(kazanan['firma_id'])
        if not firma:
            ttk.Label(self.main_container, text="⚠️ Kazanan firma bilgisi bulunamadı!", bootstyle="danger").pack(pady=20)
            return

        istekli_adi = firma.unvan

        self.ihtiyaclar = self.db.ihtiyac_getir(self.alim_id)
        if not self.ihtiyaclar:
            ttk.Label(self.main_container, text="⚠️ İhtiyaç listesi boş!", bootstyle="danger").pack(pady=20)
            return

        resmi_teklifler = self.db.resmi_teklifleri_getir(self.alim_id)
        kazanan_teklifler = {t['ihtiyac_id']: t['birim_fiyat'] for t in resmi_teklifler if t['firma_id'] == kazanan['firma_id']}

        # KDV oranlarını her açılışta güncel olarak çekiyoruz
        self.db.cursor.execute("SELECT malzeme_adi, kdv_orani FROM yaklasik_maliyet WHERE alim_id=?", (self.alim_id,))
        kdv_oranlari = {row['malzeme_adi']: row['kdv_orani'] for row in self.db.cursor.fetchall()}

        top_frame = ttk.Frame(self.main_container)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(top_frame, text="Tümü İçin Menşei Seç:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.global_mensei = ttk.Combobox(top_frame, values=["Yerli", "Yabancı", "Bilinmiyor"], state="readonly", width=15)
        self.global_mensei.pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Tümüne Uygula", command=self._apply_global_mensei, bootstyle="info-outline").pack(side=tk.LEFT, padx=5)

        ttk.Label(top_frame, text=f"İstekli: {istekli_adi}", font=("Arial", 10, "bold"), bootstyle="success").pack(side=tk.RIGHT, padx=10)

        table_frame = ttk.Frame(self.main_container)
        table_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(table_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))
        fare_tekerlegi_bagla(scrollable, canvas)

        headers = ["İş Kalemi", "Menşei", "Miktar", "Birim", "OKAS Kodu", "Toplam Fiyat (KDV'li)", "Para Birimi", "İstekli"]
        for col, header in enumerate(headers):
            ttk.Label(
                scrollable, text=header, font=("Arial", 9, "bold"), 
                background='#E8E8E8', relief=tk.RIDGE, padding=3
            ).grid(row=0, column=col, padx=1, pady=1, sticky='nsew')

        para_birimleri = ["TRY", "AUD", "CAD", "CHF", "DKK", "EUR", "GBP", "JPY", "KWD", "NOK", "SAR", "SEK", "USD"]

        self.row_widgets = []
        for row_idx, kalem in enumerate(self.ihtiyaclar, 1):
            birim_fiyat = kazanan_teklifler.get(kalem.id, 0.0)
            toplam_haric = birim_fiyat * kalem.miktar
            kdv_orani = kdv_oranlari.get(kalem.malzeme_adi, 20.0)
            toplam_kdvli = toplam_haric * (1 + kdv_orani / 100)

            ttk.Label(scrollable, text=kalem.malzeme_adi, width=45, anchor='w').grid(row=row_idx, column=0, padx=5, pady=2, sticky='w')
            
            mensei_combo = ttk.Combobox(scrollable, values=["Yerli", "Yabancı", "Bilinmiyor"], state="readonly", width=12)
            mensei_combo.set("Yerli")
            mensei_combo.grid(row=row_idx, column=1, padx=5, pady=2)
            
            ttk.Label(scrollable, text=str(kalem.miktar)).grid(row=row_idx, column=2, padx=5, pady=2)
            ttk.Label(scrollable, text=kalem.birim).grid(row=row_idx, column=3, padx=5, pady=2)
            ttk.Label(scrollable, text=kalem.okas_kodu or "-").grid(row=row_idx, column=4, padx=5, pady=2)
            
            # KDV'li fiyat etiketi her açılışta güncel hesaplanır
            ttk.Label(scrollable, text=f"{toplam_kdvli:,.2f}", font=("Arial", 10, "bold"), bootstyle="success").grid(row=row_idx, column=5, padx=5, pady=2)
            
            para_combo = ttk.Combobox(scrollable, values=para_birimleri, state="readonly", width=8)
            para_combo.set("TRY")
            para_combo.grid(row=row_idx, column=6, padx=5, pady=2)
            
            ttk.Label(scrollable, text=istekli_adi).grid(row=row_idx, column=7, padx=5, pady=2)

            self.row_widgets.append({
                'kalem': kalem,
                'toplam_fiyat': toplam_kdvli,
                'mensei_combo': mensei_combo,
                'para_combo': para_combo,
                'istekli': istekli_adi
            })

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        bottom_frame = ttk.Frame(self.main_container)
        bottom_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            bottom_frame, 
            text="📂 İndirdiğim EKAP Şablonunu Doldur", 
            command=self._sablon_doldur, 
            bootstyle="primary", 
            padding=(0, 10)
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            bottom_frame, 
            text="📊 EKAP Excel Dosyası Oluştur (Sıfırdan)", 
            command=self._excel_olustur, 
            bootstyle="success", 
            padding=(0, 10)
        ).pack(side=tk.RIGHT, padx=5)

    def _apply_global_mensei(self):
        val = self.global_mensei.get()
        if not val:
            messagebox.showwarning("Uyarı", "Lütfen uygulamak için bir menşei seçin!")
            return
        for row in self.row_widgets:
            row['mensei_combo'].set(val)
        messagebox.showinfo("Başarılı", f"Tüm kalemlerin menşei '{val}' olarak güncellendi.")

    def _verileri_topla(self):
        ekap_verileri = []
        for row in self.row_widgets:
            ekap_verileri.append({
                'is_kalemi': row['kalem'].malzeme_adi,
                'mensei': row['mensei_combo'].get() or "Bilinmiyor",
                'miktar': row['kalem'].miktar,
                'birim': row['kalem'].birim,
                'okas': row['kalem'].okas_kodu or "",
                'toplam_fiyat': row['toplam_fiyat'],
                'para_birimi': row['para_combo'].get() or "TRY",
                'istekli': row['istekli']
            })
        return ekap_verileri

    def _sablon_doldur(self):
        """Kullanıcının indirdiği orijinal .xls şablonunu seçip doldurur."""
        dosya = filedialog.askopenfilename(
            title="EKAP'tan İndirdiğiniz Şablonu Seçin (.xls)",
            filetypes=[("EKAP Şablonu", "*.xls"), ("Tüm Dosyalar", "*.*")]
        )
        if not dosya: return

        try:
            alim = self.db.alim_getir(self.alim_id)
            if not alim: return

            ekap_verileri = self._verileri_topla()
            rapor = RaporService(output_dir=alim_klasoru_getir(self.db, self.alim_id))
            
            cikti_dosyasi = rapor.ekap_orijinal_sablon_doldur(alim, ekap_verileri, dosya)

            if self.ana_pencere:
                self.ana_pencere.durum_guncelle("🟢 EKAP Şablonu başarıyla dolduruldu ✅")
                self.ana_pencere.ilerlemeyi_guncelle()

            messagebox.showinfo("Başarılı", f"✅ Orijinal EKAP şablonu dolduruldu:\n{cikti_dosyasi}")
            klasoru_ac(alim_klasoru_getir(self.db, self.alim_id))

        except Exception as e:
            messagebox.showerror("Hata", f"❌ Şablon doldurma hatası:\n{str(e)}")

    def _excel_olustur(self):
        """Sıfırdan XML şablonu oluşturur."""
        try:
            alim = self.db.alim_getir(self.alim_id)
            if not alim: return

            ekap_verileri = self._verileri_topla()
            rapor = RaporService(output_dir=alim_klasoru_getir(self.db, self.alim_id))
            dosya = rapor.ekap_excel_raporu(alim, ekap_verileri)

            if self.ana_pencere:
                self.ana_pencere.durum_guncelle("🟢 EKAP Excel dosyası oluşturuldu ✅")
                self.ana_pencere.ilerlemeyi_guncelle()

            messagebox.showinfo("Başarılı", f"✅ EKAP Excel dosyası oluşturuldu:\n{dosya}")
            klasoru_ac(alim_klasoru_getir(self.db, self.alim_id))

        except Exception as e:
            messagebox.showerror("Hata", f"❌ Excel oluşturma hatası: {str(e)}")

    def kaydet(self) -> bool:
        return True