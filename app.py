import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Sayfa Konfigürasyonu
st.set_page_config(
    page_title="Şube & Personel Operasyon Takip Paneli",
    page_icon="📦",
    layout="wide"
)

st.title("📦 Şube Operasyon ve Personel Takip Sistemi")
st.markdown("---")

# 2. Session State (Oturum Hafızası) Başlatma
if "df_zimmet" not in st.session_state:
    st.session_state.df_zimmet = None

if "df_hesap" not in st.session_state:
    st.session_state.df_hesap = None

if "df_f4" not in st.session_state:
    st.session_state.df_f4 = None

# 3. Sol Menü (Sidebar) Dosya Yükleme Paneli
st.sidebar.header("📂 Excel Dosya Yükleme Paneli")

file_zimmet = st.sidebar.file_uploader(
    "1. AT ZİMMET İZLEME Excel Dosyası",
    type=["xlsx", "xls"],
    key="file_zimmet_input"
)
if file_zimmet is not None:
    try:
        st.session_state.df_zimmet = pd.read_excel(file_zimmet)
        st.sidebar.success("✅ AT ZİMMET İZLEME yüklendi")
    except Exception as e:
        st.sidebar.error(f"AT Zimmet yükleme hatası: {e}")

file_hesap = st.sidebar.file_uploader(
    "2. PERSONEL HESAP ALIMI EKRANI Excel Dosyası",
    type=["xlsx", "xls"],
    key="file_hesap_input"
)
if file_hesap is not None:
    try:
        st.session_state.df_hesap = pd.read_excel(file_hesap)
        st.sidebar.success("✅ PERSONEL HESAP ALIMI yüklendi")
    except Exception as e:
        st.sidebar.error(f"Personel Hesap yükleme hatası: {e}")

file_f4 = st.sidebar.file_uploader(
    "3. F4 ÖDEME LİSTESİ Excel Dosyası",
    type=["xlsx", "xls"],
    key="file_f4_input"
)
if file_f4 is not None:
    try:
        st.session_state.df_f4 = pd.read_excel(file_f4)
        st.sidebar.success("✅ F4 ÖDEME LİSTESİ yüklendi")
    except Exception as e:
        st.sidebar.error(f"F4 Ödeme yükleme hatası: {e}")

# 4. Sekme Düzeni (Tabs)
tab1, tab2, tab3 = st.tabs([
    "📊 Zimmet & Performans Analizi",
    "💳 Personel Hesap Alımı",
    "📜 F4 Ödeme Listesi"
])

# ==============================================================================
# TAB 1: YALNIZCA "AT ZİMMET İZLEME" DOSYASI İLE ÇALIŞAN EKRANLAR
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
        teslim_sayisi = len(df_z[df_z['Durum'].str.contains('Teslim|TESLİM', na=False)]) if 'Durum' in df_z.columns else 0
        iade_sayisi = len(df_z[df_z['Durum'].str.contains('İade|İADE', na=False)]) if 'Durum' in df_z.columns else 0
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
                fig_kanal = px.pie(df_z, names=kanal_col, title="Kanal / Teslim Tipi Dağılımı", hole=0.4)
                st.plotly_chart(fig_kanal, use_container_width=True)
            elif 'Durum' in df_z.columns:
                fig_durum = px.pie(df_z, names='Durum', title="Teslimat Durum Dağılımı", hole=0.4)
                st.plotly_chart(fig_durum, use_container_width=True)
            else:
                st.write("Kanal / Teslim Tipi sütunu bulunamadı.")
                
        with col_b:
            sube_col = 'Şube' if 'Şube' in df_z.columns else ('Sube' if 'Sube' in df_z.columns else None)
            if sube_col:
                sube_summary = df_z[sube_col].value_counts().reset_index()
                sube_summary.columns = [sube_col, 'Adet']
                fig_sube = px.bar(sube_summary, x=sube_col, y='Adet', title="Şube Bazlı Zimmet Dağılımı", color='Adet')
                st.plotly_chart(fig_sube, use_container_width=True)
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
                
        if personel_col and 'Durum' in df_z.columns:
            df_p_summary = df_z.groupby([personel_col, 'Durum']).size().reset_index(name='Adet')
            fig_p = px.bar(
                df_p_summary, x=personel_col, y='Adet', color='Durum', 
                barmode='group', title="Personel Bazlı Teslimat ve İade Performansı"
            )
            st.plotly_chart(fig_p, use_container_width=True)
        elif personel_col:
            df_p_count = df_z[personel_col].value_counts().reset_index()
            df_p_count.columns = [personel_col, 'Toplam Zimmet']
            fig_p = px.bar(df_p_count, x=personel_col, y='Toplam Zimmet', title="Personel Zimmet Dağılımı", color='Toplam Zimmet')
            st.plotly_chart(fig_p, use_container_width=True)
        else:
            st.warning("Personel sütunu bulunamadı.")
            
        st.markdown("---")
        
        # 4. Personel Zimmet & Teslim Özeti Tablosu
        st.subheader("📋 Personel Zimmet & Teslim Özeti Tablosu")
        if personel_col:
            summary_table = df_z.groupby(personel_col).agg(
                Toplam_Zimmet=(personel_col, 'count')
            ).reset_index()
            
            if 'Durum' in df_z.columns:
                teslim_table = df_z[df_z['Durum'].str.contains('Teslim|TESLİM', na=False)].groupby(personel_col).size().reset_index(name='Teslim_Edilen')
                iade_table = df_z[df_z['Durum'].str.contains('İade|İADE', na=False)].groupby(personel_col).size().reset_index(name='İade_Edilen')
                
                summary_table = pd.merge(summary_table, teslim_table, on=personel_col, how='left').fillna(0)
                summary_table = pd.merge(summary_table, iade_table, on=personel_col, how='left').fillna(0)
                summary_table['Başarı_Oranı_(%)'] = ((summary_table['Teslim_Edilen'] / summary_table['Toplam_Zimmet']) * 100).round(2)
                
            st.dataframe(summary_table, use_container_width=True)
        else:
            st.dataframe(df_z, use_container_width=True)


# ==============================================================================
# TAB 2: YALNIZCA "PERSONEL HESAP ALIMI EKRANI" DOSYASI İLE ÇALIŞAN EKRANLAR
# ==============================================================================
with tab2:
    st.header("💳 Personel Hesap Alımı")
    if st.session_state.df_hesap is None:
        st.info("📌 Lütfen soldaki menüden **PERSONEL HESAP ALIMI EKRANI** Excel dosyasını yükleyin.")
    else:
        df_h = st.session_state.df_hesap.copy()
        
        # 1. Personel Hesap Alımı Ekranı (Detaylı Süzgeç)
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
            
            # GÜNCELLENEN ALAN: Tüm Personellerin Toplam Tahsilat Değerlerinin Toplamı
            toplam_tahsilat_tum_personel = summary_hesap["Toplam Tahsilat (₺)"].sum()
            
            st.markdown("### 💰 Listede Bulunan Tüm Personellerin Toplam Tahsilatı")
            st.success(f"**Tüm Personellerin Toplam Tahsilat Değeri:** **₺{toplam_tahsilat_tum_personel:,.2f}**")
        else:
            st.dataframe(df_h, use_container_width=True)
            if tahsilat_col:
                toplam_tahsilat_tum_personel = df_h[tahsilat_col].sum()
                st.success(f"**Tüm Personellerin Toplam Tahsilat Değeri:** **₺{toplam_tahsilat_tum_personel:,.2f}**")


# ==============================================================================
# TAB 3: YALNIZCA "F4 ÖDEME LİSTESİ" DOSYASI İLE ÇALIŞAN EKRANLAR
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
