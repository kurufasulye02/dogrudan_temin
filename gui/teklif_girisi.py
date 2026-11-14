# gui/teklif_girisi.py
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from models.firma import Firma
from models.teklif import Teklif
from tkcalendar import DateEntry

class TeklifGirisi:
    def __init__(self, parent, db, alim_id, ana_pencere):
        self.parent = parent
        self.db = db
        self.alim_id = alim_id
        self.ana_pencere = ana_pencere

        self.firma_entryleri = []
        self.teklif_entryleri = {}
        self.tum_fiyat_entryleri = []
        self.firma_satirlari = []
        self.teklif_baslik_labelari = []
        self.teklif_canvas = None
        self.teklif_scrollable_frame = None
        self.firma_container = None
        self.kaydedildi = False
        self.firma_kayit_idleri = {}
        self.frame = None
        self.teklif_frame = None # DÜZELTİLDİ: Sınıf değişkeni olarak tanımlandı

        self._olustur()
        self.frame.bind("<Map>", self._ekran_gorunur_oldu)

    def _olustur(self):
        self.frame = ttk.LabelFrame(self.parent, text="🏢 FİRMA VE TEKLİF GİRİŞİ", padding=15)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(
            self.frame,
            text="📌 En az 2 firmadan teklif alınmalıdır. İstediğiniz kadar firma ekleyebilirsiniz.",
            font=("Arial", 10, "bold"),
            bootstyle="warning"
        ).pack(anchor='w', pady=5)

        firma_frame = ttk.LabelFrame(self.frame, text="🏢 Firma Bilgileri", padding=10)
        firma_frame.pack(fill=tk.X, pady=5)

        header_frame = ttk.Frame(firma_frame)
        header_frame.pack(fill=tk.X, pady=2)
        ttk.Label(header_frame, text="#", width=5, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2)
        ttk.Label(header_frame, text="Ünvan", width=25, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2)
        ttk.Label(header_frame, text="Vergi No", width=15, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2)
        ttk.Label(header_frame, text="Telefon", width=15, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2)
        ttk.Label(header_frame, text="Doğum Tarihi", width=15, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2)
        ttk.Label(header_frame, text="", width=5, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2)

        self.firma_container = ttk.Frame(firma_frame)
        self.firma_container.pack(fill=tk.X, pady=5)

        self._mevcut_firmalari_yukle()

        ttk.Button(
            firma_frame,
            text="➕ Yeni Firma Ekle",
            command=self._yeni_firma_ekle,
            bootstyle="info-outline"
        ).pack(pady=5)

        self.teklif_frame = ttk.LabelFrame(self.frame, text="💰 Teklif Fiyatları (KDV Hariç)", padding=10)
        self.teklif_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self._teklif_tablosunu_olustur()

        ttk.Button(
            self.frame,
            text="💾 TEKLİFLERİ KAYDET",
            command=self.kaydet,
            bootstyle="success"
        ).pack(pady=10)

        ttk.Label(
            self.frame,
            text="💡 Fiyat girdikten sonra ENTER tuşuna basarak ALTTAKİ hücreye geçebilirsiniz.",
            bootstyle="info",
            font=("Arial", 9, "italic")
        ).pack(pady=2)

    def _teklif_tablosunu_olustur(self):
        # Eski tabloyu temizle (varsa)
        if hasattr(self, 'teklif_frame') and self.teklif_frame:
            for child in self.teklif_frame.winfo_children():
                child.destroy()

        ihtiyaclar = []
        try:
            if self.alim_id:
                ihtiyaclar = self.db.ihtiyac_getir(self.alim_id)
        except Exception as e:
            print(f"❌ İhtiyaç getirme hatası: {e}")

        if not ihtiyaclar:
            ttk.Label(
                self.teklif_frame,
                text="⚠️ Önce ihtiyaç listesini kaydedin!",
                bootstyle="danger",
                font=("Arial", 12)
            ).pack(pady=50)
            return

        self.teklif_canvas = tk.Canvas(self.teklif_frame, bg='white')
        self.teklif_scrollbar = ttk.Scrollbar(self.teklif_frame, orient="vertical", command=self.teklif_canvas.yview)
        self.teklif_scrollable_frame = ttk.Frame(self.teklif_canvas)

        self.teklif_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.teklif_canvas.configure(scrollregion=self.teklif_canvas.bbox("all"))
        )
        self.teklif_canvas.create_window((0, 0), window=self.teklif_scrollable_frame, anchor="nw")
        self.teklif_canvas.configure(yscrollcommand=self.teklif_scrollbar.set)

        self.teklif_baslik_labelari = []
        self.teklif_entryleri = {}
        self.tum_fiyat_entryleri = []

        for row, kalem in enumerate(ihtiyaclar, 1):
            ttk.Label(self.teklif_scrollable_frame, text=str(row), font=("Arial", 10)).grid(
                row=row, column=0, padx=2, pady=2, sticky='w'
            )
            ttk.Label(self.teklif_scrollable_frame, text=kalem.malzeme_adi[:35], width=30, anchor='w').grid(
                row=row, column=1, padx=2, pady=2, sticky='w'
            )
            ttk.Label(self.teklif_scrollable_frame, text=f"{kalem.miktar} {kalem.birim}", width=12).grid(
                row=row, column=2, padx=2, pady=2
            )

            self.teklif_entryleri[kalem.id] = {
                'fiyatlar': [],
                'miktar': kalem.miktar,
                'row': row,
                'birim': kalem.birim
            }

        self._teklif_basliklari_guncelle(bos=True)
        self._mevcut_teklifleri_yukle()

        self.teklif_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.teklif_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _ekran_gorunur_oldu(self, event):
        if event.widget == self.frame:
            guncel_ihtiyaclar = self.db.ihtiyac_getir(self.alim_id)
            if not guncel_ihtiyaclar: return
            
            if not self.teklif_entryleri or len(self.teklif_entryleri) != len(guncel_ihtiyaclar):
                self._teklif_tablosunu_olustur()
            else:
                mevcut_ids = set(self.teklif_entryleri.keys())
                yeni_ids = set(k.id for k in guncel_ihtiyaclar)
                if mevcut_ids != yeni_ids:
                    self._teklif_tablosunu_olustur()
                else:
                    for row, kalem in enumerate(guncel_ihtiyaclar, 1):
                        for widget in self.teklif_scrollable_frame.grid_slaves(row=row, column=1):
                            if isinstance(widget, ttk.Label):
                                widget.config(text=kalem.malzeme_adi[:35])

    def _mevcut_firmalari_yukle(self):
        try:
            firmalar = self.db.firmalari_getir(self.alim_id)
            if firmalar:
                gorulen_firmalar = set()
                benzersiz_firmalar = []
                for firma in firmalar:
                    if firma.id not in gorulen_firmalar:
                        gorulen_firmalar.add(firma.id)
                        benzersiz_firmalar.append(firma)
                for idx, firma in enumerate(benzersiz_firmalar):
                    self._firma_satir_ekle(idx, self.firma_container, bos=False, firma=firma)
            else:
                for idx in range(2):
                    self._firma_satir_ekle(idx, self.firma_container, bos=True)
        except Exception as e:
            print(f"Firma yükleme hatası: {e}")
            for idx in range(2):
                self._firma_satir_ekle(idx, self.firma_container, bos=True)

    def _mevcut_teklifleri_yukle(self):
        try:
            if not self.alim_id:
                return
            teklifler = self.db.teklifleri_getir(self.alim_id)
            if not teklifler:
                return
            
            mevcut_ihtiyac_ids = set(self.teklif_entryleri.keys())
            
            for teklif in teklifler:
                ihtiyac_id = teklif.get('ihtiyac_id')
                if ihtiyac_id not in mevcut_ihtiyac_ids:
                    continue
                    
                firma_index = None
                for idx, (_, _, _, _, frame) in enumerate(self.firma_entryleri):
                    if self.firma_kayit_idleri.get(frame) == teklif.get('firma_id'):
                        firma_index = idx
                        break
                if firma_index is not None and ihtiyac_id in self.teklif_entryleri:
                    fiyatlar = self.teklif_entryleri[ihtiyac_id]['fiyatlar']
                    if firma_index < len(fiyatlar):
                        fiyatlar[firma_index].delete(0, tk.END)
                        fiyatlar[firma_index].insert(0, str(teklif.get('birim_fiyat', '')))
        except Exception as e:
            print(f"Teklif yükleme hatası: {e}")

    def _yeni_firma_ekle(self):
        idx = len(self.firma_entryleri)
        self._firma_satir_ekle(idx, self.firma_container, bos=True)
        self._teklif_basliklari_guncelle(bos=True)

    def _firma_satir_ekle(self, idx, container, bos=False, firma=None):
        row_frame = ttk.Frame(container)
        row_frame.pack(fill=tk.X, pady=2)

        ttk.Label(row_frame, text=str(idx + 1), width=5).pack(side=tk.LEFT, padx=2)

        entry_unvan = ttk.Entry(row_frame, width=25)
        entry_unvan.pack(side=tk.LEFT, padx=2)
        if firma:
            entry_unvan.insert(0, firma.unvan)
        elif not bos:
            entry_unvan.insert(0, f"FİRMA_{idx+1}")

        def on_unvan_change(*args):
            self._teklif_basliklari_guncelle(bos=True)
        entry_unvan.bind('<KeyRelease>', lambda e: on_unvan_change())

        entry_vkn = ttk.Entry(row_frame, width=15)
        entry_vkn.pack(side=tk.LEFT, padx=2)
        if firma:
            entry_vkn.insert(0, firma.vergi_no)
        elif not bos:
            entry_vkn.insert(0, f"123456789{idx+1}")

        entry_telefon = ttk.Entry(row_frame, width=15)
        entry_telefon.pack(side=tk.LEFT, padx=2)
        if firma:
            entry_telefon.insert(0, firma.telefon)
        elif not bos:
            entry_telefon.insert(0, f"05{idx+1}2 345 67 89")

        # DOĞUM TARİHİ
        entry_dogum = DateEntry(row_frame, width=13, date_pattern='dd.mm.yyyy', locale='tr_TR', background='#2C3E50', foreground='white')
        entry_dogum.pack(side=tk.LEFT, padx=2)
        
        if firma and firma.dogum_tarihi:
            try:
                from datetime import datetime
                dt = datetime.strptime(firma.dogum_tarihi, '%d.%m.%Y')
                entry_dogum.set_date(dt)
            except:
                pass

        if idx >= 2:
            sil_btn = ttk.Button(
                row_frame,
                text="🗑️",
                width=3,
                command=lambda: self._firma_satir_sil(row_frame, idx),
                bootstyle="danger-outline"
            )
            sil_btn.pack(side=tk.LEFT, padx=2)
        else:
            ttk.Label(row_frame, text="", width=5).pack(side=tk.LEFT, padx=2)

        self.firma_entryleri.append((entry_unvan, entry_vkn, entry_telefon, entry_dogum, row_frame))
        if firma is not None:
            self.firma_kayit_idleri[row_frame] = firma.id

    def _firma_satir_sil(self, row_frame, idx):
        if len(self.firma_entryleri) <= 2:
            messagebox.showwarning("Uyarı", "En az 2 firma olmalıdır!")
            return

        row_frame.destroy()
        new_list = []
        for i, (unvan, vkn, telefon, dogum, frame) in enumerate(self.firma_entryleri):
            if frame != row_frame:
                new_list.append((unvan, vkn, telefon, dogum, frame))
        self.firma_entryleri = new_list

        for i, (unvan, vkn, telefon, dogum, frame) in enumerate(self.firma_entryleri):
            for child in frame.winfo_children():
                if isinstance(child, ttk.Label) and child.cget('text').isdigit():
                    child.config(text=str(i + 1))
                    break

        self._teklif_basliklari_guncelle(bos=True)

    def _teklif_basliklari_guncelle(self, bos=False):
        if not hasattr(self, 'teklif_scrollable_frame') or self.teklif_scrollable_frame is None:
            return
        if not hasattr(self, 'teklif_entryleri') or not self.teklif_entryleri:
            return

        firma_sayisi = len(self.firma_entryleri)

        for lbl in self.teklif_baslik_labelari:
            lbl.destroy()
        self.teklif_baslik_labelari = []

        basliklar = ["No", "Malzeme Adı", "Miktar"]

        firma_adlari = []
        gorulen = set()
        for entry_unvan, _, _, _, _ in self.firma_entryleri:
            unvan = entry_unvan.get().strip()
            if unvan and unvan not in gorulen:
                gorulen.add(unvan)
                firma_adlari.append(unvan)
            elif not unvan:
                firma_adlari.append(f"Firma {len(firma_adlari)+1}")

        for ad in firma_adlari:
            basliklar.append(ad)

        col = 0
        for baslik in basliklar:
            lbl = ttk.Label(
                self.teklif_scrollable_frame,
                text=baslik,
                font=("Arial", 9, "bold"),
                background='#E8E8E8',
                relief=tk.RIDGE,
                padding=3
            )
            lbl.grid(row=0, column=col, padx=1, pady=2, sticky='ew')
            self.teklif_baslik_labelari.append(lbl)
            col += 1

        self.tum_fiyat_entryleri = []

        for ihtiyac_id, veri in self.teklif_entryleri.items():
            row = veri['row']
            miktar = veri['miktar']

            for entry in veri['fiyatlar']:
                entry.destroy()
            veri['fiyatlar'] = []

            for f in range(firma_sayisi):
                entry = ttk.Entry(self.teklif_scrollable_frame, width=12, font=("Arial", 10))
                entry.grid(row=row, column=3+f, padx=1, pady=1)

                def on_enter(e, current_row=row, current_col=3+f):
                    self._entry_ileri_gotur(current_row, current_col)

                entry.bind('<Return>', on_enter)
                entry.bind('<Down>', on_enter)

                veri['fiyatlar'].append(entry)
                self.tum_fiyat_entryleri.append(entry)

        if self.tum_fiyat_entryleri:
            son_entry = self.tum_fiyat_entryleri[-1]
            def on_last_enter(e):
                self.kaydet()
            son_entry.bind('<Return>', on_last_enter)

        if hasattr(self, 'teklif_canvas') and self.teklif_canvas:
            self.teklif_canvas.configure(scrollregion=self.teklif_canvas.bbox("all"))

    def _entry_ileri_gotur(self, current_row, current_col):
        firma_sayisi = len(self.firma_entryleri)
        toplam_satir = len(self.teklif_entryleri)
        firma_index = current_col - 3
        next_row = current_row + 1
        next_col = current_col

        if next_row > toplam_satir:
            next_row = 1

        target_entry = None
        for entry_data in self.teklif_entryleri.values():
            if entry_data['row'] == next_row:
                if firma_index < len(entry_data['fiyatlar']):
                    target_entry = entry_data['fiyatlar'][firma_index]
                    break

        if target_entry:
            target_entry.focus_set()
            target_entry.select_range(0, tk.END)
        else:
            for child in self.parent.winfo_children():
                if isinstance(child, ttk.Button) and child.cget('text') == "💾 TEKLİFLERİ KAYDET":
                    child.focus_set()
                    break

    def kaydet(self) -> bool:
        try:
            if not self.alim_id:
                messagebox.showwarning("Uyarı", "Önce alım kaydını oluşturun!")
                return False

            firma_ids = []
            firma_ciftleri = set()
            for entry_unvan, entry_vkn, entry_telefon, entry_dogum, frame in self.firma_entryleri:
                unvan = entry_unvan.get().strip()
                vkn = entry_vkn.get().strip()
                telefon = entry_telefon.get().strip()
                
                try:
                    dogum = entry_dogum.get_date().strftime('%d.%m.%Y')
                except:
                    dogum = ""

                if not unvan or not vkn:
                    messagebox.showwarning("Uyarı", "Her firma için unvan ve vergi numarası girilmelidir.")
                    return False
                    
                firma = Firma(unvan=unvan, vergi_no=vkn, telefon=telefon, dogum_tarihi=dogum)
                firma_id = self.db.firma_kaydet(firma)
                if firma_id in firma_ciftleri:
                    messagebox.showwarning("Uyarı", "Aynı firma birden fazla satıra eklenemez.")
                    return False
                firma_ciftleri.add(firma_id)
                firma_ids.append(firma_id)
                self.firma_kayit_idleri[frame] = firma_id

            if len(firma_ids) < 2:
                messagebox.showwarning("Uyarı", "En az 2 farklı firma kaydedilmelidir!")
                return False

            guncel_ihtiyaclar = self.db.ihtiyac_getir(self.alim_id)
            if not guncel_ihtiyaclar:
                messagebox.showerror("Hata", "İhtiyaç listesi bulunamadı!")
                return False
            
            sira_to_id = {k.sira_no: k.id for k in guncel_ihtiyaclar}
            
            teklifler = []
            for eski_ihtiyac_id, veri in self.teklif_entryleri.items():
                ekran_sira_no = veri['row']
                guncel_ihtiyac_id = sira_to_id.get(ekran_sira_no, eski_ihtiyac_id)

                fiyatlar = veri['fiyatlar']
                for f_idx, entry in enumerate(fiyatlar):
                    if f_idx < len(firma_ids):
                        try:
                            fiyat_str = entry.get().strip().replace(',', '.')
                            if fiyat_str:
                                birim_fiyat = float(fiyat_str)
                                if birim_fiyat > 0:
                                    teklif = Teklif(
                                        alim_id=self.alim_id,
                                        firma_id=firma_ids[f_idx],
                                        ihtiyac_id=guncel_ihtiyac_id,
                                        birim_fiyat=birim_fiyat
                                    )
                                    teklifler.append(teklif)
                        except ValueError:
                            messagebox.showwarning("Geçersiz Fiyat", f"{self.firma_entryleri[f_idx][0].get().strip()} firmasının fiyatlarından biri geçersiz.")
                            return False

            if not teklifler:
                messagebox.showwarning("Uyarı", "En az 2 firmadan, bütün ihtiyaç kalemleri için teklif giriniz!")
                return False

            try:
                self.db.teklif_kaydet(teklifler, self.alim_id)
            except ValueError as e:
                messagebox.showwarning("Teklif Kontrolü", str(e))
                return False
            self.kaydedildi = True

            if self.ana_pencere:
                self.ana_pencere.durum_guncelle(f"🟢 {len(teklifler)} teklif kaydedildi ✅")

            messagebox.showinfo("Başarılı", f"✅ {len(teklifler)} teklif kaydedildi!")
            return True

        except Exception as e:
            messagebox.showerror("Hata", f"❌ Teklif kayıt hatası: {str(e)}")
            return False