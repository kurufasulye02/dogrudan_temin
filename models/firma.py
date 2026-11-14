from dataclasses import dataclass
from typing import Optional

@dataclass
class Firma:
    unvan: str
    vergi_no: str
    telefon: str
    dogum_tarihi: str = ""  # YENİ EKLENDİ
    adres: Optional[str] = None
    yetkili: Optional[str] = None
    id: Optional[int] = None

    def dict(self):
        return {
            'unvan': self.unvan,
            'vergi_no': self.vergi_no,
            'telefon': self.telefon,
            'dogum_tarihi': self.dogum_tarihi, # YENİ EKLENDİ
            'adres': self.adres,
            'yetkili': self.yetkili
        }