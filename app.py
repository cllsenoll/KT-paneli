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
    layout="wide"
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

# Oturum Hafızası (Session State)
if "df_zimmet" not in st.session_state:
    st.session_state.df_zimmet = None

if "df_hesap" not in st.session_state:
    st.session_state.df_hesap = None

if "df_f4" not in st.session_state:
    st.session_state.df_f4 = None

# Üst Başlık ve Logo
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image(LOGO_URL, width=90)
with col_title:
    st.title("Personel Performans & F4 Ödeme Paneli")
    st.caption("Şube & Personel Operasyon Takip Sistemi")

st.markdown("---")

# --- SIDEBAR: DOSYA YÜKLEME PANALİ ---
with st.sidebar:
    st.header("📂 Excel Dosya Yükleme")
    
    file_zimmet = st.file_uploader(
        "1. AT ZİMMET İZLEME Dosyası",
        type=["xlsx", "xls", "csv"],
        key="file_zimmet_input"
    )
    if file_zimmet is not None:
        try:
            st.session_state.df_zimmet = pd.read_excel(file_zimmet)
            st.success("✅ AT ZİMMET İZLEME yüklendi")
        except Exception:
            try:
                st.session_state.df_zimmet = pd.read_csv(file_zimmet)
                st.success("✅ AT ZİMMET İZLEME yüklendi")
            except Exception as e:
                st.error(f"Hata: {e}")

    file_hesap = st.file_uploader(
        "2. PERSONEL HESAP ALIMI EKRANI Dosyası",
        type=["xlsx", "xls", "csv"],
        key="file_hesap_input"
    )
    if file_hesap is not None:
        try:
            st.session_state.df_hesap = pd.read_excel(file_hesap)
            st.success("✅ PERSONEL HESAP ALIMI yüklendi")
        except Exception:
            try:
                st.session_state.df_hesap = pd.read_csv(file_hesap)
                st.success("✅ PERSONEL HESAP ALIMI yüklendi")
            except Exception as e:
                st.error(f"Hata: {e}")

    file_f4 = st.file_uploader(
        "3. F4 ÖDEME LİSTESİ Dosyası",
        type=["xlsx", "xls", "csv"],
        key="file_f4_input"
    )
    if file_f4 is not None:
        try:
            st.session_state.df_f4 = pd.read_excel(file_f4)
            st.success("✅ F4 ÖDEME LİSTESİ yüklendi")
        except Exception:
            try:
                st.session_state.df_f4 = pd.read_csv(file_f4)
                st.success("✅ F4 ÖDEME LİSTESİ yüklendi")
            except Exception as e:
                st.error(f"Hata: {e}")

# Sekmeler
tab1, tab2, tab3 = st.tabs([
    "📊 Zimmet & Performans Analizi",
    "💳 Personel Hesap Alımı",
    "📜 F4 Ödeme Listesi"
])

# ==============================================================================
# TAB 1: YALNIZCA "AT ZİMMET İZLEME" DOSYASI
# ==============================================================================
with tab1:
    st.header("📊 Şube & Zimmet Performans Analizi")
    if st.session_state.df_zimmet is None:
        st.info("📌 Lütfen soldaki menüden **AT ZİMMET İZLEME** Excel dosyasını yükleyin.")
    else:
        df_z = st.session_state.df_zimmet.copy()
        
        # 1. Genel Durum ve Performans Metrikleri
        st.subheader("📌 Genel Durum ve Performans")
        col1, col2, col3, col4 = st.columns(4)
        
        total_kargo = len(df_z)
        teslim_sayisi = len(df_z[df_z['Durum'].astype(str).str.contains('Teslim|TESLİM', na=False)]) if 'Durum' in df_z.columns else 0
        iade_sayisi = len(df_z[df_z['Durum'].astype(str).str.contains('İade|İADE', na=False)]) if 'Durum' in df_z.columns else 0
        dağıtımda_sayisi = total_kargo - (teslim_sayisi + iade_sayisi)
        
        col1.metric("Toplam Zimmet Sayısı", f"{total_kargo:,}")
        col2.metric("Teslim Edilen", f"{teslim_sayisi:,}")
        col3.metric("İade / Kalan", f"{iade_sayisi:,}")
        col4.metric("Dağıtımda / Bekleyen", f"{dağıtımda_sayisi:,}")
        
        st.markdown("---")
        
        # 2. Şube Performansı ve Kanal Dağılımı
        st.subheader("🏢 Şube Performansı ve Kanal Dağılımı")
        col_a, col_b = st.columns(2)
        
        with col_a:
            if 'Kanal' in df_z.columns or 'Teslim Tipi' in df_z.columns:
                kanal_col = 'Kanal' if 'Kanal' in df_z.columns else 'Teslim Tipi'
                counts = df_z[kanal_col].value_counts()
                fig, ax = plt.subplots(figsize=(5, 4))
                fig.patch.set_facecolor('#0E1117')
                ax.set_facecolor('#0E1117')
                ax.pie(counts, labels=counts.index, autopct='%1.1f%%', textprops={'color':"w"})
                ax.set_title("Kanal Dağılımı", color="w")
                st.pyplot(fig)
            else:
                st.write("Kanal bilgisi bulunamadı.")
                
        with col_b:
            sube_col = 'Şube' if 'Şube' in df_z.columns else ('Sube' if 'Sube' in df_z.columns else None)
            if sube_col:
                s_counts = df_z[sube_col].value_counts()
                fig, ax = plt.subplots(figsize=(5, 4))
                fig.patch.set_facecolor('#0E1117')
                ax.set_facecolor('#0E1117')
                ax.bar(s_counts.index.astype(str), s_counts.values, color='#2563EB')
                ax.tick_params(colors='w')
                ax.set_title("Şube Bazlı Zimmet Dağılımı", color="w")
                plt.xticks(rotation=45)
                st.pyplot(fig)
            else:
                st.write("Şube bilgisi bulunamadı.")
        
        st.markdown("---")
        
        # 3. Personel Bazlı Karşılaştırmalı Teslimat Grafiği
        st.subheader("👨‍💼 Personel Bazlı Karşılaştırmalı Teslimat Grafiği")
        personel_col = None
        for p_cand in ['Personel', 'Kurye', 'Dağıtıcı', 'Personel Adı', 'Ad Soyad']:
            if p_cand in df_z.columns:
                personel_col = p_cand
                break
                
        if personel_col:
            p_counts = df_z[personel_col].value_counts().head(10)
            fig, ax = plt.subplots(figsize=(8, 4))
            fig.patch.set_facecolor('#0E1117')
            ax.set_facecolor('#0E1117')
            ax.bar(p_counts.index.astype(str), p_counts.values, color='#10B981')
            ax.tick_params(colors='w')
            ax.set_title("Personel Zimmet Dağılımı", color="w")
            plt.xticks(rotation=30, ha='right')
            st.pyplot(fig)
        else:
            st.warning("Personel sütunu bulunamadı.")
            
        st.markdown("---")
        
        # 4. Personel Zimmet & Teslim Özeti Tablosu
        st.subheader("📋 Personel Zimmet & Teslim Özeti Tablosu")
        if personel_col:
            summary_table = df_z.groupby(personel_col).agg(
                Toplam_Zimmet=(personel_col, 'count')
            ).reset_index()
            st.dataframe(summary_table, use_container_width=True)
        else:
            st.dataframe(df_z, use_container_width=True)


# ==============================================================================
# TAB 2: YALNIZCA "PERSONEL HESAP ALIMI EKRANI" DOSYASI
# ==============================================================================
with tab2:
    st.header("💳 Personel Hesap Alımı")
    if st.session_state.df_hesap is None:
        st.info("📌 Lütfen soldaki menüden **PERSONEL HESAP ALIMI EKRANI** Excel dosyasını yükleyin.")
    else:
        df_h = st.session_state.df_hesap.copy()
        
        # 1. Personel Hesap Alımı Ekranı
        st.subheader("👤 Personel Hesap Alımı Ekranı")
        
        personel_hesap_col = None
        for p_cand in ['Personel', 'Personel Adı', 'Kurye', 'Ad Soyad']:
            if p_cand in df_h.columns:
                personel_hesap_col = p_cand
                break
                
        tahsilat_col = None
        for t_cand in ['Tahsilat', 'Net Tahsilat', 'Toplam Tahsilat', 'Tutar', 'Tahsil Edilen']:
            if t_cand in df_h.columns:
                tahsilat_col = t_cand
                break

        if personel_hesap_col:
            personeller = df_h[personel_hesap_col].dropna().unique().tolist()
            selected_personel = st.selectbox("İncelemek İstediğiniz Personeli Seçin:", personeller)
            
            df_selected = df_h[df_h[personel_hesap_col] == selected_personel]
            st.dataframe(df_selected, use_container_width=True)
            
            if tahsilat_col:
                pers_tahsilat = df_selected[tahsilat_col].sum()
                st.metric(f"👉 {selected_personel} Toplam Tahsilat Tutarı", f"₺{pers_tahsilat:,.2f}")
        else:
            st.dataframe(df_h, use_container_width=True)

        st.markdown("---")
        
        # 2. Tüm Personellerin Hesap Alımı Özeti Tablosu & Toplam Tahsilat
        st.subheader("📊 Tüm Personellerin Hesap Alımı Özeti Tablosu")
        
        if personel_hesap_col and tahsilat_col:
            summary_hesap = df_h.groupby(personel_hesap_col)[tahsilat_col].sum().reset_index()
            summary_hesap.columns = [personel_hesap_col, "Toplam Tahsilat (₺)"]
            
            st.dataframe(summary_hesap, use_container_width=True)
            
            # Tüm Personellerin Toplam Tahsilat Değerlerinin Toplamı
            toplam_tahsilat_tum_personel = summary_hesap["Toplam Tahsilat (₺)"].sum()
            
            st.markdown("### 💰 Listede Bulunan Tüm Personellerin Toplam Tahsilatı")
            st.success(f"**Tüm Personellerin Toplam Tahsilat Değeri:** **₺{toplam_tahsilat_tum_personel:,.2f}**")
        else:
            st.dataframe(df_h, use_container_width=True)
            if tahsilat_col:
                toplam_tahsilat_tum_personel = df_h[tahsilat_col].sum()
                st.success(f"**Tüm Personellerin Toplam Tahsilat Değeri:** **₺{toplam_tahsilat_tum_personel:,.2f}**")


# ==============================================================================
# TAB 3: YALNIZCA "F4 ÖDEME LİSTESİ" DOSYASI
# ==============================================================================
with tab3:
    st.header("📜 F4 Ödeme Listesi (Personel Bazlı Süzgeç)")
    if st.session_state.df_f4 is None:
        st.info("📌 Lütfen soldaki menüden **F4 ÖDEME LİSTESİ** Excel dosyasını yükleyin.")
    else:
        df_f = st.session_state.df_f4.copy()
        
        personel_f4_col = None
        for p_cand in ['Personel', 'Personel Adı', 'Kurye', 'Ad Soyad', 'Teslim Eden']:
            if p_cand in df_f.columns:
                personel_f4_col = p_cand
                break
                
        if personel_f4_col:
            f4_personeller = ["Tüm Personeller"] + df_f[personel_f4_col].dropna().unique().tolist()
            selected_f4_p = st.selectbox("Personel Filtresi:", f4_personeller, key="f4_filter")
            
            if selected_f4_p != "Tüm Personeller":
                df_filtered_f4 = df_f[df_f[personel_f4_col] == selected_f4_p]
            else:
                df_filtered_f4 = df_f.copy()
                
            st.write(f"Görüntülenen Kayıt Sayısı: **{len(df_filtered_f4)}**")
            st.dataframe(df_filtered_f4, use_container_width=True)
        else:
            st.dataframe(df_f, use_container_width=True)
