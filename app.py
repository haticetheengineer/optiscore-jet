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
    """
    Desteklenen formatlar (TC + OgrNo bitişik, Cep opsiyonel):

    Format A — TC(11) + OgrNo(8) + Cep(10/11) hepsi bitişik (29-30 hane):
        ELMALI MUSTAFA   42958234984249111345445617338   CAEDBBAC...
        → TC=42958234984  OgrNo=24911134  Cep=5445617338

    Format B — TC(11) + OgrNo(8) bitişik, Cep yok (19 hane):
        BAYER EBRAR   46750356028249111 48   AAADBBAB...
        → TC=46750356028  OgrNo=24911148  Cep=""

    Format C — TC(11) ve OgrNo(8) boşlukla ayrılmış (eski format):
        ALİ YILMAZ   12345678901   20230001   ABCDABCD
        → TC=12345678901  OgrNo=20230001  Cep=""

    Öğrenci No "C" önekiyle de gelebilir (ÇAP öğrencisi):
        TC+C+OgrNo bitişik: 12345678901C12345678  veya ayrı
    """
    satir = satir.strip()
    if not satir:
        return None, None

    # ── Sayısal bloğu bul (C öneki dahil) ────────────────────────────────────
    # Ad Soyad'ın bitmesi için: satır başında harf+boşluk, ardından rakam/C bloğu
    blok_match = re.search(r'(C?\d{11,30})', satir, re.IGNORECASE)
    if not blok_match:
        return None, f"Sayısal blok bulunamadı → {satir[:60]}"

    ad_soyad = satir[:blok_match.start()].strip()
    if not ad_soyad:
        return None, "Ad Soyad boş"

    blok = blok_match.group(1)
    blok_end = blok_match.end()

    cap = blok.upper().startswith('C')
    rakamlar = blok[1:] if cap else blok   # saf rakam kısmı

    tc = ""
    ogr_no = ""
    cep = ""

    if len(rakamlar) >= 19:
        # ── Format A/B: TC(11) + OgrNo(8) + [Cep(10-11)] bitişik ─────────────
        tc           = rakamlar[:11]
        ogr_no_rakam = rakamlar[11:19]
        kalan_rakam  = rakamlar[19:]          # 10-11 hane ise cep numarası

        # Cep: 0 ile başlıyorsa 11 hane, 5 ile başlıyorsa 10 hane
        if re.match(r'^(05\d{9}|5\d{9})$', kalan_rakam):
            cep = kalan_rakam if kalan_rakam.startswith('0') else '0' + kalan_rakam
        elif kalan_rakam:
            # Cep değil ama fazladan rakam var — yok say
            cep = ""

        ogr_no = ('C' if cap else '') + ogr_no_rakam

    elif len(rakamlar) == 11:
        # ── Format C: TC ayrı, öğrenci no sonraki boşlukla ayrılmış blok ──────
        tc = rakamlar
        kalan_sonra = satir[blok_end:].strip()

        ogr_match = re.match(r'^(C?\d{8})', kalan_sonra, re.IGNORECASE)
        if not ogr_match:
            return None, f"Öğrenci no bulunamadı → {kalan_sonra[:30]}"

        ogr_blok = ogr_match.group(1).upper()
        cap_ogr  = ogr_blok.startswith('C')
        ogr_no   = ogr_blok  # C dahil olduğu gibi sakla
        blok_end += ogr_match.end()

        # Cep: öğrenci no'dan sonra gelen 05xx / 5xx bloğu
        kalan2 = satir[blok_end:].strip()
        cep_match = re.match(r'^(05\d{9}|5\d{9})', kalan2)
        if cep_match:
            c = cep_match.group(1)
            cep = c if c.startswith('0') else '0' + c
            blok_end += cep_match.end()

    else:
        return None, f"Sayısal blok uzunluğu beklenmedik ({len(rakamlar)} hane) → {blok}"

    # ── Cevaplar: kalan metinden A-E ve 0 dışı karakterleri temizle ──────────
    # Öğrenci no'dan / cep'ten SONRA kalan kısım cevap alanı
    kalan = satir[blok_end:].strip()

    # Kalan rakam bloklarını temizle (başka sayısal kalıntı varsa)
    kalan = re.sub(r'\b\d{5,}\b', '', kalan)

    cevaplar = re.sub(r'[^A-Ea-e0 ]', '', kalan).replace(' ', '0').upper()

    if not cevaplar:
        return None, "Cevaplar boş"

    return {
        "ad_soyad": ad_soyad,
        "tc":       tc,
        "ogr_no":   ogr_no,
        "cevaplar": cevaplar,
        "cep":      cep,
    }, None


def puan_per_soru(anahtar):
    return 100 / len(anahtar)


def ogrenci_puanla(cevaplar, anahtar):
    puan = puan_per_soru(anahtar)
    cevaplar = cevaplar.ljust(len(anahtar), '0')[:len(anahtar)]
    return [
        round(puan, 4) if (c not in ('0', ' ', '') and c == a) else 0
        for c, a in zip(cevaplar, anahtar)
    ]


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
        kayit = {
            "ogr_no":   veri["ogr_no"],
            "ad_soyad": veri["ad_soyad"],
            "tc":       veri["tc"],
            "cep":      veri["cep"],
            "cevaplar": veri["cevaplar"],
        }
        for s, p in enumerate(puanlar, 1):
            kayit[f"S{s}"] = p
        kayit["toplam"] = round(sum(puanlar), 2)
        sonuclar.append(kayit)

    return sonuclar, hatalar


def excel_olustur(sonuclar, anahtar):
    soru_sayisi    = len(anahtar)
    puan_per_s     = round(100 / soru_sayisi, 4)
    soru_kolonlari = [f"S{i}" for i in range(1, soru_sayisi + 1)]
    soru_baslik    = [f"Soru {i} Puanı" for i in range(1, soru_sayisi + 1)]

    # ── Sheet 1: Proliz Not Girişi (başlıklı, ogr_no + soru puanları) ────────
    df_proliz = pd.DataFrame(sonuclar)[["ogr_no"] + soru_kolonlari].copy()
    df_proliz.columns = ["Öğrenci Numarası"] + soru_baslik

    # ── Sheet 2: Detaylı Liste ────────────────────────────────────────────────
    df_detay = pd.DataFrame([{
        "Öğrenci Numarası": r["ogr_no"],
        "Adı Soyadı":       r["ad_soyad"],
        "TC No":            r.get("tc", ""),
        "Cep Telefonu":     r.get("cep", ""),
        "Toplam Puan":      r["toplam"],
        **{f"Soru {i} Puanı": r[f"S{i}"] for i in range(1, soru_sayisi + 1)},
    } for r in sonuclar])

    # ── Sheet 3: Özet ─────────────────────────────────────────────────────────
    df_ozet = pd.DataFrame([{
        "Öğrenci Numarası": r["ogr_no"],
        "Adı Soyadı":       r["ad_soyad"],
        "TC No":            r.get("tc", ""),
        "Cep Telefonu":     r.get("cep", ""),
        "Toplam Puan":      r["toplam"],
    } for r in sonuclar])

    # ── Sheet 4: Ham TXT ──────────────────────────────────────────────────────
    df_ham = pd.DataFrame([{
        "Satır No":         i + 1,
        "Öğrenci Numarası": r["ogr_no"],
        "Adı Soyadı":       r["ad_soyad"],
        "TC No":            r.get("tc", ""),
        "Cep Telefonu":     r.get("cep", ""),
        "Ham Cevaplar":     r.get("cevaplar", ""),
    } for i, r in enumerate(sonuclar)])

    # ── Sheet 5: İşlem Özeti ──────────────────────────────────────────────────
    df_islem = pd.DataFrame([
        {"Bilgi": "Soru Sayısı",             "Değer": soru_sayisi},
        {"Bilgi": "Soru Başına Puan",        "Değer": puan_per_s},
        {"Bilgi": "İşlenen Öğrenci Sayısı", "Değer": len(sonuclar)},
        {"Bilgi": "Cevap Anahtarı",          "Değer": anahtar},
    ])

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_proliz.to_excel(writer, sheet_name="Proliz Not Girişi", index=False)
        df_detay.to_excel(writer,  sheet_name="Detaylı Liste",      index=False)
        df_ozet.to_excel(writer,   sheet_name="Özet",               index=False)
        df_ham.to_excel(writer,    sheet_name="Ham TXT",             index=False)
        df_islem.to_excel(writer,  sheet_name="İşlem Özeti",         index=False)
    buf.seek(0)
    return buf


# ══════════════════════════════════════════════════════════════════════════════
# ARAYÜZ
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="hero">
  <h1>Optik <span>Notlandırma</span></h1>
  <p>TXT → Excel otomatik dönüşüm & puanlama sistemi</p>
</div>
""", unsafe_allow_html=True)

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

if not isle_btn:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style="background:#1a1926;border:1px solid #2a2838;border-radius:12px;padding:1.8rem;">
            <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:#fff;margin-bottom:1rem;">
                📌 TXT Format Beklentisi
            </div>
            <div style="font-family:'DM Mono',monospace;font-size:0.82rem;color:#7a7890;line-height:2.2;">
                <span style="color:#7c6af7;">Format A</span> — TC+OgrNo+Cep bitişik (29-30 hane):<br>
                ELMALI MUSTAFA 42958234984<b style="color:#e8e6f0;">24911134</b><b style="color:#4ade80;">5445617338</b> CAEDBBAC…<br><br>
                <span style="color:#7c6af7;">Format B</span> — TC+OgrNo bitişik, Cep yok (19 hane):<br>
                BAYER EBRAR 4675035602824911148 AAADBBAB…<br><br>
                <span style="color:#7c6af7;">Format C</span> — TC ve OgrNo boşlukla ayrılmış:<br>
                ALİ YILMAZ 12345678901 20230001 ABCDABCD<br><br>
                <span style="color:#7a7890;">ÇAP öğrencisi için OgrNo başında C harfi olabilir.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="background:#1a1926;border:1px solid #2a2838;border-radius:12px;padding:1.8rem;">
            <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:#fff;margin-bottom:1rem;">
                📊 Çıktı Yapısı (5 Sheet)
            </div>
            <div style="font-size:0.85rem;color:#7a7890;line-height:2.4;">
                <span style="color:#7c6af7;">Proliz Not Girişi</span> → OgrNo + Soru puanları<br>
                <span style="color:#7c6af7;">Detaylı Liste</span> → OgrNo + Ad + TC + Cep + Toplam + Sorular<br>
                <span style="color:#4ade80;">Özet</span> → OgrNo + Ad + TC + Cep + Toplam<br>
                <span style="color:#4ade80;">Ham TXT</span> → Satır No + Ham cevap dizisi<br>
                <span style="color:#fbbf24;">İşlem Özeti</span> → Soru sayısı, puan, anahtar<br><br>
                Doğru → <b style="color:#4ade80;">100 ÷ soru sayısı</b> &nbsp;|&nbsp; Yanlış/Boş → <b style="color:#f87171;">0</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

elif not anahtar_input:
    st.warning("⚠️ Lütfen sol panelden cevap anahtarını girin.")

elif not yuklenen:
    st.warning("⚠️ Lütfen sol panelden bir TXT dosyası yükleyin.")

else:
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

    # — Metrik kartlar ─────────────────────────────────────────────────────────
    toplamlar  = [r["toplam"] for r in sonuclar]
    soru_sayisi = len(anahtar_input)
    soru_puani  = round(100 / soru_sayisi, 2)
    ort         = sum(toplamlar) / len(toplamlar)
    gecme       = sum(1 for t in toplamlar if t >= 50)
    cepli       = sum(1 for r in sonuclar if r.get("cep"))

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

    # — Hatalar ────────────────────────────────────────────────────────────────
    if hatalar:
        with st.expander(f"⚠️ {len(hatalar)} satırda sorun tespit edildi", expanded=False):
            for h in hatalar:
                st.markdown(f'<div class="warn-box">{h}</div>', unsafe_allow_html=True)

    # — Önizleme tablosu ───────────────────────────────────────────────────────
    st.markdown("#### 📋 Kontrol Tablosu (İlk 20 Öğrenci)")
    df_onizleme = pd.DataFrame([{
        "Öğrenci No":    r["ogr_no"],
        "Ad Soyad":      r["ad_soyad"],
        "TC":            r["tc"],
        "Cep":           r["cep"] if r["cep"] else "—",
        "Toplam (100)":  r["toplam"],
    } for r in sonuclar]).head(20)

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

    # — İndirme butonu ─────────────────────────────────────────────────────────
    st.markdown("---")
    excel_buf = excel_olustur(sonuclar, anahtar_input)

    st.download_button(
        label="⬇️  Excel İndir  (sonuc.xlsx)",
        data=excel_buf,
        file_name=yuklenen.name.rsplit(".", 1)[0] + ".xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=False,
    )
    st.markdown(
        f'<div class="ok-box">✅ Excel hazır — 5 sheet · {len(sonuclar)} öğrenci · Cep tespit edilen: {cepli}</div>',
        unsafe_allow_html=True
    )
