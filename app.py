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
    page_title="Kurye Takip",       # Ana ekrana eklerken önerilen varsayılan isim
    page_icon="https://github.com/cllsenoll/KT-paneli/blob/main/1000122774.png",                 # İster bir emoji, ister bir görsel dosyası ("logo.png") veya internet adresi
    layout="wide"
)


# Mobil Sayfa Ayarları
st.set_page_config(
    page_title="Kurye Performans Paneli",
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
    df_data = []
    for k, v in st.session_state["veriler"].items():
        df_data.append({
            "Kurye": k.split()[0] + " " + k.split()[-1],
            "Teslim": v.get("teslim", 0),
            "Devir": v.get("devir", 0)
        })
    
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
