import json
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# Güncel Görsel Bağlantısı
LOGO_URL = "https://raw.githubusercontent.com/cllsenoll/KT-paneli/refs/heads/main/1000122774.png"

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Kurye Performans Paneli", page_icon=LOGO_URL, layout="centered"
)

# Özel Stil / CSS
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

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
    "Suat Arı",
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
  silinecek_kurye = st.selectbox(
      "Silinecek Kurye Seçin:", st.session_state["kuryeler"]
  )
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


# İbre Grafiği Oluşturma Fonksiyonu (Sol Yeşil / Sağ Kırmızı)
def ibre_grafik_ciz(teslim, zimmet, baslik_metni, alt_metin=""):
  basari_orani = (teslim / zimmet * 100) if zimmet > 0 else 0

  fig, ax = plt.subplots(figsize=(5, 3), subplot_kw={"projection": "polar"})
  fig.patch.set_facecolor("#0E1117")
  ax.set_facecolor("#0E1117")

  # Arka Plan: Sol taraf yeşil (Teslimat), Sağ taraf kırmızı (Devir)
  theta_yesil = np.linspace(np.pi / 2, np.pi, 100)  # Sol Taraf
  theta_kirmizi = np.linspace(0, np.pi / 2, 100)  # Sağ Taraf
  r = 1

  # Arka zemin kavisleri
  ax.plot(theta_yesil, [r] * 100, color="#10B981", linewidth=16, alpha=0.3)
  ax.plot(
      theta_kirmizi, [r] * 100, color="#EF4444", linewidth=16, alpha=0.3
  )

  # Başarı oranına göre canlı ibre dolgusu (Soldan başlayarak yeşil doldurur)
  doluluk_theta = np.linspace(np.pi, np.pi - (basari_orani / 100 * np.pi), 100)
  ax.plot(doluluk_theta, [r] * 100, color="#10B981", linewidth=18)

  ax.set_theta_zero_location("W")
  ax.set_theta_direction(-1)
  ax.set_axis_off()

  ax.text(
      0,
      0,
      f"%{basari_orani:.1f}",
      horizontalalignment="center",
      verticalalignment="center",
      fontsize=22,
      fontweight="bold",
      color="white",
  )
  ax.text(
      0,
      -0.35,
      f"{alt_metin}\nZimmet: {zimmet} | Teslim: {teslim}",
      horizontalalignment="center",
      verticalalignment="center",
      fontsize=10,
      color="#8B949E",
  )

  return fig


# ==========================================
# 1. ŞUBE TESLİM ORANI
# ==========================================
st.markdown("### 🎯 Şube Teslim oranı")

toplam_zimmet = sum(
    v.get("zimmet", 0) for v in st.session_state["veriler"].values()
)
toplam_teslim = sum(
    v.get("teslim", 0) for v in st.session_state["veriler"].values()
)
toplam_devir = sum(
    v.get("devir", 0) for v in st.session_state["veriler"].values()
)

fig_sube = ibre_grafik_ciz(
    toplam_teslim,
    toplam_zimmet,
    "Şube Teslim oranı",
    "Şube Genel Performansı",
)
st.pyplot(fig_sube)

st.markdown("---")

# ==========================================
# 2. GENEL DURUM VE PERFORMANS
# ==========================================
st.subheader("📊 Genel Durum ve Performans")

toplam_nakit = sum(
    v.get("nakit", 0) for v in st.session_state["veriler"].values()
)
toplam_kart = sum(
    v.get("kart", 0) for v in st.session_state["veriler"].values()
)
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

kurye_isimleri = []
teslim_sayilari = []
devir_sayilari = []

for k, v in st.session_state["veriler"].items():
  parcalar = k.split()
  kisa_isim = (
      f"{parcalar[0]} {parcalar[-1]}" if len(parcalar) > 1 else parcalar[0]
  )
  kurye_isimleri.append(kisa_isim)
  teslim_sayilari.append(v.get("teslim", 0))
  devir_sayilari.append(v.get("devir", 0))

if kurye_isimleri:
  fig_bar, ax_bar = plt.subplots(figsize=(6, 4))
  fig_bar.patch.set_facecolor("#0E1117")
  ax_bar.set_facecolor("#161B22")

  y = range(len(kurye_isimleri))
  height = 0.35

  rects1 = ax_bar.barh(
      [i - height / 2 for i in y],
      teslim_sayilari,
      height,
      label="Teslim",
      color="#10B981",
  )
  rects2 = ax_bar.barh(
      [i + height / 2 for i in y],
      devir_sayilari,
      height,
      label="Devir",
      color="#EF4444",
  )

  ax_bar.set_yticks(y)
  ax_bar.set_yticklabels(kurye_isimleri, color="white", fontsize=10)
  ax_bar.tick_params(colors="white")
  ax_bar.spines["top"].set_visible(False)
  ax_bar.spines["right"].set_visible(False)
  ax_bar.spines["left"].set_color("#30363D")
  ax_bar.spines["bottom"].set_color("#30363D")
  ax_bar.legend(facecolor="#161B22", edgecolor="none", labelcolor="white")
  ax_bar.bar_label(rects1, padding=3, color="white", fontsize=9)
  ax_bar.bar_label(rects2, padding=3, color="white", fontsize=9)

  plt.tight_layout()
  st.pyplot(fig_bar)

st.markdown("---")

# ==========================================
# 4. KURYE TESLİM PERFORMANSI
# ==========================================
st.markdown("### ⏱️ Kurye teslim performansı")
kurye_ibre_secim = st.selectbox(
    "Performansını Görmek İstediğiniz Kurye:",
    list(st.session_state["veriler"].keys()),
)

if kurye_ibre_secim in st.session_state["veriler"]:
  v_kurye = st.session_state["veriler"][kurye_ibre_secim]
  k_zimmet = v_kurye.get("zimmet", 0)
  k_teslim = v_kurye.get("teslim", 0)

  fig_kurye = ibre_grafik_ciz(
      k_teslim, k_zimmet, "Kurye teslim performansı", kurye_ibre_secim
  )
  st.pyplot(fig_kurye)

st.markdown("---")

# ==========================================
# 5. GÜNLÜK VERİ GİRİŞİ
# ==========================================
st.subheader("📝 Günlük Veri Girişi")
secilen_kurye = st.selectbox("Kurye Seçin:", st.session_state["kuryeler"])

mevcut = st.session_state["veriler"].get(secilen_kurye, {})

with st.form("kurye_formu"):
  col1, col2 = st.columns(2)
  with col1:
    zimmet = st.number_input(
        "Zimmetli Kargo:", min_value=0, value=int(mevcut.get("zimmet", 0))
    )
    teslim = st.number_input(
        "Teslim Edilen:", min_value=0, value=int(mevcut.get("teslim", 0))
    )
    devir = st.number_input(
        "Devir Edilen:", min_value=0, value=int(mevcut.get("devir", 0))
    )
  with col2:
    sms = st.number_input(
        "SMS ile Teslim:", min_value=0, value=int(mevcut.get("sms", 0))
    )
    imza = st.number_input(
        "İmza ile Teslim:", min_value=0, value=int(mevcut.get("imza", 0))
    )
    ks = st.number_input(
        "KS ile Teslim:", min_value=0, value=int(mevcut.get("ks", 0))
    )

  st.markdown("---")
  st.markdown("**💳 Genel Tahsilat Tutarları (TL)**")
  col3, col4 = st.columns(2)
  with col3:
    nakit = st.number_input(
        "Nakit Tahsilat (₺):", min_value=0.0, value=float(mevcut.get("nakit", 0.0))
    )
  with col4:
    kart = st.number_input(
        "Kredi Kartı / POS (₺):",
        min_value=0.0,
        value=float(mevcut.get("kart", 0.0)),
    )

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
      "kart": kart,
  }
  veri_kaydet(st.session_state["veriler"], VERI_DOSYASI)
  st.success(f"✓ {secilen_kurye} verileri kaydedildi!")
  st.rerun()

st.markdown("---")

# ==========================================
# 6. FİRMA BAZLI ÖZEL TAHSİLAT GİRİŞİ
# ==========================================
st.subheader("🏢 Firma Bazlı Özel Tahsilat Girişi")

kurye_firma_secim = st.selectbox(
    "Tahsilat Eklenecek Kurye:",
    st.session_state["kuryeler"],
    key="kurye_firma",
)

if kurye_firma_secim not in st.session_state["firma_tahsilatlari"]:
  st.session_state["firma_tahsilatlari"][kurye_firma_secim] = []

with st.form("firma_tahsilat_formu"):
  c_f1, c_f2, c_f3 = st.columns([2, 1.5, 2.5])
  with c_f1:
    firma_adi = st.text_input("Firma İsmi:")
  with c_f2:
    firma_tutar = st.number_input(
        "Tahsilat Tutarı (₺):", min_value=0.0, step=10.0
    )
  with c_f3:
    firma_aciklama = st.text_input("Açıklama:")

  firma_kaydet_btn = st.form_submit_button("➕ Firmayı Kaydet")

if firma_kaydet_btn:
  if firma_adi.strip() and firma_tutar > 0:
    st.session_state["firma_tahsilatlari"][kurye_firma_secim].append({
        "Firma Adı": firma_adi.strip(),
        "Tutar (₺)": firma_tutar,
        "Açıklama": firma_aciklama.strip(),
    })
    veri_kaydet(st.session_state["firma_tahsilatlari"], FIRMA_TAHSILAT_DOSYASI)
    st.success(f"✓ {firma_adi} için {firma_tutar:,.2f} ₺ tahsilat eklendi.")
    st.rerun()
  else:
    st.error("Lütfen Firma Adı ve 0'dan büyük Tutar giriniz.")

# Seçili Kuryenin Mevcut Firma Tahsilat Listesi ve Silme İşlemi (1'den Başlayan İndeks)
mevcut_firma_listesi = st.session_state["firma_tahsilatlari"].get(
    kurye_firma_secim, []
)
if mevcut_firma_listesi:
  st.markdown(f"**{kurye_firma_secim} - Kayıtlı Firma Tahsilatları:**")

  df_kurye_firma = pd.DataFrame(mevcut_firma_listesi)
  df_kurye_firma.index = range(1, len(df_kurye_firma) + 1)  # 1'den Başlatma
  st.dataframe(df_kurye_firma, use_container_width=True)

  silinecek_idx = st.number_input(
      "Silmek İstediğiniz Sıra No (1, 2, 3...):",
      min_value=1,
      max_value=len(mevcut_firma_listesi),
      step=1,
  )
  if st.button("❌ Seçilen Firma Tahsilatını Sil"):
    st.session_state["firma_tahsilatlari"][kurye_firma_secim].pop(
        silinecek_idx - 1
    )
    veri_kaydet(st.session_state["firma_tahsilatlari"], FIRMA_TAHSILAT_DOSYASI)
    st.success("Satır silindi!")
    st.rerun()

st.markdown("---")

# ==========================================
# 7. FİRMA TAHSİLAT LİSTESİ ÇIKTI / İNDİR
# ==========================================
st.subheader("🖨️ Firma Tahsilat Listesi (Çıktı / İndir)")

tum_tahsilat_satirlari = []
for kurye_isik, firmalar in st.session_state["firma_tahsilatlari"].items():
  for f in firmalar:
    tum_tahsilat_satirlari.append({
        "Kurye": kurye_isik,
        "Firma Adı": f.get("Firma Adı", ""),
        "Tutar (₺)": f.get("Tutar (₺)", 0.0),
        "Açıklama": f.get("Açıklama", ""),
    })

if tum_tahsilat_satirlari:
  df_tum_tahsilat = pd.DataFrame(tum_tahsilat_satirlari)
  df_tum_tahsilat.index = range(1, len(df_tum_tahsilat) + 1)  # 1'den Başlatma
  st.dataframe(df_tum_tahsilat, use_container_width=True)

  c_d1, c_d2 = st.columns(2)
  with c_d1:
    csv_data = df_tum_tahsilat.to_csv(index=True, encoding="utf-8-sig")
    st.download_button(
        label="📥 Excel / CSV Olarak İndir",
        data=csv_data,
        file_name="firma_tahsilat_listesi.csv",
        mime="text/csv",
    )

  with c_d2:
    # Sayfa Yazdır / PDF İndir Butonu
    st.markdown(
        """
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
    """,
        unsafe_allow_html=True,
    )
else:
  st.info("Henüz firma bazlı tahsilat kaydı bulunmuyor.")
