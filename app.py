import streamlit as st
import matplotlib.pyplot as plt
import json
import os
import pandas as pd
import numpy as np

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
FIRMA_TAHSILAT_DOSYASI = "firma_tahsilat_verileri.json"

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

def veri_yukle(dosya_adi):
    if os.path.exists(dosya_adi):
        try:
            with open(dosya_adi, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def veri_kaydet(data, dosya_adi):
    with open(dosya_adi, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "kuryeler" not in st.session_state:
    st.session_state["kuryeler"] = kuryeleri_yukle()

if "veriler" not in st.session_state:
    st.session_state["veriler"] = veri_yukle(VERI_DOSYASI)

if "firma_tahsilatlari" not in st.session_state:
    st.session_state["firma_tahsilatlari"] = veri_yukle(FIRMA_TAHSILAT_DOSYASI)

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
            veri_kaydet(st.session_state["veriler"], VERI_DOSYASI)
        if silinecek_kurye in st.session_state["firma_tahsilatlari"]:
            del st.session_state["firma_tahsilatlari"][silinecek_kurye]
            veri_kaydet(st.session_state["firma_tahsilatlari"], FIRMA_TAHSILAT_DOSYASI)
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
    st.markdown("**💳 Genel Tahsilat Tutarları (TL)**")
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
    veri_kaydet(st.session_state["veriler"], VERI_DOSYASI)
    st.success(f"✓ {secilen_kurye} verileri kaydedildi!")

st.markdown("---")

# --- FİRMA BAZLI TAHSİLAT GİRİŞİ BÖLÜMÜ ---
st.subheader("🏢 Firma Bazlı Özel Tahsilat Girişi")

kurye_firma_secim = st.selectbox("Tahsilat Eklenecek Kurye:", st.session_state["kuryeler"], key="kurye_firma")

if kurye_firma_secim not in st.session_state["firma_tahsilatlari"]:
    st.session_state["firma_tahsilatlari"][kurye_firma_secim] = []

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
        st.session_state["firma_tahsilatlari"][kurye_firma_secim].append({
            "Firma Adı": firma_adi.strip(),
            "Tutar (₺)": firma_tutar,
            "Açıklama": firma_aciklama.strip()
        })
        veri_kaydet(st.session_state["firma_tahsilatlari"], FIRMA_TAHSILAT_DOSYASI)
        st.success(f"✓ {firma_adi} için {firma_tutar:,.2f} ₺ tahsilat eklendi.")
        st.rerun()
    else:
        st.error("Lütfen Firma Adı ve 0'dan büyük Tutar giriniz.")

# Seçili Kuryenin Mevcut Firma Tahsilat Listesi ve Silme İşlemi
mevcut_firma_listesi = st.session_state["firma_tahsilatlari"].get(kurye_firma_secim, [])
if mevcut_firma_listesi:
    st.markdown(f"**{kurye_firma_secim} - Kayıtlı Firma Tahsilatları:**")
    df_kurye_firma = pd.DataFrame(mevcut_firma_listesi)
    st.dataframe(df_kurye_firma, use_container_width=True)

    silinecek_idx = st.number_input("Silmek İstediğiniz Satır No (0, 1, 2...):", min_value=0, max_value=len(mevcut_firma_listesi)-1, step=1)
    if st.button("❌ Seçilen Firma Tahsilatını Sil"):
        st.session_state["firma_tahsilatlari"][kurye_firma_secim].pop(silinecek_idx)
        veri_kaydet(st.session_state["firma_tahsilatlari"], FIRMA_TAHSILAT_DOSYASI)
        st.success("Satır silindi!")
        st.rerun()

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

    theta = np.linspace(0, np.pi, 100)
    r = 1

    ax_g.plot(theta, [r]*100, color="#30363D", linewidth=18)
    doluluk_theta = np.linspace(np.pi, np.pi - (basari_orani / 100 * np.pi), 100)
    renk = "#EF4444" if basari_orani < 70 else "#F59E0B" if basari_orani < 85 else "#10B981"
    ax_g.plot(doluluk_theta, [r]*100, color=renk, linewidth=18)

    ax_g.set_theta_zero_location('W')
    ax_g.set_theta_direction(-1)
    ax_g.set_axis_off()

    ax_g.text(0, 0, f"%{basari_orani:.1f}", horizontalalignment='center', verticalalignment='center', fontsize=22, fontweight='bold', color='white')
    ax_g.text(0, -0.35, f"Zimmet: {toplam_zimmet} | Teslim: {toplam_teslim}", horizontalalignment='center', verticalalignment='center', fontsize=10, color='#8B949E')

    st.pyplot(fig_gauge)

    st.markdown("---")

    # --- TÜM FİRMA TAHSİLATLARI VE YAZDIRMA/ÇIKTI BÖLÜMÜ ---
    st.markdown("### 🖨️ Firma Tahsilat Listesi (Çıktı / İndir)")
    
    tum_tahsilat_satirlari = []
    for kurye_isik, firmalar in st.session_state["firma_tahsilatlari"].items():
        for f in firmalar:
            tum_tahsilat_satirlari.append({
                "Kurye": kurye_isik,
                "Firma Adı": f.get("Firma Adı", ""),
                "Tutar (₺)": f.get("Tutar (₺)", 0.0),
                "Açıklama": f.get("Açıklama", "")
            })

    if tum_tahsilat_satirlari:
        df_tum_tahsilat = pd.DataFrame(tum_tahsilat_satirlari)
        st.dataframe(df_tum_tahsilat, use_container_width=True)

        # Excel / CSV İndirme Butonu
        csv_data = df_tum_tahsilat.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Tahsilat Listesini İndir (Excel / CSV)",
            data=csv_data,
            file_name="firma_tahsilat_listesi.csv",
            mime="text/csv"
        )
    else:
        st.info("Henüz firma bazlı tahsilat kaydı bulunmuyor.")

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

    # --- KİŞİSEL KURYE PERFORMANS İBRESİ (GAUGE CHART) ---
    st.markdown("### ⏱️ Kurye Özel Teslimat Başarı İbresi")
    kurye_ibre_secim = st.selectbox("Detay İbresini Görmek İstediğiniz Kurye:", list(st.session_state["veriler"].keys()))
    
    if kurye_ibre_secim in st.session_state["veriler"]:
        v_kurye = st.session_state["veriler"][kurye_ibre_secim]
        k_zimmet = v_kurye.get("zimmet", 0)
        k_teslim = v_kurye.get("teslim", 0)
        
        k_orann = (k_teslim / k_zimmet * 100) if k_zimmet > 0 else 0

        fig_k_gauge, ax_kg = plt.subplots(figsize=(5, 3), subplot_kw={'projection': 'polar'})
        fig_k_gauge.patch.set_facecolor('#0E1117')
        ax_kg.set_facecolor('#0E1117')

        ax_kg.plot(theta, [r]*100, color="#30363D", linewidth=18)
        k_doluluk_theta = np.linspace(np.pi, np.pi - (k_orann / 100 * np.pi), 100)
        k_renk = "#EF4444" if k_orann < 70 else "#F59E0B" if k_orann < 85 else "#10B981"
        ax_kg.plot(k_doluluk_theta, [r]*100, color=k_renk, linewidth=18)

        ax_kg.set_theta_zero_location('W')
        ax_kg.set_theta_direction(-1)
        ax_kg.set_axis_off()

        ax_kg.text(0, 0, f"%{k_orann:.1f}", horizontalalignment='center', verticalalignment='center', fontsize=22, fontweight='bold', color='white')
        ax_kg.text(0, -0.35, f"{kurye_ibre_secim}\nZimmet: {k_zimmet} | Teslim: {k_teslim}", horizontalalignment='center', verticalalignment='center', fontsize=10, color='#8B949E')

        st.pyplot(fig_k_gauge)
else:
    st.info("Henüz grafik oluşturulacak veri girilmedi.")
