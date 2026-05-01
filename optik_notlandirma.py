# -*- coding: utf-8 -*-
"""
OPTİK OKUYUCU OTOMATİK NOTLANDIRMA SİSTEMİ
============================================
Desteklenen TXT Formatları:

  Format A — TC(11) + OgrNo(8) + Cep(10) bitişik (29 hane):
      YILMAZ MEHMET  123456789011234567855551112233  CAEDBBAC...
      → TC=12345678901  OgrNo=12345678  Cep=5551112233

  Format B — TC(11) + OgrNo(8) bitişik, Cep yok (19 hane):
      YILMAZ MEHMET  1234567890112345678 48  AAADBBAB...
      → TC=46750356028  OgrNo=24911148  Cep=""

  Format C — TC ve OgrNo boşlukla ayrılmış (eski format):
      YILMAZ MEHMET  12345678901  12345678  ABCDABCD
      → TC=12345678901  OgrNo=12345678  Cep=""

  ÇAP öğrencilerinde OgrNo başında 'C' harfi olabilir (her formatta).
"""

import pandas as pd
import re
import io
from google.colab import files


# ============================================================
# 1. CEVAP ANAHTARI
# ============================================================

def cevap_anahtari_al():
    """Cevap anahtarını kullanıcıdan al."""
    anahtar = input("📝 Cevap anahtarını girin (örn: ABCDABCD): ").strip().upper()
    if not anahtar:
        raise ValueError("❌ Cevap anahtarı boş olamaz!")
    soru_sayisi = len(anahtar)
    puan = round(100 / soru_sayisi, 4)
    print(f"✅ Cevap anahtarı alındı: {anahtar}")
    print(f"   {soru_sayisi} soru × {puan} puan = 100")
    return anahtar


# ============================================================
# 2. TXT DOSYASINI YÜKLEYİP OKU
# ============================================================

def dosya_yukle():
    """Kullanıcıdan .txt dosyası yüklemesini iste."""
    print("\n📂 Lütfen optik okuyucu .txt dosyanızı yükleyin...")
    uploaded = files.upload()

    for dosya_adi, icerik in uploaded.items():
        if not dosya_adi.lower().endswith(".txt"):
            print(f"⚠️  '{dosya_adi}' bir .txt dosyası değil, atlanıyor.")
            continue
        print(f"✅ Dosya yüklendi: {dosya_adi}")
        for enc in ("utf-8", "cp1254", "latin-1"):
            try:
                return dosya_adi, icerik.decode(enc)
            except UnicodeDecodeError:
                continue

    raise FileNotFoundError("❌ Geçerli bir .txt dosyası yüklenmedi.")


# ============================================================
# 3. SATIR PARSE FONKSİYONU
# ============================================================

def satir_parse_et(satir, satir_no):
    """
    Tek satırı parse eder.
    Başarılıysa dict döner, başarısızsa None döner ve uyarı basar.
    """
    satir = satir.strip()
    if not satir:
        return None

    # ── Sayısal bloğu bul (C öneki dahil) ─────────────────────────────────
    blok_match = re.search(r'(C?\d{11,30})', satir, re.IGNORECASE)
    if not blok_match:
        print(f"⚠️  Satır {satir_no}: Sayısal blok bulunamadı → '{satir[:60]}'")
        return None

    ad_soyad = satir[:blok_match.start()].strip()
    if not ad_soyad:
        print(f"⚠️  Satır {satir_no}: Ad Soyad bulunamadı.")
        return None

    blok     = blok_match.group(1)
    blok_end = blok_match.end()

    cap      = blok.upper().startswith('C')
    rakamlar = blok[1:] if cap else blok   # saf rakam kısmı

    tc = ogr_no = cep = ""

    if len(rakamlar) >= 19:
        # ── Format A / B: TC(11) + OgrNo(8) [+ Cep(10-11)] bitişik ──────────
        tc           = rakamlar[:11]
        ogr_no_rakam = rakamlar[11:19]
        kalan_rakam  = rakamlar[19:]      # varsa cep numarası

        # Cep: 05xxxxxxxxx (11 hane) veya 5xxxxxxxxx (10 hane)
        if re.match(r'^(05\d{9}|5\d{9})$', kalan_rakam):
            cep = kalan_rakam if kalan_rakam.startswith('0') else '0' + kalan_rakam
        # Başka uzunluktaki kalıntılar cep değil — yok say

        ogr_no = ('C' if cap else '') + ogr_no_rakam

    elif len(rakamlar) == 11:
        # ── Format C: TC ayrı, öğrenci no sonraki blokta ─────────────────────
        tc           = rakamlar
        kalan_sonra  = satir[blok_end:].strip()

        ogr_match = re.match(r'^(C?\d{8})', kalan_sonra, re.IGNORECASE)
        if not ogr_match:
            print(f"⚠️  Satır {satir_no}: Öğrenci no bulunamadı → '{kalan_sonra[:30]}'")
            return None

        ogr_no   = ogr_match.group(1).upper()   # C dahil olduğu gibi sakla
        blok_end += ogr_match.end()

        # Cep: öğrenci no'dan sonra gelen 05xx / 5xx bloğu (varsa)
        kalan2    = satir[blok_end:].strip()
        cep_match = re.match(r'^(05\d{9}|5\d{9})', kalan2)
        if cep_match:
            c   = cep_match.group(1)
            cep = c if c.startswith('0') else '0' + c
            blok_end += cep_match.end()

    else:
        print(f"⚠️  Satır {satir_no}: Sayısal blok uzunluğu beklenmedik "
              f"({len(rakamlar)} hane) → '{blok}'")
        return None

    # ── Cevaplar: kalan metinden A-E ve 0 dışı karakterleri temizle ────────
    kalan    = satir[blok_end:].strip()
    kalan    = re.sub(r'\b\d{5,}\b', '', kalan)   # artık rakam kalıntılarını sil
    cevaplar = re.sub(r'[^A-Ea-e0 ]', '', kalan).replace(' ', '0').upper()

    if not cevaplar:
        print(f"⚠️  Satır {satir_no}: Cevaplar bulunamadı.")
        return None

    return {
        "ad_soyad": ad_soyad,
        "tc":       tc,
        "ogr_no":   ogr_no,
        "cevaplar": cevaplar,
        "cep":      cep,
    }


# ============================================================
# 4. NOTLANDIRMA FONKSİYONU
# ============================================================

def ogrenci_puanla(cevaplar, anahtar, satir_no):
    """
    Doğru → 100 / soru_sayısı puan
    Yanlış / Boş ('0') → 0 puan
    """
    puan = round(100 / len(anahtar), 4)

    if len(cevaplar) != len(anahtar):
        print(f"⚠️  Satır {satir_no}: Cevap sayısı ({len(cevaplar)}) ≠ "
              f"anahtar sayısı ({len(anahtar)}) → padding/kesme uygulanıyor.")
        cevaplar = cevaplar.ljust(len(anahtar), '0')[:len(anahtar)]

    return [
        puan if (ogr_c not in ('0', ' ', '') and ogr_c == dogru_c) else 0
        for ogr_c, dogru_c in zip(cevaplar, anahtar)
    ]


# ============================================================
# 5. ANA İŞLEM FONKSİYONU
# ============================================================

def isle(metin, anahtar):
    """TXT içeriğini işle, tüm öğrencileri notlandır."""
    satirlar = metin.splitlines()
    print(f"\n📋 Toplam {len(satirlar)} satır işlenecek...\n")

    sonuclar   = []
    hata_sayisi = 0

    for i, satir in enumerate(satirlar, start=1):
        veri = satir_parse_et(satir, i)
        if veri is None:
            if satir.strip():
                hata_sayisi += 1
            continue

        puanlar = ogrenci_puanla(veri["cevaplar"], anahtar, i)

        kayit = {"ogr_no": veri["ogr_no"]}
        for s_no, puan in enumerate(puanlar, start=1):
            kayit[f"S{s_no}"] = puan

        sonuclar.append({
            **kayit,
            "toplam":   round(sum(puanlar), 2),
            "ad_soyad": veri["ad_soyad"],
            "tc":       veri["tc"],
            "cep":      veri["cep"],
            "cevaplar": veri["cevaplar"],
        })

    print(f"\n✅ {len(sonuclar)} öğrenci başarıyla işlendi.")
    if hata_sayisi:
        print(f"⚠️  {hata_sayisi} satırda hata oluştu.")

    return sonuclar


# ============================================================
# 6. EXCEL OLUŞTURMA FONKSİYONU
# ============================================================

def excel_olustur(sonuclar, anahtar):
    soru_sayisi    = len(anahtar)
    puan_per_s     = round(100 / soru_sayisi, 4)
    soru_kolonlari = [f"S{i}" for i in range(1, soru_sayisi + 1)]
    soru_baslik    = [f"Soru {i} Puanı" for i in range(1, soru_sayisi + 1)]

    # ── Sheet 1: Proliz Not Girişi ─────────────────────────────────────────
    # OgrNo | Soru 1 Puanı | ... | Soru N Puanı  (başlıklı)
    df_proliz = pd.DataFrame(sonuclar)[["ogr_no"] + soru_kolonlari].copy()
    df_proliz.columns = ["Öğrenci Numarası"] + soru_baslik

    # ── Sheet 2: Detaylı Liste ─────────────────────────────────────────────
    df_detay = pd.DataFrame([{
        "Öğrenci Numarası": r["ogr_no"],
        "Adı Soyadı":       r["ad_soyad"],
        "TC No":            r.get("tc", ""),
        "Cep Telefonu":     r.get("cep", ""),
        "Toplam Puan":      r["toplam"],
        **{f"Soru {i} Puanı": r[f"S{i}"] for i in range(1, soru_sayisi + 1)},
    } for r in sonuclar])

    # ── Sheet 3: Özet ──────────────────────────────────────────────────────
    df_ozet = pd.DataFrame([{
        "Öğrenci Numarası": r["ogr_no"],
        "Adı Soyadı":       r["ad_soyad"],
        "TC No":            r.get("tc", ""),
        "Cep Telefonu":     r.get("cep", ""),
        "Toplam Puan":      r["toplam"],
    } for r in sonuclar])

    # ── Sheet 4: Ham TXT ───────────────────────────────────────────────────
    df_ham = pd.DataFrame([{
        "Satır No":         i + 1,
        "Öğrenci Numarası": r["ogr_no"],
        "Adı Soyadı":       r["ad_soyad"],
        "TC No":            r.get("tc", ""),
        "Cep Telefonu":     r.get("cep", ""),
        "Ham Cevaplar":     r.get("cevaplar", ""),
    } for i, r in enumerate(sonuclar)])

    # ── Sheet 5: İşlem Özeti ───────────────────────────────────────────────
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


# ============================================================
# 7. MAIN
# ============================================================

def main():
    print("=" * 55)
    print("  OPTİK OKUYUCU OTOMATİK NOTLANDIRMA SİSTEMİ")
    print("=" * 55)

    anahtar          = cevap_anahtari_al()
    dosya_adi, metin = dosya_yukle()
    sonuclar         = isle(metin, anahtar)

    if not sonuclar:
        print("❌ Hiç öğrenci verisi işlenemedi. Dosya formatını kontrol edin.")
        return

    print("\n📊 Excel dosyası oluşturuluyor...")
    excel_buffer = excel_olustur(sonuclar, anahtar)

    cikti_adi = dosya_adi.rsplit(".", 1)[0] + ".xlsx"
    with open(cikti_adi, "wb") as f:
        f.write(excel_buffer.read())

    cepli = sum(1 for r in sonuclar if r.get("cep"))
    print(f"\n✅ Excel hazır: {cikti_adi}")
    print(f"   • Proliz Not Girişi : {len(sonuclar)} öğrenci, {len(anahtar)} soru")
    print(f"   • Detaylı Liste     : TC + Cep dahil")
    print(f"   • Özet              : {len(sonuclar)} öğrenci")
    print(f"   • Ham TXT           : ham cevap dizileri")
    print(f"   • İşlem Özeti       : anahtar & puan bilgisi")
    print(f"   • Cep tespit edilen : {cepli} öğrenci")
    print("\n⬇️  İndirme başlıyor...")
    files.download(cikti_adi)
    print("🎉 Tamamlandı!")


main()
