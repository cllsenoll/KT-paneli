"""
KURYE PERFORMANS VE TAHSİLAT MOBİL PANELİ
Çalıştırmak için terminale: streamlit run mobil_kurye_app.py
Gerekli kütüphaneler: pip install streamlit matplotlib pandas openpyxl weasyprint
"""

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import json
import os
from datetime import datetime

import streamlit as st

# Sayfa simgesini ve başlığını ayarlama
st.set_page_config(
    page_title="KPOS",       # Ana ekrana eklerken önerilen varsayılan isim
    page_icon="https://raw.github.com/cllsenoll/KT-paneli/blob/main/1000122774.png",                 # İster bir emoji, ister bir görsel dosyası ("logo.png") veya internet adresi
    layout="wide"
)


# Mobil Sayfa Ayarları
st.set_page_config(
    page_title="KPOS",
    page_icon="🚚",
    layout="centered"
)

# Başlık
st.title("🚚 Kurye Performans & Tahsilat Paneli")
st.caption("Mobil Uyumlu Veri Girişi ve Raporlama Sistemi")

# Sabit Kurye Listesi
KURYELER = [
    "Ahmet Berkan Öksüz",
    "Alattin Cebeci",
    "Hasan Sağlam",
    "Mehmet Kaymaz",
    "Suat Arı"
]

VERI_DOSYASI = "gunluk_kurye_verileri.json"

# Veri Yükle / Kaydet
def veri_yukle():
    if os.path.exists(VERI_DOSYASI):
        with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def veri_kaydet(data):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "veriler" not in st.session_state:
    st.session_state["veriler"] = veri_yukle()

# --- FORM EKRANI ---
st.subheader("📝 Günlük Veri Girişi")

secilen_kurye = st.selectbox("Kurye Seçin:", KURYELER)

# Mevcut veriyi getir
mevcut = st.session_state["veriler"].get(secilen_kurye, {})

with st.form("kurye_formu"):
    col1, col2 = st.columns(2)
    with col1:
        zimmet = st.number_input("Zimmetli Kargo:", min_value=0, value=int(mevcut.get("zimmet", 0)))
        teslim = st.number_input("Teslim Edilen:", min_value=0, value=int(mevcut.get("teslim", 0)))
        devir = st.number_input("Devir Edilen:", min_value=0, value=int(mevcut.get("devir", 0)))
    with col2:
        sms = st.number_input("SMS ile Teslim:", min_value=0, value=int(mevcut.get("sms", 0)))
        imza = st.number_input("İmza ile Teslim:", min_value=0, value=int(mevcut.get("imza", 0)))
        ks = st.number_input("KS ile Teslim:", min_value=0, value=int(mevcut.get("ks", 0)))

    st.markdown("---")
    st.markdown("**💳 Tahsilat Tutarları (TL)**")
    col3, col4 = st.columns(2)
    with col3:
        nakit = st.number_input("Nakit Tahsilat (₺):", min_value=0.0, value=float(mevcut.get("nakit", 0.0)))
    with col4:
        kart = st.number_input("Kredi Kartı / POS (₺):", min_value=0.0, value=float(mevcut.get("kart", 0.0)))

    kaydet_btn = st.form_submit_button("💾 Kurye Verisini Kaydet")

if kaydet_btn:
    st.session_state["veriler"][secilen_kurye] = {
        "zimmet": zimmet,
        "teslim": teslim,
        "devir": devir,
        "sms": sms,
        "imza": imza,
        "ks": ks,
        "nakit": nakit,
        "kart": kart
    }
    veri_kaydet(st.session_state["veriler"])
    st.success(f"✓ {secilen_kurye} verileri başarıyla kaydedildi!")

# --- GRAFİKLER VE PERFORMANS ---
st.markdown("---")
st.subheader("📊 Performans ve Grafik Analizi")

if st.session_state["veriler"]:
    # 1. Sütun Grafiği (Teslimat vs Devir)
    import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import json
import os

# Sayfa Yapılandırması ve İkon
st.set_page_config(
    page_title="Kurye Performans Paneli", 
    page_icon="🚚", 
    layout="centered"
)

# Özel Stil / CSS ile Görsel İyileştirme
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
    .metric-card {
        background-color: #1E293B;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚚 Kurye Performans & Tahsilat Paneli")
st.caption("Mobil Uyumlu Veri Girişi ve Raporlama Sistemi")

KURYELER = [
    "Ahmet Berkan Öksüz",
    "Alattin Cebeci",
    "Hasan Sağlam",
    "Mehmet Kaymaz",
    "Suat Arı"
]

VERI_DOSYASI = "gunluk_kurye_verileri.json"

def veri_yukle():
    if os.path.exists(VERI_DOSYASI):
        try:
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def veri_kaydet(data):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "veriler" not in st.session_state:
    st.session_state["veriler"] = veri_yukle()

# --- VERİ GİRİŞ FORMU ---
st.subheader("📝 Günlük Veri Girişi")
secilen_kurye = st.selectbox("Kurye Seçin:", KURYELER)

mevcut = st.session_state["veriler"].get(secilen_kurye, {})

with st.form("kurye_formu"):
    col1, col2 = st.columns(2)
    with col1:
        zimmet = st.number_input("Zimmetli Kargo:", min_value=0, value=int(mevcut.get("zimmet", 0)))
        teslim = st.number_input("Teslim Edilen:", min_value=0, value=int(mevcut.get("teslim", 0)))
        devir = st.number_input("Devir Edilen:", min_value=0, value=int(mevcut.get("devir", 0)))
    with col2:
        sms = st.number_input("SMS ile Teslim:", min_value=0, value=int(mevcut.get("sms", 0)))
        imza = st.number_input("İmza ile Teslim:", min_value=0, value=int(mevcut.get("imza", 0)))
        ks = st.number_input("KS ile Teslim:", min_value=0, value=int(mevcut.get("ks", 0)))

    st.markdown("---")
    st.markdown("**💳 Tahsilat Tutarları (TL)**")
    col3, col4 = st.columns(2)
    with col3:
        nakit = st.number_input("Nakit Tahsilat (₺):", min_value=0.0, value=float(mevcut.get("nakit", 0.0)))
    with col4:
        kart = st.number_input("Kredi Kartı / POS (₺):", min_value=0.0, value=float(mevcut.get("kart", 0.0)))

    kaydet_btn = st.form_submit_button("💾 Kurye Verisini Kaydet")

if kaydet_btn:
    st.session_state["veriler"][secilen_kurye] = {
        "zimmet": zimmet,
        "teslim": teslim,
        "devir": devir,
        "sms": sms,
        "imza": imza,
        "ks": ks,
        "nakit": nakit,
        "kart": kart
    }
    veri_kaydet(st.session_state["veriler"])
    st.success(f"✓ {secilen_kurye} verileri kaydedildi!")

st.markdown("---")

# --- GELİŞMİŞ GRAFİK VE RAPORLAMA BÖLÜMÜ ---
st.subheader("📊 Genel Durum ve Performans")

if st.session_state["veriler"]:
    # Genel Özet Kartları (KPI)
    toplam_teslim = sum(v.get("teslim", 0) for v in st.session_state["veriler"].values())
    toplam_devir = sum(v.get("devir", 0) for v in st.session_state["veriler"].values())
    toplam_tahsilat = sum(v.get("nakit", 0) + v.get("kart", 0) for v in st.session_state["veriler"].values())

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Toplam Teslim", f"{toplam_teslim} Adet")
    kpi2.metric("Toplam Devir", f"{toplam_devir} Adet")
    kpi3.metric("Toplam Tahsilat", f"{toplam_tahsilat:,.0f} ₺")

    st.markdown("---")

    # 1. GRAFİK: Kuryelerin Teslimat/Devir Karşılaştırması (Modern Matplotlib Grafiği)
    st.markdown("### 📦 Kurye Bazlı Teslimat vs Devir")
    
    kurye_isimleri = []
    teslim_sayilari = []
    devir_sayilari = []

    for k, v in st.session_state["veriler"].items():
        # İsmi kısaltma (Örn: Ahmet Berkan Öksüz -> Ahmet Öksüz)
        parcalar = k.split()
        kisa_isim = f"{parcalar[0]} {parcalar[-1]}"
        kurye_isimleri.append(kisa_isim)
        teslim_sayilari.append(v.get("teslim", 0))
        devir_sayilari.append(v.get("devir", 0))

    if kurye_isimleri:
        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#0E1117')
        ax.set_facecolor('#161B22')

        y = range(len(kurye_isimleri))
        height = 0.35

        rects1 = ax.barh([i - height/2 for i in y], teslim_sayilari, height, label='Teslim', color='#10B981')
        rects2 = ax.barh([i + height/2 for i in y], devir_sayilari, height, label='Devir', color='#EF4444')

        ax.set_yticks(y)
        ax.set_yticklabels(kurye_isimleri, color='white', fontsize=10)
        ax.tick_params(colors='white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#30363D')
        ax.spines['bottom'].set_color('#30363D')
        ax.legend(facecolor='#161B22', edgecolor='none', labelcolor='white')
        ax.bar_label(rects1, padding=3, color='white', fontsize=9)
        ax.bar_label(rects2, padding=3, color='white', fontsize=9)

        plt.tight_layout()
        st.pyplot(fig)

    st.markdown("---")

    # 2. GRAFİK: Teslimat Tipi Dağılımı (Pasta / Donut Grafiği)
    st.markdown("### 🍩 Teslimat Yöntemi Dağılımı")
    kurye_pie = st.selectbox("Detayını Görmek İstediğiniz Kurye:", list(st.session_state["veriler"].keys()))
    
    if kurye_pie in st.session_state["veriler"]:
        v = st.session_state["veriler"][kurye_pie]
        sizes = [v.get("sms", 0), v.get("imza", 0), v.get("ks", 0)]
        labels = ["SMS", "İmza", "KS"]
        colors = ['#3B82F6', '#10B981', '#F59E0B']

        if sum(sizes) > 0:
            fig2, ax2 = plt.subplots(figsize=(4, 3))
            fig2.patch.set_facecolor('#0E1117')
            
            # Donut (Halka) Grafik Şekli
            wedges, texts, autotexts = ax2.pie(
                sizes, 
                labels=labels, 
                autopct='%1.1f%%', 
                startangle=90, 
                colors=colors,
                textprops=dict(color="white"),
                wedgeprops=dict(width=0.4, edgecolor='#0E1117')
            )
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_weight('bold')

            ax2.axis('equal')
            plt.tight_layout()
            st.pyplot(fig2)
        else:
            st.info("Bu kurye için henüz teslimat detay verisi girilmedi.")
else:
    st.info("Henüz grafik oluşturulacak veri girilmedi.")

    
    if df_data:
        df = pd.DataFrame(df_data).set_index("Kurye")
        st.markdown("**Kuryeler Teslimat / Devir Karşılaştırması**")
        st.bar_chart(df)

    # 2. Pasta Grafikler
    st.markdown("**Teslimat Tipi Dağılımı (SMS / İmza / KS)**")
    kurye_pie = st.selectbox("Pasta Grafiği Gösterileyecek Kurye:", list(st.session_state["veriler"].keys()))
    
    if kurye_pie in st.session_state["veriler"]:
        v = st.session_state["veriler"][kurye_pie]
        sizes = [v.get("sms", 0), v.get("imza", 0), v.get("ks", 0)]
        labels = ["SMS", "İmza", "KS"]

        if sum(sizes) > 0:
            fig, ax = plt.subplots(figsize=(4, 3))
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#3B82F6', '#10B981', '#F59E0B'])
            ax.axis('equal')
            st.pyplot(fig)
        else:
            st.info("Bu kurye için henüz teslimat verisi girilmedi.")
else:
    st.info("Grafikleri görmek için kurye verisi girin.")
