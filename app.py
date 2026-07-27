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

# --- Metin Normalleştirme ---
def normalize_text(text):
    text = str(text).strip().lower()
    text = text.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
    return text

# --- Tutar Dönüştürme Fonksiyonu ---
def parse_currency_val(val):
    if pd.isna(val) or val is None:
        return 0.0
    
    val_str = str(val).replace('\xa0', ' ').strip()
    val_str = re.sub(r'[^\d.,\-]', '', val_str)
    
    if not val_str:
        return 0.0
    
    if ',' in val_str and '.' in val_str:
        val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        val_str = val_str.replace(',', '.')
        
    try:
        return float(val_str)
    except ValueError:
        return 0.0

# --- Başlık Satırını Düzeltme ---
def fix_excel_header(df_raw):
    # Eğer ilk satırlar boşsa veya başlık alt satırdaysa tara
    for idx in range(min(15, len(df_raw))):
        row_vals = [normalize_text(v) for v in df_raw.iloc[idx].values if pd.notna(v)]
        if len(row_vals) > 2:
            # Mantıklı bir tablo başlığı satırı bulursak onu header yap
            if any(k in " ".join(row_vals) for k in ["personel", "kurye", "zimmet", "borc", "tutar", "musteri", "alici", "firma", "fatura"]):
                new_df = df_raw.iloc[idx+1:].copy()
                new_df.columns = df_raw.iloc[idx].values
                return new_df.reset_index(drop=True)
    return df_raw

# --- OTURUM BAŞLATMA ---
if "personeller" not in st.session_state:
    st.session_state.personeller = [
        "Ahmet Berkan Öksüz",
        "Alattin Cebeci",
        "Hasan Sağlam",
        "Mehmet Kaymaz",
        "Suat Arı"
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
    st.caption("Gelişmiş Sütun Eşleştirme ve F4 Ödeme Raporlama")

# --- SIDEBAR: PERSONEL YÖNETİMİ ---
with st.sidebar:
    st.header("⚙️ Personel Yönetimi")
    yeni_personel = st.text_input("Yeni Personel Adı Soyadı:")
    if st.button("➕ Personel Ekle"):
        if yeni_personel.strip():
            if yeni_personel.strip() not in st.session_state.personeller:
                st.session_state.personeller.append(yeni_personel.strip())
                st.success(f"{yeni_personel.strip()} eklendi!")
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

# PDF Oluşturma
def generate_pdf_bytes(df_input, personel_adi=""):
    fig, ax = plt.subplots(figsize=(8.5, max(len(df_input) * 0.4 + 2, 3)))
    ax.axis('tight')
    ax.axis('off')
    
    title_str = f"F4 ÖDEME LİSTESİ - {personel_adi.upper()}" if personel_adi else "F4 ÖDEME LİSTESİ"
    plt.title(title_str, fontsize=14, fontweight='bold', pad=20)
    
    table_data = [df_input.columns.tolist()] + df_input.values.tolist()
    table = ax.table(cellText=table_data, colLabels=None, loc='center', cellLoc='left')
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)
    
    for i in range(len(df_input.columns)):
        cell = table[(0, i)]
        cell.set_facecolor('#2563EB')
        cell.get_text().set_color('white')
        cell.get_text().set_weight('bold')

    buf = io.BytesIO()
    plt.savefig(buf, format='pdf', bbox_inches='tight')
    plt.close(fig)
    return buf.getvalue()

# ==========================================
# 📁 DOSYA YÜKLEME VE İNTERAKTİF SÜTUN EŞLEŞTİRME
# ==========================================
st.subheader("📁 Excel / CSV Dosyası Yükleme")

uploaded_file = st.file_uploader(
    "Kargo veya F4 Ödeme Excel Dosyanızı Yükleyin (.xlsx, .xls veya .csv)", 
    type=["xlsx", "xls", "csv"]
)

if uploaded_file:
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
            df_raw = fix_excel_header(df_raw)
            cols = [str(c).strip() for c in df_raw.columns if str(c).strip() and not str(c).startswith("Unnamed")]

            st.info("💡 **Sütun Eşleştirme:** Otomatik bulunan sütunları kontrol edip eksik olanları manuel seçebilirsiniz.")

            # Otomatik tahmin indeksleri
            def find_best_match(keywords):
                for idx, c in enumerate(cols):
                    norm = normalize_text(c)
                    if any(k in norm for k in keywords):
                        return idx
                return 0

            p_idx = find_best_match(["zimmet", "personel", "kurye", "dagitici"])
            m_idx = find_best_match(["musteri", "alici", "firma", "unvan"])
            f_idx = find_best_match(["borc", "fatura", "tutar", "ucret", "bedel", "kapida", "tahsilat"])
            d_idx = find_best_match(["durum", "son durum", "teslim"])

            col_select1, col_select2 = st.columns(2)
            with col_select1:
                sel_personel = st.selectbox("1. Personel Sütunu:", cols, index=p_idx if p_idx < len(cols) else 0)
                sel_musteri = st.selectbox("2. Müşteri / Firma Sütunu:", cols, index=m_idx if m_idx < len(cols) else 0)

            with col_select2:
                sel_fatura = st.selectbox("3. Fatura Borcu / Tutar Sütunu:", cols, index=f_idx if f_idx < len(cols) else 0)
                sel_durum = st.selectbox("4. Kargo Durumu Sütunu (Opsiyonel):", ["Yok / Tümü Teslim"] + cols, index=(d_idx + 1) if d_idx < len(cols) else 0)

            if st.button("⚡ Verileri İşle ve Listeyi Güncelle"):
                tum_f4_listesi = []
                kullanici_ozet_listesi = []

                df = df_raw.copy()
                df["zimmet_personel"] = df[sel_personel].astype(str).str.strip()
                df["musteri_adi"] = df[sel_musteri].astype(str).str.strip()
                df["fatura_borcu"] = df[sel_fatura].apply(parse_currency_val)
                
                if sel_durum != "Yok / Tümü Teslim":
                    df["durum"] = df[sel_durum].astype(str).str.strip()
                else:
                    df["durum"] = "Teslim Edildi"

                personeller = df["zimmet_personel"].unique()

                for p in personeller:
                    if p.lower() in ["nan", "", "none", "null"]:
                        continue

                    p_df = df[df["zimmet_personel"] == p]
                    zimmet_sayisi = len(p_df)

                    teslim_edildi_sayisi = 0
                    teslim_edilmedi_bekletiliyor_sayisi = 0

                    for _, row in p_df.iterrows():
                        norm_durum = normalize_text(row["durum"])
                        is_teslim = any(k in norm_durum for k in ["teslim edildi", "teslimat yapildi", "teslim yapildi", "teslimdir"]) or norm_durum in ["teslim", "teslim edildi", ""]
                        
                        borc_val = float(row["fatura_borcu"])
                        musteri_val = str(row["musteri_adi"]) if row["musteri_adi"] and str(row["musteri_adi"]).lower() not in ["nan", "none", ""] else "Müşteri Belirtilmedi"

                        if is_teslim:
                            teslim_edildi_sayisi += 1
                        else:
                            teslim_edilmedi_bekletiliyor_sayisi += 1

                        tum_f4_listesi.append({
                            "Personel": p,
                            "Müşteri Adı": musteri_val,
                            "Fatura Borcu (₺)": borc_val,
                            "Açıklama": ""
                        })

                    kullanici_ozet_listesi.append({
                        "personel": p,
                        "zimmet": zimmet_sayisi,
                        "teslim_edildi": teslim_edildi_sayisi,
                        "teslim_edilmedi_bekletiliyor": teslim_edilmedi_bekletiliyor_sayisi,
                        "sms": 0, "imza": 0, "ks": 0,
                        "nakit": p_df["fatura_borcu"].sum(),
                        "kart": 0.0
                    })

                    if p not in st.session_state.personeller:
                        st.session_state.personeller.append(p)

                st.session_state.veriler = pd.DataFrame(kullanici_ozet_listesi)
                st.session_state.tahsilatlar = pd.DataFrame(tum_f4_listesi)
                st.success("✅ Veriler seçtiğiniz sütunlara göre başarıyla aktarıldı!")
                st.rerun()

    except Exception as e:
        st.error(f"Dosya işlenirken hata oluştu: {e}")

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

toplam_tahsilat = float(df_tahsilat["Fatura Borcu (₺)"].sum()) if not df_tahsilat.empty else 0.0

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Toplam Teslim Edildi", f"{toplam_teslim_edildi} Adet")
kpi2.metric("Teslim Edilmedi / Bekletiliyor", f"{toplam_teslim_edilmedi_bekletiliyor} Adet")
kpi3.metric("Toplam Fatura Borcu", f"{toplam_tahsilat:,.2f} ₺")

st.markdown("---")

# ==========================================
# 3. F4 ÖDEME LİSTESİ (PERSONEL BAZLI)
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
            st.warning(f"⚠️ {f4_personel_secim} için henüz kayıt bulunamadı.")
    else:
        st.info("Henüz Excel dosyası yüklenmedi.")

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
