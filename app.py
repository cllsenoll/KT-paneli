import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# --- GENEL STİL TANIMLARI ---
DARK_BLUE = "1F4E78"
LIGHT_BLUE = "D9E1F2"
GRAY_HEADER = "595959"
GRAY_LIGHT = "F2F2F2"
WHITE = "FFFFFF"

font_header = Font(name="Calibri", size=11, bold=True, color=WHITE)
font_bold = Font(name="Calibri", size=11, bold=True)
font_regular = Font(name="Calibri", size=11)

fill_dark_blue = PatternFill(start_color=DARK_BLUE, end_color=DARK_BLUE, fill_type="solid")
fill_light_blue = PatternFill(start_color=LIGHT_BLUE, end_color=LIGHT_BLUE, fill_type="solid")
fill_gray_header = PatternFill(start_color=GRAY_HEADER, end_color=GRAY_HEADER, fill_type="solid")
fill_gray_light = PatternFill(start_color=GRAY_LIGHT, end_color=GRAY_LIGHT, fill_type="solid")

thin_border_side = Side(border_style="thin", color="D9D9D9")
thin_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
thick_bottom = Border(bottom=Side(border_style="medium", color="000000"))

align_center = Alignment(horizontal="center", vertical="center")
align_left = Alignment(horizontal="left", vertical="center")
align_right = Alignment(horizontal="right", vertical="center")


def apply_autofit_and_styles(ws):
    """Sütun genişliklerini otomatik ayarlar ve hücrelere varsayılan kenarlıkları uygular."""
    ws.views.sheetView[0].showGridLines = True
    for row in ws.iter_rows():
        for cell in row:
            if cell.value is not None and not cell.border.left.style:
                cell.border = thin_border

    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            # Birleştirilmiş hücrelerin genişlik çakışmasını önlemek için
            if cell.coordinate in ws.merged_cells:
                continue
            val_str = str(cell.value or '')
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)


# ==========================================
# 1. DOSYA: AT ZİMMET İZLEME.xlsx
# ==========================================
def generate_at_zimmet_izleme(df_raw, filename="AT_ZIMMET_IZLEME.xlsx"):
    wb = openpyxl.Workbook()
    
    # 1.1 Şube Performansı ve Kanal Dağılımı
    ws1 = wb.active
    ws1.title = "Şube Performansı"
    
    # Başlık
    ws1.merge_cells("A1:E1")
    ws1["A1"] = "ŞUBE PERFORMANSI VE KANAL DAĞILIMI"
    ws1["A1"].font = Font(name="Calibri", size=14, bold=True, color=WHITE)
    ws1["A1"].fill = fill_dark_blue
    ws1["A1"].alignment = align_center

    headers1 = ["Kanal / Metrik", "Toplam Adet", "Teslim Adet", "Kullanıcı İade", "Başarı Oranı (%)"]
    for col_idx, h in enumerate(headers1, start=1):
        cell = ws1.cell(row=3, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_gray_header
        cell.alignment = align_center

    # Örnek/Özet verilerin aktarımı (Varsayılan dinamik hesaplamalar)
    total_zimmet = len(df_raw) if not df_raw.empty else 0
    total_teslim = len(df_raw[df_raw['Durum'] == 'Teslim Edildi']) if 'Durum' in df_raw.columns else 0
    total_iade = len(df_raw[df_raw['Durum'] == 'İade']) if 'Durum' in df_raw.columns else 0
    
    metrics = [
        ["Saha / Kurye Dağıtımı", total_zimmet, total_teslim, total_iade, "=C4/B4"],
        ["Genel Toplam", "=SUM(B4:B4)", "=SUM(C4:C4)", "=SUM(D4:D4)", "=C5/B5"]
    ]
    
    for r_idx, row_data in enumerate(metrics, start=4):
        for c_idx, val in enumerate(row_data, start=1):
            cell = ws1.cell(row=r_idx, column=c_idx, value=val)
            cell.alignment = align_right if c_idx > 1 else align_left
            if r_idx == 5:
                cell.font = font_bold
                cell.fill = fill_light_blue
            if c_idx == 5:
                cell.number_format = "0.0%"

    # 1.2 Personel Bazlı Karşılaştırmalı Teslimat Grafiği (Veri Tabanı)
    ws2 = wb.create_sheet(title="Personel Grafiği Verileri")
    ws2.append(["Personel", "Teslimat Adedi", "Hedef"])
    if 'Personel' in df_raw.columns:
        p_counts = df_raw['Personel'].value_counts()
        for p_name, count in p_counts.items():
            ws2.append([p_name, count, 100]) # Örnek hedef: 100

    # 1.3 Genel Durum ve Performans
    ws3 = wb.create_sheet(title="Genel Durum")
    ws3.append(["Metrik", "Değer"])
    ws3.append(["Toplam Dağıtıma Çıkan", total_zimmet])
    ws3.append(["Toplam Teslim Edilen", total_teslim])
    ws3.append(["Genel Başarı Yüzdesi", f"={(total_teslim/total_zimmet)*100:.1f}%" if total_zimmet > 0 else "0%"])

    # 1.4 Personel Zimmet & Teslim Özeti Tablosu
    ws4 = wb.create_sheet(title="Zimmet & Teslim Özeti")
    ws4.append(["Personel Adı", "Zimmet Edilen Paket", "Teslim Edilen", "Kalan Paket", "Başarı Oranı"])
    if 'Personel' in df_raw.columns:
        summary = df_raw.groupby('Personel').size().reset_index(name='Zimmet')
        for _, row in summary.iterrows():
            ws4.append([row['Personel'], row['Zimmet'], 0, row['Zimmet'], "0.0%"])

    for ws in wb.worksheets:
        apply_autofit_and_styles(ws)
        
    wb.save(filename)
    print(f"{filename} başarıyla oluşturuldu.")


# ==========================================
# 2. DOSYA: PERSONEL HESAP ALIMI EKRANI.xlsx
# ==========================================
def generate_personel_hesap_alimi(df_raw, filename="PERSONEL_HESAP_ALIMI_EKRANI.xlsx"):
    wb = openpyxl.Workbook()
    
    # 2.1 Personel Hesap Alımı Ekranı
    ws1 = wb.active
    ws1.title = "Hesap Alımı Ekranı"
    
    ws1.merge_cells("A1:G1")
    ws1["A1"] = "PERSONEL HESAP ALIMI EKRANI"
    ws1["A1"].font = Font(name="Calibri", size=14, bold=True, color=WHITE)
    ws1["A1"].fill = fill_dark_blue
    ws1["A1"].alignment = align_center

    headers1 = ["Sıra", "Personel Adı Soyadı", "Nakit Tahsilat", "POS Tahsilat", "Toplam Tahsilat", "Teslim Edilen Adet", "Durum"]
    for c_idx, h in enumerate(headers1, start=1):
        cell = ws1.cell(row=3, column=c_idx, value=h)
        cell.font = font_header
        cell.fill = fill_gray_header
        cell.alignment = align_center

    start_row = 4
    if 'Personel' in df_raw.columns:
        personeller = df_raw['Personel'].unique()
        for idx, p in enumerate(personeller, start=1):
            r = start_row + idx - 1
            ws1.cell(row=r, column=1, value=idx).alignment = align_center
            ws1.cell(row=r, column=2, value=p).alignment = align_left
            ws1.cell(row=r, column=3, value=0.0).number_format = '#,##0.00 TL' # Nakit
            ws1.cell(row=r, column=4, value=0.0).number_format = '#,##0.00 TL' # POS
            
            # Toplam Tahsilat = Nakit + POS
            cell_tot = ws1.cell(row=r, column=5, value=f"=C{r}+D{r}")
            cell_tot.number_format = '#,##0.00 TL'
            cell_tot.font = font_bold
            
            ws1.cell(row=r, column=6, value=0).alignment = align_center
            ws1.cell(row=r, column=7, value="Tamamlandı").alignment = align_center

    end_row = start_row + (len(personeller) if 'Personel' in df_raw.columns else 1) - 1
    
    # --- İSTEDİĞİNİZ ÖZEL GÜNCELLEME ---
    # Altına Şube Genel Toplam Net Tahsilat yerine: Listede bulunan tüm Personellerin Toplam Tahsilat değerlerinin toplamı
    tot_row = end_row + 2
    ws1.cell(row=tot_row, column=2, value="PERSONELLER TOPLAM TAHSİLAT HESABI:").font = font_bold
    ws1.cell(row=tot_row, column=2).alignment = align_right
    
    # E sütunundaki (Toplam Tahsilat) tüm personel değerlerini toplayan SUM formülü
    sum_cell = ws1.cell(row=tot_row, column=5, value=f"=SUM(E{start_row}:E{end_row})")
    sum_cell.font = Font(name="Calibri", size=12, bold=True, color="006100")
    sum_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid") # Yeşil vurgu
    sum_cell.number_format = '#,##0.00 TL'

    # 2.2 Tüm Personellerin Hesap Alımı Özeti Tablosu
    ws2 = wb.create_sheet(title="Hesap Alımı Özeti")
    ws2.append(["Personel", "Nakit", "POS", "Genel Toplam"])
    if 'Personel' in df_raw.columns:
        for p in personeller:
            ws2.append([p, 0.0, 0.0, f"=B{ws2.max_row+1}+C{ws2.max_row+1}"])

    for ws in wb.worksheets:
        apply_autofit_and_styles(ws)

    wb.save(filename)
    print(f"{filename} başarıyla oluşturuldu.")


# ==========================================
# 3. DOSYA: F4 ÖDEME LİSTESİ.xlsx
# ==========================================
def generate_f4_odeme_listesi(df_raw, filename="F4_ODEME_LISTESI.xlsx"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "F4 Ödeme Listesi"

    ws.merge_cells("A1:F1")
    ws["A1"] = "F4 ÖDEME LİSTESİ (PERSONEL BAZLI SÜZGEÇ)"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color=WHITE)
    ws["A1"].fill = fill_dark_blue
    ws["A1"].alignment = align_center

    headers = ["Takip No", "Personel", "Alıcı Adı", "Ödeme Tipi", "Tutar", "Ödeme Durumu"]
    for c_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=c_idx, value=h)
        cell.font = font_header
        cell.fill = fill_gray_header
        cell.alignment = align_center

    # Ham veriden veri aktarımı
    if not df_raw.empty:
        for r_idx, row in df_raw.iterrows():
            row_num = r_idx + 4
            ws.cell(row=row_num, column=1, value=row.get('Takip No', f'TKP{r_idx+1}')).alignment = align_center
            ws.cell(row=row_num, column=2, value=row.get('Personel', 'Belirtilmedi')).alignment = align_left
            ws.cell(row=row_num, column=3, value=row.get('Alıcı', 'Müşteri')).alignment = align_left
            ws.cell(row=row_num, column=4, value=row.get('Ödeme Tipi', 'Nakit')).alignment = align_center
            
            c_tutar = ws.cell(row=row_num, column=5, value=float(row.get('Tutar', 0.0)))
            c_tutar.number_format = '#,##0.00 TL'
            c_tutar.alignment = align_right
            
            ws.cell(row=row_num, column=6, value=row.get('Ödeme Durumu', 'Tahsil Edildi')).alignment = align_center

    # Excel Otomatik Süzgeç (AutoFilter) Ekleme
    max_row = ws.max_row
    ws.auto_filter.ref = f"A3:F{max_row if max_row >= 4 else 4}"

    apply_autofit_and_styles(ws)
    wb.save(filename)
    print(f"{filename} başarıyla oluşturuldu.")


# ==========================================
# ÇALIŞTIRMA / TETİKLEME
# ==========================================
if __name__ == "__main__":
    # Örnek Test Verisi (Kendi veri kaynağınız / DataFrame'iniz ile değiştirebilirsiniz)
    raw_data = {
        'Takip No': ['TK1001', 'TK1002', 'TK1003', 'TK1004'],
        'Personel': ['Ahmet Yılmaz', 'Mehmet Demir', 'Ahmet Yılmaz', 'Ayşe Kaya'],
        'Durum': ['Teslim Edildi', 'Teslim Edildi', 'İade', 'Teslim Edildi'],
        'Alıcı': ['Ali Can', 'Veli Han', 'Ayşe Tan', 'Fatma Şen'],
        'Ödeme Tipi': ['Nakit', 'POS', 'Nakit', 'POS'],
        'Tutar': [150.00, 320.50, 0.00, 450.00],
        'Ödeme Durumu': ['Tahsil Edildi', 'Tahsil Edildi', 'İptal', 'Tahsil Edildi']
    }
    df = pd.DataFrame(raw_data)

    # Dosyaları ayrı ayrı üret
    generate_at_zimmet_izleme(df)
    generate_personel_hesap_alimi(df)
    generate_f4_odeme_listesi(df)
