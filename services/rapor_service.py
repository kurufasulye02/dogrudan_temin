# services/rapor_service.py
import os
import re
import html
from datetime import datetime
from typing import List, Optional
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side
from xml.sax.saxutils import escape

from models import Kurum, IhtiyacKalemi, Firma, Alim


class RaporService:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def _dosya_adi_olustur(self, prefix: str, alim_no: str, uzanti: str = "docx") -> str:
        # Alım numarasında geçersiz dosya karakterleri varsa temizle
        guvenli_no = str(alim_no).replace("/", "_").replace("\\", "_").replace(":", "_")
        return os.path.join(self.output_dir, f"{prefix}_{guvenli_no}.{uzanti}")

    def _alim_is_niteligi(self, alim: Alim, kurum: Kurum) -> str:
        if alim and hasattr(alim, 'isin_niteligi') and alim.isin_niteligi:
            return alim.isin_niteligi.strip()
        if alim and alim.alim_adi and " - " in alim.alim_adi:
            return alim.alim_adi.split(" - ", 1)[1].strip()
        return "Malzeme"

    def _normal_stili_ayarla(self, doc, punto: int = None):
        stil = doc.styles['Normal']
        pf = stil.paragraph_format
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
        if punto is not None:
            stil.font.size = Pt(punto)
            stil.font.name = "Times New Roman"

    def _set_cell_border(self, cell, border_size=1):
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        for edge in ['top', 'left', 'bottom', 'right']:
            tag = f'w:{edge}'
            border = OxmlElement(tag)
            border.set(qn('w:val'), 'single')
            border.set(qn('w:sz'), str(border_size))
            border.set(qn('w:space'), '0')
            border.set(qn('w:color'), '000000')
            tcPr.append(border)

    def _ust_makam_basliklari(self, kurum: Kurum) -> tuple[str, str]:
        if getattr(kurum, 'ust_makam_turu', 'ilce') == 'il':
            return f"{kurum.il.upper()} VALİLİĞİ", "İL MİLLİ EĞİTİM MÜDÜRLÜĞÜ"
        return f"{kurum.ilce.upper()} KAYMAKAMLIĞI", "İLÇE MİLLİ EĞİTİM MÜDÜRLÜĞÜ"

    # ============================================================
    # YAKLAŞIK FİYAT ARAŞTIRMASI MEKTUBU (WORD)
    # ============================================================
    def yaklasik_fiyat_arastirma_mektubu_word(self, alim: Alim, kurum: Kurum, ihtiyaclar: List[IhtiyacKalemi], tarih: str = None) -> str:
        dosya_adi = self._dosya_adi_olustur("Yaklasik_Fiyat_Arastirma_Word", alim.alim_no if alim.alim_no else str(alim.id))
        doc = Document()
        self._normal_stili_ayarla(doc)
        section = doc.sections[0]
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("T.C.")
        run.bold = True
        run.font.size = Pt(14)
        run.font.name = "Times New Roman"

        ust_makam, mem = self._ust_makam_basliklari(kurum)
        for baslik in (ust_makam, mem):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(baslik)
            run.bold = True
            run.font.size = Pt(12)
            run.font.name = "Times New Roman"

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(kurum.kurum_adi.upper())
        run.bold = True
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"

        doc.add_paragraph()

        if not tarih:
            tarih = datetime.now().strftime('%d.%m.%Y')

        # EBYS Onay Sayısı varsa "Sayı" satırının sonuna ekle
        ebys = (getattr(alim, 'ebys_onay_sayisi', '') or '').strip()
        sayi_kismi = f"E-{kurum.detsis_no}-934.01.03-{ebys}" if ebys else f"E-{kurum.detsis_no}-934.01.03-"

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(f"Sayı : {sayi_kismi}\t\t\t\tTarih : {tarih}")
        run.bold = True
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run("Konu : Yaklaşık fiyat araştırması")
        run.bold = True
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"

        doc.add_paragraph()

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("YAKLAŞIK FİYAT ARAŞTIRMASI")
        run.bold = True
        run.font.size = Pt(14)
        run.font.name = "Times New Roman"

        doc.add_paragraph()

        # === DİNAMİK METİN: ALIM TÜRÜNE GÖRE ===
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        if getattr(alim, 'alim_turu', 'mal') == 'hizmet':
            metin = "Aşağıda yer alan bakım / onarım işinin ekli teknik şartnameye uygun olarak yapılmasında yaklaşık maliyete esas fiyatların tarafımıza bildirilmesi hususunda;"
        else:
            metin = "Okulumuzda kullanılmak üzere, ihtiyacımız olan aşağıda cinsi, miktarı ve özelliği yazılı olan araçların / gereçlerin / malzemelerin yaklaşık maliyete esas birim fiyatlarının tarafımıza bildirilmesi hususunda;"
            
        run = p.add_run(metin)
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"

        doc.add_paragraph()

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run("Gereğini arz ederim.")
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"

        doc.add_paragraph()
        doc.add_paragraph()

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = p.add_run(kurum.harcama_yetkilisi_ad.upper())
        run.bold = True
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = p.add_run(kurum.harcama_yetkilisi_unvan.upper())
        run.bold = True
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"

        doc.add_paragraph()

        table = doc.add_table(rows=1, cols=6)
        table.style = 'Table Grid'
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        col_widths = [Cm(1.2), Cm(8.5), Cm(2.5), Cm(2.5), Cm(2.8), Cm(2.8)]
        for i, width in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = width

        hdr_cells = table.rows[0].cells
        basliklar = ["S. No", "Malzemenin Adı ve Özellikleri", "Miktarı", "Birimi", "Birim Fiyatı", "Toplam Fiyatı"]

        for i, baslik in enumerate(basliklar):
            hdr_cells[i].text = baslik
            hdr_cells[i].paragraphs[0].runs[0].bold = True
            hdr_cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            hdr_cells[i].paragraphs[0].runs[0].font.size = Pt(10)
            hdr_cells[i].paragraphs[0].runs[0].font.name = "Times New Roman"
            self._set_cell_border(hdr_cells[i])

        for kalem in ihtiyaclar:
            row_cells = table.add_row().cells
            row_cells[0].text = str(kalem.sira_no)
            row_cells[1].text = kalem.malzeme_adi
            row_cells[2].text = str(int(kalem.miktar)) if kalem.miktar == int(kalem.miktar) else str(kalem.miktar)
            row_cells[3].text = kalem.birim
            row_cells[4].text = ""
            row_cells[5].text = ""

            for cell in row_cells:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                cell.paragraphs[0].runs[0].font.size = Pt(10)
                cell.paragraphs[0].runs[0].font.name = "Times New Roman"
                self._set_cell_border(cell)

            row_cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            row_cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            row_cells[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            row_cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT

        doc.add_paragraph()

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run("Not: Fiyatlar, 1. sınıf malzeme fiyatı olacak, malzemelerin K.D.V. Hariç fiyatı yazılacaktır.")
        run.italic = True
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

        doc.add_paragraph()

        # === DİNAMİK METİN: ALIM TÜRÜNE GÖRE ALT METİN ===
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        
        if getattr(alim, 'alim_turu', 'mal') == 'hizmet':
            metin2 = "Yukarıda yazılı bakım / onarım işinin bizdeki piyasa fiyatı karşılarında belirtildiği gibidir."
        else:
            metin2 = "Yukarıda cinsi ve miktarı yazılı malzemelerin bizdeki piyasa fiyatı karşılarında belirtildiği gibidir."
            
        run = p.add_run(metin2)
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"

        doc.add_paragraph()
        doc.add_paragraph()

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run("Adı-Soyadı- Ticaret Unvanı-İmza Mühür veya Kaşesi :")
        run.bold = True
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"

        doc.save(dosya_adi)
        return dosya_adi

    def ihtiyac_listesi_raporu(self, alim: Alim, kurum: Kurum, ihtiyaclar: List[IhtiyacKalemi], yil: int = 2026) -> str:
        dosya_adi = self._dosya_adi_olustur("Ihtiyac_Listesi", alim.alim_no if alim.alim_no else str(alim.id))
        doc = Document()
        self._normal_stili_ayarla(doc, punto=12)

        section = doc.sections[0]
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)        
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("T.C.")
        run.bold = True
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"

        ust_makam, mem = self._ust_makam_basliklari(kurum)
        for baslik in (ust_makam, mem):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(baslik)
            run.bold = True
            run.font.size = Pt(12)
            run.font.name = "Times New Roman"

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(kurum.kurum_adi.upper())
        run.bold = True
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"

        doc.add_paragraph()

        is_niteligi = self._alim_is_niteligi(alim, kurum).upper()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"{yil} - {yil+1} EĞİTİM ÖĞRETİM YILI {is_niteligi} İHTİYACI")
        run.bold = True
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"

        doc.add_paragraph()

        table = doc.add_table(rows=1, cols=3)
        table.style = 'Table Grid'

        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "SIRA NO"
        hdr_cells[1].text = "MALZEME ADI"
        hdr_cells[2].text = "ADET"

        for cell in hdr_cells:
            cell.paragraphs[0].runs[0].bold = True
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            cell.paragraphs[0].runs[0].font.size = Pt(12)
            cell.paragraphs[0].runs[0].font.name = "Times New Roman"

        for kalem in ihtiyaclar:
            row_cells = table.add_row().cells
            row_cells[0].text = str(kalem.sira_no)
            row_cells[1].text = kalem.malzeme_adi
            row_cells[2].text = str(int(kalem.miktar)) if kalem.miktar == int(kalem.miktar) else str(kalem.miktar)

            for cell in row_cells:
                cell.paragraphs[0].runs[0].font.size = Pt(12)
                cell.paragraphs[0].runs[0].font.name = "Times New Roman"

            row_cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            row_cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph()

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run("NOT: İhtiyaç miktarları birim fiyatlara göre piyasa fiyat araştırması öncesinde belirlenecektir.")
        run.italic = True
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"

        doc.add_paragraph()

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = p.add_run(kurum.gerceklestirme_gorevlisi_ad.upper())
        run.bold = True
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = p.add_run(kurum.gerceklestirme_gorevlisi_unvan.upper())
        run.bold = True
        run.font.size = Pt(12)
        run.font.name = "Times New Roman"

        doc.save(dosya_adi)
        return dosya_adi

    def karar_tutanagi(self, alim: Alim, kurum: Kurum, firma: Firma, toplam_tutar: float, karar_no: str, toplam_teklif_sayisi: int = 1, tarih: str = None) -> str:
        dosya_adi = self._dosya_adi_olustur("Karar_Tutanagi", alim.alim_no if alim.alim_no else str(alim.id), "xlsx")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Karar Tutanağı"

        bold = Font(bold=True, name="Times New Roman", size=11)
        normal = Font(name="Times New Roman", size=11)
        title_font = Font(bold=True, name="Times New Roman", size=14)
        center = Alignment(horizontal='center', vertical='center', wrap_text=True)
        left = Alignment(horizontal='left', vertical='center', wrap_text=True)
        thin = Side(style='thin')
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        last_col = 'I'

        def merge_set(rng, value=None, font=bold, align=center, brd=False):
            ws.merge_cells(rng)
            first = rng.split(':')[0]
            c = ws[first]
            if value is not None:
                c.value = value
            c.font = font
            c.alignment = align
            if brd:
                for row in ws[rng]:
                    for cell in row:
                        cell.border = border

        if not tarih:
            tarih = datetime.now().strftime('%d.%m.%Y')

        isin_niteligi = alim.isin_niteligi if hasattr(alim, 'isin_niteligi') and alim.isin_niteligi else self._alim_is_niteligi(alim, kurum)

        r = 1
        merge_set(f'A{r}:{last_col}{r}', "DOĞRUDAN TEMİN KARAR TUTANAĞI", title_font)
        r += 2
        satirlar = [
            ("Karar Tarihi :", tarih),
            ("Karar No :", karar_no),
            ("İşin adı :", isin_niteligi),
            ("Temin Şekli :", "4734 sayılı Kamu İhale Kanunu (22. maddesi d bendi) Doğrudan Temin"),
            ("Toplam Teklif Sayısı :", str(toplam_teklif_sayisi)),
        ]
        for baslik, deger in satirlar:
            merge_set(f'A{r}:B{r}', baslik, bold, left)
            merge_set(f'C{r}:{last_col}{r}', str(deger), normal, left)
            r += 1
        r += 1

        aciklama = f"İdaremizce {isin_niteligi} işine ait gerekli piyasa araştırması yapılmış olup, söz konusu alım için en avantajlı teklif veren aşağıdaki istekliden alım yapılması uygun görülmüştür."
        merge_set(f'A{r}:{last_col}{r}', aciklama, normal, left)
        ws.row_dimensions[r].height = 40
        r += 2

        merge_set(f'A{r}:{last_col}{r}', "Uygun Görülen İstekliler ve Teklif Ettiği Bedeller", bold, center)
        r += 1
        tablo_baslik = r
        merge_set(f'A{r}:A{r}', "Sıra No")
        merge_set(f'B{r}:G{r}', "İsteklinin Adı/Ticaret Unvanı")
        merge_set(f'H{r}:{last_col}{r}', "Teklif Ettiği Bedel")
        r += 1
        merge_set(f'A{r}:A{r}', "1", normal)
        merge_set(f'B{r}:G{r}', firma.unvan, normal, left)
        merge_set(f'H{r}:{last_col}{r}', f"{toplam_tutar:,.2f} TL", normal, center)
        for row in ws[f'A{tablo_baslik}:{last_col}{r}']:
            for cell in row:
                cell.border = border
        r += 2

        gorevliler = kurum.satin_alma_gorevlileri()
        gorev_unvanlari = ["Komisyon Başkanı", "Üye", "Üye"]
        kolon_araliklari = [('A', 'C'), ('D', 'F'), ('H', last_col)]
        imza_satir = r
        ad_satir = r + 1
        unvan_satir = r + 2
        for i, (bas_kol, son_kol) in enumerate(kolon_araliklari):
            merge_set(f'{bas_kol}{imza_satir}:{son_kol}{imza_satir}', "…………………", normal, center)
            ad = gorevliler[i][0] if i < len(gorevliler) else ""
            merge_set(f'{bas_kol}{ad_satir}:{son_kol}{ad_satir}', ad, bold, center)
            merge_set(f'{bas_kol}{unvan_satir}:{son_kol}{unvan_satir}', gorev_unvanlari[i], normal, center)

        genislikler = {'A': 8, 'B': 12, 'C': 12, 'D': 12, 'E': 12, 'F': 12, 'G': 12, 'H': 14, 'I': 14}
        for kol, genislik in genislikler.items():
            ws.column_dimensions[kol].width = genislik

        ws.page_setup.orientation = 'landscape'
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_options.horizontalCentered = True

        wb.save(dosya_adi)
        return dosya_adi

    def piyasa_fiyat_arastirma_tutanagi(self, alim: Alim, kurum: Kurum, ihtiyaclar: List[IhtiyacKalemi], resmi_teklifler: List[dict], tarih: str = None) -> str:
        dosya_adi = self._dosya_adi_olustur("Piyasa_Fiyat_Arastirma_Tutanagi", alim.alim_no if alim.alim_no else str(alim.id), "xlsx")

        firma_sirasi = []
        firma_bilgisi = {}
        ihtiyac_teklifleri = {}
        for t in resmi_teklifler:
            fid = t['firma_id']
            if fid not in firma_bilgisi:
                firma_bilgisi[fid] = {'unvan': t.get('unvan', ''), 'vergi_no': t.get('vergi_no', ''), 'adres': t.get('adres', '') or ''}
                firma_sirasi.append(fid)
            ihtiyac_teklifleri.setdefault(t['ihtiyac_id'], {})[fid] = t.get('birim_fiyat', 0) or 0
        firma_sirasi = firma_sirasi[:3]

        firma_toplamlari = {fid: 0.0 for fid in firma_sirasi}
        for kalem in ihtiyaclar:
            teklif_map = ihtiyac_teklifleri.get(kalem.id, {})
            for fid in firma_sirasi:
                bf = teklif_map.get(fid, 0)
                if bf:
                    firma_toplamlari[fid] += kalem.miktar * bf

        kazanan_fid = None
        if firma_toplamlari:
            gecerli = {fid: t for fid, t in firma_toplamlari.items() if t > 0}
            if gecerli:
                kazanan_fid = min(gecerli, key=gecerli.get)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Piyasa Fiyat Araştırma Tutanağı"

        bold = Font(bold=True, name="Times New Roman", size=10)
        normal = Font(name="Times New Roman", size=10)
        title_font = Font(bold=True, name="Times New Roman", size=13)
        center = Alignment(horizontal='center', vertical='center', wrap_text=True)
        left = Alignment(horizontal='left', vertical='center', wrap_text=True)
        thin = Side(style='thin')
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        last_col = 'L'

        def merge_set(rng, value=None, font=bold, align=center, brd=False):
            ws.merge_cells(rng)
            first = rng.split(':')[0]
            c = ws[first]
            if value is not None:
                c.value = value
            c.font = font
            c.alignment = align
            if brd:
                for row in ws[rng]:
                    for cell in row:
                        cell.border = border

        if not tarih:
            tarih = datetime.now().strftime('%d.%m.%Y')

        isin_niteligi = alim.isin_niteligi if hasattr(alim, 'isin_niteligi') and alim.isin_niteligi else self._alim_is_niteligi(alim, kurum)

        r = 1
        merge_set(f'A{r}:{last_col}{r}', "PİYASA FİYAT ARAŞTIRMASI TUTANAĞI", title_font)
        r += 1
        merge_set(f'A{r}:D{r}', "İdarenin Adı :", bold, left)
        merge_set(f'E{r}:{last_col}{r}', f"{kurum.kurum_adi} ({kurum.ilce}/{kurum.il})", normal, left)
        r += 1
        merge_set(f'A{r}:D{r}', "Yapılan İş / Mal / Hizmetin Adı, Niteliği :", bold, left)
        merge_set(f'E{r}:{last_col}{r}', isin_niteligi, normal, left)
        r += 1
        merge_set(f'A{r}:D{r}', "Düzenleme Tarihi :", bold, left)
        merge_set(f'E{r}:{last_col}{r}', tarih, normal, left)
        r += 2

        baslik_satir = r
        merge_set(f'A{baslik_satir}:A{baslik_satir+3}', "Sıra No")
        merge_set(f'B{baslik_satir}:D{baslik_satir+3}', "Satın Alınacak Mal ve Hizmetin Cinsi")
        merge_set(f'E{baslik_satir}:E{baslik_satir+3}', "Miktarı")
        merge_set(f'F{baslik_satir}:F{baslik_satir+3}', "Birimi")
        merge_set(f'G{baslik_satir}:{last_col}{baslik_satir}', "Kişiler / Firmalar Teklif Mektubu Fiyatları (KDV Hariç)")

        firma_kol_grup = [('G', 'H'), ('I', 'J'), ('K', 'L')]
        for i, (bkol, tkol) in enumerate(firma_kol_grup):
            bilgi = firma_bilgisi.get(firma_sirasi[i]) if i < len(firma_sirasi) else None
            merge_set(f'{bkol}{baslik_satir+1}:{tkol}{baslik_satir+1}', f"{i+1}. Teklif")
            merge_set(f'{bkol}{baslik_satir+2}:{tkol}{baslik_satir+2}', bilgi['unvan'] if bilgi else "-")
            merge_set(f'{bkol}{baslik_satir+3}:{tkol}{baslik_satir+3}', (bilgi['vergi_no'] if bilgi else "-"), normal)
            ws[f'{bkol}{baslik_satir+4}'] = "Birim Fiyat"
            ws[f'{tkol}{baslik_satir+4}'] = "Toplam Fiyat"
            for kol in (bkol, tkol):
                ws[f'{kol}{baslik_satir+4}'].font = bold
                ws[f'{kol}{baslik_satir+4}'].alignment = center

        for row in ws[f'A{baslik_satir}:{last_col}{baslik_satir+4}']:
            for cell in row:
                cell.border = border

        r = baslik_satir + 5
        for kalem in ihtiyaclar:
            ws.cell(row=r, column=1, value=kalem.sira_no).alignment = center
            ws.merge_cells(f'B{r}:D{r}')
            ws.cell(row=r, column=2, value=kalem.malzeme_adi).alignment = left
            miktar_val = int(kalem.miktar) if kalem.miktar == int(kalem.miktar) else kalem.miktar
            ws.cell(row=r, column=5, value=miktar_val).alignment = center
            ws.cell(row=r, column=6, value=kalem.birim).alignment = center

            teklif_map = ihtiyac_teklifleri.get(kalem.id, {})
            for i, fid in enumerate(firma_sirasi):
                bkol, tkol = firma_kol_grup[i]
                birim_fiyat = teklif_map.get(fid, 0)
                b_cell = ws[f'{bkol}{r}']
                b_cell.value = birim_fiyat if birim_fiyat else None
                b_cell.number_format = '#,##0.00'
                t_cell = ws[f'{tkol}{r}']
                t_cell.value = f'=IF({bkol}{r}>0,E{r}*{bkol}{r},"")'
                t_cell.number_format = '#,##0.00'

            for col in range(1, 13):
                ws.cell(row=r, column=col).border = border
                ws.cell(row=r, column=col).font = normal
            r += 1

        son_veri_satiri = r - 1
        toplam_satir = r
        merge_set(f'A{toplam_satir}:F{toplam_satir}', "Kişilerin / Firmaların Fiyat Teklifleri Toplamı (KDV Hariç)", bold, left)
        for i, (bkol, tkol) in enumerate(firma_kol_grup):
            if i < len(firma_sirasi):
                c = ws[f'{tkol}{toplam_satir}']
                c.value = f'=SUM({tkol}{baslik_satir+5}:{tkol}{son_veri_satiri})'
                c.number_format = '#,##0.00'
                c.font = bold
        for col in range(1, 13):
            ws.cell(row=toplam_satir, column=col).border = border
        r = toplam_satir + 2

        blok_baslangic = r
        merge_set(f'A{blok_baslangic}:F{blok_baslangic+2}', "Satın Alınacak Mal ve Hizmetin Tümünün Bu Kişi / Firmadan Alımı Uygun Görülmüştür.", bold, left)
        merge_set(f'G{r}:{last_col}{r}', "Uygun Görülen Kişi / Firma", bold, center)
        r += 1
        merge_set(f'G{r}:I{r}', "Adı", bold, center)
        merge_set(f'J{r}:{last_col}{r}', "Teklif Ettiği Toplam Fiyat (KDV Hariç)", bold, center)
        r += 1
        kazanan_bilgi = firma_bilgisi.get(kazanan_fid) if kazanan_fid else None
        merge_set(f'G{r}:I{r}', kazanan_bilgi['unvan'] if kazanan_bilgi else "-", normal, center)
        kazanan_toplam = firma_toplamlari.get(kazanan_fid, 0) if kazanan_fid else 0
        merge_set(f'J{r}:{last_col}{r}', f"{kazanan_toplam:,.2f} TL", normal, center)
        for row in ws[f'A{blok_baslangic}:{last_col}{r}']:
            for cell in row:
                cell.border = border
        r += 2

        aciklama = "4734 sayılı Kamu İhale Kanunu (22. maddesi d bendi) ile yapılacak alımlara ilişkin yapılan piyasa araştırmasında firmalarca / kişilerce teklif edilen fiyatlar tarafımca / tarafımızca değerlendirilerek yukarıda adı ve adresi belirtilen kişi / firma / firmalardan alım yapılması uygun görülmüştür."
        merge_set(f'A{r}:{last_col}{r}', aciklama, normal, left)
        ws.row_dimensions[r].height = 40
        r += 2

        merge_set(f'A{r}:{last_col}{r}', "Piyasa Fiyat Araştırması Görevlisi / Görevlileri", bold, center)
        r += 1
        gorevliler = kurum.satin_alma_gorevlileri()
        gorev_unvanlari = ["Komisyon Başkanı", "Üye", "Üye"]
        kolon_araliklari = [('A', 'D'), ('E', 'H'), ('I', 'L')]
        imza_satir = r
        ad_satir = r + 1
        unvan_satir = r + 2
        for i, (bas_kol, son_kol) in enumerate(kolon_araliklari):
            merge_set(f'{bas_kol}{imza_satir}:{son_kol}{imza_satir}', "…………………", normal, center)
            ad = gorevliler[i][0] if i < len(gorevliler) else ""
            merge_set(f'{bas_kol}{ad_satir}:{son_kol}{ad_satir}', ad, bold, center)
            merge_set(f'{bas_kol}{unvan_satir}:{son_kol}{unvan_satir}', gorev_unvanlari[i], normal, center)

        genislikler = {'A': 8, 'B': 10, 'C': 10, 'D': 10, 'E': 8, 'F': 8, 'G': 10, 'H': 10, 'I': 10, 'J': 10, 'K': 10, 'L': 10}
        for kol, genislik in genislikler.items():
            ws.column_dimensions[kol].width = genislik

        ws.page_setup.orientation = 'landscape'
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_options.horizontalCentered = True

        wb.save(dosya_adi)
        return dosya_adi

    def muayene_kabul_tutanagi(self, alim: Alim, kurum: Kurum, firma: Firma, muayene_detaylari: List[dict], teslim_tarihi: str = None, tarih: str = None) -> str:
        dosya_adi = self._dosya_adi_olustur("Muayene_Kabul_Tutanagi", alim.alim_no if alim.alim_no else str(alim.id), "xlsx")

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Muayene ve Kabul Tutanağı"

        bold = Font(bold=True, name="Times New Roman", size=10)
        normal = Font(name="Times New Roman", size=10)
        title_font = Font(bold=True, name="Times New Roman", size=13)
        center = Alignment(horizontal='center', vertical='center', wrap_text=True)
        left = Alignment(horizontal='left', vertical='center', wrap_text=True)
        thin = Side(style='thin')
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        last_col = 'J'

        def merge_set(rng, value=None, font=bold, align=center, brd=False):
            ws.merge_cells(rng)
            first = rng.split(':')[0]
            c = ws[first]
            if value is not None:
                c.value = value
            c.font = font
            c.alignment = align
            if brd:
                for row in ws[rng]:
                    for cell in row:
                        cell.border = border

        if not tarih:
            tarih = datetime.now().strftime('%d.%m.%Y')
        if not teslim_tarihi:
            teslim_tarihi = tarih

        isin_niteligi = alim.isin_niteligi if hasattr(alim, 'isin_niteligi') and alim.isin_niteligi else self._alim_is_niteligi(alim, kurum)

        r = 1
        merge_set(f'A{r}:{last_col}{r}', "MUAYENE VE KABUL TUTANAĞI", title_font)
        r += 1
        merge_set(f'A{r}:D{r}', "İdarenin Adı :", bold, left)
        merge_set(f'E{r}:{last_col}{r}', f"{kurum.kurum_adi} ({kurum.ilce}/{kurum.il})", normal, left)
        r += 1
        merge_set(f'A{r}:D{r}', "Yapılan İş / Mal / Hizmetin Adı, Niteliği :", bold, left)
        merge_set(f'E{r}:{last_col}{r}', isin_niteligi, normal, left)
        r += 1
        merge_set(f'A{r}:D{r}', "Satanın Adı Ünvanı :", bold, left)
        merge_set(f'E{r}:{last_col}{r}', firma.unvan, normal, left)
        r += 2

        baslik_satir = r
        ws[f'A{baslik_satir}'] = "S. No"
        merge_set(f'B{baslik_satir}:E{baslik_satir}', "Teslim Alınan Malın Cinsi ve Özellikleri")
        ws[f'F{baslik_satir}'] = "Miktarı"
        ws[f'G{baslik_satir}'] = "Birimi"
        ws[f'H{baslik_satir}'] = "Teslim Tarihi"
        ws[f'I{baslik_satir}'] = "Kabul Edilen Miktar"
        ws[f'J{baslik_satir}'] = "Red Edilen Miktar"
        for kol in ['A', 'F', 'G', 'H', 'I', 'J']:
            ws[f'{kol}{baslik_satir}'].font = bold
            ws[f'{kol}{baslik_satir}'].alignment = center

        for row in ws[f'A{baslik_satir}:{last_col}{baslik_satir}']:
            for cell in row:
                cell.border = border

        r = baslik_satir + 1
        for kalem in muayene_detaylari:
            ws.cell(row=r, column=1, value=kalem['sira_no']).alignment = center
            ws.merge_cells(f'B{r}:E{r}')
            ws.cell(row=r, column=2, value=kalem['malzeme_adi']).alignment = left
            miktar_val = kalem['miktar']
            miktar_val = int(miktar_val) if miktar_val == int(miktar_val) else miktar_val
            ws.cell(row=r, column=6, value=miktar_val).alignment = center
            ws.cell(row=r, column=7, value=kalem['birim']).alignment = center
            ws.cell(row=r, column=8, value=teslim_tarihi).alignment = center
            kabul_val = kalem['kabul_miktar']
            kabul_val = int(kabul_val) if kabul_val == int(kabul_val) else kabul_val
            ws.cell(row=r, column=9, value=kabul_val).alignment = center
            red_val = kalem['red_miktar']
            red_val = int(red_val) if red_val == int(red_val) else red_val
            ws.cell(row=r, column=10, value=red_val if red_val else 0).alignment = center

            for col in range(1, 11):
                ws.cell(row=r, column=col).border = border
                ws.cell(row=r, column=col).font = normal
            r += 1

        r += 1
        merge_set(f'A{r}:{last_col}{r}', "MUAYENE VE KABUL KOMİSYONU", bold, center)
        r += 1
        kalem_sayisi = len(muayene_detaylari)
        aciklama = f"Yukarıda yazılı {kalem_sayisi} kalem malzeme Mal Alımları Muayene ve Kabul Yönetmeliğine göre ihale dokümanında yazılı şartlar dahilinde muayene edilmiş ve ihale dökümanında yazılı şartlara uygun olduğu tespit edilerek kabul işlemi gerçekleştirilmiştir."
        merge_set(f'A{r}:{last_col}{r}', aciklama, normal, left)
        ws.row_dimensions[r].height = 40
        r += 2

        merge_set(f'A{r}:{last_col}{r}', "Muayene ve Kabul Görevlileri", bold, center)
        r += 1
        gorevliler = kurum.muayene_kabul_gorevlileri()
        gorev_unvanlari = ["Komisyon Başkanı", "Üye", "Üye"]
        kolon_araliklari = [('A', 'C'), ('E', 'G'), ('I', last_col)]
        imza_satir = r
        ad_satir = r + 1
        for i, (bas_kol, son_kol) in enumerate(kolon_araliklari):
            merge_set(f'{bas_kol}{imza_satir}:{son_kol}{imza_satir}', "…..", normal, center)
            ad = gorevliler[i][0] if i < len(gorevliler) else ""
            merge_set(f'{bas_kol}{ad_satir}:{son_kol}{ad_satir}', ad, bold, center)
            unvan_satir = ad_satir + 1
            merge_set(f'{bas_kol}{unvan_satir}:{son_kol}{unvan_satir}', gorev_unvanlari[i], normal, center)
        r = unvan_satir + 2

        merge_set(f'A{r}:{last_col}{r}', tarih, normal, center)
        r += 2

        merge_set(f'A{r}:{last_col}{r}', "…...", normal, center)
        r += 1
        merge_set(f'A{r}:{last_col}{r}', kurum.harcama_yetkilisi_ad, bold, center)
        r += 1
        merge_set(f'A{r}:{last_col}{r}', kurum.harcama_yetkilisi_unvan, normal, center)

        genislikler = {'A': 6, 'B': 10, 'C': 10, 'D': 10, 'E': 10, 'F': 8, 'G': 8, 'H': 12, 'I': 12, 'J': 12}
        for kol, genislik in genislikler.items():
            ws.column_dimensions[kol].width = genislik

        ws.page_setup.orientation = 'landscape'
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_options.horizontalCentered = True

        wb.save(dosya_adi)
        return dosya_adi

    def yaklasik_maliyet_cetveli(self, alim: Alim, kurum: Kurum, ihtiyaclar: List[IhtiyacKalemi], teklifler: List[dict], tarih: str = None) -> str:
        dosya_adi = self._dosya_adi_olustur("Yaklasik_Maliyet_Cetveli", alim.alim_no if alim.alim_no else str(alim.id), "xlsx")

        firma_sirasi = []
        firma_adlari = {}
        ihtiyac_teklifleri = {}
        for t in teklifler:
            fid = t['firma_id']
            if fid not in firma_adlari:
                firma_adlari[fid] = t.get('unvan', '')
                firma_sirasi.append(fid)
            ihtiyac_teklifleri.setdefault(t['ihtiyac_id'], {})[fid] = t.get('birim_fiyat', 0) or 0
        firma_sirasi = firma_sirasi[:3]

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Yaklaşık Maliyet Cetveli"

        bold = Font(bold=True, name="Times New Roman", size=10)
        normal = Font(name="Times New Roman", size=10)
        title_font = Font(bold=True, name="Times New Roman", size=13)
        center = Alignment(horizontal='center', vertical='center', wrap_text=True)
        left = Alignment(horizontal='left', vertical='center', wrap_text=True)
        thin = Side(style='thin')
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        last_col_letter = 'N'

        def merge_set(rng, value=None, font=bold, align=center, brd=False):
            ws.merge_cells(rng)
            first = rng.split(':')[0]
            c = ws[first]
            if value is not None:
                c.value = value
            c.font = font
            c.alignment = align
            if brd:
                for row in ws[rng]:
                    for cell in row:
                        cell.border = border

        merge_set(f'A1:{last_col_letter}1', "YAKLAŞIK MALİYET HESAP CETVELİ", title_font)

        if not tarih:
            tarih = datetime.now().strftime('%d.%m.%Y')

        isin_niteligi = alim.isin_niteligi if hasattr(alim, 'isin_niteligi') and alim.isin_niteligi else self._alim_is_niteligi(alim, kurum)

        merge_set('A2:D2', "İdarenin Adı :", bold, left)
        merge_set(f'E2:{last_col_letter}2', f"{kurum.kurum_adi} ({kurum.ilce}/{kurum.il})", normal, left)
        merge_set('A3:D3', "Yapılan İş / Mal / Hizmetin Adı, Niteliği :", bold, left)
        merge_set(f'E3:{last_col_letter}3', isin_niteligi, normal, left)
        merge_set('A4:D4', "Düzenleme Tarihi :", bold, left)
        merge_set(f'E4:{last_col_letter}4', tarih, normal, left)

        baslik_baslangic = 5
        merge_set(f'A{baslik_baslangic}:A{baslik_baslangic+3}', "Sıra No")
        merge_set(f'B{baslik_baslangic}:D{baslik_baslangic+3}', "Yaklaşık Maliyeti Hesaplanacak Mal ve Hizmetin Cinsi")
        merge_set(f'E{baslik_baslangic}:E{baslik_baslangic+3}', "Miktarı")
        merge_set(f'F{baslik_baslangic}:F{baslik_baslangic+3}', "Birimi")
        merge_set(f'G{baslik_baslangic}:L{baslik_baslangic}', "Piyasa Teklifleri (KDV Hariç)")
        merge_set(f'M{baslik_baslangic}:M{baslik_baslangic+3}', "Yaklaşık Maliyet\n(Ortalama Birim Fiyat)")
        merge_set(f'N{baslik_baslangic}:N{baslik_baslangic+3}', "Yaklaşık Maliyet\n(Ortalama Fiyat) KDV Hariç")

        firma_kol_grup = [('G', 'H'), ('I', 'J'), ('K', 'L')]
        for i, (bkol, tkol) in enumerate(firma_kol_grup):
            firma_adi = firma_adlari.get(firma_sirasi[i], "") if i < len(firma_sirasi) else ""
            merge_set(f'{bkol}{baslik_baslangic+1}:{tkol}{baslik_baslangic+1}', f"Firma {i+1}")
            merge_set(f'{bkol}{baslik_baslangic+2}:{tkol}{baslik_baslangic+2}', firma_adi if firma_adi else "-")
            ws[f'{bkol}{baslik_baslangic+3}'] = "Birim Fiyat"
            ws[f'{bkol}{baslik_baslangic+3}'].font = bold
            ws[f'{bkol}{baslik_baslangic+3}'].alignment = center
            ws[f'{tkol}{baslik_baslangic+3}'] = "Toplam Fiyat"
            ws[f'{tkol}{baslik_baslangic+3}'].font = bold
            ws[f'{tkol}{baslik_baslangic+3}'].alignment = center

        for col_letter in [c for pair in firma_kol_grup for c in pair]:
            cell = ws[f'{col_letter}{baslik_baslangic+3}']
            cell.border = border

        for row in ws[f'A{baslik_baslangic}:{last_col_letter}{baslik_baslangic+3}']:
            for cell in row:
                cell.border = border

        veri_baslangic = baslik_baslangic + 4
        row_idx = veri_baslangic
        for kalem in ihtiyaclar:
            ws.cell(row=row_idx, column=1, value=kalem.sira_no).alignment = center
            ws.merge_cells(f'B{row_idx}:D{row_idx}')
            ws.cell(row=row_idx, column=2, value=kalem.malzeme_adi).alignment = left
            miktar_val = int(kalem.miktar) if kalem.miktar == int(kalem.miktar) else kalem.miktar
            ws.cell(row=row_idx, column=5, value=miktar_val).alignment = center
            ws.cell(row=row_idx, column=6, value=kalem.birim).alignment = center

            teklif_map = ihtiyac_teklifleri.get(kalem.id, {})
            for i, fid in enumerate(firma_sirasi):
                bkol, tkol = firma_kol_grup[i]
                birim_fiyat = teklif_map.get(fid, 0)
                b_cell = ws[f'{bkol}{row_idx}']
                b_cell.value = birim_fiyat if birim_fiyat else None
                b_cell.number_format = '#,##0.00'
                t_cell = ws[f'{tkol}{row_idx}']
                t_cell.value = f'=IF({bkol}{row_idx}>0,E{row_idx}*{bkol}{row_idx},"")'
                t_cell.number_format = '#,##0.00'

            girilen_kollar = [firma_kol_grup[i][0] for i in range(len(firma_sirasi))]
            if girilen_kollar:
                say_formul = "+".join([f'IF({k}{row_idx}>0,1,0)' for k in girilen_kollar])
                toplam_formul = "+".join([f'IF({k}{row_idx}>0,{k}{row_idx},0)' for k in girilen_kollar])
                m_cell = ws[f'M{row_idx}']
                m_cell.value = f'=IF(({say_formul})>0,({toplam_formul})/({say_formul}),0)'
                m_cell.number_format = '#,##0.00'
            n_cell = ws[f'N{row_idx}']
            n_cell.value = f'=IF(M{row_idx}>0,E{row_idx}*M{row_idx},0)'
            n_cell.number_format = '#,##0.00'

            for col in range(1, 15):
                ws.cell(row=row_idx, column=col).border = border
                ws.cell(row=row_idx, column=col).font = normal
            row_idx += 1

        son_veri_satiri = row_idx - 1 if ihtiyaclar else veri_baslangic

        toplam_satir = row_idx
        merge_set(f'A{toplam_satir}:F{toplam_satir}', "Yaklaşık Maliyet Fiyatları Genel Toplamı :", bold, left)
        for i, (bkol, tkol) in enumerate(firma_kol_grup):
            if i < len(firma_sirasi):
                c = ws[f'{tkol}{toplam_satir}']
                c.value = f'=SUM({tkol}{veri_baslangic}:{tkol}{son_veri_satiri})'
                c.number_format = '#,##0.00'
                c.font = bold
        genel_toplam_cell = ws[f'N{toplam_satir}']
        genel_toplam_cell.value = f'=SUM(N{veri_baslangic}:N{son_veri_satiri})'
        genel_toplam_cell.number_format = '#,##0.00'
        genel_toplam_cell.font = bold
        for col in range(1, 15):
            ws.cell(row=toplam_satir, column=col).border = border

        aciklama_satir = toplam_satir + 2
        merge_set(f'A{aciklama_satir}:{last_col_letter}{aciklama_satir}', "Yukarıda açıklandığı üzere, ihaleye çıkılması düşünülen mal / hizmetlerin fiyat araştırması neticesinde; 4734 Sayılı İhale Kanununda değişiklik içeren 4964 Sayılı Kanunun 6. maddesi gereğince yaklaşık maliyet çıkarılmış olup; iş bu cetvel tanzim ve imza edilmiştir.", normal, left)
        ws.row_dimensions[aciklama_satir].height = 40

        imza_baslik_satir = aciklama_satir + 2
        merge_set(f'A{imza_baslik_satir}:{last_col_letter}{imza_baslik_satir}', "Yaklaşık Maliyeti Yapan Komisyon Üyeleri", bold, center)

        gorevliler = kurum.satin_alma_gorevlileri()
        gorev_unvanlari = ["Komisyon Başkanı", "Üye", "Üye"]
        kolon_araliklari = [('A', 'C'), ('F', 'H'), ('K', 'N')]

        imza_cizgi_satir = imza_baslik_satir + 3
        ad_satir = imza_cizgi_satir + 1
        unvan_satir = ad_satir + 1
        for i, (bas_kol, son_kol) in enumerate(kolon_araliklari):
            merge_set(f'{bas_kol}{imza_cizgi_satir}:{son_kol}{imza_cizgi_satir}', "…………………", normal, center)
            ad = gorevliler[i][0] if i < len(gorevliler) else ""
            merge_set(f'{bas_kol}{ad_satir}:{son_kol}{ad_satir}', ad, bold, center)
            merge_set(f'{bas_kol}{unvan_satir}:{son_kol}{unvan_satir}', gorev_unvanlari[i], normal, center)

        genislikler = {'A': 8, 'B': 10, 'C': 10, 'D': 10, 'E': 8, 'F': 8, 'G': 10, 'H': 10, 'I': 10, 'J': 10, 'K': 10, 'L': 10, 'M': 12, 'N': 12}
        for kol, genislik in genislikler.items():
            ws.column_dimensions[kol].width = genislik

        ws.page_setup.orientation = 'landscape'
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_options.horizontalCentered = True

        wb.save(dosya_adi)
        return dosya_adi

    def teklif_mektubu(self, alim: Alim, kurum: Kurum, ihtiyaclar: List[IhtiyacKalemi], firma: Firma, tarih: str = None) -> str:
        guvenli_unvan = "".join(c for c in firma.unvan if c.isalnum() or c in (' ', '_')).strip().replace(' ', '_')
        dosya_adi = self._dosya_adi_olustur(f"Teklif_Mektubu_{guvenli_unvan}", alim.alim_no if alim.alim_no else str(alim.id), "xlsx")

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Teklif Mektubu"

        bold = Font(bold=True, name="Times New Roman", size=10)
        normal = Font(name="Times New Roman", size=10)
        title_font = Font(bold=True, name="Times New Roman", size=13)
        center = Alignment(horizontal='center', vertical='center', wrap_text=True)
        left = Alignment(horizontal='left', vertical='center', wrap_text=True)
        thin = Side(style='thin')
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        last_col = 'G'

        def merge_set(rng, value=None, font=normal, align=left, brd=False):
            ws.merge_cells(rng)
            first = rng.split(':')[0]
            c = ws[first]
            if value is not None:
                c.value = value
            c.font = font
            c.alignment = align
            if brd:
                for row in ws[rng]:
                    for cell in row:
                        cell.border = border

        if not tarih:
            tarih = datetime.now().strftime('%d.%m.%Y')

        r = 1
        merge_set(f'A{r}:{last_col}{r}', "TEKLİF MEKTUBU", title_font, center)
        r += 2
        merge_set(f'A{r}:{last_col}{r}', f"Sayın {firma.unvan} Yetkilisi,", bold, left)
        r += 1
        merge_set(f'A{r}:{last_col}{r}', "İLGİLİ FİRMA YETKİLİLERİNE", bold, left)
        r += 2
        
        # DEĞİŞTİRİLEN KISIM BURASI
        aciklama = "Aşağıda, cinsi, miktarı ve özelliği yazılı olan araçlar / gereçler / malzemeler / bakım onarım işi 4734 sayılı Kamu İhale Kanunu'nun 22. maddesi (d) bendi uyarınca Doğrudan Temin ile satın alınacaktır. İlgilenmeniz halinde K.D.V. hariç birim fiyatlarınızın 5 iş günü içinde müdürlüğümüz satın alma görevlilerine verilmesi rica olunur."
        
        merge_set(f'A{r}:{last_col}{r}', aciklama, normal, left)
        ws.row_dimensions[r].height = 55
        r += 1
        merge_set(f'A{r}:{last_col}{r}', f"Tarih: {tarih}", normal, left)
        r += 2

        merge_set(f'A{r}:{last_col}{r}', "SATIN ALMA GÖREVLİLERİ", bold, center)
        r += 1
        gorevliler = kurum.satin_alma_gorevlileri()
        gorev_unvanlari = ["Komisyon Başkanı", "Üye", "Üye"]
        kolon_araliklari = [('A', 'B'), ('C', 'D'), ('F', 'G')]
        imza_satir = r
        ad_satir = r + 1
        unvan_satir = r + 2
        for i, (bas_kol, son_kol) in enumerate(kolon_araliklari):
            merge_set(f'{bas_kol}{imza_satir}:{son_kol}{imza_satir}', "….......", normal, center)
            ad = gorevliler[i][0] if i < len(gorevliler) else ""
            merge_set(f'{bas_kol}{ad_satir}:{son_kol}{ad_satir}', ad, bold, center)
            merge_set(f'{bas_kol}{unvan_satir}:{son_kol}{unvan_satir}', gorev_unvanlari[i], normal, center)
        r = unvan_satir + 2

        tablo_baslik_satir = r
        merge_set(f'A{tablo_baslik_satir}:E{tablo_baslik_satir}', "Satın Alınacak Malın / Hizmetin / Yapım İşinin", bold, center)
        merge_set(f'F{tablo_baslik_satir}:G{tablo_baslik_satir}', "Teklif Edilen\n(KDV Hariç)", bold, center)
        r += 1
        baslik_satir2 = r
        ws['A' + str(baslik_satir2)] = "S.No"
        merge_set(f'B{baslik_satir2}:C{baslik_satir2}', "Malzemenin Adı ve Özellikleri", bold, center)
        ws['D' + str(baslik_satir2)] = "Miktarı"
        ws['E' + str(baslik_satir2)] = "Birimi"
        ws['F' + str(baslik_satir2)] = "Birim Fiyatı"
        ws['G' + str(baslik_satir2)] = "Toplam Fiyatı"
        for kol in ['A', 'D', 'E', 'F', 'G']:
            ws[f'{kol}{baslik_satir2}'].font = bold
            ws[f'{kol}{baslik_satir2}'].alignment = center
            ws[f'{kol}{baslik_satir2}'].border = border

        for row in ws[f'A{tablo_baslik_satir}:{last_col}{tablo_baslik_satir}']:
            for cell in row:
                cell.border = border

        r = baslik_satir2 + 1
        for kalem in ihtiyaclar:
            ws.cell(row=r, column=1, value=kalem.sira_no).alignment = center
            ws.merge_cells(f'B{r}:C{r}')
            ws.cell(row=r, column=2, value=kalem.malzeme_adi).alignment = left
            miktar_val = int(kalem.miktar) if kalem.miktar == int(kalem.miktar) else kalem.miktar
            ws.cell(row=r, column=4, value=miktar_val).alignment = center
            ws.cell(row=r, column=5, value=kalem.birim).alignment = center
            for col in range(1, 8):
                ws.cell(row=r, column=col).border = border
                ws.cell(row=r, column=col).font = normal
            r += 1

        toplam_satir = r
        merge_set(f'A{toplam_satir}:E{toplam_satir}', "KDV Hariç Teklif Edilen Toplam Fiyat (TL)", bold, left)
        for col in range(1, 8):
            ws.cell(row=toplam_satir, column=col).border = border
        r = toplam_satir + 2

        merge_set(f'A{r}:{last_col}{r}', "DİĞER ŞARTLAR", bold, center)
        r += 1
        sartlar = [
            ("1- Teslim Süresi", "İhale sonucundan itibaren 15 iş günü"),
            ("2- Nakliye ve varsa sigortanın kime ait olduğu", "Yükleniciye aittir."),
            ("3- Diğer Özel Şartlar", ""),
            ("4- Teknik Şartname", ""),
            ("5- Diğer Hususlar", ""),
        ]
        for baslik, deger in sartlar:
            merge_set(f'A{r}:C{r}', baslik, normal, left)
            merge_set(f'D{r}:{last_col}{r}', deger, normal, left)
            r += 1
        r += 1

        kabul_metni = "Yukarıda belirtilen ve İdarenizce satın alınacak olan malların / hizmetlerin cinsi, özellikleri, miktarı ve diğer şartlarını okudum. K.D.V. hariç toplam …………………… TL, …………………………………. bedelle vermeyi kabul ve taahhüt ederim."
        merge_set(f'A{r}:{last_col}{r}', kabul_metni, normal, left)
        ws.row_dimensions[r].height = 45
        r += 3

        merge_set(f'D{r}:{last_col}{r}', "Teklif Eden", bold, center)
        r += 1
        merge_set(f'D{r}:{last_col}{r}', "…..... / ….... / 20…...", normal, center)
        r += 1
        merge_set(f'D{r}:{last_col}{r}', "Adı, Soyadı - Ticaret Ünvanı - İmza - Mühür", normal, center)

        genislikler = {'A': 6, 'B': 22, 'C': 10, 'D': 9, 'E': 9, 'F': 12, 'G': 13}
        for kol, genislik in genislikler.items():
            ws.column_dimensions[kol].width = genislik

        ws.page_setup.orientation = 'portrait'
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_options.horizontalCentered = True

        wb.save(dosya_adi)
        return dosya_adi

    def on_mali_kontrol_raporu(self, alim: Alim, kurum: Kurum, cevaplar: dict, tarih: str = None) -> str:
        from services.on_mali_kontrol_maddeleri import ON_MALI_KONTROL_MADDELERI

        dosya_adi = self._dosya_adi_olustur("On_Mali_Kontrol_Listesi", alim.alim_no if alim.alim_no else str(alim.id))
        doc = Document()
        self._normal_stili_ayarla(doc, punto=10)

        section = doc.sections[0]
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)        
        section.left_margin = Cm(1.5)
        section.right_margin = Cm(1.5)
        section.top_margin = Cm(1.5)
        section.bottom_margin = Cm(1.5)

        if not tarih:
            tarih = datetime.now().strftime('%d.%m.%Y')

        isin_niteligi = alim.isin_niteligi if hasattr(alim, 'isin_niteligi') and alim.isin_niteligi else self._alim_is_niteligi(alim, kurum)

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("4734-22/d Kapsamında Yapılacak Mal Alımlarına İlişkin\nÖn Mali Kontrol Listesi")
        run.bold = True
        run.font.size = Pt(13)
        run.font.name = "Times New Roman"

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("EK-32")
        run.bold = True
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

        doc.add_paragraph()

        for etiket, deger in (
            ("Harcama Birimi:", kurum.kurum_adi),
            ("İşin Adı:", isin_niteligi),
        ):
            p = doc.add_paragraph()
            run = p.add_run(f"{etiket} ")
            run.bold = True
            run.font.size = Pt(10)
            run.font.name = "Times New Roman"
            run2 = p.add_run(deger or "")
            run2.font.size = Pt(10)
            run2.font.name = "Times New Roman"

        doc.add_paragraph()

        table = doc.add_table(rows=1, cols=5)
        table.style = 'Table Grid'
        table.autofit = False

        genislikler = [Cm(1.3), Cm(11), Cm(2), Cm(1.5), Cm(1.5)]
        for i, genislik in enumerate(genislikler):
            for row in table.rows:
                row.cells[i].width = genislik

        basliklar = ["Sıra No", "Kontrol Edilecek Bilgi ve Belgeler", "Zorunlu Değil", "Evet", "Hayır"]
        hdr_cells = table.rows[0].cells
        for i, baslik in enumerate(basliklar):
            hdr_cells[i].text = baslik
            hdr_cells[i].width = genislikler[i]
            para = hdr_cells[i].paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = para.runs[0]
            run.bold = True
            run.font.size = Pt(9)
            run.font.name = "Times New Roman"

        secim_kolon = {'zorunlu_degil': 2, 'evet': 3, 'hayir': 4}

        for satir_no, sira_no, metin in ON_MALI_KONTROL_MADDELERI:
            row_cells = table.add_row().cells
            for i, genislik in enumerate(genislikler):
                row_cells[i].width = genislik

            row_cells[0].text = sira_no
            row_cells[1].text = metin

            secim = cevaplar.get(satir_no)
            kolon_idx = secim_kolon.get(secim)
            if kolon_idx is not None:
                row_cells[kolon_idx].text = "X"

            for i, cell in enumerate(row_cells):
                para = cell.paragraphs[0]
                if not para.runs:
                    para.add_run("")
                for run in para.runs:
                    run.font.size = Pt(9)
                    run.font.name = "Times New Roman"
                    if i in (2, 3, 4):
                        run.bold = True
                if i in (0, 2, 3, 4):
                    para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph()

        p = doc.add_paragraph()
        run = p.add_run("Kamu Ön Mali Kontrol Yönetmeliği'nin 6. maddesi gereğince hazırlanan bu kontrol listesinde yer alan bilgiler tarafımca kontrol edilmiş olup uygunluğu tasdik olunur.")
        run.font.size = Pt(10)
        run.font.name = "Times New Roman"

        doc.add_paragraph()
        doc.add_paragraph()

        for metin, kalin in (
            ("Gerçekleştirme Görevlisi", True),
            ((kurum.gerceklestirme_gorevlisi_ad or "").upper(), True),
            (kurum.gerceklestirme_gorevlisi_unvan or "", False),
            ("İmza", False),
        ):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            run = p.add_run(metin)
            run.bold = kalin
            run.font.size = Pt(10)
            run.font.name = "Times New Roman"

        doc.save(dosya_adi)
        return dosya_adi

    def mys_yaklasik_maliyet_raporu(self, alim: Alim, ihtiyaclar: List[IhtiyacKalemi], teklifler: List[dict]) -> str:
        dosya_adi = self._dosya_adi_olustur("MYS_Yaklasik_Maliyet", alim.alim_no if alim.alim_no else str(alim.id), "xlsx")

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sheet1"

        basliklar = ["Ürün Adı", "Miktar", "Ölçü Birimi", "Ürün No", "Model", "Marka", "Birim Tutar", "Firma VKN/TCKN"]
        for col, baslik in enumerate(basliklar, start=1):
            ws.cell(row=1, column=col, value=baslik)

        ihtiyac_teklifleri = {}
        for t in teklifler:
            ihtiyac_teklifleri.setdefault(t['ihtiyac_id'], []).append(
                (t.get('birim_fiyat'), t.get('vergi_no'))
            )

        r = 2
        for kalem in ihtiyaclar:
            ws.cell(row=r, column=1, value=kalem.malzeme_adi)
            miktar_val = int(kalem.miktar) if kalem.miktar == int(kalem.miktar) else kalem.miktar
            ws.cell(row=r, column=2, value=miktar_val)
            ws.cell(row=r, column=3, value=(kalem.birim or ""))
            r += 1

            for birim_fiyat, vergi_no in ihtiyac_teklifleri.get(kalem.id, []):
                if birim_fiyat is not None:
                    ws.cell(row=r, column=7, value=birim_fiyat)
                if vergi_no:
                    try:
                        ws.cell(row=r, column=8, value=int(vergi_no))
                    except (TypeError, ValueError):
                        ws.cell(row=r, column=8, value=vergi_no)
                r += 1

        genislikler = {'A': 45, 'B': 8, 'C': 14, 'D': 10, 'E': 10, 'F': 10, 'G': 12, 'H': 16}
        for kol, genislik in genislikler.items():
            ws.column_dimensions[kol].width = genislik

        wb.save(dosya_adi)
        return dosya_adi

    def yaklasik_fiyat_arastirma_mektubu(self, alim: Alim, kurum: Kurum, ihtiyaclar: List[IhtiyacKalemi], firma_adi: str = "", tarih: str = None) -> str:
        return self.yaklasik_fiyat_arastirma_mektubu_word(alim, kurum, ihtiyaclar, tarih)

    def yaklasik_fiyat_arastirma_mektubu(self, alim: Alim, kurum: Kurum, ihtiyaclar: List[IhtiyacKalemi], firma_adi: str = "", tarih: str = None) -> str:
        return self.yaklasik_fiyat_arastirma_mektubu_word(alim, kurum, ihtiyaclar, tarih)

    def _ekap_sablon_yukle(self) -> str:
        """Orijinal EKAP şablonunu (SpreadsheetML .xls) metin olarak okur."""
        import sys
        
        if getattr(sys, 'frozen', False):
            # PyInstaller ile derlenmişse geçici klasörü (_MEIPASS) kullan
            base_path = sys._MEIPASS
        else:
            # Normal Python çalışıyorsa mevcut klasörü kullan
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        yol = os.path.join(base_path, "services", "ekap_sablon.xls")
        
        # Eğer services klasöründe değilse, doğrudan ana dizinde ara (ihtimale karşı)
        if not os.path.exists(yol):
            yol = os.path.join(base_path, "ekap_sablon.xls")
            
        if not os.path.exists(yol):
            raise FileNotFoundError(f"EKAP şablonu bulunamadı: {yol}")
            
        with open(yol, "r", encoding="utf-8", newline="") as f:
            return f.read()

    def _ekap_listeleri_oku(self, sheet3: str) -> dict:
        """Şablonun Sheet3'ündeki açılır liste verilerini okur."""
        sutunlar = {1: [], 2: [], 3: [], 4: []}
        for satir in re.findall(r"<Row.*?</Row>", sheet3, re.S)[3:]:
            idx = 1
            for attrs, body in re.findall(r"<Cell([^>]*?)(?:/>|>(.*?)</Cell>)", satir, re.S):
                m = re.search(r'ss:Index="(\d+)"', attrs)
                if m:
                    idx = int(m.group(1))
                v = re.search(r"<Data[^>]*>(.*?)</Data>", body or "", re.S)
                if v and idx in sutunlar:
                    sutunlar[idx].append(html.unescape(v.group(1)))
                idx += 1
        return {"para": sutunlar[1], "mensei": sutunlar[2], "birim": sutunlar[3], "okas": sutunlar[4]}

    def ekap_excel_raporu(self, alim: Alim, ekap_verileri: list) -> str:
        if not ekap_verileri:
            raise ValueError("EKAP için aktarılacak kalem yok.")

        dosya_adi = self._dosya_adi_olustur("EKAP_Yukleme_Dosyasi", alim.alim_no if alim.alim_no else str(alim.id), "xls")
        self.ekap_uyarilar = []

        d = self._ekap_sablon_yukle()
        s1 = d.find('<Worksheet ss:Name="Sheet1">')
        s2 = d.find('<Worksheet ss:Name="Sheet2">')
        s3 = d.find('<Worksheet ss:Name="Sheet3">')
        if min(s1, s2, s3) < 0:
            raise ValueError("EKAP şablonu beklenen yapıda değil (Sheet1/2/3 bulunamadı).")

        L = self._ekap_listeleri_oku(d[s3:])

        # --- Eşleştirme yardımcıları ---
        def tr_lower(s):
            return str(s).replace("İ", "i").replace("I", "ı").lower().strip()

        para_map = {p.split(" ")[0].upper(): p for p in L["para"]}
        birim_map = {tr_lower(b): b for b in L["birim"]}
        okas_tam = set(L["okas"])
        okas_map = {}
        for o in L["okas"]:
            m = re.search(r"(\d+)\s*$", o)
            if m:
                okas_map[m.group(1)] = o

        def para_cevir(v):
            v = (v or "TRY").strip()
            return para_map.get(v.split(" ")[0].upper(), v)

        def birim_cevir(v):
            b = birim_map.get(tr_lower(v or ""))
            if not b:
                self.ekap_uyarilar.append(f"Birim EKAP listesinde yok: '{v}'")
            return b or (v or "")

        def okas_cevir(v):
            v = (v or "").strip()
            if not v or v in okas_tam:
                return v
            m = re.search(r"(\d+)\s*$", v)
            if m and m.group(1) in okas_map:
                return okas_map[m.group(1)]
            self.ekap_uyarilar.append(f"OKAS EKAP listesinde yok: '{v}'")
            return v

        def sayi(v):
            v = round(float(v or 0), 2)
            return str(int(v)) if v == int(v) else str(v)

        # ============================================================
        # SHEET 1: İŞ KALEMLERİ
        # ============================================================
        seg1 = d[s1:s2]
        
        table_match = re.search(r'<Table([^>]*)>', seg1)
        if table_match:
            table_attrs = table_match.group(1)
            new_row_count = len(ekap_verileri) + 1
            
            if 'ss:ExpandedRowCount=' in table_attrs:
                table_attrs = re.sub(r'ss:ExpandedRowCount="\d+"', f'ss:ExpandedRowCount="{new_row_count}"', table_attrs)
            else:
                table_attrs += f' ss:ExpandedRowCount="{new_row_count}"'
            
            if 'ss:ExpandedColumnCount=' in table_attrs:
                table_attrs = re.sub(r'ss:ExpandedColumnCount="\d+"', 'ss:ExpandedColumnCount="10"', table_attrs)
            else:
                table_attrs += ' ss:ExpandedColumnCount="10"'
                
            seg1 = seg1.replace(table_match.group(0), f'<Table{table_attrs}>', 1)

        rows = re.findall(r'<Row.*?</Row>', seg1, re.S)
        if len(rows) < 2:
            raise ValueError("EKAP şablonunda (Sheet1) yeterli satır yok.")

        yeni_satirlar = []
        istekli_adi = ekap_verileri[0]['istekli']

        for item in ekap_verileri:
            mensei = item['mensei'] if item['mensei'] in L["mensei"] else "Bilinmiyor"
            degerler = [
                item['is_kalemi'], mensei, sayi(item['miktar']), birim_cevir(item['birim']),
                okas_cevir(item['okas']), sayi(item['toplam_fiyat']), para_cevir(item['para_birimi']),
                item['istekli']
            ]

            sablon_satir = rows[1] 
            hucreler = list(re.finditer(r'<Cell[^>]*?(?:/>|>.*?</Cell>)', sablon_satir, re.S))
            
            yeni_satir = sablon_satir
            for i in range(min(len(hucreler), len(degerler)) - 1, -1, -1):
                hucre = hucreler[i]
                val = degerler[i]
                
                hucre_tag_match = re.search(r'<Cell([^>]*?)(?:/>|>)', hucre.group(0))
                etiket = hucre_tag_match.group(1).rstrip('/') if hucre_tag_match else ""
                
                if val == "" or val is None:
                    yeni_hucre = f'<Cell{etiket}/>'
                else:
                    tip = "Number" if i in (2, 5) else "String"
                    yeni_hucre = f'<Cell{etiket}><Data ss:Type="{tip}">{escape(str(val))}</Data></Cell>'
                
                yeni_satir = yeni_satir[:hucre.start()] + yeni_hucre + yeni_satir[hucre.end():]

            yeni_satirlar.append(yeni_satir)

        row1_end = seg1.find('</Row>') + 6 
        kalan_xml = seg1[seg1.rfind('</Row>') + 6:]
        seg1_yeni = seg1[:row1_end] + "\r\n   ".join(yeni_satirlar) + "\r\n  " + kalan_xml


        # ============================================================
        # SHEET 2: İSTEKLİ ADI (Hatasız A2 Yazımı)
        # ============================================================
        seg2 = d[s2:s3]
        
        # Şablondaki varsayılan ismi temizle
        seg2 = seg2.replace("SEMİH RIDVAN TOSUN", "")

        # A1'deki "DEĞİŞTİRMEYİN" satırını bul
        a1_match = re.search(r'<Row[^>]*>(?:(?!</Row>).)*DEĞİŞTİRMEYİN(?:(?!</Row>).)*</Row>', seg2, re.S)
        
        if a1_match:
            row1_end = a1_match.end()
            
            # A1'den sonra hemen başka bir satır (Row) var mı?
            # (Genelde şablonda altında boş bir satır bulunur)
            next_row_match = re.search(r'<Row[^>]*>.*?</Row>', seg2[row1_end:], re.S)
            
            if next_row_match:
                # Eğer altında satır varsa, onu kullan (Satır sayısını artırmaya gerek yok)
                hedef_row = next_row_match.group(0)
                cell_match = re.search(r'<Cell([^>]*?)>.*?</Cell>', hedef_row, re.S)
                
                if cell_match:
                    yeni_hucre = f'<Cell{cell_match.group(1)}><Data ss:Type="String">{escape(istekli_adi)}</Data></Cell>'
                    yeni_row = hedef_row.replace(cell_match.group(0), yeni_hucre, 1)
                else:
                    # Eğer hücre boşsa (<Cell/>)
                    cell_match_self = re.search(r'<Cell([^>]*?)/>', hedef_row, re.S)
                    if cell_match_self:
                        yeni_hucre = f'<Cell{cell_match_self.group(1)}><Data ss:Type="String">{escape(istekli_adi)}</Data></Cell>'
                        yeni_row = hedef_row.replace(cell_match_self.group(0), yeni_hucre, 1)
                    else:
                        yeni_row = hedef_row.replace('</Row>', f'<Cell><Data ss:Type="String">{escape(istekli_adi)}</Data></Cell></Row>', 1)
                        
                seg2_yeni = seg2[:row1_end + next_row_match.start()] + yeni_row + seg2[row1_end + next_row_match.end():]
            else:
                # Eğer altında satır yoksa, yeni satır ekle VE ExpandedRowCount'u güncelle
                yeni_a2_satiri = f'<Row><Cell><Data ss:Type="String">{escape(istekli_adi)}</Data></Cell></Row>'
                seg2_yeni = seg2[:row1_end] + yeni_a2_satiri + seg2[row1_end:]
                
                # Table satır sayısını güncelle (Excel hatasını önlemek için)
                table2_match = re.search(r'<Table([^>]*)>', seg2_yeni)
                if table2_match:
                    t_attrs = table2_match.group(1)
                    r_count_match = re.search(r'ss:ExpandedRowCount="(\d+)"', t_attrs)
                    if r_count_match:
                        yeni_count = int(r_count_match.group(1)) + 1
                        t_attrs = t_attrs.replace(r_count_match.group(0), f'ss:ExpandedRowCount="{yeni_count}"')
                        seg2_yeni = seg2_yeni.replace(table2_match.group(0), f'<Table{t_attrs}>', 1)
        else:
            seg2_yeni = seg2

        # ============================================================
        # BİRLEŞTİR VE KAYDET
        # ============================================================
        yeni_xml = d[:s1] + seg1_yeni + seg2_yeni + d[s3:]
        
        with open(dosya_adi, "w", encoding="utf-8", newline="") as f:
            f.write(yeni_xml)
            
        return dosya_adi
   
    def gerekce_formu_raporu(self, alim: Alim, kurum: Kurum, veriler: dict, ihtiyaclar: List[IhtiyacKalemi], toplam_maliyet: float) -> str:
        dosya_adi = self._dosya_adi_olustur("Mal_ve_Hizmet_Alimi_Gerekce", alim.alim_no if alim.alim_no else str(alim.id))
        doc = Document()
        self._normal_stili_ayarla(doc, punto=11)

        section = doc.sections[0]
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)

        # Başlık
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("MAL VE HİZMET ALIMI GEREKÇE FORMU")
        run.bold = True
        run.font.size = Pt(14)
        run.font.name = "Times New Roman"

        doc.add_paragraph()

        # Üst Bilgiler
        p = doc.add_paragraph()
        run = p.add_run("Tarih: " + datetime.now().strftime('%d/%m/%Y'))
        run.bold = True
        run.font.name = "Times New Roman"

        p = doc.add_paragraph()
        run = p.add_run("Kurum Adı: MİLLİ EĞİTİM BAKANLIĞI")
        run.bold = True
        run.font.name = "Times New Roman"

        p = doc.add_paragraph()
        run = p.add_run(f"Harcama Birimi: {kurum.kurum_adi}")
        run.bold = True
        run.font.name = "Times New Roman"

        doc.add_paragraph()

        # 1. Genel Bilgiler
        p = doc.add_paragraph()
        run = p.add_run("1. Alıma İlişkin Genel Bilgiler")
        run.bold = True
        run.font.size = Pt(12)

        isin_niteligi = self._alim_is_niteligi(alim, kurum)

        p = doc.add_paragraph(style='List Bullet')
        p.add_run("Talep Edilen Mal/Hizmetin Adı: ").bold = True
        p.add_run(isin_niteligi)

        p = doc.add_paragraph(style='List Bullet')
        p.add_run("Miktarı / Adedi: ").bold = True
        p.add_run(f"{len(ihtiyaclar)} Kalem")

        p = doc.add_paragraph(style='List Bullet')
        p.add_run("Tahmini Yaklaşık Maliyeti: ").bold = True
        p.add_run(f"{toplam_maliyet:,.2f} TL")

        doc.add_paragraph()

        # 2. DMO Gerekçesi
        p = doc.add_paragraph()
        run = p.add_run("2. DMO'dan Temin Edilememe Gerekçesi (Uygun olan seçeneği işaretleyiniz ve açıklayınız)")
        run.bold = True
        run.font.size = Pt(12)

        dmo_maddeler = [
            ('katalog_disinda', "Katalogda Bulunmaması: İhtiyaç duyulan mal/hizmetin teknik özellikleri veya doğrudan kendisi güncel DMO kataloglarında yer almamaktadır."),
            ('teknik_yetersiz', "Teknik Yetersizlik / Uyumsuzluk: DMO kataloglarında yer alan muadil ürünler, kurumumuzda mevcut olan sistem/donanım altyapısı ile teknik olarak uyum sağlamamaktadır."),
            ('fiyat_avantajsiz', "Fiyat Avantajsızlığı: Yapılan piyasa fiyat araştırması neticesinde, talep edilen ürünün piyasadan daha ekonomik şartlarda temin edilebileceği ve kamu yararı oluşacağı tespit edilmiştir."),
            ('teslimat_ivedi', "Teslimat ve İvedilik Süresi: DMO üzerinden yapılacak alımlarda öngörülen teslimat süresi, birimimizin yürütmekte olduğu acil/zorunlu faaliyetleri aksatacak niteliktedir.")
        ]

        for key, metin in dmo_maddeler:
            isaret = "(X)" if veriler.get(key) else "( )"
            p = doc.add_paragraph(style='List Bullet')
            p.add_run(f"{isaret} {metin}")

        doc.add_paragraph()
        p = doc.add_paragraph()
        run = p.add_run("Detaylı Açıklama:")
        run.bold = True
        p = doc.add_paragraph(veriler.get('detayli_aciklama', ''))

        doc.add_paragraph()

        # 3. Acil Gerekçe
        p = doc.add_paragraph()
        run = p.add_run("3. Acil ve Zorunlu Alım Gerekçesi (Tasarruf Tedbirleri Kapsamında)")
        run.bold = True
        run.font.size = Pt(12)
        p = doc.add_paragraph(veriler.get('acil_gerekce', ''))

        doc.add_paragraph()

        # 4. Beyan
        p = doc.add_paragraph()
        run = p.add_run("4. Beyan ve Taahhüt")
        run.bold = True
        run.font.size = Pt(12)
        p = doc.add_paragraph("Yukarıda bilgileri ve gerekçeleri belirtilen mal/hizmet alımının, 4734 sayılı Kamu İhale Kanunu ve ilgili Tasarruf Tedbirleri Genelgelerine uygun olarak kamu yararı ve hizmetin ivediliği gözetilerek DMO dışından temin edilmesini arz ederim.")

        doc.add_paragraph()
        doc.add_paragraph()

        # İmzalar
        table = doc.add_table(rows=1, cols=2)
        table.autofit = False
        table.columns[0].width = Cm(8)
        table.columns[1].width = Cm(8)

        cell1 = table.cell(0, 0)
        p = cell1.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run("Gerçekleştirme Görevlisi\n").bold = True
        p.add_run(f"Adı Soyadı: {kurum.gerceklestirme_gorevlisi_ad}\n")
        p.add_run(f"Unvanı: {kurum.gerceklestirme_gorevlisi_unvan}\n")
        p.add_run("İmza:")

        cell2 = table.cell(0, 1)
        p = cell2.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run("Harcama Yetkilisi\n").bold = True
        p.add_run(f"Adı Soyadı: {kurum.harcama_yetkilisi_ad}\n")
        p.add_run(f"Unvanı: {kurum.harcama_yetkilisi_unvan}\n")
        p.add_run("İmza:")

        doc.save(dosya_adi)
        return dosya_adi
        
    def hizmet_kabul_tutanagi(self, alim: Alim, kurum: Kurum, firma: Firma, veriler: dict) -> str:
        dosya_adi = self._dosya_adi_olustur("Hizmet_Isleri_Kabul_Tutanagi", alim.alim_no if alim.alim_no else str(alim.id))
        doc = Document()
        self._normal_stili_ayarla(doc, punto=11)

        section = doc.sections[0]
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)

        # Başlık
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("HİZMET İŞLERİ KABUL TUTANAĞI")
        run.bold = True
        run.font.size = Pt(14)
        run.font.name = "Times New Roman"

        doc.add_paragraph()

        # 1. Tablo (Bilgiler)
        table = doc.add_table(rows=5, cols=4)
        table.style = 'Table Grid'
        table.autofit = False
        table.columns[0].width = Cm(4)
        table.columns[1].width = Cm(6)
        table.columns[2].width = Cm(4)
        table.columns[3].width = Cm(4)

        def set_cell(cell, text, bold=False):
            cell.text = text
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(10)
                    r.bold = bold

        set_cell(table.cell(0, 0), "İşin adı", True)
        set_cell(table.cell(0, 1), alim.isin_niteligi)
        set_cell(table.cell(0, 2), "Yüklenicinin adı/ticari unvanı", True)
        set_cell(table.cell(0, 3), firma.unvan)

        set_cell(table.cell(1, 0), "Sözleşme tarihi", True)
        set_cell(table.cell(1, 1), veriler.get('sozlesme_tarihi', ''))
        set_cell(table.cell(1, 2), "Sözleşme bedeli", True)
        set_cell(table.cell(1, 3), f"{veriler.get('sozlesme_bedeli', 0):,.2f} TL")

        set_cell(table.cell(2, 0), "Sözleşmeye göre işin süresi (takvim günü)", True)
        set_cell(table.cell(2, 1), str(veriler.get('is_suresi', 0)))
        set_cell(table.cell(2, 2), "Sözleşmeye göre işin bitirilmesi gereken tarih", True)
        set_cell(table.cell(2, 3), veriler.get('is_bitis_tarihi', ''))

        set_cell(table.cell(3, 0), "Varsa süre uzatımları", True)
        set_cell(table.cell(3, 1), str(veriler.get('sure_uzatimi', 0)))
        set_cell(table.cell(3, 2), "Süre uzatımı dahil işin bitirilmesi gereken tarih", True)
        set_cell(table.cell(3, 3), veriler.get('uzatim_dahil_bitis', ''))

        set_cell(table.cell(4, 0), "İşin bitirildiği tarih", True)
        set_cell(table.cell(4, 1), veriler.get('isin_bitirildigi_tarih', ''))
        set_cell(table.cell(4, 2), "", False)
        set_cell(table.cell(4, 3), "", False)

        doc.add_paragraph()

        # Metin
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        
        p.add_run(f"{kurum.kurum_adi.upper()} ile yüklenici {firma.unvan.upper()} arasında imzalanan sözleşme kapsamında gerçekleştirilen iş tamamlandığı beyan edilmiş olup; ")
        p.add_run(f"{veriler.get('karar_tarihi', '')}").bold = True
        p.add_run(" tarihli ")
        p.add_run(f"{veriler.get('karar_turu', '')}").bold = True
        p.add_run(" ile ")
        
        # Komisyon Üyeleri
        komisyon = kurum.muayene_kabul_gorevlileri()
        komisyon_metni = ", ".join([f"{ad} ({unvan})" for ad, unvan in komisyon])
        p.add_run(komisyon_metni).bold = True
        p.add_run(" olmak üzere teşkil edilen MUAYENE VE KABUL KOMİSYONUMUZ, kontrol teşkilatı ve yüklenici ")
        p.add_run(firma.unvan).bold = True
        p.add_run(" de hazır olduğu halde ")
        p.add_run(f"{veriler.get('kabul_baslangic', '')}").bold = True
        p.add_run(" - ")
        p.add_run(f"{veriler.get('kabul_bitis', '')}").bold = True
        p.add_run(" tarihleri arasında işyerine (kabul için öngörülen yere) giderek yüklenici tarafından yapılmış işleri kabul bakımından incelemiş ve aşağıda yazılı hususları tespit etmiştir.")

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.add_run("Yapılan işin sözleşme ve eklerine uygun olduğu ve kabule engel olabilecek eksik, kusur ve arızaların bulunmadığı görülmüştür.")

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.add_run("ANCAK(1) ")
        p.add_run(veriler.get('ancak_notu', ''))

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.add_run("SONUÇ: Kabul bakımından muayene ve inceleme işlemlerinin yapılması görevi Komisyonumuza verilmiş bulunan söz konusu işin yukarıda belirtilen (varsa ayrıntıları veya gerekçeleri ekli sayfalarda sayılan ve gösterilen) kayıtlarla ve bitim tarihi de ")
        p.add_run(f"{veriler.get('isin_bitirildigi_tarih', '')}").bold = True
        p.add_run(" olarak itibar edilmek üzere kabulünün yapılması Komisyonumuzca uygun görülmüş ve ")
        p.add_run(veriler.get('makam_adi', 'OKUL MÜDÜRLÜĞÜ')).bold = True
        p.add_run(" Makamının onayına sunulmak üzere işbu Kabul Tutanağı manuel girilecek nüsha olarak düzenlenmiştir.")

        doc.add_paragraph()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.add_run(f"Tarih: {veriler.get('tutanak_tarihi', '')}")

        doc.add_paragraph()

        # İmzalar
        p = doc.add_paragraph()
        p.add_run("MUAYENE VE KABUL KOMİSYONU").bold = True
        
        for ad, unvan in komisyon:
            p = doc.add_paragraph()
            p.add_run(f"Başkan/Üye: {ad}\nUnvan: {unvan}\nİmza: \n\n")

        p = doc.add_paragraph()
        p.add_run("Yüklenicinin Adı, Soyadı veya ticaret unvanı ve İmzası").bold = True
        p = doc.add_paragraph()
        p.add_run(f"{firma.unvan}\nİmza: \n\n")

        p = doc.add_paragraph()
        p.add_run("Kabul Tutanağının onay tarihi").bold = True
        p = doc.add_paragraph()
        p.add_run(f"{veriler.get('tutanak_tarihi', '')}\n\n")
        
        p = doc.add_paragraph()
        p.add_run("Harcama Yetkilisi").bold = True
        p = doc.add_paragraph()
        p.add_run(f"{kurum.harcama_yetkilisi_ad}\n{kurum.harcama_yetkilisi_unvan}\nİmza:")

        p = doc.add_paragraph()
        p.add_run("\n(1) Buraya muayene ve kabul komisyonu üyelerinin düşünceleri ile varsa kusur ve noksanların kaç maddeden ibaret olduğu, tamamlanması için gereken süre yazılacaktır.").italic = True
        p.runs[0].font.size = Pt(9)

        doc.save(dosya_adi)
        return dosya_adi  
    def ekap_orijinal_sablon_doldur(self, alim: Alim, ekap_verileri: list, kaynak_dosya: str) -> str:
        if not ekap_verileri:
            raise ValueError("EKAP için aktarılacak kalem yok.")

        dosya_adi = self._dosya_adi_olustur("EKAP_Doldurulmus_Sablon", alim.alim_no if alim.alim_no else str(alim.id), "xls")
        self.ekap_uyarilar = []

        # Kullanıcının EKAP'tan indirdiği orijinal .xls dosyasını metin (XML) olarak oku
        try:
            with open(kaynak_dosya, "r", encoding="utf-8", errors="ignore") as f:
                d = f.read()
        except Exception as e:
            raise ValueError(f"Dosya okunamadı. Lütfen geçerli bir EKAP şablonu seçtiğinizden emin olun.\nHata: {e}")

        # Sayfa konumlarını bul
        s1 = d.find('<Worksheet ss:Name="Sheet1">')
        s2 = d.find('<Worksheet ss:Name="Sheet2">')
        s3 = d.find('<Worksheet ss:Name="Sheet3">')
        
        if min(s1, s2, s3) < 0:
            raise ValueError("Seçilen dosya geçerli bir EKAP şablonu değil (Sheet1/2/3 bulunamadı).")

        # Sheet3'ten listeleri oku (Birim, Para Birimi vb. için)
        L = self._ekap_listeleri_oku(d[s3:])

        # --- Eşleştirme yardımcıları ---
        def tr_lower(s):
            return str(s).replace("İ", "i").replace("I", "ı").lower().strip()

        para_map = {p.split(" ")[0].upper(): p for p in L["para"]}
        birim_map = {tr_lower(b): b for b in L["birim"]}
        okas_tam = set(L["okas"])
        okas_map = {}
        for o in L["okas"]:
            m = re.search(r"(\d+)\s*$", o)
            if m:
                okas_map[m.group(1)] = o

        def para_cevir(v):
            v = (v or "TRY").strip()
            return para_map.get(v.split(" ")[0].upper(), v)

        def birim_cevir(v):
            b = birim_map.get(tr_lower(v or ""))
            if not b:
                self.ekap_uyarilar.append(f"Birim EKAP listesinde yok: '{v}'")
            return b or (v or "")

        def okas_cevir(v):
            v = (v or "").strip()
            if not v or v in okas_tam:
                return v
            m = re.search(r"(\d+)\s*$", v)
            if m and m.group(1) in okas_map:
                return okas_map[m.group(1)]
            self.ekap_uyarilar.append(f"OKAS EKAP listesinde yok: '{v}'")
            return v

        def sayi(v):
            v = round(float(v or 0), 2)
            return str(int(v)) if v == int(v) else str(v)

        # ============================================================
        # SHEET 1: İŞ KALEMLERİ (Sadece burayı dolduruyoruz)
        # ============================================================
        seg1 = d[s1:s2]
        
        # Excel'in "Dosya bozuk" dememesi için Table satır sayısını güncelle
        table_match = re.search(r'<Table([^>]*)>', seg1)
        if table_match:
            table_attrs = table_match.group(1)
            new_row_count = len(ekap_verileri) + 1  # 1 Başlık + Ürünler
            
            if 'ss:ExpandedRowCount=' in table_attrs:
                table_attrs = re.sub(r'ss:ExpandedRowCount="\d+"', f'ss:ExpandedRowCount="{new_row_count}"', table_attrs)
            else:
                table_attrs += f' ss:ExpandedRowCount="{new_row_count}"'
            
            if 'ss:ExpandedColumnCount=' in table_attrs:
                table_attrs = re.sub(r'ss:ExpandedColumnCount="\d+"', 'ss:ExpandedColumnCount="10"', table_attrs)
            else:
                table_attrs += ' ss:ExpandedColumnCount="10"'
                
            seg1 = seg1.replace(table_match.group(0), f'<Table{table_attrs}>', 1)

        rows = re.findall(r'<Row.*?</Row>', seg1, re.S)
        if len(rows) < 2:
            raise ValueError("EKAP şablonunda (Sheet1) yeterli satır yok.")

        yeni_satirlar = []
        for item in ekap_verileri:
            mensei = item['mensei'] if item['mensei'] in L["mensei"] else "Bilinmiyor"
            degerler = [
                item['is_kalemi'], mensei, sayi(item['miktar']), birim_cevir(item['birim']),
                okas_cevir(item['okas']), sayi(item['toplam_fiyat']), para_cevir(item['para_birimi']),
                item['istekli']
            ]

            # Şablondaki 2. satırı (index 1) taslak olarak al
            sablon_satir = rows[1] 
            hucreler = list(re.finditer(r'<Cell[^>]*?(?:/>|>.*?</Cell>)', sablon_satir, re.S))
            
            yeni_satir = sablon_satir
            # Hücreleri değiştir (stilleri ve dropdown'ları koruyarak)
            for i in range(min(len(hucreler), len(degerler)) - 1, -1, -1):
                hucre = hucreler[i]
                val = degerler[i]
                
                hucre_tag_match = re.search(r'<Cell([^>]*?)(?:/>|>)', hucre.group(0))
                etiket = hucre_tag_match.group(1).rstrip('/') if hucre_tag_match else ""
                
                if val == "" or val is None:
                    yeni_hucre = f'<Cell{etiket}/>'
                else:
                    tip = "Number" if i in (2, 5) else "String"
                    yeni_hucre = f'<Cell{etiket}><Data ss:Type="{tip}">{escape(str(val))}</Data></Cell>'
                
                yeni_satir = yeni_satir[:hucre.start()] + yeni_hucre + yeni_satir[hucre.end():]

            yeni_satirlar.append(yeni_satir)

        # Sheet1'i yeniden inşa et (Başlık + Yeni Satırlar + Kalan XML)
        row1_end = seg1.find('</Row>') + 6 
        kalan_xml = seg1[seg1.rfind('</Row>') + 6:]
        
        seg1_yeni = seg1[:row1_end] + "\r\n   ".join(yeni_satirlar) + "\r\n  " + kalan_xml

        # ============================================================
        # BİRLEŞTİR VE KAYDET
        # ============================================================
        # d[s2:] diyerek Sheet2 ve Sheet3'ün orijinal (kullanıcının indirdiği) halini koruyoruz.
        yeni_xml = d[:s1] + seg1_yeni + d[s2:]
        
        with open(dosya_adi, "w", encoding="utf-8", newline="") as f:
            f.write(yeni_xml)
            
        return dosya_adi        