# gui/rehber.py
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from versiyon import VERSIYON

class RehberPenceresi:
    """Doğrudan temin süreci rehber penceresi"""
    
    def __init__(self, parent):
        self.pencere = tk.Toplevel(parent)
        self.pencere.title(f"📖 Doğrudan Temin Süreç Rehberi - {VERSIYON}")
        self.pencere.geometry("950x800")
        self.pencere.minsize(850, 600)
        self.pencere.transient(parent)
        self.pencere.focus_force()
        
        self._olustur()
    
    def _olustur(self):
        main_frame = ttk.Frame(self.pencere, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # === BAŞLIK ===
        baslik_frame = ttk.Frame(main_frame)
        baslik_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            baslik_frame,
            text="📖 DOĞRUDAN TEMİN SÜREÇ REHBERİ",
            font=("Segoe UI", 18, "bold"),
            bootstyle="primary"
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            baslik_frame,
            text="✖ Kapat",
            command=self.pencere.destroy,
            bootstyle="danger-outline"
        ).pack(side=tk.RIGHT)
        
        ttk.Label(
            main_frame,
            text=f"4734 sayılı Kamu İhale Kanunu'nun 22. maddesi (d) bendi kapsamında doğrudan temin süreci ve program kullanım kılavuzu ({VERSIYON})",
            font=("Segoe UI", 10),
            bootstyle="secondary"
        ).pack(anchor='w', pady=(0, 10))
        
        # === KAYDIRILABİLİR ALAN ===
        self.canvas = tk.Canvas(main_frame, bg='#F8F9FA', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Fare tekerleği desteği
        self.pencere.bind("<MouseWheel>", self._on_mousewheel)
        self.pencere.bind("<Button-4>", self._on_mousewheel_linux)
        self.pencere.bind("<Button-5>", self._on_mousewheel_linux)
        
        # === İÇERİK ===
        self._icerik_olustur(self.scrollable_frame)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_mousewheel(self, event):
        if self.canvas and self.canvas.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux(self, event):
        if self.canvas and self.canvas.winfo_exists():
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def _icerik_olustur(self, parent):
        row = 0
        
        def baslik_ekle(text, color="primary", pad=(0, 5)):
            nonlocal row
            ttk.Label(
                parent,
                text=text,
                font=("Segoe UI", 13, "bold"),
                bootstyle=color
            ).grid(row=row, column=0, sticky='w', pady=pad, padx=10)
            row += 1

        def metin_ekle(text, font=("Segoe UI", 10), color="default", pad=(0, 10)):
            nonlocal row
            lbl = ttk.Label(
                parent,
                text=text,
                font=font,
                wraplength=850,
                justify='left'
            )
            if color != "default":
                lbl.configure(bootstyle=color)
            lbl.grid(row=row, column=0, sticky='w', pady=pad, padx=15)
            row += 1

        def ayirici_ekle():
            nonlocal row
            ttk.Separator(parent, orient='horizontal').grid(row=row, column=0, sticky='ew', pady=15, padx=10)
            row += 1

        # ============================================================
        # GİRİŞ
        # ============================================================
        baslik_ekle("📌 GİRİŞ")
        metin_ekle(
            "Doğrudan Temin, 4734 sayılı Kamu İhale Kanunu'nun 22. maddesi (d) bendi uyarınca, "
            "belirli bir bedelin altındaki mal ve hizmet alımlarında uygulanan bir yöntemdir.\n\n"
            "Bu modül, okul/kurumların doğrudan temin sürecini 10 adımda eksiksiz yönetmek, "
            "resmi evrakları otomatik oluşturmak ve arşivlemek için geliştirilmiştir."
        )
        ayirici_ekle()

        # ============================================================
        # ADIMLAR
        # ============================================================
        baslik_ekle("🏛️ ADIM 1: KURUM BİLGİLERİ")
        metin_ekle(
            "📌 Okul/kurum bilgilerini girin.\n"
            "📌 DETSIS No (Resmi Yazışma Kodu) mutlaka girilmelidir (Word belgelerinin 'Sayı' kısmında kullanılır).\n"
            "📌 Harcama Yetkilisi, Gerçekleştirme Görevlisi, Satın Alma ve Muayene Kabul komisyon üyelerini girin."
        )
        ayirici_ekle()

        baslik_ekle("📂 ADIM 2: ALIM YÖNETİMİ (V4.0.0 YENİLİKLERİ)")
        metin_ekle(
            "📌 'Yeni Alım Başlat' ile yeni bir dosya oluşturun.\n"
            "📌 🆕 Alım Türü: Artık 3 seçenek var: 'Mal Alımı', 'Hizmet Alımı' ve 'Bakım / Onarım'.\n"
            "📌 🆕 Bütçe Yılı: Yıl seçimi yerine, içinde bulunduğumuz yılın 2 yıl öncesi ve 2 yıl sonrasını içeren açılır bir takvim menüsü eklendi.\n"
            "📌 🆕 Otomatik Doldurma: Alım türünü seçtiğiniz an, 'İşin Tanımı' (örn: MENKUL MAL, GAYRİMADDİ HAK ALIM, BAKIM VE ONARIM GİDERLERİ) kendiliğinden yazılır.\n"
            "📌 🆕 Akıllı Bütçe Kodları: Seçtiğiniz alım türüne ve 'İşin Niteliği'ne göre Bütçe Tertibi (Ekonomik Kod) açılır listeden otomatik atanır. Eğer listede yoksa 'Diğer' seçeneği ile kendiniz manuel girebilirsiniz.\n"
            "📌 Her alım kendi veritabanına ve kendi klasörüne sahiptir.\n"
            "📌 '📊 İstatistikler' butonu ile geçmiş alım sayılarını ve firma dağılımlarını grafiksel olarak görüntüleyebilirsiniz."
        )
        ayirici_ekle()

        baslik_ekle("📦 ADIM 3: İHTİYAÇ LİSTESİ")
        metin_ekle(
            "📌 Alınacak malzemeleri (Ad, Miktar, Birim) girin.\n"
            "📌 OKAS Kodu arama: Malzemenin yanındaki 🔍 butonuna basarak CPV/OKAS kodunu ismine göre arayıp seçebilirsiniz.\n"
            "📌 Excel Entegrasyonu: 'Şablon İndir' ile standart bir Excel dosyası alıp doldurabilir, 'Excel'den Yükle' ile listeye tek tıkla aktarabilirsiniz.\n"
            "📌 EBYS Onay Sayısı: Ekranın üstündeki alana girilen sayı, Word mektubunun 'Sayı' satırının sonuna otomatik eklenir."
        )
        ayirici_ekle()

        baslik_ekle("🏢 ADIM 4: FİRMA VE TEKLİF GİRİŞİ")
        metin_ekle(
            "📌 En az 2 firmadan teklif alınmalıdır.\n"
            "📌 Firma bilgilerini girin (Ünvan, Vergi No, Telefon ve Doğum Tarihi).\n"
            "📌 Her firma için tüm kalemlere birim fiyat yazın.\n"
            "📌 Fiyat kutularına yazdığınız sayılar, kutudan çıktığınızda otomatik olarak 1.234,56 formatına dönüşür."
        )
        ayirici_ekle()

        baslik_ekle("💰 ADIM 5: YAKLAŞIK MALİYET")
        metin_ekle(
            "📌 Her kalem için KDV oranı girin (varsayılan %20).\n"
            "📌 Ortalama fiyat ve KDV'li toplam otomatik hesaplanır.\n"
            "📌 'HYS Raporu Oluştur' ile sisteme yüklenebilecek Excel dosyasını indirin.\n"
            "📌 'Teklif Mektubu Oluştur' ile firmalara gönderilecek resmi evrakları hazırlayın (Seçtiğiniz Alım Türüne göre metin otomatik değişir)."
        )
        ayirici_ekle()

        baslik_ekle("📝 ADIM 6: GEREKÇE FORMU")
        metin_ekle(
            "📌 DMO'dan temin edilememe gerekçesini (Katalogda bulunmaması, Teknik yetersizlik, Fiyat avantajsızlığı, Teslimat süresi) işaretleyin.\n"
            "📌 Tasarruf tedbirleri kapsamında acil ve zorunlu alım gerekçesini yazın.\n"
            "📌 Yaklaşık Maliyet'teki en güncel KDV oranlarını kullanarak formu oluşturur ve 'Mal ve Hizmet Alımı Gerekçe Formu'nu Word olarak indirir."
        )
        ayirici_ekle()

        baslik_ekle("📊 ADIM 7: TEKLİF KARŞILAŞTIRMA")
        metin_ekle(
            "📌 Firmalardan gelen resmi teklif fiyatlarını sisteme girin.\n"
            "📌 Her firma sütununun yanında 'Toplam Fiyat (KDV'li)' hesaplanır.\n"
            "📌 En uygun teklif otomatik olarak belirlenir. 'Piyasa Fiyat Araştırma Tutanağı' ve 'Karar Tutanağı' oluşturabilirsiniz."
        )
        ayirici_ekle()

        baslik_ekle("✅ ADIM 8: MUAYENE KABUL")
        metin_ekle(
            "📌 Bu ekran, Alım Yönetiminde seçtiğiniz türe göre değişir:\n"
            "  🟢 MAL ALIMI: Teslim alınan ürünlerin kabul ve red miktarlarını girip 'Muayene ve Kabul Tutanağı' oluşturursunuz.\n"
            "  🔵 HİZMET ALIMI: Sözleşme tarihi, bedeli, iş süresi, geçici kabul tarihleri ve komisyon notlarını doldurup 'Hizmet İşleri Kabul Tutanağı' (Standart Form KİK057.0/H) oluşturursunuz."
        )
        ayirici_ekle()

        baslik_ekle("📤 ADIM 9: EKAP İŞLEMLERİ")
        metin_ekle(
            "📌 İki farklı yöntemle EKAP Excel dosyası hazırlayabilirsiniz:\n"
            "  1. YÖNTEM (Sıfırdan): Programın kendi oluşturduğu XML formatındaki .xls dosyasını üretir.\n"
            "  2. YÖNTEM (Akıllı Yöntem): EKAP'a girip istekliyi seçtikten sonra indirdiğiniz orijinal Excel şablonunu programa verirsiniz. Program sadece 'Sheet1' kısmını doldurur ve size geri verir (İndirilen şablonun yapısını bozmaz)."
        )
        ayirici_ekle()

        baslik_ekle("🗂️ ADIM 10: BELGE KONTROL")
        metin_ekle(
            "📌 Raporların ve yüklediğiniz belgelerin (Fatura, VIF, Harcama Talimatı vb.) durumunu buradan kontrol edin.\n"
            "📌 Ön Mali Kontrol Listesi (EK-32)'ni doldurun.\n"
            "📌 Vadesi Geçmiş Borç Durumu sorgulamasını işaretleyin.\n"
            "📌 Tüm evraklar tamamlandığında 'ÖDEME TAMAMLANDI' butonuna tıklayarak dosyayı 10/10 kapatın.\n"
            "📌 '📦 DOSYAYI YEDEKLE (ZIP)' butonu ile tüm evrakları ve veritabanını tek bir ZIP dosyasına sıkıştırabilirsiniz."
        )
        ayirici_ekle()

        # ============================================================
        # KRİTİK SÜREÇ TAKİBİ
        # ============================================================
        baslik_ekle("⏰ KRİTİK SÜREÇ TAKİBİ (YASAL ZORUNLULUKLAR)", color="danger")
        
        kritik_maddeler = [
            "1. İhtiyaç Listesi kurum onayını müteakiben aynı gün ya da ertesi gün Yaklaşık Maliyet belirleme süreci başlatılmalıdır.",
            "2. Yaklaşık Maliyet Cetveli tarihi en erken mektupların dağıtıldığı ertesi gün olmalıdır.",
            "3. Yaklaşık Maliyet belirlendikten sonra HYS sisteminden ilgili harcama işlemi başlatılmalı ve 'Harcama Talimatı Onay Belgesi' alınmalıdır. Bu süreçte program içinde oluşturulan 'MYS_Yaklasik_Maliyet_X.xlsx' dosyası kullanılarak HYS'de yaklaşık maliyetin otomatik olarak girilmesi sağlanabilir.",
            "4. Piyasa fiyat araştırması teklif mektupları Harcama Talimatı Onay belgesi ile aynı tarih ya da ertesi gün olabilir.",
            "5. Piyasa fiyat araştırması tutanağı ve Karar Tutanağı tarihleri teklif mektuplarının ertesi günü olmalıdır.",
            "6. Muayene Kabul Tutanağı tarihi, Piyasa Fiyat Araştırması Tutanağı ve Karar Tutanağı tarihlerinin ertesi günü olmalıdır.",
            "7. Firma fatura tarihi muayene kabul tutanağı tarihi ile aynı gün olabilir. E-Arşiv fatura kullanılacaksa mutlaka firma tarafından kaşeli ve imzalı olmalıdır. Ayrıca E-Arşiv fatura mutlaka sistemden kontrol edilmeli ve üzerine 'Sistemden kontrol edilmiştir' notu düşülerek taranmalı HYS'ye öyle yüklenmelidir.",
            "8. TKYS işlemleri muayene kabulden sonra faturanın kesildiği tarihte başlamalıdır.",
            "9. Vadesi Geçmiş Borç Durumu Belgesi ödeme süreci de dikkate alınarak süresi geçmemiş olmalıdır ve harcama birimi tarafından sistem üzerinden doğrulaması yapılmış ve üzerine not düşülmüş olarak taranıp HYS sistemine yüklenmelidir.",
            "10. Doğrudan Temin Kayıt Belgesi bazı muhasebe müdürlükleri tarafından ödeme evrakları arasında istendiğinden ödeme aşamasında EKAP girişi yapılarak HYS sistemine yüklenmelidir.",
            "11. Her ne kadar 200.000 TL altındaki alımlarda Ön Mali Kontrol Listesi istenmese de bazı muhasebe müdürlükleri bunu da istemektedir. Bu nedenle bağlı bulunulan muhasebe müdürlüğü ile istişare yapılarak ödeme işlemleri aşamasında imzalanıp taranarak sisteme yüklenmelidir.",
            "12. Sistemden en son alınacak olan ödeme emri de dahil olmak üzere diğer tüm yüklenmesi gerek evraklar program aracılığı ile ilgili klasöre yüklenerek bir arada tek klasör olarak arşivlemesi yapılabilmektedir."
        ]
        
        for madde in kritik_maddeler:
            metin_ekle(madde, font=("Segoe UI", 9), pad=(0, 4))
        
        ayirici_ekle()

        # ============================================================
        # SON
        # ============================================================
        baslik_ekle("✅ SÜREÇ TAMAMLANDI!", color="success")
        metin_ekle(
            "Tüm adımlar tamamlandığında alım dosyanız 10/10 olarak kapanır.\n"
            "Tüm belgeler ve raporlar seçtiğiniz alım klasöründe saklanır.\n"
            "İstediğiniz zaman ZIP yedeği alarak dosyalarınızı güvenceye alabilirsiniz.",
            color="success"
        )