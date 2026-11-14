import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict


class ArsivKatalog:
    def __init__(self, katalog_path: Optional[str] = None):
        if katalog_path is None:
            katalog_path = Path.cwd() / "alim_katalog.db"
        self.katalog_path = str(katalog_path)
        self._baglan()
        self._tablolari_olustur()
    
    def _baglan(self):
        self.conn = sqlite3.connect(self.katalog_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout = 5000")
        self.cursor = self.conn.cursor()
    
    def _tablolari_olustur(self):
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS alim_katalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alim_adi TEXT NOT NULL,
                yil INTEGER NOT NULL,
                alim_no TEXT,
                db_yolu TEXT NOT NULL UNIQUE,
                klasor_yolu TEXT,
                durum TEXT DEFAULT 'hazirlik',
                tamamlanan_adim INTEGER DEFAULT 0,
                toplam_adim INTEGER DEFAULT 8,
                son_acilma_tarihi TEXT,
                kayit_tarihi TEXT DEFAULT CURRENT_TIMESTAMP,
                meta_data TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_katalog_yil ON alim_katalog(yil);
            CREATE INDEX IF NOT EXISTS idx_katalog_adi ON alim_katalog(alim_adi);
            CREATE INDEX IF NOT EXISTS idx_katalog_db_yolu ON alim_katalog(db_yolu);
        """)
        self.conn.commit()
    
    def kaydet(self, alim_adi: str, yil: int, db_yolu: str, klasor_yolu: str = None,
               alim_no: str = None, durum: str = 'hazirlik', tamamlanan_adim: int = 0,
               meta_data: dict = None) -> int:
        db_yolu = str(Path(db_yolu).resolve())
        klasor_yolu = str(Path(klasor_yolu or Path(db_yolu).parent).resolve())
        now = datetime.now().isoformat(timespec='seconds')
        meta = json.dumps(meta_data, ensure_ascii=False) if meta_data else None
        
        self.cursor.execute("""
            INSERT INTO alim_katalog 
                (alim_adi, yil, alim_no, db_yolu, klasor_yolu, durum, tamamlanan_adim, toplam_adim, son_acilma_tarihi, meta_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(db_yolu) DO UPDATE SET
                alim_adi=excluded.alim_adi,
                yil=excluded.yil,
                alim_no=excluded.alim_no,
                klasor_yolu=excluded.klasor_yolu,
                durum=excluded.durum,
                tamamlanan_adim=excluded.tamamlanan_adim,
                toplam_adim=excluded.toplam_adim,
                son_acilma_tarihi=excluded.son_acilma_tarihi,
                meta_data=excluded.meta_data
        """, (alim_adi, yil, alim_no, db_yolu, klasor_yolu, durum, tamamlanan_adim, 8, now, meta))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def son_acilma_guncelle(self, db_yolu: str):
        db_yolu = str(Path(db_yolu).resolve())
        now = datetime.now().isoformat(timespec='seconds')
        self.cursor.execute("UPDATE alim_katalog SET son_acilma_tarihi=? WHERE db_yolu=?", (now, db_yolu))
        self.conn.commit()
    
    def ilerleme_guncelle(self, db_yolu: str, tamamlanan_adim: int, durum: str = None):
        db_yolu = str(Path(db_yolu).resolve())
        if durum:
            self.cursor.execute("UPDATE alim_katalog SET tamamlanan_adim=?, durum=? WHERE db_yolu=?", (tamamlanan_adim, durum, db_yolu))
        else:
            self.cursor.execute("UPDATE alim_katalog SET tamamlanan_adim=? WHERE db_yolu=?", (tamamlanan_adim, db_yolu))
        self.conn.commit()
    
    def listele(self, arama: str = None, yil: int = None) -> List[Dict]:
        sql = "SELECT * FROM alim_katalog WHERE 1=1"
        params = []
        if arama:
            sql += " AND (alim_adi LIKE ? OR db_yolu LIKE ? OR klasor_yolu LIKE ? OR alim_no LIKE ?)"
            q = f"%{arama}%"
            params.extend([q, q, q, q])
        if yil:
            sql += " AND yil=?"
            params.append(yil)
        sql += " ORDER BY yil DESC, son_acilma_tarihi DESC, id DESC"
        self.cursor.execute(sql, params)
        return [dict(row) for row in self.cursor.fetchall()]
    
    def getir(self, db_yolu: str) -> Optional[Dict]:
        db_yolu = str(Path(db_yolu).resolve())
        self.cursor.execute("SELECT * FROM alim_katalog WHERE db_yolu=?", (db_yolu,))
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def sil(self, db_yolu: str):
        db_yolu = str(Path(db_yolu).resolve())
        self.cursor.execute("DELETE FROM alim_katalog WHERE db_yolu=?", (db_yolu,))
        self.conn.commit()
    
    def db_gecerli_mi(self, db_yolu: str) -> bool:
        try:
            with sqlite3.connect(str(Path(db_yolu).resolve())) as conn:
                tablolar = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            gerekli_tablolar = {'kurum', 'alimlar', 'ihtiyac_listesi', 'teklifler'}
            return gerekli_tablolar.issubset(tablolar)
        except Exception:
            return False
    
    def kapat(self):
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.kapat()