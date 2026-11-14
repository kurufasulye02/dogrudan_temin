from typing import List, Dict
from collections import defaultdict


class MaliyetService:
    @staticmethod
    def ortalama_fiyat_hesapla(fiyatlar: List[float]) -> float:
        fiyatlar = [f for f in fiyatlar if f > 0]
        if not fiyatlar:
            return 0
        return round(sum(fiyatlar) / len(fiyatlar), 2)

    @staticmethod
    def kdv_ekle(tutar: float, kdv_orani: float = 20) -> float:
        return round(tutar * (1 + kdv_orani / 100), 2)

    @staticmethod
    def yaklasik_maliyet_hesapla(teklifler: List[dict]) -> Dict[str, dict]:
        kalem_fiyatlari = defaultdict(list)
        for teklif in teklifler:
            malzeme_adi = teklif.get('malzeme_adi', '')
            birim_fiyat = teklif.get('birim_fiyat', 0)
            miktar = teklif.get('miktar', 0)
            if malzeme_adi and birim_fiyat > 0:
                kalem_fiyatlari[malzeme_adi].append({'birim_fiyat': birim_fiyat, 'miktar': miktar})

        sonuc = {}
        for malzeme, fiyatlar in kalem_fiyatlari.items():
            birim_fiyatlar = [f['birim_fiyat'] for f in fiyatlar]
            ortalama = MaliyetService.ortalama_fiyat_hesapla(birim_fiyatlar)
            miktar = fiyatlar[0]['miktar'] if fiyatlar else 0
            toplam = ortalama * miktar
            kdvli_toplam = MaliyetService.kdv_ekle(toplam)
            sonuc[malzeme] = {
                'ortalama_birim': ortalama,
                'miktar': miktar,
                'toplam': toplam,
                'kdvli_toplam': kdvli_toplam,
                'fiyatlar': birim_fiyatlar
            }
        return sonuc

    @staticmethod
    def genel_toplam_hesapla(maliyetler: Dict[str, dict]) -> Dict[str, float]:
        toplam_kdv_haric = 0
        toplam_kdv_dahil = 0
        for malzeme, veri in maliyetler.items():
            toplam_kdv_haric += veri.get('toplam', 0)
            toplam_kdv_dahil += veri.get('kdvli_toplam', 0)
        return {
            'toplam_kdv_haric': round(toplam_kdv_haric, 2),
            'toplam_kdv_dahil': round(toplam_kdv_dahil, 2)
        }