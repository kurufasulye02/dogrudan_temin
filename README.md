# 🏫 Doğrudan Temin Modülü (V4.0.0)

4734 sayılı Kamu İhale Kanunu'nun **22/d maddesi** kapsamında, okullar ve kamu kurumları için geliştirilmiş, uçtan uca **Mal, Hizmet ve Bakım-Onarım Alımı** süreç yönetim yazılımıdır.

Bu program; ihtiyaç listesinin oluşturulmasından başlayarak, piyasa fiyat araştırması, yaklaşık maliyet hesaplama, gerekçe formu hazırlama, teklif karşılaştırma, muayene kabul işlemleri ve EKAP evraklarının oluşturulmasına kadar tüm süreci tek bir arayüzden yönetir.

---

## ✨ Özellikler

*   **10 Adımlı Süreç Yönetimi:** Kurum bilgilerinden belge kapanışına kadar tüm adımlar sol menüden takip edilebilir.
*   **Mal / Hizmet / Bakım-Onarım Ayrımı (V4.0.0):** Alım türüne göre bütçe kodları ve rapor şablonları otomatik şekillenir.
*   **Otomatik Bütçe Tertibi:** Seçilen "İşin Niteliği"ne göre MEB'in resmi bütçe kodları (03.02.10.01 vb.) açılır listeden otomatik atanır.
*   **OKAS/CPV Kodu Arama:** İhtiyaç listesine eklenen ürünler için OKAS kodları program içinden aranıp seçilebilir.
*   **Excel Entegrasyonu:** İhtiyaç listeleri Excel şablonu ile toplu yüklenebilir veya Excel'e aktarılabilir.
*   **KDV'li Maliyet Hesaplama:** Yaklaşık maliyet ve teklif karşılaştırma ekranlarında KDV oranları kalem bazında hesaplanır.
*   **Resmi Evrak Üretimi:** İhtiyaç listesi, teklif mektubu, karar tutanağı, piyasa fiyat tutanağı, gerekçe formu ve muayene kabul tutanakları (Word/Excel) otomatik üretilir.
*   **EKAP Excel Desteği:** İki farklı yöntemle EKAP'a yüklenecek Excel dosyası hazırlanır (Sıfırdan üretim veya EKAP'tan indirilen orijinal şablonun doldurulması).
*   **Ön Mali Kontrol (EK-32):** 48 maddelik kontrol listesi entegre edilmiştir.
*   **Arşivleme ve ZIP Yedekleme:** Her alım kendi klasöründe ve kendi veritabanında saklanır.
*   **Grafiksel İstatistikler:** Geçmiş yıllara ait alımlar ve firma dağılımları grafiklerle görüntülenebilir.

---

## 🚀 Son Kullanıcı Kurulumu (EXE ile Kullanım)

Programı kullanmak için bilgisayarınızda **Python veya herhangi bir kütüphane kurulu olmasına gerek yoktur.** Her şey tek bir `.exe` dosyası içine gömülmüştür.

### 1. İndirme
Sayfanın sağ tarafındaki **Releases (Sürümler)** bölümüne gidin. En son sürümün (V4.0.0) altında bulunan **`DogrudanTemin_V4.0.0.exe`** dosyasını indirin.

### 2. Klasör Oluşturma (ÖNEMLİ)
Bilgisayarınızda (örneğin Masaüstü'nde veya `D:\DogrudanTemin` gibi bir sürücüde) **yeni bir klasör** açın.
*   İndirdiğiniz `.exe` dosyasını bu klasörün içine taşıyın.
*   Programı doğrudan indirilenler klasöründen veya USB bellekten çalıştırmayın.
*   **Neden?** Program ilk çalıştığında bulunduğu klasörde veritabanı (`.db`) dosyalarını ve `logs` klasörünü oluşturur. Bu dosyalar programın hafızasıdır ve silinmemelidir.

### 3. Çalıştırma
`DogrudanTemin_V4.0.0.exe` dosyasına çift tıklayarak programı başlatın.
*   İlk açılışta Windows Defender veya antivirüs programı "bilinmeyen yayıncı" uyarısı verebilir. **"Daha fazla bilgi" -> "Yine de çalıştır"** diyerek izin vermeniz gerekebilir. *(Bu, PyInstaller ile üretilen tüm exe dosyalarında görülen standart bir durumdur, program virüslü değildir).*

### 4. Güncelleme Kontrolü
Program her açılışta otomatik olarak GitHub sunucularına bağlanır ve yeni bir sürüm olup olmadığını kontrol eder. Eğer yeni bir sürüm yayınlandıysa, ekranda bir uyarı çıkar ve sizi indirme sayfasına yönlendirir. Güncellemek için yeni `.exe` dosyasını indirip eskisinin üzerine yazmanız yeterlidir (Verileriniz `.db` dosyalarında olduğu için kaybolmaz).

---

## 💻 Geliştirici Kurulumu (Kaynak Koddan Çalıştırma)

Projeyi kendi bilgisayarınızda incelemek veya geliştirmek isterseniz:

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
EXE Derleme (V4.0.0)
Programı tek bir .exe dosyası haline getirmek için, tüm kütüphaneleri, ikonu ve EKAP şablonunu içine gömen şu komutu kullanın:


pyinstaller --noconfirm --windowed --onefile --icon="logo.ico" --add-data "logo.ico;." --add-data "services/ekap_sablon.xls;services" --collect-all docx --collect-all openpyxl --collect-all ttkbootstrap --collect-all tkcalendar --collect-all matplotlib --hidden-import lxml --hidden-import lxml.etree --name "DogrudanTemin_V4.0.0" main.py

📁 Proje Yapısı
text
dogrudan-temin/
│
├── database/           # SQLite bağlantı ve tablo yönetimi (Migration)
├── gui/                # Tkinter arayüz dosyaları (Ekranlar)
├── models/             # Veri modelleri (dataclass)
├── services/           # İş mantığı, veritabanı ve raporlama servisleri
│   └── ekap_sablon.xls # EKAP Excel Şablonu (Derlemeye dahildir)
├── utils/              # Yardımcı fonksiyonlar (logger, ui_helpers vb.)
├── main.py             # Uygulama giriş noktası
├── versiyon.py         # Sürüm numarası yönetimi
├── requirements.txt    # Gerekli Python kütüphaneleri
├── logo.ico            # Uygulama ikonu (Derlemeye dahildir)
└── README.md           # Bu dosya
⚠️ Önemli Uyarılar
Programın çalıştığı klasörde oluşan dogrudan_temin.db, alim_katalog.db dosyalarını ve logs klasörünü ASLA SİLMEYİN. Bu dosyalar geçmiş alımlarınızı ve ayarlarınızı saklar.

Herhangi bir hata durumunda logs klasöründeki son tarihli .txt dosyasını inceleyebilirsiniz.

Raporları (Word/Excel) oluştururken, dosya o an başka bir programda (örneğin Excel'de) açıksa program "Dosya Kilitli" uyarısı verecektir. İşlem öncesi açık dosyaları kapatınız.

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