# models/kurum.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Kurum:
    kurum_adi: str
    il: str
    ilce: str
    harcama_yetkilisi_ad: str
    harcama_yetkilisi_unvan: str
    gerceklestirme_gorevlisi_ad: str
    gerceklestirme_gorevlisi_unvan: str
    detsis_no: str = ""
    ust_makam_turu: str = "ilce"
    # Satın Alma Görevlileri (TC Kimlik No dahil)
    satin_alma_1_ad: str = ""
    satin_alma_1_unvan: str = ""
    satin_alma_1_tc: str = ""
    satin_alma_2_ad: str = ""
    satin_alma_2_unvan: str = ""
    satin_alma_2_tc: str = ""
    satin_alma_3_ad: str = ""
    satin_alma_3_unvan: str = ""
    satin_alma_3_tc: str = ""
    # Muayene ve Kabul Komisyonu Görevlileri (TC Kimlik No dahil)
    muayene_1_ad: str = ""
    muayene_1_unvan: str = ""
    muayene_1_tc: str = ""
    muayene_2_ad: str = ""
    muayene_2_unvan: str = ""
    muayene_2_tc: str = ""
    muayene_3_ad: str = ""
    muayene_3_unvan: str = ""
    muayene_3_tc: str = ""
    id: Optional[int] = None

    def dict(self):
        return {
            'kurum_adi': self.kurum_adi,
            'il': self.il,
            'ilce': self.ilce,
            'harcama_yetkilisi_ad': self.harcama_yetkilisi_ad,
            'harcama_yetkilisi_unvan': self.harcama_yetkilisi_unvan,
            'gerceklestirme_gorevlisi_ad': self.gerceklestirme_gorevlisi_ad,
            'gerceklestirme_gorevlisi_unvan': self.gerceklestirme_gorevlisi_unvan,
            'detsis_no': self.detsis_no,
            'ust_makam_turu': self.ust_makam_turu,
            'satin_alma_1_ad': self.satin_alma_1_ad,
            'satin_alma_1_unvan': self.satin_alma_1_unvan,
            'satin_alma_1_tc': self.satin_alma_1_tc,
            'satin_alma_2_ad': self.satin_alma_2_ad,
            'satin_alma_2_unvan': self.satin_alma_2_unvan,
            'satin_alma_2_tc': self.satin_alma_2_tc,
            'satin_alma_3_ad': self.satin_alma_3_ad,
            'satin_alma_3_unvan': self.satin_alma_3_unvan,
            'satin_alma_3_tc': self.satin_alma_3_tc,
            'muayene_1_ad': self.muayene_1_ad,
            'muayene_1_unvan': self.muayene_1_unvan,
            'muayene_1_tc': self.muayene_1_tc,
            'muayene_2_ad': self.muayene_2_ad,
            'muayene_2_unvan': self.muayene_2_unvan,
            'muayene_2_tc': self.muayene_2_tc,
            'muayene_3_ad': self.muayene_3_ad,
            'muayene_3_unvan': self.muayene_3_unvan,
            'muayene_3_tc': self.muayene_3_tc,
        }

    def satin_alma_gorevlileri(self):
        adaylar = [
            (self.satin_alma_1_ad, self.satin_alma_1_unvan),
            (self.satin_alma_2_ad, self.satin_alma_2_unvan),
            (self.satin_alma_3_ad, self.satin_alma_3_unvan),
        ]
        return [(ad, unvan) for ad, unvan in adaylar if ad.strip()]

    def muayene_kabul_gorevlileri(self):
        adaylar = [
            (self.muayene_1_ad, self.muayene_1_unvan),
            (self.muayene_2_ad, self.muayene_2_unvan),
            (self.muayene_3_ad, self.muayene_3_unvan),
        ]
        return [(ad, unvan) for ad, unvan in adaylar if ad.strip()]