import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io
import re

# Güncel Görsel Bağlantısı
LOGO_URL = "https://raw.githubusercontent.com/cllsenoll/KT-paneli/refs/heads/main/1000122774.png"

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Personel Performans & F4 Ödeme Paneli", 
    page_icon=LOGO_URL, 
    layout="centered"
)

# Özel Stil / CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #2563EB;
        color: white;
        font-weight: bold;
    }
    @media print {
        .stSidebar, .stButton, header, footer {
            display: none !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# --- Metin Normalleştirme & Boşluk Temizliği ---
def normalize_text(text):
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    # Aradaki birden fazla boşluğu tek boşluğa düşür ve kenar boşluklarını sil
    text = re.sub(r'\s+', ' ', text.strip()).lower()
    text = text.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
    text = text.replace('İ', 'i').replace('Ğ', 'g').replace('Ü', 'u').replace('Ş', 's').replace('Ö', 'o').replace('Ç', 'c')
    return text

# --- İLK 3 HARF BAZLI EŞLEŞTİRME ANAHTARI ---
def get_name_key(raw_name):
    """
    İsmin ilk 3 harfi ve soyismin (son kelimenin) ilk 3 harfini alarak anahtar oluşturur.
    Örn: "AHMET   YILMAZ" -> "ahm_yil"
    Örn: "Ahmet Yilmaz"   -> "ahm_yil"
    """
    norm = normalize_text(raw_name)
    if not norm:
        return ""
    
    parts = norm.split(' ')
    if len(parts) == 1:
        return parts[0][:3]
    
    first_part = parts[0][:3]
    last_part = parts[-1][:3]
    return f"{first_part}_{last_part}"

# --- ESNEK PERSONEL EŞLEŞTİRME FONKSİYONU ---
def match_personel_name(raw_name, existing_list):
    if pd.isna(raw_name) or str(raw_name).strip().lower() in ["nan", "none", "null", "toplam", ""]:
        return ""
        
    cleaned_raw = re.sub(r'\s+', ' ', str(raw_name).strip()).upper()
    raw_key = get_name_key(cleaned_raw)
    
    # Mevcut personel listesindeki isimlerle İlk 3 Harf anahtarını karşılaştır
    for p in existing_list:
        p_key = get_name_key(p)
        if raw_key and p_key and raw_key == p_key:
            return p  # Listedeki kayıtlı ismi döndür
            
    return cleaned_raw

# --- FATURA BORCU / TUTAR / SAYI DÖNÜŞTÜRÜCÜ ---
def parse_numeric_val(val):
    if pd.isna(val) or val is None:
        return 0.0
    
    if isinstance(val, (int, float)):
        return float(val)
        
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ['nan', 'none', 'null', '']:
        return 0.0

    val_str = val_str.replace('₺', '').replace('TL', '').replace('tl', '').strip()

    if ',' in val_str and '.' in val_str:
        val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        val_str = val_str.replace(',', '.')
        
    try:
        return float(val_str)
    except ValueError:
        return 0.0

# --- OTURUM BAŞLATMA ---
if "personeller" not in st.session_state:
    st.session_state.personeller = [
        "ALATTİN CEBECİ",
        "SUAT ARI",
        "HASAN SAĞLAM",
        "MEHMET KAYMAZ",
        "AHMET BERKAN ÖKSÜZ"
    ]

if "veriler" not in st.session_state:
    st.session_state.veriler = pd.DataFrame(columns=[
        "personel", "zimmet", "teslim_edildi", "teslim_edilmedi_bekletiliyor", "sms", "imza", "ks", "nakit", "kart",
        "nakit_ft_tutari_top", "nakit_odeme_tutari_top", "toplam_tahsilat"
    ])

if "tahsilatlar" not in st.session_state:
    st.session_state.tahsilatlar = pd.DataFrame(columns=[
        "Personel", "Müşteri Adı", "Fatura Borcu (₺)", "Açıklama"
    ])

# Üst Başlık ve Logo
col_logo, col_title = st.columns([1, 3])

with col_logo:
    st.image(LOGO_URL, width=90)

with col_title:
    st.title("Personel Performans & F4 Ödeme Paneli")
    st.caption("Çoklu Excel (At Zimmet / Kargo / F4 / Hesap Alımı) İşleme ve Otomatik Raporlama")

# --- SIDEBAR: PERSONEL YÖNETİMİ ---
with st.sidebar:
    st.header("⚙️ Personel Yönetimi")
    yeni_personel = st.text_input("Yeni Personel Adı Soyadı:")
    if st.button("➕ Personel Ekle"):
        if yeni_personel.strip():
            yeni_p_formatted = re.sub(r'\s+', ' ', yeni_personel.strip()).upper()
            
            # Eklenecek personel ismi mevcut listedeki biriyle anahtar bazlı eşleşiyor mu?
            matched = match_personel_name(yeni_p_formatted, st.session_state.personeller)
            if matched not in st.session_state.personeller:
                st.session_state.personeller.append(yeni_p_formatted)
                st.success(f"{yeni_p_formatted} eklendi!")
                st.rerun()
            else:
                st.warning(f"Bu personel ({matched}) zaten listede mevcut.")
        else:
            st.error("Lütfen geçerli bir isim girin.")

    st.markdown("---")
    if st.session_state.personeller:
        silinecek_personel = st.selectbox("Silinecek Personel Seçin:", st.session_state.personeller)
        if st.button("🗑️ Seçili Personeli Sil"):
            st.session_state.personeller.remove(silinecek_personel)
            st.success(f"{silinecek_personel} silindi!")
            st.rerun()

# 1. İbre Grafiği (Şube Teslim Oranı)
def ibre_grafik_ciz(teslim_edildi, bekletiliyor, zimmet, baslik_metni, alt_metin=""):
    basari_orani = (teslim_edildi / zimmet * 100) if zimmet > 0 else 0

    fig, ax = plt.subplots(figsize=(5, 3), subplot_kw={'projection': 'polar'})
    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#0E1117')

    theta_yesil = np.linspace(np.pi/2, np.pi, 100)
    theta_kirmizi = np.linspace(0, np.pi/2, 100)
    r = 1

    ax.plot(theta_yesil, [r]*100, color="#10B981", linewidth=16, alpha=0.3)
    ax.plot(theta_kirmizi, [r]*100, color="#EF4444", linewidth=16, alpha=0.3)

    doluluk_theta = np.linspace(np.pi, np.pi - (basari_orani / 100 * np.pi), 100)
    ax.plot(doluluk_theta, [r]*100, color="#10B981", linewidth=18)

    ax.set_theta_zero_location('W')
    ax.set_theta_direction(-1)
    ax.set_axis_off()

    ax.text(0, 0, f"%{basari_orani:.1f}", horizontalalignment='center', verticalalignment='center', fontsize=22, fontweight='bold', color='white')
    ax.text(0, -0.35, f"{alt_metin}\nZimmet: {zimmet} | Teslim: {teslim_edildi} | Bekleyen: {bekletiliyor}", horizontalalignment='center', verticalalignment='center', fontsize=9, color='#8B949E')

    return fig

# 2. Pasta Grafiği (Genel Kargo Teslimat Kanalları)
def pasta_grafigi_ciz(sms, imza, ks):
    etiketler = []
    degerler = []

    if sms > 0:
        etiketler.append(f"SMS\n({sms})")
        degerler.append(sms)
    if imza > 0:
        etiketler.append(f"İmza\n({imza})")
        degerler.append(imza)
    if ks > 0:
        etiketler.append(f"KS / Diğer\n({ks})")
        degerler.append(ks)

    if not degerler:
        fig, ax = plt.subplots(figsize=(4, 3))
        fig.patch.set_facecolor('#0E1117')
        ax.set_facecolor('#0E1117')
        ax.text(0.5, 0.5, "Kanal Verisi Yok", color="white", ha="center", va="center")
        ax.axis("off")
        return fig

    fig, ax = plt.subplots(figsize=(4, 3))
    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#0E1117')

    renkler = ['#3B82F6', '#10B981', '#F59E0B']
    wedges, texts, autotexts = ax.pie(
        degerler, 
        labels=etiketler, 
        autopct='%1.1f%%', 
        startangle=140, 
        colors=renkler[:len(degerler)],
        textprops=dict(color="white", fontsize=9)
    )

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_weight('bold')

    ax.set_title("Kargo Teslimat Kanalları Dağılımı", color="white", fontsize=11, fontweight="bold", pad=10)
    return fig

# 3. Personel Özel Teslimat Oranı Pasta Grafiği
def personel_pasta_grafigi_ciz(personel_adi, teslim_edildi, bekletiliyor):
    fig, ax = plt.subplots(figsize=(4, 3.2))
    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#0E1117')

    degerler = [teslim_edildi, bekletiliyor]
    etiketler = [f"Teslim Edildi\n({teslim_edildi})", f"Bekletiliyor\n({bekletiliyor})"]
    renkler = ['#10B981', '#EF4444']

    if sum(degerler) == 0:
        ax.text(0.5, 0.5, "Henüz Veri Yok", color="white", ha="center", va="center", fontsize=11)
        ax.axis("off")
        return fig

    wedges, texts, autotexts = ax.pie(
        degerler, 
        labels=etiketler, 
        autopct='%1.1f%%', 
        startangle=90, 
        colors=renkler,
        textprops=dict(color="white", fontsize=9)
    )

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_weight('bold')

    ax.set_title(f"{personel_adi}\nTeslimat Durum Dağılımı", color="white", fontsize=10, fontweight="bold", pad=10)
    return fig

# 4. Sütun Grafiği (Personel Bazlı Teslim / Bekleyen)
def sutun_grafigi_ciz(df_veriler):
    fig, ax = plt.subplots(figsize=(7, 3.5))
    fig.patch.set_facecolor('#0E1117')
    ax.set_facecolor('#0E1117')

    df_p = df_veriler.groupby("personel")[["teslim_edildi", "teslim_edilmedi_bekletiliyor"]].sum().reset_index()

    x = np.arange(len(df_p))
    width = 0.35

    rects1 = ax.bar(x - width/2, df_p["teslim_edildi"], width, label='Teslim Edildi', color='#10B981')
    rects2 = ax.bar(x + width/2, df_p["teslim_edilmedi_bekletiliyor"], width, label='Teslim Edilmedi / Bekletiliyor', color='#EF4444')

    ax.set_ylabel('Kargo Adedi', color='white')
    ax.set_title('Personel Bazlı Teslimat ve Bekleyen Dağılımı', color='white', fontweight='bold', pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(df_p["personel"], color='white', rotation=15, ha='right', fontsize=8)
    ax.tick_params(colors='white')
    ax.legend(facecolor='#1F2937', edgecolor='none', labelcolor='white')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#374151')
    ax.spines['left'].set_color('#374151')

    for rect in rects1:
        h = rect.get_height()
        if h > 0:
            ax.annotate(f'{int(h)}', xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', color='white', fontsize=8)

    for rect in rects2:
        h = rect.get_height()
        if h > 0:
            ax.annotate(f'{int(h)}', xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', color='white', fontsize=8)

    plt.tight_layout()
    return fig

# --- A4 DİKEY PDF OLUŞTURMA FONKSİYONU ---
def generate_pdf_bytes(df_input, personel_adi=""):
    fig, ax = plt.subplots(figsize=(8.27, 11.69))
    ax.axis('off')
    
    title_str = f"F4 ÖDEME LİSTESİ - {personel_adi.upper()}" if personel_adi else "F4 ÖDEME LİSTESİ"
    plt.title(title_str, fontsize=14, fontweight='bold', pad=30, y=0.98)
    
    table_data = [df_input.columns.tolist()] + df_input.values.tolist()
    table = ax.table(cellText=table_data, colLabels=None, loc='upper center', cellLoc='left')
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.8)
    
    for i in range(len(df_input.columns)):
        cell = table[(0, i)]
        cell.set_facecolor('#2563EB')
        cell.get_text().set_color('white')
        cell.get_text().set_weight('bold')

    buf = io.BytesIO()
    plt.savefig(buf, format='pdf', bbox_inches='tight', orientation='portrait')
    plt.close(fig)
    return buf.getvalue()

# ==========================================
# 📁 ÇOKLU EXCEL DOSYASI İLE OTOMATİK VERİ İŞLEME
# ==========================================
st.subheader("📁 Excel / CSV Dosyası Yükleme (Çoklu Dosya Destekli)")

uploaded_files = st.file_uploader(
    "At Zimmet İzleme, Kargo Dağıtım, F4 Ödeme veya Hesap Alımı Excel Dosyalarınızı Yükleyin (.xlsx, .xls veya .csv)", 
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=True
)

if uploaded_files:
    tum_f4_listesi = []
    kullanici_ozet_listesi = []

    for uploaded_file in uploaded_files:
        try:
            file_bytes = uploaded_file.getvalue()
            df_raw = None

            try:
                df_raw = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
            except Exception:
                try:
                    df_raw = pd.read_excel(io.BytesIO(file_bytes), engine="xlrd")
                except Exception:
                    try:
                        df_raw = pd.read_excel(io.BytesIO(file_bytes))
                    except Exception:
                        pass

            if df_raw is None:
                for enc in ["utf-8", "latin5", "iso-8859-9"]:
                    for sep in [";", ",", "\t"]:
                        try:
                            df_raw = pd.read_csv(io.BytesIO(file_bytes), sep=sep, encoding=enc, on_bad_lines="skip")
                            if len(df_raw.columns) > 1:
                                break
                        except Exception:
                            pass
                    if df_raw is not None and len(df_raw.columns) > 1:
                        break

            if df_raw is not None and not df_raw.empty:
                col_map = {}

                # 1. Aşama: FATURA BORCU VE NAKİT HESAP ALIMI SÜTUNLARINI TESPİT ETME
                fatura_col = None
                for c in df_raw.columns:
                    norm_c = normalize_text(c)
                    if "irsaliye" in norm_c:
                        continue
                    
                    if norm_c in ["fatura borcu", "fatura borcun", "faturaborcu", "fatura borcu (tl)", "fatura borcu (₺)"]:
                        fatura_col = c
                        break
                    elif "fatura" in norm_c and "borc" in norm_c:
                        fatura_col = c

                if not fatura_col:
                    for c in df_raw.columns:
                        norm_c = normalize_text(c)
                        if "irsaliye" in norm_c:
                            continue
                        if any(k in norm_c for k in ["fatura", "kapida odeme", "tahsilat tutari"]):
                            fatura_col = c
                            break

                if fatura_col:
                    col_map["fatura_borcu"] = fatura_col

                # NAKİT HESAP ALIMI SÜTUN TESPİTLERİ
                for c in df_raw.columns:
                    norm_c = normalize_text(c)
                    if "nakit ft" in norm_c and "tutari" in norm_c:
                        col_map["nakit_ft_tutari_top"] = c
                    elif "nakit odeme" in norm_c and "tutari" in norm_c:
                        col_map["nakit_odeme_tutari_top"] = c

                # 2. Aşama: DİĞER SÜTUNLARI VE AT ZİMMET SÜTUNLARINI TESPİT ETME
                for c in df_raw.columns:
                    norm_c = normalize_text(c)
                    
                    if any(k in norm_c for k in ["zimmet personel", "at zimmet", "kurye", "dagitici", "dağıtıcı", "personel", "kullanici"]):
                        if "zimmet_personel" not in col_map:
                            col_map["zimmet_personel"] = c

                    # AT ZİMMET İZLEME / ÖZET TABLO SÜTUN TESPİTLERİ
                    if any(k in norm_c for k in ["zimmet adet", "zimmet sayi", "toplam zimmet", "at zimmet adet", "zimmetteki"]):
                        col_map["summary_zimmet"] = c
                    elif any(k in norm_c for k in ["teslim edilen", "teslim sayi", "teslim edilen adet", "teslim adet"]):
                        col_map["summary_teslim"] = c
                    elif any(k in norm_c for k in ["bekletilen", "bekleyen", "kalan", "teslim edilmeyen"]):
                        col_map["summary_bekleyen"] = c

                    # SATIR BAZLI SÜTUN TESPİTLERİ
                    elif any(k in norm_c for k in ["teslim durumu", "kargo durumu", "son durum", "durum", "teslimat durumu"]):
                        col_map["durum"] = c
                    elif any(k in norm_c for k in ["teslimat kanali", "kanal", "teslim tipi"]):
                        col_map["kanal"] = c
                    elif "aciklama" in norm_c or "açıklama" in norm_c:
                        col_map["aciklama"] = c
                    elif any(k in norm_c for k in ["musteri adi", "musteri", "alici", "alici adi", "firma", "unvan"]):
                        col_map["musteri_adi"] = c
                    elif any(k in norm_c for k in ["odeme tipi", "odeme türü", "tahsilat tipi", "odeme karsi"]):
                        col_map["odeme_tipi"] = c

                if "zimmet_personel" in col_map:
                    df = df_raw.copy()
                    df["zimmet_personel"] = df[col_map["zimmet_personel"]].astype(str).str.strip()

                    # ÖZET İZLEME TABLOSU MU (AT ZİMMET İZLEME EXCEL'İ) YOKSA SATIR BAZLI MÜŞTERİ LİSTESİ Mİ?
                    is_summary_excel = "summary_zimmet" in col_map or ("summary_teslim" in col_map and "durum" not in col_map) or ("nakit_ft_tutari_top" in col_map or "nakit_odeme_tutari_top" in col_map)

                    if is_summary_excel:
                        # AT ZİMMET İZLEME VEYA HESAP ALIMI ÖZET EXCEL İŞLEME
                        for _, row in df.iterrows():
                            raw_p = row["zimmet_personel"]
                            if str(raw_p).lower() in ["nan", "", "none", "null", "toplam"]:
                                continue

                            matched_p = match_personel_name(raw_p, st.session_state.personeller)
                            if not matched_p:
                                continue

                            z_val = int(parse_numeric_val(row[col_map["summary_zimmet"]])) if "summary_zimmet" in col_map else 0
                            t_val = int(parse_numeric_val(row[col_map["summary_teslim"]])) if "summary_teslim" in col_map else 0
                            b_val = int(parse_numeric_val(row[col_map["summary_bekleyen"]])) if "summary_bekleyen" in col_map else (z_val - t_val if z_val >= t_val else 0)

                            # HESAP ALIMI NAKİT TOPLAMLARI
                            nft_val = parse_numeric_val(row[col_map["nakit_ft_tutari_top"]]) if "nakit_ft_tutari_top" in col_map else 0.0
                            nod_val = parse_numeric_val(row[col_map["nakit_odeme_tutari_top"]]) if "nakit_odeme_tutari_top" in col_map else 0.0
                            toplam_tahsilat_val = nft_val + nod_val

                            kullanici_ozet_listesi.append({
                                "personel": matched_p,
                                "zimmet": z_val,
                                "teslim_edildi": t_val,
                                "teslim_edilmedi_bekletiliyor": b_val,
                                "sms": 0,
                                "imza": 0,
                                "ks": 0,
                                "nakit": 0.0,
                                "kart": 0.0,
                                "nakit_ft_tutari_top": nft_val,
                                "nakit_odeme_tutari_top": nod_val,
                                "toplam_tahsilat": toplam_tahsilat_val
                            })

                            if matched_p not in st.session_state.personeller:
                                st.session_state.personeller.append(matched_p)

                    else:
                        # SATIR BAZLI DETAYLI EXCEL (KARGO / F4) İŞLEME
                        df["durum"] = df[col_map["durum"]].astype(str).str.strip() if "durum" in col_map else "Teslim Edildi"
                        df["kanal"] = df[col_map["kanal"]].astype(str).str.strip() if "kanal" in col_map else ""
                        df["musteri_adi"] = df[col_map["musteri_adi"]].astype(str).str.strip() if "musteri_adi" in col_map else ""
                        df["odeme_tipi"] = df[col_map["odeme_tipi"]].astype(str).str.strip() if "odeme_tipi" in col_map else ""

                        if "aciklama" in col_map:
                            df["aciklama"] = df[col_map["aciklama"]].astype(str).str.strip()
                            df["aciklama"] = df["aciklama"].apply(lambda x: "" if str(x).lower() in ["nan", "none", "null"] else str(x))
                        else:
                            df["aciklama"] = ""

                        if "fatura_borcu" in col_map:
                            df["fatura_borcu"] = df[col_map["fatura_borcu"]].apply(parse_numeric_val)
                        else:
                            df["fatura_borcu"] = 0.0

                        personeller = df["zimmet_personel"].unique()

                        for raw_p in personeller:
                            if str(raw_p).lower() in ["nan", "", "none", "null", "toplam"]:
                                continue
                            
                            matched_p = match_personel_name(raw_p, st.session_state.personeller)
                            if not matched_p:
                                continue
                            
                            p_df = df[df["zimmet_personel"] == raw_p]
                            zimmet_sayisi = len(p_df)

                            teslim_edildi_sayisi = 0
                            teslim_edilmedi_bekletiliyor_sayisi = 0

                            sms_sayisi, imza_sayisi, ks_sayisi = 0, 0, 0
                            auto_nakit, auto_kart = 0.0, 0.0

                            for _, row in p_df.iterrows():
                                norm_durum = normalize_text(row["durum"])
                                is_teslim = any(k in norm_durum for k in ["teslim edildi", "teslimat yapildi", "teslim yapildi", "teslimdir"]) or norm_durum in ["teslim", ""]
                                
                                borc_val = float(row["fatura_borcu"])
                                musteri_val = str(row["musteri_adi"]) if row["musteri_adi"] and str(row["musteri_adi"]).lower() not in ["nan", "none", ""] else "Müşteri Belirtilmedi"
                                odeme_tipi_val = normalize_text(row["odeme_tipi"])
                                aciklama_val = str(row["aciklama"])

                                if is_teslim:
                                    teslim_edildi_sayisi += 1
                                    kanal_val = str(row["kanal"]).upper()

                                    if "SMS" in kanal_val:
                                        sms_sayisi += 1
                                    elif "İMZA" in kanal_val or "IMZA" in kanal_val:
                                        imza_sayisi += 1
                                    else:
                                        ks_sayisi += 1

                                    if "nakit" in odeme_tipi_val or "nakıt" in odeme_tipi_val:
                                        auto_nakit += borc_val
                                    elif any(k in odeme_tipi_val for k in ["kart", "pos", "kredi"]):
                                        auto_kart += borc_val
                                else:
                                    teslim_edilmedi_bekletiliyor_sayisi += 1

                                if borc_val > 0 or musteri_val != "Müşteri Belirtilmedi":
                                    tum_f4_listesi.append({
                                        "Personel": matched_p,
                                        "Müşteri Adı": musteri_val,
                                        "Fatura Borcu (₺)": borc_val,
                                        "Açıklama": aciklama_val
                                    })

                            kullanici_ozet_listesi.append({
                                "personel": matched_p,
                                "zimmet": zimmet_sayisi,
                                "teslim_edildi": teslim_edildi_sayisi,
                                "teslim_edilmedi_bekletiliyor": teslim_edilmedi_bekletiliyor_sayisi,
                                "sms": sms_sayisi,
                                "imza": imza_sayisi,
                                "ks": ks_sayisi,
                                "nakit": auto_nakit,
                                "kart": auto_kart,
                                "nakit_ft_tutari_top": 0.0,
                                "nakit_odeme_tutari_top": 0.0,
                                "toplam_tahsilat": auto_nakit
                            })

                            if matched_p not in st.session_state.personeller:
                                st.session_state.personeller.append(matched_p)

        except Exception as e:
            st.error(f"{uploaded_file.name} işlenirken hata oluştu: {e}")

    if kullanici_ozet_listesi:
        st.session_state.veriler = pd.DataFrame(kullanici_ozet_listesi)
    if tum_f4_listesi:
        st.session_state.tahsilatlar = pd.DataFrame(tum_f4_listesi)
    
    st.success("✅ Yüklenen tüm Excel dosyaları başarıyla okundu ve veriler güncellendi!")

st.markdown("---")

df_veriler = st.session_state.veriler
df_tahsilat = st.session_state.tahsilatlar
personel_listesi = st.session_state.personeller

# ==========================================
# 1. ŞUBE TESLİM ORANI VE KANAL DAĞILIMI (GRAFİKLER)
# ==========================================
st.markdown("### 🎯 Şube Performansı ve Kanal Dağılımı")

toplam_zimmet = int(df_veriler["zimmet"].sum()) if not df_veriler.empty else 0
toplam_teslim_edildi = int(df_veriler["teslim_edildi"].sum()) if not df_veriler.empty else 0
toplam_teslim_edilmedi_bekletiliyor = int(df_veriler["teslim_edilmedi_bekletiliyor"].sum()) if not df_veriler.empty else 0

toplam_sms = int(df_veriler["sms"].sum()) if not df_veriler.empty else 0
toplam_imza = int(df_veriler["imza"].sum()) if not df_veriler.empty else 0
toplam_ks = int(df_veriler["ks"].sum()) if not df_veriler.empty else 0

col_g1, col_g2 = st.columns([1, 1])

with col_g1:
    fig_sube = ibre_grafik_ciz(toplam_teslim_edildi, toplam_teslim_edilmedi_bekletiliyor, toplam_zimmet, "Şube Teslim Oranı", "Genel Performans")
    st.pyplot(fig_sube)

with col_g2:
    fig_pasta = pasta_grafigi_ciz(toplam_sms, toplam_imza, toplam_ks)
    st.pyplot(fig_pasta)

# PERSONEL BAZLI TESLİMAT SÜTUN GRAFİĞİ
if not df_veriler.empty and df_veriler["zimmet"].sum() > 0:
    st.markdown("#### 📊 Personel Bazlı Karşılaştırmalı Teslimat Grafiği")
    fig_sutun = sutun_grafigi_ciz(df_veriler)
    st.pyplot(fig_sutun)

st.markdown("---")

# ==========================================
# 2. GENEL DURUM VE PERFORMANS (KPİ & ÖZET TABLO)
# ==========================================
st.subheader("📊 Genel Durum ve Performans")

toplam_nakit = float(df_veriler["nakit"].sum()) if not df_veriler.empty else 0.0
toplam_kart = float(df_veriler["kart"].sum()) if not df_veriler.empty else 0.0
toplam_tahsilat = toplam_nakit + toplam_kart

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Toplam Teslim Edildi", f"{toplam_teslim_edildi} Adet")
kpi2.metric("Teslim Edilmedi / Bekletiliyor", f"{toplam_teslim_edilmedi_bekletiliyor} Adet")
kpi3.metric("Toplam Fatura Borcu", f"{toplam_tahsilat:,.2f} ₺")

# PERSONEL BAZLI ÖZEL ANALİZ (YÜZDELİK VE PASTA GRAFİĞİ)
st.markdown("#### 👤 Personel Bazlı Özel Teslimat Analizi")

if personel_listesi:
    secili_p_analiz = st.selectbox("Analiz Edilecek Personeli Seçin:", personel_listesi, key="analiz_personel_select")
    
    p_zimmet = 0
    p_teslim = 0
    p_bekleyen = 0

    if not df_veriler.empty:
        p_df = df_veriler[df_veriler["personel"] == secili_p_analiz]
        if not p_df.empty:
            p_zimmet = int(p_df["zimmet"].sum())
            p_teslim = int(p_df["teslim_edildi"].sum())
            p_bekleyen = int(p_df["teslim_edilmedi_bekletiliyor"].sum())

    p_yuzde = (p_teslim / p_zimmet * 100) if p_zimmet > 0 else 0.0

    col_p_info, col_p_chart = st.columns([1.2, 1])

    with col_p_info:
        st.markdown(f"**{secili_p_analiz}** Detaylı Performans Verileri:")
        st.metric("Teslimat Başarı Oranı", f"%{p_yuzde:.1f}")
        
        c_k1, c_k2, c_k3 = st.columns(3)
        c_k1.metric("Zimmet", f"{p_zimmet}")
        c_k2.metric("Teslim", f"{p_teslim}")
        c_k3.metric("Bekleyen", f"{p_bekleyen}")

    with col_p_chart:
        fig_p_pasta = personel_pasta_grafigi_ciz(secili_p_analiz, p_teslim, p_bekleyen)
        st.pyplot(fig_p_pasta)

# Personel Bazlı Performans Özeti Tablosu
if not df_veriler.empty:
    st.markdown("#### 👥 Personel Zimmet & Teslim Özeti Tablosu")
    df_ozet_goster = df_veriler.groupby("personel")[["zimmet", "teslim_edildi", "teslim_edilmedi_bekletiliyor", "sms", "imza", "ks"]].sum().reset_index()
    df_ozet_goster.columns = ["Personel", "Zimmet Adedi", "Teslim Edilen", "Bekleyen", "SMS", "İmza", "KS/Diğer"]
    st.dataframe(df_ozet_goster, use_container_width=True)

st.markdown("---")

# ==========================================
# 3. PERSONEL HESAP ALIMI EKRANI
# ==========================================
st.subheader("💵 Personel Hesap Alımı Ekranı")

if not df_veriler.empty and "toplam_tahsilat" in df_veriler.columns:
    df_hesap = df_veriler.groupby("personel")[["nakit_ft_tutari_top", "nakit_odeme_tutari_top", "toplam_tahsilat"]].sum().reset_index()
    
    genel_toplam_tahsilat = df_hesap["toplam_tahsilat"].sum()
    st.info(f"💵 **Şube Genel Toplam Nakit Tahsilat:** {genel_toplam_tahsilat:,.2f} ₺")

    if personel_listesi:
        hesap_p_secim = st.selectbox("Hesap Alımı Yapılacak Personeli Seçin:", personel_listesi, key="hesap_p_select")
        
        p_hesap_df = df_hesap[df_hesap["personel"] == hesap_p_secim]

        if not p_hesap_df.empty:
            nft = float(p_hesap_df["nakit_ft_tutari_top"].values[0])
            nod = float(p_hesap_df["nakit_odeme_tutari_top"].values[0])
            top_tah = float(p_hesap_df["toplam_tahsilat"].values[0])

            st.markdown(f"**{hesap_p_secim}** Günlük Tahsilat Detayı:")
            
            h_col1, h_col2, h_col3 = st.columns(3)
            h_col1.metric("Nakit Ft. Tutarı Top.", f"{nft:,.2f} ₺")
            h_col2.metric("Nakit Ödeme Tutarı Topl.", f"{nod:,.2f} ₺")
            h_col3.metric("Toplam Tahsilat", f"{top_tah:,.2f} ₺")

        st.markdown("#### 📋 Tüm Personellerin Hesap Alım Özeti Tablosu")
        df_hesap_goster = df_hesap.copy()
        df_hesap_goster.columns = ["Personel", "Nakit Ft. Tutarı Top. (₺)", "Nakit Ödeme Tutarı Topl. (₺)", "Toplam Tahsilat (₺)"]
        st.dataframe(df_hesap_goster, use_container_width=True)
else:
    st.info("Hesap Alımı verilerini görmek için lütfen içerisinde 'Nakit Ft. Tutarı Top' ve 'Nakit Ödeme Tutarı Topl.' alanları bulunan Excel dosyanızı yükleyin.")

st.markdown("---")

# ==========================================
# 4. F4 ÖDEME LİSTESİ (PERSONEL BAZLI OTOMATİK LİSTELEME)
# ==========================================
st.subheader("📋 F4 Ödeme Listesi")

if personel_listesi:
    f4_personel_secim = st.selectbox("F4 Ödeme Listesini Görmek İstediğiniz Personel:", personel_listesi, key="f4_personel_select")

    if not df_tahsilat.empty and "Personel" in df_tahsilat.columns:
        p_f4_df = df_tahsilat[df_tahsilat["Personel"] == f4_personel_secim]

        if not p_f4_df.empty:
            df_f4_goster = p_f4_df[["Müşteri Adı", "Fatura Borcu (₺)", "Açıklama"]].reset_index(drop=True)
            df_f4_goster.index = range(1, len(df_f4_goster) + 1)
            
            st.markdown(f"**{f4_personel_secim}** için tanımlı **F4 Ödeme Listesi**:")
            st.dataframe(df_f4_goster, use_container_width=True)

            toplam_f4_borc = df_f4_goster["Fatura Borcu (₺)"].sum()
            st.info(f"💰 **{f4_personel_secim} Toplam Fatura Borcu:** {toplam_f4_borc:,.2f} ₺")

            col_pdf, col_excel = st.columns(2)
            
            with col_pdf:
                pdf_bytes = generate_pdf_bytes(df_f4_goster, f4_personel_secim)
                st.download_button(
                    label="📄 F4 Ödeme Listesini PDF İndir",
                    data=pdf_bytes,
                    file_name=f"F4_Odeme_Listesi_{f4_personel_secim.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )

            with col_excel:
                excel_csv = df_f4_goster.to_csv(index=True, encoding='utf-8-sig')
                st.download_button(
                    label="📥 F4 Ödeme Listesini Excel/CSV İndir",
                    data=excel_csv,
                    file_name=f"F4_Odeme_Listesi_{f4_personel_secim.replace(' ', '_')}.csv",
                    mime="text/csv"
                )
        else:
            st.warning(f"⚠️ {f4_personel_secim} için yüklenen Excel dosyalarında F4 kaydı bulunamadı.")
    else:
        st.info("Henüz F4 Ödeme kaydı içeren bir dosya yüklenmedi.")

st.markdown("---")

# ==========================================
# 5. MANUEL F4 KAYDI EKLEME
# ==========================================
st.subheader("➕ Manuel F4 Kaydı Ekle")

with st.form("manual_f4_form"):
    p_sec = st.selectbox("Personel:", personel_listesi, key="manual_p_sec")
    c_m1, c_m2, c_m3 = st.columns([2, 1.5, 2.5])
    with c_m1:
        m_adi_in = st.text_input("Müşteri Adı:")
    with c_m2:
        m_borc_in = st.number_input("Fatura Borcu (₺):", min_value=0.0, step=10.0)
    with c_m3:
        m_ack_in = st.text_input("Açıklama:")

    f4_add_btn = st.form_submit_button("💾 F4 Kaydını Ekle")

if f4_add_btn:
    if m_adi_in.strip():
        yeni_f4 = {
            "Personel": p_sec,
            "Müşteri Adı": m_adi_in.strip(),
            "Fatura Borcu (₺)": m_borc_in,
            "Açıklama": m_ack_in.strip()
        }
        st.session_state.tahsilatlar = pd.concat([st.session_state.tahsilatlar, pd.DataFrame([yeni_f4])], ignore_index=True)
        st.success(f"✓ {m_adi_in} kaydı {p_sec} için eklendi.")
        st.rerun()
    else:
        st.error("Lütfen Müşteri Adı alanını doldurun.")
