import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io

# Güncel Görsel Bağlantısı
LOGO_URL = "https://raw.githubusercontent.com/cllsenoll/KT-paneli/refs/heads/main/1000122774.png"

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Personel Performans Paneli", 
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

# --- Metin Normalleştirme (Sütun Adı Eşleştirme İçin) ---
def normalize_text(text):
    text = str(text).strip().lower()
    text = text.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
    return text

# --- OTURUM / DAHİLİ HAFIZA (SESSION STATE) BAŞLATMA ---
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
        "personel", "zimmet", "teslim", "devir", "sms", "imza", "ks", "nakit", "kart"
    ])

if "tahsilatlar" not in st.session_state:
    st.session_state.tahsilatlar = pd.DataFrame(columns=[
        "Personel", "Firma Adı", "Tutar (₺)", "Açıklama"
    ])

# Üst Başlık ve Logo Alanı
col_logo, col_title = st.columns([1, 3])

with col_logo:
    st.image(LOGO_URL, width=90)

with col_title:
    st.title("Personel Performans & Tahsilat Paneli")
    st.caption("Mobil Uyumlu Otomatik Excel İşleme ve Canlı Raporlama")

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
# 📁 EXCEL DOSYASI İLE OTOMATİK VERİ İŞLEME
# ==========================================
st.subheader("📁 Excel Dosyasından Otomatik Aktarım")

uploaded_file = st.file_uploader("Kargo Excel Dosyanızı Yükleyin (.xlsx, .xls veya .csv)", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        file_bytes = uploaded_file.getvalue()
        df_raw = None

        # 1. DENEME: Eski Format Excel (.xls - xlrd motoru ile)
        try:
            df_raw = pd.read_excel(io.BytesIO(file_bytes), engine="xlrd")
        except Exception:
            pass

        # 2. DENEME: Yeni Format Excel (.xlsx - openpyxl motoru ile)
        if df_raw is None:
            try:
                df_raw = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
            except Exception:
                pass

        # 3. DENEME: Motor belirtmeden genel read_excel
        if df_raw is None:
            try:
                df_raw = pd.read_excel(io.BytesIO(file_bytes))
            except Exception:
                pass

        # 4. DENEME: CSV (Noktalı Virgül - Latin5/Türkçe Kodlama)
        if df_raw is None:
            try:
                df_raw = pd.read_csv(io.BytesIO(file_bytes), sep=";", encoding="latin5", on_bad_lines="skip")
            except Exception:
                pass

        # 5. DENEME: CSV (Virgül - UTF-8 Kodlama)
        if df_raw is None:
            try:
                df_raw = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8", on_bad_lines="skip")
            except Exception:
                pass

        # 6. DENEME: CSV (Noktalı Virgül - UTF-8 Kodlama)
        if df_raw is None:
            try:
                df_raw = pd.read_csv(io.BytesIO(file_bytes), sep=";", encoding="utf-8", on_bad_lines="skip")
            except Exception:
                pass

        # 7. DENEME: Gerçek HTML Tablosu Şeklinde Dışa Aktarılmış .xls Dosyaları
        if df_raw is None:
            try:
                dfs = pd.read_html(io.BytesIO(file_bytes))
                if dfs:
                    df_raw = dfs[0]
            except Exception:
                pass

        if df_raw is None:
            st.error("❌ Dosya biçimi okunamadı. Lütfen dosyanızın geçerli bir Excel veya CSV olduğundan emin olun.")
        else:
            # Esnek Sütun Bulma Mantığı
            col_map = {}
            for c in df_raw.columns:
                norm_c = normalize_text(c)
                if "zimmet personel" in norm_c or "zimmet personel adi" in norm_c or "at zimmet" in norm_c:
                    col_map["zimmet_personel"] = c
                elif "teslim eden" in norm_c or "teslim eden personel" in norm_c:
                    col_map["teslim_personel"] = c
                elif "teslimat kanali" in norm_c or "kargo teslimat kanali" in norm_c:
                    col_map["kanal"] = c
                elif "aciklama" in norm_c or "açıklama" in norm_c:
                    col_map["aciklama"] = c

            gerekli_anahtarlar = ["zimmet_personel", "teslim_personel", "kanal", "aciklama"]
            eksikler = [k for k in gerekli_anahtarlar if k not in col_map]

            if eksikler:
                st.error(f"Excel dosyasında gerekli sütunlar tam olarak eşleştirilemedi. Dosyadaki sütunlar: {list(df_raw.columns)}")
            else:
                # Okuma ve Temizleme
                df = df_raw[[col_map["zimmet_personel"], col_map["teslim_personel"], col_map["kanal"], col_map["aciklama"]]].copy()
                df.columns = ["zimmet_personel", "teslim_personel", "kanal", "aciklama"]

                for col in df.columns:
                    df[col] = df[col].astype(str).str.strip()

                kullanici_ozet = []
                personeller = df["zimmet_personel"].unique()

                for p in personeller:
                    if p == "nan" or not p or p == "None":
                        continue
                    
                    # Personelin zimmetindeki tüm satırlar
                    p_df = df[df["zimmet_personel"] == p]
                    zimmet_sayisi = len(p_df)

                    # Teslim edilenler (Zimmet personeli == Teslim eden personel)
                    teslim_df = p_df[p_df["zimmet_personel"] == p_df["teslim_personel"]]
                    teslim_sayisi = len(teslim_df)
                    devir_sayisi = zimmet_sayisi - teslim_sayisi

                    # Kanal Hesaplamaları
                    sms_sayisi = 0
                    imza_sayisi = 0
                    ks_sayisi = 0

                    for _, row in teslim_df.iterrows():
                        kanal_val = str(row["kanal"]).upper()
                        aciklama_val = str(row["aciklama"]).upper()

                        if "SMS" in kanal_val:
                            sms_sayisi += 1
                        elif "İMZA" in kanal_val or "IMZA" in kanal_val:
                            imza_sayisi += 1
                        elif "KAPIYA BIRAKILDI" in kanal_val:
                            ks_sayisi += 1
                        elif (kanal_val in ["NAN", "", "NONE"]) and ("POS ENTEGRASYON" in aciklama_val):
                            ks_sayisi += 1
                        else:
                            ks_sayisi += 1

                    # Mevcut manuel girilmiş nakit/kart verisini koru
                    mevcut_veriler = st.session_state.veriler
                    nakit_val = 0.0
                    kart_val = 0.0
                    if not mevcut_veriler.empty and p in mevcut_veriler["personel"].values:
                        p_row = mevcut_veriler[mevcut_veriler["personel"] == p].iloc[0]
                        nakit_val = float(p_row.get("nakit", 0.0))
                        kart_val = float(p_row.get("kart", 0.0))

                    kullanici_ozet.append({
                        "personel": p,
                        "zimmet": zimmet_sayisi,
                        "teslim": teslim_sayisi,
                        "devir": devir_sayisi,
                        "sms": sms_sayisi,
                        "imza": imza_sayisi,
                        "ks": ks_sayisi,
                        "nakit": nakit_val,
                        "kart": kart_val
                    })

                new_df = pd.DataFrame(kullanici_ozet)

                # Oturum verisini güncelle
                st.session_state.veriler = new_df
                for p in personeller:
                    if p and p not in ["nan", "None"] and p not in st.session_state.personeller:
                        st.session_state.personeller.append(p)

                st.success("✅ Dosya başarıyla okundu! Tüm veriler ve grafikler güncellendi.")

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
toplam_teslim = int(df_veriler["teslim"].sum()) if not df_veriler.empty else 0
toplam_devir = int(df_veriler["devir"].sum()) if not df_veriler.empty else 0

fig_sube = ibre_grafik_ciz(toplam_teslim, toplam_zimmet, "Şube Teslim Oranı", "Şube Genel Performansı")
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
kpi1.metric("Toplam Teslim", f"{toplam_teslim} Adet")
kpi2.metric("Toplam Devir", f"{toplam_devir} Adet")
kpi3.metric("Toplam Tahsilat", f"{toplam_tahsilat:,.2f} ₺")

st.markdown("---")

# ==========================================
# 3. PERSONEL BAZLI TESLİMAT VS DEVİR
# ==========================================
st.markdown("### 📦 Personel Bazlı Teslimat vs Devir")

if not df_veriler.empty:
    fig_bar, ax_bar = plt.subplots(figsize=(6, 4))
    fig_bar.patch.set_facecolor('#0E1117')
    ax_bar.set_facecolor('#161B22')

    personel_names = df_veriler["personel"].tolist()
    y = range(len(personel_names))
    height = 0.35

    rects1 = ax_bar.barh([i - height/2 for i in y], df_veriler["teslim"], height, label='Teslim', color='#10B981')
    rects2 = ax_bar.barh([i + height/2 for i in y], df_veriler["devir"], height, label='Devir', color='#EF4444')

    ax_bar.set_yticks(y)
    ax_bar.set_yticklabels(personel_names, color='white', fontsize=10)
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
else:
    st.info("Personel bazlı grafik için henüz Excel yüklenmedi veya veri girilmedi.")

st.markdown("---")

# ==========================================
# 4. PERSONEL TESLİM PERFORMANSI
# ==========================================
st.markdown("### ⏱️ Personel Teslim Performansı")

if personel_listesi:
    personel_ibre_secim = st.selectbox("Performansını Görmek İstediğiniz Personel:", personel_listesi)

    if not df_veriler.empty and personel_ibre_secim in df_veriler["personel"].values:
        row = df_veriler[df_veriler["personel"] == personel_ibre_secim].iloc[0]
        p_zimmet = int(row["zimmet"])
        p_teslim = int(row["teslim"])
    else:
        p_zimmet, p_teslim = 0, 0

    fig_personel = ibre_grafik_ciz(p_teslim, p_zimmet, "Personel Teslim Performansı", personel_ibre_secim)
    st.pyplot(fig_personel)

st.markdown("---")

# ==========================================
# 5. GÜNLÜK MANUEL VERİ / TAHSİLAT GİRİŞİ
# ==========================================
st.subheader("📝 Manuel Veri & Tahsilat Düzenleme")
secilen_personel = st.selectbox("Personel Seçin:", personel_listesi)

mevcut_row = df_veriler[df_veriler["personel"] == secilen_personel] if not df_veriler.empty else pd.DataFrame()

with st.form("personel_formu"):
    col1, col2 = st.columns(2)
    with col1:
        zimmet = st.number_input("Zimmetli Kargo:", min_value=0, value=int(mevcut_row["zimmet"].values[0]) if not mevcut_row.empty else 0)
        teslim = st.number_input("Teslim Edilen:", min_value=0, value=int(mevcut_row["teslim"].values[0]) if not mevcut_row.empty else 0)
        devir = st.number_input("Devir Edilen:", min_value=0, value=int(mevcut_row["devir"].values[0]) if not mevcut_row.empty else 0)
    with col2:
        sms = st.number_input("SMS ile Teslim:", min_value=0, value=int(mevcut_row["sms"].values[0]) if not mevcut_row.empty else 0)
        imza = st.number_input("İmza ile Teslim:", min_value=0, value=int(mevcut_row["imza"].values[0]) if not mevcut_row.empty else 0)
        ks = st.number_input("KS ile Teslim:", min_value=0, value=int(mevcut_row["ks"].values[0]) if not mevcut_row.empty else 0)

    st.markdown("---")
    st.markdown("**💳 Genel Tahsilat Tutarları (TL)**")
    col3, col4 = st.columns(2)
    with col3:
        nakit = st.number_input("Nakit Tahsilat (₺):", min_value=0.0, value=float(mevcut_row["nakit"].values[0]) if not mevcut_row.empty else 0.0)
    with col4:
        kart = st.number_input("Kredi Kartı / POS (₺):", min_value=0.0, value=float(mevcut_row["kart"].values[0]) if not mevcut_row.empty else 0.0)

    kaydet_btn = st.form_submit_button("💾 Verileri Kaydet / Güncelle")

if kaydet_btn:
    yeni_veri = {
        "personel": secilen_personel,
        "zimmet": zimmet,
        "teslim": teslim,
        "devir": devir,
        "sms": sms,
        "imza": imza,
        "ks": ks,
        "nakit": nakit,
        "kart": kart
    }
    yeni_df = pd.DataFrame([yeni_veri])

    if not st.session_state.veriler.empty and "personel" in st.session_state.veriler.columns:
        st.session_state.veriler = st.session_state.veriler[st.session_state.veriler["personel"] != secilen_personel]
        st.session_state.veriler = pd.concat([st.session_state.veriler, yeni_df], ignore_index=True)
    else:
        st.session_state.veriler = yeni_df

    st.success(f"✓ {secilen_personel} verileri güncellendi!")
    st.rerun()

st.markdown("---")

# ==========================================
# 6. FİRMA BAZLI ÖZEL TAHSİLAT GİRİŞİ
# ==========================================
st.subheader("🏢 Firma Bazlı Özel Tahsilat Girişi")

personel_firma_secim = st.selectbox("Tahsilat Eklenecek Personel:", personel_listesi, key="personel_firma")

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
            "Personel": personel_firma_secim,
            "Firma Adı": firma_adi.strip(),
            "Tutar (₺)": firma_tutar,
            "Açıklama": firma_aciklama.strip()
        }
        yeni_tahsilat_df = pd.DataFrame([yeni_tahsilat])
        
        st.session_state.tahsilatlar = pd.concat([st.session_state.tahsilatlar, yeni_tahsilat_df], ignore_index=True)
        st.success(f"✓ {firma_adi} için {firma_tutar:,.2f} ₺ tahsilat eklendi.")
        st.rerun()
    else:
        st.error("Lütfen Firma Adı ve 0'dan büyük Tutar giriniz.")

# Seçili Personelin Mevcut Firma Tahsilat Listesi
if not df_tahsilat.empty and "Personel" in df_tahsilat.columns:
    personel_tahsilatlari = df_tahsilat[df_tahsilat["Personel"] == personel_firma_secim]
    if not personel_tahsilatlari.empty:
        st.markdown(f"**{personel_firma_secim} - Kayıtlı Firma Tahsilatları:**")
        df_goster = personel_tahsilatlari.reset_index(drop=True)
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
