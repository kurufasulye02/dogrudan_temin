# services/on_mali_kontrol_maddeleri.py

ON_MALI_KONTROL_MADDELERI = [
    (1, "1", "Yaklaşık Maliyet Tablosu oluşturulmuş mu?"),
    (2, "1.1", "Yaklaşık Maliyet hesaplanırken KDV hariç mi hesaplanmış?"),
    (3, "1.2", "Yaklaşık Maliyet İcmal Tablosu mevcut mu?"),
    (4, "1.3", "Yaklaşık Maliyet hesaplanırken dayanakları mevcut mu?"),
    (5, "2", "Harcama işlemleri planlanırken 2024/7 Sayılı tasarruf tedbirleri genelgesine uyuldu mu?"),
    (6, "3", "Harcama Talimatı Onay Belgesi mevcut mu?"),
    (7, "2.1", "Harcama talimatının hukuki dayanağı ve gerekçesi mahiyetine uygun mu?"),
    (8, "2.2", "Gerçekleştirme Usulü mahiyetine uygun mu?"),
    (9, "2.3", "Seçilen Bütçe Tertibi harcamanın türüne uygun mu?"),
    (10, "2.4", "Parasal limitler dahilinde mi?"),
    (11, "4", "EKAP üzerinden Doğrudan Temin Kayıt Numarası alındı mı?"),
    (12, "6", "Piyasa Fiyat Araştırma Tutanağı eklenmiş mi?"),
    (13, "6.1", "Piyasa Fiyat Araştırma Tutanağında yer alan malzemelerin adet ve birim fiyatlarının çarpımı doğru hesaplanmış mı?"),
    (14, "6.2", "Piyasa Fiyat Araştırma Tutanağının tarihi, Harcama Talimatı/Onay Belgesi tarihi ile aynı veya sonra mı?"),
    (15, "6.3", "Piyasa Fiyat Araştırma Tutanağı, piyasa fiyat araştırması görevlileri tarafında imzalanmış mı?"),
    (16, "7", "Mal alımına ait sözleşme yapıldı mı?"),
    (17, "7.1", "Sözleşme üzerinde yer alan bilgiler eksiksiz doldurulmuş mu?"),
    (18, "7.2", "Sözleşmenin her sayfası taraflar tarafından paraf, kaşe ve imza yapılmış mı?"),
    (19, "7.3", "Sözleşmeye Ait Damga Vergisinin yatırıldığına dair Vergi Dairesi Alındısı mevcut mu?"),
    (20, "8", "Muayene Kabul Komisyon Tutanağı mevcut mu?"),
    (21, "8.1", "Muayene ve Kabul Komisyonu tutanağı fatura öncesi veya fatura tarihli düzenlenmiş mi?"),
    (22, "8.2", "Alınan mal, Muayene Kabul Komisyonu Görevlileri tarafından kontrol edildi mi?"),
    (23, "8.3", "Teslim edilen mal Muayene Kabul Komisyonu Görevlileri tarafından teslim alındı mı?"),
    (24, "9", "Fatura mevcut mu?"),
    (25, "9.1", "Yüklenici tarafından kesilen fatura, faturada bulunması gereken şekil şartlarını taşıyor mu?"),
    (26, "9.2", "Faturanın muhatabı doğru mu?"),
    (27, "9.3", "Faturada yer alan malzemelerin adedi ile birim fiyatlarının çarpımı doğru mu?"),
    (28, "9.4", "e-Arşiv Fatura ise barkod veya ilgisi tarafından kaşe ve yapılmış mı?"),
    (29, "9.5", "Faturanın notlar kısmına IBAN bilgileri yazılmış mı? IBAN bilgileri yoksa IBAN dilekçesi alındı mı?"),
    (30, "9.6", "e-Arşiv Fatura ise sorgulamayı yapan kişi tarafından kontrol edilerek kaşe ve imza yapılmış mı?"),
    (31, "10", "Mal alımlarında;"),
    (32, "10.1", "TKYS üzerinden Alınan Varlık İşlem Fişi eklendi mi?"),
    (33, "10.2", "Varlık İşlem Fişi üzerinde yer alan malzeme ile faturada yer alan malzeme aynı mı?"),
    (34, "10.3", "VİF'te kuruş farkı var mı?"),
    (35, "10.4", "Taşınır Kayıt Yetkilisi tarafından imzalandı mı?"),
    (36, "10.5", "HYS üzerinden alınan Varlık İşlem Fişi eklendi mi?"),
    (37, "11", "Gelir İdaresi Başkanlığından alınan Vergi Borcu Sorgusu mevcut mu?"),
    (38, "11.1", "Alınan Vergi Borcu Sorgusu güncel mi? (Belge tanzim edildiği tarihten itibaren 15 gün geçerlidir)"),
    (39, "11.2", "Vergi Borcu Sorgusu, sorgulamayı yapan görevli tarafından kontrol edilerek kaşelenip imzalanmış mı?"),
    (40, "11.3", "Vergi Borcu Sorgusunda Kişi/Firma/Kuruma ait borç varsa ve borç limitini aşıyorsa vergi borcu, Ödeme Emri Belgesi üzerinden kesildi mi?"),
    (41, "12", "KİK Yasaklılık sorgusu yapılarak Teyit Belgesi eklendi mi?"),
    (42, "14", "Ödeme Emri Belgesinde yer alan IBAN bilgileri fatura veya IBAN dilekçesi üzerinde yer alan bilgiler uyumlu mu?"),
    (43, "14.1", "Ödeme Emri Belgesinde yer alan Bütçe Tertibi doğru mu?"),
    (44, "14.2", "Fatura üzerinde yer alan KDV'siz toplam tutar üzerinden Diğer Ödemelere Ait Damga Vergisi kesildi mi?"),
    (45, "14.3", "Damga Vergisi Detay Kodu doğru seçilmiş mi?"),
    (46, "16", "Ödeme Emri Belgesi'ndeki imzalar görevlendirme belgeleri ile uyumlu mu?"),
    (47, "16.1", "Ödeme Emri Belgesi, farklı bir personel tarafından imzalandı ise yetki devri yapılmış mı?"),
    (48, "16.2", "Yetki devri yapıldığına dair evrak eklendi mi? (Yıllık İzin Formu vb.)"),
]

TOPLAM_MADDE_SAYISI = len(ON_MALI_KONTROL_MADDELERI)
RADYO_GEREKTIRMEYEN_SATIRLAR = {31}
CEVAPLANABILIR_MADDE_SAYISI = TOPLAM_MADDE_SAYISI - len(RADYO_GEREKTIRMEYEN_SATIRLAR)


def ana_madde_mi(sira_no: str) -> bool:
    return '.' not in sira_no