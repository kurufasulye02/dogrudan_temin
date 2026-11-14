from dataclasses import dataclass
from typing import Optional

@dataclass
class Teklif:
    alim_id: int
    firma_id: int
    ihtiyac_id: int
    birim_fiyat: float
    kdv_orani: float = 20.0
    toplam_fiyat: Optional[float] = None
    id: Optional[int] = None

    def __post_init__(self):
        if self.toplam_fiyat is None:
            self.toplam_fiyat = self.birim_fiyat

    def dict(self):
        return {
            'alim_id': self.alim_id,
            'firma_id': self.firma_id,
            'ihtiyac_id': self.ihtiyac_id,
            'birim_fiyat': self.birim_fiyat,
            'kdv_orani': self.kdv_orani,
            'toplam_fiyat': self.toplam_fiyat
        }