# gui/alim_yonetimi.py
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import os
import re
import shutil
from pathlib import Path
from datetime import datetime
import json
from typing import Optional

from models.alim import Alim
from models.kurum import Kurum
from services.veritabani_service import VeritabaniService
from services.arsiv_katalog import ArsivKatalog
from services.butce_verisi import ISIN_TANIMLARI, BUTCE_KODLARI
from gui.istatistik_penceresi import IstatistikPenceresi


class AlimYonetimi:
    def __init__(self, parent, db, alim_id, ana_pencere):
        self.parent = parent
        self.db = db
        self.alim_id = alim_id
        self.ana_pencere = ana_pencere
        self.katalog = ArsivKatalog()
        self.frame = None
        self.tree = None
        self.secili_db_yolu = None
        self.secili_id = None
        
        self.yeni_alim_entryleri = {}
        self.alim_turu_var = tk.StringVar(value="mal")
        
        self._olustur()
        self._alimlari_yukle()
    
    def _olustur(self):
        self.frame = ttk.LabelFrame(self.parent, text="📂 ALIM YÖNETİMİ", padding=15)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_frame = ttk.Frame(self.frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(
            info_frame,
            text="💡 Yeni alım bilgilerini girip 'Yeni Alım Başlat' butonuna tıklayın veya mevcut bir alımı açın.",
            bootstyle="info",
            font=("Arial", 9, "italic")
        ).pack(anchor='w')
        
        form_frame = ttk.LabelFrame(self.frame, text="📝 Yeni Alım Bilgileri", padding=10)
        form_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 1. Satır: Alım Türü ve Bütçe Yılı
        row1 = ttk.Frame(form_frame)
        row1.grid(row=0, column=0, sticky='w', pady=5, padx=10)
        
        ttk.Label(row1, text="Alım Türü:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Radiobutton(row1, text="Mal Alımı", variable=self.alim_turu_var, value="mal", bootstyle="primary", command=self._alim_turu_degisti).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(row1, text="Hizmet Alımı", variable=self.alim_turu_var, value="hizmet", bootstyle="success", command=self._alim_turu_degisti).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(row1, text="Bakım / Onarım", variable=self.alim_turu_var, value="bakim", bootstyle="warning", command=self._alim_turu_degisti).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(row1, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        ttk.Label(row1, text="Bütçe Yılı:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        current_year = datetime.now().year
        years = [str(y) for y in range(current_year - 2, current_year + 3)]
        self.yil_combo = ttk.Combobox(row1, values=years, width=8, state="readonly")
        self.yil_combo.set(str(current_year))
        self.yil_combo.pack(side=tk.LEFT)
        
        # 2. Satır: İşin Tanımı ve İşin Niteliği
        row2 = ttk.Frame(form_frame)
        row2.grid(row=1, column=0, sticky='ew', pady=5, padx=10)
        
        ttk.Label(row2, text="İşin Tanımı:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.isin_tanimi_entry = ttk.Entry(row2, width=50, font=("Arial", 10), state="readonly")
        self.isin_tanimi_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(row2, text="İşin Niteliği (Ekonomik Adı):", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.isin_niteligi_combo = ttk.Combobox(row2, width=55, font=("Arial", 10))
        self.isin_niteligi_combo.pack(side=tk.LEFT)
        self.isin_niteligi_combo.bind("<<ComboboxSelected>>", self._nitelik_degisti)
        
        # 3. Satır: Bütçe Tertibi ve Ödenek Miktarı
        row3 = ttk.Frame(form_frame)
        row3.grid(row=2, column=0, sticky='ew', pady=5, padx=10)
        
        ttk.Label(row3, text="Bütçe Tertibi:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.butce_tertibi_combo = ttk.Combobox(row3, width=25, font=("Arial", 10))
        self.butce_tertibi_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(row3, text="Ödenek Miktarı (TL):", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.odeneck_entry = ttk.Entry(row3, width=20, font=("Arial", 10))
        self.odeneck_entry.pack(side=tk.LEFT)
        
        # 4. Satır: Butonlar
        row4 = ttk.Frame(form_frame)
        row4.grid(row=3, column=0, pady=15, padx=10)
        
        ttk.Button(row4, text="➕ YENİ ALIM BAŞLAT", command=self._yeni_alim_baslat, bootstyle="success", padding=(10, 5)).pack(side=tk.LEFT, padx=5)
        ttk.Button(row4, text="🔄 Formu Temizle", command=self._formu_temizle, bootstyle="secondary-outline", padding=(10, 5)).pack(side=tk.LEFT, padx=5)
        
        # Başlangıçta Mal Alımı seçili olduğu için verileri yükle
        self._alim_turu_degisti()
        
        # ===== MEVCUT ALIMLAR LİSTESİ =====
        list_frame = ttk.LabelFrame(self.frame, text="📋 Arşivlenmiş Alımlar", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        btn_frame2 = ttk.Frame(list_frame)
        btn_frame2.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(btn_frame2, text="📂 SEÇİLİ ALIMI AÇ", command=self._alim_ac, bootstyle="primary").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="📊 İSTATİSTİKLER", command=self._istatistik_goster, bootstyle="info").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="🗄️ ARŞİVDEN EKLE", command=self._arsivden_alim_ekle, bootstyle="secondary").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="🗑️ SİL", command=self._alim_sil, bootstyle="danger").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="↻ YENİLE", command=self._alimlari_yukle, bootstyle="secondary-outline").pack(side=tk.LEFT, padx=5)
        
        columns = ("id", "alim_adi", "yil", "tur", "odenek", "durum", "ilerleme", "tarih", "klasor", "db_yolu")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse", height=10)
        
        kolon_basliklari = {
            "id": ("#", 40), "alim_adi": ("Alım Adı", 200), "yil": ("Bütçe Yılı", 70),
            "tur": ("Tür", 80),
            "odenek": ("Ödenek (TL)", 100),
            "durum": ("Durum", 100), "ilerleme": ("İlerleme", 70), "tarih": ("Son Açılma", 130),
            "klasor": ("Klasör", 150), "db_yolu": ("DB Yolu", 0)
        }
        
        for col, (baslik, genislik) in kolon_basliklari.items():
            self.tree.heading(col, text=baslik)
            if col == "db_yolu":
                self.tree.column(col, width=0, stretch=False)
            else:
                self.tree.column(col, width=genislik, anchor="w" if col not in ["yil", "id", "tur", "odenek"] else "center")
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<<TreeviewSelect>>", self._secim_degisti)
        self.tree.bind("<Double-1>", lambda e: self._alim_ac())
        
        self.durum_label = ttk.Label(self.frame, text="", font=("Arial", 9), bootstyle="secondary")
        self.durum_label.pack(anchor='w', pady=(10, 0))

    def _alim_turu_degisti(self):
        tur = self.alim_turu_var.get()
        
        # İşin tanımını otomatik doldur
        self.isin_tanimi_entry.config(state="normal")
        self.isin_tanimi_entry.delete(0, tk.END)
        self.isin_tanimi_entry.insert(0, ISIN_TANIMLARI.get(tur, ""))
        self.isin_tanimi_entry.config(state="readonly")
        
        # İşin Niteliği combobox'ını güncelle
        nitelikler = [item[0] for item in BUTCE_KODLARI.get(tur, [])]
        nitelikler.append("Diğer (Elle Gir)")
        self.isin_niteligi_combo['values'] = nitelikler
        self.isin_niteligi_combo.set("") # Seçimi temizle
        
        # Bütçe tertibi temizle
        self.butce_tertibi_combo.set("")
        self.butce_tertibi_combo['values'] = []

    def _nitelik_degisti(self, event):
        secilen = self.isin_niteligi_combo.get()
        tur = self.alim_turu_var.get()
        
        if secilen == "Diğer (Elle Gir)":
            # Serbest girişe izin ver
            self.isin_niteligi_combo.config(state="normal")
            self.isin_niteligi_combo.delete(0, tk.END)
            self.isin_niteligi_combo.focus()
            self.butce_tertibi_combo.set("")
            self.butce_tertibi_combo['values'] = []
        else:
            # Seçime göre bütçe tertiplerini bul
            kodlar = []
            for ad, kod in BUTCE_KODLARI.get(tur, []):
                if ad == secilen:
                    kodlar.append(kod)
            
            if kodlar:
                self.butce_tertibi_combo['values'] = kodlar
                self.butce_tertibi_combo.set(kodlar[0]) # İlkini otomatik seç
            else:
                self.butce_tertibi_combo.set("")
                self.butce_tertibi_combo['values'] = []

    def _formu_temizle(self):
        self.alim_turu_var.set("mal")
        self._alim_turu_degisti()
        self.yil_combo.set(str(datetime.now().year))
        self.isin_niteligi_combo.set("")
        self.butce_tertibi_combo.set("")
        self.odeneck_entry.delete(0, tk.END)

    def _alimlari_yukle(self):
        if not hasattr(self, 'tree') or self.tree is None:
            return

        for item in self.tree.get_children():
            self.tree.delete(item)
        
        katalog_kayitlari = self.katalog.listele()
        
        if not katalog_kayitlari:
            self.tree.insert("", "end", values=("", "Henüz alım yok", "", "", "", "", "", "", "", ""))
            self.durum_label.config(text="📭 Hiç alım bulunamadı.")
            return
        
        for kayit in katalog_kayitlari:
            db_yolu = kayit.get('db_yolu', '')
            dosya_var = os.path.exists(db_yolu)
            
            durum = kayit.get('durum', 'hazirlik')
            durum_metni = {
                'hazirlik': '🟡 Hazırlık',
                'teklif_aliniyor': '🔵 Teklif Alınıyor',
                'degerlendirme': '🟠 Değerlendirme',
                'onaylandi': '🟢 Onaylandı',
                'tamamlandi': '✅ Tamamlandı'
            }.get(durum, durum)
            
            if not dosya_var:
                durum_metni = '⚠️ Dosya Yok'
            
            tamamlanan = kayit.get('tamamlanan_adim', 0)
            toplam = kayit.get('toplam_adim', 10)
            ilerleme = f"{tamamlanan}/{toplam}" if dosya_var else "-"
            
            son_acilma = kayit.get('son_acilma_tarihi', '')
            if son_acilma:
                try:
                    dt = datetime.fromisoformat(son_acilma.replace('Z', '+00:00'))
                    tarih = dt.strftime('%d.%m.%Y %H:%M')
                except:
                    tarih = son_acilma[:16]
            else:
                tarih = kayit.get('kayit_tarihi', '-')[:16] if kayit.get('kayit_tarihi') else '-'
            
            klasor = kayit.get('klasor_yolu', '-')
            if len(klasor) > 25:
                klasor = "..." + klasor[-22:]
            
            alim_turu_metin = "Bilinmiyor"
            odenek_degeri = 0.0
            try:
                if os.path.exists(db_yolu):
                    gecici_db = VeritabaniService(db_yolu)
                    a = gecici_db.son_alim_getir()
                    if a:
                        if hasattr(a, 'alim_turu') and a.alim_turu:
                            if a.alim_turu == "hizmet": alim_turu_metin = "Hizmet"
                            elif a.alim_turu == "bakim": alim_turu_metin = "Bakım"
                            else: alim_turu_metin = "Mal"
                        if hasattr(a, 'odeneck_miktari'):
                            odenek_degeri = a.odeneck_miktari or 0.0
                    gecici_db.kapat()
            except Exception as e:
                print(f"Katalog okuma hatası: {e}")

            self.tree.insert(
                "",
                "end",
                iid=str(kayit['id']),
                values=(
                    kayit['id'],
                    kayit.get('alim_adi', '-'),
                    kayit.get('yil', '-'),
                    alim_turu_metin,
                    f"{odenek_degeri:,.2f}",
                    durum_metni,
                    ilerleme,
                    tarih,
                    klasor,
                    db_yolu
                )
            )
        
        self.durum_label.config(text=f"📂 {len(katalog_kayitlari)} alım bulundu.")
    
    def _secim_degisti(self, event):
        secim = self.tree.selection()
        if secim:
            item = self.tree.item(secim[0])
            values = item['values']
            if values and len(values) > 9:
                self.secili_id = values[0]
                self.secili_db_yolu = values[9]
            else:
                self.secili_id = None
                self.secili_db_yolu = None
        else:
            self.secili_id = None
            self.secili_db_yolu = None

    def _istatistik_goster(self):
        IstatistikPenceresi(self.parent, self.katalog)

    def _alim_ac(self):
        if not self.secili_db_yolu:
            messagebox.showwarning("Uyarı", "Lütfen önce bir alım seçin!")
            return
        
        if not os.path.exists(self.secili_db_yolu):
            messagebox.showerror("Hata", f"Veritabanı dosyası bulunamadı:\n{self.secili_db_yolu}")
            return
        
        try:
            yeni_db = VeritabaniService(self.secili_db_yolu)
            alimlar = yeni_db.alimlari_getir()
            if not alimlar:
                messagebox.showerror("Hata", "Bu veritabanında alım kaydı bulunamadı!")
                yeni_db.kapat()
                return
            
            alim = alimlar[0]
            
            self.katalog.son_acilma_guncelle(self.secili_db_yolu)
            
            if hasattr(self.ana_pencere, 'db') and self.ana_pencere.db:
                try:
                    self.ana_pencere.db.kapat()
                except:
                    pass
            
            self.ana_pencere.db = yeni_db
            self.ana_pencere.alim_id = alim.id
            self.ana_pencere.alim_no_label.config(text=f"📄 Alım: {alim.alim_adi}")
            self.ana_pencere.durum_guncelle(f"🟢 Alım açıldı: {alim.alim_adi}")
            
            self._alimlari_yukle()
            
            messagebox.showinfo("Başarılı", f"✅ Alım başarıyla açıldı:\n{alim.alim_adi}")
            
            self.ana_pencere.adim_degistir(2)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Alım açılırken hata oluştu:\n{str(e)}")
    
    def _alim_sil(self):
        if not self.secili_db_yolu:
            messagebox.showwarning("Uyarı", "Lütfen önce silmek istediğiniz alımı seçin!")
            return
        
        kayit = self.katalog.getir(self.secili_db_yolu)
        if not kayit:
            messagebox.showerror("Hata", "Bu alım katalogda bulunamadı!")
            return
        
        alim_adi = kayit.get('alim_adi', 'Bilinmeyen Alım')
        klasor_yolu = kayit.get('klasor_yolu', '')
        if not klasor_yolu:
            klasor_yolu = str(Path(self.secili_db_yolu).parent)
        
        cevap = messagebox.askyesnocancel(
            "Alım Sil",
            f"'{alim_adi}' alımını silmek istediğinize emin misiniz?\n\n"
            f"📁 Klasör: {klasor_yolu}\n\n"
            "• EVET → Klasörüyle birlikte TAMAMEN sil (geri alınamaz!)\n"
            "• HAYIR → Sadece katalogdan kaldır (dosyalar korunur)\n"
            "• İPTAL → Vazgeç"
        )
        
        if cevap is None: return
        
        if cevap:
            if not messagebox.askyesno("⚠️ SON ONAY", f"Bu işlem GERİ ALINAMAZ!\n\nSilinecek klasör:\n{klasor_yolu}\n\nİçindeki TÜM dosyalar silinecek.\n\nDevam etmek istiyor musunuz?"):
                return
            
            self._aktif_alimi_kapat_gerekirse()
            
            try:
                klasor = Path(klasor_yolu)
                if klasor.exists():
                    shutil.rmtree(klasor)
                else:
                    print(f"⚠️ Klasör zaten yok: {klasor_yolu}")
            except Exception as e:
                messagebox.showerror("Klasör Silme Hatası", f"Klasör silinemedi:\n{klasor_yolu}\n\nHata: {e}\n\nKatalogdan kaldırma işlemi yine de yapılacak.")
        
        try:
            self.katalog.sil(self.secili_db_yolu)
            self.secili_id = None
            self.secili_db_yolu = None
            self._alimlari_yukle()
            
            if cevap:
                messagebox.showinfo("Silindi", f"✅ '{alim_adi}' tamamen silindi.")
            else:
                messagebox.showinfo("Katalogdan Kaldırıldı", f"✅ '{alim_adi}' katalogdan kaldırıldı.\n\n📁 Dosyalar korundu:\n{klasor_yolu}")
        except Exception as e:
            messagebox.showerror("Hata", f"Katalogdan silme hatası:\n{e}")
    
    def _aktif_alimi_kapat_gerekirse(self):
        try:
            aktif_db_yolu = getattr(self.ana_pencere.db, 'db_path', None) if hasattr(self.ana_pencere, 'db') else None
            if not aktif_db_yolu: return
            if Path(aktif_db_yolu).resolve() == Path(self.secili_db_yolu).resolve():
                self.ana_pencere.db.kapat()
                self.ana_pencere.alim_id = None
                self.ana_pencere.alim_no_label.config(text="📄 Alım: -")
                self.ana_pencere.durum_guncelle("🟡 Alım kapatıldı (silindi)")
                self.ana_pencere.adim_degistir(0)
        except Exception as e:
            print(f"Aktif alım kapatma hatası: {e}")
    
    def _yeni_alim_baslat(self):
        try:
            try:
                yil = int(self.yil_combo.get())
            except ValueError:
                messagebox.showwarning("Uyarı", "Yıl seçimi geçersiz!")
                return
            
            isin_tanimi = self.isin_tanimi_entry.get().strip()
            isin_niteligi = self.isin_niteligi_combo.get().strip()
            butce_tertibi = self.butce_tertibi_combo.get().strip()
            
            try:
                odeneck_miktari = float(self.odeneck_entry.get().strip().replace(',', '.') or 0)
            except ValueError:
                messagebox.showwarning("Uyarı", "Ödenek miktarı sayısal olmalıdır!")
                return
                
            alim_turu = self.alim_turu_var.get()
            
            if not isin_niteligi or isin_niteligi == "Diğer (Elle Gir)":
                if isin_niteligi == "Diğer (Elle Gir)" and not self.isin_niteligi_combo.get().strip():
                    messagebox.showwarning("Uyarı", "Lütfen işin niteliğini giriniz!")
                    return
                elif not isin_niteligi:
                    messagebox.showwarning("Uyarı", "Lütfen işin niteliğini seçiniz!")
                    return
            
            kurum = self.db.kurum_getir()
            if not kurum:
                messagebox.showwarning("Uyarı", "Önce Kurum Bilgileri ekranından kurum bilgilerini kaydedin!")
                self.ana_pencere.adim_degistir(0)
                return
            
            secilen_yer = filedialog.askdirectory(title="Yeni alım arşivlerinin tutulacağı ana klasörü seçin")
            if not secilen_yer: return
            
            alim_adi = f"{yil} - {isin_niteligi}"
            
            temiz_ad = re.sub(r'[^\w\s-]', '', alim_adi, flags=re.UNICODE).strip().replace(' ', '_')
            klasor = Path(secilen_yer) / temiz_ad
            
            sayac = 1
            while klasor.exists():
                sayac += 1
                klasor = Path(secilen_yer) / f"{temiz_ad}_{sayac}"
            
            try:
                klasor.mkdir(parents=True, exist_ok=False)
            except Exception as e:
                messagebox.showerror("Hata", f"Klasör oluşturulamadı:\n{e}")
                return
            
            db_path = klasor / "alim.db"
            try:
                yeni_db = VeritabaniService(str(db_path))
                
                kurum_snapshot = json.dumps(kurum.dict(), ensure_ascii=False, default=str)
                
                alim = Alim(
                    alim_adi=alim_adi,
                    yil=yil,
                    isin_tanimi=isin_tanimi,
                    isin_niteligi=isin_niteligi,
                    butce_tertibi=butce_tertibi,
                    odeneck_miktari=odeneck_miktari,
                    alim_turu=alim_turu,
                    durum='hazirlik',
                    kurum_id=None,
                    dosya_klasoru=str(klasor),
                    kurum_snapshot=kurum_snapshot
                )
                
                alim_id = yeni_db.alim_olustur(alim)
                alim.id = alim_id
                
                snapshot_dict = json.loads(kurum_snapshot)
                snapshot_kurum = Kurum(**snapshot_dict)
                kurum_id = yeni_db.kurum_kaydet(snapshot_kurum)
                
                alim.kurum_id = kurum_id
                yeni_db.alim_guncelle(alim)
                
                self.katalog.kaydet(
                    alim_adi=alim_adi,
                    yil=yil,
                    db_yolu=str(db_path),
                    klasor_yolu=str(klasor),
                    durum='hazirlik',
                    tamamlanan_adim=1
                )
                
                if hasattr(self.ana_pencere, 'db') and self.ana_pencere.db:
                    try:
                        self.ana_pencere.db.kapat()
                    except:
                        pass
                
                self.ana_pencere.db = yeni_db
                self.ana_pencere.alim_id = alim_id
                self.ana_pencere.alim_no_label.config(text=f"📄 Alım: {alim_adi}")
                self.ana_pencere.durum_guncelle("🟢 Yeni alım başlatıldı")
                
                self._alimlari_yukle()
                self._formu_temizle()
                
                messagebox.showinfo("Başarılı", f"✅ Yeni alım başlatıldı.\n\n📁 {klasor}\n📄 {alim_adi}")
                
                self.ana_pencere.adim_degistir(2)
                
            except Exception as e:
                try:
                    yeni_db.kapat()
                except:
                    pass
                messagebox.showerror("Hata", f"Alım oluşturulamadı:\n{str(e)}")
                
        except Exception as e:
            messagebox.showerror("Hata", str(e))
    
    def _arsivden_alim_ekle(self):
        db_path = filedialog.askopenfilename(
            title="Arşivlenmiş alım veritabanını seçin",
            filetypes=[("Alım Veritabanı", "*.db"), ("SQLite", "*.sqlite;*.sqlite3"), ("Tüm Dosyalar", "*.*")]
        )
        if not db_path: return
        
        try:
            mevcut = self.katalog.getir(db_path)
            if mevcut:
                messagebox.showinfo("Bilgi", "Bu alım zaten katalogda mevcut.")
                self._alimlari_yukle()
                return
            
            if not self.katalog.db_gecerli_mi(db_path):
                messagebox.showerror("Hata", "Seçilen dosya geçerli bir alım veritabanı değil!")
                return
            
            gecici_db = VeritabaniService(db_path)
            alimlar = gecici_db.alimlari_getir()
            if not alimlar:
                messagebox.showerror("Hata", "Bu veritabanında alım kaydı bulunamadı!")
                gecici_db.kapat()
                return
            
            alim = alimlar[0]
            durumlar = gecici_db.ilerleme_durumlari(alim.id)
            tamamlanan = sum(durumlar)
            
            self.katalog.kaydet(
                alim_adi=alim.alim_adi,
                yil=alim.yil,
                db_yolu=db_path,
                klasor_yolu=alim.dosya_klasoru or str(Path(db_path).parent),
                durum=alim.durum,
                tamamlanan_adim=tamamlanan
            )
            
            gecici_db.kapat()
            
            messagebox.showinfo("Başarılı", "✅ Alım arşiv kataloğuna eklendi.")
            self._alimlari_yukle()
            
        except Exception as e:
            messagebox.showerror("Hata", f"Arşiv eklenemedi:\n{str(e)}")
    
    def kaydet(self) -> bool:
        return True
    
    def __del__(self):
        try:
            if hasattr(self, 'katalog') and self.katalog:
                self.katalog.kapat()
        except:
            pass