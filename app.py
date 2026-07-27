import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io

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

# --- Metin Normalleştirme ---
def normalize_text(text):
    text = str(text).strip().lower()
    text = text.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
    text = text.replace('İ', 'i').replace('Ğ', 'g').replace('Ü', 'u').replace('Ş', 's').replace('Ö', 'o').replace('Ç', 'c')
    return text

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
        "personel", "zimmet", "teslim_edildi", "teslim_edilmedi_bekletiliyor", "sms", "imza", "ks", "nakit", "kart"
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
    st.caption("Çoklu Excel (At Zimmet / Kargo / F4) İşleme ve Otomatik Raporlama")

# --- SIDEBAR: PERSONEL YÖNETİMİ ---
with st.sidebar:
    st.header("⚙️ Personel Yönetimi")
    yeni_personel = st.text_input("Yeni Personel Adı Soyadı:")
    if st.button("➕ Personel Ekle"):
        if yeni_personel.strip():
            yeni_p_upper = yeni_personel.strip().upper()
            if yeni_p_upper not in st.session_state.personeller:
                st.session_state.personeller.append(yeni_p_upper)
                st.success(f"{yeni_p_upper} eklendi!")
                st.rerun()
            else:
                st.warning("Bu personel zaten listede var.")
        else:
            st.error("Lütfen geçerli bir isim girin.")

    st.markdown("---")
    if st.session_state.personeller:
        silinecek_personel = st.selectbox("Silinecek Personel Seçin:", st.session_state.personeller)
        if st.button("🗑️ Seçili Personeli Sil"):
            st.session_state.personeller.remove(silinecek_personel)
            st.success(f"{silinecek_personel} silindi!")
            st.rerun()

# İbre Grafiği
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

# Esnek Personel Adı Eşleştirme Fonksiyonu
def match_personel_name(raw_name, existing_list):
    norm_raw = normalize_text(raw_name)
    for p in existing_list:
        if normalize_text(p) == norm_raw:
            return p
    return str(raw_name).strip().upper()

# ==========================================
# 📁 ÇOKLU EXCEL DOSYASI İLE OTOMATİK VERİ İŞLEME
# ==========================================
st.subheader("📁 Excel / CSV Dosyası Yükleme (Çoklu Dosya Destekli)")

uploaded_files = st.file_uploader(
    "At Zimmet İzleme, Kargo Dağıtım veya F4 Ödeme Excel Dosyalarınızı Yükleyin (.xlsx, .xls veya .csv)", 
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

                # 1. Aşama: FATURA BORCU SÜTUNUNU İRSALİYE'DEN AYIRARAK TESPİT ETME
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
                    is_summary_excel = "summary_zimmet" in col_map or ("summary_teslim" in col_map and "durum" not in col_map)

                    if is_summary_excel:
                        # AT ZİMMET İZLEME ÖZET EXCEL İŞLEME
                        for _, row in df.iterrows():
                            raw_p = row["zimmet_personel"]
                            if str(raw_p).lower() in ["nan", "", "none", "null", "toplam"]:
                                continue

                            matched_p = match_personel_name(raw_p, st.session_state.personeller)
                            
                            z_val = int(parse_numeric_val(row[col_map["summary_zimmet"]])) if "summary_zimmet" in col_map else 0
                            t_val = int(parse_numeric_val(row[col_map["summary_teslim"]])) if "summary_teslim" in col_map else 0
                            b_val = int(parse_numeric_val(row[col_map["summary_bekleyen"]])) if "summary_bekleyen" in col_map else (z_val - t_val if z_val >= t_val else 0)

                            kullanici_ozet_listesi.append({
                                "personel": matched_p,
                                "zimmet": z_val,
                                "teslim_edildi": t_val,
                                "teslim_edilmedi_bekletiliyor": b_val,
                                "sms": 0,
                                "imza": 0,
                                "ks": 0,
                                "nakit": 0.0,
                                "kart": 0.0
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
                                "kart": auto_kart
                            })

                            if matched_p not in st.session_state.personeller:
                                st.session_state.personeller.append(matched_p)

        except Exception as e:
            st.error(f"{uploaded_file.name} işlenirken hata oluştu: {e}")

    if kullanici_ozet_listesi:
        st.session_state.veriler = pd.DataFrame(kullanici_ozet_listesi)
    if tum_f4_listesi:
        st.session_state.tahsilatlar = pd.DataFrame(tum_f4_listesi)
    
    st.success("✅ Yüklenen tüm Excel dosyaları (At Zimmet / F4 / Kargo) başarıyla okundu ve veriler güncellendi!")

st.markdown("---")

df_veriler = st.session_state.veriler
df_tahsilat = st.session_state.tahsilatlar
personel_listesi = st.session_state.personeller

# ==========================================
# 1. ŞUBE TESLİM ORANI
# ==========================================
st.markdown("### 🎯 Şube Teslim Oranı")

toplam_zimmet = int(df_veriler["zimmet"].sum()) if not df_veriler.empty else 0
toplam_teslim_edildi = int(df_veriler["teslim_edildi"].sum()) if not df_veriler.empty else 0
toplam_teslim_edilmedi_bekletiliyor = int(df_veriler["teslim_edilmedi_bekletiliyor"].sum()) if not df_veriler.empty else 0

fig_sube = ibre_grafik_ciz(toplam_teslim_edildi, toplam_teslim_edilmedi_bekletiliyor, toplam_zimmet, "Şube Teslim Oranı", "Şube Genel Performansı")
st.pyplot(fig_sube)

st.markdown("---")

# ==========================================
# 2. GENEL DURUM VE PERFORMANS
# ==========================================
st.subheader("📊 Genel Durum ve Performans")

toplam_nakit = float(df_veriler["nakit"].sum()) if not df_veriler.empty else 0.0
toplam_kart = float(df_veriler["kart"].sum()) if not df_veriler.empty else 0.0
toplam_tahsilat = toplam_nakit + toplam_kart

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Toplam Teslim Edildi", f"{toplam_teslim_edildi} Adet")
kpi2.metric("Teslim Edilmedi / Bekletiliyor", f"{toplam_teslim_edilmedi_bekletiliyor} Adet")
kpi3.metric("Toplam Fatura Borcu", f"{toplam_tahsilat:,.2f} ₺")

# Personel Bazlı Performans Özeti Tablosu
if not df_veriler.empty:
    st.markdown("#### 👥 Personel Zimmet & Teslim Özeti")
    df_ozet_goster = df_veriler.groupby("personel")[["zimmet", "teslim_edildi", "teslim_edilmedi_bekletiliyor"]].sum().reset_index()
    df_ozet_goster.columns = ["Personel", "Zimmet Adedi", "Teslim Edilen", "Bekleyen"]
    st.dataframe(df_ozet_goster, use_container_width=True)

st.markdown("---")

# ==========================================
# 3. F4 ÖDEME LİSTESİ (PERSONEL BAZLI OTOMATİK LİSTELEME)
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
# 4. MANUEL F4 KAYDI EKLEME
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
