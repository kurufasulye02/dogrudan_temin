# gui/belge_kontrol.py
import os
import glob
import shutil
import zipfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from gui.dosya_yardimci import alim_klasoru_getir, klasoru_ac, dosyayi_ac
from gui.on_mali_kontrol import OnMaliKontrolPenceresi
from services.on_mali_kontrol_maddeleri import CEVAPLANABILIR_MADDE_SAYISI

# Rapor Tanımları GÜNCELLENDİ
RAPOR_TANIMLARI = [
    {'baslik': 'İhtiyaç Listesi Raporu', 'prefixler': ['Ihtiyac_Listesi']},
    {'baslik': 'Yaklaşık Fiyat Araştırması Mektubu', 'prefixler': ['Yaklasik_Fiyat_Arastirma_Word']},
    {'baslik': 'Gerekçe Formu', 'prefixler': ['Mal_ve_Hizmet_Alimi_Gerekce']},
    {'baslik': 'Yaklaşık Maliyet Hesap Cetveli', 'prefixler': ['Yaklasik_Maliyet_Cetveli']},
    {'baslik': 'Teklif Mektubu', 'prefixler': ['Teklif_Mektubu_']},
    {'baslik': 'Piyasa Fiyat Araştırma Tutanağı', 'prefixler': ['Piyasa_Fiyat_Arastirma_Tutanagi']},
    {'baslik': 'Doğrudan Temin Karar Tutanağı', 'prefixler': ['Karar_Tutanagi']},
    {'baslik': 'Muayene ve Kabul Tutanağı', 'prefixler': ['Muayene_Kabul_Tutanagi', 'Hizmet_Isleri_Kabul_Tutanagi']},
    {'baslik': 'EKAP Yükleme Dosyası', 'prefixler': ['EKAP_Yukleme_Dosyasi', 'EKAP_Doldurulmus_Sablon']},
]

YUKLEME_TANIMLARI = [
    {'baslik': 'Doğrudan Temin Kayıt Belgesi', 'dosya_adi': 'Dogrudan_Temin_Kayit_Belgesi'},
    {'baslik': 'Harcama Talimatı', 'dosya_adi': 'Harcama_Talimati'},
    {'baslik': 'VİF', 'dosya_adi': 'VIF_Belgesi'},
    {'baslik': 'Ödeme Emri Belgesi', 'dosya_adi': 'Odeme_Emri_Belgesi'},
]


class BelgeOlustur:
    def __init__(self, parent, db, alim_id, ana_pencere):
        self.parent = parent
        self.db = db
        self.alim_id = alim_id
        self.ana_pencere = ana_pencere
        self.frame = None
        self.rapor_durum_etiketleri = {}
        self.yukleme_durum_etiketleri = {}
        
        self.vadesi_gecmis_borc_var = tk.StringVar(value="hayir")
        self.fatura_turu_var = tk.StringVar(value="e_fatura")
        self.e_fatura_iliskilendirildi_var = tk.StringVar(value="hayir")
        self.belgesiz_odeme_var = tk.BooleanVar(value=False)

        self._olustur()

    def _klasor(self) -> str:
        return alim_klasoru_getir(self.db, self.alim_id)

    def _olustur(self):
        self.frame = ttk.LabelFrame(self.parent, text="🗂️ BELGE KONTROL", padding=15)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        if not self.alim_id:
            ttk.Label(self.frame, text="⚠️ Önce alım kaydını oluşturun!", bootstyle="danger").pack(pady=20)
            self._bos_ekran_butonlari()
            return

        klasor = self._klasor()
        ust_bilgi = ttk.Frame(self.frame)
        ust_bilgi.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(ust_bilgi, text=f"📁 Belge klasörü: {klasor}", font=("Arial", 9), bootstyle="secondary").pack(side=tk.LEFT)
        ttk.Button(ust_bilgi, text="🔄 Durumu Yenile", command=self._durumlari_guncelle, bootstyle="secondary-outline").pack(side=tk.RIGHT, padx=5)
        ttk.Button(self.frame, text="📂 Klasörü Aç", command=lambda: klasoru_ac(self._klasor()), bootstyle="info-outline").pack(anchor='w', pady=(0, 10))

        ust_bolme = ttk.Frame(self.frame)
        ust_bolme.pack(fill=tk.BOTH, expand=True, pady=5)
        ust_bolme.columnconfigure(0, weight=1)
        ust_bolme.columnconfigure(1, weight=1)
        ust_bolme.rowconfigure(0, weight=1)

        rapor_frame = ttk.LabelFrame(ust_bolme, text="📑 Raporlar", padding=10)
        rapor_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5))

        yukleme_frame = ttk.LabelFrame(ust_bolme, text="📤 Belge Yükleme ve Kontroller", padding=10)
        yukleme_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0))

        for i, tanim in enumerate(RAPOR_TANIMLARI):
            satir = ttk.Frame(rapor_frame)
            satir.pack(fill=tk.X, pady=3)
            ttk.Label(satir, text=tanim['baslik'], width=30, anchor='w', font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
            durum_lbl = ttk.Label(satir, text="", width=14, font=("Arial", 10, "bold"))
            durum_lbl.pack(side=tk.LEFT, padx=5)
            self.rapor_durum_etiketleri[i] = durum_lbl
            ttk.Button(satir, text="👁️ Göster", command=lambda t=tanim: self._raporu_goster(t), bootstyle="primary-outline").pack(side=tk.LEFT, padx=5)

        for i, tanim in enumerate(YUKLEME_TANIMLARI):
            satir = ttk.Frame(yukleme_frame)
            satir.pack(fill=tk.X, pady=3)
            ttk.Label(satir, text=tanim['baslik'], width=26, anchor='w', font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
            durum_lbl = ttk.Label(satir, text="", width=12, font=("Arial", 10, "bold"))
            durum_lbl.pack(side=tk.LEFT, padx=5)
            self.yukleme_durum_etiketleri[i] = durum_lbl
            ttk.Button(satir, text="📤 Yükle", command=lambda t=tanim: self._dosya_yukle(t), bootstyle="info-outline").pack(side=tk.LEFT, padx=3)
            ttk.Button(satir, text="👁️ Göster", command=lambda t=tanim: self._yuklenen_dosyayi_goster(t), bootstyle="primary-outline").pack(side=tk.LEFT, padx=3)

        ttk.Separator(yukleme_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        borc_frame = ttk.Frame(yukleme_frame)
        borc_frame.pack(fill=tk.X, pady=3)
        
        ttk.Label(
            borc_frame, 
            text="Vadesi Geçmiş Borç Durumu Sorgulandı mı?", 
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(borc_frame, text="Evet", variable=self.vadesi_gecmis_borc_var, value="evet", command=self._kaydet_secimler, bootstyle="success").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(borc_frame, text="Hayır", variable=self.vadesi_gecmis_borc_var, value="hayir", command=self._kaydet_secimler, bootstyle="danger").pack(side=tk.LEFT, padx=5)

        ttk.Separator(yukleme_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        fatura_frame = ttk.LabelFrame(yukleme_frame, text="📄 Fatura İşlemleri", padding=5)
        fatura_frame.pack(fill=tk.X, pady=3)
        
        tur_frame = ttk.Frame(fatura_frame)
        tur_frame.pack(fill=tk.X, pady=2)
        ttk.Label(tur_frame, text="Fatura Türü:", width=12, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(tur_frame, text="E-Fatura", variable=self.fatura_turu_var, value="e_fatura", command=self._fatura_turu_degisti).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(tur_frame, text="E-Arşiv Fatura", variable=self.fatura_turu_var, value="e_arsiv", command=self._fatura_turu_degisti).pack(side=tk.LEFT, padx=5)
        
        self.efatura_frame = ttk.Frame(fatura_frame)
        self.efatura_frame.pack(fill=tk.X, pady=2)
        ttk.Label(self.efatura_frame, text="Sistemde İlişkilendirildi mi?", width=26, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.efatura_frame, text="Evet", variable=self.e_fatura_iliskilendirildi_var, value="evet", command=self._kaydet_secimler, bootstyle="success").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.efatura_frame, text="Hayır", variable=self.e_fatura_iliskilendirildi_var, value="hayir", command=self._kaydet_secimler, bootstyle="danger").pack(side=tk.LEFT, padx=5)

        self.earsiv_frame = ttk.Frame(fatura_frame)
        self.earsiv_frame.pack(fill=tk.X, pady=2)
        ttk.Label(self.earsiv_frame, text="E-Arşiv Fatura Yükle:", width=26, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.earsiv_durum_lbl = ttk.Label(self.earsiv_frame, text="", width=12, font=("Arial", 10, "bold"))
        self.earsiv_durum_lbl.pack(side=tk.LEFT, padx=5)
        ttk.Button(self.earsiv_frame, text="📤 Yükle", command=lambda: self._dosya_yukle({'baslik': 'E-Arşiv Fatura', 'dosya_adi': 'E_Arsiv_Fatura'}), bootstyle="info-outline").pack(side=tk.LEFT, padx=3)
        ttk.Button(self.earsiv_frame, text="👁️ Göster", command=lambda: self._yuklenen_dosyayi_goster({'baslik': 'E-Arşiv Fatura', 'dosya_adi': 'E_Arsiv_Fatura'}), bootstyle="primary-outline").pack(side=tk.LEFT, padx=3)

        ttk.Separator(self.frame, orient='horizontal').pack(fill=tk.X, pady=(8, 5))
        odeme_frame = ttk.LabelFrame(self.frame, text="💳 Ödeme ve Dosya Kapanışı", padding=10)
        odeme_frame.pack(fill=tk.X, pady=(0, 5))

        on_mali_satir = ttk.Frame(odeme_frame)
        on_mali_satir.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(on_mali_satir, text="Ön Mali Kontrol Listesi (EK-32):", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.on_mali_durum_lbl = ttk.Label(on_mali_satir, text="", font=("Arial", 10, "bold"))
        self.on_mali_durum_lbl.pack(side=tk.LEFT, padx=5)
        ttk.Button(on_mali_satir, text="📋 Doldur / Görüntüle", command=self._on_mali_kontrol_ac, bootstyle="primary-outline").pack(side=tk.LEFT, padx=5)

        self.belgesiz_odeme_cb = ttk.Checkbutton(
            odeme_frame, 
            text="⚠️ Ödemeyi belge yüklemeden tamamlamak istiyorum (Sorumluluk kullanıcıya aittir)", 
            variable=self.belgesiz_odeme_var,
            bootstyle="round-toggle"
        )
        self.belgesiz_odeme_cb.pack(anchor='w', padx=5, pady=5)

        odeme_alt_frame = ttk.Frame(odeme_frame)
        odeme_alt_frame.pack(fill=tk.X, pady=5)
        
        self.odeme_durum_lbl = ttk.Label(odeme_alt_frame, text="", font=("Arial", 10, "bold"))
        self.odeme_durum_lbl.pack(side=tk.LEFT, padx=5)
        
        self.zip_btn = ttk.Button(odeme_alt_frame, text="📦 DOSYAYI YEDEKLE (ZIP)", command=self._alim_yedekle, bootstyle="info")
        self.zip_btn.pack(side=tk.RIGHT, padx=5)

        self.odeme_btn = ttk.Button(odeme_alt_frame, text="💳 ÖDEME TAMAMLANDI", command=self._odeme_tamamla, bootstyle="success")
        self.odeme_btn.pack(side=tk.RIGHT, padx=5)

        self._verileri_yukle()
        self._durumlari_guncelle()

    def _alim_yedekle(self):
        if not self.alim_id:
            messagebox.showwarning("Uyarı", "Önce bir alım açın!")
            return
            
        klasor_yolu = self._klasor()
        if not klasor_yolu or not os.path.exists(klasor_yolu):
            messagebox.showerror("Hata", "Alım klasörü bulunamadı!")
            return

        alim = self.db.alim_getir(self.alim_id)
        alim_adi = alim.alim_adi if alim else "Alim"

        hedef_zip = filedialog.asksaveasfilename(
            defaultextension=".zip",
            initialfile=f"Yedek_{alim_adi.replace(' ', '_')}.zip",
            filetypes=[("ZIP Dosyası", "*.zip")]
        )
        
        if not hedef_zip: return

        hedef_zip_abs = os.path.abspath(hedef_zip)
        klasor_yolu_abs = os.path.abspath(klasor_yolu)

        progress_win = tk.Toplevel(self.parent)
        progress_win.title("Yedekleniyor...")
        progress_win.geometry("400x150")
        progress_win.transient(self.parent)
        progress_win.grab_set()
        
        self.parent.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 200
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 75
        progress_win.geometry(f"+{x}+{y}")

        lbl_durum = ttk.Label(progress_win, text="Lütfen bekleyin, dosyalar sıkıştırılıyor...", font=("Arial", 10, "bold"))
        lbl_durum.pack(pady=15)
        
        pb = ttk.Progressbar(progress_win, mode='indeterminate', bootstyle="info-striped")
        pb.pack(fill=tk.X, padx=20, pady=10)
        pb.start(15)

        def zip_islemi():
            basarili = True
            hata_mesaji = ""
            try:
                with zipfile.ZipFile(hedef_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(klasor_yolu):
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        for file in files:
                            file_path = os.path.abspath(os.path.join(root, file))
                            
                            if file_path == hedef_zip_abs:
                                continue
                            
                            if file.endswith('-shm') or file.endswith('-wal'):
                                continue

                            if file.startswith('~') or file.startswith('.'):
                                continue
                                
                            if len(file_path) > 250:
                                continue
                                
                            arcname = os.path.relpath(file_path, klasor_yolu)
                            
                            self.parent.after(0, lambda f=file: lbl_durum.config(text=f"Sıkıştırılıyor: {f[:30]}..."))
                            
                            try:
                                zipf.write(file_path, arcname)
                            except PermissionError:
                                print(f"Kilitli dosya atlandı: {file_path}")
                                
            except Exception as e:
                basarili = False
                hata_mesaji = str(e)
                
            def islem_bitti():
                pb.stop()
                progress_win.destroy()
                if basarili:
                    messagebox.showinfo("Başarılı", f"Yedek başarıyla oluşturuldu:\n{hedef_zip}")
                else:
                    messagebox.showerror("Hata", f"Yedekleme sırasında hata oluştu:\n{hata_mesaji}")
            
            self.parent.after(0, islem_bitti)

        threading.Thread(target=zip_islemi, daemon=True).start()

    def _verileri_yukle(self):
        alim = self.db.alim_getir(self.alim_id)
        if alim:
            self.vadesi_gecmis_borc_var.set("evet" if getattr(alim, 'vadesi_gecmis_borc_sorgulandi', 0) else "hayir")
            ft = getattr(alim, 'fatura_turu', 'e_fatura')
            if not ft: ft = 'e_fatura'
            self.fatura_turu_var.set(ft)
            self.e_fatura_iliskilendirildi_var.set("evet" if getattr(alim, 'e_fatura_iliskilendirildi', 0) else "hayir")
            self._fatura_turu_degisti(save=False)

    def _kaydet_secimler(self):
        try:
            alim = self.db.alim_getir(self.alim_id)
            if not alim: return
            
            alim.vadesi_gecmis_borc_sorgulandi = 1 if self.vadesi_gecmis_borc_var.get() == "evet" else 0
            alim.fatura_turu = self.fatura_turu_var.get()
            alim.e_fatura_iliskilendirildi = 1 if self.e_fatura_iliskilendirildi_var.get() == "evet" else 0
            
            self.db.alim_guncelle(alim)
            self._durumlari_guncelle()
        except Exception as e:
            print(f"Seçim kaydetme hatası: {e}")

    def _fatura_turu_degisti(self, save=True):
        tur = self.fatura_turu_var.get()
        if tur == "e_fatura":
            self.earsiv_frame.pack_forget()
            self.efatura_frame.pack(fill=tk.X, pady=2, after=self.efatura_frame.master.winfo_children()[0])
        else:
            self.efatura_frame.pack_forget()
            self.earsiv_frame.pack(fill=tk.X, pady=2, after=self.earsiv_frame.master.winfo_children()[0])
            
        if save:
            self._kaydet_secimler()

    def _bos_ekran_butonlari(self):
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(pady=20)
        ttk.Label(btn_frame, text="Bu ekranı kullanabilmek için önce bir alım açmalısınız.", font=("Arial", 10)).pack(pady=5)
        ttk.Button(btn_frame, text="📂 Alım Yönetimine Git", command=lambda: self.ana_pencere.adim_degistir(1) if self.ana_pencere else None, bootstyle="primary").pack(pady=5)

    def _on_mali_kontrol_ac(self):
        if not self.alim_id:
            messagebox.showwarning("Uyarı", "Önce bir alım açın!")
            return
        OnMaliKontrolPenceresi(self.parent, self.db, self.alim_id, kaydet_sonrasi_callback=self._durumlari_guncelle)

    def _odeme_tamamla(self):
        try:
            alim = self.db.alim_getir(self.alim_id)
            if not alim:
                messagebox.showwarning("Uyarı", "Alım bilgisi bulunamadı!")
                return
            if alim.odeme_tamamlandi:
                if messagebox.askyesno("Ödeme Durumu", "Ödeme tamamlandı olarak işaretlenmiş. Bu işareti geri almak istiyor musunuz?"):
                    self.db.odeme_tamamla(self.alim_id, False)
                    self._durumlari_guncelle()
                    self.ana_pencere.ilerlemeyi_guncelle()
                return

            if not self.belgesiz_odeme_var.get():
                eksikler = []
                for tanim in YUKLEME_TANIMLARI:
                    if not self._yukleme_dosyasini_bul(tanim):
                        eksikler.append(tanim['baslik'])
                
                if self.vadesi_gecmis_borc_var.get() != "evet":
                    eksikler.append("Vadesi Geçmiş Borç Durumu Sorgulaması (Evet seçilmeli)")

                fatura_turu = self.fatura_turu_var.get()
                if fatura_turu == "e_fatura":
                    if self.e_fatura_iliskilendirildi_var.get() != "evet":
                        eksikler.append("E-Fatura İlişkilendirmesi (Evet seçilmeli)")
                elif fatura_turu == "e_arsiv":
                    if not self._yukleme_dosyasini_bul({'dosya_adi': 'E_Arsiv_Fatura'}):
                        eksikler.append("E-Arşiv Fatura Yüklemesi")
                
                if eksikler:
                    messagebox.showwarning(
                        "Eksik Belgeler",
                        "Ödeme tamamlanmadan önce aşağıdaki işlemler yapılmalıdır:\n\n- " + "\n- ".join(eksikler) + 
                        "\n\n(Belgeleri yüklemeden geçmek için lütfen yukarıdaki onay kutusunu işaretleyin.)"
                    )
                    return

            if not self.db.on_mali_kontrol_tamamlandi_mi(self.alim_id):
                cevap_sayisi = len(self.db.on_mali_kontrol_getir(self.alim_id))
                messagebox.showwarning("Ön Mali Kontrol Listesi Eksik", f"Ödeme tamamlanmadan önce Ön Mali Kontrol Listesi'ndeki (EK-32) tüm maddeler işaretlenmelidir.\n\nŞu an: {cevap_sayisi}/{CEVAPLANABILIR_MADDE_SAYISI} madde işaretli.")
                return

            if not all(self.db.ilerleme_durumlari(self.alim_id)[:9]):
                messagebox.showwarning("İşlem Sırası", "İlk 9 aşama (EKAP dahil) tamamlanmadan ödeme tamamlandı olarak işaretlenemez.")
                return

            if not messagebox.askyesno("Ödemeyi Tamamla", "Ödeme işleminin tamamlandığını onaylıyor musunuz?\n\nBu işlem alımı 10/10 tamamlandı olarak işaretler."):
                return

            self.db.odeme_tamamla(self.alim_id, True)
            self._durumlari_guncelle()
            self.ana_pencere.ilerlemeyi_guncelle()
            self.ana_pencere.durum_guncelle("🟢 Ödeme tamamlandı — alım dosyası kapatıldı ✅")
            messagebox.showinfo("Alım Tamamlandı", "✅ Ödeme tamamlandı. Alım dosyası 10/10 olarak kapatıldı.")
        except Exception as e:
            messagebox.showerror("Hata", f"Ödeme durumu güncellenemedi:\n{e}")

    def _rapor_dosyalarini_bul(self, tanim) -> list:
        klasor = self._klasor()
        bulunanlar = []
        for prefix in tanim['prefixler']:
            # Bütün uzantıları ve varyasyonları yakalamak için * kullanıyoruz
            bulunanlar.extend(glob.glob(os.path.join(klasor, f"{prefix}*")))
        return sorted(list(set(bulunanlar))) # Varsa çift kayıtları temizler

    def _yukleme_dosyasini_bul(self, tanim):
        klasor = self._klasor()
        eslesenler = glob.glob(os.path.join(klasor, f"{tanim['dosya_adi']}.*"))
        return eslesenler[0] if eslesenler else None

    def _durumlari_guncelle(self):
        if not self.alim_id:
            return
            
        for i, tanim in enumerate(RAPOR_TANIMLARI):
            dosyalar = self._rapor_dosyalarini_bul(tanim)
            lbl = self.rapor_durum_etiketleri[i]
            if dosyalar:
                metin = "✅ Oluşturuldu" if len(dosyalar) == 1 else f"✅ Oluşturuldu ({len(dosyalar)})"
                lbl.config(text=metin, bootstyle="success")
            else:
                lbl.config(text="❌ Oluşturulma", bootstyle="danger")

        for i, tanim in enumerate(YUKLEME_TANIMLARI):
            dosya = self._yukleme_dosyasini_bul(tanim)
            lbl = self.yukleme_durum_etiketleri[i]
            if dosya:
                lbl.config(text="✅ Yüklendi", bootstyle="success")
            else:
                lbl.config(text="❌ Yüklenmedi", bootstyle="danger")

        earsiv_dosya = self._yukleme_dosyasini_bul({'dosya_adi': 'E_Arsiv_Fatura'})
        if earsiv_dosya:
            self.earsiv_durum_lbl.config(text="✅ Yüklendi", bootstyle="success")
        else:
            self.earsiv_durum_lbl.config(text="❌ Yüklenmedi", bootstyle="danger")

        alim = self.db.alim_getir(self.alim_id) if self.alim_id else None
        if self.alim_id:
            cevap_sayisi = len(self.db.on_mali_kontrol_getir(self.alim_id))
            if cevap_sayisi >= CEVAPLANABILIR_MADDE_SAYISI:
                self.on_mali_durum_lbl.config(text=f"✅ Tamamlandı ({cevap_sayisi}/{CEVAPLANABILIR_MADDE_SAYISI})", bootstyle="success")
            else:
                self.on_mali_durum_lbl.config(text=f"❌ {cevap_sayisi}/{CEVAPLANABILIR_MADDE_SAYISI}", bootstyle="danger")

        if getattr(alim, 'odeme_tamamlandi', 0):
            self.odeme_durum_lbl.config(text="✅ Ödeme Tamamlandı", bootstyle="success")
            self.odeme_btn.config(text="↩ Ödeme Durumunu Geri Al", bootstyle="warning")
            self.belgesiz_odeme_cb.config(state='disabled')
            self.zip_btn.config(state='normal')
        else:
            self.odeme_durum_lbl.config(text="⏳ Ödeme Bekleniyor", bootstyle="warning")
            self.odeme_btn.config(text="💳 ÖDEME TAMAMLANDI", bootstyle="success")
            self.belgesiz_odeme_cb.config(state='normal')

    def _raporu_goster(self, tanim):
        dosyalar = self._rapor_dosyalarini_bul(tanim)
        if not dosyalar:
            messagebox.showwarning("Uyarı", f"'{tanim['baslik']}' henüz oluşturulmamış!")
            return
        if len(dosyalar) == 1:
            dosyayi_ac(dosyalar[0])
            return
        self._coklu_dosya_secim_penceresi(tanim['baslik'], dosyalar)

    def _yuklenen_dosyayi_goster(self, tanim):
        dosya = self._yukleme_dosyasini_bul(tanim)
        if not dosya:
            messagebox.showwarning("Uyarı", f"'{tanim['baslik']}' henüz yüklenmemiş!")
            return
        dosyayi_ac(dosya)

    def _coklu_dosya_secim_penceresi(self, baslik, dosyalar):
        pencere = tk.Toplevel(self.parent)
        pencere.title(f"{baslik} - Dosya Seç")
        pencere.geometry("450x300")
        pencere.transient(self.parent)
        pencere.grab_set()
        
        ttk.Label(pencere, text=f"Birden fazla '{baslik}' dosyası bulundu, açmak istediğinizi seçin:", wraplength=420, font=("Arial", 10)).pack(pady=10, padx=10)
        for dosya in dosyalar:
            ttk.Button(pencere, text=os.path.basename(dosya), command=lambda d=dosya: dosyayi_ac(d), bootstyle="primary-outline").pack(fill=tk.X, padx=15, pady=3)

    def _dosya_yukle(self, tanim):
        try:
            kaynak = filedialog.askopenfilename(title=f"{tanim['baslik']} dosyasını seçin")
            if not kaynak:
                return

            klasor = self._klasor()
            uzanti = os.path.splitext(kaynak)[1]
            hedef = os.path.join(klasor, f"{tanim['dosya_adi']}{uzanti}")

            eski = self._yukleme_dosyasini_bul(tanim)
            if eski and os.path.abspath(eski) != os.path.abspath(hedef) and os.path.exists(eski):
                os.remove(eski)

            shutil.copy2(kaynak, hedef)

            messagebox.showinfo("Başarılı", f"✅ {tanim['baslik']} yüklendi.")
            self._durumlari_guncelle()
        except Exception as e:
            messagebox.showerror("Hata", f"❌ Dosya yükleme hatası: {str(e)}")

    def kaydet(self) -> bool:
        return True

BelgeKontrol = BelgeOlustur