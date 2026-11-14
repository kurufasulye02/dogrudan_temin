# models/ihtiyac.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class IhtiyacKalemi:
    malzeme_adi: str
    miktar: float
    birim: str
    alim_id: int
    sira_no: Optional[int] = None
    okas_kodu: Optional[str] = None # YENİ EKLENDİ
    id: Optional[int] = None

    def dict(self):
        return {
            'malzeme_adi': self.malzeme_adi,
            'miktar': self.miktar,
            'birim': self.birim,
            'alim_id': self.alim_id,
            'sira_no': self.sira_no,
            'okas_kodu': self.okas_kodu
        }