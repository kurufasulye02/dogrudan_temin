# models/alim.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import json

@dataclass
class Alim:
    alim_adi: str
    yil: int
    isin_tanimi: str = "TÜKETİME YÖNELİK MAL VE MALZEME ALIMLARI"
    isin_niteligi: str = ""
    butce_tertibi: str = ""
    odeneck_miktari: float = 0.0
    alim_turu: str = "mal"  # 'mal', 'hizmet', 'bakim'
    durum: str = 'hazirlik'
    kurum_id: Optional[int] = None
    toplam_tutar: float = 0.0
    odeneck_kontrol: str = 'Beklemede'
    alim_no: Optional[str] = None
    olusturma_tarihi: Optional[datetime] = None
    tamamlanma_tarihi: Optional[datetime] = None
    dosya_klasoru: Optional[str] = None
    odeme_tamamlandi: int = 0
    odeme_tamamlanma_tarihi: Optional[datetime] = None
    kurum_snapshot: Optional[str] = None

    vadesi_gecmis_borc_sorgulandi: int = 0
    fatura_turu: str = ""
    e_fatura_iliskilendirildi: int = 0
    ebys_onay_sayisi: str = ""
    
    id: Optional[int] = None

    def dict(self):
        return {
            'alim_adi': self.alim_adi,
            'yil': self.yil,
            'isin_tanimi': self.isin_tanimi,
            'isin_niteligi': self.isin_niteligi,
            'butce_tertibi': self.butce_tertibi,
            'odeneck_miktari': self.odeneck_miktari,
            'alim_turu': self.alim_turu,
            'durum': self.durum,
            'kurum_id': self.kurum_id,
            'toplam_tutar': self.toplam_tutar,
            'odeneck_kontrol': self.odeneck_kontrol,
            'alim_no': self.alim_no,
            'tamamlanma_tarihi': self.tamamlanma_tarihi,
            'dosya_klasoru': self.dosya_klasoru,
            'odeme_tamamlandi': self.odeme_tamamlandi,
            'odeme_tamamlanma_tarihi': self.odeme_tamamlanma_tarihi,
            'kurum_snapshot': self.kurum_snapshot,
            'vadesi_gecmis_borc_sorgulandi': self.vadesi_gecmis_borc_sorgulandi,
            'fatura_turu': self.fatura_turu,
            'e_fatura_iliskilendirildi': self.e_fatura_iliskilendirildi,
            'ebys_onay_sayisi': self.ebys_onay_sayisi,
        }
    
    def set_kurum_snapshot(self, kurum) -> None:
        if kurum:
            self.kurum_snapshot = json.dumps(kurum.dict(), ensure_ascii=False, default=str)
    
    def get_kurum_snapshot(self) -> Optional[dict]:
        if self.kurum_snapshot:
            try:
                return json.loads(self.kurum_snapshot)
            except:
                return None
        return None