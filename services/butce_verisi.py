# services/butce_verisi.py

# Her alım türü için varsayılan İşin Tanımı
ISIN_TANIMLARI = {
    "mal": "TÜKETİME YÖNELİK MAL VE MALZEME ALIMLARI",
    "hizmet": "HİZMET ALIMLARI",
    "bakim": "MENKUL MAL, GAYRİMADDİ HAK ALIM, BAKIM VE ONARIM GİDERLERİ"
}

# Alım türüne göre ekonomik kodlar ve isimleri
BUTCE_KODLARI = {
    "mal": [
        ("Kırtasiye Alımları", "03.02.10.01"),
        ("Büro Malzemesi Alımları", "03.02.10.02"),
        ("Diğer Kırtasiye, Yayın, Baskı ve Büro Malzemesi Alımları", "03.02.10.90"),
        ("Temizlik Malzemesi Alımları", "03.02.20.02"),
        ("Yakacak Alımları", "03.02.30.01"),
        ("Taşıtlar İçin Yakıt ve Yağ Alımları", "03.02.30.02"),
        ("Elektrik Alımları", "03.02.30.03"),
        ("Genel Amaçlı Akaryakıt ve Yağ Alımları", "03.02.30.04"),
        ("Yiyecek Alımları", "03.02.40.01"),
        ("İçecek Alımları", "03.02.40.02"),
        ("Diğer Yiyecek, İçecek ve Yem Alımları", "03.02.40.90"),
        ("Giyecek Alımları", "03.02.50.01"),
        ("Spor Malzemeleri Alımları", "03.02.50.02"),
        ("Tören Malzemeleri Alımları", "03.02.50.03"),
        ("Bando Malzemeleri Alımları", "03.02.50.04"),
        ("Laboratuvar Malzemesi ile Kimyevi ve Temrinlik Malzeme Alımları", "03.02.60.01")
    ],
    "hizmet": [
        ("İş Sağlığı ve Güvenliği Hizmeti Alım Giderleri", "03.05.10.07"),
        ("Yemek Hizmeti Alım Giderleri", "03.05.10.09"),
        ("Taşıma Yoluyla Eğitime Erişim Giderleri", "03.05.10.10"),
        ("Posta ve Telgraf Giderleri", "03.05.20.01"),
        ("Telefon Abonelik ve Kullanım Ücretleri", "03.05.20.02"),
        ("İnternet Erişimi Giderleri", "03.05.20.03"),
        ("Bilgiye Abonelik Giderleri", "03.05.20.07"),
        ("Taşıtların Sigorta Giderleri", "03.05.40.02")
    ],
    "bakim": [
        ("Büro ve İşyeri Mal ve Malzeme Alımları", "03.07.10.01"),
        ("Büro ve İşyeri Makine ve Techizat Alımları", "03.07.10.02"),
        ("Avadanlık ve Yedek Parça Alımları", "03.07.10.03"),
        ("Yangından Korunma Malzemeleri Alımları", "03.07.10.04"),
        ("Taşıtlar İçin Lastik Alımları", "03.07.10.05"),
        ("Taşıtlar İçin Yedek Parça Alımları", "03.07.10.06"),
        ("Diğer Dayanıklı Mal ve Malzeme Alımları", "03.07.10.90"),
        ("Tefrişat Bakım ve Onarım Giderleri", "03.07.30.01"),
        ("Makine Teçhizat Bakım ve Onarım Giderleri", "03.07.30.02"),
        ("Taşıt Bakım ve Onarım Giderleri", "03.07.30.03"),
        ("Diğer Bakım ve Onarım Giderleri", "03.07.30.90"),
        ("Büro Bakım ve Onarımı Giderleri", "03.08.10.01"),
        ("Eğitim ve Öğretim Tesisi Bakım ve Onarımı Giderleri", "03.08.10.02"),
        ("Atölye ve Tesis Binaları Bakım ve Onarımı Giderleri", "03.08.10.04"),
        ("Diğer Hizmet Binası Bakım ve Onarımı Giderleri", "03.08.10.90"),
        ("Lojman Bakım ve Onarımı Giderleri", "03.08.20.01"),
        ("Sosyal Tesis Bakım ve Onarımı Giderleri", "03.08.30.01")
    ]
}