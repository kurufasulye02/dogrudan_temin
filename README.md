# 🏫 Doğrudan Temin Modülü (V4.0.0)

4734 sayılı Kamu İhale Kanunu'nun **22/d maddesi** kapsamında, okullar ve kamu kurumları için geliştirilmiş, uçtan uca **Mal ve Hizmet Alımı** süreç yönetim yazılımıdır.

Bu program; ihtiyaç listesinin oluşturulmasından başlayarak, piyasa fiyat araştırması, yaklaşık maliyet hesaplama, gerekçe formu hazırlama, teklif karşılaştırma, muayene kabul işlemleri ve EKAP evraklarının oluşturulmasına kadar tüm süreci tek bir arayüzden yönetir.

---

## ✨ Özellikler

*   **10 Adımlı Süreç Yönetimi:** Kurum bilgilerinden belge kapanışına kadar tüm adımlar sol menüden takip edilebilir.
*   **Mal / Hizmet / Bakım-Onarım Ayrımı:** Alım türüne göre (V4.0.0 ile gelen yeni özellik) bütçe kodları ve rapor şablonları otomatik şekillenir.
*   **Otomatik Bütçe Tertibi:** Seçilen "İşin Niteliği"ne göre MEB'in resmi bütçe kodları (03.02.10.01 vb.) açılır listeden otomatik atanır.
*   **OKAS/CPV Kodu Arama:** İhtiyaç listesine eklenen ürünler için OKAS kodları program içinden aranıp seçilebilir.
*   **Excel Entegrasyonu:** İhtiyaç listeleri Excel şablonu ile toplu yüklenebilir veya Excel'e aktarılabilir.
*   **KDV'li Maliyet Hesaplama:** Yaklaşık maliyet ve teklif karşılaştırma ekranlarında KDV oranları kalem bazında hesaplanır.
*   **Resmi Evrak Üretimi:** İhtiyaç listesi, teklif mektubu, karar tutanağı, piyasa fiyat tutanağı, gerekçe formu ve muayene kabul tutanakları (Word/Excel) otomatik üretilir.
*   **EKAP Excel Desteği:** İki farklı yöntemle EKAP'a yüklenecek Excel dosyası hazırlanır:
    1. Sıfırdan `.xls` şablonu üretimi.
    2. EKAP'tan indirilen orijinal şablonun program tarafından doldurulması.
*   **Ön Mali Kontrol (EK-32):** 48 maddelik kontrol listesi entegre edilmiştir.
*   **Arşivleme ve ZIP Yedekleme:** Her alım kendi klasöründe ve kendi veritabanında saklanır. Süreç sonunda tüm evraklar tek tıkla `.zip` olarak yedeklenebilir.
*   **Grafiksel İstatistikler:** Geçmiş yıllara ait alımlar ve firma dağılımları grafiklerle görüntülenebilir.

---

## 🚀 Kurulum (Son Kullanıcı İçin)

Programı kullanmak için bilgisayarınızda **Python veya herhangi bir kütüphane kurulu olmasına gerek yoktur.**

1.  Sayfanın sağ tarafındaki **Releases (Sürümler)** bölümüne gidin.
2.  En son sürümün altındaki `DogrudanTemin_V4.0.0.exe` dosyasını indirin.
3.  Bilgisayarınızda (örneğin Masaüstü'nde) yeni bir klasör açın.
4.  İndirdiğiniz `.exe` dosyasını bu klasöre taşıyın ve çift tıklayarak çalıştırın.
5.  İlk çalıştırmada program bulunduğu klasörde otomatik olarak veritabanı dosyalarını (`.db`) oluşturacaktır.

> ⚠️ **Önemli:** Programın çalışması sırasında oluşan `dogrudan_temin.db`, `alim_katalog.db` dosyalarını ve `logs` klasörünü silmeyiniz. Bu dosyalar veri güvenliğiniz için hayati önem taşır.

---

## 💻 Geliştirici Kurulumu (Kaynak Koddan Çalıştırma)

Projeyi kendi bilgisayarınızda geliştirmek veya incelemek isterseniz:

### Gereksinimler
*   Python 3.11 (önerilen)
*   Git

### Adımlar

# 1. Depoyu klonlayın
git clone https://github.com/kurufasulye02/dogrudan-temin.git
cd dogrudan-temin

# 2. Sanal ortam oluşturun ve aktifleştirin
python -m venv sanal_ortam
# Windows için:
.\sanal_ortam\Scripts\activate
# Mac/Linux için:
source sanal_ortam/bin/activate

# 3. Gerekli kütüphaneleri yükleyin
pip install -r requirements.txt

# 4. Programı çalıştırın
python main.py
EXE Derleme
Programı tek bir .exe dosyası haline getirmek için (terminalde sanal ortam aktifken):


pyinstaller --noconfirm --windowed --onefile --icon="logo.ico" --add-data "logo.ico;." --add-data "services/ekap_sablon.xls;services" --collect-all docx --collect-all openpyxl --collect-all ttkbootstrap --collect-all tkcalendar --collect-all matplotlib --hidden-import lxml --hidden-import lxml.etree --name "DogrudanTemin_V4.0.0" main.py

📁 Proje Yapısı

dogrudan-temin/
│
├── database/           # SQLite bağlantı ve tablo yönetimi (Migration)
├── gui/                # Tkinter arayüz dosyaları (Ekranlar)
├── models/             # Veri modelleri (dataclass)
├── services/           # İş mantığı, veritabanı ve raporlama servisleri
├── utils/              # Yardımcı fonksiyonlar (logger, ui_helpers vb.)
├── main.py             # Uygulama giriş noktası
├── versiyon.py         # Sürüm numarası yönetimi
├── requirements.txt    # Gerekli Python kütüphaneleri
├── logo.ico            # Uygulama ikonu
└── README.md           # Bu dosya

🤝 Katkıda Bulunma
Bu projeyi fork'layın (Fork butonu).

Yeni bir özellik dalı oluşturun (git checkout -b ozellik/YeniOzellik).

Değişikliklerinizi commit edin (git commit -m 'Yeni özellik eklendi').

Dalınızı push edin (git push origin ozellik/YeniOzellik).

Bir Pull Request (PR) açın.

📄 Lisans
Bu proje MIT Lisansı altında lisanslanmıştır. Daha fazla bilgi için LICENSE dosyasına bakınız.

📞 İletişim
Herhangi bir hata, öneri veya yeni özellik talebiniz için lütfen Issues sekmesini kullanın.

Not: Bu yazılım, kamu kurumlarında doğrudan temin süreçlerini hızlandırmak ve evrak hatalarını minimize etmek amacıyla geliştirilmiştir. Resmi işlemlerinizde nihai sorumluluk kullanıcıya aittir.