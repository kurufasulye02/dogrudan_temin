-- Doğrudan Temin uygulaması - merkezi SQLite şeması.
-- CREATE IF NOT EXISTS mevcut veriyi korur; eski DB'ler db_manager tarafından migrate edilir.

CREATE TABLE IF NOT EXISTS kurum (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kurum_adi TEXT, il TEXT, ilce TEXT,
    butce_tertibi TEXT, odeneck_miktari REAL,
    isin_tanimi TEXT, isin_niteligi TEXT,
    harcama_yetkilisi_ad TEXT, harcama_yetkilisi_unvan TEXT,
    gerceklestirme_gorevlisi_ad TEXT, gerceklestirme_gorevlisi_unvan TEXT,
    detsis_no TEXT,
    ust_makam_turu TEXT DEFAULT 'ilce',
    satin_alma_1_ad TEXT, satin_alma_1_unvan TEXT,
    satin_alma_2_ad TEXT, satin_alma_2_unvan TEXT,
    satin_alma_3_ad TEXT, satin_alma_3_unvan TEXT,
    muayene_1_ad TEXT, muayene_1_unvan TEXT,
    muayene_2_ad TEXT, muayene_2_unvan TEXT,
    muayene_3_ad TEXT, muayene_3_unvan TEXT
);

CREATE TABLE IF NOT EXISTS alimlar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alim_adi TEXT NOT NULL,
    yil INTEGER NOT NULL,
    kurum_id INTEGER,
    durum TEXT DEFAULT 'hazirlik',
    toplam_tutar REAL DEFAULT 0,
    odeneck_kontrol TEXT DEFAULT 'Beklemede',
    alim_no TEXT,
    olusturma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    tamamlanma_tarihi DATETIME,
    dosya_klasoru TEXT,
    odeme_tamamlandi INTEGER DEFAULT 0,
    odeme_tamamlanma_tarihi DATETIME,
    FOREIGN KEY (kurum_id) REFERENCES kurum(id)
);

CREATE TABLE IF NOT EXISTS ihtiyac_listesi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alim_id INTEGER NOT NULL,
    sira_no INTEGER,
    malzeme_adi TEXT NOT NULL,
    miktar REAL NOT NULL,
    birim TEXT NOT NULL,
    FOREIGN KEY (alim_id) REFERENCES alimlar(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS firmalar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unvan TEXT NOT NULL,
    vergi_no TEXT UNIQUE NOT NULL,
    adres TEXT,
    telefon TEXT,
    yetkili TEXT
);

CREATE TABLE IF NOT EXISTS teklifler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alim_id INTEGER NOT NULL,
    firma_id INTEGER NOT NULL,
    ihtiyac_id INTEGER NOT NULL,
    birim_fiyat REAL NOT NULL,
    kdv_orani REAL DEFAULT 20,
    toplam_fiyat REAL,
    teklif_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alim_id) REFERENCES alimlar(id) ON DELETE CASCADE,
    FOREIGN KEY (firma_id) REFERENCES firmalar(id),
    FOREIGN KEY (ihtiyac_id) REFERENCES ihtiyac_listesi(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS resmi_teklifler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alim_id INTEGER NOT NULL,
    firma_id INTEGER NOT NULL,
    ihtiyac_id INTEGER NOT NULL,
    birim_fiyat REAL NOT NULL,
    kdv_orani REAL DEFAULT 20,
    toplam_fiyat REAL,
    teklif_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alim_id) REFERENCES alimlar(id) ON DELETE CASCADE,
    FOREIGN KEY (firma_id) REFERENCES firmalar(id),
    FOREIGN KEY (ihtiyac_id) REFERENCES ihtiyac_listesi(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS yaklasik_maliyet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alim_id INTEGER NOT NULL,
    malzeme_adi TEXT NOT NULL,
    kdv_orani REAL DEFAULT 20,
    FOREIGN KEY (alim_id) REFERENCES alimlar(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS degerlendirme (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alim_id INTEGER NOT NULL,
    kazanan_firma_id INTEGER NOT NULL,
    kazanan_toplam_tutar REAL,
    karar_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
    karar_no TEXT,
    FOREIGN KEY (alim_id) REFERENCES alimlar(id) ON DELETE CASCADE,
    FOREIGN KEY (kazanan_firma_id) REFERENCES firmalar(id)
);

CREATE TABLE IF NOT EXISTS muayene_kabul (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alim_id INTEGER NOT NULL,
    firma_id INTEGER NOT NULL,
    teslim_tarihi DATETIME,
    kabul_edilen_miktar REAL,
    red_edilen_miktar REAL,
    aciklama TEXT,
    FOREIGN KEY (alim_id) REFERENCES alimlar(id) ON DELETE CASCADE,
    FOREIGN KEY (firma_id) REFERENCES firmalar(id)
);

CREATE TABLE IF NOT EXISTS muayene_kabul_detay (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alim_id INTEGER NOT NULL,
    ihtiyac_id INTEGER NOT NULL,
    kabul_miktar REAL DEFAULT 0,
    red_miktar REAL DEFAULT 0,
    FOREIGN KEY (alim_id) REFERENCES alimlar(id) ON DELETE CASCADE,
    FOREIGN KEY (ihtiyac_id) REFERENCES ihtiyac_listesi(id) ON DELETE CASCADE
);

-- Ön Mali Kontrol Listesi (EK-32) cevapları. satir_no, on_mali_kontrol_maddeleri.py
-- içindeki 48 maddenin sabit pozisyon anahtarıdır (sira_no metni tekil olmadığından
-- - örn. "3" iki farklı satırda geçtiğinden - pozisyon kullanılır).
CREATE TABLE IF NOT EXISTS on_mali_kontrol (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alim_id INTEGER NOT NULL,
    satir_no INTEGER NOT NULL,
    secim TEXT NOT NULL,
    FOREIGN KEY (alim_id) REFERENCES alimlar(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_alimlar_alim_adi ON alimlar(alim_adi);
CREATE INDEX IF NOT EXISTS idx_alimlar_yil ON alimlar(yil);
CREATE INDEX IF NOT EXISTS idx_ihtiyac_alim_id ON ihtiyac_listesi(alim_id);
CREATE INDEX IF NOT EXISTS idx_teklifler_alim_id ON teklifler(alim_id);
CREATE INDEX IF NOT EXISTS idx_teklifler_firma_id ON teklifler(firma_id);
CREATE INDEX IF NOT EXISTS idx_resmi_teklifler_alim_id ON resmi_teklifler(alim_id);
CREATE INDEX IF NOT EXISTS idx_firmalar_vergi_no ON firmalar(vergi_no);
CREATE INDEX IF NOT EXISTS idx_degerlendirme_alim_id ON degerlendirme(alim_id);
CREATE INDEX IF NOT EXISTS idx_yaklasik_maliyet_alim_id ON yaklasik_maliyet(alim_id);
CREATE INDEX IF NOT EXISTS idx_muayene_kabul_alim_id ON muayene_kabul(alim_id);
CREATE INDEX IF NOT EXISTS idx_muayene_kabul_detay_alim_id ON muayene_kabul_detay(alim_id);
CREATE INDEX IF NOT EXISTS idx_on_mali_kontrol_alim_id ON on_mali_kontrol(alim_id);
