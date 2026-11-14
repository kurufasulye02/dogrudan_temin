# gui/gerekce_formu.py
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from gui.dosya_yardimci import alim_klasoru_getir, klasoru_ac
from services.rapor_service import RaporService
from services.maliyet_service import MaliyetService
from utils.ui_helpers import fare_tekerlegi_bagla

class GerekceFormu:
    def __init__(self, parent, db, alim_id, ana_pencere):
        self.parent = parent
        self.db = db
        self.alim_id = alim_id
        self.ana_pencere = ana_pencere
        self.frame = None
        self.main_container = None
        self.check_vars = {}
        self.detay_text = None
        self.acil_text = None
        self.guncel_toplam_maliyet = 0.0

        self._olustur()
        self.frame.bind("<Map>", self._ekran_yenile)

    def _olustur(self):
        self.frame = ttk.LabelFrame(self.parent, text="📝 MAL VE HİZMET ALIMI GEREKÇE FORMU", padding=15)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.main_container = ttk.Frame(self.frame)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self._icerik_olustur()

    def _ekran_yenile(self, event):
        if event.widget == self.frame:
            for child in self.main_container.winfo_children():
                child.destroy()
            self._icerik_olustur()

    def _hesapla_guncel_maliyet(self):
        """Yaklaşık Maliyet sekmesindeki verileri kullanarak tam toplamı hesaplar."""
        teklifler = self.db.teklifleri_getir(self.alim_id)
        maliyetler = MaliyetService.yaklasik_maliyet_hesapla(teklifler)
        
        # Veritabanındaki KDV oranlarını çek
        self.db.cursor.execute("SELECT malzeme_adi, kdv_orani FROM yaklasik_maliyet WHERE alim_id=?", (self.alim_id,))
        kdv_oranlari = {row['malzeme_adi']: row['kdv_orani'] for row in self.db.cursor.fetchall()}
        
        toplam_kdvli = 0.0
        for malzeme, veri in maliyetler.items():
            toplam_haric = veri['toplam']
            kdv = kdv_oranlari.get(malzeme, 20.0)
            toplam_kdvli += toplam_haric * (1 + kdv / 100)
            
        return toplam_kdvli

    def _icerik_olustur(self):
        if not self.alim_id:
            ttk.Label(self.main_container, text="⚠️ Önce alım kaydını oluşturun!", bootstyle="danger").pack(pady=20)
            return

        alim = self.db.alim_getir(self.alim_id)
        kurum = self.db.kurum_getir()
        if not alim or not kurum:
            ttk.Label(self.main_container, text="⚠️ Kurum veya Alım bilgisi eksik!", bootstyle="danger").pack(pady=20)
            return

        mevcut = self.db.gerekce_getir(self.alim_id)
        self.guncel_toplam_maliyet = self._hesapla_guncel_maliyet()

        canvas = tk.Canvas(self.main_container, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        fare_tekerlegi_bagla(scrollable, canvas)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 1. BÖLÜM
        ttk.Label(scrollable, text="1. Alıma İlişkin Genel Bilgiler", font=("Arial", 11, "bold"), bootstyle="primary").pack(anchor='w', pady=(10, 5))
        
        isin_niteligi = alim.isin_niteligi
        if not isin_niteligi and alim.alim_adi and " - " in alim.alim_adi:
            isin_niteligi = alim.alim_adi.split(" - ", 1)[1].strip()
        if not isin_niteligi:
            isin_niteligi = "Belirtilmedi"

        f1 = ttk.Frame(scrollable)
        f1.pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(f1, text="Talep Edilen Mal/Hizmetin Adı:").pack(side=tk.LEFT)
        ttk.Label(f1, text=isin_niteligi, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)

        ihtiyaclar = self.db.ihtiyac_getir(self.alim_id)
        f2 = ttk.Frame(scrollable)
        f2.pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(f2, text="Miktarı / Adedi:").pack(side=tk.LEFT)
        ttk.Label(f2, text=f"{len(ihtiyaclar)} Kalem", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)

        f3 = ttk.Frame(scrollable)
        f3.pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(f3, text="Tahmini Yaklaşık Maliyeti:").pack(side=tk.LEFT)
        ttk.Label(f3, text=f"{self.guncel_toplam_maliyet:,.2f} TL", font=("Arial", 10, "bold"), bootstyle="success").pack(side=tk.LEFT, padx=5)

        # 2. BÖLÜM
        ttk.Separator(scrollable, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(scrollable, text="2. DMO'dan Temin Edilememe Gerekçesi", font=("Arial", 11, "bold"), bootstyle="primary").pack(anchor='w', pady=(5, 0))
        ttk.Label(scrollable, text="(Uygun olan seçenekleri işaretleyiniz)", font=("Arial", 9, "italic")).pack(anchor='w', pady=(0, 5))

        maddeler = [
            ('katalog_disinda', "Katalogda Bulunmaması: İhtiyaç duyulan mal/hizmetin teknik özellikleri veya doğrudan kendisi güncel DMO kataloglarında yer almamaktadır."),
            ('teknik_yetersiz', "Teknik Yetersizlik / Uyumsuzluk: DMO kataloglarında yer alan muadil ürünler, kurumumuzda mevcut olan sistem/donanım altyapısı ile teknik olarak uyum sağlamamaktadır."),
            ('fiyat_avantajsiz', "Fiyat Avantajsızlığı: Yapılan piyasa fiyat araştırması neticesinde, talep edilen ürünün piyasadan daha ekonomik şartlarda temin edilebileceği ve kamu yararı oluşacağı tespit edilmiştir."),
            ('teslimat_ivedi', "Teslimat ve İvedilik Süresi: DMO üzerinden yapılacak alımlarda öngörülen teslimat süresi, birimimizin yürütmekte olduğu acil/zorunlu faaliyetleri aksatacak niteliktedir.")
        ]

        for key, metin in maddeler:
            var = tk.BooleanVar(value=bool(mevcut.get(key, 0)))
            self.check_vars[key] = var
            ttk.Checkbutton(scrollable, text=metin, variable=var, bootstyle="round-toggle").pack(anchor='w', padx=10, pady=3)

        ttk.Label(scrollable, text="Detaylı Açıklama:", font=("Arial", 10, "bold")).pack(anchor='w', padx=10, pady=(10, 2))
        self.detay_text = tk.Text(scrollable, height=4, font=("Arial", 10), wrap="word")
        self.detay_text.pack(fill=tk.X, padx=10, pady=2)
        self.detay_text.insert("1.0", mevcut.get('detayli_aciklama', ''))

        # 3. BÖLÜM
        ttk.Separator(scrollable, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(scrollable, text="3. Acil ve Zorunlu Alım Gerekçesi (Tasarruf Tedbirleri Kapsamında)", font=("Arial", 11, "bold"), bootstyle="primary").pack(anchor='w', pady=(5, 0))
        ttk.Label(scrollable, text="(Bu alımın ertelenemez olduğuna ve birim faaliyetleri için neden zorunlu olduğuna dair kısa açıklama yazılmalıdır)", font=("Arial", 9, "italic")).pack(anchor='w', pady=(0, 5))
        
        self.acil_text = tk.Text(scrollable, height=4, font=("Arial", 10), wrap="word")
        self.acil_text.pack(fill=tk.X, padx=10, pady=2)
        self.acil_text.insert("1.0", mevcut.get('acil_gerekce', ''))

        # ALT BUTONLAR
        btn_frame = ttk.Frame(self.main_container)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="💾 KAYDET", command=self.kaydet, bootstyle="success").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📄 WORD RAPORU OLUŞTUR", command=self._rapor_olustur, bootstyle="primary").pack(side=tk.LEFT, padx=5)

    def kaydet(self) -> bool:
        if not self.alim_id: return False
        
        veriler = {
            'katalog_disinda': 1 if self.check_vars['katalog_disinda'].get() else 0,
            'teknik_yetersiz': 1 if self.check_vars['teknik_yetersiz'].get() else 0,
            'fiyat_avantajsiz': 1 if self.check_vars['fiyat_avantajsiz'].get() else 0,
            'teslimat_ivedi': 1 if self.check_vars['teslimat_ivedi'].get() else 0,
            'detayli_aciklama': self.detay_text.get("1.0", tk.END).strip(),
            'acil_gerekce': self.acil_text.get("1.0", tk.END).strip()
        }
        
        self.db.gerekce_kaydet(self.alim_id, veriler)
        if self.ana_pencere:
            self.ana_pencere.durum_guncelle("🟢 Gerekçe formu kaydedildi ✅")
        messagebox.showinfo("Başarılı", "✅ Gerekçe formu başarıyla kaydedildi.")
        return True

    def _rapor_olustur(self):
        if not self.kaydet(): return

        alim = self.db.alim_getir(self.alim_id)
        kurum = self.db.kurum_getir()
        ihtiyaclar = self.db.ihtiyac_getir(self.alim_id)
        veriler = self.db.gerekce_getir(self.alim_id)

        if not alim or not kurum:
            messagebox.showerror("Hata", "Alım veya Kurum bilgisi eksik.")
            return

        try:
            rapor = RaporService(output_dir=alim_klasoru_getir(self.db, self.alim_id))
            # Hesaplanan GÜNCEL toplam maliyeti fonksiyona gönderiyoruz
            dosya = rapor.gerekce_formu_raporu(alim, kurum, veriler, ihtiyaclar, self.guncel_toplam_maliyet)
            
            messagebox.showinfo("Başarılı", f"✅ Word raporu oluşturuldu:\n{dosya}")
            klasoru_ac(alim_klasoru_getir(self.db, self.alim_id))
            if self.ana_pencere:
                self.ana_pencere.ilerlemeyi_guncelle()
        except Exception as e:
            messagebox.showerror("Hata", f"Rapor oluşturulamadı:\n{e}")