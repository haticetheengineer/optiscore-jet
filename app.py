import streamlit as st
import pandas as pd
import re
import io

# ── Sayfa ayarları ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Optik Notlandırma",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Özel CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Ana arka plan */
.stApp {
    background: #0f0f13;
    color: #e8e6f0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #16151d !important;
    border-right: 1px solid #2a2838;
}
[data-testid="stSidebar"] .block-container {
    padding-top: 2rem;
}

/* Başlık */
.hero {
    padding: 2.5rem 0 1.5rem 0;
    border-bottom: 1px solid #2a2838;
    margin-bottom: 2rem;
}
.hero h1 {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: #ffffff;
    margin: 0;
    line-height: 1.1;
}
.hero h1 span {
    color: #7c6af7;
}
.hero p {
    color: #7a7890;
    font-size: 0.95rem;
    margin-top: 0.5rem;
}

/* Metrik kartları */
.metric-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin: 1.5rem 0;
}
.metric-card {
    background: #1a1926;
    border: 1px solid #2a2838;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
}
.metric-card .label {
    font-size: 0.75rem;
    color: #7a7890;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 500;
}
.metric-card .value {
    font-family: 'DM Mono', monospace;
    font-size: 2rem;
    font-weight: 500;
    color: #ffffff;
    margin-top: 0.2rem;
    line-height: 1;
}
.metric-card .value.accent { color: #7c6af7; }
.metric-card .value.green  { color: #4ade80; }
.metric-card .value.amber  { color: #fbbf24; }

/* Adım göstergesi */
.step-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: #1a1926;
    border: 1px solid #2a2838;
    border-radius: 999px;
    padding: 0.3rem 0.8rem;
    font-size: 0.78rem;
    color: #7c6af7;
    font-family: 'DM Mono', monospace;
    margin-bottom: 0.5rem;
}

/* Uyarı/hata kutuları */
.warn-box {
    background: #2a1f00;
    border-left: 3px solid #fbbf24;
    padding: 0.7rem 1rem;
    border-radius: 0 8px 8px 0;
    font-size: 0.85rem;
    color: #fbbf24;
    margin: 0.3rem 0;
    font-family: 'DM Mono', monospace;
}
.ok-box {
    background: #0d2218;
    border-left: 3px solid #4ade80;
    padding: 0.7rem 1rem;
    border-radius: 0 8px 8px 0;
    font-size: 0.85rem;
    color: #4ade80;
    margin: 0.3rem 0;
}

/* Tablo */
.dataframe-container {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #2a2838;
}

/* Input & button override */
.stTextInput > div > div > input {
    background: #1a1926 !important;
    border: 1px solid #2a2838 !important;
    color: #e8e6f0 !important;
    font-family: 'DM Mono', monospace !important;
    border-radius: 8px !important;
    font-size: 1rem !important;
}
.stButton > button {
    background: #7c6af7 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 0.6rem 1.8rem !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #6b59e8 !important;
    transform: translateY(-1px);
}
[data-testid="stDownloadButton"] > button {
    background: #1a2e1a !important;
    border: 1px solid #4ade80 !important;
    color: #4ade80 !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: #0d2218 !important;
}
.stFileUploader {
    background: #1a1926 !important;
    border-radius: 10px !important;
}

/* Divider */
hr { border-color: #2a2838 !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CORE FONKSİYONLAR
# ══════════════════════════════════════════════════════════════════════════════

def satir_parse_et(satir):
    satir = satir.strip()
    if not satir:
        return None, None

    tc_match = re.search(r'\b(\d{11})\b', satir)
    if not tc_match:
        return None, f"TC bulunamadı → {satir[:50]}"

    tc = tc_match.group(1)
    ad_soyad = satir[:tc_match.start()].strip()
    if not ad_soyad:
        return None, "Ad Soyad boş"

    kalan = satir[tc_match.end():].strip()
    ogr_match = re.match(r'^(C\d{8}|\d{8})', kalan, re.IGNORECASE)
    if not ogr_match:
        return None, f"Öğrenci no bulunamadı → {kalan[:30]}"

    ogr_no = ogr_match.group(1).upper()
    cevaplar_ham = kalan[ogr_match.end():].strip()
    cevaplar = re.sub(r'[^A-Ea-e0 ]', '', cevaplar_ham).replace(' ', '0').upper()

    if not cevaplar:
        return None, "Cevaplar boş"

    return {"ad_soyad": ad_soyad, "tc": tc, "ogr_no": ogr_no, "cevaplar": cevaplar}, None


def puan_per_soru(anahtar):
    """Soru başına düşen puanı cevap anahtarı uzunluğundan hesapla: 100 / soru_sayısı"""
    return 100 / len(anahtar)


def ogrenci_puanla(cevaplar, anahtar):
    """Her soru için tam puan veya 0 döndürür. Puan = 100 / soru_sayısı"""
    puan = puan_per_soru(anahtar)
    cevaplar = cevaplar.ljust(len(anahtar), '0')[:len(anahtar)]
    return [round(puan, 4) if (c not in ('0', ' ', '') and c == a) else 0
            for c, a in zip(cevaplar, anahtar)]


def isle(metin, anahtar):
    satirlar = metin.splitlines()
    sonuclar, hatalar = [], []

    for i, satir in enumerate(satirlar, 1):
        veri, hata = satir_parse_et(satir)
        if hata:
            hatalar.append(f"Satır {i}: {hata}")
            continue
        if veri is None:
            continue

        puanlar = ogrenci_puanla(veri["cevaplar"], anahtar)
        kayit = {"ogr_no": veri["ogr_no"], "ad_soyad": veri["ad_soyad"]}
        for s, p in enumerate(puanlar, 1):
            kayit[f"S{s}"] = p
        kayit["toplam"] = round(sum(puanlar), 2)
        sonuclar.append(kayit)

    return sonuclar, hatalar


def excel_olustur(sonuclar, anahtar):
    soru_kolonlari = ["ogr_no"] + [f"S{i}" for i in range(1, len(anahtar) + 1)]
    df_ana = pd.DataFrame(sonuclar)[soru_kolonlari]
    df_kontrol = pd.DataFrame([
        {"Ogrenci No": r["ogr_no"], "Ad Soyad": r["ad_soyad"], "Toplam Puan": r["toplam"]}
        for r in sonuclar
    ])

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_ana.to_excel(writer, sheet_name="SONUCLAR", index=False, header=False)
        df_kontrol.to_excel(writer, sheet_name="KONTROL", index=False)
    buf.seek(0)
    return buf


# ══════════════════════════════════════════════════════════════════════════════
# ARAYÜZ
# ══════════════════════════════════════════════════════════════════════════════

# — Hero başlık ——————————————————————————————————————————————————————————————
st.markdown("""
<div class="hero">
  <h1>Optik <span>Notlandırma</span></h1>
  <p>TXT → Excel otomatik dönüşüm & puanlama sistemi</p>
</div>
""", unsafe_allow_html=True)

# — Sidebar: Girdiler ————————————————————————————————————————————————————————
with st.sidebar:
    st.markdown('<div class="step-badge">① Cevap Anahtarı</div>', unsafe_allow_html=True)
    anahtar_input = st.text_input(
        "Cevap anahtarı",
        placeholder="örn: ABCDABCDABCD",
        label_visibility="collapsed",
    ).strip().upper()

    st.markdown('<div style="margin-top:1.5rem"></div>', unsafe_allow_html=True)
    st.markdown('<div class="step-badge">② Dosya Yükle</div>', unsafe_allow_html=True)
    yuklenen = st.file_uploader(
        "Optik okuyucu TXT dosyası",
        type=["txt"],
        label_visibility="collapsed",
    )

    st.markdown('<div style="margin-top:1.5rem"></div>', unsafe_allow_html=True)
    isle_btn = st.button("▶  Notlandır", use_container_width=True)

# — Ana içerik ————————————————————————————————————————————————————————————————
if not isle_btn:
    # Boş durum
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background:#1a1926;border:1px solid #2a2838;border-radius:12px;padding:1.8rem;">
            <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:#fff;margin-bottom:1rem;">
                📌 TXT Format Beklentisi
            </div>
            <div style="font-family:'DM Mono',monospace;font-size:0.82rem;color:#7a7890;line-height:2;">
                AD SOYAD &nbsp;|&nbsp; 11 haneli TC<br>
                Öğrenci No (8 hane veya C+8)<br>
                Cevaplar (ABCD… veya 0=boş)<br><br>
                <span style="color:#7c6af7;">Örnek:</span><br>
                ALİ YILMAZ 12345678901 20230001 ABCDABCD
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background:#1a1926;border:1px solid #2a2838;border-radius:12px;padding:1.8rem;">
            <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:#fff;margin-bottom:1rem;">
                📊 Çıktı Yapısı
            </div>
            <div style="font-size:0.85rem;color:#7a7890;line-height:2.2;">
                <span style="color:#7c6af7;">SONUCLAR</span> sheet → Öğrenci No + Soru puanları (başlıksız)<br>
                <span style="color:#4ade80;">KONTROL</span> sheet → Öğrenci No + Ad Soyad + Toplam<br><br>
                Doğru → <b style="color:#4ade80;">100 ÷ soru sayısı puan</b> &nbsp;|&nbsp; Yanlış/Boş → <b style="color:#f87171;">0 puan</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

elif not anahtar_input:
    st.warning("⚠️ Lütfen sol panelden cevap anahtarını girin.")

elif not yuklenen:
    st.warning("⚠️ Lütfen sol panelden bir TXT dosyası yükleyin.")

else:
    # Dosyayı oku
    try:
        raw = yuklenen.read()
        for enc in ("utf-8", "cp1254", "latin-1"):
            try:
                metin = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
    except Exception as e:
        st.error(f"Dosya okunamadı: {e}")
        st.stop()

    with st.spinner("İşleniyor…"):
        sonuclar, hatalar = isle(metin, anahtar_input)

    if not sonuclar:
        st.error("Hiç öğrenci verisi işlenemedi. Dosya formatını kontrol edin.")
        st.stop()

    # — Metrik kartlar ————————————————————————————————————————————————————————
    toplamlar = [r["toplam"] for r in sonuclar]
    soru_sayisi = len(anahtar_input)
    soru_puani = round(100 / soru_sayisi, 2)  # her sorunun puanı
    maks_puan = 100                             # her zaman 100 üzerinden
    ort = sum(toplamlar) / len(toplamlar)
    gecme = sum(1 for t in toplamlar if t >= 50)

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="label">Öğrenci</div>
            <div class="value accent">{len(sonuclar)}</div>
        </div>
        <div class="metric-card">
            <div class="label">Soru Sayısı</div>
            <div class="value">{soru_sayisi} <span style="font-size:1rem;color:#7a7890;">× {soru_puani} pt</span></div>
        </div>
        <div class="metric-card">
            <div class="label">Sınıf Ortalaması</div>
            <div class="value green">{ort:.1f}</div>
        </div>
        <div class="metric-card">
            <div class="label">Geçen (≥50)</div>
            <div class="value amber">{gecme}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # — Hatalar ————————————————————————————————————————————————————————————————
    if hatalar:
        with st.expander(f"⚠️ {len(hatalar)} satırda sorun tespit edildi", expanded=False):
            for h in hatalar:
                st.markdown(f'<div class="warn-box">{h}</div>', unsafe_allow_html=True)

    # — Önizleme tablosu ————————————————————————————————————————————————————————
    st.markdown("#### 📋 Kontrol Tablosu (İlk 20 Öğrenci)")
    df_onizleme = pd.DataFrame([
        {"Öğrenci No": r["ogr_no"], "Ad Soyad": r["ad_soyad"], "Toplam (100)": r["toplam"]}
        for r in sonuclar
    ]).head(20)

    st.dataframe(
        df_onizleme,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Toplam (100)": st.column_config.ProgressColumn(
                "Toplam Puan (/100)", min_value=0, max_value=100, format="%.2f"
            ),
        }
    )

    # — İndirme butonu ————————————————————————————————————————————————————————
    st.markdown("---")
    excel_buf = excel_olustur(sonuclar, anahtar_input)

    st.download_button(
        label="⬇️  Excel İndir  (sonuc.xlsx)",
        data=excel_buf,
        file_name="sonuc.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=False,
    )
    st.markdown(
        '<div class="ok-box">✅ Excel hazır — SONUCLAR + KONTROL sheet içeriyor.</div>',
        unsafe_allow_html=True
    )
