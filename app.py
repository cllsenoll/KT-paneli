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

# --- Metin Normalleştirme (Sütun Adı & Veri Eşleştirme İçin) ---
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
        "personel", "zimmet", "teslim_edildi", "teslim_edilmedi_bekletiliyor", "sms", "imza", "ks", "nakit", "kart"
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

# ==========================================
# 📁 EXCEL DOSYASI İLE OTOMATİK VERİ İŞLEME
# ==========================================
st.subheader("📁 Excel Dosyasından Otomatik Aktarım")

uploaded_file = st.file_uploader("Kargo Excel Dosyanızı Yükleyin (.xlsx, .xls veya .csv)", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        file_bytes = uploaded_file.getvalue()
        df_raw = None

        # 1. DENEME: Eski Format Excel (.xls)
        try:
            df_raw = pd.read_excel(io.BytesIO(file_bytes), engine="xlrd")
        except Exception:
            pass

        # 2. DENEME: Yeni Format Excel (.xlsx)
        if df_raw is None:
            try:
                df_raw = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
            except Exception:
                pass

        # 3. DENEME: Genel read_excel
        if df_raw is None:
            try:
                df_raw = pd.read_excel(io.BytesIO(file_bytes))
            except Exception:
                pass

        # 4. DENEME: CSV
        if df_raw is None:
            for enc in ["latin5", "utf-8", "iso-8859-9"]:
                for sep in [";", ",", "\t"]:
                    try:
                        df_raw = pd.read_csv(io.BytesIO(file_bytes), sep=sep, encoding=enc, on_bad_lines="skip")
                        if len(df_raw.columns) > 1:
                            break
                    except Exception:
                        pass
                if df_raw is not None and len(df_raw.columns) > 1:
                    break

        # 5. DENEME: HTML Tablosu
        if df_raw is None:
            try:
                dfs = pd.read_html(io.BytesIO(file_bytes))
                if dfs:
                    df_raw = dfs[0]
            except Exception:
                pass

        if df_raw is None:
            st.error("❌ Dosya biçimi okunamadı. Lütfen geçerli bir Excel veya CSV dosyası yükleyin.")
        else:
            # Esnek Sütun Eşleştirme
            col_map = {}
            for c in df_raw.columns:
                norm_c = normalize_text(c)
                
                # Zimmet Personeli
                if any(k in norm_c for k in ["zimmet personel", "at zimmet", "kurye", "dağıtıcı", "dagitici"]):
                    col_map["zimmet_personel"] = c
                
                # Teslim / Kargo Durumu
                elif any(k in norm_c for k in ["teslim durumu", "kargo durumu", "son durum", "durum", "teslimat durumu"]):
                    col_map["durum"] = c
                
                # Teslimat Kanalı
                elif any(k in norm_c for k in ["teslimat kanali", "kanal", "teslim tipi"]):
                    col_map["kanal"] = c
                
                # Açıklama
                elif "aciklama" in norm_c or "açıklama" in norm_c:
                    col_map["aciklama"] = c
                
                # Firma / Alıcı Adı
                elif any(k in norm_c for k in ["alici", "alici adi", "firma", "musteri", "unvan"]):
                    col_map["firma"] = c

                # Tahsilat Tutarı / Ücret
                elif any(k in norm_c for k in ["tutar", "ucret", "fiyat", "tahsilat tutari", "bedel"]):
                    col_map["tutar"] = c

                # Ödeme / Tahsilat Tipi
                elif any(k in norm_c for k in ["odeme tipi", "odeme türü", "tahsilat tipi", "odeme karsi"]):
                    col_map["odeme_tipi"] = c

            if "durum" not in col_map:
                for c in df_raw.columns:
                    norm_c = normalize_text(c)
                    if "teslim" in norm_c and c not in col_map.values():
                        col_map["durum"] = c
                        break

            gerekli_anahtarlar = ["zimmet_personel", "durum"]
            eksikler = [k for k in gerekli_anahtarlar if k not in col_map]

            if eksikler:
                st.error(f"Excel dosyasında zimmet personeli veya durum sütunları tespit edilemedi. Dosyadaki sütunlar: {list(df_raw.columns)}")
            else:
                df = df_raw.copy()
                df["zimmet_personel"] = df[col_map["zimmet_personel"]].astype(str).str.strip()
                df["durum"] = df[col_map["durum"]].astype(str).str.strip()
                
                df["kanal"] = df[col_map["kanal"]].astype(str).str.strip() if "kanal" in col_map else ""
                df["aciklama"] = df[col_map["aciklama"]].astype(str).str.strip() if "aciklama" in col_map else ""
                df["firma"] = df[col_map["firma"]].astype(str).str.strip() if "firma" in col_map else ""
                df["odeme_tipi"] = df[col_map["odeme_tipi"]].astype(str).str.strip() if "odeme_tipi" in col_map else ""

                # Tutar temizleme ve sayıya çevirme
                if "tutar" in col_map:
                    df["tutar"] = df[col_map["tutar"]].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
                    df["tutar"] = pd.to_numeric(df["tutar"], errors="coerce").fillna(0.0)
                else:
                    df["tutar"] = 0.0

                kullanici_ozet = []
                otomatik_tahsilat_listesi = []
                personeller = df["zimmet_personel"].unique()

                for p in personeller:
                    if p.lower() in ["nan", "", "none", "null"]:
                        continue
                    
                    p_df = df[df["zimmet_personel"] == p]
                    zimmet_sayisi = len(p_df)

                    teslim_edildi_sayisi = 0
                    teslim_edilmedi_bekletiliyor_sayisi = 0

                    sms_sayisi = 0
                    imza_sayisi = 0
                    ks_sayisi = 0

                    auto_nakit = 0.0
                    auto_kart = 0.0

                    for _, row in p_df.iterrows():
                        norm_durum = normalize_text(row["durum"])
                        is_teslim = any(k in norm_durum for k in ["teslim edildi", "teslimat yapildi", "teslim yapildi", "teslimdir"]) or norm_durum == "teslim"
                        
                        tutar_val = float(row["tutar"])
                        firma_val = str(row["firma"]) if row["firma"] and str(row["firma"]).lower() not in ["nan", "none", ""] else "Firma/Alıcı Belirtilmedi"
                        odeme_tipi_val = normalize_text(row["odeme_tipi"])
                        aciklama_val = str(row["aciklama"])

                        if is_teslim:
                            teslim_edildi_sayisi += 1
                            
                            kanal_val = str(row["kanal"]).upper()

                            if "SMS" in kanal_val:
                                sms_sayisi += 1
                            elif "İMZA" in kanal_val or "IMZA" in kanal_val:
                                imza_sayisi += 1
                            elif "KAPIYA BIRAKILDI" in kanal_val or "KS" in kanal_val:
                                ks_sayisi += 1
                            elif ("POS ENTEGRASYON" in aciklama_val.upper()):
                                ks_sayisi += 1
                            else:
                                ks_sayisi += 1

                            # OTOMATİK TAHSİLAT HESAPLAMA VE FİRMA LİSTESİNE AKTARIM
                            if tutar_val > 0:
                                if "nakit" in odeme_tipi_val or "nakıt" in odeme_tipi_val:
                                    auto_nakit += tutar_val
                                    otomatik_tahsilat_listesi.append({
                                        "Personel": p,
                                        "Firma Adı": firma_val,
                                        "Tutar (₺)": tutar_val,
                                        "Açıklama": "Excel Otomatik Aktarım (Nakit)"
                                    })
                                elif any(k in odeme_tipi_val for k in ["kart", "pos", "kredi"]):
                                    auto_kart += tutar_val
                                    otomatik_tahsilat_listesi.append({
                                        "Personel": p,
                                        "Firma Adı": firma_val,
                                        "Tutar (₺)": tutar_val,
                                        "Açıklama": "Excel Otomatik Aktarım (Kredi Kartı / POS)"
                                    })
                                else:
                                    # Ödeme tipi belirtilmemişse varsayılan olarak firmaya kaydet
                                    otomatik_tahsilat_listesi.append({
                                        "Personel": p,
                                        "Firma Adı": firma_val,
                                        "Tutar (₺)": tutar_val,
                                        "Açıklama": "Excel Otomatik Aktarım"
                                    })
                        else:
                            teslim_edilmedi_bekletiliyor_sayisi += 1

                    kullanici_ozet.append({
                        "personel": p,
                        "zimmet": zimmet_sayisi,
                        "teslim_edildi": teslim_edildi_sayisi,
                        "teslim_edilmedi_bekletiliyor": teslim_edilmedi_bekletiliyor_sayisi,
                        "sms": sms_sayisi,
                        "imza": imza_sayisi,
                        "ks": ks_sayisi,
                        "nakit": auto_nakit,
                        "kart": auto_kart
                    })

                new_df = pd.DataFrame(kullanici_ozet)

                st.session_state.veriler = new_df
                if otomatik_tahsilat_listesi:
                    st.session_state.tahsilatlar = pd.DataFrame(otomatik_tahsilat_listesi)

                for p in personeller:
                    if p and p.lower() not in ["nan", "none", ""] and p not in st.session_state.personeller:
                        st.session_state.personeller.append(p)

                st.success("✅ Dosya başarıyla analiz edildi! Personel performansları ve firma tahsilat listesi otomatik oluşturuldu.")

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

toplam_nakit = float(df_veriler["nakit"].sum()) if not df_veriler.empty else 0.0
toplam_kart = float(df_veriler["kart"].sum()) if not df_veriler.empty else 0.0
toplam_tahsilat = toplam_nakit + toplam_kart

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Toplam Teslim Edildi", f"{toplam_teslim_edildi} Adet")
kpi2.metric("Teslim Edilmedi / Bekletiliyor şubede", f"{toplam_teslim_edilmedi_bekletiliyor} Adet")
kpi3.metric("Toplam Tahsilat", f"{toplam_tahsilat:,.2f} ₺")

st.markdown("---")

# ==========================================
# 3. PERSONEL BAZLI TESLİM EDİLDİ VS TESLİM EDİLMEDİ / BEKLETİLİYOR ŞUBEDE
# ==========================================
st.markdown("### 📦 Personel Bazlı Teslim Edildi vs Teslim Edilmedi / Bekletiliyor şubede")

if not df_veriler.empty:
    fig_bar, ax_bar = plt.subplots(figsize=(6, 4))
    fig_bar.patch.set_facecolor('#0E1117')
    ax_bar.set_facecolor('#161B22')

    personel_names = df_veriler["personel"].tolist()
    y = range(len(personel_names))
    height = 0.35

    rects1 = ax_bar.barh([i - height/2 for i in y], df_veriler["teslim_edildi"], height, label='Teslim Edildi', color='#10B981')
    rects2 = ax_bar.barh([i + height/2 for i in y], df_veriler["teslim_edilmedi_bekletiliyor"], height, label='Teslim Edilmedi / Bekletiliyor şubede', color='#EF4444')

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
        p_teslim_edildi = int(row["teslim_edildi"])
        p_bekletiliyor = int(row["teslim_edilmedi_bekletiliyor"])
    else:
        p_zimmet, p_teslim_edildi, p_bekletiliyor = 0, 0, 0

    fig_personel = ibre_grafik_ciz(p_teslim_edildi, p_bekletiliyor, p_zimmet, "Personel Teslim Performansı", personel_ibre_secim)
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
        teslim_edildi = st.number_input("Teslim Edildi:", min_value=0, value=int(mevcut_row["teslim_edildi"].values[0]) if not mevcut_row.empty else 0)
        teslim_edilmedi_bekletiliyor = st.number_input("Teslim Edilmedi / Bekletiliyor şubede:", min_value=0, value=int(mevcut_row["teslim_edilmedi_bekletiliyor"].values[0]) if not mevcut_row.empty else 0)
    with col2:
        sms = st.number_input("SMS ile Teslim Edildi:", min_value=0, value=int(mevcut_row["sms"].values[0]) if not mevcut_row.empty else 0)
        imza = st.number_input("İmza ile Teslim Edildi:", min_value=0, value=int(mevcut_row["imza"].values[0]) if not mevcut_row.empty else 0)
        ks = st.number_input("KS ile Teslim Edildi:", min_value=0, value=int(mevcut_row["ks"].values[0]) if not mevcut_row.empty else 0)

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
        "teslim_edildi": teslim_edildi,
        "teslim_edilmedi_bekletiliyor": teslim_edilmedi_bekletiliyor,
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

# Seçili Personelin Mevcut Firma Tahsilat Listesi
if not df_tahsilat.empty and "Personel" in df_tahsilat.columns:
    personel_tahsilatlari = df_tahsilat[df_tahsilat["Personel"] == personel_firma_secim]
    if not personel_tahsilatlari.empty:
        st.markdown(f"**{personel_firma_secim} - Aktarılan/Kayıtlı Firma Tahsilatları:**")
        df_goster = personel_tahsilatlari.reset_index(drop=True)
        df_goster.index = range(1, len(df_goster) + 1)
        st.dataframe(df_goster[["Firma Adı", "Tutar (₺)", "Açıklama"]], use_container_width=True)
    else:
        st.info(f"{personel_firma_secim} için henüz firma tahsilat kaydı bulunmuyor.")

with st.form("firma_tahsilat_formu"):
    st.markdown("**Ek Manuel Firma Tahsilatı Ekle:**")
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
            "Açıklama": firma_aciklama.strip() if firma_aciklama.strip() else "Manuel Eklendi"
        }
        yeni_tahsilat_df = pd.DataFrame([yeni_tahsilat])
        
        st.session_state.tahsilatlar = pd.concat([st.session_state.tahsilatlar, yeni_tahsilat_df], ignore_index=True)
        st.success(f"✓ {firma_adi} için {firma_tutar:,.2f} ₺ tahsilat eklendi.")
        st.rerun()
    else:
        st.error("Lütfen Firma Adı ve 0'dan büyük Tutar giriniz.")

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
