import streamlit as st
import matplotlib.pyplot as plt
import json
import os

# Güncel Görsel Bağlantınız
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
    </style>
""", unsafe_allow_html=True)

# Üst Başlık ve Logo Alanı
col_logo, col_title = st.columns([1, 3])

with col_logo:
    st.image(LOGO_URL, width=90)

with col_title:
    st.title("Kurye Performans & Tahsilat Paneli")
    st.caption("Mobil Uyumlu Veri Girişi ve Raporlama Sistemi")

VERI_DOSYASI = "gunluk_kurye_verileri.json"
KURYE_DOSYASI = "kurye_listesi.json"

# Varsayılan Kurye Listesi
VARSAYILAN_KURYELER = [
    "Ahmet Berkan Öksüz",
    "Alattin Cebeci",
    "Hasan Sağlam",
    "Mehmet Kaymaz",
    "Suat Arı"
]

def kuryeleri_yukle():
    if os.path.exists(KURYE_DOSYASI):
        try:
            with open(KURYE_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return VARSAYILAN_KURYELER
    return VARSAYILAN_KURYELER

def kuryeleri_kaydet(liste):
    with open(KURYE_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=4)

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

if "kuryeler" not in st.session_state:
    st.session_state["kuryeler"] = kuryeleri_yukle()

if "veriler" not in st.session_state:
    st.session_state["veriler"] = veri_yukle()

# --- SIDEBAR: KURYE YÖNETİMİ ---
with st.sidebar:
    st.header("⚙️ Kurye Yönetimi")
    yeni_kurye = st.text_input("Yeni Kurye Adı Soyadı:")
    if st.button("➕ Kurye Ekle"):
        if yeni_kurye.strip():
            if yeni_kurye.strip() not in st.session_state["kuryeler"]:
                st.session_state["kuryeler"].append(yeni_kurye.strip())
                kuryeleri_kaydet(st.session_state["kuryeler"])
                st.success(f"{yeni_kurye.strip()} eklendi!")
                st.rerun()
            else:
                st.warning("Bu kurye zaten listede var.")
        else:
            st.error("Lütfen geçerli bir isim girin.")

    st.markdown("---")
    silinecek_kurye = st.selectbox("Silinecek Kurye Seçin:", st.session_state["kuryeler"])
    if st.button("🗑️ Seçili Kuryeyi Sil"):
        st.session_state["kuryeler"].remove(silinecek_kurye)
        kuryeleri_kaydet(st.session_state["kuryeler"])
        if silinecek_kurye in st.session_state["veriler"]:
            del st.session_state["veriler"][silinecek_kurye]
            veri_kaydet(st.session_state["veriler"])
        st.success(f"{silinecek_kurye} silindi!")
        st.rerun()

# --- VERİ GİRİŞ FORMU ---
st.subheader("📝 Günlük Veri Girişi")
secilen_kurye = st.selectbox("Kurye Seçin:", st.session_state["kuryeler"])

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
    toplam_zimmet = sum(v.get("zimmet", 0) for v in st.session_state["veriler"].values())
    toplam_teslim = sum(v.get("teslim", 0) for v in st.session_state["veriler"].values())
    toplam_devir = sum(v.get("devir", 0) for v in st.session_state["veriler"].values())
    toplam_nakit = sum(v.get("nakit", 0) for v in st.session_state["veriler"].values())
    toplam_kart = sum(v.get("kart", 0) for v in st.session_state["veriler"].values())
    toplam_tahsilat = toplam_nakit + toplam_kart

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Toplam Teslim", f"{toplam_teslim} Adet")
    kpi2.metric("Toplam Devir", f"{toplam_devir} Adet")
    kpi3.metric("Toplam Tahsilat", f"{toplam_tahsilat:,.2f} ₺")

    st.markdown("---")

    # --- ŞUBE PERFORMANS İBRESİ (GAUGE CHART) ---
    st.markdown("### 🎯 Şube Teslimat Başarı Performansı")
    
    basari_orani = (toplam_teslim / toplam_zimmet * 100) if toplam_zimmet > 0 else 0

    fig_gauge, ax_g = plt.subplots(figsize=(5, 3), subplot_kw={'projection': 'polar'})
    fig_gauge.patch.set_facecolor('#0E1117')
    ax_g.set_facecolor('#0E1117')

    # İbre Grafiği Çizimi (Yarım Daire)
    import numpy as np
    theta = np.linspace(0, np.pi, 100)
    r = 1

    # Arka plan yarım daire halkası
    ax_g.plot(theta, [r]*100, color="#30363D", linewidth=18)
    
    # Başarı oranına karşılık gelen renkli halka
    doluluk_theta = np.linspace(np.pi, np.pi - (basari_orani / 100 * np.pi), 100)
    
    # Performans rengi belirleme
    renk = "#EF4444" if basari_orani < 70 else "#F59E0B" if basari_orani < 85 else "#10B981"
    ax_g.plot(doluluk_theta, [r]*100, color=renk, linewidth=18)

    ax_g.set_theta_zero_location('W')
    ax_g.set_theta_direction(-1)
    ax_g.set_axis_off()

    # İbre değerini yazdır
    ax_g.text(0, 0, f"%{basari_orani:.1f}", horizontalalignment='center', verticalalignment='center', fontsize=22, fontweight='bold', color='white')
    ax_g.text(0, -0.35, f"Zimmet: {toplam_zimmet} | Teslim: {toplam_teslim}", horizontalalignment='center', verticalalignment='center', fontsize=10, color='#8B949E')

    st.pyplot(fig_gauge)

    st.markdown("---")

    # --- KURYE TAHSİLAT LİSTESİ ---
    st.markdown("### 💰 Kurye Bazlı Tahsilat Listesi")
    
    tahsilat_verileri = []
    for k, v in st.session_state["veriler"].items():
        n = v.get("nakit", 0.0)
        k_pos = v.get("kart", 0.0)
        t = n + k_pos
        if t > 0 or n > 0 or k_pos > 0:
            tahsilat_verileri.append({
                "Kurye": k,
                "Nakit Tahsilat (₺)": f"{n:,.2f} ₺",
                "POS / Kart Tahsilat (₺)": f"{k_pos:,.2f} ₺",
                "Toplam Tahsilat (₺)": f"{t:,.2f} ₺"
            })

    if tahsilat_verileri:
        st.dataframe(tahsilat_verileri, use_container_width=True)
    else:
        st.info("Henüz tahsilat verisi girilmedi.")

    st.markdown("---")

    st.markdown("### 📦 Kurye Bazlı Teslimat vs Devir")
    
    kurye_isimleri = []
    teslim_sayilari = []
    devir_sayilari = []

    for k, v in st.session_state["veriler"].items():
        parcalar = k.split()
        kisa_isim = f"{parcalar[0]} {parcalar[-1]}" if len(parcalar) > 1 else parcalar[0]
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
