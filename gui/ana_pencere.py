# gui/ana_pencere.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
import os
import subprocess
import platform

from versiyon import VERSIYON # YENİ EKLENDİ

from services.veritabani_service import VeritabaniService
from gui.kurum_girisi import KurumGirisi
from gui.alim_yonetimi import AlimYonetimi
from gui.ihtiyac_girisi import IhtiyacGirisi
from gui.teklif_girisi import TeklifGirisi
from gui.yaklasik_maliyet import YaklasikMaliyet
from gui.gerekce_formu import GerekceFormu
from gui.teklif_karsilastir import TeklifKarsilastir
from gui.muayene_kabul import MuayeneKabul
from gui.ekap_islemleri import EkapIslemleri
from gui.belge_kontrol import BelgeOlustur
from gui.rehber import RehberPenceresi

class AnaPencere:
    def __init__(self, root):
        self.root = root
        self.root.title(f"🏫 DOĞRUDAN TEMİN MODÜLÜ - {VERSIYON}") # GÜNCELLENDİ
        self.root.geometry("1280x820")
        
        self.db = VeritabaniService()
        self.alim_id = None
        self.mevcut_alim_no = None

        self.adimlar = [
            "🏛️ Kurum Bilgileri",
            "📂 Alım Yönetimi",
            "📦 İhtiyaç Listesi",
            "🏢 Firma & Teklif Girişi",
            "💰 Yaklaşık Maliyet",
            "📝 Gerekçe Formu",
            "📊 Teklif Karşılaştırma",
            "✅ Muayene Kabul",
            "📤 EKAP İşlemleri",
            "🗂️ Belge Kontrol"
        ]

        self.adim_siniflari = [
            KurumGirisi, AlimYonetimi, IhtiyacGirisi, TeklifGirisi,
            YaklasikMaliyet, GerekceFormu, 
            TeklifKarsilastir, MuayeneKabul, EkapIslemleri, BelgeOlustur
        ]

        self.aktif_adim = 0
        self.mevcut_adim_nesnesi = None
        self.adim_nesneleri = {}
        self.aktif_frame = None

        self._arayuz_olustur()
        self._yeni_alim_kontrol()
        self.adim_degistir(0)

    def _arayuz_olustur(self):
        self.ana_frame = ttk.Frame(self.root)
        self.ana_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.sol_frame = ttk.Frame(self.ana_frame, width=280) 
        self.sol_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        self.sol_frame.pack_propagate(False)

        title_frame = ttk.Frame(self.sol_frame)
        title_frame.pack(fill=tk.X, pady=(20, 15))
        ttk.Label(title_frame, text="📋 DOĞRUDAN", font=("Segoe UI", 18, "bold"), bootstyle="primary").pack()
        ttk.Label(title_frame, text="TEMİN MODÜLÜ", font=("Segoe UI", 13, "bold")).pack()
        # ARTIK VERSİYON DOSYASINDAN ÇEKİLİYOR
        ttk.Label(title_frame, text=VERSIYON, font=("Segoe UI", 10, "italic"), bootstyle="secondary").pack()

        ttk.Button(
            self.sol_frame, 
            text="📖 REHBER", 
            command=self._rehber_ac, 
            bootstyle="warning", 
            width=30,
            padding=(0, 10)
        ).pack(pady=(10, 20), padx=5)

        self.adim_butonlari = []
        for i, adim in enumerate(self.adimlar):
            btn = ttk.Button(
                self.sol_frame,
                text=adim,
                command=lambda idx=i: self.adim_degistir(idx),
                bootstyle="secondary",
                width=30,
                padding=(10, 8), 
                style="Bold.TButton"
            )
            btn.configure(cursor="hand2")
            btn.pack(pady=3, fill=tk.X, padx=5)
            btn.bind('<FocusIn>', lambda e: e.widget.master.focus_set())
            self.adim_butonlari.append(btn)
            
        try:
            self.root.style.configure("Bold.TButton", font=("Segoe UI", 10, "bold"))
        except:
            pass

        self.durum_frame = ttk.Frame(self.sol_frame)
        self.durum_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=15)
        ttk.Label(self.durum_frame, text="📊 DURUM", font=("Segoe UI", 10, "bold"), bootstyle="info").pack(anchor='w')
        self.durum_label = ttk.Label(self.durum_frame, text="🔴 Hazırlık Aşaması", font=("Segoe UI", 9, "bold"))
        self.durum_label.pack(anchor='w', pady=2)
        self.alim_no_label = ttk.Label(self.durum_frame, text="📄 Alım: -", font=("Segoe UI", 9))
        self.alim_no_label.pack(anchor='w', pady=2)

        self.sag_frame = ttk.Frame(self.ana_frame)
        self.sag_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.sag_frame.columnconfigure(0, weight=1)
        self.sag_frame.rowconfigure(1, weight=1)

        self.baslik_frame = ttk.Frame(self.sag_frame)
        self.baslik_frame.grid(row=0, column=0, sticky='ew', pady=(10, 5))

        self.baslik_label = ttk.Label(self.baslik_frame, text="", font=("Segoe UI", 20, "bold"), bootstyle="primary")
        self.baslik_label.pack(side=tk.LEFT, padx=10)

        self.progress = ttk.Progressbar(self.baslik_frame, length=250, mode='determinate', maximum=len(self.adimlar), bootstyle="success-striped")
        self.progress.pack(side=tk.RIGHT, padx=5)
        
        self.progress_text = ttk.Label(self.baslik_frame, text=f"0/{len(self.adimlar)} tamamlandı", font=("Segoe UI", 10, "bold"))
        self.progress_text.pack(side=tk.RIGHT, padx=(0, 5))
        
        self.progress_refresh_btn = ttk.Button(self.baslik_frame, text="↻", width=3, command=self.ilerlemeyi_guncelle, bootstyle="secondary-outline")
        self.progress_refresh_btn.pack(side=tk.RIGHT, padx=2)

        self.icerik_frame = ttk.Frame(self.sag_frame, padding=15, relief="solid", borderwidth=1)
        self.icerik_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)

        self.nav_frame = ttk.Frame(self.sag_frame)
        self.nav_frame.grid(row=2, column=0, sticky='ew', pady=(10, 5))

        self.onceki_btn = ttk.Button(self.nav_frame, text="◄ Önceki", command=self.onceki_adim, bootstyle="secondary", state='disabled', width=15, padding=(0, 8))
        self.onceki_btn.pack(side=tk.LEFT, padx=5)

        self.sonraki_btn = ttk.Button(self.nav_frame, text="Sonraki ►", command=self.sonraki_adim, bootstyle="primary", width=15, padding=(0, 8))
        self.sonraki_btn.pack(side=tk.LEFT, padx=5)

    def _rehber_ac(self):
        RehberPenceresi(self.root)

    def _yeni_alim_kontrol(self):
        son_alim = self.db.son_alim_getir()
        if son_alim:
            self.alim_id = son_alim.id
            self.mevcut_alim_no = son_alim.alim_no
            alim_adi = son_alim.alim_adi if hasattr(son_alim, 'alim_adi') else str(son_alim.id)
            self.alim_no_label.config(text=f"📄 Alım: {alim_adi}")
            self.durum_label.config(text="🟢 Alım devam ediyor", bootstyle="success")
        else:
            self.alim_no_label.config(text="📄 Alım: -")
            self.durum_label.config(text="🟡 Alım Yönetimi'nden alım başlatın", bootstyle="warning")

    def adim_renklendir(self):
        durumlar = self.db.ilerleme_durumlari(self.alim_id) if self.alim_id else [False] * len(self.adimlar)
        
        for i, btn in enumerate(self.adim_butonlari):
            ikon = '✓' if durumlar[i] else ('▶' if i == self.aktif_adim else '○')
            btn.config(text=f"{ikon}  {self.adimlar[i]}")
            
            if i == self.aktif_adim:
                btn.config(bootstyle="primary")
            elif durumlar[i]:
                btn.config(bootstyle="success")
            else:
                btn.config(bootstyle="secondary")
        
        tamamlanan = sum(durumlar)
        self.progress['value'] = tamamlanan
        self.progress_text.config(text=f"{tamamlanan}/{len(self.adimlar)} tamamlandı")

    def ilerlemeyi_guncelle(self):
        self.adim_renklendir()

    def adim_degistir(self, idx):
        self.aktif_adim = idx
        self.adim_renklendir()
        self.baslik_label.config(text=self.adimlar[idx])

        self.onceki_btn.config(state='normal' if idx > 0 else 'disabled')
        self.sonraki_btn.config(state='normal' if idx < len(self.adimlar) - 1 else 'disabled')

        for child in self.icerik_frame.winfo_children():
            child.pack_forget()

        self.aktif_frame = None

        if idx in self.adim_nesneleri and self.alim_id == getattr(self.adim_nesneleri[idx], 'alim_id', None):
            adim_nesnesi = self.adim_nesneleri[idx]
            if hasattr(adim_nesnesi, 'frame') and adim_nesnesi.frame:
                
                if hasattr(adim_nesnesi, 'yenile'):
                    adim_nesnesi.yenile()
                    
                self.aktif_frame = adim_nesnesi.frame
                self.aktif_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.mevcut_adim_nesnesi = adim_nesnesi
        else:
            if idx in self.adim_nesneleri:
                eski_nesne = self.adim_nesneleri[idx]
                if hasattr(eski_nesne, 'frame') and eski_nesne.frame:
                    try:
                        eski_nesne.frame.destroy()
                    except:
                        pass
                del self.adim_nesneleri[idx]

            adim_sinifi = self.adim_siniflari[idx]
            self.mevcut_adim_nesnesi = adim_sinifi(self.icerik_frame, self.db, self.alim_id, self)
            if hasattr(self.mevcut_adim_nesnesi, 'frame'):
                self.aktif_frame = self.mevcut_adim_nesnesi.frame
                self.aktif_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.adim_nesneleri[idx] = self.mevcut_adim_nesnesi

    def adim_nesnelerini_temizle(self):
        for idx, nesne in self.adim_nesneleri.items():
            if hasattr(nesne, 'frame') and nesne.frame:
                try:
                    nesne.frame.destroy()
                except:
                    pass
        self.adim_nesneleri = {}
        self.mevcut_adim_nesnesi = None
        self.aktif_frame = None

    def onceki_adim(self):
        if self.aktif_adim > 0:
            if self.mevcut_adim_nesnesi and hasattr(self.mevcut_adim_nesnesi, 'kaydet'):
                self.mevcut_adim_nesnesi.kaydet()
            self.adim_degistir(self.aktif_adim - 1)

    def sonraki_adim(self):
        if self.aktif_adim < len(self.adimlar) - 1:
            if self.mevcut_adim_nesnesi and hasattr(self.mevcut_adim_nesnesi, 'kaydet'):
                if not self.mevcut_adim_nesnesi.kaydet():
                    return
            self.adim_degistir(self.aktif_adim + 1)

    def durum_guncelle(self, mesaj):
        self.durum_label.config(text=mesaj)

    def __del__(self):
        try:
            if hasattr(self, 'db') and self.db:
                self.db.kapat()
        except:
            pass