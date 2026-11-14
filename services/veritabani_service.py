from typing import List, Optional
from models import Kurum, IhtiyacKalemi, Firma, Teklif, Alim
from database.db_manager import DatabaseManager


class VeritabaniService:
    # Ortak alım SELECT listesi (yeni sütun eklendiğinde TEK yerden güncellenir)
    _ALIM_SELECT = (
        "SELECT id, alim_adi, yil, durum, kurum_id, toplam_tutar, odeneck_kontrol, alim_no, "
        "olusturma_tarihi, tamamlanma_tarihi, dosya_klasoru, odeme_tamamlandi, "
        "odeme_tamamlanma_tarihi, kurum_snapshot, ebys_onay_sayisi, alim_turu, "
        "odeneck_miktari, butce_tertibi, isin_tanimi, isin_niteligi FROM alimlar "
    )

    def __init__(self, db_path: Optional[str] = None):
        self.db = DatabaseManager(db_path)
        self.cursor = self.db.cursor
        self.connection = self.db.connection
        self._db_path = db_path

    @property
    def db_path(self) -> str:
        return self.db.db_path

    def kapat(self):
        if hasattr(self, 'db') and self.db:
            self.db.kapat()

    def ilerleme_durumlari(self, alim_id: int) -> list[bool]:
        if not alim_id:
            return [False] * 10
        kurum = self.kurum_getir()
        ihtiyaclar = self.ihtiyac_getir(alim_id)
        teklifler = self.teklifleri_getir(alim_id)
        gerekce = self.gerekce_getir(alim_id)
        resmi = self.resmi_teklifleri_getir(alim_id)
        kazanan = self.kazanan_getir(alim_id)
        muayene = self.muayene_kabul_detaylarini_getir(alim_id)
        alim = self.alim_getir(alim_id)
        hizmet_kabul = self.hizmet_kabul_getir(alim_id)

        from pathlib import Path
        klasor = Path(self.db_path).resolve().parent
        try:
            if alim and alim.dosya_klasoru and Path(alim.dosya_klasoru).is_dir():
                klasor = Path(alim.dosya_klasoru).resolve()
        except Exception:
            pass

        def has_prefix(*prefixes):
            for prefix in prefixes:
                if list(klasor.glob(f"{prefix}*")):
                    return True
            return False

        firma_sayisi = len({t['firma_id'] for t in teklifler})
        resmi_firma_sayisi = len({t['firma_id'] for t in resmi})
        teklif_tam = bool(ihtiyaclar) and firma_sayisi >= 2 and len(teklifler) >= len(ihtiyaclar) * firma_sayisi
        resmi_tam = bool(ihtiyaclar) and resmi_firma_sayisi >= 2 and len(resmi) >= len(ihtiyaclar) * resmi_firma_sayisi
        
        gerekce_tam = bool(gerekce) and has_prefix('Mal_ve_Hizmet_Alimi_Gerekce')

        if alim and getattr(alim, 'alim_turu', 'mal') == 'hizmet':
            muayene_tam = bool(hizmet_kabul) and has_prefix('Hizmet_Isleri_Kabul_Tutanagi')
        else:
            muayene_tam = bool(kazanan) and bool(muayene) and has_prefix('Muayene_Kabul_Tutanagi')
            
        ekap_tam = has_prefix('EKAP_Yukleme_Dosyasi', 'EKAP_Doldurulmus_Sablon')
        yaklasik_tam = has_prefix('Yaklasik_Maliyet_Cetveli')

        return [
            bool(kurum),
            bool(alim),
            bool(ihtiyaclar) and has_prefix('Ihtiyac_Listesi'),
            teklif_tam, # DÜZELTİLDİ: Sadece teklifler girildiyse yeşil olacak.
            yaklasik_tam,
            gerekce_tam,
            resmi_tam and has_prefix('Piyasa_Fiyat_Arastirma_Tutanagi', 'Karar_Tutanagi'),
            muayene_tam,
            ekap_tam,
            bool(alim and alim.odeme_tamamlandi),
        ]

    def kurum_kaydet(self, kurum: Kurum) -> int:
        veri = kurum.dict()
        self.cursor.execute("SELECT id FROM kurum LIMIT 1")
        var = self.cursor.fetchone()
        if var:
            sql = "UPDATE kurum SET " + ", ".join([f"{k}=?" for k in veri.keys()]) + " WHERE id=?"
            self.cursor.execute(sql, list(veri.values()) + [var[0]])
            self.connection.commit()
            return var[0]
        else:
            sql = f"INSERT INTO kurum ({', '.join(veri.keys())}) VALUES ({', '.join(['?']*len(veri))})"
            self.cursor.execute(sql, list(veri.values()))
            self.connection.commit()
            return self.cursor.lastrowid

    def kurum_getir(self) -> Optional[Kurum]:
        self.cursor.execute("SELECT * FROM kurum LIMIT 1")
        row = self.cursor.fetchone()
        if row:
            veri = dict(row)
            gecerli_alanlar = set(Kurum.__dataclass_fields__.keys())
            veri = {k: v for k, v in veri.items() if k in gecerli_alanlar}
            if veri.get('ust_makam_turu') not in ('il', 'ilce'):
                veri['ust_makam_turu'] = 'ilce'
            return Kurum(**veri)
        return None

    def alim_olustur(self, alim: Alim) -> int:
        veri = alim.dict()
        sql = f"INSERT INTO alimlar ({', '.join(veri.keys())}) VALUES ({', '.join(['?']*len(veri))})"
        self.cursor.execute(sql, list(veri.values()))
        self.connection.commit()
        return self.cursor.lastrowid

    def alim_guncelle(self, alim: Alim) -> bool:
        veri = alim.dict()
        sql = "UPDATE alimlar SET " + ", ".join([f"{k}=?" for k in veri.keys()]) + " WHERE id=?"
        self.cursor.execute(sql, list(veri.values()) + [alim.id])
        self.connection.commit()
        return self.cursor.rowcount > 0

    def alim_getir(self, alim_id: int) -> Optional[Alim]:
        self.cursor.execute(self._ALIM_SELECT + "WHERE id=?", (alim_id,))
        row = self.cursor.fetchone()
        if row:
            return Alim(**dict(row))
        return None

    def son_alim_getir(self) -> Optional[Alim]:
        self.cursor.execute(self._ALIM_SELECT + "ORDER BY id DESC LIMIT 1")
        row = self.cursor.fetchone()
        if row:
            return Alim(**dict(row))
        return None

    def alimlari_getir(self, yil: Optional[int] = None) -> List[Alim]:
        if yil:
            self.cursor.execute(self._ALIM_SELECT + "WHERE yil=? ORDER BY id DESC", (yil,))
        else:
            self.cursor.execute(self._ALIM_SELECT + "ORDER BY id DESC")
        rows = self.cursor.fetchall()
        return [Alim(**dict(row)) for row in rows]

    def alim_klasoru_guncelle(self, alim_id: int, klasor: str):
        self.cursor.execute("UPDATE alimlar SET dosya_klasoru=? WHERE id=?", (klasor, alim_id))
        self.connection.commit()

    def odeme_tamamla(self, alim_id: int, tamamlandi: bool = True):
        from datetime import datetime
        from services.arsiv_katalog import ArsivKatalog

        if tamamlandi:
            self.cursor.execute(
                "UPDATE alimlar SET odeme_tamamlandi=1, odeme_tamamlanma_tarihi=?, durum='tamamlandi', "
                "tamamlanma_tarihi=? WHERE id=?",
                (datetime.now(), datetime.now(), alim_id)
            )
            try:
                alim = self.alim_getir(alim_id)
                if alim:
                    katalog = ArsivKatalog()
                    durumlar = self.ilerleme_durumlari(alim_id)
                    tamamlanan = sum(durumlar)
                    katalog.ilerleme_guncelle(self.db_path, tamamlanan, 'tamamlandi')
                    katalog.kapat()
            except Exception as e:
                print(f"Katalog güncelleme hatası: {e}")
        else:
            self.cursor.execute(
                "UPDATE alimlar SET odeme_tamamlandi=0, odeme_tamamlanma_tarihi=NULL, durum='devam ediyor', "
                "tamamlanma_tarihi=NULL WHERE id=?",
                (alim_id,)
            )
            try:
                alim = self.alim_getir(alim_id)
                if alim:
                    katalog = ArsivKatalog()
                    durumlar = self.ilerleme_durumlari(alim_id)
                    tamamlanan = sum(durumlar)
                    katalog.ilerleme_guncelle(self.db_path, tamamlanan, 'devam ediyor')
                    katalog.kapat()
            except Exception as e:
                print(f"Katalog güncelleme hatası: {e}")

        self.connection.commit()

    # ============================================================
    # İHTİYAÇ LİSTESİ (OKAS DESTEKLİ)
    # ============================================================
    def ihtiyac_kaydet(self, kalemler: List[IhtiyacKalemi], alim_id: int | None = None):
        hedef_alim_id = alim_id if alim_id is not None else (kalemler[0].alim_id if kalemler else None)
        if hedef_alim_id is None:
            return
        if any(k.alim_id != hedef_alim_id for k in kalemler):
            raise ValueError("Aynı kaydetme işlemindeki tüm ihtiyaç kalemleri aynı alıma ait olmalıdır.")

        sira_nolar = [k.sira_no for k in kalemler]
        if any(n is None or n <= 0 for n in sira_nolar):
            raise ValueError("İhtiyaç sıra numaraları 1'den büyük olmalıdır.")
        if len(sira_nolar) != len(set(sira_nolar)):
            raise ValueError("Aynı alım içinde sıra numarası tekrar edemez.")

        try:
            self.cursor.execute("BEGIN")
            mevcut_rows = self.cursor.execute("SELECT id FROM ihtiyac_listesi WHERE alim_id=?", (hedef_alim_id,)).fetchall()
            mevcut_ids = {row['id'] for row in mevcut_rows}
            gelen_ids = {k.id for k in kalemler if k.id is not None}

            yabanci_ids = gelen_ids - mevcut_ids
            if yabanci_ids:
                raise ValueError("İhtiyaç kalemlerinden biri bu alıma ait değil veya artık mevcut değil.")

            for kalem in kalemler:
                if kalem.id is not None:
                    self.cursor.execute(
                        "UPDATE ihtiyac_listesi SET malzeme_adi=?, miktar=?, birim=?, sira_no=?, okas_kodu=? "
                        "WHERE id=? AND alim_id=?",
                        (kalem.malzeme_adi, kalem.miktar, kalem.birim, kalem.sira_no,
                         kalem.okas_kodu, kalem.id, hedef_alim_id)
                    )
                else:
                    self.cursor.execute(
                        "INSERT INTO ihtiyac_listesi (malzeme_adi, miktar, birim, alim_id, sira_no, okas_kodu) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (kalem.malzeme_adi, kalem.miktar, kalem.birim, hedef_alim_id,
                         kalem.sira_no, kalem.okas_kodu)
                    )

            silinecek_ids = mevcut_ids - gelen_ids
            for eski_id in silinecek_ids:
                for tablo in ("teklifler", "resmi_teklifler", "muayene_kabul_detay"):
                    self.cursor.execute(f"DELETE FROM {tablo} WHERE ihtiyac_id=?", (eski_id,))
                self.cursor.execute("DELETE FROM ihtiyac_listesi WHERE id=?", (eski_id,))

            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def ihtiyac_getir(self, alim_id: int) -> List[IhtiyacKalemi]:
        self.cursor.execute(
            "SELECT id, malzeme_adi, miktar, birim, alim_id, sira_no, okas_kodu "
            "FROM ihtiyac_listesi WHERE alim_id=? ORDER BY sira_no",
            (alim_id,)
        )
        rows = self.cursor.fetchall()
        return [IhtiyacKalemi(**dict(row)) for row in rows]

    def ihtiyac_sil(self, alim_id: int):
        self.cursor.execute("SELECT id FROM ihtiyac_listesi WHERE alim_id=?", (alim_id,))
        ids = [row['id'] for row in self.cursor.fetchall()]
        if ids:
            for tablo in ("teklifler", "resmi_teklifler", "muayene_kabul_detay"):
                self.cursor.executemany(f"DELETE FROM {tablo} WHERE ihtiyac_id=?", [(i,) for i in ids])
        self.cursor.execute("DELETE FROM ihtiyac_listesi WHERE alim_id=?", (alim_id,))
        self.connection.commit()

    # ============================================================
    # OKAS KODU ARAMA
    # ============================================================
    def okas_ara(self, sorgu: str = "", limit: int = 300) -> List[dict]:
        if not sorgu or not sorgu.strip():
            self.cursor.execute(
                "SELECT cpv_kodu, kalem_adi, kalem_turu FROM okas_kodlari "
                "ORDER BY cpv_kodu LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in self.cursor.fetchall()]

        q = sorgu.strip()
        q_like = f"%{q}%"
        q_start = f"{q}%"
        self.cursor.execute("""
            SELECT cpv_kodu, kalem_adi, kalem_turu FROM okas_kodlari
            WHERE cpv_kodu LIKE ? OR kalem_adi LIKE ?
            ORDER BY
                CASE WHEN cpv_kodu LIKE ? THEN 0 ELSE 1 END,
                CASE WHEN kalem_adi LIKE ? THEN 0 ELSE 1 END,
                cpv_kodu
            LIMIT ?
        """, (q_like, q_like, q_start, q_start, limit))
        return [dict(row) for row in self.cursor.fetchall()]

    def okas_kodu_getir(self, cpv_kodu: str) -> Optional[dict]:
        if not cpv_kodu:
            return None
        self.cursor.execute(
            "SELECT cpv_kodu, kalem_adi, kalem_turu FROM okas_kodlari WHERE cpv_kodu=? LIMIT 1",
            (str(cpv_kodu).strip(),)
        )
        row = self.cursor.fetchone()
        return dict(row) if row else None

    # ============================================================
    # FİRMALAR
    # ============================================================
    def firma_kaydet(self, firma: Firma) -> int:
        veri = firma.dict()
        self.cursor.execute("SELECT id FROM firmalar WHERE vergi_no=?", (firma.vergi_no,))
        var = self.cursor.fetchone()
        if var:
            firma_id = var[0]
            alanlar = [k for k in veri if k != "vergi_no"]
            self.cursor.execute(
                f"UPDATE firmalar SET {', '.join(f'{k}=?' for k in alanlar)} WHERE id=?",
                [veri[k] for k in alanlar] + [firma_id]
            )
            self.connection.commit()
            return firma_id
        sql = f"INSERT INTO firmalar ({', '.join(veri.keys())}) VALUES ({', '.join(['?']*len(veri))})"
        self.cursor.execute(sql, list(veri.values()))
        self.connection.commit()
        return self.cursor.lastrowid

    def firmalari_getir(self, alim_id: Optional[int] = None) -> List[Firma]:
        if alim_id:
            self.cursor.execute(
                "SELECT DISTINCT f.id, f.unvan, f.vergi_no, f.telefon, f.dogum_tarihi, f.adres, f.yetkili "
                "FROM firmalar f JOIN teklifler t ON t.firma_id = f.id "
                "WHERE t.alim_id = ? ORDER BY f.unvan",
                (alim_id,)
            )
        else:
            self.cursor.execute(
                "SELECT DISTINCT id, unvan, vergi_no, telefon, dogum_tarihi, adres, yetkili FROM firmalar ORDER BY unvan"
            )
        rows = self.cursor.fetchall()
        return [Firma(**dict(row)) for row in rows]

    def firma_getir(self, firma_id: int) -> Optional[Firma]:
        self.cursor.execute(
            "SELECT id, unvan, vergi_no, telefon, dogum_tarihi, adres, yetkili FROM firmalar WHERE id=?",
            (firma_id,)
        )
        row = self.cursor.fetchone()
        if row:
            return Firma(**dict(row))
        return None

    # ============================================================
    # TEKLİFLER
    # ============================================================
    def _teklifleri_kaydet_atomik(self, teklifler: List[Teklif], alim_id: int | None, tablo: str):
        if tablo not in {"teklifler", "resmi_teklifler"}:
            raise ValueError("Geçersiz teklif tablosu.")
        hedef_alim_id = alim_id if alim_id is not None else (teklifler[0].alim_id if teklifler else None)
        if hedef_alim_id is None:
            return

        ihtiyac_rows = self.cursor.execute(
            "SELECT id FROM ihtiyac_listesi WHERE alim_id=? ORDER BY sira_no",
            (hedef_alim_id,)
        ).fetchall()
        ihtiyac_ids = {row['id'] for row in ihtiyac_rows}
        if not ihtiyac_ids:
            raise ValueError("Bu alım için önce ihtiyaç listesi oluşturulmalıdır.")
        if not teklifler:
            self.cursor.execute(f"DELETE FROM {tablo} WHERE alim_id=?", (hedef_alim_id,))
            self.connection.commit()
            return

        if any(t.alim_id != hedef_alim_id for t in teklifler):
            raise ValueError("Aynı kaydetme işlemindeki tüm teklifler aynı alıma ait olmalıdır.")

        firma_ids = {t.firma_id for t in teklifler}
        if len(firma_ids) < 2:
            raise ValueError("En az 2 farklı firmadan teklif alınmalıdır.")

        gelen_ciftler = {(t.firma_id, t.ihtiyac_id) for t in teklifler}
        if any(t.ihtiyac_id not in ihtiyac_ids for t in teklifler):
            raise ValueError("Tekliflerden biri bu alıma ait olmayan bir ihtiyaç kalemine bağlı.")
        if len(gelen_ciftler) != len(teklifler):
            raise ValueError("Aynı firma ve ihtiyaç kalemi için birden fazla teklif kaydedilemez.")

        eksikler = {}
        for firma_id in firma_ids:
            eksik = ihtiyac_ids - {t.ihtiyac_id for t in teklifler if t.firma_id == firma_id}
            if eksik:
                eksikler[firma_id] = sorted(eksik)
        if eksikler:
            raise ValueError("Her firma bütün ihtiyaç kalemleri için teklif vermelidir. Eksik firma teklifleri var.")

        for t in teklifler:
            if t.birim_fiyat is None or float(t.birim_fiyat) <= 0:
                raise ValueError("Teklif fiyatları sıfırdan büyük olmalıdır.")

        try:
            self.cursor.execute("BEGIN")
            self.cursor.execute(f"DELETE FROM {tablo} WHERE alim_id=?", (hedef_alim_id,))
            for teklif in teklifler:
                veri = teklif.dict()
                sql = f"INSERT INTO {tablo} ({', '.join(veri.keys())}) VALUES ({', '.join(['?']*len(veri))})"
                self.cursor.execute(sql, list(veri.values()))
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def teklif_kaydet(self, teklifler: List[Teklif], alim_id: int | None = None):
        self._teklifleri_kaydet_atomik(teklifler, alim_id, "teklifler")

    def teklifleri_getir(self, alim_id: int) -> List[dict]:
        self.cursor.execute(
            "SELECT i.id as ihtiyac_id, i.malzeme_adi, i.miktar, i.birim, i.sira_no, "
            "f.id as firma_id, f.unvan, f.vergi_no, "
            "t.id as teklif_id, t.birim_fiyat, t.toplam_fiyat, t.kdv_orani "
            "FROM teklifler t "
            "JOIN ihtiyac_listesi i ON t.ihtiyac_id = i.id "
            "JOIN firmalar f ON t.firma_id = f.id "
            "WHERE t.alim_id = ? ORDER BY i.sira_no, f.unvan, f.id",
            (alim_id,)
        )
        return [dict(row) for row in self.cursor.fetchall()]

    def teklif_karsilastir(self, alim_id: int) -> List[dict]:
        self.cursor.execute(
            "SELECT f.id as firma_id, f.unvan, SUM(i.miktar * t.birim_fiyat) as toplam "
            "FROM teklifler t "
            "JOIN firmalar f ON t.firma_id = f.id "
            "JOIN ihtiyac_listesi i ON t.ihtiyac_id = i.id "
            "WHERE t.alim_id = ? "
            "GROUP BY t.firma_id, f.unvan "
            "HAVING COUNT(DISTINCT t.ihtiyac_id) = (SELECT COUNT(*) FROM ihtiyac_listesi WHERE alim_id=?) "
            "ORDER BY toplam, f.id",
            (alim_id, alim_id)
        )
        return [dict(row) for row in self.cursor.fetchall()]

    # ============================================================
    # RESMİ TEKLİFLER
    # ============================================================
    def resmi_teklif_kaydet(self, teklifler: List[Teklif], alim_id: int | None = None):
        self._teklifleri_kaydet_atomik(teklifler, alim_id, "resmi_teklifler")

    def resmi_teklifleri_getir(self, alim_id: int) -> List[dict]:
        self.cursor.execute(
            "SELECT i.id as ihtiyac_id, i.malzeme_adi, i.miktar, i.birim, i.sira_no, "
            "f.id as firma_id, f.unvan, f.vergi_no, f.adres, "
            "t.id as teklif_id, t.birim_fiyat, t.toplam_fiyat, t.kdv_orani "
            "FROM resmi_teklifler t "
            "JOIN ihtiyac_listesi i ON t.ihtiyac_id = i.id "
            "JOIN firmalar f ON t.firma_id = f.id "
            "WHERE t.alim_id = ? ORDER BY i.sira_no, f.unvan, f.id",
            (alim_id,)
        )
        return [dict(row) for row in self.cursor.fetchall()]

    def resmi_teklif_karsilastir(self, alim_id: int) -> List[dict]:
        self.cursor.execute(
            "SELECT f.id as firma_id, f.unvan, f.adres, SUM(i.miktar * t.birim_fiyat) as toplam "
            "FROM resmi_teklifler t "
            "JOIN firmalar f ON t.firma_id = f.id "
            "JOIN ihtiyac_listesi i ON t.ihtiyac_id = i.id "
            "WHERE t.alim_id = ? "
            "GROUP BY t.firma_id, f.unvan, f.adres "
            "HAVING COUNT(DISTINCT t.ihtiyac_id) = (SELECT COUNT(*) FROM ihtiyac_listesi WHERE alim_id=?) "
            "ORDER BY toplam, f.id",
            (alim_id, alim_id)
        )
        return [dict(row) for row in self.cursor.fetchall()]

    # ============================================================
    # DEĞERLENDİRME
    # ============================================================
    def kazanan_kaydet(self, alim_id: int, firma_id: int, toplam_tutar: float, karar_no: str):
        self.cursor.execute(
            "INSERT INTO degerlendirme (alim_id, kazanan_firma_id, kazanan_toplam_tutar, karar_no) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(alim_id) DO UPDATE SET "
            "kazanan_firma_id=excluded.kazanan_firma_id, "
            "kazanan_toplam_tutar=excluded.kazanan_toplam_tutar, "
            "karar_tarihi=CURRENT_TIMESTAMP, "
            "karar_no=excluded.karar_no",
            (alim_id, firma_id, toplam_tutar, karar_no)
        )
        self.connection.commit()

    def kazanan_getir(self, alim_id: int) -> Optional[dict]:
        self.cursor.execute(
            "SELECT f.id as firma_id, f.unvan, d.kazanan_toplam_tutar, d.karar_tarihi, d.karar_no "
            "FROM degerlendirme d "
            "JOIN firmalar f ON d.kazanan_firma_id = f.id "
            "WHERE d.alim_id = ?",
            (alim_id,)
        )
        row = self.cursor.fetchone()
        return dict(row) if row else None

    # ============================================================
    # MUAYENE KABUL
    # ============================================================
    def muayene_kabul_kaydet(self, alim_id: int, firma_id: int, kabul_edilen: float,
                             red_edilen: float, aciklama: str = "", teslim_tarihi: str = None):
        self.cursor.execute(
            "INSERT INTO muayene_kabul (alim_id, firma_id, teslim_tarihi, kabul_edilen_miktar, "
            "red_edilen_miktar, aciklama) VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(alim_id) DO UPDATE SET "
            "firma_id=excluded.firma_id, "
            "teslim_tarihi=excluded.teslim_tarihi, "
            "kabul_edilen_miktar=excluded.kabul_edilen_miktar, "
            "red_edilen_miktar=excluded.red_edilen_miktar, "
            "aciklama=excluded.aciklama",
            (alim_id, firma_id, teslim_tarihi, kabul_edilen, red_edilen, aciklama)
        )
        self.connection.commit()

    def muayene_kabul_detay_kaydet(self, alim_id: int, kalemler: List[dict]):
        self.cursor.execute("DELETE FROM muayene_kabul_detay WHERE alim_id=?", (alim_id,))
        for k in kalemler:
            self.cursor.execute(
                "INSERT INTO muayene_kabul_detay (alim_id, ihtiyac_id, kabul_miktar, red_miktar) "
                "VALUES (?, ?, ?, ?)",
                (alim_id, k['ihtiyac_id'], k['kabul_miktar'], k['red_miktar'])
            )
        self.connection.commit()

    def muayene_kabul_detaylarini_getir(self, alim_id: int) -> List[dict]:
        self.cursor.execute(
            "SELECT i.id as ihtiyac_id, i.sira_no, i.malzeme_adi, i.miktar, i.birim, "
            "d.kabul_miktar, d.red_miktar "
            "FROM muayene_kabul_detay d "
            "JOIN ihtiyac_listesi i ON d.ihtiyac_id = i.id "
            "WHERE d.alim_id = ? ORDER BY i.sira_no",
            (alim_id,)
        )
        return [dict(row) for row in self.cursor.fetchall()]

    # ============================================================
    # ÖN MALİ KONTROL (EK-32)
    # ============================================================
    def on_mali_kontrol_kaydet(self, alim_id: int, cevaplar: dict):
        self.cursor.execute("DELETE FROM on_mali_kontrol WHERE alim_id=?", (alim_id,))
        for satir_no, secim in cevaplar.items():
            self.cursor.execute(
                "INSERT INTO on_mali_kontrol (alim_id, satir_no, secim) VALUES (?, ?, ?)",
                (alim_id, satir_no, secim)
            )
        self.connection.commit()

    def on_mali_kontrol_getir(self, alim_id: int) -> dict:
        self.cursor.execute(
            "SELECT satir_no, secim FROM on_mali_kontrol WHERE alim_id=?",
            (alim_id,)
        )
        return {row['satir_no']: row['secim'] for row in self.cursor.fetchall()}

    def on_mali_kontrol_tamamlandi_mi(self, alim_id: int) -> bool:
        from services.on_mali_kontrol_maddeleri import CEVAPLANABILIR_MADDE_SAYISI
        cevaplar = self.on_mali_kontrol_getir(alim_id)
        return len(cevaplar) >= CEVAPLANABILIR_MADDE_SAYISI

    def __del__(self):
        self.kapat()
        
    def gerekce_kaydet(self, alim_id: int, veriler: dict):
        self.cursor.execute("""
            INSERT INTO gerekce_formu 
            (alim_id, katalog_disinda, teknik_yetersiz, fiyat_avantajsiz, teslimat_ivedi, detayli_aciklama, acil_gerekce)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(alim_id) DO UPDATE SET
            katalog_disinda=excluded.katalog_disinda,
            teknik_yetersiz=excluded.teknik_yetersiz,
            fiyat_avantajsiz=excluded.fiyat_avantajsiz,
            teslimat_ivedi=excluded.teslimat_ivedi,
            detayli_aciklama=excluded.detayli_aciklama,
            acil_gerekce=excluded.acil_gerekce
        """, (
            alim_id, veriler.get('katalog_disinda', 0), veriler.get('teknik_yetersiz', 0),
            veriler.get('fiyat_avantajsiz', 0), veriler.get('teslimat_ivedi', 0),
            veriler.get('detayli_aciklama', ''), veriler.get('acil_gerekce', '')
        ))
        self.connection.commit()

    def gerekce_getir(self, alim_id: int) -> dict:
        self.cursor.execute("SELECT * FROM gerekce_formu WHERE alim_id=?", (alim_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else {}

    def hizmet_kabul_kaydet(self, alim_id: int, veriler: dict):
        self.cursor.execute("""
            INSERT INTO hizmet_kabul 
            (alim_id, sozlesme_tarihi, sozlesme_bedeli, is_suresi, is_bitis_tarihi, sure_uzatimi, 
             uzatim_dahil_bitis, isin_bitirildigi_tarih, karar_turu, karar_tarihi, kabul_baslangic, 
             kabul_bitis, ancak_notu, makam_adi, tutanak_tarihi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(alim_id) DO UPDATE SET
            sozlesme_tarihi=excluded.sozlesme_tarihi,
            sozlesme_bedeli=excluded.sozlesme_bedeli,
            is_suresi=excluded.is_suresi,
            is_bitis_tarihi=excluded.is_bitis_tarihi,
            sure_uzatimi=excluded.sure_uzatimi,
            uzatim_dahil_bitis=excluded.uzatim_dahil_bitis,
            isin_bitirildigi_tarih=excluded.isin_bitirildigi_tarih,
            karar_turu=excluded.karar_turu,
            karar_tarihi=excluded.karar_tarihi,
            kabul_baslangic=excluded.kabul_baslangic,
            kabul_bitis=excluded.kabul_bitis,
            ancak_notu=excluded.ancak_notu,
            makam_adi=excluded.makam_adi,
            tutanak_tarihi=excluded.tutanak_tarihi
        """, (
            alim_id, veriler.get('sozlesme_tarihi'), veriler.get('sozlesme_bedeli'),
            veriler.get('is_suresi'), veriler.get('is_bitis_tarihi'), veriler.get('sure_uzatimi'),
            veriler.get('uzatim_dahil_bitis'), veriler.get('isin_bitirildigi_tarih'),
            veriler.get('karar_turu'), veriler.get('karar_tarihi'), veriler.get('kabul_baslangic'),
            veriler.get('kabul_bitis'), veriler.get('ancak_notu'), veriler.get('makam_adi'),
            veriler.get('tutanak_tarihi')
        ))
        self.connection.commit()

    def hizmet_kabul_getir(self, alim_id: int) -> dict:
        self.cursor.execute("SELECT * FROM hizmet_kabul WHERE alim_id=?", (alim_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else {}        