# ============================================================
# OPTİK OKUYUCU OTOMATIK NOTLANDIRMA SİSTEMİ
# Google Colab Uyumlu | Upload Butonlu | Excel Çıktılı
# ============================================================

import pandas as pd
import re
import io
from google.colab import files

# ============================================================
# 1. CEVAP ANAHTARI (buraya girin veya aşağıdaki input'u kullanın)
# ============================================================

CEVAP_ANAHTARI_MANUEL = ""  # Örnek: "ABCDABCDABCD" — boş bırakılırsa input ile sorulur

def cevap_anahtari_al():
    """Cevap anahtarını kullanıcıdan al."""
    if CEVAP_ANAHTARI_MANUEL.strip():
        anahtar = CEVAP_ANAHTARI_MANUEL.strip().upper()
        print(f"✅ Cevap anahtarı (manuel): {anahtar}")
        return anahtar
    anahtar = input("📝 Cevap anahtarını girin (örn: ABCDABCD): ").strip().upper()
    if not anahtar:
        raise ValueError("❌ Cevap anahtarı boş olamaz!")
    print(f"✅ Cevap anahtarı alındı: {anahtar} ({len(anahtar)} soru)")
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
        try:
            metin = icerik.decode("utf-8")
        except UnicodeDecodeError:
            try:
                metin = icerik.decode("cp1254")  # Türkçe Windows encoding
            except UnicodeDecodeError:
                metin = icerik.decode("latin-1")
        return dosya_adi, metin

    raise FileNotFoundError("❌ Geçerli bir .txt dosyası yüklenmedi.")


# ============================================================
# 3. SATIR PARSE FONKSİYONU
# ============================================================

# ============================================================
# 3. SATIR PARSE FONKSİYONU
# ============================================================

def satir_parse_et(satir, satir_no):
    """
    TC ve öğrenci no bazen bitişik gelir:
      1234567890112345678 → TC=12345678901  OgrNo=12345678  (19 hane)
    Ayrı gelen format da desteklenir:
      12345678901  12345678  (boşlukla ayrılmış)
    ÇAP: C + 19 hane veya C + 8 hane
    """
    satir = satir.strip()
    if not satir:
        return None

    # Sayısal bloğu bul — TC+OgrNo bitişik olabilir (19 hane) veya ayrı (11+8)
    blok_match = re.search(r'(C?\d{11,20})', satir, re.IGNORECASE)
    if not blok_match:
        print(f"⚠️  Satır {satir_no}: Sayısal blok bulunamadı → '{satir[:60]}'")
        return None

    blok      = blok_match.group(1)
    blok_end  = blok_match.end()
    ad_soyad  = satir[:blok_match.start()].strip()

    if not ad_soyad:
        print(f"⚠️  Satır {satir_no}: Ad Soyad bulunamadı.")
        return None

    cap       = blok.upper().startswith('C')
    rakamlar  = blok[1:] if cap else blok   # sadece rakam kısmı

    if len(rakamlar) >= 19:
        # Bitişik: ilk 11 = TC, 11-19 = öğrenci no (8 hane)
        tc           = rakamlar[:11]
        ogr_no_rakam = rakamlar[11:19]

    elif len(rakamlar) == 11:
        # Sadece TC, öğrenci no ayrı boşlukla geliyor
        tc = rakamlar
        kalan_sonra  = satir[blok_end:].strip()
        ogr_no_match = re.match(r'^(C?\d{8})', kalan_sonra, re.IGNORECASE)
        if not ogr_no_match:
            print(f"⚠️  Satır {satir_no}: Öğrenci no bulunamadı → '{kalan_sonra[:30]}'")
            return None
        ogr_blok     = ogr_no_match.group(1).upper()
        cap          = ogr_blok.startswith('C')
        ogr_no_rakam = ogr_blok[1:] if cap else ogr_blok
        blok_end    += ogr_no_match.end()

    else:
        print(f"⚠️  Satır {satir_no}: Sayısal blok uzunluğu beklenmedik ({len(rakamlar)}) → '{blok}'")
        return None

    ogr_no   = ('C' if cap else '') + ogr_no_rakam
    kalan    = satir[blok_end:].strip()
    cevaplar = re.sub(r'[^A-Ea-e0 ]', '', kalan).replace(' ', '0').upper()

    if not cevaplar:
        print(f"⚠️  Satır {satir_no}: Cevaplar bulunamadı.")
        return None

    return {"ad_soyad": ad_soyad, "tc": tc, "ogr_no": ogr_no, "cevaplar": cevaplar}
    return {"ad_soyad": ad_soyad, "tc": tc, "ogr_no": ogr_no, "cevaplar": cevaplar}

# ============================================================
# 4. NOTLANDIRMA FONKSİYONU
# ============================================================

def ogrenci_puanla(cevaplar, anahtar, satir_no):
    """
    Her soruyu karşılaştırır.
    Doğru → 4 puan, Yanlış/Boş → 0 puan

    Returns:
        list[int] — her soru için puan
    """
    if len(cevaplar) != len(anahtar):
        print(f"⚠️  Satır {satir_no}: Cevap sayısı ({len(cevaplar)}) ≠ "
              f"anahtar sayısı ({len(anahtar)}) → padding/kesme uygulanıyor.")
        # Kısa olanı 0 ile doldur
        cevaplar = cevaplar.ljust(len(anahtar), '0')[:len(anahtar)]

    puanlar = []
    for i, (ogr_cevap, dogru_cevap) in enumerate(zip(cevaplar, anahtar)):
        if ogr_cevap in ('0', ' ', '') or ogr_cevap != dogru_cevap:
            puanlar.append(0)
        else:
            puanlar.append(4)
    return puanlar


# ============================================================
# 5. ANA İŞLEM FONKSİYONU
# ============================================================

def isle(metin, anahtar):
    """TXT içeriğini işle, tüm öğrencileri notlandır."""
    satirlar = metin.splitlines()
    print(f"\n📋 Toplam {len(satirlar)} satır işlenecek...\n")

    sonuclar = []
    hata_sayisi = 0

    for i, satir in enumerate(satirlar, start=1):
        veri = satir_parse_et(satir, i)
        if veri is None:
            if satir.strip():  # boş satır değilse say
                hata_sayisi += 1
            continue

        puanlar = ogrenci_puanla(veri["cevaplar"], anahtar, i)

        kayit = {"ogr_no": veri["ogr_no"]}
        for s_no, puan in enumerate(puanlar, start=1):
            kayit[f"S{s_no}"] = puan

        sonuclar.append({**kayit, "_toplam": sum(puanlar), "_ad_soyad": veri["ad_soyad"]})

    print(f"✅ {len(sonuclar)} öğrenci başarıyla işlendi.")
    if hata_sayisi:
        print(f"⚠️  {hata_sayisi} satırda hata oluştu (yukarıdaki uyarılara bakın).")

    return sonuclar


# ============================================================
# 6. EXCEL OLUŞTURMA FONKSİYONU
# ============================================================

def excel_olustur(sonuclar, anahtar):
    """
    İki sheet içeren Excel dosyası oluşturur:
    - Sheet 1: Öğrenci No + her soru puanı (başlık YOK)
    - Sheet 2: KONTROL — Öğrenci No + Toplam Puan
    """
    if not sonuclar:
        raise ValueError("❌ Hiç öğrenci verisi işlenemedi, Excel oluşturulamıyor.")

    # Sheet 1: başlıksız puan tablosu
    soru_sayisi = len(anahtar)
    ana_kolonlar = ["ogr_no"] + [f"S{i}" for i in range(1, soru_sayisi + 1)]

    df_ana = pd.DataFrame(sonuclar)[ana_kolonlar]

    # Sheet 2: kontrol
    df_kontrol = pd.DataFrame([
        {"Ogrenci No": r["ogr_no"], "Toplam Puan": r["_toplam"]}
        for r in sonuclar
    ])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Sheet 1: başlık satırı YOK (header=False)
        df_ana.to_excel(writer, sheet_name="SONUCLAR", index=False, header=False)
        # Sheet 2: başlık VAR
        df_kontrol.to_excel(writer, sheet_name="KONTROL", index=False)

    output.seek(0)
    return output


# ============================================================
# 7. MAIN — HER ŞEYİ BİR ARADA ÇALIŞTIR
# ============================================================

def main():
    print("=" * 55)
    print("  OPTİK OKUYUCU OTOMATIK NOTLANDIRMA SİSTEMİ")
    print("=" * 55)

    # Adım 1: Cevap anahtarı
    anahtar = cevap_anahtari_al()

    # Adım 2: Dosya yükle
    dosya_adi, metin = dosya_yukle()

    # Adım 3: İşle
    sonuclar = isle(metin, anahtar)

    # Adım 4: Excel oluştur
    print("\n📊 Excel dosyası oluşturuluyor...")
    excel_buffer = excel_olustur(sonuclar, anahtar)

    # Adım 5: İndir
    cikti_adi = dosya_adi.rsplit(".", 1)[0] + ".xlsx"
    with open(cikti_adi, "wb") as f:
        f.write(excel_buffer.read())

    print(f"✅ Excel hazır: {cikti_adi}")
    print(f"   • SONUCLAR sheet: {len(sonuclar)} öğrenci, {len(anahtar)} soru")
    print(f"   • KONTROL sheet : Öğrenci No + Toplam Puan")
    print("\n⬇️  İndirme başlıyor...")
    files.download(cikti_adi)
    print("🎉 Tamamlandı!")


# Çalıştır
main()
