"""
analiz.py — Ticket verisini analiz eder, sonuçları JSON'a kaydeder.

Bu script pandas ile tüm sayısal analizi yapar ve sonucu
analiz_sonuclari.json dosyasına yazar. LLM yorumlama scripti
(yorumla.py) ve dashboard bu dosyayı okur.

Boylece pandas hesabi bir kez yapilir, tekrar tekrar calistirilmaz.
"""

import json
import pandas as pd

# =====================================================================
# VERIYI OKU VE KATEGORILE
# =====================================================================

df = pd.read_csv("20k_ariza_ticket.csv", sep=";")
metin = df["ARIZA_NEDENI"].str.lower()

kategoriler = [
    ("OLT Donanim", r"lt\d+ kart|lt kart|kartı|kartın|kartına|uplink|"
                    r"sıcaklık|°c|servis dışı|güç ünitesi|"
                    r"olt'sine erişilemiyor|olt'ye erişilemiyor|"
                    r"yönetim ip|rx/tx"),
    ("Enerji/Guc", r"enerji kesinti|güç kaynağı|saha dolab|elektrik|jeneratör|akü"),
    ("Optik Seviye", r"optik|dbm|sinyal seviye|los durumu|rx seviye"),
    ("IPTV/Yayin", r"iptv|multicast|igmp|kanal|yayın|televizyon"),
    ("VoIP/Ses", r"voip|sip|ses |sesi|telefon|register|arama kuruluyor"),
    ("VLAN/Konfigurasyon", r"vlan|profil|eşleşmiyor|uyuşmuyor|konfigür"),
    ("Hiz/Performans", r"hız|mbps|paket kaybı|gecikme"),
    ("Internet Erisim", r"pppoe|padi|dhcp|ip alamıyor|ip alamadığı|"
                        r"ip tahsis|ip alma|ip atanamıyor|oturum|internet"),
    ("ONT Cihaz", r"ont|omci|esn|seri numara|modem|reboot|cpe|alcl|"
                  r"yazılım|offline|erişilemez|kayıt olmuyor|"
                  r"yeniden başlama"),
]

df["kategori"] = "Diger"
for ad, desen in kategoriler:
    etiketsiz = df["kategori"] == "Diger"
    eslesme = metin.str.contains(desen, na=False)
    df.loc[etiketsiz & eslesme, "kategori"] = ad

# Tarih dönüşümü (saniye yok: %H:%M)
df["tarih"] = pd.to_datetime(
    df["ARIZA_ACILIS_TARIHI"],
    format="%d.%m.%Y %H:%M",
    errors="coerce",
)


# =====================================================================
# SONUÇLARI SÖZLÜĞE TOPLA
# =====================================================================

sonuc = {}

# --- Soru 1 & 2: Arıza türleri ---
kategori_dagilimi = df["kategori"].value_counts()
sonuc["ariza_turleri"] = {
    "dagilim": kategori_dagilimi.to_dict(),
    "yuzde": (kategori_dagilimi / len(df) * 100).round(1).to_dict(),
    "en_cok": {
        "kategori": kategori_dagilimi.index[0],
        "adet": int(kategori_dagilimi.iloc[0]),
        "yuzde": round(kategori_dagilimi.iloc[0] / len(df) * 100, 1),
    },
    "toplam_tur": len(kategori_dagilimi),
}

# --- Soru 3: Cihaz (OLT) ---
olt_dagilimi = df["OLT_ADI"].value_counts()
sonuc["cihaz"] = {
    "toplam_olt": int(df["OLT_ADI"].nunique()),
    "ortalama": round(olt_dagilimi.mean(), 1),
    "medyan": round(olt_dagilimi.median(), 1),
    "en_cok_20": olt_dagilimi.head(20).to_dict(),
    "en_cok": {
        "olt": olt_dagilimi.index[0],
        "adet": int(olt_dagilimi.iloc[0]),
        "yuzde": round(olt_dagilimi.iloc[0] / len(df) * 100, 1),
    },
}

# --- Soru 4: Zaman ---
gunluk = df.groupby(df["tarih"].dt.date).size()
aylik = df.groupby(df["tarih"].dt.to_period("M")).size()
saatlik = df.groupby(df["tarih"].dt.hour).size()
gun_adlari = ["Pazartesi", "Sali", "Carsamba", "Persembe",
              "Cuma", "Cumartesi", "Pazar"]
haftalik = df.groupby(df["tarih"].dt.dayofweek).size()

esik = gunluk.mean() + 2 * gunluk.std()
anormal = gunluk[gunluk > esik]

sonuc["zaman"] = {
    "baslangic": str(df["tarih"].min().date()),
    "bitis": str(df["tarih"].max().date()),
    "gunluk_ortalama": round(gunluk.mean(), 1),
    "gunluk_std": round(gunluk.std(), 1),
    "en_yogun_10_gun": {str(k): int(v) for k, v in gunluk.nlargest(10).items()},
    "aylik": {str(k): int(v) for k, v in aylik.items()},
    "saatlik": {int(k): int(v) for k, v in saatlik.items()},
    "haftalik": {gun_adlari[k]: int(v) for k, v in haftalik.items()},
    "anomali_esigi": round(esik, 1),
    "anormal_gun_sayisi": int(len(anormal)),
    "anormal_gunler": {str(k): int(v) for k, v in anormal.items()},
}

sonuc["ozet"] = {
    "toplam_kayit": len(df),
    "tarihi_cozulen": int(df["tarih"].notna().sum()),
}


# =====================================================================
# JSON'A KAYDET + ETIKETLI VERIYI KAYDET
# =====================================================================

with open("analiz_sonuclari.json", "w", encoding="utf-8") as f:
    json.dump(sonuc, f, ensure_ascii=False, indent=2, default=str)

# Dashboard'un ham veriye erişebilmesi için etiketli CSV
df.to_csv("etiketli_ticketlar.csv", sep=";", index=False, encoding="utf-8")

print("Analiz tamamlandi.")
print("  -> analiz_sonuclari.json")
print("  -> etiketli_ticketlar.csv")
print()
print("Ozet:")
print(f"  Toplam kayit    : {sonuc['ozet']['toplam_kayit']:,}")
print(f"  En cok ariza    : {sonuc['ariza_turleri']['en_cok']['kategori']} "
      f"(%{sonuc['ariza_turleri']['en_cok']['yuzde']})")
print(f"  En sorunlu OLT  : {sonuc['cihaz']['en_cok']['olt']}")
print(f"  Gunluk ortalama : {sonuc['zaman']['gunluk_ortalama']}")
print(f"  Anormal gun     : {sonuc['zaman']['anormal_gun_sayisi']}")
print()
print("Sonraki adim (VM'de): python yorumla.py")
