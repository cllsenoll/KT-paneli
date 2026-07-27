import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import requests

# Güncel Görsel Bağlantısı
LOGO_URL = "https://raw.githubusercontent.com/cllsenoll/KT-paneli/refs/heads/main/1000122774.png"

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Kurye Performans Paneli", 
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

# Üst Başlık ve Logo Alanı
col_logo, col_title = st.columns([1, 3])

with col_logo:
    st.image(LOGO_URL, width=90)

with col_title:
    st.title("Kurye Performans & Tahsilat Paneli")
    st.caption("Mobil Uyumlu Veri Girişi ve Canlı Raporlama Sistemi")

# --- GOOGLE SHEETS VE APPS SCRIPT ENTEGRASYONU ---
SHEET_ID = "1bpU7FWdH6xGJ3Vl5DdbunrwXM_Q4yS7AYnL8kdUtBvg"
# BURAYA 1. ADIMDA KOPYALADIĞIN WEB APP URL'SİNİ YAPIŞTIR:
SCRIPT_URL = "https://script.google.com/macros/s/BURAYA_KENDI_SCRIPT_URL_ADRESINI_YAPISTIR/exec"

def gsheet_oku(sheet_name):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        df = pd.read_csv(url)
        df = df.dropna(how='all')
        return df
    except Exception as e:
        return pd.DataFrame()

def gsheet_yaz(sheet_name, data):
    try:
        payload = {"sheet": sheet_name, "data": data}
        res = requests.post(SCRIPT_URL, json=payload)
        return res.status_code == 200
    except Exception as e:
        st.error(f"Veri yazma hatası: {e}")
        return False

def verileri_cek():
    df_kuryeler = gsheet_oku("Kuryeler")
    df_veriler = gsheet_oku("Veriler")
    df_tahsilat = gsheet_oku("FirmaTahsilat")
    return df_kuryeler, df_veriler, df_tahsilat

df_kuryeler, df_veriler, df_tahsilat = verileri_cek()

# Varsayılan Kuryeler
VARSAYILAN_KURYELER = [
    "Ahmet Berkan Öksüz",
    "Alattin Cebeci",
    "Hasan Sağlam",
    "Mehmet Kaymaz",
    "Suat Arı"
]

if df_kuryeler.empty or "Kurye" not in df_kuryeler.columns:
    kurye_listesi = VARSAYILAN_KURYELER
else:
    kurye_listesi = [k for k in df_kuryeler["Kurye"].tolist() if str(k).strip() != ""]

# --- SIDEBAR: KURYE YÖNETİMİ ---
with st.sidebar:
    st.header("⚙️ Kurye Yönetimi")
    yeni_kurye = st.text_input("Yeni Kurye Adı Soyadı:")
    if st.button("➕ Kurye Ekle"):
        if yeni_kurye.strip():
            if yeni_kurye.strip() not in kurye_listesi:
                yeni_liste = kurye_listesi + [yeni_kurye.strip()]
                gsheet_yaz("Kuryeler", yeni_liste)
                st.success(f"{yeni_kurye.strip()} eklendi!")
                st.rerun()
            else:
                st.warning("Bu kurye zaten listede var.")
        else:
            st.error("Lütfen geçerli bir isim girin.")

    st.markdown("---")
    if kurye_listesi:
        silinecek_kurye = st.selectbox("Silinecek Kurye Seçin:", kurye_listesi)
        if st.button("🗑️ Seçili Kuryeyi Sil"):
            kurye_listesi.remove(silinecek_kurye)
            gsheet_yaz("Kuryeler", kurye_listesi)
            st.success(f"{silinecek_kurye} silindi!")
            st.rerun()

# İbre Grafiği Oluşturma Fonksiyonu
def ibre_grafik_ciz(teslim, zimmet, baslik_metni, alt_metin=""):
    basari_orani = (teslim / zimmet * 100) if zimmet > 0 else 0

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
    ax.text(0, -0.35, f"{alt_metin}\nZimmet: {zimmet} | Teslim: {teslim}", horizontalalignment='center', verticalalignment='center', fontsize=10, color='#8B949E')

    return fig

# ==========================================
# 1. ŞUBE TESLİM ORANI
# ==========================================
st.markdown("### 🎯 Şube Teslim oranı")

toplam_zimmet = int(pd.to_numeric(df_veriler["zimmet"], errors='coerce').sum()) if not df_veriler.empty and "zimmet" in df_veriler.columns else 0
toplam_teslim = int(pd.to_numeric(df_veriler["teslim"], errors='coerce').sum()) if not df_veriler.empty and "teslim" in df_veriler.columns else 0
toplam_devir = int(pd.to_numeric(df_veriler["devir"], errors='coerce').sum()) if not df_veriler.empty and "devir" in df_veriler.columns else 0

fig_sube = ibre_grafik_ciz(toplam_teslim, toplam_zimmet, "Şube Teslim oranı", "Şube Genel Performansı")
st.pyplot(fig_sube)

st.markdown("---")

# ==========================================
# 2. GENEL DURUM VE PERFORMANS
# ==========================================
st.subheader("📊 Genel Durum ve Performans")

toplam_nakit = float(pd.to_numeric(df_veriler["nakit"], errors='coerce').sum()) if not df_veriler.empty and "nakit" in df_veriler.columns else 0.0
toplam_kart = float(pd.to_numeric(df_veriler["kart"], errors='coerce').sum()) if not df_veriler.empty and "kart" in df_veriler.columns else 0.0
toplam_tahsilat = toplam_nakit + toplam_kart

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Toplam Teslim", f"{toplam_teslim} Adet")
kpi2.metric("Toplam Devir", f"{toplam_devir} Adet")
kpi3.metric("Toplam Tahsilat", f"{toplam_tahsilat:,.2f} ₺")

st.markdown("---")

# ==========================================
# 3. KURYE BAZLI TESLİMAT VS DEVİR
# ==========================================
st.markdown("### 📦 Kurye Bazlı Teslimat vs Devir")

if not df_veriler.empty and "kurye" in df_veriler.columns:
    fig_bar, ax_bar = plt.subplots(figsize=(6, 4))
    fig_bar.patch.set_facecolor('#0E1117')
    ax_bar.set_facecolor('#161B22')

    kurye_names = df_veriler["kurye"].tolist()
    y = range(len(kurye_names))
    height = 0.35

    teslim_vals = pd.to_numeric(df_veriler["teslim"], errors='coerce').fillna(0).tolist()
    devir_vals = pd.to_numeric(df_veriler["devir"], errors='coerce').fillna(0).tolist()

    rects1 = ax_bar.barh([i - height/2 for i in y], teslim_vals, height, label='Teslim', color='#10B981')
    rects2 = ax_bar.barh([i + height/2 for i in y], devir_vals, height, label='Devir', color='#EF4444')

    ax_bar.set_yticks(y)
    ax_bar.set_yticklabels(kurye_names, color='white', fontsize=10)
    ax_bar.tick_params(colors='white')
    ax_bar.spines['top'].set_visible(False)
    ax_bar.spines['right'].set_visible(False)
    ax_bar.spines['left'].set_color('#30363D')
    ax_bar.spines['bottom'].set_color('#30363D')
    ax_bar.legend(facecolor='#161B22', edgecolor='none', labelcolor='white')
    ax_bar.bar_label(rects1, padding=3, color='white', fontsize=9)
    ax_bar.bar_label(rects2, padding=3, color='white', fontsize=9)

    plt.tight_layout()
    st.pyplot(fig_bar)

st.markdown("---")

# ==========================================
# 4. KURYE TESLİM PERFORMANSI
# ==========================================
st.markdown("### ⏱️ Kurye teslim performansı")

if kurye_listesi:
    kurye_ibre_secim = st.selectbox("Performansını Görmek İstediğiniz Kurye:", kurye_listesi)

    if not df_veriler.empty and kurye_ibre_secim in df_veriler["kurye"].values:
        row = df_veriler[df_veriler["kurye"] == kurye_ibre_secim].iloc[0]
        k_zimmet = int(pd.to_numeric(row.get("zimmet", 0), errors='coerce'))
        k_teslim = int(pd.to_numeric(row.get("teslim", 0), errors='coerce'))
    else:
        k_zimmet, k_teslim = 0, 0

    fig_kurye = ibre_grafik_ciz(k_teslim, k_zimmet, "Kurye teslim performansı", kurye_ibre_secim)
    st.pyplot(fig_kurye)

st.markdown("---")

# ==========================================
# 5. GÜNLÜK VERİ GİRİŞİ
# ==========================================
st.subheader("📝 Günlük Veri Girişi")
secilen_kurye = st.selectbox("Kurye Seçin:", kurye_listesi)

mevcut_row = df_veriler[df_veriler["kurye"] == secilen_kurye] if not df_veriler.empty and "kurye" in df_veriler.columns else pd.DataFrame()

with st.form("kurye_formu"):
    col1, col2 = st.columns(2)
    with col1:
        zimmet = st.number_input("Zimmetli Kargo:", min_value=0, value=int(pd.to_numeric(mevcut_row["zimmet"].values[0], errors='coerce')) if not mevcut_row.empty else 0)
        teslim = st.number_input("Teslim Edilen:", min_value=0, value=int(pd.to_numeric(mevcut_row["teslim"].values[0], errors='coerce')) if not mevcut_row.empty else 0)
        devir = st.number_input("Devir Edilen:", min_value=0, value=int(pd.to_numeric(mevcut_row["devir"].values[0], errors='coerce')) if not mevcut_row.empty else 0)
    with col2:
        sms = st.number_input("SMS ile Teslim:", min_value=0, value=int(pd.to_numeric(mevcut_row["sms"].values[0], errors='coerce')) if not mevcut_row.empty else 0)
        imza = st.number_input("İmza ile Teslim:", min_value=0, value=int(pd.to_numeric(mevcut_row["imza"].values[0], errors='coerce')) if not mevcut_row.empty else 0)
        ks = st.number_input("KS ile Teslim:", min_value=0, value=int(pd.to_numeric(mevcut_row["ks"].values[0], errors='coerce')) if not mevcut_row.empty else 0)

    st.markdown("---")
    st.markdown("**💳 Genel Tahsilat Tutarları (TL)**")
    col3, col4 = st.columns(2)
    with col3:
        nakit = st.number_input("Nakit Tahsilat (₺):", min_value=0.0, value=float(pd.to_numeric(mevcut_row["nakit"].values[0], errors='coerce')) if not mevcut_row.empty else 0.0)
    with col4:
        kart = st.number_input("Kredi Kartı / POS (₺):", min_value=0.0, value=float(pd.to_numeric(mevcut_row["kart"].values[0], errors='coerce')) if not mevcut_row.empty else 0.0)

    kaydet_btn = st.form_submit_button("💾 Kurye Verisini Kaydet")

if kaydet_btn:
    yeni_veri = {
        "kurye": secilen_kurye,
        "zimmet": zimmet,
        "teslim": teslim,
        "devir": devir,
        "sms": sms,
        "imza": imza,
        "ks": ks,
        "nakit": nakit,
        "kart": kart
    }
    
    if gsheet_yaz("Veriler", yeni_veri):
        st.success(f"✓ {secilen_kurye} verileri Google Sheets'e başarıyla kaydedildi!")
        st.rerun()

st.markdown("---")

# ==========================================
# 6. FİRMA BAZLI ÖZEL TAHSİLAT GİRİŞİ
# ==========================================
st.subheader("🏢 Firma Bazlı Özel Tahsilat Girişi")

kurye_firma_secim = st.selectbox("Tahsilat Eklenecek Kurye:", kurye_listesi, key="kurye_firma")

with st.form("firma_tahsilat_formu"):
    c_f1, c_f2, c_f3 = st.columns([2, 1.5, 2.5])
    with c_f1:
        firma_adi = st.text_input("Firma İsmi:")
    with c_f2:
        firma_tutar = st.number_input("Tahsilat Tutarı (₺):", min_value=0.0, step=10.0)
    with c_f3:
        firma_aciklama = st.text_input("Açıklama:")

    firma_kaydet_btn = st.form_submit_button("➕ Firmayı Kaydet")

if firma_kaydet_btn:
    if firma_adi.strip() and firma_tutar > 0:
        yeni_tahsilat = {
            "Kurye": kurye_firma_secim,
            "Firma Adı": firma_adi.strip(),
            "Tutar (₺)": firma_tutar,
            "Açıklama": firma_aciklama.strip()
        }
        if gsheet_yaz("FirmaTahsilat", yeni_tahsilat):
            st.success(f"✓ {firma_adi} için {firma_tutar:,.2f} ₺ tahsilat eklendi.")
            st.rerun()
    else:
        st.error("Lütfen Firma Adı ve 0'dan büyük Tutar giriniz.")

# Seçili Kuryenin Mevcut Firma Tahsilat Listesi
if not df_tahsilat.empty and "Kurye" in df_tahsilat.columns:
    kurye_tahsilatlari = df_tahsilat[df_tahsilat["Kurye"] == kurye_firma_secim]
    if not kurye_tahsilatlari.empty:
        st.markdown(f"**{kurye_firma_secim} - Kayıtlı Firma Tahsilatları:**")
        df_goster = kurye_tahsilatlari.reset_index(drop=True)
        df_goster.index = range(1, len(df_goster) + 1)
        st.dataframe(df_goster[["Firma Adı", "Tutar (₺)", "Açıklama"]], use_container_width=True)

st.markdown("---")

# ==========================================
# 7. FİRMA TAHSİLAT LİSTESİ ÇIKTI / İNDİR
# ==========================================
st.subheader("🖨️ Firma Tahsilat Listesi (Çıktı / İndir)")

if not df_tahsilat.empty and "Firma Adı" in df_tahsilat.columns:
    df_tahsilat_goster = df_tahsilat.reset_index(drop=True)
    df_tahsilat_goster.index = range(1, len(df_tahsilat_goster) + 1)
    st.dataframe(df_tahsilat_goster, use_container_width=True)

    c_d1, c_d2 = st.columns(2)
    with c_d1:
        csv_data = df_tahsilat_goster.to_csv(index=True, encoding='utf-8-sig')
        st.download_button(
            label="📥 Excel / CSV Olarak İndir",
            data=csv_data,
            file_name="firma_tahsilat_listesi.csv",
            mime="text/csv"
        )
    
    with c_d2:
        st.markdown("""
            <button onclick="window.print()" style="
                width: 100%;
                height: 3em;
                border-radius: 8px;
                background-color: #10B981;
                color: white;
                font-weight: bold;
                border: none;
                cursor: pointer;">
                📄 PDF İndir / Yazdır
            </button>
        """, unsafe_allow_html=True)
else:
    st.info("Henüz firma bazlı tahsilat kaydı bulunmuyor.")
