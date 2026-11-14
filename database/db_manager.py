# database/db_manager.py
import sqlite3
import os
import sys
from pathlib import Path
from typing import Optional


class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = self._varsayilan_db_yolu()
        self.db_path = str(db_path)
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self._baglan()
        self._tablolari_olustur()

    @staticmethod
    def _varsayilan_db_yolu() -> str:
        env_path = os.getenv("DOGRUDA_TEMIN_DB")
        if env_path:
            return str(Path(env_path).expanduser().resolve())
        if getattr(sys, 'frozen', False):
            return str(Path(sys.executable).resolve().parent / "dogrudan_temin.db")
        return str(Path.cwd() / "dogrudan_temin.db")

    def _baglan(self):
        try:
            db_file = Path(self.db_path).expanduser().resolve()
            db_file.parent.mkdir(parents=True, exist_ok=True)
            self.db_path = str(db_file)
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.connection.execute("PRAGMA busy_timeout = 5000")
            self.connection.execute("PRAGMA journal_mode=WAL;")
            self.cursor = self.connection.cursor()
            print(f"✅ Veritabanı bağlantısı başarılı: {self.db_path}")
        except Exception as e:
            print(f"❌ Bağlantı hatası: {e}")
            raise

    def _tablolari_olustur(self):
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS kurum (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kurum_adi TEXT, il TEXT, ilce TEXT,
                harcama_yetkilisi_ad TEXT, harcama_yetkilisi_unvan TEXT,
                gerceklestirme_gorevlisi_ad TEXT, gerceklestirme_gorevlisi_unvan TEXT,
                detsis_no TEXT,
                ust_makam_turu TEXT DEFAULT 'ilce',
                satin_alma_1_ad TEXT, satin_alma_1_unvan TEXT, satin_alma_1_tc TEXT,
                satin_alma_2_ad TEXT, satin_alma_2_unvan TEXT, satin_alma_2_tc TEXT,
                satin_alma_3_ad TEXT, satin_alma_3_unvan TEXT, satin_alma_3_tc TEXT,
                muayene_1_ad TEXT, muayene_1_unvan TEXT, muayene_1_tc TEXT,
                muayene_2_ad TEXT, muayene_2_unvan TEXT, muayene_2_tc TEXT,
                muayene_3_ad TEXT, muayene_3_unvan TEXT, muayene_3_tc TEXT
            );

            CREATE TABLE IF NOT EXISTS alimlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alim_adi TEXT NOT NULL,
                yil INTEGER NOT NULL,
                isin_tanimi TEXT DEFAULT 'Mal Alımı',
                isin_niteligi TEXT DEFAULT '',
                butce_tertibi TEXT DEFAULT '',
                odeneck_miktari REAL DEFAULT 0,
                alim_turu TEXT DEFAULT 'mal',
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
                kurum_snapshot TEXT,
                vadesi_gecmis_borc_sorgulandi INTEGER DEFAULT 0,
                fatura_turu TEXT DEFAULT '',
                e_fatura_iliskilendirildi INTEGER DEFAULT 0,
                ebys_onay_sayisi TEXT DEFAULT '',
                FOREIGN KEY (kurum_id) REFERENCES kurum(id)
            );

            CREATE TABLE IF NOT EXISTS okas_kodlari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpv_kodu TEXT UNIQUE,
                kalem_adi TEXT,
                kalem_turu TEXT
            );

            CREATE TABLE IF NOT EXISTS ihtiyac_listesi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alim_id INTEGER NOT NULL,
                sira_no INTEGER,
                malzeme_adi TEXT NOT NULL,
                miktar REAL NOT NULL,
                birim TEXT NOT NULL,
                okas_kodu TEXT,
                FOREIGN KEY (alim_id) REFERENCES alimlar(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS firmalar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unvan TEXT NOT NULL,
                vergi_no TEXT UNIQUE NOT NULL,
                adres TEXT,
                telefon TEXT,
                dogum_tarihi TEXT DEFAULT '', -- YENİ EKLENDİ
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

            CREATE TABLE IF NOT EXISTS on_mali_kontrol (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alim_id INTEGER NOT NULL,
                satir_no INTEGER NOT NULL,
                secim TEXT NOT NULL,
                FOREIGN KEY (alim_id) REFERENCES alimlar(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS gerekce_formu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alim_id INTEGER NOT NULL UNIQUE,
                katalog_disinda INTEGER DEFAULT 0,
                teknik_yetersiz INTEGER DEFAULT 0,
                fiyat_avantajsiz INTEGER DEFAULT 0,
                teslimat_ivedi INTEGER DEFAULT 0,
                detayli_aciklama TEXT,
                acil_gerekce TEXT,
                FOREIGN KEY (alim_id) REFERENCES alimlar(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS hizmet_kabul (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alim_id INTEGER NOT NULL UNIQUE,
                sozlesme_tarihi TEXT,
                sozlesme_bedeli REAL,
                is_suresi INTEGER,
                is_bitis_tarihi TEXT,
                sure_uzatimi INTEGER DEFAULT 0,
                uzatim_dahil_bitis TEXT,
                isin_bitirildigi_tarih TEXT,
                karar_turu TEXT,
                karar_tarihi TEXT,
                kabul_baslangic TEXT,
                kabul_bitis TEXT,
                ancak_notu TEXT,
                makam_adi TEXT,
                tutanak_tarihi TEXT,
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
        """)
        self.connection.commit()
        self._eksik_kolonlari_ekle()
        self._eski_kurum_verilerini_alimlara_tasi()
        self._benzersiz_kisitlari_ekle()
        self._okas_listesini_yukle()
        print("✅ Tablolar kontrol edildi/oluşturuldu")

    def _eksik_kolonlari_ekle(self):
        """Eski DB'leri kaybetmeden günceller"""
        # Kurum tablosuna TC sütunları ekle
        mevcut = self._kolonlari_getir("kurum")
        kurum_ekleri = [
            ("satin_alma_1_tc", "TEXT DEFAULT ''"),
            ("satin_alma_2_tc", "TEXT DEFAULT ''"),
            ("satin_alma_3_tc", "TEXT DEFAULT ''"),
            ("muayene_1_tc", "TEXT DEFAULT ''"),
            ("muayene_2_tc", "TEXT DEFAULT ''"),
            ("muayene_3_tc", "TEXT DEFAULT ''"),
        ]
        for kolon, tip in kurum_ekleri:
            if kolon not in mevcut:
                self.cursor.execute(f"ALTER TABLE kurum ADD COLUMN {kolon} {tip}")

        # Alimlar tablosuna yeni sütunları ekle
        mevcut = self._kolonlari_getir("alimlar")
        alim_ekleri = [
            ("isin_tanimi", "TEXT DEFAULT 'Mal Alımı'"),
            ("isin_niteligi", "TEXT DEFAULT ''"),
            ("butce_tertibi", "TEXT DEFAULT ''"),
            ("odeneck_miktari", "REAL DEFAULT 0"),
            ("alim_turu", "TEXT DEFAULT 'mal'"),
            ("dosya_klasoru", "TEXT"),
            ("odeme_tamamlandi", "INTEGER DEFAULT 0"),
            ("odeme_tamamlanma_tarihi", "DATETIME"),
            ("kurum_snapshot", "TEXT"),
            ("vadesi_gecmis_borc_sorgulandi", "INTEGER DEFAULT 0"),
            ("fatura_turu", "TEXT DEFAULT ''"),
            ("e_fatura_iliskilendirildi", "INTEGER DEFAULT 0"),
            ("ebys_onay_sayisi", "TEXT DEFAULT ''"),
        ]
        for kolon, tip in alim_ekleri:
            if kolon not in mevcut:
                self.cursor.execute(f"ALTER TABLE alimlar ADD COLUMN {kolon} {tip}")

        # İhtiyaç listesine OKAS kodu ekle
        mevcut = self._kolonlari_getir("ihtiyac_listesi")
        if "okas_kodu" not in mevcut:
            self.cursor.execute("ALTER TABLE ihtiyac_listesi ADD COLUMN okas_kodu TEXT")
            
        self.connection.commit()
        
        # Firmalar tablosuna dogum_tarihi ekle
        mevcut_firma = self._kolonlari_getir("firmalar")
        if "dogum_tarihi" not in mevcut_firma:
            self.cursor.execute("ALTER TABLE firmalar ADD COLUMN dogum_tarihi TEXT DEFAULT ''")        

    def _eski_kurum_verilerini_alimlara_tasi(self):
        """Eski DB'lerde kurum tablosunda olan alanları alimlar tablosuna kopyalar."""
        try:
            kurum_kolonlari = self._kolonlari_getir("kurum")
            gerekli_eski = {'butce_tertibi', 'odeneck_miktari', 'isin_tanimi', 'isin_niteligi'}
            
            if not gerekli_eski.issubset(kurum_kolonlari):
                return
            
            self.cursor.execute("SELECT butce_tertibi, odeneck_miktari, isin_tanimi, isin_niteligi FROM kurum LIMIT 1")
            eski = self.cursor.fetchone()
            
            if not eski:
                return
            
            eski_butce = eski['butce_tertibi'] or ''
            eski_odeneck = eski['odeneck_miktari'] or 0
            eski_tanim = eski['isin_tanimi'] or 'Mal Alımı'
            eski_nitelik = eski['isin_niteligi'] or ''
            
            self.cursor.execute("""
                UPDATE alimlar 
                SET isin_tanimi = COALESCE(NULLIF(isin_tanimi, ''), ?),
                    isin_niteligi = COALESCE(NULLIF(isin_niteligi, ''), ?),
                    butce_tertibi = COALESCE(NULLIF(butce_tertibi, ''), ?),
                    odeneck_miktari = CASE WHEN odeneck_miktari = 0 THEN ? ELSE odeneck_miktari END
            """, (eski_tanim, eski_nitelik, eski_butce, eski_odeneck))
            
            self.connection.commit()
            print(f"✅ Eski kurum verileri alimlara taşındı")
        except Exception as e:
            print(f"⚠️ Veri taşıma hatası (önemsiz): {e}")

    def _kolonlari_getir(self, tablo: str) -> set[str]:
        self.cursor.execute(f"PRAGMA table_info({tablo})")
        return {row["name"] for row in self.cursor.fetchall()}

    def _benzersiz_kisitlari_ekle(self):
        self.cursor.executescript("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_degerlendirme_alim ON degerlendirme(alim_id);
            CREATE UNIQUE INDEX IF NOT EXISTS ux_muayene_kabul_alim ON muayene_kabul(alim_id);
            CREATE UNIQUE INDEX IF NOT EXISTS ux_teklif_kalem_firma ON teklifler(alim_id, firma_id, ihtiyac_id);
            CREATE UNIQUE INDEX IF NOT EXISTS ux_resmi_teklif_kalem_firma ON resmi_teklifler(alim_id, firma_id, ihtiyac_id);
            CREATE UNIQUE INDEX IF NOT EXISTS ux_muayene_kabul_detay_kalem ON muayene_kabul_detay(alim_id, ihtiyac_id);
            CREATE UNIQUE INDEX IF NOT EXISTS ux_on_mali_kontrol_satir ON on_mali_kontrol(alim_id, satir_no);
        """)
        self.connection.commit()

    def _okas_listesini_yukle(self):
        """OKAS kodlarını Python dosyasından veritabanına yükler."""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM okas_kodlari")
            if self.cursor.fetchone()[0] > 0:
                return 

            print("⏳ OKAS kodları veritabanına yükleniyor, lütfen bekleyin...")
            
            from services.okas_verisi import OKAS_KODLARI
            
            self.cursor.executemany(
                "INSERT OR IGNORE INTO okas_kodlari (cpv_kodu, kalem_adi, kalem_turu) VALUES (?, ?, ?)",
                OKAS_KODLARI
            )
            self.connection.commit()
            print(f"✅ {len(OKAS_KODLARI)} adet OKAS kodu başarıyla yüklendi!")
            
        except ImportError:
            print("⚠️ services/okas_verisi.py bulunamadı. Lütfen önce pdf_py_yap.py'yi çalıştırın.")
        except Exception as e:
            print(f"❌ OKAS yükleme hatası: {e}")

    def kapat(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.kapat()