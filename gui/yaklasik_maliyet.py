# gui/yaklasik_maliyet.py
import os
import tkinter as tk
from tkinter import ttk, messagebox
from services.maliyet_service import MaliyetService
from services.rapor_service import RaporService
from gui.dosya_yardimci import alim_klasoru_getir, klasoru_ac
from utils.ui_helpers import fare_tekerlegi_bagla
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class YaklasikMaliyet:
    def __init__(self, parent, db, alim_id, ana_pencere):
        self.parent = parent
        self.db = db
        self.alim_id = alim_id
        self.ana_pencere = ana_pencere
        self.kdv_entryleri = {}
        self.kaydedildi = False
        self.frame = None
        self.main_container = None
        
        self._olustur()
        # EKRANA HER GELİNDİĞİNDE YENİLE
        self.frame.bind("<Map>", self._ekran_yenile)

    def _olustur(self):
        self.frame = ttk.LabelFrame(self.parent, text="💰 YAKLAŞIK MALİYET", padding=15)
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

        teklifler = self.db.teklifleri_getir(self.alim_id)
        if not teklifler:
            ttk.Label(self.main_container, text="⚠️ Henüz teklif girilmemiş!", bootstyle="danger").pack(pady=20)
            return

        maliyetler = MaliyetService.yaklasik_maliyet_hesapla(teklifler)
        
        alim = self.db.alim_getir(self.alim_id)
        odeneck = alim.odeneck_miktari if alim and alim.odeneck_miktari else 0

        result_frame = ttk.Frame(self.main_container)
        result_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(result_frame, bg='white')
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        fare_tekerlegi_bagla(scrollable_frame, canvas)

        headers = ["Malzeme", "Miktar", "Ort. Birim Fiyat", "Ort. Toplam", "KDV %", "KDV'li Toplam"]
        for col, header in enumerate(headers):
            lbl = ttk.Label(
                scrollable_frame,
                text=header,
                font=("Arial", 10, "bold"),
                background='#E8E8E8',
                relief=tk.RIDGE,
                padding=5
            )
            lbl.grid(row=0, column=col, padx=2, pady=5, sticky='ew')

        self.kdv_entryleri = {}
        row = 1
        genel_toplam_kdv_haric = 0

        for malzeme, veri in maliyetler.items():
            miktar = veri.get('miktar', 0)
            ortalama = veri.get('ortalama_birim', 0)
            toplam = veri.get('toplam', 0)
            genel_toplam_kdv_haric += toplam

            ttk.Label(scrollable_frame, text=malzeme[:40], anchor='w').grid(row=row, column=0, padx=5, pady=2, sticky='w')
            ttk.Label(scrollable_frame, text=f"{miktar}").grid(row=row, column=1, padx=5, pady=2)
            ttk.Label(scrollable_frame, text=f"₺{ortalama:.2f}").grid(row=row, column=2, padx=5, pady=2)
            lbl_toplam = ttk.Label(scrollable_frame, text=f"₺{toplam:.2f}")
            lbl_toplam.grid(row=row, column=3, padx=5, pady=2)

            entry_kdv = ttk.Entry(scrollable_frame, width=8, font=("Arial", 10))
            kdv_orani = self._kdv_orani_getir(malzeme)
            if kdv_orani is not None:
                entry_kdv.insert(0, str(kdv_orani))
            else:
                entry_kdv.insert(0, "20")
            entry_kdv.grid(row=row, column=4, padx=5, pady=2)

            lbl_kdvli = ttk.Label(scrollable_frame, text="", font=("Arial", 10, "bold"), bootstyle="success")
            lbl_kdvli.grid(row=row, column=5, padx=5, pady=2)

            def on_kdv_change(e, m=malzeme, t=toplam, lbl=lbl_kdvli, entry=entry_kdv):
                try:
                    kdv_orani = float(entry.get().strip() or 0)
                    kdvli = t * (1 + kdv_orani / 100)
                    lbl.config(text=f"₺{kdvli:.2f}")
                    self._genel_toplam_guncelle()
                    self._kdv_orani_kaydet(m, kdv_orani)
                except ValueError:
                    lbl.config(text="Hata!")

            entry_kdv.bind('<KeyRelease>', on_kdv_change)
            entry_kdv.bind('<FocusOut>', on_kdv_change)

            try:
                kdv_orani = float(entry_kdv.get().strip() or 20)
                kdvli = toplam * (1 + kdv_orani / 100)
                lbl_kdvli.config(text=f"₺{kdvli:.2f}")
            except:
                lbl_kdvli.config(text="₺0.00")

            self.kdv_entryleri[malzeme] = {
                'entry': entry_kdv,
                'lbl_toplam': lbl_toplam,
                'lbl_kdvli': lbl_kdvli,
                'toplam': toplam
            }
            row += 1

        ttk.Separator(scrollable_frame, orient='horizontal').grid(row=row, column=0, columnspan=6, sticky='ew', pady=5)
        row += 1

        self.lbl_genel_kdv_haric = ttk.Label(scrollable_frame, text=f"₺{genel_toplam_kdv_haric:.2f}", font=("Arial", 10, "bold"), bootstyle="primary")
        self.lbl_genel_kdv_haric.grid(row=row, column=3, padx=5, pady=5)

        self.lbl_genel_kdv_dahil = ttk.Label(scrollable_frame, text="", font=("Arial", 10, "bold"), bootstyle="success")
        self.lbl_genel_kdv_dahil.grid(row=row, column=5, padx=5, pady=5)

        ttk.Label(scrollable_frame, text="📊 GENEL TOPLAM", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, padx=5, pady=5)
        row += 1

        self.lbl_odeneck = ttk.Label(scrollable_frame, text="", font=("Arial", 10, "bold"))
        self.lbl_odeneck.grid(row=row, column=0, columnspan=6, pady=10)

        self._genel_toplam_guncelle()
        self._odeneck_kontrol(odeneck)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = ttk.Frame(self.main_container)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="💾 KDV ORANLARINI KAYDET", command=self.kdv_oranlarini_kaydet, bootstyle="success").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📄 RAPOR OLUŞTUR", command=self.rapor_olustur, bootstyle="primary").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✉️ TEKLİF MEKTUBU OLUŞTUR", command=self.teklif_mektubu_olustur, bootstyle="primary").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📤 HYS RAPORU OLUŞTUR", command=self.mys_raporu_olustur, bootstyle="info").pack(side=tk.LEFT, padx=5)

    def _kdv_orani_getir(self, malzeme_adi: str) -> float:
        try:
            self.db.cursor.execute("""
                SELECT kdv_orani FROM yaklasik_maliyet 
                WHERE alim_id = ? AND malzeme_adi = ?
            """, (self.alim_id, malzeme_adi))
            row = self.db.cursor.fetchone()
            if row:
                return row[0]
            return None
        except:
            return None

    def _kdv_orani_kaydet(self, malzeme_adi: str, kdv_orani: float):
        try:
            self.db.cursor.execute("""
                SELECT id FROM yaklasik_maliyet 
                WHERE alim_id = ? AND malzeme_adi = ?
            """, (self.alim_id, malzeme_adi))
            row = self.db.cursor.fetchone()
            if row:
                self.db.cursor.execute("""
                    UPDATE yaklasik_maliyet SET kdv_orani = ? WHERE alim_id = ? AND malzeme_adi = ?
                """, (kdv_orani, self.alim_id, malzeme_adi))
            else:
                self.db.cursor.execute("""
                    INSERT INTO yaklasik_maliyet (alim_id, malzeme_adi, kdv_orani) VALUES (?, ?, ?)
                """, (self.alim_id, malzeme_adi, kdv_orani))
            self.db.connection.commit()
            self.kaydedildi = True
        except Exception as e:
            print(f"KDV kaydetme hatası: {e}")

    def kdv_oranlarini_kaydet(self):
        try:
            kaydedilen = 0
            for malzeme, veri in self.kdv_entryleri.items():
                try:
                    kdv_orani = float(veri['entry'].get().strip() or 0)
                    self._kdv_orani_kaydet(malzeme, kdv_orani)
                    kaydedilen += 1
                except ValueError:
                    pass
            if kaydedilen > 0:
                messagebox.showinfo("Başarılı", f"✅ {kaydedilen} KDV oranı kaydedildi!")
                if self.ana_pencere:
                    self.ana_pencere.durum_guncelle(f"🟢 {kaydedilen} KDV oranı kaydedildi ✅")
            else:
                messagebox.showwarning("Uyarı", "Kaydedilecek KDV oranı bulunamadı!")
        except Exception as e:
            messagebox.showerror("Hata", f"❌ KDV kayıt hatası: {str(e)}")

    def _genel_toplam_guncelle(self):
        try:
            genel_kdv_dahil = 0
            for malzeme, veri in self.kdv_entryleri.items():
                try:
                    kdv_orani = float(veri['entry'].get().strip() or 0)
                    toplam = veri['toplam']
                    kdvli = toplam * (1 + kdv_orani / 100)
                    veri['lbl_kdvli'].config(text=f"₺{kdvli:.2f}")
                    genel_kdv_dahil += kdvli
                except ValueError:
                    pass
            if hasattr(self, 'lbl_genel_kdv_dahil'):
                self.lbl_genel_kdv_dahil.config(text=f"₺{genel_kdv_dahil:.2f}")
            if hasattr(self, '_odeneck_kontrol'):
                self._odeneck_kontrol()
        except Exception as e:
            print(f"Genel toplam güncelleme hatası: {e}")

    def _odeneck_kontrol(self, odeneck=None):
        try:
            if odeneck is None:
                alim = self.db.alim_getir(self.alim_id)
                odeneck = alim.odeneck_miktari if alim and alim.odeneck_miktari else 0
            
            genel_kdv_dahil = 0
            for malzeme, veri in self.kdv_entryleri.items():
                try:
                    kdv_orani = float(veri['entry'].get().strip() or 0)
                    toplam = veri['toplam']
                    kdvli = toplam * (1 + kdv_orani / 100)
                    genel_kdv_dahil += kdvli
                except ValueError:
                    pass
                    
            if hasattr(self, 'lbl_odeneck'):
                if genel_kdv_dahil > odeneck:
                    asilan_miktar = genel_kdv_dahil - odeneck
                    self.lbl_odeneck.config(
                        text=f"⚠️ UYARI: Toplam maliyet (₺{genel_kdv_dahil:,.2f}) ödeneği (₺{odeneck:,.2f}) {asilan_miktar:,.2f} TL aşıyor!",
                        bootstyle="danger"
                    )
                else:
                    kalan_miktar = odeneck - genel_kdv_dahil
                    self.lbl_odeneck.config(
                        text=f"✅ Ödenek yeterli: Kalan Ödenek ₺{kalan_miktar:,.2f} (Ödenek: ₺{odeneck:,.2f} - Toplam: ₺{genel_kdv_dahil:,.2f})",
                        bootstyle="success"
                    )
        except Exception as e:
            print(f"Ödenek kontrol hatası: {e}")

    def mys_raporu_olustur(self):
        try:
            alim = self.db.alim_getir(self.alim_id)
            if not alim: return
            ihtiyaclar = self.db.ihtiyac_getir(self.alim_id)
            teklifler = self.db.teklifleri_getir(self.alim_id)
            
            rapor = RaporService(output_dir=self._output_dir())
            dosya = rapor.mys_yaklasik_maliyet_raporu(alim, ihtiyaclar, teklifler)
            messagebox.showinfo("Başarılı", f"✅ HYS Yaklaşık Maliyet raporu oluşturuldu:\n{os.path.basename(dosya)}")
            self._cikti_klasoru_ac()
        except Exception as e:
            messagebox.showerror("Hata", f"❌ Rapor oluşturma hatası: {str(e)}")

    def rapor_olustur(self):
        try:
            alim = self.db.alim_getir(self.alim_id)
            kurum = self.db.kurum_getir()
            if not alim or not kurum: return
            ihtiyaclar = self.db.ihtiyac_getir(self.alim_id)
            teklifler = self.db.teklifleri_getir(self.alim_id)
            
            rapor = RaporService(output_dir=self._output_dir())
            dosya = rapor.yaklasik_maliyet_cetveli(alim, kurum, ihtiyaclar, teklifler)
            messagebox.showinfo("Başarılı", f"✅ Yaklaşık Maliyet Hesap Cetveli oluşturuldu:\n{os.path.basename(dosya)}")
            self._cikti_klasoru_ac()
        except Exception as e:
            messagebox.showerror("Hata", f"❌ Rapor oluşturma hatası: {str(e)}")

    def teklif_mektubu_olustur(self):
        try:
            alim = self.db.alim_getir(self.alim_id)
            kurum = self.db.kurum_getir()
            if not alim or not kurum: return
            if not kurum.satin_alma_gorevlileri(): return
            
            ihtiyaclar = self.db.ihtiyac_getir(self.alim_id)
            teklifler = self.db.teklifleri_getir(self.alim_id)
            firma_idler = sorted({t['firma_id'] for t in teklifler})
            
            rapor = RaporService(output_dir=self._output_dir())
            olusturulan = []
            for firma_id in firma_idler:
                firma = self.db.firma_getir(firma_id)
                if firma:
                    dosya = rapor.teklif_mektubu(alim, kurum, ihtiyaclar, firma)
                    olusturulan.append(os.path.basename(dosya))

            messagebox.showinfo("Başarılı", "✅ Teklif Mektupları oluşturuldu:\n" + "\n".join(olusturulan))
            self._cikti_klasoru_ac()
        except Exception as e:
            messagebox.showerror("Hata", f"❌ Hata: {str(e)}")

    def _output_dir(self) -> str:
        return alim_klasoru_getir(self.db, self.alim_id)

    def _cikti_klasoru_ac(self):
        klasoru_ac(self._output_dir())

    def kaydet(self) -> bool:
        return True