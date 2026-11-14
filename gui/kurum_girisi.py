# gui/kurum_girisi.py
import tkinter as tk
from tkinter import ttk, messagebox
from models.kurum import Kurum


class KurumGirisi:
    def __init__(self, parent, db, alim_id, ana_pencere):
        self.parent = parent
        self.db = db
        self.alim_id = alim_id
        self.ana_pencere = ana_pencere
        self.entryler = {}
        self.placeholderlar = {}
        self.ust_makam_var = tk.StringVar(value="ilce")
        self.canvas = None
        self.scrollable_frame = None
        self.frame = None
        self._olustur()
        self._doldur()

    def _placeholder_ekle(self, label, entry, ornek):
        self.entryler[label] = entry
        self.placeholderlar[label] = f"Örn. {ornek}"
        self._placeholder_goster(label)
        entry.bind("<FocusIn>", lambda event, l=label: self._placeholder_temizle(l))
        entry.bind("<FocusOut>", lambda event, l=label: self._placeholder_goster(l))

    def _placeholder_goster(self, label):
        entry = self.entryler[label]
        if not entry.get().strip():
            entry.delete(0, tk.END)
            entry.insert(0, self.placeholderlar[label])
            entry.configure(foreground='gray')

    def _placeholder_temizle(self, label):
        entry = self.entryler[label]
        if entry.get().strip() == self.placeholderlar.get(label):
            entry.delete(0, tk.END)
            entry.configure(foreground='black')

    def _entry_degeri(self, label):
        deger = self.entryler[label].get().strip()
        return "" if deger == self.placeholderlar.get(label) else deger

    def _entry_deger_yaz(self, label, value):
        entry = self.entryler[label]
        entry.delete(0, tk.END)
        if value is not None and str(value).strip():
            entry.configure(foreground='black')
            entry.insert(0, str(value))
        else:
            self._placeholder_goster(label)

    def _olustur(self):
        self.frame = ttk.LabelFrame(self.parent, text="🏫 KURUM BİLGİLERİ", padding=20)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        info_frame = ttk.Frame(self.frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(
            info_frame,
            text="💡 Bu ekranda sadece kurum bilgilerini güncelleyin. Alım işlemleri için sonraki adıma geçin.",
            foreground='blue',
            font=("Arial", 9, "italic")
        ).pack(anchor='w')

        kurum_frame = ttk.Frame(self.frame)
        kurum_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Arka planı hafif gri yapalım ki beyaz alan göze batmasın
        self.canvas = tk.Canvas(kurum_frame, bg='#F8F9FA', highlightthickness=0)
        scrollbar = ttk.Scrollbar(kurum_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Canvas içine bir pencere oluştur
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        # YENİ: Canvas boyutu değiştiğinde scrollable_frame'in genişliğini canvas genişliğine eşitle
        def _canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        
        self.canvas.bind('<Configure>', _canvas_configure)

        def _on_mousewheel(event):
            if self.canvas and self.canvas.winfo_exists():
                try:
                    self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                except:
                    pass

        def _on_mousewheel_linux(event):
            if self.canvas and self.canvas.winfo_exists():
                try:
                    self.canvas.yview_scroll(int(-1 * event.num), "units")
                except:
                    pass

        def _scrollable_widgetleri_bagla(widget):
            widget.bind("<MouseWheel>", _on_mousewheel, add="+")
            widget.bind("<Button-4>", _on_mousewheel_linux, add="+")
            widget.bind("<Button-5>", _on_mousewheel_linux, add="+")
            for child in widget.winfo_children():
                _scrollable_widgetleri_bagla(child)

        # ===== YENİ: İçeriği tutacak ve ortalayacak form_frame =====
        form_frame = ttk.Frame(self.scrollable_frame)
        form_frame.pack(pady=20, expand=False) # expand=False ve varsayılan pack ile yatayda ortalalanır

        labels = [
            ("Kurum Adı:", "Hasandede İlkokulu", 50),
            ("İl:", "Bartın", 30),
            ("İlçe:", "Ulus", 30),
            ("DETSIS No (Resmi Yazışma Kodu):", "17636644", 30),
            ("Harcama Yetkilisi (Ad):", "ORHAN ALKAN", 30),
            ("Harcama Yetkilisi (Unvan):", "Müdür", 25),
            ("Gerçekleştirme Görevlisi (Ad):", "ORHAN ALKAN", 30),
            ("Gerçekleştirme Görevlisi (Unvan):", "Müdür", 25),
        ]

        row = 0
        for label, default, width in labels:
            ttk.Label(form_frame, text=label, font=("Arial", 10)).grid(
                row=row, column=0, sticky='e', padx=10, pady=8
            )
            entry = ttk.Entry(form_frame, width=width, font=("Arial", 10))
            entry.grid(row=row, column=1, sticky='w', padx=10, pady=8)
            self._placeholder_ekle(label, entry, default)
            row += 1

        # Üst Makam Seçimi
        ttk.Label(
            form_frame, text="Üst Makam / Milli Eğitim Müdürlüğü:",
            font=("Arial", 10, "bold")
        ).grid(row=row, column=0, sticky='e', padx=10, pady=8)
        makam_frame = ttk.Frame(form_frame)
        makam_frame.grid(row=row, column=1, sticky='w', padx=10, pady=8)
        ttk.Radiobutton(
            makam_frame, text="İL (Valilik / İl Milli Eğitim Müdürlüğü)",
            variable=self.ust_makam_var, value="il"
        ).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(
            makam_frame, text="İLÇE (Kaymakamlık / İlçe Milli Eğitim Müdürlüğü)",
            variable=self.ust_makam_var, value="ilce"
        ).pack(side=tk.LEFT)
        row += 1

        # ===== SATIN ALMA GÖREVLİLERİ (Yan Yana) =====
        ttk.Separator(form_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky='ew', pady=10
        )
        row += 1
        ttk.Label(
            form_frame, text="🖊️ SATIN ALMA GÖREVLİLERİ",
            font=("Arial", 10, "bold"), foreground='#1a7a5e'
        ).grid(row=row, column=0, columnspan=2, pady=(0, 5))
        row += 1

        basliklar_frame = ttk.Frame(form_frame)
        basliklar_frame.grid(row=row, column=0, columnspan=2, sticky='w', padx=10, pady=(5, 0))
        ttk.Label(basliklar_frame, text="Üye", width=6, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2)
        ttk.Label(basliklar_frame, text="Ad Soyad", width=25, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2)
        ttk.Label(basliklar_frame, text="Unvan", width=20, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2)
        ttk.Label(basliklar_frame, text="TC Kimlik No", width=15, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2)
        row += 1

        satin_alma_varsayilan = [
            ("NAZİF OZAN", "ÖĞRETMEN", ""),
            ("YUNUS ÇELİK", "ÖĞRETMEN", ""),
            ("MAKBULE BOZKURT", "ÖĞRETMEN", ""),
        ]
        for i, (ad_default, unvan_default, tc_default) in enumerate(satin_alma_varsayilan, start=1):
            satir_frame = ttk.Frame(form_frame)
            satir_frame.grid(row=row, column=0, columnspan=2, sticky='w', padx=10, pady=3)

            ttk.Label(satir_frame, text=str(i), width=6).pack(side=tk.LEFT, padx=2)

            entry_ad = ttk.Entry(satir_frame, width=25, font=("Arial", 10))
            entry_ad.pack(side=tk.LEFT, padx=2)
            self._placeholder_ekle(f"Satın Alma {i} (Ad):", entry_ad, ad_default)

            entry_unvan = ttk.Entry(satir_frame, width=20, font=("Arial", 10))
            entry_unvan.pack(side=tk.LEFT, padx=2)
            self._placeholder_ekle(f"Satın Alma {i} (Unvan):", entry_unvan, unvan_default)

            entry_tc = ttk.Entry(satir_frame, width=15, font=("Arial", 10))
            entry_tc.pack(side=tk.LEFT, padx=2)
            self._placeholder_ekle(f"Satın Alma {i} (TC):", entry_tc, "11 haneli TC")

            row += 1

        # ===== MUAYENE VE KABUL KOMİSYONU (Yan Yana) =====
        ttk.Separator(form_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky='ew', pady=10
        )
        row += 1
        ttk.Label(
            form_frame, text="🖊️ MUAYENE VE KABUL KOMİSYONU GÖREVLİLERİ",
            font=("Arial", 10, "bold"), foreground='#1a7a5e'
        ).grid(row=row, column=0, columnspan=2, pady=(0, 5))
        row += 1

        basliklar_frame2 = ttk.Frame(form_frame)
        basliklar_frame2.grid(row=row, column=0, columnspan=2, sticky='w', padx=10, pady=(5, 0))
        ttk.Label(basliklar_frame2, text="Üye", width=6, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2)
        ttk.Label(basliklar_frame2, text="Ad Soyad", width=25, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2)
        ttk.Label(basliklar_frame2, text="Unvan", width=20, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2)
        ttk.Label(basliklar_frame2, text="TC Kimlik No", width=15, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2)
        row += 1

        muayene_varsayilan = [
            ("İLKNUR ÖZDEMİR BİLLİK", "ÖĞRETMEN", ""),
            ("AHU ÜNSAL", "ÖĞRETMEN", ""),
            ("MİNTEHA ÇOK", "ÖĞRETMEN", ""),
        ]
        for i, (ad_default, unvan_default, tc_default) in enumerate(muayene_varsayilan, start=1):
            satir_frame = ttk.Frame(form_frame)
            satir_frame.grid(row=row, column=0, columnspan=2, sticky='w', padx=10, pady=3)

            ttk.Label(satir_frame, text=str(i), width=6).pack(side=tk.LEFT, padx=2)

            entry_ad = ttk.Entry(satir_frame, width=25, font=("Arial", 10))
            entry_ad.pack(side=tk.LEFT, padx=2)
            self._placeholder_ekle(f"Muayene {i} (Ad):", entry_ad, ad_default)

            entry_unvan = ttk.Entry(satir_frame, width=20, font=("Arial", 10))
            entry_unvan.pack(side=tk.LEFT, padx=2)
            self._placeholder_ekle(f"Muayene {i} (Unvan):", entry_unvan, unvan_default)

            entry_tc = ttk.Entry(satir_frame, width=15, font=("Arial", 10))
            entry_tc.pack(side=tk.LEFT, padx=2)
            self._placeholder_ekle(f"Muayene {i} (TC):", entry_tc, "11 haneli TC")

            row += 1

        ttk.Separator(form_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky='ew', pady=10
        )
        row += 1

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)

        ttk.Button(
            btn_frame,
            text="💾 KURUM BİLGİLERİNİ KAYDET",
            command=self.kaydet,
            style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="🔄 Alanları Temizle",
            command=self.temizle
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(
            form_frame,
            text="💡 Bilgileri düzenledikten sonra 'Kurum Bilgilerini Kaydet' butonuna tıklayın.",
            foreground='blue',
            font=("Arial", 9, "italic")
        ).grid(row=row + 1, column=0, columnspan=2, pady=10)

        _scrollable_widgetleri_bagla(self.scrollable_frame)
        self.canvas.bind("<MouseWheel>", _on_mousewheel, add="+")
        self.canvas.bind("<Button-4>", _on_mousewheel_linux, add="+")
        self.canvas.bind("<Button-5>", _on_mousewheel_linux, add="+")

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _doldur(self):
        # ... (doldurma kodları aynı kalıyor, önceki mesajdaki gibi) ...
        # Değişiklik yok, sadece yukarıdaki _olustur kısmı güncellendi.
        kurum = self.db.kurum_getir()
        if kurum:
            entry_map = {
                "Kurum Adı:": kurum.kurum_adi,
                "İl:": kurum.il,
                "İlçe:": kurum.ilce,
                "DETSIS No (Resmi Yazışma Kodu):": kurum.detsis_no,
                "Harcama Yetkilisi (Ad):": kurum.harcama_yetkilisi_ad,
                "Harcama Yetkilisi (Unvan):": kurum.harcama_yetkilisi_unvan,
                "Gerçekleştirme Görevlisi (Ad):": kurum.gerceklestirme_gorevlisi_ad,
                "Gerçekleştirme Görevlisi (Unvan):": kurum.gerceklestirme_gorevlisi_unvan,
                "Satın Alma 1 (Ad):": kurum.satin_alma_1_ad,
                "Satın Alma 1 (Unvan):": kurum.satin_alma_1_unvan,
                "Satın Alma 1 (TC):": kurum.satin_alma_1_tc,
                "Satın Alma 2 (Ad):": kurum.satin_alma_2_ad,
                "Satın Alma 2 (Unvan):": kurum.satin_alma_2_unvan,
                "Satın Alma 2 (TC):": kurum.satin_alma_2_tc,
                "Satın Alma 3 (Ad):": kurum.satin_alma_3_ad,
                "Satın Alma 3 (Unvan):": kurum.satin_alma_3_unvan,
                "Satın Alma 3 (TC):": kurum.satin_alma_3_tc,
                "Muayene 1 (Ad):": kurum.muayene_1_ad,
                "Muayene 1 (Unvan):": kurum.muayene_1_unvan,
                "Muayene 1 (TC):": kurum.muayene_1_tc,
                "Muayene 2 (Ad):": kurum.muayene_2_ad,
                "Muayene 2 (Unvan):": kurum.muayene_2_unvan,
                "Muayene 2 (TC):": kurum.muayene_2_tc,
                "Muayene 3 (Ad):": kurum.muayene_3_ad,
                "Muayene 3 (Unvan):": kurum.muayene_3_unvan,
                "Muayene 3 (TC):": kurum.muayene_3_tc,
            }
            self.ust_makam_var.set(kurum.ust_makam_turu if kurum.ust_makam_turu in ("il", "ilce") else "ilce")
            for label, value in entry_map.items():
                if label in self.entryler:
                    self._entry_deger_yaz(label, value)

    def kaydet(self) -> bool:
        # ... (kaydetme kodları aynı kalıyor) ...
        try:
            zorunlu_alanlar = [
                "Kurum Adı:", "İl:", "İlçe:", "DETSIS No (Resmi Yazışma Kodu):",
                "Harcama Yetkilisi (Ad):", "Harcama Yetkilisi (Unvan):",
                "Gerçekleştirme Görevlisi (Ad):", "Gerçekleştirme Görevlisi (Unvan):",
            ]
            for label in zorunlu_alanlar:
                if not self._entry_degeri(label):
                    messagebox.showwarning("Uyarı", f"Lütfen '{label}' alanını doldurun!")
                    return False

            kurum = Kurum(
                kurum_adi=self._entry_degeri("Kurum Adı:"),
                il=self._entry_degeri("İl:"),
                ilce=self._entry_degeri("İlçe:"),
                harcama_yetkilisi_ad=self._entry_degeri("Harcama Yetkilisi (Ad):"),
                harcama_yetkilisi_unvan=self._entry_degeri("Harcama Yetkilisi (Unvan):"),
                gerceklestirme_gorevlisi_ad=self._entry_degeri("Gerçekleştirme Görevlisi (Ad):"),
                gerceklestirme_gorevlisi_unvan=self._entry_degeri("Gerçekleştirme Görevlisi (Unvan):"),
                detsis_no=self._entry_degeri("DETSIS No (Resmi Yazışma Kodu):"),
                ust_makam_turu=self.ust_makam_var.get(),
                satin_alma_1_ad=self._entry_degeri("Satın Alma 1 (Ad):"),
                satin_alma_1_unvan=self._entry_degeri("Satın Alma 1 (Unvan):"),
                satin_alma_1_tc=self._entry_degeri("Satın Alma 1 (TC):"),
                satin_alma_2_ad=self._entry_degeri("Satın Alma 2 (Ad):"),
                satin_alma_2_unvan=self._entry_degeri("Satın Alma 2 (Unvan):"),
                satin_alma_2_tc=self._entry_degeri("Satın Alma 2 (TC):"),
                satin_alma_3_ad=self._entry_degeri("Satın Alma 3 (Ad):"),
                satin_alma_3_unvan=self._entry_degeri("Satın Alma 3 (Unvan):"),
                satin_alma_3_tc=self._entry_degeri("Satın Alma 3 (TC):"),
                muayene_1_ad=self._entry_degeri("Muayene 1 (Ad):"),
                muayene_1_unvan=self._entry_degeri("Muayene 1 (Unvan):"),
                muayene_1_tc=self._entry_degeri("Muayene 1 (TC):"),
                muayene_2_ad=self._entry_degeri("Muayene 2 (Ad):"),
                muayene_2_unvan=self._entry_degeri("Muayene 2 (Unvan):"),
                muayene_2_tc=self._entry_degeri("Muayene 2 (TC):"),
                muayene_3_ad=self._entry_degeri("Muayene 3 (Ad):"),
                muayene_3_unvan=self._entry_degeri("Muayene 3 (Unvan):"),
                muayene_3_tc=self._entry_degeri("Muayene 3 (TC):"),
            )

            self.db.kurum_kaydet(kurum)

            if self.ana_pencere:
                self.ana_pencere.durum_guncelle("🟢 Kurum bilgileri kaydedildi ✅")

            messagebox.showinfo("Başarılı", "✅ Kurum bilgileri kaydedildi!")
            return True

        except Exception as e:
            messagebox.showerror("Hata", f"❌ Kayıt hatası: {str(e)}")
            return False

    def temizle(self):
        for label, entry in self.entryler.items():
            entry.delete(0, tk.END)
            self._placeholder_goster(label)
        messagebox.showinfo("Bilgi", "✅ Alanlar temizlendi, yeni değerler girebilirsiniz.")