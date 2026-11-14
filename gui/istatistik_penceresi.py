# gui/istatistik_penceresi.py
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import sqlite3
from collections import Counter
from datetime import datetime

# Matplotlib için backend ayarı (Tkinter ile çalışması için)
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

class IstatistikPenceresi:
    def __init__(self, parent, katalog):
        self.katalog = katalog
        self.pencere = tk.Toplevel(parent)
        self.pencere.title("📊 Alım İstatistikleri ve Grafikler")
        self.pencere.geometry("1000x700")
        self.pencere.transient(parent)
        self.pencere.focus_force()

        # Türkçe karakterler ve grafik ayarları
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'Segoe UI', 'Tahoma']

        self._verileri_analiz_et()
        self._arayuz_olustur()

    def _verileri_analiz_et(self):
        """Tüm arşivdeki (katalogdaki) veritabanlarını tarayıp verileri toplar."""
        self.yillik_alimlar = Counter()
        self.firma_kazanimlari = Counter()
        self.toplam_harcama = 0
        self.basariyla_okunan = 0

        kayitlar = self.katalog.listele()
        if not kayitlar:
            return

        for kayit in kayitlar:
            db_yolu = kayit.get('db_yolu')
            if not db_yolu:
                continue
            
            try:
                # Veritabanına bağlan (sadece okuma modunda)
                conn = sqlite3.connect(f"file:{db_yolu}?mode=ro", uri=True)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # 1. Yıllık Alım Sayıları
                cursor.execute("SELECT yil FROM alimlar LIMIT 1")
                row = cursor.fetchone()
                if row and row['yil']:
                    self.yillik_alimlar[row['yil']] += 1

                # 2. Kazanan Firmalar ve Tutarlar
                cursor.execute("""
                    SELECT f.unvan, d.kazanan_toplam_tutar 
                    FROM degerlendirme d 
                    JOIN firmalar f ON d.kazanan_firma_id = f.id
                """)
                for firma_row in cursor.fetchall():
                    firma = firma_row['unvan']
                    tutar = firma_row['kazanan_toplam_tutar'] or 0
                    self.firma_kazanimlari[firma] += 1
                    self.toplam_harcama += tutar

                conn.close()
                self.basariyla_okunan += 1
            except Exception as e:
                print(f"İstatistik okuma hatası ({db_yolu}): {e}")

    def _arayuz_olustur(self):
        # Üst Bilgi Paneli
        bilgi_frame = ttk.Frame(self.pencere, padding=10)
        bilgi_frame.pack(fill=tk.X)

        ttk.Label(bilgi_frame, text=f"📂 Taranan Alım Dosyası: {self.basariyla_okunan}", font=("Arial", 12, "bold"), bootstyle="primary").pack(side=tk.LEFT, padx=10)
        ttk.Label(bilgi_frame, text=f"💰 Toplam Harcama: {self.toplam_harcama:,.2f} ₺", font=("Arial", 12, "bold"), bootstyle="success").pack(side=tk.LEFT, padx=20)

        if self.basariyla_okunan == 0:
            ttk.Label(self.pencere, text="Henüz istatistik oluşturulacak bir alım verisi bulunamadı.", font=("Arial", 12), bootstyle="danger").pack(pady=50)
            return

        # Grafik Alanı
        fig = Figure(figsize=(10, 6), dpi=100)
        fig.patch.set_facecolor('#f8f9fa') # Arka plan rengi

        # --- GRAFİK 1: Yıllara Göre Alım Sayısı (Bar Chart) ---
        ax1 = fig.add_subplot(121)
        yillar = list(self.yillik_alimlar.keys())
        sayilar = list(self.yillik_alimlar.values())
        
        if yillar:
            bars = ax1.bar([str(y) for y in yillar], sayilar, color='#3498db')
            ax1.set_title("Yıllara Göre Alım Sayısı", fontsize=12, fontweight='bold')
            ax1.set_xlabel("Yıl")
            ax1.set_ylabel("Alım Adedi")
            # Barların üzerine sayıları yazdır
            for bar in bars:
                yval = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2, yval, int(yval), ha='center', va='bottom', fontweight='bold')
        else:
            ax1.text(0.5, 0.5, 'Veri Yok', ha='center', va='center')

        # --- GRAFİK 2: En Çok İhale Kazanan Firmalar (Pie Chart) ---
        ax2 = fig.add_subplot(122)
        if self.firma_kazanimlari:
            # En çok kazanan ilk 5 firmayı al
            en_iyi_5 = dict(self.firma_kazanimlari.most_common(5))
            etiketler = list(en_iyi_5.keys())
            degerler = list(en_iyi_5.values())
            
            # Uzun firma isimlerini kısalt
            etiketler = [e[:15] + "..." if len(e) > 15 else e for e in etiketler]
            
            colors = ['#2ecc71', '#e74c3c', '#f1c40f', '#9b59b6', '#e67e22']
            ax2.pie(degerler, labels=etiketler, autopct='%1.1f%%', startangle=140, colors=colors, textprops={'fontsize': 9})
            ax2.set_title("En Çok Kazanan Firmalar (İlk 5)", fontsize=12, fontweight='bold')
        else:
            ax2.text(0.5, 0.5, 'Henüz Kazanan Firma Yok', ha='center', va='center')

        fig.tight_layout()

        # Grafiği Tkinter'a Yerleştir
        canvas = FigureCanvasTkAgg(fig, master=self.pencere)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)